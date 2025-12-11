#!/usr/bin/env python3
"""
Test Database Connection
"""

import sqlite3
from pathlib import Path

def test_db_connection(db_path: str):
    """Test database connection and basic operations"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 1:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False

def main():
    db_path = "data/govinfo_downloads.db"
    print(f"Testing database connection: {db_path}")
    
    if test_db_connection(db_path):
        print("✅ Database is accessible, ready for processing")
    else:
        print("❌ Database connection failed, check database file and permissions")

if __name__ == "__main__":
    main()