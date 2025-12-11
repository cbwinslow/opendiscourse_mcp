"""Configuration for govinfo.gov bulk data ingestion."""
import logging
from pathlib import Path
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for govinfo bulk data
BASE_URL = "https://www.govinfo.gov/bulkdata"

# Congress sessions to process (113th to 119th)
CONGRESS_SESSIONS = list(range(113, 120))

# Document types to download
DOCUMENT_TYPES = [
    "BILLS",
    "BILLSTATUS",
    "PLAW",  # Public and Private Laws
    "STATUTE",
    "FR",    # Federal Register
    "CREC",  # Congressional Record
]

# Output directory (can be overridden by environment variable)
OUTPUT_DIR = Path(os.getenv("GOVINFO_DATA_DIR", "govinfo_data"))

# Performance settings
WORKERS = int(os.getenv("GOVINFO_WORKERS", "10"))  # Number of parallel downloads
RATE_LIMIT = int(os.getenv("GOVINFO_RATE_LIMIT", "10"))  # Requests per second
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming downloads

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 30

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Validation settings
VALIDATE_XML = os.getenv("GOVINFO_VALIDATE_XML", "true").lower() == "true"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "ingestion.log"

# File patterns for different document types
FILE_PATTERNS = {
    "BILLS": "BILLS-{congress}{bill_type}{bill_number}{version}.xml",
    "BILLSTATUS": "BILLSTATUS-{congress}{bill_type}{bill_number}.xml",
    "PLAW": "PLAW-{congress}publ{pub_number}.xml",
    "STATUTE": "STATUTE-{volume}pg{page}.xml",
    "FR": "FR-{year}-{month}-{day}.xml",
    "CREC": "CREC-{year}-{month}-{day}.xml",
}

# XSD schemas for validation (relative to project root)
SCHEMA_PATHS = {
    "BILLS": "schemas/bill.xsd",
    "BILLSTATUS": "schemas/billstatus.xsd",
    "PLAW": "schemas/plaw.xsd",
    "STATUTE": "schemas/statute.xsd",
    "FR": "schemas/fr.xsd",
    "CREC": "schemas/crec.xsd",
}

def get_document_path(congress: int, doc_type: str, **kwargs) -> Path:
    """
    Get the output path for a document.
    
    Args:
        congress: The congress number (e.g., 115)
        doc_type: Document type (e.g., 'BILLS', 'PLAW')
        **kwargs: Additional format arguments for the filename pattern
        
    Returns:
        Path where the document should be saved
    """
    doc_dir = OUTPUT_DIR / str(congress) / doc_type
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    if doc_type in FILE_PATTERNS:
        try:
            filename = FILE_PATTERNS[doc_type].format(congress=congress, **kwargs)
            return doc_dir / filename
        except (KeyError, IndexError) as e:
            logger.warning(f"Error formatting filename for {doc_type}: {e}")
    
    # Fallback naming if pattern formatting fails or no pattern exists
    return doc_dir / f"{doc_type}_{kwargs.get('id', 'unknown')}.xml"
