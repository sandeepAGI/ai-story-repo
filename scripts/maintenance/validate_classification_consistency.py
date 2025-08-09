#!/usr/bin/env python3
"""
Validate and fix classification consistency across the database.
This script ensures is_gen_ai database field matches ai_type in extracted_data.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations
from ai_integration.claude_processor import ClaudeProcessor

def validate_all_classifications():
    """Validate and fix classification consistency for all stories"""
    db_ops = DatabaseOperations()
    processor = ClaudeProcessor()
    
    print("🔍 VALIDATING CLASSIFICATION CONSISTENCY")
    print("=" * 60)
    
    with db_ops.db.get_cursor() as cursor:
        # Find all stories with potential consistency issues
        cursor.execute("""
            SELECT id, customer_name, is_gen_ai, extracted_data
            FROM customer_stories
            WHERE extracted_data IS NOT NULL
            AND (
                (is_gen_ai = TRUE AND extracted_data->>'ai_type' = 'traditional') OR
                (is_gen_ai = FALSE AND extracted_data->>'ai_type' = 'generative') OR
                (is_gen_ai IS NULL AND extracted_data->>'ai_type' IS NOT NULL)
            )
            ORDER BY id
        """)
        
        inconsistent_stories = cursor.fetchall()
        
        if not inconsistent_stories:
            print("✅ No classification consistency issues found!")
            return
        
        print(f"⚠️  Found {len(inconsistent_stories)} stories with consistency issues:")
        print()
        
        fixes_applied = 0
        
        for story in inconsistent_stories:
            story_id = story['id']
            customer_name = story['customer_name']
            current_is_gen_ai = story['is_gen_ai']
            extracted_data = story['extracted_data'] or {}
            ai_type = extracted_data.get('ai_type')
            
            print(f"📝 Story ID {story_id}: {customer_name}")
            print(f"   Current is_gen_ai: {current_is_gen_ai}")
            print(f"   Extracted ai_type: {ai_type}")
            
            # Apply consistency validation
            corrected_data = processor.validate_is_gen_ai_consistency(
                extracted_data.copy(), 
                f"story {story_id} ({customer_name})"
            )
            
            corrected_is_gen_ai = corrected_data.get('is_gen_ai')
            
            if corrected_is_gen_ai != current_is_gen_ai:
                # Update database fields
                cursor.execute("""
                    UPDATE customer_stories 
                    SET is_gen_ai = %s, extracted_data = %s, last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, [corrected_is_gen_ai, corrected_data, story_id])
                
                print(f"   ✅ Fixed: is_gen_ai = {corrected_is_gen_ai}")
                fixes_applied += 1
            else:
                print(f"   ℹ️  Already consistent")
            
            print()
        
        # Commit changes
        if fixes_applied > 0:
            cursor.connection.commit()
            print(f"✅ Applied {fixes_applied} consistency fixes to database")
        else:
            print("ℹ️  No fixes needed - all stories already consistent")
        
        # Final verification
        print("\n🔍 FINAL VERIFICATION:")
        print("-" * 30)
        
        # Check for any remaining inconsistencies
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM customer_stories
            WHERE extracted_data IS NOT NULL
            AND (
                (is_gen_ai = TRUE AND extracted_data->>'ai_type' = 'traditional') OR
                (is_gen_ai = FALSE AND extracted_data->>'ai_type' = 'generative')
            )
        """)
        remaining_issues = cursor.fetchone()['count']
        
        if remaining_issues == 0:
            print("✅ All classification consistency issues resolved!")
        else:
            print(f"⚠️  {remaining_issues} issues still remain - manual review needed")
        
        # Show current counts
        cursor.execute("SELECT COUNT(*) as count FROM customer_stories WHERE is_gen_ai = TRUE")
        gen_ai_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM customer_stories 
            WHERE is_gen_ai = TRUE AND extracted_data->'gen_ai_superpowers' IS NOT NULL
        """)
        gen_ai_with_aileron = cursor.fetchone()['count']
        
        print(f"\nCurrent status:")
        print(f"  Gen AI stories: {gen_ai_count}")
        print(f"  Gen AI with Aileron data: {gen_ai_with_aileron}")
        print(f"  Missing Aileron data: {gen_ai_count - gen_ai_with_aileron}")

if __name__ == "__main__":
    validate_all_classifications()