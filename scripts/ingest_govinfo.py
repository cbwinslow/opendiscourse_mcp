#!/usr/bin/env python3
"""
Command-line interface for ingesting data from govinfo.gov.

This script provides a convenient way to download and process bulk data from
govinfo.gov for US Congress sessions.
"""
import asyncio
import logging
from pathlib import Path

from scripts.ingestion import ingest_all_congresses, ingest_congress_data
from scripts.ingestion.config import (
    CONGRESS_SESSIONS,
    DOCUMENT_TYPES,
    LOG_LEVEL,
    OUTPUT_DIR,
    WORKERS,
)


def parse_args():
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and process bulk data from govinfo.gov"
    )

    # Main arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all available congresses (113-119)",
    )
    group.add_argument(
        "--congress",
        type=int,
        nargs="+",
        help="Specific congress numbers to process (e.g., 115 116 117)",
    )

    # Document types
    parser.add_argument(
        "--doc-types",
        nargs="+",
        choices=DOCUMENT_TYPES,
        help=f"Document types to process (default: all: {', '.join(DOCUMENT_TYPES)})",
    )

    # Output options
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )

    # Performance options
    parser.add_argument(
        "--workers",
        type=int,
        default=WORKERS,
        help=f"Number of parallel downloads (default: {WORKERS})",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        default=LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Logging level (default: {LOG_LEVEL})",
    )

    return parser.parse_args()


def main():
    """Run the ingestion process based on command-line arguments."""
    args = parse_args()

    # Configure logging
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Determine congresses to process
    if args.all:
        congresses = CONGRESS_SESSIONS
    else:
        congresses = args.congress

    # Run the appropriate ingestion function
    try:
        if len(congresses) == 1:
            # Single congress - use the more specific function
            result = asyncio.run(
                ingest_congress_data(
                    congress=congresses[0],
                    doc_types=args.doc_types,
                    output_dir=args.output,
                    workers=args.workers,
                )
            )
            print(f"Processed Congress {congresses[0]}:")
            for doc_type, count in result.items():
                print(f"  {doc_type}: {count} files")
        else:
            # Multiple congresses
            results = asyncio.run(
                ingest_all_congresses(
                    congresses=congresses,
                    doc_types=args.doc_types,
                    output_dir=args.output,
                    workers=args.workers,
                )
            )

            # Print summary
            print("\n=== Processing Complete ===\n")
            print("Files downloaded by Congress and document type:")
            print("-" * 60)

            # Calculate column widths
            congress_width = max(10, len("Congress") + 2)
            type_width = max(15, max(len(t) for t in DOCUMENT_TYPES) + 2)

            # Print header
            print(
                f"{'Congress':<{congress_width}} "
                + " ".join(
                    f"{t:<{type_width-1}}" for t in (args.doc_types or DOCUMENT_TYPES)
                )
            )
            print("-" * 60)

            # Print results
            for congress in sorted(results.keys()):
                row = [f"{congress}th".ljust(congress_width)]
                for doc_type in args.doc_types or DOCUMENT_TYPES:
                    count = results[congress].get(doc_type, 0)
                    row.append(str(count).ljust(type_width - 1))
                print(" ".join(row))

            print("-" * 60)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
