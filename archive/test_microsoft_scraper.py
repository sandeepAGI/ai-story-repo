#!/usr/bin/env python3
"""
Test script for Microsoft Azure AI customer stories scraper
Tests URL discovery and content extraction capabilities
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scrapers.microsoft_scraper import MicrosoftScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('microsoft_scraper_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_url_discovery():
    """Test Microsoft story URL discovery"""
    print("=" * 60)
    print("TESTING: Microsoft Azure AI Customer Stories URL Discovery")
    print("=" * 60)
    
    scraper = MicrosoftScraper()
    
    try:
        urls = scraper.get_customer_story_urls()
        
        print(f"\n✅ Successfully discovered {len(urls)} story URLs")
        print("\nDiscovered URLs:")
        for i, url in enumerate(urls[:10], 1):  # Show first 10
            print(f"{i:2d}. {url}")
        
        if len(urls) > 10:
            print(f"... and {len(urls) - 10} more URLs")
        
        return urls
        
    except Exception as e:
        print(f"❌ URL discovery failed: {e}")
        logger.error(f"URL discovery error: {e}", exc_info=True)
        return []

def test_single_story_scraping(url: str):
    """Test scraping a single Microsoft story"""
    print(f"\n" + "=" * 60)
    print(f"TESTING: Single Story Scraping")
    print(f"URL: {url}")
    print("=" * 60)
    
    scraper = MicrosoftScraper()
    
    try:
        story_data = scraper.scrape_story(url)
        
        if story_data:
            print("✅ Successfully scraped story")
            print(f"\nStory Details:")
            print(f"Customer Name: {story_data.get('customer_name', 'N/A')}")
            print(f"Title: {story_data.get('title', 'N/A')}")
            print(f"URL: {story_data.get('url', 'N/A')}")
            print(f"Publish Date: {story_data.get('publish_date', 'N/A')}")
            
            raw_content = story_data.get('raw_content', {})
            metadata = raw_content.get('metadata', {})
            print(f"Word Count: {metadata.get('word_count', 'N/A')}")
            print(f"Images: {len(metadata.get('images', []))}")
            print(f"External Links: {len(metadata.get('external_links', []))}")
            
            scraping_info = raw_content.get('scraping_info', {})
            print(f"Page Load Time: {scraping_info.get('page_load_time', 'N/A')}s")
            print(f"Final URL: {scraping_info.get('final_url', 'N/A')}")
            
            return story_data
        else:
            print("❌ Failed to scrape story (returned None)")
            return None
            
    except Exception as e:
        print(f"❌ Story scraping failed: {e}")
        logger.error(f"Story scraping error for {url}: {e}", exc_info=True)
        return None

def test_sample_stories(urls: list, max_stories: int = 3):
    """Test scraping multiple sample stories"""
    print(f"\n" + "=" * 60)
    print(f"TESTING: Sample Stories Scraping (max {max_stories})")
    print("=" * 60)
    
    successful_stories = []
    failed_stories = []
    
    test_urls = urls[:max_stories] if urls else [
        "https://www.microsoft.com/en/customers/story/23953-accenture-azure-ai-foundry"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n--- Story {i}/{len(test_urls)} ---")
        story_data = test_single_story_scraping(url)
        
        if story_data:
            successful_stories.append(story_data)
        else:
            failed_stories.append(url)
    
    print(f"\n" + "=" * 60)
    print("SAMPLE STORIES TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {len(successful_stories)}")
    print(f"❌ Failed: {len(failed_stories)}")
    print(f"Success Rate: {len(successful_stories)/(len(successful_stories)+len(failed_stories))*100:.1f}%")
    
    if failed_stories:
        print(f"\nFailed URLs:")
        for url in failed_stories:
            print(f"  - {url}")
    
    return successful_stories, failed_stories

def test_ai_filtering():
    """Test AI content filtering logic"""
    print(f"\n" + "=" * 60)
    print("TESTING: AI Content Filtering")
    print("=" * 60)
    
    scraper = MicrosoftScraper()
    
    # Test with known AI story
    test_url = "https://www.microsoft.com/en/customers/story/23953-accenture-azure-ai-foundry"
    
    try:
        response = scraper.make_request(test_url)
        if response:
            soup = scraper.parse_html(response.text)
            is_ai_story = scraper._is_ai_story(soup, response.text)
            
            print(f"Test URL: {test_url}")
            print(f"Identified as AI story: {'✅ Yes' if is_ai_story else '❌ No'}")
            
            # Show some detected keywords
            text_content = soup.get_text().lower()
            found_keywords = [kw for kw in scraper.ai_keywords if kw in text_content]
            print(f"AI Keywords found: {len(found_keywords)}")
            if found_keywords:
                print(f"Sample keywords: {', '.join(found_keywords[:5])}")
        else:
            print("❌ Could not fetch test URL for AI filtering test")
            
    except Exception as e:
        print(f"❌ AI filtering test failed: {e}")
        logger.error(f"AI filtering test error: {e}", exc_info=True)

def main():
    """Run all Microsoft scraper tests"""
    print("Microsoft Azure AI Customer Stories Scraper Test")
    print("=" * 60)
    
    # Test 1: URL Discovery
    discovered_urls = test_url_discovery()
    
    # Test 2: AI Content Filtering
    test_ai_filtering()
    
    # Test 3: Sample Story Scraping
    successful_stories, failed_stories = test_sample_stories(discovered_urls, max_stories=2)
    
    # Final Summary
    print(f"\n" + "=" * 60)
    print("MICROSOFT SCRAPER TEST SUMMARY")
    print("=" * 60)
    print(f"URLs Discovered: {len(discovered_urls)}")
    print(f"Stories Successfully Scraped: {len(successful_stories)}")
    print(f"Failed Story URLs: {len(failed_stories)}")
    
    if successful_stories:
        print(f"\n📊 Sample Story Quality Analysis:")
        for i, story in enumerate(successful_stories, 1):
            raw_content = story.get('raw_content', {})
            metadata = raw_content.get('metadata', {})
            word_count = metadata.get('word_count', 0)
            
            print(f"  Story {i}: {story.get('customer_name', 'Unknown')} - {word_count} words")
    
    # Recommendations
    print(f"\n🎯 Recommendations:")
    if len(discovered_urls) > 0:
        print("✅ URL discovery is working - ready for database integration")
    else:
        print("❌ URL discovery needs debugging")
        
    if len(successful_stories) > 0:
        print("✅ Content scraping is working - ready for Claude AI processing")
    else:
        print("❌ Content scraping needs debugging")
    
    success_rate = len(successful_stories) / max(1, len(successful_stories) + len(failed_stories))
    if success_rate > 0.8:
        print("✅ High success rate - scraper is production ready")
    elif success_rate > 0.5:
        print("⚠️  Moderate success rate - some improvements needed")
    else:
        print("❌ Low success rate - significant debugging required")

if __name__ == "__main__":
    main()