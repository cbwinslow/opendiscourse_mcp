#!/usr/bin/env python3
"""
GovInfo Bulk Data Downloader

This script downloads XML files and XSL schemas from govinfo.gov bulk data repository
using concurrent processing for maximum speed while preventing data duplication.

Features:
- Concurrent downloads (10-15 threads)
- Data duplication prevention using checksums
- Comprehensive error handling and retry logic
- Progress tracking and logging
- Support for all govinfo bulk data collections
"""

import os
import sys
import time
import hashlib
import requests
import threading
import concurrent.futures
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass
from enum import Enum, auto
import sqlite3
from config.global_settings import GlobalSettings

# Initialize global settings
settings = GlobalSettings()

class DownloadStatus(Enum):
    """Download status enumeration"""
    PENDING = auto()
    DOWNLOADING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()

@dataclass
class DownloadResult:
    """Download result data class"""
    url: str
    local_path: str
    status: DownloadStatus
    error: Optional[str] = None
    size: int = 0
    checksum: Optional[str] = None
    duration: float = 0.0

class GovInfoBulkDownloader:
    """
    GovInfo Bulk Data Downloader

    Handles downloading XML files and XSL schemas from govinfo.gov bulk data repository
    with concurrent processing and duplication prevention.
    """

    def __init__(self, base_url: str = "https://www.govinfo.gov/bulkdata/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.security.user_agent,
            'Accept': 'application/xml,text/xml,application/json,*/*'
        })

        # Configure logging
        self._setup_logging()

        # Initialize database for tracking downloads
        self.db_path = Path(settings.data_directory) / "govinfo_downloads.db"
        self._init_database()

        # Thread-safe sets for tracking
        self.downloaded_files: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.lock = threading.Lock()

        # Statistics
        self.total_files = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_files = 0
        self.total_bytes = 0
        self.start_time = None

    def _setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=getattr(logging, settings.logging.level.upper(), logging.INFO),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    Path(settings.logging.file_path).parent / "govinfo_downloader.log",
                    mode='a',
                    encoding='utf-8'
                )
            ]
        )
        self.logger = logging.getLogger("GovInfoBulkDownloader")

    def _init_database(self):
        """Initialize SQLite database for tracking downloads"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    local_path TEXT,
                    checksum TEXT,
                    size INTEGER,
                    status TEXT,
                    error TEXT,
                    timestamp DATETIME,
                    collection TEXT,
                    data_type TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    last_checked DATETIME,
                    file_count INTEGER,
                    total_size INTEGER
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_downloads_url ON downloads(url)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_downloads_checksum ON downloads(checksum)
            ''')

            conn.commit()

        self.logger.info(f"Database initialized at {self.db_path}")

    def _load_existing_downloads(self):
        """Load existing downloads from database to prevent duplication"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT url, checksum FROM downloads WHERE status = "COMPLETED"')
            existing = cursor.fetchall()

            with self.lock:
                self.downloaded_files = {url for url, _ in existing}
                self.logger.info(f"Loaded {len(self.downloaded_files)} existing downloads from database")

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _is_duplicate(self, url: str, checksum: str) -> bool:
        """Check if file is a duplicate using checksum"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM downloads WHERE checksum = ?', (checksum,))
            return cursor.fetchone() is not None

    def _record_download(self, result: DownloadResult):
        """Record download result in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO downloads
                (url, local_path, checksum, size, status, error, timestamp, collection, data_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.url,
                str(result.local_path),
                result.checksum,
                result.size,
                result.status.name,
                result.error,
                datetime.now().isoformat(),
                self._extract_collection_from_url(result.url),
                self._extract_data_type_from_url(result.url)
            ))
            conn.commit()

    def _extract_collection_from_url(self, url: str) -> str:
        """Extract collection name from URL"""
        parts = urlparse(url).path.strip('/').split('/')
        return parts[1] if len(parts) > 1 else "unknown"

    def _extract_data_type_from_url(self, url: str) -> str:
        """Extract data type from URL"""
        if url.endswith('.xml'):
            return "xml"
        elif url.endswith('.xsl'):
            return "xsl"
        elif url.endswith('.xsd'):
            return "xsd"
        else:
            return "other"

    def _get_local_path(self, url: str, base_dir: Path) -> Path:
        """Generate local file path from URL"""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        # Remove empty parts and create directory structure
        clean_parts = [part for part in path_parts if part and not part.startswith('.')]

        # Create collection directory
        collection_dir = base_dir / clean_parts[0] if clean_parts else base_dir / "misc"

        # Create subdirectories if they exist
        if len(clean_parts) > 2:
            subdirs = clean_parts[1:-1]
            for subdir in subdirs:
                collection_dir = collection_dir / subdir

        # Create filename
        filename = clean_parts[-1] if clean_parts else "unknown"
        return collection_dir / filename

    def _download_file(self, url: str, base_dir: Path, retry_count: int = 3) -> DownloadResult:
        """
        Download a single file with retry logic

        Args:
            url: URL to download
            base_dir: Base directory for local storage
            retry_count: Maximum retry attempts

        Returns:
            DownloadResult with download status and metadata
        """
        result = DownloadResult(url=url, local_path="", status=DownloadStatus.PENDING)
        start_time = time.time()

        # Check if already downloaded
        with self.lock:
            if url in self.downloaded_files:
                result.status = DownloadStatus.SKIPPED
                result.error = "Already downloaded"
                return result

        try:
            # Create local directory structure
            local_path = self._get_local_path(url, base_dir)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            result.local_path = str(local_path)

            # Download with retry
            for attempt in range(retry_count):
                try:
                    self.logger.debug(f"Downloading {url} (attempt {attempt + 1}/{retry_count})")

                    response = self.session.get(
                        url,
                        stream=True,
                        timeout=settings.api.request_timeout,
                        headers={'Accept': 'application/xml,text/xml,application/json,*/*'}
                    )

                    # Check for successful response
                    if response.status_code == 200:
                        # Save file
                        with open(local_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    self.total_bytes += len(chunk)

                        # Calculate checksum and file size
                        result.size = local_path.stat().st_size
                        result.checksum = self._calculate_checksum(local_path)

                        # Check for duplicates
                        if self._is_duplicate(url, result.checksum):
                            local_path.unlink()  # Remove duplicate file
                            result.status = DownloadStatus.SKIPPED
                            result.error = "Duplicate file detected"
                            self.logger.warning(f"Duplicate detected: {url}")
                            break

                        result.status = DownloadStatus.COMPLETED
                        result.duration = time.time() - start_time

                        # Add to downloaded files set
                        with self.lock:
                            self.downloaded_files.add(url)

                        self.logger.info(f"✅ Downloaded {url} ({result.size} bytes, {result.duration:.2f}s)")
                        break

                    elif response.status_code == 406:
                        # Try with different accept headers
                        response = self.session.get(
                            url,
                            stream=True,
                            timeout=settings.api.request_timeout,
                            headers={'Accept': '*/*'}
                        )
                        if response.status_code == 200:
                            continue
                        else:
                            raise Exception(f"406 error even with wildcard accept header")

                    else:
                        raise Exception(f"HTTP {response.status_code}: {response.text[:100]}...")

                except Exception as e:
                    if attempt == retry_count - 1:
                        result.status = DownloadStatus.FAILED
                        result.error = str(e)
                        self.logger.error(f"❌ Failed to download {url}: {str(e)}")
                        with self.lock:
                            self.failed_urls.add(url)
                    else:
                        wait_time = settings.api.retry_delay * (attempt + 1)
                        self.logger.warning(f"Retrying {url} in {wait_time}s...")
                        time.sleep(wait_time)

        except Exception as e:
            result.status = DownloadStatus.FAILED
            result.error = str(e)
            self.logger.error(f"❌ Unexpected error downloading {url}: {str(e)}")

        result.duration = time.time() - start_time
        return result

    def _crawl_collection_recursive(self, start_url: str, collection: str, max_depth: int = 10, current_depth: int = 0) -> List[str]:
        """
        Recursively crawl govinfo directory structure to find files
        
        Args:
            start_url: URL to start crawling from
            collection: Collection name (for filtering)
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            
        Returns:
            List of file URLs
        """
        file_urls = []
        
        if current_depth > max_depth:
            return file_urls
            
        try:
            self.logger.debug(f"Crawling {start_url} (Depth: {current_depth})")
            response = self.session.get(start_url)
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to access {start_url}: Status {response.status_code}")
                return file_urls

            # Try parsing as custom XML format first (found in govinfo)
            # Structure: <data><files><file><folder>true/false</folder><link>url</link>...</file>...</files></data>
            try:
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.content)
                
                # Check if it looks like the expected XML
                if root.tag == 'data' or root.find('.//file') is not None:
                    for file_elem in root.findall('.//file'):
                        link = file_elem.find('link').text if file_elem.find('link') is not None else None
                        is_folder = file_elem.find('folder').text == 'true' if file_elem.find('folder') is not None else False
                        
                        if not link:
                            continue
                            
                        if is_folder:
                             # Recurse
                             if '/bulkdata/' in link and collection in link:
                                sub_files = self._crawl_collection_recursive(
                                    link, 
                                    collection, 
                                    max_depth, 
                                    current_depth + 1
                                )
                                file_urls.extend(sub_files)
                        else:
                            # It's a file
                            if link.lower().endswith(('.xml', '.xsl', '.xsd')):
                                file_urls.append(link)
                    
                    return file_urls # Successfully parsed as XML
            except Exception:
                # Not XML or parse error, fall back to HTML
                pass
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # GovInfo bulk data directory listings typically have links in a table or list
            # We look for links that are either directories (ending in /) or files
            for link in soup.find_all('a'):
                href = link.get('href')
                if not href or href == '../' or href == './' or href.startswith('?'):
                    continue
                    
                full_url = urljoin(start_url, href)
                
                # Check if it's a file we want
                if href.lower().endswith(('.xml', '.xsl', '.xsd')):
                    file_urls.append(full_url)
                    
                # Check if it's a directory to traverse
                elif href.endswith('/'):
                    # Ensure we stay within the bulkdata realm and don't go up
                    if '/bulkdata/' in full_url and collection in full_url:
                        # Recursive call
                        sub_files = self._crawl_collection_recursive(
                            full_url, 
                            collection, 
                            max_depth, 
                            current_depth + 1
                        )
                        file_urls.extend(sub_files)
                        
        except Exception as e:
            self.logger.error(f"Error crawling {start_url}: {str(e)}")
            
        return file_urls

    def _get_all_collections(self) -> List[str]:
        """Get list of all available collections"""
        # Common govinfo collections
        common_collections = [
            'BILLS', 'BILLSTATUS', 'CFR', 'CONGREC', 'ECFR',
            'FR', 'HOUSE', 'PLAW', 'PPRO', 'SENATE', 'STATUTE'
        ]

        # Try to fetch from main bulkdata page
        try:
            response = self.session.get(
                self.base_url,
                headers={'Accept': 'text/html'}
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                collections = []
                
                # Look for links that look like collection names (uppercase directories)
                for link in soup.find_all('a'):
                    href = link.get('href', '').strip('/')
                    # Collection names are usually uppercase and top-level in bulkdata
                    if href and href.isupper() and len(href) > 1 and '/' not in href:
                         collections.append(href)

                if collections:
                    # Filter out non-collections if necessary, but returning what we find is usually good
                    # Deduplicate and sort
                    return sorted(list(set(collections)))

        except Exception as e:
            self.logger.warning(f"Could not fetch collections structure: {str(e)}")

        return sorted(common_collections)

    def download_collection(self, collection: str, base_dir: Path = None,
                          max_workers: int = 15, include_xsl: bool = True, congress: str = None) -> Dict[str, any]:
        """
        Download all files for a specific collection

        Args:
            collection: Collection name
            base_dir: Base directory for downloads (default: data/govinfo)
            max_workers: Maximum concurrent workers
            include_xsl: Include XSL schema files
            congress: Optional congress number to filter by (e.g. "115")

        Returns:
            Dictionary with download statistics
        """
        if base_dir is None:
            base_dir = Path(settings.data_directory) / "govinfo"

        self.logger.info(f"Starting download for collection: {collection}")
        self.logger.info(f"Base directory: {base_dir}")
        self.logger.info(f"Max workers: {max_workers}")

        # Reset statistics
        self.total_files = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_files = 0
        self.total_bytes = 0
        self.start_time = time.time()

        # Load existing downloads
        self._load_existing_downloads()

        # Get all file URLs for this collection
        self.logger.info(f"Crawling collection {collection} for files...")
        
        # Determine start URL
        collection_url = urljoin(self.base_url, collection + '/')
        if congress:
            # Append congress number to base URL if provided
            # This assumes the collection is organized by congress (e.g. BILLS/115)
            # If it's not (e.g. FR), check if this path exists first?
            # For now, we attempt to append it. Crawler will handle 404s/warnings if invalid.
            collection_url = urljoin(collection_url, f"{congress}/")
            self.logger.info(f"Targeting specific congress: {congress} at {collection_url}")
        
        # Use recursive crawler
        file_urls = self._crawl_collection_recursive(collection_url, collection)

        if include_xsl:
            # Try to find XSLs. They might be in a 'resources' folder or separate 'xsl' folders?
            # Based on user research, some might be in the collection or in global folders.
            # We can also check specific XSL paths.
            self.logger.info("Scanning for additional XSL schemas...")
            # Some schemas are in /bulkdata/xsl or /bulkdata/<COLLECTION>/resources
            xsl_roots = [
                 urljoin(self.base_url, "xsl/"),
                 urljoin(self.base_url, f"{collection}/resources/")
            ]
            for root in xsl_roots:
                xsl_files = self._crawl_collection_recursive(root, collection) # collection filter might block 'xsl' dir if distinct
                # If checking common xsl/ without filter
                if "xsl/" in root:
                     xsl_files = self._crawl_collection_recursive(root, "xsl")
                
                file_urls.extend(xsl_files)

        # Remove duplicates
        file_urls = sorted(list(set(file_urls)))

        self.total_files = len(file_urls)
        self.logger.info(f"Found {self.total_files} files to download")

        if not file_urls:
            self.logger.warning(f"No files found for collection {collection}")
            return self._get_stats()

        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self._download_file, url, base_dir): url
                for url in file_urls
            }

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()

                    # Record download result
                    self._record_download(result)

                    # Update statistics
                    if result.status == DownloadStatus.COMPLETED:
                        self.successful_downloads += 1
                    elif result.status == DownloadStatus.FAILED:
                        self.failed_downloads += 1
                    elif result.status == DownloadStatus.SKIPPED:
                        self.skipped_files += 1

                except Exception as e:
                    self.logger.error(f"Error processing {url}: {str(e)}")
                    self.failed_downloads += 1

        return self._get_stats()



    def download_all_collections(self, base_dir: Path = None,
                               max_workers: int = 15, include_xsl: bool = True,
                               congress: str = None) -> Dict[str, any]:
        """
        Download all available collections

        Args:
            base_dir: Base directory for downloads
            max_workers: Maximum concurrent workers per collection
            include_xsl: Include XSL schema files
            congress: Optional congress number filter
        """
        if base_dir is None:
            base_dir = Path(settings.data_directory) / "govinfo"

        self.logger.info("Starting download for all collections")
        if congress:
            self.logger.info(f"Filtering for Congress: {congress}")

        # Get all collections
        collections = self._get_all_collections()
        self.logger.info(f"Found {len(collections)} collections: {', '.join(collections)}")

        # Process each collection
        overall_stats = {
            'total_files': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_files': 0,
            'total_bytes': 0,
            'collections': {}
        }

        for collection in collections:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing collection: {collection}")
            self.logger.info('='*60)

            collection_dir = base_dir / collection
            stats = downloader.download_collection(
                collection,
                collection_dir,
                max_workers=max_workers,
                include_xsl=include_xsl,
                congress=congress
            )

            # Update overall statistics
            overall_stats['total_files'] += stats['total_files']
            overall_stats['successful_downloads'] += stats['successful_downloads']
            overall_stats['failed_downloads'] += stats['failed_downloads']
            overall_stats['skipped_files'] += stats['skipped_files']
            overall_stats['total_bytes'] += stats['total_bytes']
            overall_stats['collections'][collection] = stats

            # Save progress after each collection
            self._save_progress(overall_stats)

        return overall_stats

    def _get_stats(self) -> Dict[str, any]:
        """Get current download statistics"""
        duration = time.time() - self.start_time if self.start_time else 0

        return {
            'total_files': self.total_files,
            'successful_downloads': self.successful_downloads,
            'failed_downloads': self.failed_downloads,
            'skipped_files': self.skipped_files,
            'total_bytes': self.total_bytes,
            'duration': duration,
            'speed': self.total_bytes / duration if duration > 0 else 0,
            'failed_urls': list(self.failed_urls)
        }

    def _save_progress(self, stats: Dict[str, any]):
        """Save download progress to file"""
        progress_file = Path(settings.data_directory) / "govinfo_download_progress.json"

        with open(progress_file, 'w') as f:
            json.dump(stats, f, indent=2)

        self.logger.info(f"Progress saved to {progress_file}")

    def print_summary(self, stats: Dict[str, any]):
        """Print download summary"""
        duration = stats['duration']
        speed_mb = stats['speed'] / (1024 * 1024) if stats['speed'] > 0 else 0

        print("\n" + "="*60)
        print("GOVINFO BULK DOWNLOAD SUMMARY")
        print("="*60)
        print(f"Total Files Processed: {stats['total_files']}")
        print(f"Successful Downloads: {stats['successful_downloads']}")
        print(f"Failed Downloads: {stats['failed_downloads']}")
        print(f"Skipped Files: {stats['skipped_files']}")
        print(f"Total Data Downloaded: {stats['total_bytes'] / (1024 * 1024):.2f} MB")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Average Speed: {speed_mb:.2f} MB/s")
        print(f"Start Time: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'N/A'}")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if stats['failed_downloads'] > 0:
            print(f"\nFailed URLs ({stats['failed_downloads']}):")
            for url in stats['failed_urls'][:10]:  # Show first 10
                print(f"  - {url}")
            if len(stats['failed_urls']) > 10:
                print(f"  ... and {len(stats['failed_urls']) - 10} more")

        print("="*60)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="GovInfo Bulk Data Downloader")
    parser.add_argument('--collection', help="Specific collection to download (e.g., BILLS, FR)")
    parser.add_argument('--all', action='store_true', help="Download all collections")
    parser.add_argument('--workers', type=int, default=15, help="Number of concurrent workers")
    parser.add_argument('--congress', help="Specific congress number to download (e.g., 115, 116)")
    parser.add_argument('--output', help="Output directory")
    parser.add_argument('--no-xsl', action='store_false', dest='include_xsl', help="Exclude XSL schema files")
    parser.add_argument('--resume', action='store_true', help="Resume previous download")

    args = parser.parse_args()

    # Initialize downloader
    downloader = GovInfoBulkDownloader()

    if args.resume:
        downloader.logger.info("Resuming previous download session")
        downloader._load_existing_downloads()

    if args.all:
        # Download all collections
        output_dir = Path(args.output) if args.output else None
        stats = downloader.download_all_collections(
            base_dir=output_dir,
            max_workers=args.workers,
            include_xsl=args.include_xsl,
            congress=args.congress
        )
        downloader.print_summary(stats)

    elif args.collection:
        # Download specific collection
        output_dir = Path(args.output) if args.output else None
        stats = downloader.download_collection(
            args.collection,
            base_dir=output_dir,
            max_workers=args.workers,
            include_xsl=args.include_xsl,
            congress=args.congress
        )
        downloader.print_summary(stats)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()