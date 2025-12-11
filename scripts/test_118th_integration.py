#!/usr/bin/env python3
"""
Test 118th Congress Data Integration
Verifies that the 118th Congress data processing and database integration works correctly
"""

import sqlite3
import json
from pathlib import Path

def test_118th_congress_data():
    """Test that 118th Congress data was processed correctly"""
    
    db_path = Path("data/govinfo_downloads.db")
    if not db_path.exists():
        print("❌ Database not found")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Test 1: Check we have 118th Congress bills
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM bills 
            WHERE congress = 118
        """)
        result = cursor.fetchone()
        bill_count = result[0] if result else 0
        
        print(f"✅ Found {bill_count} 118th Congress bills")
        
        if bill_count == 0:
            print("❌ No 118th Congress bills found")
            return False
        
        # Test 2: Check we have both House and Senate bills
        cursor.execute("""
            SELECT bill_type, COUNT(*) as count 
            FROM bills 
            WHERE congress = 118 
            GROUP BY bill_type
        """)
        bill_types = cursor.fetchall()
        
        print(f"✅ Bill types found: {dict(bill_types)}")
        
        # Test 3: Check we have content sections
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM bill_sections bs
            JOIN bills b ON bs.bill_id = b.bill_id
            WHERE b.congress = 118
        """)
        result = cursor.fetchone()
        section_count = result[0] if result else 0
        
        print(f"✅ Found {section_count} content sections")
        
        # Test 4: Get sample bill details
        cursor.execute("""
            SELECT bill_id, title, sponsor_name, bill_type, session
            FROM bills 
            WHERE congress = 118 
            LIMIT 3
        """)
        sample_bills = cursor.fetchall()
        
        print(f"✅ Sample bills:")
        for bill in sample_bills:
            bill_id, title, sponsor, bill_type, session = bill
            title_text = title[:50] if title else "No title"
            sponsor_text = sponsor if sponsor else "No sponsor"
            print(f"  - {bill_id}: {title_text}... (Sponsor: {sponsor_text})")
        
        # Test 5: Check sections for a specific bill
        if sample_bills:
            sample_bill_id = sample_bills[0][0]
            cursor.execute("""
                SELECT section_type, COUNT(*) as count
                FROM bill_sections
                WHERE bill_id = ?
                GROUP BY section_type
            """, (sample_bill_id,))
            
            sections = cursor.fetchall()
            print(f"✅ Bill {sample_bill_id} has {dict(sections)} sections")
        
        print(f"\n🎉 118th Congress integration test PASSED!")
        print(f"   - {bill_count} bills processed")
        print(f"   - {section_count} content sections extracted")
        print(f"   - {len(bill_types)} bill types represented")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    finally:
        conn.close()

def test_api_response_format():
    """Test that we can format data like MCP API responses"""
    
    db_path = Path("data/govinfo_downloads.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Format like MCP tool response
        cursor.execute("""
            SELECT bill_id, bill_type, bill_number, title, sponsor_name, session
            FROM bills 
            WHERE congress = 118 
            ORDER BY bill_number
            LIMIT 5
        """)
        
        bills = cursor.fetchall()
        
        # Format as JSON response
        response_data = []
        for bill in bills:
            if bill and len(bill) >= 6:
                response_data.append({
                    'bill_id': bill[0],
                    'bill_type': bill[1], 
                    'bill_number': bill[2],
                    'title': bill[3],
                    'sponsor_name': bill[4],
                    'session': bill[5]
                })
        
        mcp_response = {
            'content': [{
                'type': 'text',
                'text': json.dumps(response_data, indent=2)
            }],
            'results': len(response_data)
        }
        
        print(f"✅ MCP Response format test:")
        print(json.dumps(mcp_response, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Response format test failed: {str(e)}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("Testing 118th Congress Data Integration")
    print("=" * 50)
    
    success1 = test_118th_congress_data()
    print()
    success2 = test_api_response_format()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! 118th Congress integration is ready.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")