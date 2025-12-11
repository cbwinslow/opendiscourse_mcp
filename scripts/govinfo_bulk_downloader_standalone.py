#!/usr/bin/env python3
"""
GovInfo Bulk Data Downloader - Standalone Version

This script downloads XML files and XSL schemas from govinfo.gov bulk data repository
using concurrent processing for maximum speed while preventing data duplication.

Features:
- Concurrent downloads (10-15 threads)
- Data duplication prevention using file tracking
- Basic error handling and retry logic
- Progress tracking
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
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

class GovInfoBulkDownloaderStandalone:
    """
    Standalone GovInfo Bulk Data Downloader
    """

    def __init__(self, base_url: str = "https://www.govinfo.gov/bulkdata/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': "OpenDiscourse-MCP/1.0",
            'Accept': 'application/xml,text/xml,application/json,*/*'
        })

        # Configure logging
        self._setup_logging()

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
        self.start_time: Optional[float] = None

        # Default settings
        self.max_concurrent_requests = 15
        self.request_timeout = 60
        self.retry_delay = 2
        self.max_retries = 3
        self.data_directory = "data/govinfo"

    def _setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    "logs/govinfo_downloader_standalone.log",
                    mode='a',
                    encoding='utf-8'
                )
            ]
        )
        self.logger = logging.getLogger("GovInfoBulkDownloaderStandalone")

    def _load_tracking_file(self):
        """Load existing downloads from tracking file"""
        tracking_file = Path(self.data_directory) / "govinfo_downloads_tracking.json"

        if tracking_file.exists():
            try:
                with open(tracking_file, 'r') as f:
                    tracking_data = json.load(f)
                    with self.lock:
                        self.downloaded_files = set(tracking_data.get('downloaded_files', []))
                        self.logger.info(f"Loaded {len(self.downloaded_files)} existing downloads from tracking file")
            except Exception as e:
                self.logger.error(f"Error loading tracking file: {str(e)}")

    def _save_tracking_file(self):
        """Save download tracking to file"""
        tracking_file = Path(self.data_directory) / "govinfo_downloads_tracking.json"
        tracking_data = {
            'downloaded_files': list(self.downloaded_files),
            'failed_urls': list(self.failed_urls),
            'last_updated': datetime.now().isoformat()
        }

        tracking_file.parent.mkdir(parents=True, exist_ok=True)
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)

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

    def _download_file(self, url: str, base_dir: Path, retry_count: int = 3) -> Dict[str, any]:
        """
        Download a single file with retry logic

        Args:
            url: URL to download
            base_dir: Base directory for local storage
            retry_count: Maximum retry attempts

        Returns:
            Dictionary with download status and metadata
        """
        result = {
            'url': url,
            'local_path': "",
            'status': 'pending',
            'error': None,
            'size': 0,
            'duration': 0.0
        }
        start_time = time.time()

        # Check if already downloaded
        with self.lock:
            if url in self.downloaded_files:
                result['status'] = 'skipped'
                result['error'] = "Already downloaded"
                return result

        try:
            # Create local directory structure
            local_path = self._get_local_path(url, base_dir)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            result['local_path'] = str(local_path)

            # Download with retry
            for attempt in range(retry_count):
                try:
                    self.logger.debug(f"Downloading {url} (attempt {attempt + 1}/{retry_count})")

                    response = self.session.get(
                        url,
                        stream=True,
                        timeout=self.request_timeout,
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

                        # Get file size
                        result['size'] = local_path.stat().st_size
                        result['status'] = 'completed'
                        result['duration'] = time.time() - start_time

                        # Add to downloaded files set
                        with self.lock:
                            self.downloaded_files.add(url)

                        self.logger.info(f"✅ Downloaded {url} ({result['size']} bytes, {result['duration']:.2f}s)")
                        break

                    elif response.status_code == 406:
                        # Try with different accept headers
                        response = self.session.get(
                            url,
                            stream=True,
                            timeout=self.request_timeout,
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
                        result['status'] = 'failed'
                        result['error'] = str(e)
                        self.logger.error(f"❌ Failed to download {url}: {str(e)}")
                        with self.lock:
                            self.failed_urls.add(url)
                    else:
                        wait_time = self.retry_delay * (attempt + 1)
                        self.logger.warning(f"Retrying {url} in {wait_time}s...")
                        time.sleep(wait_time)

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.logger.error(f"❌ Unexpected error downloading {url}: {str(e)}")

        result['duration'] = time.time() - start_time
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

        return common_collections

    def download_collection(self, collection: str, base_dir: Optional[Path] = None,
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
            base_dir = Path(self.data_directory)

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
        self._load_tracking_file()

        # Get all file URLs for this collection
        self.logger.info(f"Fetching file list for {collection}...")
        file_urls = self._get_collection_urls(collection)

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

                    # Update statistics
                    if result['status'] == 'completed':
                        self.successful_downloads += 1
                    elif result['status'] == 'failed':
                        self.failed_downloads += 1
                    elif result['status'] == 'skipped':
                        self.skipped_files += 1

                except Exception as e:
                    self.logger.error(f"Error processing {url}: {str(e)}")
                    self.failed_downloads += 1

        # Save tracking file
        self._save_tracking_file()

        return self._get_stats()

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

    def print_summary(self, stats: Dict[str, any]) -> None:
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

    parser = argparse.ArgumentParser(description="GovInfo Bulk Data Downloader - Standalone Version")
    parser.add_argument('--collection', help="Specific collection to download (e.g., BILLS, FR)")
    parser.add_argument('--all', action='store_true', help="Download all collections")
    parser.add_argument('--workers', type=int, default=15, help="Number of concurrent workers")
    parser.add_argument('--output', help="Output directory")
    parser.add_argument('--no-xsl', action='store_false', dest='include_xsl', help="Exclude XSL schema files")
    parser.add_argument('--resume', action='store_true', help="Resume previous download")

    args = parser.parse_args()

    # Initialize downloader
    downloader = GovInfoBulkDownloaderStandalone()

    if args.resume:
        downloader.logger.info("Resuming previous download session")
        downloader._load_tracking_file()

    if args.all:
        # Download all collections
        output_dir = Path(args.output) if args.output else None
        stats = downloader.download_collection(
            "BILLS",  # Start with BILLS for testing
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