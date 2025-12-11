# OpenDiscourse MCP — Setup

Target Python version
- 3.10 (enforced via .envrc, .python-version, and .tool-versions)

One-time setup
1) Ensure Python 3.10 is available (system, pyenv, or asdf)
   - pyenv: pyenv install 3.10.14; pyenv local 3.10.14
   - asdf: asdf install python 3.10.14; asdf local python 3.10.14
2) Create virtualenv and install dependencies
   - python3.10 -m venv .venv
   - . .venv/bin/pip install --upgrade pip
   - . .venv/bin/pip install -r requirements.txt
3) (Optional) Enable direnv for automatic activation
   - direnv allow

Verify environment
- Ensure python and pytest resolve to venv binaries:
  - which python  # should be .venv/bin/python
  - which pytest  # should be .venv/bin/pytest
- Verify Python version:
  - python --version  # should be 3.10.x

Run tests
- pytest -q

Run ingestion
- Full coverage (defaults from config):
  - python -m scripts.ingest_all_govinfo --workers 8
- Targeted run:
  - python -m scripts.ingest_govinfo --congress 118 --doc-types BILLS BILLSTATUS

Notes
- If using direnv, the .envrc prepends .venv/bin to PATH rather than sourcing any shell-specific activation scripts.
- requirements.txt is pinned for Python 3.10 compatibility.
