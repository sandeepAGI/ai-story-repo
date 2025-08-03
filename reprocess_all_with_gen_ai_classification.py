#!/usr/bin/env python3
"""
Reprocess ALL customer stories with the new two-step Gen AI classification approach.

This script:
1. Uses the new Gen AI determination step first
2. Applies appropriate extraction (Gen AI with Aileron framework OR Traditional AI without)
3. Updates the is_gen_ai boolean field
4. Removes Gen AI superpowers data from Traditional AI stories
5. Preserves all other extracted data
"""

import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.append('src')

from database.models import DatabaseOperations
from ai_integration.claude_processor import ClaudeProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reprocess_gen_ai_classification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def reprocess_all_stories_with_gen_ai_classification():
    """Reprocess all stories with new two-step Gen AI classification approach"""
    
    db_ops = DatabaseOperations()
    processor = ClaudeProcessor()
    
    # Get ALL stories for reprocessing
    stories = db_ops.get_all_stories_for_reprocessing()
    
    total_stories = len(stories)
    logger.info(f"Starting complete reprocessing of {total_stories} stories with Gen AI classification")
    
    processed_count = 0
    error_count = 0
    gen_ai_count = 0
    traditional_ai_count = 0
    cleaned_traditional_count = 0
    start_time = time.time()
    
    for i, story in enumerate(stories, 1):
        story_id = story['id']
        customer_name = story['customer_name']
        title = story['title'] or 'No title'
        existing_data = story['extracted_data'] or {}
        
        try:
            logger.info(f"Processing {i}/{total_stories}: {customer_name} (ID: {story_id})")
            
            # Reprocess with new two-step approach
            new_extracted_data = processor.extract_story_data(story['raw_content'])
            
            if new_extracted_data:
                # Get Gen AI classification
                is_gen_ai = new_extracted_data.get('is_gen_ai', None)
                ai_type = new_extracted_data.get('ai_type', 'unknown')
                
                if is_gen_ai is None:
                    logger.error(f"  ✗ Missing is_gen_ai classification for story {story_id}")
                    error_count += 1
                    continue
                
                # Update extracted data preserving existing non-classification data
                updated_data = {**existing_data, **new_extracted_data}
                updated_data['last_processed'] = datetime.now().isoformat()
                updated_data['reprocessed_with_gen_ai_classification'] = True
                
                # Clean Traditional AI stories of Gen AI fields
                if not is_gen_ai:
                    original_fields = len(updated_data)
                    updated_data = db_ops.remove_gen_ai_fields_from_traditional_ai(story_id, updated_data)
                    if len(updated_data) < original_fields:
                        cleaned_traditional_count += 1
                    traditional_ai_count += 1
                else:
                    gen_ai_count += 1
                
                # Update database
                db_ops.update_story_extracted_data(story_id, updated_data)
                db_ops.update_story_gen_ai_flag(story_id, is_gen_ai)
                
                processed_count += 1
                
                # Log classification results
                if is_gen_ai:
                    superpowers = new_extracted_data.get('gen_ai_superpowers', [])
                    impacts = new_extracted_data.get('business_impacts', [])
                    enablers = new_extracted_data.get('adoption_enablers', [])
                    function = new_extracted_data.get('business_function', 'unknown')
                    logger.info(f"  ✓ Gen AI Story - SP={len(superpowers)}, BI={len(impacts)}, AE={len(enablers)}, BF={function}")
                else:
                    logger.info(f"  ✓ Traditional AI Story - Type: {ai_type}")
                
            else:
                logger.error(f"  ✗ Failed to extract data for story {story_id}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"  ✗ Error processing story {story_id}: {str(e)}")
            error_count += 1
            
        # Rate limiting - small delay between requests
        time.sleep(0.5)
        
        # Progress report every 50 stories
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed * 60  # stories per minute
            eta_minutes = (total_stories - i) / rate if rate > 0 else 0
            logger.info(f"  Progress: {i}/{total_stories} ({i/total_stories*100:.1f}%) - Rate: {rate:.1f}/min - ETA: {eta_minutes:.1f}min")
    
    # Summary
    elapsed_time = time.time() - start_time
    logger.info(f"\n=== REPROCESSING COMPLETE ===")
    logger.info(f"Total stories: {total_stories}")
    logger.info(f"Successfully processed: {processed_count}")
    logger.info(f"Gen AI stories: {gen_ai_count}")
    logger.info(f"Traditional AI stories: {traditional_ai_count}")
    logger.info(f"Traditional AI stories cleaned of Gen AI fields: {cleaned_traditional_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    logger.info(f"Average time per story: {elapsed_time/total_stories:.1f} seconds")
    
    return processed_count, error_count, gen_ai_count, traditional_ai_count

def verify_gen_ai_classifications():
    """Verify that Gen AI classifications have been updated correctly"""
    
    db_ops = DatabaseOperations()
    
    with db_ops.db.get_cursor() as cursor:
        # Check classification statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_gen_ai = true THEN 1 END) as gen_ai_stories,
                COUNT(CASE WHEN is_gen_ai = false THEN 1 END) as traditional_ai_stories,
                COUNT(CASE WHEN is_gen_ai IS NULL THEN 1 END) as unclassified,
                COUNT(CASE WHEN extracted_data->>'gen_ai_superpowers' IS NOT NULL THEN 1 END) as has_superpowers,
                COUNT(CASE WHEN extracted_data->>'business_impacts' IS NOT NULL THEN 1 END) as has_impacts,
                COUNT(CASE WHEN extracted_data->>'adoption_enablers' IS NOT NULL THEN 1 END) as has_enablers,
                COUNT(CASE WHEN extracted_data->>'business_function' IS NOT NULL THEN 1 END) as has_function,
                COUNT(CASE WHEN extracted_data->>'reprocessed_with_gen_ai_classification' = 'true' THEN 1 END) as reprocessed
            FROM customer_stories
            WHERE extracted_data IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        
        print("\n=== GEN AI CLASSIFICATION VERIFICATION ===")
        print(f"Total stories with extracted_data: {stats['total']}")
        print(f"Gen AI stories (is_gen_ai = true): {stats['gen_ai_stories']}")
        print(f"Traditional AI stories (is_gen_ai = false): {stats['traditional_ai_stories']}")
        print(f"Unclassified stories (is_gen_ai = null): {stats['unclassified']}")
        print(f"Stories with gen_ai_superpowers: {stats['has_superpowers']}")
        print(f"Stories with business_impacts: {stats['has_impacts']}")
        print(f"Stories with adoption_enablers: {stats['has_enablers']}")
        print(f"Stories with business_function: {stats['has_function']}")
        print(f"Stories marked as reprocessed: {stats['reprocessed']}")
        
        # Check for data integrity issues
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM customer_stories 
            WHERE is_gen_ai = false 
            AND (extracted_data->'gen_ai_superpowers' IS NOT NULL 
                 OR extracted_data->'business_impacts' IS NOT NULL
                 OR extracted_data->'adoption_enablers' IS NOT NULL)
        """)
        dirty_traditional = cursor.fetchone()['count']
        
        if dirty_traditional > 0:
            print(f"\n⚠️  WARNING: {dirty_traditional} Traditional AI stories still have Gen AI fields!")
        else:
            print(f"\n✅ All Traditional AI stories properly cleaned of Gen AI fields")
        
        # Get sample of each type
        print("\n=== SAMPLE GEN AI CLASSIFICATIONS ===")
        cursor.execute("""
            SELECT 
                customer_name,
                is_gen_ai,
                extracted_data->>'ai_type' as ai_type,
                extracted_data->>'gen_ai_superpowers' as superpowers,
                extracted_data->>'business_impacts' as impacts,
                publish_date
            FROM customer_stories
            WHERE extracted_data->>'reprocessed_with_gen_ai_classification' = 'true'
            AND is_gen_ai = true
            ORDER BY publish_date DESC
            LIMIT 3
        """)
        
        print("\nGen AI Stories:")
        for row in cursor.fetchall():
            print(f"  {row['customer_name']} ({row['publish_date']})")
            print(f"    AI Type: {row['ai_type']}")
            print(f"    Superpowers: {row['superpowers']}")
            print(f"    Impacts: {row['impacts']}")
        
        print("\nTraditional AI Stories:")
        cursor.execute("""
            SELECT 
                customer_name,
                is_gen_ai,
                extracted_data->>'ai_type' as ai_type,
                publish_date,
                CASE WHEN extracted_data->'gen_ai_superpowers' IS NOT NULL THEN 'HAS_SUPERPOWERS' ELSE 'CLEAN' END as status
            FROM customer_stories
            WHERE extracted_data->>'reprocessed_with_gen_ai_classification' = 'true'
            AND is_gen_ai = false
            ORDER BY publish_date ASC
            LIMIT 3
        """)
        
        for row in cursor.fetchall():
            print(f"  {row['customer_name']} ({row['publish_date']})")
            print(f"    AI Type: {row['ai_type']}")
            print(f"    Status: {row['status']}")

def analyze_classification_by_year():
    """Analyze Gen AI vs Traditional AI classification by publish year"""
    
    db_ops = DatabaseOperations()
    
    with db_ops.db.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                EXTRACT(YEAR FROM publish_date) as year,
                COUNT(*) as total,
                COUNT(CASE WHEN is_gen_ai = true THEN 1 END) as gen_ai,
                COUNT(CASE WHEN is_gen_ai = false THEN 1 END) as traditional_ai
            FROM customer_stories
            WHERE publish_date IS NOT NULL
            AND extracted_data->>'reprocessed_with_gen_ai_classification' = 'true'
            GROUP BY EXTRACT(YEAR FROM publish_date)
            ORDER BY year
        """)
        
        print("\n=== CLASSIFICATION BY YEAR ===")
        print("Year | Total | Gen AI | Traditional | Gen AI %")
        print("-" * 50)
        
        for row in cursor.fetchall():
            year = int(row['year']) if row['year'] else 'Unknown'
            total = row['total']
            gen_ai = row['gen_ai']
            traditional = row['traditional_ai']
            gen_ai_pct = (gen_ai / total * 100) if total > 0 else 0
            
            print(f"{year:<4} | {total:5} | {gen_ai:6} | {traditional:11} | {gen_ai_pct:6.1f}%")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reprocess all stories with Gen AI classification')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Only verify current classifications, do not reprocess')
    parser.add_argument('--analyze-years', action='store_true',
                       help='Analyze classification distribution by year')
    
    args = parser.parse_args()
    
    if args.verify_only:
        verify_gen_ai_classifications()
        if args.analyze_years:
            analyze_classification_by_year()
    elif args.analyze_years:
        analyze_classification_by_year()
    else:
        # Run full reprocessing
        print("🚀 Starting complete reprocessing with Gen AI classification...")
        print("This will:")
        print("1. Classify each story as Gen AI or Traditional AI")
        print("2. Apply appropriate extraction prompts")
        print("3. Update is_gen_ai boolean field")
        print("4. Remove Gen AI fields from Traditional AI stories")
        print("5. Preserve all other data")
        print()
        
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        
        processed, errors, gen_ai, traditional = reprocess_all_stories_with_gen_ai_classification()
        
        # Verify results
        print("\n" + "="*60)
        verify_gen_ai_classifications()
        analyze_classification_by_year()
        
        if errors > 0:
            print(f"\n⚠️  {errors} stories had processing errors. Check reprocess_gen_ai_classification.log for details.")
        else:
            print(f"\n✅ All {processed} stories successfully reprocessed!")
            print(f"📊 Final counts: {gen_ai} Gen AI, {traditional} Traditional AI")