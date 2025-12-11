#!/usr/bin/env python3
import sys
import logging
from pathlib import Path

# Add project root to path to import config
sys.path.append(str(Path(__file__).parent.parent))

# Add scripts dir to path to import downloader (though it is in the same dir)
sys.path.append(str(Path(__file__).parent))

from govinfo_bulk_downloader import GovInfoBulkDownloader

def test_crawler():
    print("Initializing Downloader...")
    downloader = GovInfoBulkDownloader()
    
    # Test on a specific deep URL that should have files
    test_url = "https://www.govinfo.gov/bulkdata/BILLS/119/1/hconres/"
    collection = "BILLS"
    
    print(f"Testing crawler on: {test_url}")
    
    files = downloader._crawl_collection_recursive(test_url, collection, max_depth=2)
    
    print(f"\nFound {len(files)} files.")
    if files:
        print("First 5 files:")
        for f in files[:5]:
            print(f" - {f}")
            
    if len(files) > 0:
        print("\n✅ Crawler verification SUCCESS!")
        return True
    else:
        print("\n❌ Crawler verification FAILED (No files found)")
        return False

if __name__ == "__main__":
    test_crawler()
