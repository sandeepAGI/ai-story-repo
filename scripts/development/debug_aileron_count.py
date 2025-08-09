#!/usr/bin/env python3
"""
Debug Aileron count discrepancy
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations

def debug_aileron_counts():
    db_ops = DatabaseOperations()
    
    with db_ops.db.get_cursor() as cursor:
        print("🔍 DEBUGGING AILERON COUNT DISCREPANCY")
        print("="*50)
        
        # Check Gen AI stories with Aileron data
        cursor.execute("""
            SELECT COUNT(*) as gen_ai_with_aileron
            FROM customer_stories
            WHERE is_gen_ai = TRUE 
            AND extracted_data->'gen_ai_superpowers' IS NOT NULL
        """)
        result1 = cursor.fetchone()
        
        # Check all Gen AI stories  
        cursor.execute("""
            SELECT COUNT(*) as total_gen_ai
            FROM customer_stories
            WHERE is_gen_ai = TRUE
        """)
        result2 = cursor.fetchone()
        
        # Check all stories with Aileron data
        cursor.execute("""
            SELECT COUNT(*) as total_with_aileron
            FROM customer_stories
            WHERE extracted_data->'gen_ai_superpowers' IS NOT NULL
        """)
        result3 = cursor.fetchone()
        
        # Check Non-Gen AI stories with Aileron data (shouldn't exist)
        cursor.execute("""
            SELECT id, customer_name, is_gen_ai
            FROM customer_stories
            WHERE is_gen_ai = FALSE 
            AND extracted_data->'gen_ai_superpowers' IS NOT NULL
            LIMIT 10
        """)
        non_gen_ai_with_aileron = cursor.fetchall()
        
        print(f"📊 COUNTS:")
        print(f"   Gen AI stories with Aileron data: {result1['gen_ai_with_aileron']}")
        print(f"   Total Gen AI stories: {result2['total_gen_ai']}")
        print(f"   Total stories with Aileron data: {result3['total_with_aileron']}")
        print(f"   Missing Gen AI Aileron: {result2['total_gen_ai'] - result1['gen_ai_with_aileron']}")
        print(f"   Non-Gen AI with Aileron: {len(non_gen_ai_with_aileron)}")
        
        print(f"\n🚨 NON-GEN AI STORIES WITH AILERON DATA:")
        if non_gen_ai_with_aileron:
            for story in non_gen_ai_with_aileron:
                print(f"   • ID {story['id']}: {story['customer_name']} (is_gen_ai: {story['is_gen_ai']})")
        else:
            print("   None found - Good!")
        
        # Check what the dashboard function would return
        cursor.execute("""
            SELECT 
                jsonb_array_elements_text(extracted_data->'gen_ai_superpowers') as superpower,
                COUNT(*) as count
            FROM customer_stories
            WHERE is_gen_ai = TRUE 
            AND extracted_data->'gen_ai_superpowers' IS NOT NULL
            GROUP BY superpower
            ORDER BY count DESC
            LIMIT 1
        """)
        
        dashboard_result = cursor.fetchone()
        if dashboard_result:
            print(f"\n📈 DASHBOARD QUERY TEST:")
            print(f"   Top superpower: {dashboard_result['superpower']} ({dashboard_result['count']} stories)")
            print(f"   This means dashboard should show {dashboard_result['count']} stories analyzed")

if __name__ == "__main__":
    debug_aileron_counts()