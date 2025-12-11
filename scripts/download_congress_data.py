
import os
import requests
import logging
import concurrent.futures
from urllib.parse import urljoin
import json
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base URL for the congress.gov API
BASE_URL = "https://api.congress.gov/v3/"

# API Key
API_KEY = "U71JFZEqNsiSranCdbrj4pZaobtoMtAnl18cIJc2"

# Bill types to download
BILL_TYPES = ['hr', 's']

# Directory to store the downloaded data
DATA_DIR = "congress_data"

# Number of threads to use for downloading
MAX_WORKERS = 50

def get_bills_for_congress(congress, bill_type):
    """Fetches all bills for a given congress and bill type."""
    all_bills = []
    limit = 250
    offset = 0
    while True:
        url = f"{BASE_URL}bill/{congress}/{bill_type}?api_key={API_KEY}&limit={limit}&offset={offset}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            bills = data.get('bills', [])
            all_bills.extend(bills)
            if len(bills) < limit:
                break
            offset += limit
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching bills from {url}: {e}")
            break
        except ValueError:
            logging.error(f"Error parsing JSON from {url}")
            break
    return all_bills

def download_bill_data(bill_url, directory):
    """Downloads the data for a single bill."""
    url = f"{bill_url}?api_key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        bill_number = data.get('bill', {}).get('number')
        if bill_number:
            filename = f"{bill_number}.json"
            filepath = os.path.join(directory, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            logging.info(f"Downloaded {filename} to {directory}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading bill data from {url}: {e}")
    except ValueError:
        logging.error(f"Error parsing JSON from {url}")

def main():
    """Main function to download the congress.gov bulk data."""
    parser = argparse.ArgumentParser(description="Download congress.gov bill data.")
    parser.add_argument("--congress", type=int, default=118,
                        help="The congress number to download data for (e.g., 117).")
    args = parser.parse_args()

    congress_num = args.congress

    if congress_num == 113:
        logging.warning("Skipping 113th Congress as requested.")
        return

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.info(f"Created directory: {DATA_DIR}")

    congress_dir = os.path.join(DATA_DIR, str(congress_num))
    if not os.path.exists(congress_dir):
        os.makedirs(congress_dir)
        logging.info(f"Created directory: {congress_dir}")

    bills_dir = os.path.join(congress_dir, 'bills')
    if not os.path.exists(bills_dir):
        os.makedirs(bills_dir)
        logging.info(f"Created directory: {bills_dir}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for bill_type in BILL_TYPES:
            logging.info(f"Fetching bills for {congress_num}th Congress, type: {bill_type}")
            bills = get_bills_for_congress(congress_num, bill_type)
            logging.info(f"Found {len(bills)} bills.")

            for bill in bills:
                bill_url = bill.get('url')
                if bill_url:
                    executor.submit(download_bill_data, bill_url, bills_dir)

if __name__ == "__main__":
    main()
