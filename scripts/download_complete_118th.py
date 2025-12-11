#!/usr/bin/env python3
"""
Complete 118th Congress XML Downloader
Downloads all 118th Congress XML files using direct URL enumeration
"""

import os
import requests
import time
import threading
import concurrent.futures
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin
from datetime import datetime

class Complete118thDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': "OpenDiscourse-MCP/1.0 Complete-118th-Downloader",
            'Accept': 'application/xml,text/xml,*/*'
        })
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("logs/complete_118th_downloader.log", mode='a', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger("Complete118thDownloader")
        
        # Statistics
        self.total_files = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.total_bytes = 0
        self.start_time = time.time()
        
        # Base directory
        self.base_dir = Path("govinfo_data")
        
        # Thread safety
        self.lock = threading.Lock()
        self.downloaded_files: Set[str] = set()

    def get_all_118th_urls(self) -> List[str]:
        """Generate all possible 118th Congress URLs"""
        urls = []
        
        # Bill types and their ranges
        bill_configs = [
            # House bills (hr) - typically 4000-9000 range
            {'type': 'hr', 'session': 1, 'start': 1, 'end': 5000},
            {'type': 'hr', 'session': 2, 'start': 5001, 'end': 11000},
            
            # Senate bills (s) - typically 2000-4000 range  
            {'type': 's', 'session': 1, 'start': 1, 'end': 3000},
            {'type': 's', 'session': 2, 'start': 3001, 'end': 6000},
            
            # House joint resolutions (hjres)
            {'type': 'hjres', 'session': 1, 'start': 1, 'end': 200},
            {'type': 'hjres', 'session': 2, 'start': 201, 'end': 400},
            
            # Senate joint resolutions (sjres) 
            {'type': 'sjres', 'session': 1, 'start': 1, 'end': 100},
            {'type': 'sjres', 'session': 2, 'start': 101, 'end': 200},
            
            # House concurrent resolutions (hconres)
            {'type': 'hconres', 'session': 1, 'start': 1, 'end': 100},
            {'type': 'hconres', 'session': 2, 'start': 101, 'end': 200},
            
            # Senate concurrent resolutions (sconres)
            {'type': 'sconres', 'session': 1, 'start': 1, 'end': 50},
            {'type': 'sconres', 'session': 2, 'start': 51, 'end': 100},
        ]
        
        base_url = "https://www.govinfo.gov/bulkdata/BILLS/118"
        
        for config in bill_configs:
            bill_type = config['type']
            session = config['session']
            start_num = config['start']
            end_num = config['end']
            
            self.logger.info(f"Generating URLs for {bill_type} session {session}, bills {start_num}-{end_num}")
            
            for bill_num in range(start_num, end_num + 1):
                # Try different version suffixes
                for suffix in ['ih', 'is', 'eh', 'rh', 'rs', 'enr', 'rfs', 'pcs', 'es', 'ats']:
                    url = f"{base_url}/{session}/{bill_type}/BILLS-118{bill_type}{bill_num}{suffix}.xml"
                    urls.append(url)
        
        self.logger.info(f"Generated {len(urls)} total URLs for 118th Congress")
        return urls

    def download_file(self, url: str) -> Dict:
        """Download a single file"""
        result = {'url': url, 'status': 'pending', 'error': None}
        
        # Check if already downloaded
        with self.lock:
            if url in self.downloaded_files:
                result['status'] = 'skipped'
                result['error'] = "Already downloaded"
                return result
        
        try:
            # Parse URL to get local path
            parts = url.split('/')
            if len(parts) >= 8:
                collection = parts[4]  # BILLS
                congress = parts[5]     # 118
                session = parts[6]      # 1 or 2
                bill_type = parts[7]   # hr, s, etc.
                filename = parts[-1]     # BILLS-118hr366eh.xml
                
                # Create local directory structure
                local_dir = self.base_dir / collection / "bulkdata" / collection / congress / session / bill_type
                local_dir.mkdir(parents=True, exist_ok=True)
                local_path = local_dir / filename
                
                # Download file
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    with self.lock:
                        self.downloaded_files.add(url)
                        self.successful_downloads += 1
                        self.total_bytes += len(response.content)
                    
                    result['status'] = 'completed'
                    result['size'] = len(response.content)
                    result['local_path'] = str(local_path)
                    
                    if self.successful_downloads % 100 == 0:
                        self.logger.info(f"✅ Downloaded {self.successful_downloads} files ({self.total_bytes / (1024*1024):.1f} MB)")
                    
                else:
                    result['status'] = 'failed'
                    result['error'] = f"HTTP {response.status_code}"
                    
                    with self.lock:
                        self.failed_downloads += 1
                    
                    self.logger.debug(f"❌ Failed to download {url}: HTTP {response.status_code}")
                    
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            
            with self.lock:
                self.failed_downloads += 1
            
            self.logger.debug(f"❌ Error downloading {url}: {str(e)}")
        
        return result

    def download_all_files(self, max_workers: int = 10):
        """Download all files with concurrent processing"""
        urls = self.get_all_118th_urls()
        self.total_files = len(urls)
        
        self.logger.info(f"Starting download of {self.total_files} 118th Congress files")
        self.logger.info(f"Using {max_workers} concurrent workers")
        
        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.download_file, url): url
                for url in urls
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_url):
                completed += 1
                url = future_to_url[future]
                
                try:
                    result = future.result()
                    
                    if completed % 500 == 0 or completed == self.total_files:
                        progress = (completed / self.total_files) * 100
                        self.logger.info(f"Progress: {completed}/{self.total_files} ({progress:.1f}%) - Success: {self.successful_downloads}, Failed: {self.failed_downloads}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing {url}: {str(e)}")
                    with self.lock:
                        self.failed_downloads += 1
        
        # Final summary
        duration = time.time() - self.start_time
        speed_mb = self.total_bytes / duration / (1024 * 1024) if duration > 0 else 0
        
        self.logger.info("=" * 70)
        self.logger.info("118TH CONGRESS COMPLETE DOWNLOAD SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total URLs attempted: {self.total_files}")
        self.logger.info(f"Successful downloads: {self.successful_downloads}")
        self.logger.info(f"Failed downloads: {self.failed_downloads}")
        self.logger.info(f"Total data: {self.total_bytes / (1024*1024):.2f} MB")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info(f"Average speed: {speed_mb:.2f} MB/s")
        self.logger.info("=" * 70)
        
        return {
            'total_files': self.total_files,
            'successful_downloads': self.successful_downloads,
            'failed_downloads': self.failed_downloads,
            'total_bytes': self.total_bytes,
            'duration': duration,
            'speed_mb': speed_mb
        }

def main():
    """Main entry point"""
    downloader = Complete118thDownloader()
    
    print("Starting Complete 118th Congress Download")
    print("This will attempt to download ALL 118th Congress XML files")
    print("Estimated total: ~20,000 files")
    print()
    
    # Start download with moderate concurrency to avoid overwhelming the server
    stats = downloader.download_all_files(max_workers=8)
    
    print(f"\nDownload completed!")
    print(f"Success: {stats['successful_downloads']}/{stats['total_files']} files")
    print(f"Data downloaded: {stats['total_bytes'] / (1024*1024):.1f} MB")
    
    if stats['successful_downloads'] > 0:
        print("✅ Ready to process with: python3 scripts/process_118th_congress.py --data-dir govinfo_data")
    else:
        print("❌ No files downloaded. Check network connection or server availability.")

if __name__ == "__main__":
    main()