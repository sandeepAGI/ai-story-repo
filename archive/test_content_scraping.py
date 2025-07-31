#!/usr/bin/env python3
"""
Test OpenAI Content Scraping Phase
Tests the second phase of two-phase scraping: scraping individual story content
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from src.config import Config
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations
from src.scrapers.openai_content_scraper import OpenAIContentScraper

def test_content_scraping():
    """Test OpenAI content scraping phase"""
    
    # Setup logging
    Config.setup_logging()
    logger = logging.getLogger(__name__)
    
    print("="*70)
    print("TESTING OPENAI CONTENT SCRAPING PHASE")
    print("="*70)
    
    try:
        # Test database connection
        print("1. Testing database connection...")
        db_connection = DatabaseConnection()
        if not db_connection.test_connection():
            print("❌ Database connection failed - please ensure PostgreSQL is running")
            return
        print("✅ Database connection successful")
        
        # Initialize database operations
        db_ops = DatabaseOperations(db_connection)
        
        # Check if OpenAI source exists
        print("\n2. Checking OpenAI source in database...")
        openai_source = db_ops.get_source_by_name("OpenAI")
        if not openai_source:
            print("❌ OpenAI source not found in database - please run database setup")
            return
        print(f"✅ OpenAI source found (ID: {openai_source.id})")
        
        # Get pending URLs
        print("\n3. Getting pending URLs...")
        pending_urls = db_ops.get_pending_urls(openai_source.id, limit=3)
        if not pending_urls:
            print("❌ No pending URLs found - please run URL discovery first")
            return
        print(f"✅ Found {len(pending_urls)} pending URLs")
        
        # Initialize content scraper
        print("\n4. Initializing content scraper...")
        content_scraper = OpenAIContentScraper(db_ops)
        print("✅ Content scraper initialized successfully")
        
        # Test scraping individual URLs
        print("\n5. Testing content scraping...")
        print("   This may take several minutes per story...")
        
        for i, discovered_url in enumerate(pending_urls, 1):
            print(f"\n--- Testing Story {i}/{len(pending_urls)} ---")
            print(f"Customer: {discovered_url.inferred_customer_name}")
            print(f"URL: {discovered_url.url}")
            print(f"Date: {discovered_url.publish_date}")
            
            try:
                result = content_scraper.scrape_and_store_story(discovered_url)
                
                if result['success']:
                    print("✅ Story scraped and stored successfully!")
                    print(f"   Story ID: {result['story_id']}")
                    print(f"   Customer: {result['customer_name']}")
                    print(f"   Title: {result['title'][:100]}...")
                    print(f"   Content length: {len(result['content'])} chars")
                    
                    if result.get('claude_data'):
                        claude_data = result['claude_data']
                        print(f"   AI Quality Score: {claude_data.get('content_quality_score', 'N/A')}")
                        print(f"   Industry: {claude_data.get('company_info', {}).get('industry_sector', 'N/A')}")
                        print(f"   Technologies: {claude_data.get('technologies_used', [])[:3]}")
                else:
                    print(f"❌ Story scraping failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error scraping story: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*70)
        print("CONTENT SCRAPING PHASE COMPLETED")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n❌ Scraping cancelled by user")
    except Exception as e:
        print(f"❌ Content scraping failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_scraping()