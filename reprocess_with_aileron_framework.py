#!/usr/bin/env python3
"""
Reprocess all customer stories with updated Aileron GenAI SuperPowers framework classifications.
This script updates existing stories with the new classification definitions while preserving
all other extracted data.
"""

import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.append('src')

from database.models import DatabaseOperations
from ai_integration.claude_processor import ClaudeProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reprocess_aileron.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def reprocess_all_stories(story_ids=None):
    """Reprocess stories with updated Aileron GenAI SuperPowers framework"""
    
    db_ops = DatabaseOperations()
    processor = ClaudeProcessor()
    
    # Build query based on whether specific IDs are requested
    if story_ids:
        # Reprocess specific story IDs regardless of flags
        placeholders = ','.join(['%s'] * len(story_ids))
        query = f"""
            SELECT id, customer_name, title, raw_content, extracted_data
            FROM customer_stories 
            WHERE id IN ({placeholders})
            AND raw_content IS NOT NULL
            ORDER BY id
        """
        query_params = story_ids
        logger.info(f"Targeting specific {len(story_ids)} stories for Aileron reprocessing")
    else:
        # Get only stories that haven't been reprocessed with Aileron framework yet
        query = """
            SELECT id, customer_name, title, raw_content, extracted_data
            FROM customer_stories 
            WHERE raw_content IS NOT NULL
            AND (extracted_data->>'reprocessed_with_aileron_framework' IS NULL 
                 OR extracted_data->>'reprocessed_with_aileron_framework' <> 'true')
            ORDER BY id
        """
        query_params = []
        logger.info("Reprocessing all stories without Aileron framework flag")
    
    with db_ops.db.get_cursor() as cursor:
        cursor.execute(query, query_params)
        stories = cursor.fetchall()
    
    total_stories = len(stories)
    logger.info(f"Starting reprocessing of {total_stories} stories with Aileron framework")
    
    processed_count = 0
    error_count = 0
    start_time = time.time()
    
    for i, story in enumerate(stories, 1):
        story_id = story['id']
        customer_name = story['customer_name']
        title = story['title'] or 'No title'
        
        try:
            logger.info(f"Processing {i}/{total_stories}: {customer_name} (ID: {story_id})")
            
            # Reprocess with updated prompts
            new_extracted_data = processor.extract_story_data(story['raw_content'])
            
            if new_extracted_data:
                # Preserve any existing data not related to classifications
                existing_data = story['extracted_data'] or {}
                
                # Update with new classification data
                updated_data = {**existing_data, **new_extracted_data}
                updated_data['last_processed'] = datetime.now().isoformat()
                updated_data['reprocessed_with_aileron_framework'] = True
                
                # Update in database
                db_ops.update_story_extracted_data(story_id, updated_data)
                processed_count += 1
                
                # Log classification results
                superpowers = new_extracted_data.get('gen_ai_superpowers', [])
                impacts = new_extracted_data.get('business_impacts', [])
                enablers = new_extracted_data.get('adoption_enablers', [])
                function = new_extracted_data.get('business_function', 'unknown')
                
                logger.info(f"  ✓ Classifications: SP={len(superpowers)}, BI={len(impacts)}, AE={len(enablers)}, BF={function}")
                
            else:
                logger.error(f"  ✗ Failed to extract data for story {story_id}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"  ✗ Error processing story {story_id}: {str(e)}")
            error_count += 1
            
        # Rate limiting - small delay between requests
        time.sleep(0.5)
    
    # Summary
    elapsed_time = time.time() - start_time
    logger.info(f"\n=== REPROCESSING COMPLETE ===")
    logger.info(f"Total stories: {total_stories}")
    logger.info(f"Successfully processed: {processed_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Time elapsed: {elapsed_time:.1f} seconds")
    logger.info(f"Average time per story: {elapsed_time/total_stories:.1f} seconds")
    
    return processed_count, error_count

def verify_classifications():
    """Verify that classifications have been updated correctly"""
    
    db_ops = DatabaseOperations()
    
    with db_ops.db.get_cursor() as cursor:
        # Check how many stories have the new classification fields
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN extracted_data->>'gen_ai_superpowers' IS NOT NULL THEN 1 END) as has_superpowers,
                COUNT(CASE WHEN extracted_data->>'business_impacts' IS NOT NULL THEN 1 END) as has_impacts,
                COUNT(CASE WHEN extracted_data->>'adoption_enablers' IS NOT NULL THEN 1 END) as has_enablers,
                COUNT(CASE WHEN extracted_data->>'business_function' IS NOT NULL THEN 1 END) as has_function,
                COUNT(CASE WHEN extracted_data->>'reprocessed_with_aileron_framework' = 'true' THEN 1 END) as reprocessed
            FROM customer_stories
            WHERE extracted_data IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        
        print("\n=== CLASSIFICATION VERIFICATION ===")
        print(f"Total stories with extracted_data: {stats['total']}")
        print(f"Stories with gen_ai_superpowers: {stats['has_superpowers']}")
        print(f"Stories with business_impacts: {stats['has_impacts']}")
        print(f"Stories with adoption_enablers: {stats['has_enablers']}")
        print(f"Stories with business_function: {stats['has_function']}")
        print(f"Stories marked as reprocessed: {stats['reprocessed']}")
        
        # Get sample of classifications
        cursor.execute("""
            SELECT 
                customer_name,
                extracted_data->>'gen_ai_superpowers' as superpowers,
                extracted_data->>'business_impacts' as impacts,
                extracted_data->>'adoption_enablers' as enablers,
                extracted_data->>'business_function' as function
            FROM customer_stories
            WHERE extracted_data->>'reprocessed_with_aileron_framework' = 'true'
            ORDER BY id
            LIMIT 5
        """)
        
        print("\n=== SAMPLE CLASSIFICATIONS ===")
        for row in cursor.fetchall():
            print(f"\nCustomer: {row['customer_name']}")
            print(f"  Superpowers: {row['superpowers']}")
            print(f"  Impacts: {row['impacts']}")
            print(f"  Enablers: {row['enablers']}")
            print(f"  Function: {row['function']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reprocess stories with Aileron framework')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Only verify current classifications, do not reprocess')
    parser.add_argument('--story-ids', type=str,
                       help='Comma-separated list of story IDs to reprocess (e.g., 1001,995,978)')
    
    args = parser.parse_args()
    
    if args.verify_only:
        verify_classifications()
    else:
        # Parse story IDs if provided
        story_ids = None
        if args.story_ids:
            try:
                story_ids = [int(id.strip()) for id in args.story_ids.split(',')]
                print(f"🎯 Targeting specific stories: {story_ids}")
            except ValueError:
                print("❌ Error: Story IDs must be comma-separated integers (e.g., 1001,995,978)")
                sys.exit(1)
        
        # Run reprocessing
        processed, errors = reprocess_all_stories(story_ids)
        
        # Verify results
        print("\n" + "="*50)
        verify_classifications()
        
        if errors > 0:
            print(f"\n⚠️  {errors} stories had processing errors. Check reprocess_aileron.log for details.")
        else:
            print(f"\n✅ All {processed} stories successfully reprocessed with Aileron framework!")