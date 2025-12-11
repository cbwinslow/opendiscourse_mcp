# OpenDiscourse MCP

Model Context Protocol (MCP) servers for accessing bulk data from govinfo.gov and congress.gov APIs with comprehensive AI-powered code review and data ingestion capabilities.

## Overview

This project provides MCP servers that enable AI assistants to access comprehensive legislative and governmental data from:

- **GovInfo API**: Congressional documents, Federal Register, Code of Federal Regulations, and more
- **Congress.gov API**: Bills, members, committees, nominations, and legislative activities
- **Bulk Data Ingestion**: Automated downloading and processing of govinfo.gov bulk data
- **AI Code Review**: Multi-agent AI crews for comprehensive code analysis

## Features

### GovInfo Server Tools
- `govinfo_list_collections` - List collections updated since a specific date
- `govinfo_get_package` - Get detailed package information
- `govinfo_list_granules` - List granules within a package
- `govinfo_get_granule` - Get detailed granule information
- `govinfo_download_content` - Download content (PDF, XML, HTML)

### Congress.gov Server Tools

- `congress_get_bill` - Get detailed bill information
- `congress_search_bills` - Search for bills by text query
- `congress_get_bill_actions` - Get legislative actions for a bill
- `congress_get_bill_text` - Get full text of a bill
- `congress_search_members` - Search for members of Congress
- `congress_get_member` - Get detailed member information
- `congress_get_committee_meetings` - Get committee meetings
- `congress_get_nominations` - Get presidential nominations

### Bulk Data Ingestion
- **Comprehensive Download**: Automated ingestion of all govinfo.gov bulk data
- **Congress Coverage**: 113th to 123rd Congress (2013-2024)
- **Document Types**: BILLS, BILLSTATUS, PLAW, STATUTE, FR, CREC
- **Parallel Processing**: 50 workers for high-performance downloads
- **XML Validation**: Schema-based validation for data integrity
- **Skip-on-Existing**: Resumable downloads with intelligent file skipping
- **Progress Monitoring**: Real-time progress tracking and comprehensive reporting

### AI Code Review Suite
- **Security Review**: Vulnerability assessment and security analysis
- **Performance Review**: Bottleneck identification and optimization suggestions
- **Quality Review**: Code style, testing, architecture, and accessibility analysis
- **Documentation Review**: Documentation quality and completeness assessment
- **Multi-Agent**: Specialized AI agents for different review aspects
- **Observability**: Langfuse integration for monitoring and tracing

## Installation

### Prerequisites

1. **Node.js and npm** (for MCP server)
2. **Python 3.10+** (for setup scripts)
3. **PostgreSQL** (for database storage)
4. **Bitwarden CLI** (for API key management)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/cbwinslow/opendiscourse_mcp.git
cd opendiscourse_mcp

# Install Node.js dependencies
npm install

# Install Bitwarden CLI
npm install -g @bitwarden/cli

# Set up database
./scripts/setup_database.sh

# Set up API keys with Bitwarden
python3 scripts/setup_bitwarden.py

# Start MCP server
npm start
```

### Detailed Setup

#### 1. Python Environment

```bash
# Verify Python version (requires 3.10+)
python --version

# Using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Database Setup

```bash
# Automated database setup
./scripts/setup_database.sh

# Manual setup (if script fails)
# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# Create database and user
sudo -u postgres createdb opendiscourse
sudo -u postgres createuser -s opendiscourse
sudo -u postgres psql -c "ALTER USER opendiscourse PASSWORD 'opendiscourse123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO opendiscourse;"
```

#### 3. Bitwarden Setup

```bash
# Install Bitwarden CLI
npm install -g @bitwarden/cli

# Test Bitwarden integration
python3 scripts/test_bitwarden.py

# Add API keys to Bitwarden:
# - GovInfo API Key
# - Congress.gov API Key
```

#### 4. API Key Configuration

```bash
# Set environment variables (optional)
export BITWARDEN_EMAIL="your-email@example.com"
export BITWARDEN_PASSWORD="your-master-password"

# Run automated setup
python3 scripts/setup_bitwarden.py
```

#### 5. MCP Server Deployment

```bash
# Install dependencies
uv sync

# Start server
npm start

# Development mode
npm run dev
```

**Bitwarden Item Setup:**

Create these items in your Bitwarden vault:

- **GovInfo API Key**
  - Name: `GovInfo API Key`
  - Custom Field: `api_key` with your GovInfo API key

- **Congress.gov API Key**
  - Name: `Congress.gov API Key`
  - Custom Field: `api_key` with your Congress.gov API key

## Configuration

### Required API Keys

1. **GovInfo API Key**
   - Sign up at: <https://api.data.gov/signup>
   - Add to `.env`: `GOVINFO_API_KEY=your_key_here`

2. **Congress.gov API Key**
   - Sign up at: <https://api.congress.gov/sign-up/>
   - Add to `.env`: `CONGRESS_API_KEY=your_key_here`

### Optional Configuration

- `MCP_LOG_LEVEL` - Logging level (default: info)
- `GOVINFO_RATE_LIMIT` - GovInfo rate limit requests/hour (default: 1000)
- `CONGRESS_RATE_LIMIT` - Congress.gov rate limit requests/hour (default: 4000)

## Usage

### Bulk Data Ingestion

The project includes comprehensive bulk data ingestion capabilities for govinfo.gov:

```bash
# Run comprehensive ingestion for all available data
python3 scripts/run_comprehensive_ingestion.py

# Run specific congress and document type
python3 -m scripts.ingest_all_govinfo --congress 118 --doc-types BILLS --workers 50

# Run with validation enabled
python3 -m scripts.ingest_all_govinfo --congress 118 --doc-types STATUTE --validate-xml --workers 50
```

**Ingestion Features:**

- **Congress Coverage**: 113th-123rd Congress (2013-2024)
- **Document Types**: BILLS, BILLSTATUS, PLAW, STATUTE, FR, CREC
- **Parallel Downloads**: 50 concurrent workers
- **XML Validation**: Schema-based validation with XSD files
- **Resume Capability**: Skip-on-existing functionality
- **Progress Tracking**: Real-time monitoring and JSON results

**Configuration:**

```python
# Use enums for type-safe configuration
from scripts.ingestion.enums import DocumentType, CongressSession

# Available document types
DocumentType.BILLS.value  # "BILLS"
DocumentType.STATUTE.value  # "STATUTE"

# Available congress sessions
CongressSession.get_available_sessions()  # [113, 114, ..., 123]
```

### AI Code Review

The project includes specialized AI crews for comprehensive code review:

```bash
# Run all review types (via GitHub Actions)
# Or manually trigger specific reviews:

# Security review
python3 scripts/security_review_crew.py

# Performance review
python3 scripts/performance_review_crew.py

# Quality review (style, testing, architecture, dependencies, accessibility)
python3 scripts/quality_review_crew.py

# Documentation review
python3 scripts/documentation_review_crew.py

# Original comprehensive review
python3 scripts/code_review_crew.py
```

**AI Review Features:**

- **Security Analysis**: Vulnerability assessment, security best practices
- **Performance Optimization**: Bottleneck identification, efficiency improvements
- **Quality Assessment**: Code style, testing coverage, architecture review
- **Documentation Review**: API docs, README, inline comments
- **Multi-Agent**: Specialized AI agents for different review aspects
- **Observability**: Langfuse integration for monitoring and tracing

**GitHub Actions Integration:**

- Automatic PR reviews
- Configurable review types (security, performance, quality, documentation)
- Python 3.10 enforcement
- Comprehensive reporting

### As MCP Server

```bash
# Start MCP server
npm start

# Or in development mode with auto-restart
npm run dev
```

### Integration with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "opendiscourse": {
      "command": "node",
      "args": ["/path/to/opendiscourse_mcp/src/index.js"],
      "env": {
        "GOVINFO_API_KEY": "your_govinfo_key",
        "CONGRESS_API_KEY": "your_congress_key"
      }
    }
  }
}
```

### API Key Management

The project includes automated API key management through Bitwarden:

```bash
# Test Bitwarden integration
python3 scripts/test_bitwarden.py

# Set up API keys from Bitwarden
python3 scripts/setup_bitwarden.py
```

**Features:**
- 🔍 Automatic API key discovery from Bitwarden vault
- 🔓 Secure vault unlocking
- 📝 Environment file updates
- 🗄️ Database storage with encryption
- 🔐 Security masking in console output

### Integration with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "opendiscourse": {
      "command": "node",
      "args": ["/path/to/opendiscourse_mcp/src/index.js"],
      "env": {
        "GOVINFO_API_KEY": "your_govinfo_key",
        "CONGRESS_API_KEY": "your_congress_key"
      }
    }
  }
}
```

## API Coverage

### GovInfo Collections

- **BILLS** - Congressional bills (all versions)
- **CREC** - Congressional Record
- **FR** - Federal Register
- **CFR** - Code of Federal Regulations
- **USCOURTS** - U.S. Courts opinions
- **CHRG** - Committee reports and prints

### Congress.gov Data

- Bills and amendments (93rd Congress to present)
- Member information and voting records
- Committee data and meetings
- Presidential nominations
- Roll call votes
- Legislative text and summaries

## Rate Limits

- **GovInfo API**: Follows api.data.gov limits (configurable, default 1000/hour)
- **Congress.gov API**: 5,000 requests/hour (configurable, default 4000/hour)

Both clients implement automatic rate limiting with delays between requests.

## Development

```bash
# Run tests
npm test

# Lint code
npm run lint

# Full build process
npm run build
```

## Documentation

Comprehensive documentation is available in the `/docs` folder:

- `docs/README.md` - Complete reference guide
- `docs/govinfo-api-summary.md` - GovInfo API quick reference
- `docs/congress-api-summary.md` - Congress.gov API quick reference
- Downloaded official API repositories and samples

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run `npm run build`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Issues: <https://github.com/cbwinslow/opendiscourse_mcp/issues>
- GovInfo API: <https://github.com/usgpo/api/issues>
- Congress.gov API: <https://github.com/LibraryOfCongress/api.congress.gov/issues>
