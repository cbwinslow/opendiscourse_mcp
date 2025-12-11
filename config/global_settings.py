#!/usr/bin/env python3
"""
Global Settings for OpenDiscourse MCP Servers

This module provides centralized configuration management for both
Congress.gov and GovInfo.gov MCP servers using Pydantic for
validation and environment variable support.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, SecretStr
import os
from pathlib import Path

class DatabaseConfig(BaseModel):
    """
    Database connection configuration

    Attributes:
        connection_string: Database connection URL
        max_connections: Maximum database connections
        timeout: Connection timeout in seconds
        ssl_enabled: Enable SSL for database connections
    """
    connection_string: str = Field(
        default="sqlite:///data/opendiscourse.db",
        description="Database connection URL (SQLite, PostgreSQL, etc.)",
        env="DATABASE_URL"
    )
    max_connections: int = Field(
        default=10,
        description="Maximum database connections in pool",
        ge=1,
        le=100
    )
    timeout: int = Field(
        default=30,
        description="Database connection timeout in seconds",
        ge=5,
        le=300
    )
    ssl_enabled: bool = Field(
        default=False,
        description="Enable SSL for database connections",
        env="DATABASE_SSL"
    )

class ApiConfig(BaseModel):
    """
    API configuration for government data sources

    Attributes:
        congress_base_url: Base URL for Congress.gov API
        govinfo_base_url: Base URL for GovInfo.gov API
        max_concurrent_requests: Maximum concurrent API requests
        request_timeout: API request timeout in seconds
        retry_delay: Initial retry delay in seconds
        max_retries: Maximum retry attempts for failed requests
    """
    congress_base_url: str = Field(
        default="https://api.congress.gov/v3",
        description="Base URL for Congress.gov API",
        env="CONGRESS_API_URL"
    )
    govinfo_base_url: str = Field(
        default="https://api.govinfo.gov",
        description="Base URL for GovInfo.gov API",
        env="GOVINFO_API_URL"
    )
    max_concurrent_requests: int = Field(
        default=5,
        description="Maximum concurrent API requests",
        ge=1,
        le=50
    )
    request_timeout: int = Field(
        default=60,
        description="API request timeout in seconds",
        ge=10,
        le=300
    )
    retry_delay: int = Field(
        default=2,
        description="Initial retry delay in seconds",
        ge=1,
        le=60
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed requests",
        ge=0,
        le=10
    )

class LoggingConfig(BaseModel):
    """
    Logging configuration

    Attributes:
        level: Minimum logging level
        file_path: Log file path
        max_file_size: Maximum log file size in MB
        backup_count: Number of log files to keep
        json_format: Use JSON format for logs
    """
    level: str = Field(
        default="INFO",
        description="Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        env="LOG_LEVEL"
    )
    file_path: str = Field(
        default="logs/opendiscourse.log",
        description="Path for log file"
    )
    max_file_size: int = Field(
        default=10,
        description="Maximum log file size in MB",
        ge=1,
        le=100
    )
    backup_count: int = Field(
        default=5,
        description="Number of log files to keep",
        ge=1,
        le=20
    )
    json_format: bool = Field(
        default=True,
        description="Use JSON format for logs"
    )

class PerformanceConfig(BaseModel):
    """
    Performance tuning configuration

    Attributes:
        batch_size: Default batch size for data processing
        worker_threads: Number of worker threads
        cache_ttl: Cache time-to-live in seconds
        memory_limit: Memory limit in MB (0 for no limit)
    """
    batch_size: int = Field(
        default=100,
        description="Default batch size for data processing",
        ge=10,
        le=1000
    )
    worker_threads: int = Field(
        default=4,
        description="Number of worker threads for parallel processing",
        ge=1,
        le=32
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache time-to-live in seconds",
        ge=60,
        le=86400
    )
    memory_limit: int = Field(
        default=2048,
        description="Memory limit in MB (0 for no limit)",
        ge=0,
        le=16384
    )

class SecurityConfig(BaseModel):
    """
    Security configuration

    Attributes:
        api_key: API key for authentication (if required)
        rate_limit: Maximum requests per minute
        user_agent: Custom user agent string
        ssl_verify: Verify SSL certificates
    """
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key for authentication (if required)",
        env="API_KEY"
    )
    rate_limit: int = Field(
        default=60,
        description="Maximum requests per minute",
        ge=10,
        le=1000
    )
    user_agent: str = Field(
        default="OpenDiscourse-MCP/1.0",
        description="Custom user agent string"
    )
    ssl_verify: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )

class GlobalSettings(BaseModel):
    """
    Global application settings for OpenDiscourse MCP Servers

    This class combines all configuration sections and provides
    environment variable overrides and validation.
    """
    database: DatabaseConfig = DatabaseConfig()
    api: ApiConfig = ApiConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    security: SecurityConfig = SecurityConfig()

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        env="DEBUG"
    )
    environment: str = Field(
        default="development",
        description="Deployment environment (development, staging, production)",
        env="ENVIRONMENT"
    )
    data_directory: str = Field(
        default="data",
        description="Directory for storing downloaded data"
    )
    temp_directory: str = Field(
        default="temp",
        description="Directory for temporary files"
    )
    max_log_days: int = Field(
        default=30,
        description="Maximum days to keep log files",
        ge=1,
        le=365
    )

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value"""
        valid_envs = ['development', 'staging', 'production', 'test']
        if v not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v

    @validator('data_directory', 'temp_directory')
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_congress_config(self) -> Dict[str, Any]:
        """Get Congress.gov specific configuration"""
        return {
            "base_url": self.api.congress_base_url,
            "max_concurrent": self.api.max_concurrent_requests,
            "timeout": self.api.request_timeout,
            "retries": self.api.max_retries,
            "retry_delay": self.api.retry_delay,
            "rate_limit": self.security.rate_limit,
            "user_agent": self.security.user_agent,
            "ssl_verify": self.security.ssl_verify,
            "api_key": self.security.api_key.get_secret_value() if self.security.api_key else None
        }

    def get_govinfo_config(self) -> Dict[str, Any]:
        """Get GovInfo.gov specific configuration"""
        return {
            "base_url": self.api.govinfo_base_url,
            "max_concurrent": self.api.max_concurrent_requests,
            "timeout": self.api.request_timeout,
            "retries": self.api.max_retries,
            "retry_delay": self.api.retry_delay,
            "rate_limit": self.security.rate_limit,
            "user_agent": self.security.user_agent,
            "ssl_verify": self.security.ssl_verify,
            "api_key": self.security.api_key.get_secret_value() if self.security.api_key else None
        }

# Initialize global settings with environment variable overrides
settings = GlobalSettings()

def get_settings() -> GlobalSettings:
    """
    Get the global settings instance

    Returns:
        GlobalSettings: Configured settings instance
    """
    return settings

def reload_settings() -> GlobalSettings:
    """
    Reload settings from environment variables

    Returns:
        GlobalSettings: Fresh settings instance
    """
    global settings
    settings = GlobalSettings()
    return settings

if __name__ == "__main__":
    # Example usage and validation
    print("OpenDiscourse MCP Servers - Global Configuration")
    print("=" * 50)
    print(f"Environment: {settings.environment}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Database: {settings.database.connection_string}")
    print(f"Congress API: {settings.api.congress_base_url}")
    print(f"GovInfo API: {settings.api.govinfo_base_url}")
    print(f"Max Concurrent Requests: {settings.api.max_concurrent_requests}")
    print(f"Log Level: {settings.logging.level}")
    print(f"Data Directory: {settings.data_directory}")
    print(f"Temp Directory: {settings.temp_directory}")

    # Validate configuration
    try:
        # Test database connection string format
        if not settings.database.connection_string.startswith(('sqlite://', 'postgresql://', 'mysql://')):
            print("⚠️  Warning: Database connection string may be invalid")

        # Test API URLs
        for url in [settings.api.congress_base_url, settings.api.govinfo_base_url]:
            if not url.startswith('http'):
                print(f"⚠️  Warning: API URL {url} may be invalid")

        print("✅ Configuration validation complete")

    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        raise