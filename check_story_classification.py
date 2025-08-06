#!/usr/bin/env python3
"""
Check classification status of specific stories
"""

import sys
import os

# Add src directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations

def check_stories():
    db_ops = DatabaseOperations()
    
    with db_ops.db.get_cursor() as cursor:
        print("🔍 CHECKING STORY CLASSIFICATIONS")
        print("="*50)
        
        # Check the 4 stories that show as missing
        story_ids = [1001, 978, 977, 302]
        for story_id in story_ids:
            cursor.execute("""
                SELECT id, customer_name, is_gen_ai, 
                       extracted_data->>'ai_type' as ai_type,
                       CASE WHEN extracted_data->'gen_ai_superpowers' IS NOT NULL THEN 'HAS' ELSE 'MISSING' END as aileron_status
                FROM customer_stories
                WHERE id = %s
            """, [story_id])
            story = cursor.fetchone()
            if story:
                print(f"ID {story['id']}: {story['customer_name']}")
                print(f"  is_gen_ai (DB): {story['is_gen_ai']}")
                print(f"  ai_type (extracted): {story['ai_type']}")
                print(f"  Aileron data: {story['aileron_status']}")
                print()

if __name__ == "__main__":
    check_stories()