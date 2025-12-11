# Installation Guide

## Overview

This guide provides step-by-step instructions for installing and setting up the OpenDiscourse MCP Servers in various environments.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4GB | 8GB+ |
| **Disk Space** | 10GB | 50GB+ |
| **OS** | Linux/macOS/Windows | Linux (Ubuntu 20.04+) |

### Software Requirements

- **Python**: 3.8+
- **Node.js**: 14+ (for TypeScript version)
- **Docker**: 20.10+ (for containerized deployment)
- **Git**: 2.0+
- **pip**: Latest version
- **npm/yarn**: Latest version (for TypeScript)

## Installation Methods

### 1. PyPI Installation (Python)

```bash
# Install from PyPI
pip install opendiscourse-congress opendiscourse-govinfo

# Verify installation
opendiscourse-congress --version
opendiscourse-govinfo --version
```

### 2. NPM Installation (TypeScript)

```bash
# Install from NPM
npm install -g @opendiscourse/congress @opendiscourse/govinfo

# Verify installation
opendiscourse-congress --version
opendiscourse-govinfo --version
```

### 3. Docker Installation

```bash
# Pull Docker images
docker pull opendiscourse/congress:latest
docker pull opendiscourse/govinfo:latest

# Run containers
docker run -d --name congress-mcp opendiscourse/congress:latest
docker run -d --name govinfo-mcp opendiscourse/govinfo:latest
```

### 4. Source Code Installation

```bash
# Clone repository
git clone https://github.com/opendiscourse/opendiscourse-mcp.git
cd opendiscourse-mcp

# Create virtual environment (Python)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install TypeScript dependencies
npm install

# Build TypeScript
npm run build
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database configuration
DATABASE_URL=sqlite:///data/opendiscourse.db
DATABASE_SSL=false

# API configuration
CONGRESS_API_URL=https://api.congress.gov/v3
GOVINFO_API_URL=https://api.govinfo.gov
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=60

# Security
API_KEY=your_api_key_here
RATE_LIMIT=60
SSL_VERIFY=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/opendiscourse.log

# Performance
BATCH_SIZE=100
WORKER_THREADS=4
```

### Configuration File

Edit `config/global_settings.py` to customize settings:

```python
from config.global_settings import GlobalSettings

# Load settings
settings = GlobalSettings()

# Override specific settings
settings.debug = True
settings.api.max_concurrent_requests = 10

# Save settings
settings.save()
```

## Running the Servers

### Congress.gov MCP Server

```bash
# Run Congress server
python -m src.congress.main

# With custom configuration
python -m src.congress.main --config custom_config.py

# As MCP server
opendiscourse-congress --mcp-mode
```

### GovInfo.gov MCP Server

```bash
# Run GovInfo server
python -m src.govinfo.main

# With custom configuration
python -m src.govinfo.main --config custom_config.py

# As MCP server
opendiscourse-govinfo --mcp-mode
```

## Docker Deployment

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  congress-mcp:
    image: opendiscourse/congress:latest
    container_name: congress-mcp
    environment:
      - DATABASE_URL=sqlite:///data/congress.db
      - CONGRESS_API_URL=https://api.congress.gov/v3
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8001:8000"
    restart: unless-stopped

  govinfo-mcp:
    image: opendiscourse/govinfo:latest
    container_name: govinfo-mcp
    environment:
      - DATABASE_URL=sqlite:///data/govinfo.db
      - GOVINFO_API_URL=https://api.govinfo.gov
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8002:8000"
    restart: unless-stopped

  # Optional: Database service
  postgres:
    image: postgres:13
    container_name: opendiscourse-postgres
    environment:
      POSTGRES_USER: opendiscourse
      POSTGRES_PASSWORD: securepassword
      POSTGRES_DB: opendiscourse
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
```

Start the services:

```bash
docker-compose up -d
```

## Development Setup

### Python Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/unit/congress/
```

### TypeScript Development

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run tests
npm test

# Watch for changes
npm run watch
```

## Troubleshooting

### Common Issues

#### 1. API Connection Errors

**Symptoms**: Connection timeouts, rate limiting errors

**Solutions**:
- Check your internet connection
- Verify API URLs in configuration
- Increase timeout settings
- Reduce concurrent requests
- Check API status pages

#### 2. Database Connection Errors

**Symptoms**: Database connection failures, timeouts

**Solutions**:
- Verify database URL format
- Check database service is running
- Test connection with database client
- Increase connection timeout

#### 3. Permission Errors

**Symptoms**: File access denied, permission issues

**Solutions**:
- Check file/directory permissions
- Run with appropriate user
- Create missing directories
- Set proper environment variables

#### 4. Memory Errors

**Symptoms**: Out of memory errors, high memory usage

**Solutions**:
- Reduce batch size
- Increase system memory
- Optimize data processing
- Use streaming for large datasets

### Debugging

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debug output
python -m src.congress.main --debug

# View detailed logs
tail -f logs/opendiscourse.log
```

## Upgrading

### PyPI Upgrade

```bash
pip install --upgrade opendiscourse-congress opendiscourse-govinfo
```

### NPM Upgrade

```bash
npm update -g @opendiscourse/congress @opendiscourse/govinfo
```

### Docker Upgrade

```bash
docker pull opendiscourse/congress:latest
docker pull opendiscourse/govinfo:latest
docker-compose up -d --force-recreate
```

## Uninstallation

### PyPI Uninstall

```bash
pip uninstall opendiscourse-congress opendiscourse-govinfo
```

### NPM Uninstall

```bash
npm uninstall -g @opendiscourse/congress @opendiscourse/govinfo
```

### Docker Uninstall

```bash
docker stop congress-mcp govinfo-mcp
docker rm congress-mcp govinfo-mcp
docker rmi opendiscourse/congress opendiscourse/govinfo
```

## Configuration Examples

### Production Configuration

```python
# config/production_settings.py
from config.global_settings import GlobalSettings

settings = GlobalSettings(
    environment="production",
    debug=False,
    logging=LoggingConfig(
        level="WARNING",
        file_path="/var/log/opendiscourse/opendiscourse.log",
        max_file_size=50,
        backup_count=10
    ),
    database=DatabaseConfig(
        connection_string="postgresql://user:pass@db.example.com/opendiscourse",
        max_connections=20,
        ssl_enabled=True
    ),
    api=ApiConfig(
        max_concurrent_requests=10,
        request_timeout=120,
        retry_delay=5,
        max_retries=5
    )
)
```

### Development Configuration

```python
# config/development_settings.py
from config.global_settings import GlobalSettings

settings = GlobalSettings(
    environment="development",
    debug=True,
    logging=LoggingConfig(
        level="DEBUG",
        file_path="logs/opendiscourse-debug.log",
        json_format=False
    ),
    database=DatabaseConfig(
        connection_string="sqlite:///data/dev.db",
        max_connections=5
    ),
    api=ApiConfig(
        max_concurrent_requests=2,
        request_timeout=30,
        retry_delay=1,
        max_retries=2
    )
)
```

## Performance Tuning

### Optimization Tips

1. **Increase Batch Size**: Process more items per batch
2. **Adjust Concurrent Requests**: Find optimal concurrency level
3. **Enable Caching**: Cache frequent API responses
4. **Optimize Database**: Add indexes, optimize queries
5. **Monitor Performance**: Use monitoring tools

### Performance Configuration

```python
# config/performance_settings.py
from config.global_settings import GlobalSettings

settings = GlobalSettings(
    performance=PerformanceConfig(
        batch_size=500,
        worker_threads=8,
        cache_ttl=3600,
        memory_limit=4096
    ),
    api=ApiConfig(
        max_concurrent_requests=20,
        request_timeout=90,
        retry_delay=3,
        max_retries=3
    )
)
```

## Security Configuration

### Secure Production Setup

```python
# config/secure_settings.py
from config.global_settings import GlobalSettings

settings = GlobalSettings(
    security=SecurityConfig(
        api_key="your_secure_api_key",
        rate_limit=100,
        user_agent="OpenDiscourse-MCP-Secure/1.0",
        ssl_verify=True
    ),
    database=DatabaseConfig(
        connection_string="postgresql://secure_user:complex_password@secure-db.example.com/opendiscourse",
        ssl_enabled=True
    ),
    logging=LoggingConfig(
        level="INFO",
        file_path="/secure/logs/opendiscourse.log",
        max_file_size=100,
        backup_count=20
    )
)
```

## Next Steps

After installation, refer to:

- [Usage Guide](usage.md) for how to use the MCP servers
- [API Reference](api-reference/) for detailed API documentation
- [Development Guide](development/) for contributing to the project

## Support

If you encounter any issues during installation:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [FAQ](faq.md)
3. Open an issue on GitHub with detailed error information
4. Join our community discussions for help

Thank you for using OpenDiscourse MCP Servers! 🚀