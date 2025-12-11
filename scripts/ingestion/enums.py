"""Enums and constants for govinfo.gov data ingestion."""

from enum import Enum
from pathlib import Path

class DocumentType(Enum):
    """Document types available from govinfo.gov bulk data."""

    BILLS = "BILLS"
    BILLSTATUS = "BILLSTATUS"
    PLAW = "PLAW"
    STATUTE = "STATUTE"
    FR = "FR"
    CREC = "CREC"

    @classmethod
    def all_types(cls) -> list[str]:
        """Get all document types as strings."""
        return [doc_type.value for doc_type in cls]

    @classmethod
    def get_type(cls, value: str) -> "DocumentType":
        """Get DocumentType enum from string value."""
        for doc_type in cls:
            if doc_type.value == value:
                return doc_type
        raise ValueError(f"Unknown document type: {value}")


class CongressSession:
    """Congress session information and utilities."""

    # Current available congress sessions (113th to 123rd)
    AVAILABLE_SESSIONS = list(range(113, 124))

    # Historical congress sessions for reference
    HISTORICAL_SESSIONS = list(range(93, 124))  # 93rd to 123rd Congress

    @classmethod
    def get_available_sessions(cls) -> list[int]:
        """Get list of currently available congress sessions."""
        return cls.AVAILABLE_SESSIONS.copy()

    @classmethod
    def get_historical_sessions(cls) -> list[int]:
        """Get list of all historical congress sessions."""
        return cls.HISTORICAL_SESSIONS.copy()

    @classmethod
    def is_valid_session(cls, session: int) -> bool:
        """Check if a congress session is valid."""
        return session in cls.AVAILABLE_SESSIONS

    @classmethod
    def get_session_name(cls, session: int) -> str:
        """Get formatted congress session name."""
        return f"{session}th Congress"

    @classmethod
    def get_year_range(cls, session: int) -> tuple[int, int]:
        """Get approximate year range for a congress session."""
        # Congress sessions typically span 2 years
        # 113th Congress: 2013-2014, 114th: 2015-2016, etc.
        base_year = 2011 + (session - 112) * 2
        return (base_year, base_year + 1)


class IngestionConfig:
    """Configuration constants for data ingestion."""

    # Worker configuration
    DEFAULT_WORKERS = 50
    MAX_WORKERS = 100
    MIN_WORKERS = 1

    # Rate limiting
    DEFAULT_RATE_LIMIT = 10  # requests per second
    MAX_RATE_LIMIT = 50

    # Timeouts and retries
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    # File handling
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks

    # Validation
    VALIDATE_XML_BY_DEFAULT = True

    # Logging
    DEFAULT_LOG_LEVEL = "INFO"
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# Commonly used combinations
DEFAULT_CONGRESSES = CongressSession.get_available_sessions()
DEFAULT_DOCUMENT_TYPES = DocumentType.all_types()

# Test combinations (smaller subset for testing)
TEST_CONGRESSES = [118, 119]
TEST_DOCUMENT_TYPES = ["STATUTE", "BILLS"]

# Production combinations (full dataset)
PRODUCTION_CONGRESSES = CongressSession.get_available_sessions()
PRODUCTION_DOCUMENT_TYPES = DocumentType.all_types()
