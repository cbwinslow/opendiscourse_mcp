
import os
import requests
import logging
import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base URL for the govinfo bulk data repository
BASE_URL = "https://www.govinfo.gov"

# Collections to download
COLLECTIONS = [
    "BILLS",
    "BILLSTATUS",
    "BILLSUM",
    "CFR",
    "FR",
    "PLAW",
    "STATUTE"
]

# Directory to store the downloaded data
DATA_DIR = "govinfo_data"

# Number of threads to use for downloading
MAX_WORKERS = 10

def get_html_listing(url):
    """Fetches an HTML page and parses it to find file links."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        for a in soup.find_all('a'):
            href = a.get('href')
            if href and (href.endswith('.zip') or href.endswith('.xml')):
                # Construct absolute URL if the href is relative
                full_url = urljoin(url, href)
                links.append(full_url)
        return links
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching HTML listing from {url}: {e}")
        return None

def download_file(url, directory, filename):
    """Downloads a file from a URL and saves it to a directory."""
    filepath = os.path.join(directory, filename)
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded {filename} to {directory}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading {filename} from {url}: {e}")

def process_collection(collection):
    """Processes a single collection: gets listing and downloads files."""
    collection_dir = os.path.join(DATA_DIR, collection)
    if not os.path.exists(collection_dir):
        os.makedirs(collection_dir)
        logging.info(f"Created directory: {collection_dir}")

    # We are now fetching the HTML page for the collection
    collection_url = f"{BASE_URL}/bulkdata/{collection}"
    logging.info(f"Fetching file list for collection: {collection}")
    file_urls = get_html_listing(collection_url)

    if file_urls:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for file_url in file_urls:
                file_name = file_url.split("/")[-1]
                executor.submit(download_file, file_url, collection_dir, file_name)
    else:
        logging.warning(f"No files found or error in listing for collection: {collection}")

def main():
    """Main function to download the govinfo bulk data."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.info(f"Created directory: {DATA_DIR}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(COLLECTIONS)) as executor:
        executor.map(process_collection, COLLECTIONS)

if __name__ == "__main__":
    main()
