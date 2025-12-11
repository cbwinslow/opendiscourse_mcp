"""Main ingestion logic for govinfo.gov bulk data."""
import asyncio
import logging
from pathlib import Path

import aiofiles
import aiohttp
from tqdm import tqdm

from .config import (
    BASE_URL,
    CHUNK_SIZE,
    CONGRESS_SESSIONS,
    DOCUMENT_TYPES,
    LOG_LEVEL,
    MAX_RETRIES,
    OUTPUT_DIR,
    RATE_LIMIT,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    VALIDATE_XML,
    WORKERS,
)
from .rate_limiter import RateLimiter
from .xml_validator import XMLValidator

# Set up logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class GovInfoIngestor:
    """Handles downloading and processing of govinfo.gov bulk data."""

    def __init__(
        self,
        output_dir: Path = OUTPUT_DIR,
        workers: int = WORKERS,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        rate_limit: int = RATE_LIMIT,
        chunk_size: int = CHUNK_SIZE,
        validate_xml: bool = VALIDATE_XML,
    ):
        """Initialize the ingestor with configuration.

        Args:
            output_dir: Directory to save downloaded files
            workers: Number of parallel downloads
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            rate_limit: Maximum requests per second
            chunk_size: Chunk size for downloads in bytes
            validate_xml: Whether to validate XML against schemas
        """
        self.output_dir = Path(output_dir)
        self.workers = workers
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        self.chunk_size = chunk_size
        self.validate_xml = validate_xml
        self.semaphore = asyncio.Semaphore(workers)

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(rate_limit)

        # Initialize XML validator if needed
        self.validator = XMLValidator() if validate_xml else None

        # Map document types to schema names
        self.schema_map = {
            "BILLS": "bills",
            "BILLSTATUS": "billstatus",
            "PLAW": "plaw",
            "STATUTE": "statute",
            "FR": "federalregister",
            "CREC": "crec",
        }

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def validate_downloaded_file(self, file_path: Path, doc_type: str) -> bool:
        """Validate a downloaded XML file against its schema.

        Args:
            file_path: Path to the downloaded file
            doc_type: Document type for schema lookup

        Returns:
            bool: True if valid, False otherwise
        """
        if not self.validator or doc_type not in self.schema_map:
            return True

        try:
            content = file_path.read_text(encoding="utf-8")
            schema_name = self.schema_map[doc_type]
            is_valid, errors = self.validator.validate_xml(content, schema_name)

            if not is_valid:
                logger.error(f"XML validation failed for {file_path}: {errors[:3]}")
                if len(errors) > 3:
                    logger.error(f"... and {len(errors) - 3} more validation errors")
                return False

            return True

        except Exception as e:
            logger.error(f"Error during XML validation for {file_path}: {str(e)}")
            return False

    async def download_file(
        self,
        session: aiohttp.ClientSession,
        url: str,
        output_path: Path,
        doc_type: str,
        retries: int = 0,
    ) -> bool:
        """Download a single file with retries and validation."""
        if output_path.exists():
            logger.debug(f"File exists, skipping: {output_path}")
            return True

        async with self.semaphore:
            for attempt in range(retries + 1):
                try:
                    # Apply rate limiting
                    await self.rate_limiter.acquire()

                    # Make the request
                    async with session.get(url, timeout=self.timeout) as response:
                        if response.status == 200:
                            # Create parent directory if it doesn't exist
                            output_path.parent.mkdir(parents=True, exist_ok=True)

                            # Download the file
                            async with aiofiles.open(output_path, "wb") as f:
                                await f.write(await response.read())

                            # Validate if needed
                            if self.validate_xml and doc_type in self.schema_map:
                                is_valid = await self.validate_downloaded_file(
                                    output_path, doc_type
                                )
                                if not is_valid:
                                    output_path.unlink()  # Remove invalid file
                                    logger.error(
                                        f"Removed invalid XML file: {output_path}"
                                    )
                                    return False

                            logger.debug(f"Downloaded and validated: {output_path}")
                            return True

                        elif response.status == 404:
                            logger.warning(f"Not found (404): {url}")
                            return False
                        else:
                            logger.warning(
                                f"Failed to download {url}: {response.status}"
                            )

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(
                        f"Error downloading {url} (attempt {attempt + 1}): {e}"
                    )
                    if attempt < retries:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                except Exception as e:
                    logger.error(f"Unexpected error downloading {url}: {e}")
                    return False

        return False

    async def get_document_list(
        self,
        session: aiohttp.ClientSession,
        congress: int,
        doc_type: str,
    ) -> list[str]:
        """Recursively retrieve all XML file URLs for a given congress and document type.
        Uses govinfo bulkdata XML/JSON directory listings.
        """
        base = f"{BASE_URL}/{doc_type}/{congress}/"

        async def list_dir(url: str, depth: int = 0) -> list[str]:
            files: list[str] = []
            try:
                # Prefer XML listing endpoint
                listing_xml = url.replace("/bulkdata/", "/bulkdata/xml/")
                async with session.get(
                    listing_xml,
                    timeout=self.timeout,
                    headers={"Accept": "application/xml,*/*"},
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        try:
                            import xml.etree.ElementTree as ET

                            root = ET.fromstring(text)
                            for f in root.findall(".//file"):
                                link_el = f.find("link")
                                is_folder_el = f.find("folder")
                                link = link_el.text if link_el is not None else None
                                is_folder = (
                                    (is_folder_el.text.lower() == "true")
                                    if is_folder_el is not None
                                    else False
                                )
                                if not link:
                                    continue
                                if is_folder:
                                    # Recurse into subdirectory
                                    sub_files = await list_dir(link, depth + 1)
                                    files.extend(sub_files)
                                else:
                                    if link.lower().endswith(".xml"):
                                        files.append(link)
                        except Exception:
                            # Fall back to JSON listing endpoint
                            listing_json = url.replace("/bulkdata/", "/bulkdata/json/")
                            async with session.get(
                                listing_json,
                                timeout=self.timeout,
                                headers={"Accept": "application/json"},
                            ) as jresp:
                                if jresp.status == 200:
                                    data = await jresp.json()

                                    def walk(node) -> list[str]:
                                        acc: list[str] = []
                                        if isinstance(node, dict):
                                            # JSON formats vary; look for keys
                                            if (
                                                node.get("folder") is True
                                                and "link" in node
                                            ):
                                                acc.extend(walk(node.get("files", [])))
                                            elif (
                                                node.get("folder") is False
                                                and "link" in node
                                            ):
                                                link = node["link"]
                                                if isinstance(
                                                    link, str
                                                ) and link.lower().endswith(".xml"):
                                                    acc.append(link)
                                            else:
                                                for v in node.values():
                                                    acc.extend(walk(v))
                                        elif isinstance(node, list):
                                            for item in node:
                                                acc.extend(walk(item))
                                        return acc

                                    files.extend(walk(data))
                                else:
                                    logger.warning(
                                        f"Directory listing not available: {listing_json} ({jresp.status})"
                                    )
                    else:
                        logger.warning(
                            f"Directory listing not available: {listing_xml} ({resp.status})"
                        )
            except Exception as e:
                logger.error(f"Error listing {url}: {e}")
            return files

        return await list_dir(base)

    async def process_document_type(
        self,
        session: aiohttp.ClientSession,
        congress: int,
        doc_type: str,
    ) -> int:
        """Process all documents of a specific type for a given congress."""
        logger.info(f"Processing {doc_type} for Congress {congress}")

        # Get list of documents
        documents = await self.get_document_list(session, congress, doc_type)
        if not documents:
            logger.warning(f"No documents found for {doc_type} in Congress {congress}")
            return 0

        # Download documents
        tasks = []
        for doc_url in documents:
            # Derive filename from URL
            filename = doc_url.rstrip("/").split("/")[-1]
            output_path = self.output_dir / str(congress) / doc_type / filename
            tasks.append(
                self.download_file(
                    session, doc_url, output_path, doc_type, retries=self.max_retries
                )
            )

        # Run downloads in parallel with progress bar
        results = []
        for f in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc=f"{doc_type}-{congress}",
            unit="file",
        ):
            results.append(await f)

        success_count = sum(1 for r in results if r)
        logger.info(
            f"Processed {success_count}/{len(documents)} {doc_type} files "
            f"for Congress {congress}"
        )
        return success_count

    async def process_congress(
        self,
        session: aiohttp.ClientSession,
        congress: int,
        doc_types: list[str] | None = None,
    ) -> dict[str, int]:
        """Process all document types for a specific congress."""
        if doc_types is None:
            doc_types = DOCUMENT_TYPES

        results = {}
        for doc_type in doc_types:
            count = await self.process_document_type(session, congress, doc_type)
            results[doc_type] = count

        return results

    async def run(
        self,
        congresses: list[int] | None = None,
        doc_types: list[str] | None = None,
    ) -> dict[int, dict[str, int]]:
        """Run the ingestion process."""
        if congresses is None:
            congresses = CONGRESS_SESSIONS

        results = {}
        async with aiohttp.ClientSession() as session:
            for congress in congresses:
                results[congress] = await self.process_congress(
                    session, congress, doc_types
                )

        return results


async def ingest_congress_data(
    congress: int,
    doc_types: list[str] | None = None,
    output_dir: Path | None = None,
    workers: int = WORKERS,
) -> dict[str, int]:
    """
    Ingest data for a specific congress.

    Args:
        congress: The congress number (e.g., 115)
        doc_types: List of document types to download (None for all)
        output_dir: Directory to save downloaded files
        workers: Number of parallel downloads

    Returns:
        Dictionary with counts of downloaded files by document type
    """
    ingestor = GovInfoIngestor(output_dir=output_dir or OUTPUT_DIR, workers=workers)

    async with aiohttp.ClientSession() as session:
        return await ingestor.process_congress(session, congress, doc_types)


async def ingest_all_congresses(
    congresses: list[int] | None = None,
    doc_types: list[str] | None = None,
    output_dir: Path | None = None,
    workers: int = WORKERS,
) -> dict[int, dict[str, int]]:
    """
    Ingest data for multiple congresses.

    Args:
        congresses: List of congress numbers (None for all)
        doc_types: List of document types to download (None for all)
        output_dir: Directory to save downloaded files
        workers: Number of parallel downloads per congress

    Returns:
        Nested dictionary with counts of downloaded files by congress and document type
    """
    ingestor = GovInfoIngestor(output_dir=output_dir or OUTPUT_DIR, workers=workers)

    return await ingestor.run(congresses, doc_types)


def main():
    """Command-line entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Download bulk data from govinfo.gov")
    parser.add_argument(
        "--congress",
        type=int,
        nargs="+",
        help="Congress numbers to download (default: all 113-119)",
    )
    parser.add_argument(
        "--doc-types",
        nargs="+",
        choices=DOCUMENT_TYPES,
        help=f"Document types to download (default: all: {', '.join(DOCUMENT_TYPES)})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=WORKERS,
        help=f"Number of parallel downloads (default: {WORKERS})",
    )
    parser.add_argument(
        "--log-level",
        default=LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=args.log_level)

    # Run the ingestion
    asyncio.run(
        ingest_all_congresses(
            congresses=args.congress,
            doc_types=args.doc_types,
            output_dir=args.output,
            workers=args.workers,
        )
    )


if __name__ == "__main__":
    main()
