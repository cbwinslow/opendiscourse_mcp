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
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
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

    def _get_collection_urls(self, collection: str) -> List[str]:
        """
        Get all file URLs for a specific collection

        Args:
            collection: Collection name (e.g., 'BILLS', 'FR', 'CFR')

        Returns:
            List of file URLs
        """
        base_url = urljoin(self.base_url, collection + '/')
        file_urls = []

        try:
            # Try XML endpoint first
            xml_url = f"https://www.govinfo.gov/bulkdata/xml/{collection}"
            response = self.session.get(xml_url, headers={'Accept': 'application/xml'})

            if response.status_code == 200:
                # Parse XML to extract file URLs
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.content)

                for file_elem in root.findall('.//file'):
                    file_path = file_elem.text
                    if file_path:
                        full_url = urljoin(base_url, file_path)
                        file_urls.append(full_url)

            else:
                # Fall back to JSON endpoint
                json_url = f"https://www.govinfo.gov/bulkdata/json/{collection}"
                response = self.session.get(json_url, headers={'Accept': 'application/json'})

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'path' in item:
                                full_url = urljoin(base_url, item['path'])
                                file_urls.append(full_url)
                    elif isinstance(data, dict) and 'files' in data:
                        for file_info in data['files']:
                            full_url = urljoin(base_url, file_info['path'])
                            file_urls.append(full_url)

        except Exception as e:
            self.logger.error(f"Error fetching collection {collection}: {str(e)}")

        return file_urls

    def _get_all_collections(self) -> List[str]:
        """Get list of all available collections"""
        # Common govinfo collections
        common_collections = [
            'BILLS', 'BILLSTATUS', 'CFR', 'CONGREC', 'ECFR',
            'FR', 'HOUSE', 'PLAW', 'PPRO', 'SENATE', 'STATUTE'
        ]

        # Try to fetch from API
        try:
            response = self.session.get(
                self.base_url,
                headers={'Accept': 'application/json'}
            )

            if response.status_code == 200:
                # Parse HTML to find collection links
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                collections = []
                for link in soup.find_all('a'):
                    href = link.get('href', '').strip('/')
                    if href and href.isupper() and len(href) > 2:
                        collections.append(href)

                if collections:
                    return collections

        except Exception as e:
            self.logger.warning(f"Could not fetch collections from API: {str(e)}")

        return common_collections

    def download_collection(self, collection: str, base_dir: Path = None,
                          max_workers: int = 15, include_xsl: bool = True) -> Dict[str, any]:
        """
        Download all files for a specific collection

        Args:
            collection: Collection name
            base_dir: Base directory for downloads (default: data/govinfo)
            max_workers: Maximum concurrent workers
            include_xsl: Include XSL schema files

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
        self.logger.info(f"Fetching file list for {collection}...")
        file_urls = self._get_collection_urls(collection)

        if include_xsl:
            # Add XSL schema files
            xsl_urls = self._get_xsl_files(collection)
            file_urls.extend(xsl_urls)

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

    def _get_xsl_files(self, collection: str) -> List[str]:
        """Get XSL schema files for a collection"""
        xsl_urls = []

        # Common XSL locations
        xsl_paths = [
            f"{collection}/xsl",
            f"xsl/{collection}",
            "xsl/common"
        ]

        for xsl_path in xsl_paths:
            try:
                # Try XML endpoint
                xml_url = f"https://www.govinfo.gov/bulkdata/xml/{xsl_path}"
                response = self.session.get(xml_url, headers={'Accept': 'application/xml'})

                if response.status_code == 200:
                    from xml.etree import ElementTree
                    root = ElementTree.fromstring(response.content)

                    for file_elem in root.findall('.//file'):
                        file_path = file_elem.text
                        if file_path and file_path.endswith('.xsl'):
                            full_url = f"https://www.govinfo.gov/bulkdata/{xsl_path}/{file_path}"
                            xsl_urls.append(full_url)

                else:
                    # Try JSON endpoint
                    json_url = f"https://www.govinfo.gov/bulkdata/json/{xsl_path}"
                    response = self.session.get(json_url, headers={'Accept': 'application/json'})

                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'path' in item and item['path'].endswith('.xsl'):
                                    full_url = f"https://www.govinfo.gov/bulkdata/{xsl_path}/{item['path']}"
                                    xsl_urls.append(full_url)

            except Exception as e:
                self.logger.debug(f"Could not fetch XSL files from {xsl_path}: {str(e)}")

        return xsl_urls

    def download_all_collections(self, base_dir: Path = None,
                               max_workers: int = 15, include_xsl: bool = True) -> Dict[str, any]:
        """
        Download all available collections

        Args:
            base_dir: Base directory for downloads
            max_workers: Maximum concurrent workers per collection
            include_xsl: Include XSL schema files

        Returns:
            Dictionary with overall statistics
        """
        if base_dir is None:
            base_dir = Path(settings.data_directory) / "govinfo"

        self.logger.info("Starting download for all collections")

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
            stats = self.download_collection(
                collection,
                collection_dir,
                max_workers=max_workers,
                include_xsl=include_xsl
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
            include_xsl=args.include_xsl
        )
        downloader.print_summary(stats)

    elif args.collection:
        # Download specific collection
        output_dir = Path(args.output) if args.output else None
        stats = downloader.download_collection(
            args.collection,
            base_dir=output_dir,
            max_workers=args.workers,
            include_xsl=args.include_xsl
        )
        downloader.print_summary(stats)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()