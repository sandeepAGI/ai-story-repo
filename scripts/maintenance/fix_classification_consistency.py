#!/usr/bin/env python3
"""
Fix is_gen_ai field consistency with ai_type classification
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations

def fix_classification_consistency():
    db_ops = DatabaseOperations()
    story_ids = [1001, 978, 977, 302]

    with db_ops.db.get_cursor() as cursor:
        print("🔧 UPDATING is_gen_ai FIELD TO MATCH AI_TYPE CLASSIFICATION")
        print("="*60)
        
        for story_id in story_ids:
            # Check current status
            cursor.execute("""
                SELECT id, customer_name, is_gen_ai, extracted_data->>'ai_type' as ai_type
                FROM customer_stories 
                WHERE id = %s
            """, [story_id])
            story = cursor.fetchone()
            
            if story:
                print(f"📝 Story ID {story['id']}: {story['customer_name']}")
                print(f"   Current is_gen_ai: {story['is_gen_ai']}")
                print(f"   Current ai_type: {story['ai_type']}")
                
                if story['ai_type'] == 'traditional' and story['is_gen_ai'] == True:
                    # Update is_gen_ai to FALSE for Traditional AI stories
                    cursor.execute("""
                        UPDATE customer_stories 
                        SET is_gen_ai = FALSE
                        WHERE id = %s
                    """, [story_id])
                    
                    print(f"   ✅ Updated: is_gen_ai = FALSE")
                elif story['ai_type'] == 'generative' and story['is_gen_ai'] == False:
                    # Update is_gen_ai to TRUE for Gen AI stories  
                    cursor.execute("""
                        UPDATE customer_stories 
                        SET is_gen_ai = TRUE
                        WHERE id = %s
                    """, [story_id])
                    
                    print(f"   ✅ Updated: is_gen_ai = TRUE")
                else:
                    print(f"   ℹ️  No update needed - already consistent")
                
                print()
        
        # Commit the changes
        cursor.connection.commit()
        print("✅ Database updated successfully!")
        
        # Verify the changes
        print("\n🔍 VERIFICATION:")
        print("-" * 30)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM customer_stories
            WHERE is_gen_ai = TRUE
        """)
        gen_ai_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count  
            FROM customer_stories
            WHERE is_gen_ai = TRUE 
            AND extracted_data->'gen_ai_superpowers' IS NOT NULL
        """)
        gen_ai_with_aileron = cursor.fetchone()['count']
        
        print(f"Gen AI stories: {gen_ai_count}")
        print(f"Gen AI with Aileron: {gen_ai_with_aileron}")
        print(f"Missing Aileron: {gen_ai_count - gen_ai_with_aileron}")

if __name__ == "__main__":
    fix_classification_consistency()