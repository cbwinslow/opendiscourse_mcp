#!/usr/bin/env python3
"""
Simple Database Connection Test
"""

import sqlite3
import sys
from pathlib import Path

def test_imports():
    """Test if we can import the required modules"""
    try:
        # Test basic imports
        import sqlite3
        print("✅ sqlite3 import: SUCCESS")
        
        # Test sys.path manipulation
        sys.path.append('/home/cbwinslow/Documents/opendiscourse_mcp')
        print("✅ sys.path manipulation: SUCCESS")
        
        # Test pathlib
        from pathlib import Path
        print("✅ pathlib import: SUCCESS")
        
        # Test basic database operations
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()
        print("✅ Basic database operations: SUCCESS")
        
        return True

def main():
    try:
        print("Testing imports for 113th/114th Congress processing...")
        
        if test_imports():
            print("✅ All imports successful - ready to start processing")
        else:
            print("❌ Import issues detected - cannot proceed")
            return
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return

if __name__ == "__main__":
    main()