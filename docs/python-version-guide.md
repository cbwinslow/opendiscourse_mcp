# OpenDiscourse MCP - Development Guide

## Python Version Management

This project enforces Python 3.10+ usage through multiple mechanisms:

### 1. pyproject.toml Configuration

```toml
[project]
requires-python = ">=3.10,<3.13"

[tool.rye]
managed = true
dev-dependencies = [
    "python>=3.10,<3.13"
]

[tool.uv]
python-preference = "3.10"
```

### 2. .python-version File

```toml
[tool.rye]
managed = true
dev-dependencies = [
    "python>=3.10,<3.13"
]

[tool.uv]
python-preference = "3.10"
```

### 3. CI/CD Integration

```yaml
# .github/workflows/ci.yml
steps:
  - uses: actions/setup-python@v4
    with:
      python-version: '3.10'
```

### 4. Development Environment Setup

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -r requirements.txt

# Verify Python version
python --version  # Should show 3.10+
```

### 5. Docker Support

```dockerfile
FROM python:3.10-slim

# Or with version pin
FROM python:3.11
```

## Why Python 3.10+?

- **psycopg2-binary**: Requires Python 3.7+ but 3.10+ recommended
- **cryptography**: Latest versions require Python 3.10+
- **pydantic**: Modern features need Python 3.10+
- **MCP SDK**: Built for Python 3.10+

## Version Enforcement

The project uses multiple complementary approaches:

1. **pyproject.toml**: Modern Python packaging standard
2. **.python-version**: For tools like ryne and uv
3. **CI/CD**: Automated environment setup
4. **Documentation**: Clear version requirements

## Installation Instructions

### For Developers

```bash
# Clone with Python 3.10+
git clone https://github.com/cbwinslow/opendiscourse_mcp.git
cd opendiscourse_mcp

# Using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or ensure Python 3.10+
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### For Users

```bash
# Check Python version
python --version

# Should show 3.10.x or 3.11.x
# If not, install Python 3.10+ or use uv
```

## Troubleshooting

**"Python version too old" error:**
```bash
# Install uv (Python version manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Use uv to install with correct Python version
uv sync
```

**Dependency conflicts:**
```bash
# Create fresh environment
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```