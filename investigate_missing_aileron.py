#!/usr/bin/env python3
"""
Investigate Gen AI stories missing Aileron framework data
Identifies which stories are marked as Gen AI but lack SuperPowers analysis
"""

import sys
import os
import pandas as pd

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations

def investigate_missing_aileron():
    """Find Gen AI stories missing Aileron framework data"""
    
    db_ops = DatabaseOperations()
    
    print("🔍 Investigating Gen AI stories missing Aileron framework data...")
    print("=" * 70)
    
    with db_ops.db.get_cursor() as cursor:
        # Get all Gen AI stories
        cursor.execute("""
            SELECT 
                id,
                customer_name,
                source_id,
                url,
                title,
                scraped_date,
                extracted_data,
                CASE 
                    WHEN extracted_data->'gen_ai_superpowers' IS NOT NULL THEN 'HAS_SUPERPOWERS'
                    ELSE 'MISSING_SUPERPOWERS'
                END as aileron_status
            FROM customer_stories 
            WHERE is_gen_ai = TRUE
            ORDER BY scraped_date DESC
        """)
        
        gen_ai_stories = cursor.fetchall()
        
        # Get source names
        cursor.execute("SELECT id, name FROM sources")
        sources = {row['id']: row['name'] for row in cursor.fetchall()}
        
        # Separate stories with and without Aileron data
        with_aileron = [s for s in gen_ai_stories if s['aileron_status'] == 'HAS_SUPERPOWERS']
        missing_aileron = [s for s in gen_ai_stories if s['aileron_status'] == 'MISSING_SUPERPOWERS']
        
        print(f"📊 SUMMARY:")
        print(f"  Total Gen AI Stories: {len(gen_ai_stories)}")
        print(f"  With Aileron Data: {len(with_aileron)}")
        print(f"  Missing Aileron Data: {len(missing_aileron)}")
        print()
        
        if missing_aileron:
            print(f"❌ STORIES MISSING AILERON DATA ({len(missing_aileron)}):")
            print("-" * 70)
            
            # Group by source
            missing_by_source = {}
            for story in missing_aileron:
                source_name = sources.get(story['source_id'], 'Unknown')
                if source_name not in missing_by_source:
                    missing_by_source[source_name] = []
                missing_by_source[source_name].append(story)
            
            for source_name, stories in missing_by_source.items():
                print(f"\n🔸 {source_name} ({len(stories)} stories):")
                for story in stories[:5]:  # Show first 5 per source
                    print(f"  • ID: {story['id']} | {story['customer_name']}")
                    print(f"    URL: {story['url'][:80]}{'...' if len(story['url']) > 80 else ''}")
                    print(f"    Scraped: {story['scraped_date']}")
                    
                    # Check what extracted_data exists
                    if story['extracted_data']:
                        fields = list(story['extracted_data'].keys())
                        print(f"    Has fields: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
                    else:
                        print(f"    No extracted_data at all")
                    print()
                
                if len(stories) > 5:
                    print(f"    ... and {len(stories) - 5} more {source_name} stories")
                    print()
        
        # Analysis by scraped date
        print(f"\n📅 MISSING AILERON BY DATE:")
        print("-" * 40)
        
        missing_dates = {}
        for story in missing_aileron:
            date_str = story['scraped_date'].strftime('%Y-%m-%d') if story['scraped_date'] else 'Unknown'
            missing_dates[date_str] = missing_dates.get(date_str, 0) + 1
        
        for date, count in sorted(missing_dates.items(), reverse=True)[:10]:
            print(f"  {date}: {count} stories")
        
        # Check for patterns in extracted_data
        print(f"\n🔍 EXTRACTED DATA ANALYSIS (Missing Aileron):")
        print("-" * 50)
        
        field_counts = {}
        no_extracted_data = 0
        
        for story in missing_aileron:
            if not story['extracted_data']:
                no_extracted_data += 1
            else:
                for field in story['extracted_data'].keys():
                    field_counts[field] = field_counts.get(field, 0) + 1
        
        print(f"Stories with no extracted_data: {no_extracted_data}")
        print(f"Common fields in extracted_data:")
        for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count} stories")
        
        # Recommend action
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 30)
        
        if no_extracted_data > 0:
            print(f"1. {no_extracted_data} stories have no extracted_data - need complete reprocessing")
        
        partial_data = len(missing_aileron) - no_extracted_data
        if partial_data > 0:
            print(f"2. {partial_data} stories have partial data - need Aileron framework update only")
        
        print(f"3. Most recent missing stories are from recent scrapes - check AI processing pipeline")
        
        # Generate SQL update command template
        print(f"\n🔧 TO FIX - RUN THESE COMMANDS:")
        print("-" * 40)
        print("# For stories with no extracted_data (complete reprocessing):")
        if no_extracted_data > 0:
            no_data_ids = [str(s['id']) for s in missing_aileron if not s['extracted_data']][:5]
            print(f"python update_all_databases.py reprocess --story-ids {','.join(no_data_ids)}")
        
        print("\n# For stories with partial data (Aileron update only):")
        if partial_data > 0:
            partial_ids = [str(s['id']) for s in missing_aileron if s['extracted_data']][:5]
            print(f"python update_all_databases.py update-aileron --story-ids {','.join(partial_ids)}")

if __name__ == "__main__":
    try:
        investigate_missing_aileron()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()