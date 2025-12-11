# OpenDiscourse GovInfo MCP — Task Plan and Script Inventory

Objective
- Provide a minimal, robust pipeline to ingest all required data from govinfo.gov/bulkdata for Congress sessions 113–119.
- Reduce the code footprint to only a few essential scripts to download (and optionally validate and load) the total data.

Essential script set (keep)
- scripts/ingest_govinfo.py
  - CLI entrypoint to download bulk data by congress and document types using the async ingestor.
- scripts/ingestion/
  - ingestor.py — Async crawler/downloader with rate limiting, retries, optional XML validation.
  - config.py — Ingestion configuration: congress ranges, document types, rate limits, output dir, etc.
  - rate_limiter.py — Token-bucket rate limiter for respectful crawling.
  - xml_validator.py — Optional XSD-based validation support.
  - __init__.py — Exposes the ingestion API for programmatic usage.
- scripts/govinfo_ingest.py (optional)
  - Database ingestion of downloaded XML to PostgreSQL for selected collections using lxml; use with schema.sql/schema_extended.sql.
- SQL schemas (keep both unless we consolidate)
  - scripts/schema.sql — Base schema for ingestion targets.
  - scripts/schema_extended.sql — Extended schema variant.

Deprecated/replace (remove or archive)
These are superseded by the essential ingestion pipeline above. They are either duplicates, one-offs, or experimental.
- Downloaders and crawlers
  - scripts/download_govinfo_data.py
  - scripts/download_congress_data.py
  - scripts/download_118th_sample.py
  - scripts/download_complete_118th.py
  - scripts/govinfo_118th_congress_downloader.py
  - scripts/govinfo_bulk_downloader.py
  - scripts/govinfo_bulk_downloader_simple.py
  - scripts/govinfo_bulk_downloader_standalone.py
  - scripts/verify_crawler.py
- Alternative/overlapping ingestion
  - scripts/ingest_govinfo_xml.py
  - scripts/govinfo_schema.sql (prefer schema.sql/schema_extended.sql)
- One-off process/testing/infra helpers not required for the minimal ingestion deliverable
  - scripts/process_118th_congress.py
  - scripts/setup_bitwarden.py
  - scripts/test_118th_integration.py
  - scripts/test_bitwarden.py
  - scripts/test_pycongress.py

Rationale for consolidation
- The async ingestion stack (ingest_govinfo.py + scripts/ingestion/*) fully implements the documented bulkdata traversal using the XML/JSON listing endpoints, supports rate limiting and retries, and organizes output by congress/doc type.
- Keeping one clear path reduces maintenance and ambiguity, while remaining flexible (validation, future incremental update logic).

Suggested cleanup commands (optional)
- Dry-run list of files to remove:
  - git ls-files scripts | egrep "(download_|govinfo_118th|_standalone|_simple|verify_crawler|ingest_govinfo_xml|test_|process_118th|setup_bitwarden|govinfo_schema\.sql)$"
- Remove deprecated files (verify before running):
  - git rm scripts/download_govinfo_data.py scripts/download_congress_data.py scripts/download_118th_sample.py scripts/download_complete_118th.py scripts/govinfo_118th_congress_downloader.py scripts/govinfo_bulk_downloader.py scripts/govinfo_bulk_downloader_simple.py scripts/govinfo_bulk_downloader_standalone.py scripts/verify_crawler.py scripts/ingest_govinfo_xml.py scripts/govinfo_schema.sql scripts/process_118th_congress.py scripts/setup_bitwarden.py scripts/test_118th_integration.py scripts/test_bitwarden.py scripts/test_pycongress.py

End-to-end workflows
- Download bulk data for one congress (all default types):
  - python3 scripts/ingest_govinfo.py --congress 118
- Download for multiple congresses, restricted types:
  - python3 scripts/ingest_govinfo.py --congress 117 118 --doc-types BILLS BILLSTATUS
- Download all configured congresses (113–119 by default):
  - python3 scripts/ingest_govinfo.py --all
- Optional: Ingest downloaded XML into PostgreSQL (example: BILLS):
  - python3 scripts/govinfo_ingest.py --collection BILLS --input govinfo_data --host localhost --database opendiscourse --user opendiscourse --password '…'

Configuration and environment
- scripts/ingestion/config.py controls ingestion defaults.
  - GOVINFO_DATA_DIR — Output directory (default: govinfo_data)
  - GOVINFO_WORKERS — Parallel downloads (default: 10)
  - GOVINFO_RATE_LIMIT — Requests per second (default: 10)
  - GOVINFO_VALIDATE_XML — Enable XML validation (default: true)
  - LOG_LEVEL — Logging level (default: INFO)

Task plan (optimized)
1) Finalize ingestion pipeline
   - Verify directory traversal covers all subpaths using XML then JSON listing endpoints.
   - Confirm output directory layout: govinfo_data/{congress}/{doc_type}/…
   - Ensure skip-on-existing logic supports resumability; add checksum tracking if needed.
2) Validation and schemas (optional)
   - Collect required XSDs and place under scripts/ingestion/schemas.
   - Wire doc types to schema names; exercise XMLValidator on a sample batch.
3) Performance and stability
   - Tune workers and rate limit to avoid 429s; add exponential backoff if necessary.
   - Add progress metrics per doc type and congress; summarize counts.
4) Storage and metadata (optional)
   - Produce a manifest (JSON) with file list, sizes, and timestamps per run.
   - Record failures with retry hints for later re-run.
5) Database ingestion (optional)
   - Validate schema.sql/schema_extended.sql downstream.
   - Run scripts/govinfo_ingest.py per collection; verify counts.
6) Tests
   - Add integration tests for get_document_list and downloading a small fixture set.
   - CLI smoke tests for ingest_govinfo.py (arg parsing, basic flows).
7) Documentation
   - Update docs/govinfo_bulk_download_process.md with ingest_govinfo.py usage.
   - Add a short deprecations note listing removed scripts and the rationale.

Definition of done
- One clear command fetches the total dataset for 113–119 across selected doc types into govinfo_data with logging and resumability.
- Optional: validated XMLs for selected collections with a manifest and basic summary metrics.
- Optional: DB tables populated for selected collections using govinfo_ingest.py.
