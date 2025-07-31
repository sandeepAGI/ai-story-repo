#!/usr/bin/env python3
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations

def show_all_stories():
    """Display all stories from the database"""
    db = DatabaseConnection()
    db_ops = DatabaseOperations(db)
    
    try:
        # Get Anthropic source
        anthropic_source = db_ops.get_source_by_name("Anthropic")
        if not anthropic_source:
            print("No Anthropic source found in database")
            return
        
        # Get all stories for Anthropic
        stories = db_ops.get_stories_by_source(anthropic_source.id)
        
        print(f"\n{'='*80}")
        print(f"STORED CUSTOMER STORIES - Total: {len(stories)}")
        print(f"{'='*80}")
        
        for i, story in enumerate(stories, 1):
            print(f"\n{'='*60}")
            print(f"STORY {story.id}: {story.customer_name}")
            print(f"{'='*60}")
            print(f"URL: {story.url}")
            print(f"Title: {story.title}")
            print(f"Industry: {story.industry}")
            print(f"Company Size: {story.company_size}")
            print(f"Use Case Category: {story.use_case_category}")
            print(f"Scraped Date: {story.scraped_date}")
            
            # Show publish date with estimation info
            pub_date_str = story.publish_date.strftime('%Y-%m-%d') if story.publish_date else 'Unknown'
            if hasattr(story, 'publish_date_estimated') and story.publish_date_estimated:
                confidence = getattr(story, 'publish_date_confidence', 'unknown') or 'unknown'
                reasoning = getattr(story, 'publish_date_reasoning', '') or ''
                pub_date_str += f" (estimated with {confidence} confidence"
                if reasoning:
                    pub_date_str += f": {reasoning[:100]}..."
                pub_date_str += ")"
            print(f"Publish Date: {pub_date_str}")
            print(f"Content Hash: {story.content_hash[:16]}...")
            
            # Show raw content metadata
            if story.raw_content:
                raw_meta = story.raw_content.get('metadata', {})
                print(f"\nRAW CONTENT METADATA:")
                print(f"  Word Count: {raw_meta.get('word_count', 'N/A')}")
                print(f"  Images: {len(raw_meta.get('images', []))}")
                print(f"  External Links: {len(raw_meta.get('external_links', []))}")
                
                # Show first 500 chars of raw text
                raw_text = story.raw_content.get('text', '')
                print(f"  Raw Text Preview: {raw_text[:500]}...")
            
            # Show extracted data from Claude
            if story.extracted_data:
                print(f"\nCLAUDE EXTRACTED DATA:")
                extracted = story.extracted_data
                print(f"  Summary: {extracted.get('summary', 'N/A')}")
                print(f"  Problem Statement: {extracted.get('problem_statement', 'N/A')}")
                print(f"  Solution: {extracted.get('solution_description', 'N/A')}")
                print(f"  Technologies: {extracted.get('technologies_used', [])}")
                print(f"  Use Cases: {extracted.get('use_cases', [])}")
                print(f"  Business Outcomes: {len(extracted.get('business_outcomes', []))} outcomes")
                for outcome in extracted.get('business_outcomes', [])[:2]:  # Show first 2
                    print(f"    - {outcome.get('type', 'N/A')}: {outcome.get('description', 'N/A')}")
                print(f"  Quality Score: {extracted.get('content_quality_score', 'N/A')}")
                print(f"  Key Quote: {extracted.get('key_quote', 'N/A')}")
            
            print(f"\n{'-'*60}")
        
        if not stories:
            print("No stories found in database")
            
    except Exception as e:
        print(f"Error retrieving stories: {e}")
        import traceback
        traceback.print_exc()

def show_database_stats():
    """Show database statistics"""
    db = DatabaseConnection()
    
    try:
        with db.get_cursor() as cursor:
            # Count stories by source
            cursor.execute("""
                SELECT s.name, COUNT(cs.id) as story_count 
                FROM sources s 
                LEFT JOIN customer_stories cs ON s.id = cs.source_id 
                GROUP BY s.name, s.id
                ORDER BY story_count DESC
            """)
            source_counts = cursor.fetchall()
            
            print(f"\n{'='*40}")
            print("DATABASE STATISTICS")
            print(f"{'='*40}")
            for row in source_counts:
                print(f"{row['name']}: {row['story_count']} stories")
            
            # Show recent stories
            cursor.execute("""
                SELECT customer_name, title, scraped_date, publish_date,
                       publish_date_estimated, publish_date_confidence
                FROM customer_stories 
                ORDER BY scraped_date DESC 
                LIMIT 5
            """)
            recent = cursor.fetchall()
            
            print(f"\nMOST RECENT STORIES:")
            for row in recent:
                pub_date_str = row['publish_date'].strftime('%Y-%m-%d') if row['publish_date'] else 'Unknown'
                if row['publish_date_estimated']:
                    confidence = row['publish_date_confidence'] or 'unknown'
                    pub_date_str += f" (est. {confidence})"
                print(f"  {row['scraped_date'].strftime('%Y-%m-%d %H:%M')} - {row['customer_name']} (Published: {pub_date_str})")
                
    except Exception as e:
        print(f"Error getting database stats: {e}")

if __name__ == "__main__":
    show_database_stats()
    show_all_stories()