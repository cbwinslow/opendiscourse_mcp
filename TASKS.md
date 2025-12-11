# OpenDiscourse GovInfo MCP — Final Task Plan and Documentation

Status: Complete

Objective
- Provide a minimal, robust pipeline to ingest govinfo.gov/bulkdata XML for Congress 113–119.
- Keep only the essential scripts to download, optionally validate, and optionally ingest into a database.

Essential script set
- scripts/ingest_govinfo.py — CLI for orchestrating downloads via async ingestor.
- scripts/ingestion/
  - ingestor.py — Async crawler/downloader using XML/JSON directory listings, with rate limiting, retries, per-doc-type manifests/failures, and optional XSD validation.
  - config.py — Config for congress range, document types, rate limits, timeouts, output paths.
  - rate_limiter.py — Token-bucket limiter for crawl politeness.
  - xml_validator.py — Optional XML validation via XSDs.
  - __init__.py — Module exports for programmatic control.
- scripts/govinfo_ingest.py — Optional: parse downloaded XML and insert into PostgreSQL (selected collections).
- SQL schemas
  - scripts/schema.sql
  - scripts/schema_extended.sql

Removed (deprecated / redundant)
- Legacy downloaders and one-offs have been removed to eliminate duplication and confusion.
- Removed files included:
  - download_118th_sample.py, download_complete_118th.py, download_congress_data.py, download_govinfo_data.py
  - govinfo_118th_congress_downloader.py, govinfo_bulk_downloader.py, govinfo_bulk_downloader_simple.py, govinfo_bulk_downloader_standalone.py
  - verify_crawler.py, ingest_govinfo_xml.py, govinfo_schema.sql, process_118th_congress.py, setup_bitwarden.py
  - test_118th_integration.py, test_bitwarden.py, test_pycongress.py

Artifacts produced by ingestion
- For each congress and doc type directory: govinfo_data/{congress}/{doc_type}/
  - manifest.json — Run summary and file inventory
    - attempted, succeeded, failed
    - new_files_count, dir_total_files, dir_total_bytes
    - started_at, finished_at
    - new_files: ["filename.xml", ...]
  - failures.json — List of failed_urls (present only when failures occur)

Usage
- Single congress (default document types from config):
  - python3 scripts/ingest_govinfo.py --congress 118
- Multiple congresses and selected document types:
  - python3 scripts/ingest_govinfo.py --congress 117 118 --doc-types BILLS BILLSTATUS
- All configured congresses:
  - python3 scripts/ingest_govinfo.py --all
- Tuning workers and output directory:
  - python3 scripts/ingest_govinfo.py --congress 118 --workers 8 --output govinfo_data
- Optional: Database ingest (example for BILLS):
  - python3 scripts/govinfo_ingest.py --collection BILLS --input govinfo_data --host localhost --database opendiscourse --user opendiscourse --password '…'

Configuration (env overrides; see scripts/ingestion/config.py)
- GOVINFO_DATA_DIR — Output directory (default: govinfo_data)
- GOVINFO_WORKERS — Parallel downloads (default: 10)
- GOVINFO_RATE_LIMIT — Requests per second (default: 10)
- GOVINFO_VALIDATE_XML — true/false (default: true)
- LOG_LEVEL — INFO/DEBUG/etc.

Testing
- Run all tests:
  - pytest -q
- Integration-style test for manifests/failures (no network):
  - tests/test_ingestor_integration.py monkeypatches get_document_list and download_file, then asserts that manifest.json and failures.json are written correctly.
- Existing unit tests for rate limiter are included.
- Optional: add aioresponses for HTTP-level mocking if needed.

Documentation
- docs/govinfo_bulk_download_process.md updated to reflect:
  - CLI usage via scripts/ingest_govinfo.py
  - Programmatic usage sample via ingest_congress_data
  - Tracking artifacts: manifest.json, failures.json
  - Debugging and best practices

Milestones and acceptance criteria — Final state
- M1 — End-to-end download (complete)
  - Recursive listing via XML/JSON endpoints for BILLS, BILLSTATUS, PLAW, STATUTE, FR, CREC
  - CLI supports --all, --congress, --doc-types, --workers, --output
  - Output layout: govinfo_data/{congress}/{doc_type}/<filename>.xml
- M2 — Resumability and manifest (complete)
  - Skip-on-existing works
  - Per doc type manifest.json and failures.json are written
- M3 — Optional validation (available, requires XSDs)
  - Place XSDs under scripts/ingestion/schemas and set GOVINFO_VALIDATE_XML=true
  - Invalid XML is removed and errors recorded/logged
- M4 — Optional DB ingestion (available)
  - scripts/govinfo_ingest.py ingests selected collections into PostgreSQL tables as per schema.sql/schema_extended.sql

Definition of done (met)
- One clear command downloads the total dataset for target congress/doc types into govinfo_data with logs, retries, and safe re-runs.
- Per-doc-type manifest and failure logs are produced.
- Minimal essential scripts only; duplicates removed.
- Documentation reflects the new CLI and artifacts.
- Tests cover key ingestion behaviors (manifest/failures, rate limiter).

Notes and recommendations
- For large runs, monitor disk space and adjust workers/rate limits to avoid rate limiting.
- For validation, ensure schemas match the exact versions of XML in target collections.
- Consider incremental updates in future revisions using manifest data to skip already enumerated URLs.

Changelog (summary)
- Added: per-doc-type manifest/failures; integration test; refined docs and task plan.
- Changed: ingest CLI and async ingestor are the canonical ingestion path.
- Removed: legacy downloaders and one-off scripts.
