-- Database schema for OpenDiscourse MCP
-- This file contains all table definitions for the project

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) UNIQUE NOT NULL,
    key_value VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Data fetch logs table
CREATE TABLE IF NOT EXISTS data_fetch_logs (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    parameters TEXT,
    status VARCHAR(20) NOT NULL,
    response_time INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cached data table
CREATE TABLE IF NOT EXISTS cached_data (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    service VARCHAR(50) NOT NULL,
    data TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bulk download jobs table
CREATE TABLE IF NOT EXISTS bulk_download_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    service VARCHAR(50) NOT NULL,
    collection VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    parameters TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_api_keys_service ON api_keys(service);
CREATE INDEX IF NOT EXISTS idx_data_fetch_logs_service ON data_fetch_logs(service);
CREATE INDEX IF NOT EXISTS idx_data_fetch_logs_created_at ON data_fetch_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_cached_data_key ON cached_data(cache_key);
CREATE INDEX IF NOT EXISTS idx_cached_data_expires_at ON cached_data(expires_at);
CREATE INDEX IF NOT EXISTS idx_bulk_download_jobs_status ON bulk_download_jobs(status);
CREATE INDEX IF NOT EXISTS idx_bulk_download_jobs_created_at ON bulk_download_jobs(created_at);