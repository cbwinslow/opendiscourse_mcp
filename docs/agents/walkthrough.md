# OpenDiscourse GovInfo MCP — AI Agent Walkthrough

Goal
- Walk an AI agent through setup, configuration, and ingestion of GovInfo bulkdata using the provided CLI and functions.

Step 1 — Environment setup
- Ensure Python 3.10 is installed.
- Enter project directory; direnv will create/activate .venv automatically if present.
- If direnv is not used:
  python3.10 -m venv .venv
  . .venv/bin/activate
- Install dependencies:
  pip install --upgrade pip
  pip install -r requirements.txt

Step 2 — Basic ingestion via CLI
- Single congress, default document types:
  python -m scripts.ingest_govinfo --congress 118
- Multiple congresses and selected types:
  python -m scripts.ingest_govinfo --congress 117 118 --doc-types BILLS BILLSTATUS
- Full coverage using defaults from config:
  python -m scripts.ingest_all_govinfo

Step 3 — Programmatic ingestion
```python
import asyncio
from pathlib import Path
from scripts.ingestion import ingest_congress_data, ingest_all_congresses

# Targeted
result = asyncio.run(
    ingest_congress_data(congress=118, doc_types=["BILLS", "BILLSTATUS"], output_dir=Path("govinfo_data"), workers=12)
)
print(result)

# Full coverage
results = asyncio.run(
    ingest_all_congresses(output_dir=Path("govinfo_data"), workers=8)
)
print(results)
```

Step 4 — Monitoring artifacts
- After a run, check:
  - govinfo_data/{congress}/{doc_type}/manifest.json — summary and inventory
  - govinfo_data/{congress}/{doc_type}/failures.json — failed URLs
- Re-run as needed; existing files are skipped.

Step 5 — Tuning and validation
- Concurrency: adjust --workers (or workers argument) based on network and server behavior.
- Rate limiting: set GOVINFO_RATE_LIMIT in the environment.
- Validation: place XSDs in scripts/ingestion/schemas and export GOVINFO_VALIDATE_XML=true.

Step 6 — Optional DB ingestion
- After files are downloaded, optionally ingest into PostgreSQL:
  python scripts/govinfo_ingest.py --collection BILLS --input govinfo_data --host localhost --database opendiscourse --user opendiscourse --password '…'

Troubleshooting
- Import errors: run CLIs with python -m from repo root or export PYTHONPATH=$PWD.
- HTTP 429: reduce workers and/or rate; confirm logs and retry counts.
- Permission issues: ensure write access to govinfo_data and use a user-owned .venv.

You are now ready to ingest GovInfo bulkdata at scale with robust resumability and logging.
