#!/usr/bin/env python3
"""
Comprehensive GovInfo Bulk Data Ingestion Script

This script orchestrates the complete ingestion of all available govinfo.gov bulk data,
broken down by congress number and document type for better monitoring and control.

Features:
- Runs ingestion for each congress/document type combination separately
- Provides detailed progress tracking and monitoring
- Includes retry logic and error handling
- Generates comprehensive summary reports
- Supports resumption from partial runs
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Import enums and configurations
from scripts.ingestion.enums import (
    IngestionConfig,
    PRODUCTION_CONGRESSES,
    PRODUCTION_DOCUMENT_TYPES
)

# Configuration - Use production settings
CONGRESS_SESSIONS = PRODUCTION_CONGRESSES
DOCUMENT_TYPES = PRODUCTION_DOCUMENT_TYPES
WORKERS = IngestionConfig.DEFAULT_WORKERS
LOG_LEVEL = IngestionConfig.DEFAULT_LOG_LEVEL

# Results tracking
RESULTS_FILE = Path("ingestion_results.json")
PROGRESS_FILE = Path("ingestion_progress.log")

def setup_logging():
    """Set up comprehensive logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROGRESS_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_existing_results(logger) -> dict:
    """Load existing results from previous runs."""
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing results: {e}")
    return {}

def save_results(results: dict, logger):
    """Save results to file."""
    try:
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Could not save results: {e}")

def run_ingestion_command(congress: int, doc_type: str, logger) -> tuple[bool, str, dict]:
    """
    Run ingestion for a specific congress and document type.

    Args:
        congress: Congress number
        doc_type: Document type

    Returns:
        tuple of (success, output, stats)
    """
    cmd = [
        "python3.10", "-m", "scripts.ingest_all_govinfo",
        "--congress", str(congress),
        "--doc-types", doc_type,
        "--workers", str(WORKERS),
        "--log-level", LOG_LEVEL
    ]

    env = {
        "GOVINFO_WORKERS": str(WORKERS),
        "GOVINFO_VALIDATE_XML": "true"
    }

    logger.info(f"Starting ingestion: Congress {congress}, Type {doc_type}")
    logger.info(f"Command: {' '.join(cmd)}")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per run
            env={**os.environ, **env}
        )

        execution_time = time.time() - start_time

        # Parse output for stats
        stats = parse_ingestion_output(result.stdout, result.stderr, execution_time)

        success = result.returncode == 0
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

        logger.info(f"Completed ingestion: Congress {congress}, Type {doc_type} - "
                   f"{'SUCCESS' if success else 'FAILED'} ({execution_time:.1f}s)")

        return success, output, stats

    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        logger.error(f"TIMEOUT: Congress {congress}, Type {doc_type} ({execution_time:.1f}s)")
        return False, f"Command timed out after {execution_time:.1f}s", {"timeout": True, "execution_time": execution_time}

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"ERROR: Congress {congress}, Type {doc_type}: {str(e)}")
        return False, f"Exception: {str(e)}", {"error": str(e), "execution_time": execution_time}

def parse_ingestion_output(stdout: str, stderr: str, execution_time: float) -> dict:
    """Parse ingestion output to extract statistics."""
    stats = {
        "execution_time": execution_time,
        "files_processed": 0,
        "files_failed": 0,
        "files_skipped": 0,
        "success_rate": 0.0
    }

    # Parse stdout for file counts
    lines = stdout.split('\n')
    for line in lines:
        if "Overall results:" in line:
            # Look for patterns like "7/7 files" or "5/10 files"
            import re
            match = re.search(r'(\d+)/(\d+) files', line)
            if match:
                stats["files_processed"] = int(match.group(1))
                total_files = int(match.group(2))
                stats["files_failed"] = total_files - stats["files_processed"]
                if total_files > 0:
                    stats["success_rate"] = (stats["files_processed"] / total_files) * 100

        elif "File exists, skipping:" in line:
            stats["files_skipped"] += 1

    return stats

def print_progress_summary(results: dict):
    """Print a comprehensive progress summary."""
    print("\n" + "="*80)
    print("COMPREHENSIVE INGESTION PROGRESS SUMMARY")
    print("="*80)

    total_runs = len(results)
    successful_runs = sum(1 for r in results.values() if r.get("success", False))
    failed_runs = total_runs - successful_runs

    print(f"Total Runs: {total_runs}")
    print(f"Successful: {successful_runs}")
    print(f"Failed: {failed_runs}")
    print(f"Success Rate: {(successful_runs/total_runs*100):.1f}%" if total_runs > 0 else "N/A")

    # Summary by congress
    congress_summary = {}
    doc_type_summary = {}
    total_files = 0
    total_time = 0

    for key, result in results.items():
        congress, doc_type = key.split("_")

        if congress not in congress_summary:
            congress_summary[congress] = {"success": 0, "total": 0, "files": 0}
        if doc_type not in doc_type_summary:
            doc_type_summary[doc_type] = {"success": 0, "total": 0, "files": 0}

        congress_summary[congress]["total"] += 1
        doc_type_summary[doc_type]["total"] += 1

        if result.get("success", False):
            congress_summary[congress]["success"] += 1
            doc_type_summary[doc_type]["success"] += 1

        stats = result.get("stats", {})
        files = stats.get("files_processed", 0)
        congress_summary[congress]["files"] += files
        doc_type_summary[doc_type]["files"] += files
        total_files += files
        total_time += stats.get("execution_time", 0)

    print(f"\nTotal Files Processed: {total_files}")
    print(f"Total Execution Time: {total_time:.1f}s ({total_time/60:.1f}m)")

    print("\nBy Congress:")
    for congress in sorted(congress_summary.keys()):
        data = congress_summary[congress]
        success_rate = (data["success"]/data["total"]*100) if data["total"] > 0 else 0
        print(f"  {congress}: {data['success']}/{data['total']} ({success_rate:.1f}%) - {data['files']} files")

    print("\nBy Document Type:")
    for doc_type in sorted(doc_type_summary.keys()):
        data = doc_type_summary[doc_type]
        success_rate = (data["success"]/data["total"]*100) if data["total"] > 0 else 0
        print(f"  {doc_type}: {data['success']}/{data['total']} ({success_rate:.1f}%) - {data['files']} files")

    print("\nFailed Runs:")
    for key, result in results.items():
        if not result.get("success", False):
            congress, doc_type = key.split("_")
            print(f"  {congress}_{doc_type}: {result.get('output', 'Unknown error')[:100]}...")

    print("="*80)

async def main():
    """Main orchestration function."""
    logger = setup_logging()

    logger.info("Starting comprehensive GovInfo bulk data ingestion")
    logger.info(f"Target: Congress {CONGRESS_SESSIONS} ({len(CONGRESS_SESSIONS)} congresses)")
    logger.info(f"Document Types: {DOCUMENT_TYPES} ({len(DOCUMENT_TYPES)} types)")
    logger.info(f"Workers: {WORKERS}, Validation: enabled")

    # Load existing results
    results = load_existing_results(logger)

    # Generate all possible combinations
    total_combinations = len(CONGRESS_SESSIONS) * len(DOCUMENT_TYPES)
    completed = 0

    logger.info(f"Total combinations to process: {total_combinations}")

    # Process each combination
    for congress in CONGRESS_SESSIONS:
        for doc_type in DOCUMENT_TYPES:
            key = f"{congress}_{doc_type}"

            # Skip if already completed successfully
            if key in results and results[key].get("success", False):
                logger.info(f"Skipping already completed: {key}")
                completed += 1
                continue

            # Run ingestion
            success, output, stats = run_ingestion_command(congress, doc_type, logger)

            # Store results
            results[key] = {
                "congress": congress,
                "doc_type": doc_type,
                "success": success,
                "output": output,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }

            # Save results after each run
            save_results(results, logger)

            completed += 1
            progress = (completed / total_combinations) * 100
            logger.info(f"Progress: {completed}/{total_combinations} ({progress:.1f}%)")

            # Print summary every 10 runs
            if completed % 10 == 0:
                print_progress_summary(results)

    # Final summary
    logger.info("Comprehensive ingestion completed!")
    print_progress_summary(results)

if __name__ == "__main__":
    import os
    asyncio.run(main())
