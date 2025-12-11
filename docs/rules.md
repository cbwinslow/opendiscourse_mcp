# Development Guidelines and Rules

## 1. Code Quality Standards

### 1.1 Python Coding Standards
- **PEP 8 Compliance**: Follow Python style guide strictly
- **Type Hints**: Use Python type hints for all functions and methods
- **Docstrings**: Comprehensive docstrings for all public functions
- **Pydantic Models**: Use Pydantic for data validation and settings

```python
# Example of proper Python code structure
from pydantic import BaseModel, Field

class ApiConfig(BaseModel):
    """Configuration for API connections"""
    base_url: str = Field(..., description="Base API URL")
    api_key: str = Field(..., description="API authentication key")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")

def fetch_data(config: ApiConfig, endpoint: str) -> dict:
    """
    Fetch data from API endpoint with retry logic

    Args:
        config: API configuration
        endpoint: API endpoint to call

    Returns:
        dict: Parsed JSON response

    Raises:
        ApiError: If request fails after retries
    """
    # Implementation with proper error handling
```

### 1.2 TypeScript Coding Standards
- **Strict Typing**: Use TypeScript strict mode
- **Interfaces**: Define interfaces for all data structures
- **JSDoc Comments**: Comprehensive documentation
- **ESLint**: Follow ESLint recommended rules

```typescript
// Example of proper TypeScript code structure
interface ApiConfig {
    baseUrl: string;
    apiKey: string;
    timeout: number;
    maxRetries: number;
}

/**
 * Fetch data from API endpoint with retry logic
 * @param config API configuration
 * @param endpoint API endpoint to call
 * @returns Promise with parsed JSON response
 * @throws ApiError if request fails after retries
 */
async function fetchData(config: ApiConfig, endpoint: string): Promise<any> {
    // Implementation with proper error handling
}
```

## 2. Project Structure Rules

### 2.1 Directory Structure
```
opendiscourse-mcp/
├── config/                  # Configuration files
│   ├── global_settings.py   # Global settings (Python)
│   ├── global_settings.ts   # Global settings (TypeScript)
│   └── .env.example         # Environment variable template
├── docs/                    # Documentation
├── src/                     # Source code
│   ├── congress/            # Congress.gov MCP Server
│   │   ├── client.py        # API client
│   │   ├── models.py        # Data models
│   │   ├── tools.py         # MCP tools
│   │   └── main.py          # Server entry point
│   ├── govinfo/             # GovInfo.gov MCP Server
│   │   ├── client.py        # API client
│   │   ├── models.py        # Data models
│   │   ├── tools.py         # MCP tools
│   │   └── main.py          # Server entry point
│   └── shared/              # Shared components
│       ├── config.py        # Configuration management
│       ├── logging.py       # Logging utilities
│       └── utils.py         # Common utilities
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
└── .gitignore               # Git ignore rules
```

### 2.2 Separation of Concerns
- **Strict Separation**: Congress.gov and GovInfo.gov logic must be completely separate
- **No Cross-Imports**: Servers should not import from each other
- **Shared Components**: Common utilities in `shared/` directory
- **Clear Boundaries**: Well-defined interfaces between components

## 3. Configuration Management

### 3.1 Global Settings File
- **Location**: `config/global_settings.py` (Python) / `config/global_settings.ts` (TypeScript)
- **Purpose**: Centralized configuration for both servers
- **Requirements**:
  - Use Pydantic for Python settings
  - Use TypeScript interfaces for TS settings
  - Support environment variable overrides
  - Include comprehensive documentation

### 3.2 Environment Variables
- **Prefix**: Use `CONGRESS_` and `GOVINFO_` prefixes for server-specific vars
- **Validation**: Validate all environment variables on startup
- **Defaults**: Provide sensible defaults where possible
- **Security**: Never commit `.env` files to version control

### 3.3 Configuration Example
```python
# config/global_settings.py
from pydantic import BaseModel, Field
from typing import Optional
import os

class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    connection_string: str = Field(
        default="sqlite:///data.db",
        description="Database connection URL"
    )
    max_connections: int = Field(
        default=10,
        description="Maximum database connections"
    )
    timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )

class ApiConfig(BaseModel):
    """API configuration"""
    congress_base_url: str = Field(
        default="https://api.congress.gov",
        description="Congress.gov API base URL"
    )
    govinfo_base_url: str = Field(
        default="https://api.govinfo.gov",
        description="GovInfo.gov API base URL"
    )
    max_concurrent_requests: int = Field(
        default=5,
        description="Maximum concurrent API requests"
    )
    request_timeout: int = Field(
        default=60,
        description="API request timeout in seconds"
    )

class GlobalSettings(BaseModel):
    """Global application settings"""
    database: DatabaseConfig = DatabaseConfig()
    api: ApiConfig = ApiConfig()
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

# Load settings with environment variable overrides
settings = GlobalSettings()
```

## 4. Error Handling Rules

### 4.1 Error Classification
- **Transient Errors**: Network issues, timeouts (automatic retry)
- **Configuration Errors**: Invalid settings (fail fast)
- **Data Errors**: Invalid data formats (log and skip)
- **Critical Errors**: Unrecoverable failures (crash with details)

### 4.2 Error Handling Pattern
```python
from typing import Optional, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ApiError(Exception):
    """Base class for API errors"""
    pass

class RateLimitError(ApiError):
    """API rate limit exceeded"""
    pass

class DataValidationError(ApiError):
    """Data validation failed"""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=(RateLimitError, ConnectionError)
)
def fetch_with_retry(url: str, params: Optional[dict] = None) -> Any:
    """
    Fetch data with automatic retry for transient errors

    Args:
        url: API endpoint URL
        params: Query parameters

    Returns:
        Parsed response data

    Raises:
        ApiError: For unrecoverable errors
    """
    try:
        # Implementation with proper error handling
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        # Validate response data
        if not response.json():
            raise DataValidationError("Empty response received")

        return response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            raise RateLimitError("Rate limit exceeded") from e
        raise ApiError(f"HTTP error: {str(e)}") from e
    except requests.exceptions.RequestException as e:
        logger.warning(f"Transient error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise ApiError(f"Unexpected error: {str(e)}") from e
```

## 5. Logging Rules

### 5.1 Logging Levels
- **DEBUG**: Detailed development information
- **INFO**: Normal operation messages
- **WARNING**: Potential issues
- **ERROR**: Serious problems
- **CRITICAL**: System failures

### 5.2 Logging Format
```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [MODULE] - Message
```

### 5.3 Logging Implementation
```python
import logging
from pythonjsonlogger import jsonlogger

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging with JSON formatter

    Args:
        log_level: Minimum logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger("opendiscourse")
    logger.setLevel(log_level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger
```

## 6. Testing Rules

### 6.1 Test Coverage Requirements
- **Unit Tests**: 90%+ coverage for core modules
- **Integration Tests**: Critical path coverage
- **End-to-End Tests**: User journey validation
- **Performance Tests**: Load and stress testing

### 6.2 Testing Framework
- **Python**: `pytest` with `pytest-cov`
- **TypeScript**: `jest` with `ts-jest`
- **Mocking**: `unittest.mock` (Python) / `jest.mock` (TS)

### 6.3 Test Structure
```
tests/
├── unit/
│   ├── congress/
│   │   ├── test_client.py
│   │   ├── test_models.py
│   │   └── test_tools.py
│   ├── govinfo/
│   │   ├── test_client.py
│   │   ├── test_models.py
│   │   └── test_tools.py
│   └── shared/
│       ├── test_config.py
│       └── test_utils.py
├── integration/
│   ├── test_congress_integration.py
│   └── test_govinfo_integration.py
└── e2e/
    ├── test_workflow.py
    └── test_performance.py
```

## 7. Documentation Rules

### 7.1 Documentation Standards
- **Markdown Format**: All documentation in `.md` files
- **Comprehensive**: Cover all public APIs and features
- **Examples**: Include usage examples
- **Up-to-Date**: Documentation must match implementation

### 7.2 Documentation Structure
```
docs/
├── README.md                    # Main documentation
├── features.md                  # Feature specifications
├── srs.md                       # Software requirements
├── project_summary.md           # Project overview
├── rules.md                     # Development guidelines (this file)
├── api-reference/               # API documentation
│   ├── congress-api.md          # Congress API reference
│   └── govinfo-api.md           # GovInfo API reference
├── installation/                # Installation guides
│   ├── python-installation.md   # Python setup
│   ├── typescript-installation.md # TypeScript setup
│   └── docker-installation.md   # Docker setup
├── usage/                       # Usage examples
│   ├── congress-usage.md        # Congress usage
│   └── govinfo-usage.md         # GovInfo usage
└── development/                 # Developer docs
    ├── architecture.md          # System architecture
    ├── testing.md               # Testing guide
    └── contributing.md          # Contribution guidelines
```

## 8. Security Rules

### 8.1 Secret Management
- **Never Commit Secrets**: No API keys in source code
- **Environment Variables**: Use `.env` files for local development
- **Secret Rotation**: Implement key rotation procedures
- **Access Control**: Restrict access to sensitive data

### 8.2 Data Protection
- **Encryption**: Encrypt sensitive data at rest
- **HTTPS**: Use secure connections for all API calls
- **Input Validation**: Validate all external inputs
- **Output Sanitization**: Sanitize all outputs

### 8.3 Dependency Security
- **Regular Audits**: Check for vulnerable dependencies
- **Minimal Dependencies**: Keep dependency tree small
- **Version Pinning**: Pin dependency versions
- **Update Procedures**: Regular dependency updates

## 9. Performance Rules

### 9.1 Performance Optimization
- **Batch Processing**: Process data in batches
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache frequent API responses
- **Memory Management**: Monitor and optimize memory usage

### 9.2 Performance Metrics
- **Throughput**: Documents processed per second
- **Latency**: Response time for MCP calls
- **Memory Usage**: Peak memory consumption
- **CPU Usage**: Processing efficiency

## 10. Deployment Rules

### 10.1 Versioning
- **Semantic Versioning**: `MAJOR.MINOR.PATCH`
- **Pre-release Versions**: Use `-alpha`, `-beta`, `-rc` suffixes
- **Version Tags**: Git tags for releases

### 10.2 Release Process
1. **Feature Freeze**: Stop adding new features
2. **Testing Phase**: Comprehensive testing
3. **Documentation Review**: Update all documentation
4. **Release Candidate**: Create RC version
5. **Final Release**: Publish stable version

### 10.3 Distribution Channels
- **PyPI**: Python package distribution
- **NPM**: TypeScript package distribution
- **Docker Hub**: Container images
- **GitHub Releases**: Source code releases

## 11. Code Review Process

### 11.1 Review Requirements
- **Minimum Approvals**: 2 approvals for core changes
- **Checklist**: Complete review checklist
- **Testing**: All tests must pass
- **Documentation**: Documentation must be updated

### 11.2 Review Checklist
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Performance considered
- [ ] Security reviewed
- [ ] No hardcoded secrets

## 12. Branch Strategy

### 12.1 Git Branching Model
- **main**: Production-ready code
- **develop**: Integration branch
- **feature/**: Feature development
- **bugfix/**: Bug fixes
- **release/**: Release preparation

### 12.2 Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
**Scope**: `congress`, `govinfo`, `shared`, `config`, `tests`

## 13. Continuous Integration

### 13.1 CI Pipeline Requirements
- **Automated Testing**: Run on every push
- **Code Quality Checks**: Linting and formatting
- **Build Verification**: Ensure build succeeds
- **Artifact Generation**: Create distribution packages

### 13.2 CI Configuration Example
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2

    - name: Lint code
      run: |
        flake8 src/
        black --check src/
        isort --check-only src/
```

## 14. Dependency Management

### 14.1 Python Dependencies
- **Core**: Minimal required dependencies
- **Development**: Testing and linting tools
- **Optional**: Additional features

### 14.2 Dependency Files
- **requirements.txt**: Production dependencies
- **requirements-dev.txt**: Development dependencies
- **pyproject.toml**: Modern Python project configuration

## 15. Internationalization

### 15.1 i18n Requirements
- **Unicode Support**: Full Unicode compatibility
- **Timezone Handling**: Proper timezone management
- **Locale Support**: Configurable locale settings

### 15.2 Date/Time Handling
```python
from datetime import datetime
import pytz

def get_current_time(timezone: str = "UTC") -> datetime:
    """
    Get current time in specified timezone

    Args:
        timezone: IANA timezone name

    Returns:
        datetime: Current time in specified timezone
    """
    tz = pytz.timezone(timezone)
    return datetime.now(tz)
```

## 16. Accessibility

### 16.1 Accessibility Guidelines
- **Color Contrast**: Sufficient contrast for readability
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: Proper ARIA attributes
- **Internationalization**: Language support

## 17. Legal Compliance

### 17.1 License Requirements
- **Open Source**: Use MIT or Apache 2.0 license
- **Attribution**: Proper attribution of dependencies
- **Data Usage**: Compliance with data source terms

### 17.2 License File
```
MIT License

Copyright (c) 2025 OpenDiscourse

Permission is hereby granted...
```

## 18. Community Guidelines

### 18.1 Contribution Rules
- **Code of Conduct**: Respectful communication
- **Issue Tracking**: Use GitHub issues
- **Pull Requests**: Follow contribution guidelines
- **Documentation**: Update docs with changes

### 18.2 Support Channels
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community discussions
- **Documentation**: Comprehensive guides

## 19. Monitoring and Maintenance

### 19.1 Monitoring Requirements
- **Health Checks**: Regular system checks
- **Performance Metrics**: Track key metrics
- **Error Tracking**: Monitor and alert on errors
- **Usage Analytics**: Track feature usage

### 19.2 Maintenance Procedures
- **Regular Updates**: Security and dependency updates
- **Bug Fixes**: Prompt issue resolution
- **Feature Enhancements**: Continuous improvement
- **Documentation Updates**: Keep docs current

## 20. Future-Proofing

### 20.1 Extensibility Rules
- **Plugin Architecture**: Support for additional data sources
- **Configuration-Driven**: Minimal hardcoded values
- **Backward Compatibility**: Maintain API compatibility
- **Deprecation Policy**: Clear deprecation warnings

### 20.2 Technology Watch
- **Regular Reviews**: Evaluate new technologies
- **Upgrade Paths**: Plan for technology upgrades
- **Community Feedback**: Incorporate user suggestions

## Appendix: Tools and Libraries

### Recommended Tools
- **Python**: `black`, `flake8`, `isort`, `mypy`, `pytest`
- **TypeScript**: `eslint`, `prettier`, `typescript`, `jest`
- **Documentation**: `mkdocs`, `sphinx`, `docusaurus`
- **CI/CD**: `GitHub Actions`, `GitLab CI`, `CircleCI`

### Recommended Libraries
- **Python**: `pydantic`, `requests`, `tenacity`, `structlog`, `sqlalchemy`
- **TypeScript**: `axios`, `zod`, `winston`, `typeorm`
- **Testing**: `pytest`, `jest`, `mock-service-worker`

This document serves as the comprehensive development guidelines for the OpenDiscourse MCP Servers project. All contributors are expected to follow these rules to ensure code quality, consistency, and maintainability.