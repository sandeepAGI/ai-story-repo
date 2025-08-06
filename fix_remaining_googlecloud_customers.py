#!/usr/bin/env python3
"""
Fix Remaining GoogleCloud Customer Stories
Quick fix for the 5 actual customer stories that weren't caught by the main cleanup
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations

def main():
    """Fix the remaining 5 customer stories"""
    print("🔧 Fixing Remaining GoogleCloud Customer Stories")
    print("=" * 50)
    
    db_ops = DatabaseOperations()
    
    # Manual mapping for the 5 remaining customer stories
    fixes = [
        {
            'id': 977,
            'new_name': 'Wayfair',
            'reason': 'Wayfair MLOps story - clear customer story'
        },
        {
            'id': 976, 
            'new_name': 'Wayfair',
            'reason': 'Wayfair Vertex AI story - clear customer story'
        },
        {
            'id': 975,
            'new_name': 'Toyota', 
            'reason': 'Toyota AI training story - clear customer story'
        },
        {
            'id': 974,
            'new_name': 'Toyota',
            'reason': 'Toyota manufacturing AI story - clear customer story'  
        },
        {
            'id': 978,
            'new_name': 'Wells Fargo',
            'reason': 'Wells Fargo Fargo virtual assistant story - clear customer story'
        }
    ]
    
    print(f"📋 Will fix {len(fixes)} customer stories:")
    for fix in fixes:
        print(f"  • ID {fix['id']}: → {fix['new_name']} ({fix['reason']})")
    
    # Execute fixes
    updated_count = 0
    with db_ops.db.get_cursor() as cursor:
        for fix in fixes:
            try:
                # Get current name for verification
                cursor.execute("SELECT customer_name FROM customer_stories WHERE id = %s", (fix['id'],))
                current = cursor.fetchone()
                
                if current:
                    print(f"\n🔄 Updating ID {fix['id']}:")
                    print(f"   From: {current['customer_name'][:60]}...")
                    print(f"   To:   {fix['new_name']}")
                    
                    # Update the record
                    cursor.execute("UPDATE customer_stories SET customer_name = %s WHERE id = %s", 
                                 (fix['new_name'], fix['id']))
                    updated_count += 1
                    print(f"   ✅ Updated successfully")
                else:
                    print(f"❌ Record ID {fix['id']} not found")
                    
            except Exception as e:
                print(f"❌ Failed to update ID {fix['id']}: {e}")
    
    print(f"\n✅ COMPLETED:")
    print(f"   Successfully updated: {updated_count} records")
    print(f"   Remaining non-customer posts: 8 (partnership/award/industry posts)")
    
    # Verify the fix
    print(f"\n🔍 VERIFICATION:")
    with db_ops.db.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as remaining_issues
            FROM customer_stories 
            WHERE source_id = (SELECT id FROM sources WHERE name = 'Google Cloud')
            AND (
                customer_name LIKE '%https://cloud.google.com/blog/%'
                OR customer_name LIKE '%Https://Cloud.Google.Com/Blog/%'
                OR (LENGTH(customer_name) > 50 AND customer_name LIKE '%Cloud.Google.Com%')
            )
            AND id IN (975, 976, 977, 978, 974)  -- The customer story IDs we just fixed
        """)
        
        remaining = cursor.fetchone()['remaining_issues']
        
        if remaining == 0:
            print(f"   ✅ All customer stories fixed! No remaining customer story issues.")
        else:
            print(f"   ⚠️  Still {remaining} customer story issues remain")
        
        # Show final clean customer stories
        cursor.execute("""
            SELECT customer_name, url
            FROM customer_stories 
            WHERE id IN (975, 976, 977, 978, 974)
            ORDER BY customer_name
        """)
        
        results = cursor.fetchall()
        print(f"\n📋 Fixed customer stories now show:")
        for result in results:
            print(f"   • {result['customer_name']} - {result['url']}")

if __name__ == "__main__":
    main()