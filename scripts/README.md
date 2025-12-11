# OpenDiscourse MCP - Scripts

This directory contains utility scripts for managing the OpenDiscourse MCP project.

## setup_database.sh

Automated script to set up PostgreSQL database and user for OpenDiscourse MCP.

### Features

- 🗄️ **Database Creation**: Creates `opendiscourse` database
- 👤 **User Setup**: Creates `opendiscourse` user with password
- 🏗️ **Table Creation**: Creates all required database tables
- 🔍 **Service Detection**: Checks if PostgreSQL is installed/running
- 🧪 **Connection Testing**: Verifies database connectivity

### Database Schema

Creates these tables:

- **api_keys**: Stores encrypted API keys from Bitwarden
- **data_fetch_logs**: Logs API requests and responses
- **cached_data**: Caches API responses for performance
- **bulk_download_jobs**: Tracks bulk data download operations

### Usage

```bash
# Make script executable
chmod +x scripts/setup_database.sh

# Run database setup
./scripts/setup_database.sh
```

### Database Configuration

- **Host**: localhost
- **Port**: 5432
- **Database**: opendiscourse
- **User**: opendiscourse
- **Password**: opendiscourse123

### Prerequisites

1. **PostgreSQL**:
   ```bash
   # macOS
   brew install postgresql
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install postgresql postgresql-contrib
   ```

2. **Sudo access** (for database/user creation):
   ```bash
   # Script needs sudo to create database and user
   sudo ./scripts/setup_database.sh
   ```

### Manual Setup (if script fails)

```bash
# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# Create database
sudo -u postgres createdb opendiscourse

# Create user
sudo -u postgres createuser -s opendiscourse

# Set password
sudo -u postgres psql -c "ALTER USER opendiscourse PASSWORD 'opendiscourse123';"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO opendiscourse;"

# Create tables
psql -h localhost -p 5432 -U opendiscourse -d opendiscourse -f scripts/schema.sql
```

### Environment Variables

The script sets up these connection parameters:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=opendiscourse
DB_USER=opendiscourse
DB_PASS=opendiscourse123
```

### Troubleshooting

**PostgreSQL not found**:
```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt update && sudo apt install postgresql postgresql-contrib
```

**Permission denied**:
```bash
# Make sure PostgreSQL is running
brew services start postgresql
sudo systemctl start postgresql

# Check if user exists
sudo -u postgres psql -c "\du"
```

**Connection failed**:
```bash
# Check PostgreSQL status
brew services list | grep postgresql
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -p 5432 -U opendiscourse -d opendiscourse
```

### Security Notes

- 🔐 Database uses dedicated user with limited privileges
- 🗄️ No sensitive data logged in plain text
- 🔑 API keys are encrypted in database
- 🚫 Connection uses localhost only by default

### Integration with Bitwarden Script

After running database setup, use the Bitwarden script:

```bash
# Fetch API keys and store in database
python3 scripts/setup_bitwarden.py
```

This will:
1. 🔍 Fetch API keys from Bitwarden vault
2. 📝 Update .env file with keys
3. 🗄️ Store encrypted keys in database
4. 🧪 Test database connectivity