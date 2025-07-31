#!/usr/bin/env python3
"""
Test accessing a single OpenAI story to understand the content and structure
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from src.scrapers.openai_scraper import OpenAIScraper
from src.config import Config

def test_single_story():
    """Test accessing a single OpenAI story"""
    
    # Setup logging with more verbose output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    test_url = "https://openai.com/index/outtake/"
    
    print("="*60)
    print(f"TESTING SINGLE OPENAI STORY: {test_url}")
    print("="*60)
    
    try:
        # Initialize scraper
        print("1. Initializing OpenAI scraper...")
        scraper = OpenAIScraper()
        print("✅ Scraper initialized successfully")
        
        # Test scraping this specific story
        print(f"\n2. Attempting to scrape: {test_url}")
        story_data = scraper.scrape_story(test_url)
        
        if story_data:
            print("✅ Story scraped successfully!")
            print("\n" + "="*40)
            print("STORY DATA EXTRACTED:")
            print("="*40)
            print(f"Customer Name: {story_data['customer_name']}")
            print(f"Title: {story_data['title']}")
            print(f"Publish Date: {story_data.get('publish_date', 'Not found')}")
            print(f"Content Length: {len(story_data['raw_content']['text'].split())} words")
            print(f"Content Hash: {story_data['content_hash'][:12]}...")
            
            # Show first 500 characters of content
            content_preview = story_data['raw_content']['text'][:500]
            print(f"\nContent Preview (first 500 chars):")
            print("-" * 40)
            print(content_preview)
            print("-" * 40)
            
        else:
            print("❌ Failed to scrape story")
            print("This could be due to:")
            print("- Content-based filtering (video-only, insufficient text)")
            print("- Page loading issues")
            print("- Bot protection")
        
        print("\n" + "="*60)
        print("SINGLE STORY TEST COMPLETED")
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
    test_single_story()