#!/usr/bin/env python3
"""
Ingest all GovInfo bulkdata XML across configured congress sessions and document types.

This script uses the async ingestion API to traverse govinfo.gov/bulkdata using
XML/JSON listing endpoints, applies rate limiting and retries, and writes per-doc-type
manifests and failure logs under the output directory.

Defaults come from scripts/ingestion/config.py, but can be overridden via CLI.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

from scripts.ingestion import ingest_all_congresses
from scripts.ingestion.config import (
    CONGRESS_SESSIONS,
    DOCUMENT_TYPES,
    OUTPUT_DIR,
    WORKERS,
    LOG_LEVEL,
)


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest all GovInfo bulkdata XML across configured congresses and document types"
    )

    parser.add_argument(
        "--congress",
        type=int,
        nargs="+",
        help="Specific congress numbers to process (default: all from config)",
    )
    parser.add_argument(
        "--doc-types",
        nargs="+",
        choices=DOCUMENT_TYPES,
        help=f"Document types to process (default: all: {', '.join(DOCUMENT_TYPES)})",
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
        help=f"Logging level (default: {LOG_LEVEL})",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Configure logging
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Determine targets
    congresses = args.congress if args.congress else CONGRESS_SESSIONS
    doc_types = args.doc_types if args.doc_types else DOCUMENT_TYPES

    logging.info(
        "Starting full GovInfo ingestion | Congresses: %s | DocTypes: %s | Workers: %s | Output: %s",
        congresses,
        doc_types,
        args.workers,
        args.output,
    )

    # Run ingestion
    results = asyncio.run(
        ingest_all_congresses(
            congresses=congresses,
            doc_types=doc_types,
            output_dir=args.output,
            workers=args.workers,
        )
    )

    # Print concise summary
    print("\n=== GovInfo Ingestion Summary ===\n")
    # Column widths
    congress_width = max(10, len("Congress") + 2)
    type_width = max(15, max(len(t) for t in DOCUMENT_TYPES) + 2)

    header = f"{'Congress':<{congress_width}} " + " ".join(
        f"{t:<{type_width-1}}" for t in (args.doc_types or DOCUMENT_TYPES)
    )
    print(header)
    print("-" * len(header))

    for congress in sorted(results.keys()):
        row = [f"{congress}th".ljust(congress_width)]
        for t in (args.doc_types or DOCUMENT_TYPES):
            row.append(str(results[congress].get(t, 0)).ljust(type_width - 1))
        print(" ".join(row))

    print("\nNote: Per-doc-type manifests and failures are written under: {}/<congress>/<doctype>/".format(args.output))

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
