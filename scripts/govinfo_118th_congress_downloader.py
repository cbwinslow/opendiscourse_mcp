#!/usr/bin/env python3
"""
GovInfo 118th Congress Bulk Data Downloader

This script specifically downloads XML files and XSL schemas for the 118th Congress
from govinfo.gov bulk data repository using concurrent processing for maximum speed
while preventing data duplication.

Features:
- Multi-threaded downloads (12-15 threads)
- 118th Congress specific targeting
- All data types: Bills, Joint Resolutions, Concurrent Resolutions
- XSL schema support and validation
- Enhanced duplicate prevention using SHA256 checksums
- Progress tracking and comprehensive logging
- Support for both sessions of 118th Congress
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
from typing import List, Dict, Set, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime
import xml.etree.ElementTree as ET

class GovInfo118thCongressDownloader:
    """
    118th Congress Specific GovInfo Bulk Data Downloader
    """

    def __init__(self, base_url: str = "https://www.govinfo.gov/bulkdata/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.congress_number = 118
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': "OpenDiscourse-MCP/1.0 118th-Congress-Downloader",
            'Accept': 'application/xml,text/xml,application/json,*/*'
        })

        # Configure logging
        self._setup_logging()

        # Thread-safe tracking
        self.downloaded_files: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.file_checksums: Dict[str, str] = {}
        self.lock = threading.Lock()

        # Statistics
        self.total_files = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_files = 0
        self.total_bytes = 0
        self.start_time: Optional[float] = None

        # 118th Congress specific settings
        self.max_concurrent_requests = 15  # 12-15 threads as requested
        self.request_timeout = 60
        self.retry_delay = 2
        self.max_retries = 3
        self.data_directory = "data/govinfo"
        
        # 118th Congress bill types to target
        self.bill_types = {
            'hr': 'House Bills',
            's': 'Senate Bills', 
            'hjres': 'House Joint Resolutions',
            'sjres': 'Senate Joint Resolutions',
            'hconres': 'House Concurrent Resolutions',
            'sconres': 'Senate Concurrent Resolutions'
        }


    def _setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    "logs/govinfo_118th_congress_downloader.log",
                    mode='a',
                    encoding='utf-8'
                )
            ]
        )
        self.logger = logging.getLogger("GovInfo118thCongressDownloader")

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def _load_tracking_file(self):
        """Load existing downloads from tracking file"""
        tracking_file = Path(self.data_directory) / "govinfo_118th_congress_tracking.json"

        if tracking_file.exists():
            try:
                with open(tracking_file, 'r') as f:
                    tracking_data = json.load(f)
                    with self.lock:
                        self.downloaded_files = set(tracking_data.get('downloaded_files', []))
                        self.file_checksums = tracking_data.get('file_checksums', {})
                        self.logger.info(f"Loaded {len(self.downloaded_files)} existing downloads from tracking file")
            except Exception as e:
                self.logger.error(f"Error loading tracking file: {str(e)}")

    def _save_tracking_file(self):
        """Save download tracking to file"""
        tracking_file = Path(self.data_directory) / "govinfo_118th_congress_tracking.json"
        tracking_data = {
            'congress': self.congress_number,
            'downloaded_files': list(self.downloaded_files),
            'failed_urls': list(self.failed_urls),
            'file_checksums': self.file_checksums,
            'last_updated': datetime.now().isoformat()
        }

        tracking_file.parent.mkdir(parents=True, exist_ok=True)
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)


    def _get_local_path(self, url: str, base_dir: Path) -> Path:
        """Generate local file path from URL following 118th congress structure"""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        # Expected structure: BILLS/118/1/hr/BILLS-118hr23ih.xml
        clean_parts = [part for part in path_parts if part and not part.startswith('.')]

        # Create directory structure
        if len(clean_parts) >= 4:
            collection = clean_parts[0]  # BILLS
            congress = clean_parts[1]    # 118
            session = clean_parts[2]     # 1 or 2
            bill_type = clean_parts[3]   # hr, s, hjres, etc.
            filename = clean_parts[-1]   # actual filename
            
            # Validate this is 118th congress (extract from filename as backup)
            if congress != str(self.congress_number):
                # Try to extract congress number from filename as fallback
                if filename and f"BILLS-{self.congress_number}" in filename:
                    # Filename contains correct congress, continue
                    pass
                else:
                    raise ValueError(f"URL does not target {self.congress_number}th Congress")
                
            # Build path
            directory_path = base_dir / collection / congress / session / bill_type
            return directory_path / filename
        else:
            # Fallback for unexpected structure
            self.logger.warning(f"Unexpected URL structure: {url}")
            return base_dir / "misc" / Path(parsed.path).name

    def _download_file(self, url: str, base_dir: Path, retry_count: int = 3) -> Dict[str, Any]:
        """
        Download a single file with enhanced duplicate prevention and retry logic

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
            'duration': 0.0,
            'checksum': ""
        }
        start_time = time.time()

        # Check if already downloaded with checksum verification
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

                        # Verify file integrity and calculate checksum
                        if local_path.exists():
                            file_size = local_path.stat().st_size
                            checksum = self._calculate_file_checksum(local_path)
                            
                            result['size'] = file_size
                            result['checksum'] = checksum
                            result['status'] = 'completed'
                            result['duration'] = time.time() - start_time

                            # Check for duplicates using checksum
                            with self.lock:
                                if checksum in self.file_checksums.values():
                                    # Duplicate found, remove this file
                                    local_path.unlink()
                                    result['status'] = 'skipped'
                                    result['error'] = "Duplicate content (checksum match)"
                                    self.skipped_files += 1
                                    self.logger.warning(f"Duplicate detected and removed: {url}")
                                    return result
                                
                                # Add to tracking
                                self.downloaded_files.add(url)
                                self.file_checksums[url] = checksum

                            self.logger.info(f"✅ Downloaded {url} ({file_size} bytes, {checksum[:8]}..., {result['duration']:.2f}s)")
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


    def _discover_available_congresses(self) -> List[int]:
        """
        Discover which congress numbers are available in the bulk data repository
        
        Returns:
            List of available congress numbers
        """
        available_congresses = []
        
        self.logger.info("Discovering available congress numbers...")
        
        # Check the base BILLS directory for available congress numbers
        try:
            xml_url = "https://www.govinfo.gov/bulkdata/xml/BILLS"
            response = self.session.get(xml_url, headers={'Accept': 'application/xml'})
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                # Look for folder elements that contain congress numbers
                for folder_elem in root.findall('.//folder'):
                    folder_name = folder_elem.text
                    if folder_name and folder_name.isdigit():
                        congress_num = int(folder_name)
                        if 100 <= congress_num <= 120:  # Reasonable range
                            available_congresses.append(congress_num)
                            
                self.logger.info(f"Available congress numbers: {sorted(available_congresses)}")
                
        except Exception as e:
            self.logger.error(f"Error discovering congress numbers: {str(e)}")
            
        return sorted(available_congresses)

    def _get_118th_congress_urls(self) -> List[str]:
        """
        Get all file URLs for the 118th Congress with fallback to other recent congresses

        Returns:
            List of file URLs for available congress data
        """
        file_urls = []
        
        # First, discover available congresses
        available_congresses = self._discover_available_congresses()
        
        # Check if 118th Congress is available
        if self.congress_number in available_congresses:
            target_congresses = [self.congress_number]
            self.logger.info(f"118th Congress found in available data!")
        else:
            # Use the most recent available congresses as fallback
            recent_congresses = [c for c in available_congresses if c >= 115]
            if recent_congresses:
                target_congresses = [max(recent_congresses)]  # Use the most recent
                self.logger.warning(f"118th Congress not found. Using most recent available: {target_congresses[0]}th Congress")
            else:
                self.logger.error("No recent congress data available")
                return []

        # Process each target congress
        for congress in target_congresses:
            self.logger.info(f"Processing {congress}th Congress data...")
            
            # Target both sessions
            for session in ['1', '2']:
                self.logger.info(f"Scanning {congress}th Congress, Session {session}...")
                
                # Check each bill type
                for bill_type in self.bill_types.keys():
                    try:
                        # Try XML endpoint first
                        xml_url = f"https://www.govinfo.gov/bulkdata/xml/BILLS/{congress}/{session}/{bill_type}"
                        self.logger.debug(f"Checking XML endpoint: {xml_url}")
                        
                        response = self.session.get(xml_url, headers={'Accept': 'application/xml'})
                        
                        if response.status_code == 200:
                            # Parse XML to extract file URLs
                            root = ET.fromstring(response.content)
                            
                            # Find all file elements
                            session_files = 0
                            for file_elem in root.findall('.//file'):
                                # Get filename from <name> element
                                name_elem = file_elem.find('name')
                                if name_elem is not None:
                                    file_path = name_elem.text
                                    if file_path and file_path.endswith(('.xml', '.xsl', '.xsd')):
                                        # Construct full URL
                                        base_url = f"https://www.govinfo.gov/bulkdata/BILLS/{congress}/{session}/{bill_type}/"
                                        full_url = urljoin(base_url, file_path)
                                        file_urls.append(full_url)
                                        session_files += 1
                                        self.logger.debug(f"Found file: {full_url}")
                            
                            self.logger.info(f"Found {session_files} files in {bill_type}/{session}")

                        else:
                            self.logger.debug(f"XML endpoint not available for {bill_type}/{session}: HTTP {response.status_code}")
                            
                            # Try JSON endpoint as fallback
                            json_url = f"https://www.govinfo.gov/bulkdata/json/BILLS/{congress}/{session}/{bill_type}"
                            response = self.session.get(json_url, headers={'Accept': 'application/json'})
                            
                            if response.status_code == 200:
                                data = response.json()
                                session_files = 0
                                if isinstance(data, list):
                                    for item in data:
                                        if isinstance(item, dict) and 'path' in item:
                                            file_path = item['path']
                                            if file_path.endswith(('.xml', '.xsl', '.xsd')):
                                                base_url = f"https://www.govinfo.gov/bulkdata/BILLS/{congress}/{session}/{bill_type}/"
                                                full_url = urljoin(base_url, file_path)
                                                file_urls.append(full_url)
                                                session_files += 1
                                elif isinstance(data, dict) and 'files' in data:
                                    for file_info in data['files']:
                                        if 'path' in file_info:
                                            file_path = file_info['path']
                                            if file_path.endswith(('.xml', '.xsl', '.xsd')):
                                                base_url = f"https://www.govinfo.gov/bulkdata/BILLS/{congress}/{session}/{bill_type}/"
                                                full_url = urljoin(base_url, file_path)
                                                file_urls.append(full_url)
                                                session_files += 1
                                
                                self.logger.info(f"Found {session_files} files in {bill_type}/{session} (JSON)")

                    except Exception as e:
                        self.logger.error(f"Error fetching {bill_type}/{session}: {str(e)}")

        # Remove duplicates and sort
        file_urls = list(set(file_urls))
        file_urls.sort()
        
        self.logger.info(f"Total files found: {len(file_urls)}")
        return file_urls

    def download_118th_congress(self, base_dir: Optional[Path] = None, 
                              max_workers: int = 15, include_xsl: bool = True) -> Dict[str, Any]:
        """
        Download all 118th Congress files

        Args:
            base_dir: Base directory for downloads (default: data/govinfo)
            max_workers: Maximum concurrent workers (12-15 recommended)
            include_xsl: Include XSL schema files

        Returns:
            Dictionary with download statistics
        """
        if base_dir is None:
            base_dir = Path(self.data_directory)

        self.logger.info(f"Starting 118th Congress download")
        self.logger.info(f"Base directory: {base_dir}")
        self.logger.info(f"Max workers: {max_workers}")
        self.logger.info(f"Include XSL files: {include_xsl}")

        # Reset statistics
        self.total_files = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_files = 0
        self.total_bytes = 0
        self.start_time = time.time()

        # Load existing downloads
        self._load_tracking_file()

        # Get all file URLs for 118th Congress
        self.logger.info(f"Discovering 118th Congress files...")
        file_urls = self._get_118th_congress_urls()

        # Filter for XSL files if requested
        if not include_xsl:
            file_urls = [url for url in file_urls if not url.endswith(('.xsl', '.xsd'))]

        self.total_files = len(file_urls)
        self.logger.info(f"Found {self.total_files} files to download")

        if not file_urls:
            self.logger.warning("No 118th Congress files found")
            return self._get_stats()

        # Process files concurrently
        self.logger.info(f"Starting concurrent download with {max_workers} workers...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self._download_file, url, base_dir): url
                for url in file_urls
            }

            completed = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                completed += 1
                
                # Progress reporting
                if completed % 50 == 0 or completed == self.total_files:
                    progress = (completed / self.total_files) * 100
                    self.logger.info(f"Progress: {completed}/{self.total_files} ({progress:.1f}%)")

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


    def _get_stats(self) -> Dict[str, Any]:
        """Get current download statistics"""
        duration = time.time() - self.start_time if self.start_time else 0

        return {
            'congress': self.congress_number,
            'total_files': self.total_files,
            'successful_downloads': self.successful_downloads,
            'failed_downloads': self.failed_downloads,
            'skipped_files': self.skipped_files,
            'total_bytes': self.total_bytes,
            'duration': duration,
            'speed': self.total_bytes / duration if duration > 0 else 0,
            'failed_urls': list(self.failed_urls)
        }

    def print_summary(self, stats: Dict[str, Any]) -> None:
        """Print comprehensive download summary"""
        duration = stats['duration']
        speed_mb = stats['speed'] / (1024 * 1024) if stats['speed'] > 0 else 0

        print("\n" + "="*70)
        print("GOVINFO 118TH CONGRESS BULK DOWNLOAD SUMMARY")
        print("="*70)
        print(f"Congress: {stats['congress']}th")
        print(f"Total Files Processed: {stats['total_files']}")
        print(f"Successful Downloads: {stats['successful_downloads']}")
        print(f"Failed Downloads: {stats['failed_downloads']}")
        print(f"Skipped Files (Duplicates): {stats['skipped_files']}")
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

        print("="*70)

def main():
    """Main entry point for 118th Congress downloader"""
    import argparse

    parser = argparse.ArgumentParser(description="GovInfo 118th Congress Bulk Data Downloader")
    parser.add_argument('--workers', type=int, default=15, 
                       help="Number of concurrent workers (12-15 recommended)")
    parser.add_argument('--output', help="Output directory (default: data/govinfo)")
    parser.add_argument('--no-xsl', action='store_false', dest='include_xsl', 
                       help="Exclude XSL schema files")
    parser.add_argument('--resume', action='store_true', 
                       help="Resume previous download session")

    args = parser.parse_args()

    # Validate worker count
    if not 10 <= args.workers <= 15:
        print("Warning: Worker count should be between 10-15 for optimal performance")

    # Initialize downloader
    downloader = GovInfo118thCongressDownloader()

    if args.resume:
        downloader.logger.info("Resuming previous 118th Congress download session")
        downloader._load_tracking_file()

    # Start download
    output_dir = Path(args.output) if args.output else None
    stats = downloader.download_118th_congress(
        base_dir=output_dir,
        max_workers=args.workers,
        include_xsl=args.include_xsl
    )
    
    # Print comprehensive summary
    downloader.print_summary(stats)

if __name__ == "__main__":
    main()