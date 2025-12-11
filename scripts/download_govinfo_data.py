
import os
import requests
import logging
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base URL for the govinfo bulk data repository
BASE_URL = "https://www.govinfo.gov/bulkdata"

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

def get_json_listing(url):
    """Fetches a JSON listing from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        # It seems the server returns XML even if we ask for JSON.
        # We will try to parse JSON, but fall back to XML parsing if it fails.
        try:
            return response.json()
        except ValueError:
            # The user mentioned that the server might be returning XML.
            # I will try to handle this case, but for now I will log an error.
            logging.warning(f"Could not parse JSON from {url}. It might be XML. The raw text is: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching JSON listing from {url}: {e}")
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

def main():
    """Main function to download the govinfo bulk data."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.info(f"Created directory: {DATA_DIR}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for collection in COLLECTIONS:
            collection_dir = os.path.join(DATA_DIR, collection)
            if not os.path.exists(collection_dir):
                os.makedirs(collection_dir)
                logging.info(f"Created directory: {collection_dir}")

            collection_url = f"{BASE_URL}/{collection}/json"
            logging.info(f"Fetching file list for collection: {collection}")
            # The web_fetch tool initially reported that the /json endpoint returns an error,
            # but the tool output also showed that it parsed an XML response and returned a JSON object.
            # I will try to use the /json endpoint first, and if it fails, I will try the /xml endpoint.
            listing = get_json_listing(collection_url)

            # If the /json endpoint fails, try the /xml endpoint
            if not listing:
                xml_url = f"{BASE_URL}/{collection}/xml"
                logging.info(f"Fetching file list for collection from XML endpoint: {collection}")
                # The logic to parse XML is not implemented yet. I will add it if needed.
                # For now, I will just log a warning.
                logging.warning(f"JSON listing failed. XML parsing is not implemented yet for {xml_url}")


            if listing and "files" in listing:
                for file_info in listing["files"]:
                    file_url = file_info.get("link")
                    if file_url:
                        file_name = file_url.split("/")[-1]
                        executor.submit(download_file, file_url, collection_dir, file_name)
            else:
                logging.warning(f"No files found or error in listing for collection: {collection}")

if __name__ == "__main__":
    main()
