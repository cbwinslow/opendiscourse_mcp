#!/usr/bin/env python3
"""
Simple 118th Congress File Downloader
Downloads a sample of 118th Congress files to expected location for processing
"""

import os
import requests
import time
from pathlib import Path
from urllib.parse import urlparse
import concurrent.futures
import json

def download_file(url: str, base_dir: Path) -> dict:
    """Download a single file"""
    result = {'url': url, 'status': 'pending', 'error': None}
    
    try:
        # Parse URL to create local path
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Expected: BILLS/118/1/hr/BILLS-118hr366eh.xml
        if len(path_parts) >= 5:
            collection = path_parts[1]  # BILLS
            congress = path_parts[2]     # 118
            session = path_parts[3]      # 1 or 2
            bill_type = path_parts[4]    # hr, s, etc.
            filename = path_parts[-1]     # actual filename
            
            # Create directory structure
            local_dir = base_dir / collection / "bulkdata" / collection / congress / session / bill_type
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / filename
            
            # Download file
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                result['status'] = 'completed'
                result['local_path'] = str(local_path)
                result['size'] = len(response.content)
                print(f"✅ Downloaded {filename} ({len(response.content)} bytes)")
            else:
                result['status'] = 'failed'
                result['error'] = f"HTTP {response.status_code}"
                print(f"❌ Failed to download {filename}: HTTP {response.status_code}")
        else:
            result['status'] = 'failed'
            result['error'] = "Invalid URL structure"
            
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        print(f"❌ Error downloading {url}: {str(e)}")
    
    return result

def main():
    """Download sample 118th Congress files"""
    
    # Sample URLs from tracking file
    sample_urls = [
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/hr/BILLS-118hr366eh.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/s/BILLS-118s2403is.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/2/s/BILLS-118s4942rs.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/hr/BILLS-118hr4709ih.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/s/BILLS-118s432is.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/hr/BILLS-118hr1812ih.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/s/BILLS-118s3447is.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/hr/BILLS-118hr3854ih.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/1/hr/BILLS-118hr5112ih.xml",
        "https://www.govinfo.gov/bulkdata/BILLS/118/2/s/BILLS-118s4073is.xml"
    ]
    
    base_dir = Path("govinfo_data")
    base_dir.mkdir(exist_ok=True)
    
    print(f"Downloading {len(sample_urls)} sample 118th Congress files...")
    print(f"Base directory: {base_dir.absolute()}")
    
    # Download files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(download_file, url, base_dir): url
            for url in sample_urls
        }
        
        completed = 0
        successful = 0
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            completed += 1
            
            try:
                result = future.result()
                if result['status'] == 'completed':
                    successful += 1
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
            
            print(f"Progress: {completed}/{len(sample_urls)}")
    
    print(f"\nDownload complete: {successful}/{len(sample_urls)} files successful")
    
    # Verify files exist
    downloaded_files = list(base_dir.rglob("BILLS-118*.xml"))
    print(f"Files in target directory: {len(downloaded_files)}")
    
    for f in downloaded_files[:5]:  # Show first 5
        print(f"  - {f.relative_to(base_dir)}")

if __name__ == "__main__":
    main()