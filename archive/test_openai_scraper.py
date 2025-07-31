#!/usr/bin/env python3
"""
Test script for OpenAI scraper functionality
Tests URL discovery and content extraction without database
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from src.scrapers.openai_scraper import OpenAIScraper
from src.config import Config

def test_openai_scraper():
    """Test OpenAI scraper functionality"""
    
    # Setup logging
    Config.setup_logging()
    logger = logging.getLogger(__name__)
    
    print("="*60)
    print("TESTING OPENAI SCRAPER")
    print("="*60)
    
    try:
        # Initialize scraper
        print("1. Initializing OpenAI scraper...")
        scraper = OpenAIScraper()
        print("✅ Scraper initialized successfully")
        
        # Test URL discovery
        print("\n2. Testing story URL discovery...")
        story_urls = scraper.get_customer_story_urls()
        
        print(f"✅ Found {len(story_urls)} story URLs")
        
        # Show first few URLs
        print("\nSample URLs found:")
        for i, url in enumerate(story_urls[:5]):
            print(f"  {i+1}. {url}")
        
        if len(story_urls) > 5:
            print(f"  ... and {len(story_urls) - 5} more URLs")
        
        # Test scraping individual story
        if story_urls:
            print(f"\n3. Testing individual story scraping...")
            test_url = story_urls[0]
            print(f"Scraping: {test_url}")
            
            story_data = scraper.scrape_story(test_url)
            
            if story_data:
                print("✅ Story scraped successfully!")
                print(f"Customer Name: {story_data['customer_name']}")
                print(f"Title: {story_data['title']}")
                print(f"Publish Date: {story_data.get('publish_date', 'Not found')}")
                print(f"Content Length: {len(story_data['raw_content']['text'].split())} words")
                print(f"Content Hash: {story_data['content_hash'][:12]}...")
            else:
                print("❌ Failed to scrape story")
        
        else:
            print("❌ No URLs found to test individual scraping")
        
        print("\n" + "="*60)
        print("OPENAI SCRAPER TEST COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if 'scraper' in locals():
            try:
                if hasattr(scraper, 'driver') and scraper.driver:
                    scraper.driver.quit()
                    print("WebDriver cleaned up")
            except:
                pass

if __name__ == "__main__":
    test_openai_scraper()