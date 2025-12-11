# OpenDiscourse GovInfo MCP — Functions Reference for AI Agents

Overview
- This document details the primary callable functions AI agents should use for ingesting GovInfo bulkdata.
- All functions are asynchronous entry points exposed in scripts/ingestion/__init__.py and implemented in scripts/ingestion/ingestor.py.

Module: scripts.ingestion

Functions
1) ingest_congress_data
- Signature:
  ingest_congress_data(congress: int, doc_types: list[str] | None = None, output_dir: Path | None = None, workers: int = WORKERS) -> dict[str, int]
- Description:
  Ingests all documents for a single congress across the specified document types. Handles directory traversal via XML/JSON endpoints, rate limiting, retries, and per-doc-type manifests/failures.
- Parameters:
  - congress: Target congress number (e.g., 118)
  - doc_types: Subset of document types (default: all types from config)
  - output_dir: Base output directory; defaults to config.OUTPUT_DIR
  - workers: Parallelism level (semaphore and rate limiter)
- Returns:
  - Mapping of doc_type to number of successfully downloaded files.
- Side effects:
  - Writes files to {output_dir}/{congress}/{doc_type}/
  - Writes manifest.json and failures.json per doc type
- Exceptions:
  - Errors are logged; failed downloads recorded in failures.json. The function aims to return successfully processed counts.

2) ingest_all_congresses
- Signature:
  ingest_all_congresses(congresses: list[int] | None = None, doc_types: list[str] | None = None, output_dir: Path | None = None, workers: int = WORKERS) -> dict[int, dict[str, int]]
- Description:
  Orchestrates ingestion across multiple congresses and document types with the same robustness as ingest_congress_data.
- Parameters:
  - congresses: List of congress numbers (default: config.CONGRESS_SESSIONS)
  - doc_types: Subset of document types (default: config.DOCUMENT_TYPES)
  - output_dir: Base output directory; defaults to config.OUTPUT_DIR
  - workers: Parallelism level
- Returns:
  - Nested mapping of congress -> { doc_type -> success_count }.
- Side effects:
  - Same as above for each congress/doc type combination.

3) GovInfoIngestor (class)
- Purpose:
  Provides the core async ingestion implementation. AI agents typically won’t construct this directly unless they need fine-grained control.
- Constructor parameters:
  - output_dir: Path
  - workers: int
  - timeout: int (seconds)
  - max_retries: int
  - rate_limit: int (requests/sec)
  - chunk_size: int (bytes)
  - validate_xml: bool
- Key methods:
  - process_congress(session, congress, doc_types)
  - process_document_type(session, congress, doc_type)
  - get_document_list(session, congress, doc_type)
  - download_file(session, url, output_path, doc_type, retries)

Usage patterns
- Typical agents should call ingest_congress_data or ingest_all_congresses, not the low-level methods.
- Ensure an asyncio event loop is available; use asyncio.run(...) for top-level calls.

Environment variables (from scripts/ingestion/config.py)
- GOVINFO_DATA_DIR — Output directory
- GOVINFO_WORKERS — Parallel downloads
- GOVINFO_RATE_LIMIT — Requests/sec
- GOVINFO_VALIDATE_XML — Enable/disable validation
- LOG_LEVEL — Logging verbosity

Return values and artifacts
- Success counts per doc type help agents decide if additional retries are needed.
- Manifests and failures files provide a durable record of work and errors.

Examples
- See docs/agents/usage_guide.md for code snippets using these functions.
