"""
GovInfo Bulk Data Ingestion System

This module provides tools for downloading and processing bulk data from govinfo.gov
for US Congress sessions 113-119.
"""

__version__ = "0.1.0"
__all__ = [
    "ingest_congress_data",
    "ingest_all_congresses",
    "RateLimiter",
    "GovInfoIngestor"
]

from .ingestor import ingest_congress_data, ingest_all_congresses, GovInfoIngestor
from .rate_limiter import RateLimiter
