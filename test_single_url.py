#!/usr/bin/env python3
"""
Test single OpenAI URL scraping for debugging
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from src.config import Config
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations
from src.scrapers.openai_content_scraper import OpenAIContentScraper

def test_single_url():
    """Test scraping a single URL for debugging"""
    
    # Setup logging
    Config.setup_logging()
    logger = logging.getLogger(__name__)
    
    print("="*70)
    print("TESTING SINGLE OPENAI URL SCRAPING")
    print("="*70)
    
    try:
        # Test database connection
        print("1. Testing database connection...")
        db_connection = DatabaseConnection()
        if not db_connection.test_connection():
            print("❌ Database connection failed")
            return
        print("✅ Database connection successful")
        
        # Initialize database operations
        db_ops = DatabaseOperations(db_connection)
        
        # Get a single URL to test
        print("\n2. Getting test URL...")
        openai_source = db_ops.get_source_by_name("OpenAI")
        pending_urls = db_ops.get_pending_urls(openai_source.id, limit=1)
        
        if not pending_urls:
            print("❌ No pending URLs found")
            return
            
        test_url = pending_urls[0]
        print(f"✅ Testing URL: {test_url.url}")
        print(f"   Customer: {test_url.inferred_customer_name}")
        
        # Initialize content scraper
        print("\n3. Initializing content scraper...")
        content_scraper = OpenAIContentScraper(db_ops)
        print("✅ Content scraper initialized")
        
        # Test scraping (this will open a browser window)
        print(f"\n4. Scraping content from: {test_url.url}")
        print("   (Browser window will open for debugging)")
        
        story_data = content_scraper.scrape_story_content(test_url.url)
        
        if story_data:
            print("✅ Content scraped successfully!")
            print(f"   Customer: {story_data['customer_name']}")
            print(f"   Title: {story_data['title']}")
            print(f"   Content length: {len(story_data['text_content'])} chars")
            print(f"   Word count: {len(story_data['text_content'].split())} words")
            print(f"   Publish date: {story_data['publish_date']}")
            
            # Show first 200 chars of content
            print(f"\n   Content sample:")
            print(f"   {story_data['text_content'][:200]}...")
            
        else:
            print("❌ Content scraping failed")
        
        print("\n5. Closing browser...")
        
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_url()