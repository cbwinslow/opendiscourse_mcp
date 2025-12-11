"""Command utilities for the ingestion system."""

import asyncio
import logging
from pathlib import Path

import aiohttp

from .xml_validator import XMLValidator

logger = logging.getLogger(__name__)

SCHEMA_URLS = {
    "bill": "https://www.govinfo.gov/bulkdata/xml/BILLS.xsd",
    "billstatus": "https://www.govinfo.gov/bulkdata/xml/BILLSTATUS.xsd",
    "plaw": "https://www.govinfo.gov/bulkdata/xml/PLAW.xsd",
    "statute": "https://www.govinfo.gov/bulkdata/xml/STATUTE.xsd",
    "fr": "https://www.govinfo.gov/bulkdata/xml/FR.xsd",
    "crec": "https://www.govinfo.gov/bulkdata/xml/CREC.xsd",
}


async def download_schemas(schema_dir: str | None = None) -> None:
    """Download all required XSD schemas from govinfo.gov.

    This function downloads XML schema definitions for all supported
    document types (BILLS, BILLSTATUS, PLAW, etc.) and caches them
    locally for validation.

    Args:
        schema_dir: Directory to save schemas. If None, defaults to
            'schemas' in the ingestion module directory.

    Raises:
        Exception: If schema download fails for multiple schemas.

    Example:
        >>> await download_schemas("/path/to/schemas")
        # Downloads all schemas to the specified directory
    """
    validator = XMLValidator(schema_dir)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, url in SCHEMA_URLS.items():
            tasks.append(validator.download_schema(session, url, name))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = sum(1 for r in results if r is True)
        logger.info(f"Downloaded {success}/{len(SCHEMA_URLS)} schemas successfully")

        # Log any failures
        for (name, url), result in zip(SCHEMA_URLS.items(), results, strict=False):
            if result is not True:
                logger.error(f"Failed to download schema {name} from {url}: {result}")


async def validate_xml_files(
    xml_dir: str, schema_name: str, schema_dir: str | None = None
) -> dict[str, int]:
    """Validate all XML files in a directory against a specific schema.

    This function scans a directory for XML files and validates each one
    against the specified XSD schema. It returns statistics about the
    validation process including counts of valid, invalid, and error files.

    Args:
        xml_dir: Directory containing XML files to validate.
        schema_name: Name of the schema to validate against (e.g., 'bill').
        schema_dir: Directory containing schemas. If None, defaults to
            'schemas' in the ingestion module directory.

    Returns:
        Dictionary with validation statistics:
        - 'total': Total number of XML files found
        - 'valid': Number of files that passed validation
        - 'invalid': Number of files that failed validation
        - 'errors': Number of files that had processing errors

    Raises:
        ValueError: If xml_dir does not exist.

    Example:
        >>> stats = await validate_xml_files("/data/xmls", "bill")
        >>> print(f"Validated {stats['total']} files, {stats['valid']} valid")
    """
    validator = XMLValidator(schema_dir)
    xml_path = Path(xml_dir)

    if not xml_path.exists():
        logger.error(f"XML directory does not exist: {xml_dir}")
        return {"total": 0, "valid": 0, "invalid": 0, "errors": 0}

    xml_files = list(xml_path.glob("*.xml"))
    if not xml_files:
        logger.warning(f"No XML files found in {xml_dir}")
        return {"total": 0, "valid": 0, "invalid": 0, "errors": 0}

    stats = {"total": len(xml_files), "valid": 0, "invalid": 0, "errors": 0}

    logger.info(f"Validating {len(xml_files)} XML files against schema: {schema_name}")

    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8")
            is_valid, errors = validator.validate_xml(content, schema_name)

            if is_valid:
                stats["valid"] += 1
            else:
                stats["invalid"] += 1
                logger.error(f"Invalid XML: {xml_file.name} - {errors[:1]}")

        except Exception as e:
            stats["errors"] += 1
            logger.error(f"Error validating {xml_file.name}: {str(e)}")

    logger.info(
        f"Validation complete: {stats['valid']} valid, {stats['invalid']} invalid, {stats['errors']} errors"
    )
    return stats


def list_available_schemas(schema_dir: str | None = None) -> list[str]:
    """List all available XSD schemas in the schema directory.

    This function scans the schema directory and returns a list of
    available schema names (without the .xsd extension). Useful for
    checking which schemas are downloaded and ready for validation.

    Args:
        schema_dir: Directory containing schemas. If None, defaults to
            'schemas' in the ingestion module directory.

    Returns:
        List of schema names available for validation.

    Example:
        >>> schemas = list_available_schemas()
        >>> print(f"Available schemas: {schemas}")
        ['bill', 'billstatus', 'plaw']
    """
    validator = XMLValidator(schema_dir)
    return list(validator.schemas.keys())
