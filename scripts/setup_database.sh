#!/bin/bash
# Database Setup Script for OpenDiscourse MCP
# This script sets up PostgreSQL database and user

echo "🗄️ OpenDiscourse MCP - Database Setup"
echo "=================================="

# Database configuration
DB_NAME="opendiscourse"
DB_USER="opendiscourse"
DB_PASS="opendiscourse123"
DB_HOST="localhost"
DB_PORT="5432"

echo "📋 Database Configuration:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"

# Check if PostgreSQL is running
echo ""
echo "🔍 Checking PostgreSQL status..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client found"
else
    echo "❌ PostgreSQL client not found"
    echo "Installing PostgreSQL..."
    if command -v brew &> /dev/null; then
        brew install postgresql
    elif command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y postgresql postgresql-contrib
    else
        echo "Please install PostgreSQL manually"
        exit 1
    fi
fi

# Check if PostgreSQL service is running
echo ""
echo "🔍 Checking PostgreSQL service..."
if command -v pg_isready &> /dev/null; then
    if pg_isready -h $DB_HOST -p $DB_PORT; then
        echo "✅ PostgreSQL is running"
    else
        echo "❌ PostgreSQL is not running"
        echo "Starting PostgreSQL..."
        if command -v brew &> /dev/null; then
            brew services start postgresql
        elif command -v systemctl &> /dev/null; then
            sudo systemctl start postgresql
        else
            echo "Please start PostgreSQL manually"
        fi
    fi
else
    echo "⚠️ Cannot check PostgreSQL status - assuming it's running"
fi

# Create database and user
echo ""
echo "🔧 Setting up database and user..."

# Try to connect as postgres superuser to create database/user
if command -v sudo &> /dev/null; then
    echo "Creating database and user..."
    
    # Create database
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database may already exist"
    
    # Create user
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "User may already exist"
    
    # Grant privileges
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;" 2>/dev/null
    
    echo "✅ Database and user setup complete"
else
    echo "❌ Cannot setup database without sudo access"
    echo "Please run this script with sudo or setup manually:"
    echo "  sudo -u postgres create database $DB_NAME"
    echo "  sudo -u postgres create user $DB_USER"
    echo "  sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""
fi

# Test connection
echo ""
echo "🧪 Testing database connection..."
export PGPASSWORD="$DB_PASS"

if command -v psql &> /dev/null; then
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();" &> /dev/null; then
        echo "✅ Database connection successful!"
        
        # Create tables
        echo ""
        echo "🏗️ Creating database tables..."
        
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF'
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
EOF

        if [ $? -eq 0 ]; then
            echo "✅ Database tables created successfully"
        else
            echo "❌ Failed to create database tables"
        fi
    else
        echo "❌ Database connection test failed"
    fi
else
    echo "❌ psql command not found"
fi

echo ""
echo "🎉 Database setup complete!"
echo ""
echo "📝 Connection Information:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""
echo "You can now run the Bitwarden setup script:"
echo "  python3 scripts/setup_bitwarden.py"