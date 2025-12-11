# OpenDiscourse GovInfo MCP — Context for AI Agents

Domain overview
- Source: govinfo.gov/bulkdata provides hierarchical directories of XML documents for US government publications and datasets.
- Target collections (examples): BILLS, BILLSTATUS, BILLSUM, PLAW, STATUTE, FR, CREC.
- The ingestion traverses XML/JSON directory listings and downloads .xml files efficiently.

Key design points
- Async ingestion using aiohttp with concurrency control and rate limiting.
- Robustness with retries and actionable artifacts per doc type (manifest.json, failures.json).
- Idempotent: Re-runs skip existing files and update manifests. Safe to run repeatedly.

What an AI agent needs to know
- Entry points:
  - CLI: scripts/ingest_govinfo.py (targeted) and scripts/ingest_all_govinfo.py (full coverage)
  - Functions: ingest_congress_data and ingest_all_congresses in scripts.ingestion
- Output location:
  - govinfo_data/{congress}/{doc_type}/
- Monitoring and resumability:
  - manifest.json summarizes work done and inventory
  - failures.json records failed URLs

Guardrails
- Avoid overly high concurrency that could trigger HTTP 429; tune the workers parameter.
- Be mindful of disk space; datasets can be large.
- XML validation is optional and requires XSDs present in scripts/ingestion/schemas. Validation will slow ingestion; enable only when required.

Operational checklist for agents
1) Ensure Python 3.10 virtualenv and requirements are installed.
2) Choose ingestion mode:
   - Full coverage: python -m scripts.ingest_all_govinfo --workers 8
   - Targeted: python -m scripts.ingest_govinfo --congress 118 --doc-types BILLS BILLSTATUS
3) Monitor logs and manifests; adjust workers/rate limits to avoid rate limiting.
4) Re-run as needed; duplicates are skipped and manifests updated.

Common pitfalls
- Running scripts without module invocation may cause import errors; always run with python -m from the repo root or set PYTHONPATH.
- Missing Python version (3.10) can cause dependency install failures.
- Validation without schemas will fail; ensure schemas are present before enabling GOVINFO_VALIDATE_XML.
