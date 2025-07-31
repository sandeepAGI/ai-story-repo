#!/usr/bin/env python3
"""
Test script for AWS scraper functionality
"""

import sys
import os
sys.path.insert(0, 'src')

from src.scrapers.aws_scraper import AWScraper
from src.config import Config
import logging

def test_aws_url_discovery():
    """Test URL discovery for AWS customer stories"""
    print("=" * 60)
    print("TESTING AWS URL DISCOVERY")
    print("=" * 60)
    
    scraper = AWScraper()
    
    print(f"Base URL: {scraper.base_url}")
    print(f"AI Keywords: {len(scraper.ai_keywords)} keywords")
    print(f"Secondary URLs: {len(scraper.secondary_urls)} additional sources")
    
    print("\nFetching story URLs...")
    urls = scraper.get_customer_story_urls()
    
    print(f"\nFound {len(urls)} story URLs:")
    for i, url in enumerate(urls[:10], 1):  # Show first 10
        print(f"{i:2d}. {url}")
    
    if len(urls) > 10:
        print(f"    ... and {len(urls) - 10} more URLs")
    
    return urls

def test_aws_story_scraping(urls, limit=3):
    """Test scraping individual AWS stories"""
    print("\n" + "=" * 60)
    print("TESTING AWS STORY SCRAPING")
    print("=" * 60)
    
    scraper = AWScraper()
    test_urls = urls[:limit] if urls else []
    
    if not test_urls:
        print("No URLs available for testing")
        return []
    
    scraped_stories = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nScraping story {i}/{len(test_urls)}: {url}")
        print("-" * 40)
        
        story_data = scraper.scrape_story(url)
        
        if story_data:
            scraped_stories.append(story_data)
            print(f"✅ SUCCESS")
            print(f"   Customer: {story_data['customer_name']}")
            print(f"   Title: {story_data['title'][:100]}...")
            print(f"   Publish Date: {story_data['publish_date']}")
            print(f"   Content Length: {len(story_data['raw_content'].get('text', ''))} chars")
            print(f"   Hash: {story_data['content_hash'][:16]}...")
        else:
            print(f"❌ FAILED - Could not scrape story")
    
    print(f"\nScraping Summary: {len(scraped_stories)}/{len(test_urls)} stories successfully scraped")
    return scraped_stories

def test_ai_filtering():
    """Test AI keyword filtering functionality"""
    print("\n" + "=" * 60)
    print("TESTING AI KEYWORD FILTERING")
    print("=" * 60)
    
    scraper = AWScraper()
    
    # Test cases for AI filtering
    test_cases = [
        {
            'title': 'Generative AI Case Study',
            'content': 'This company uses Amazon Bedrock for generative AI applications.',
            'expected': True
        },
        {
            'title': 'Machine Learning Success Story',
            'content': 'Using SageMaker and AI services to improve customer experience.',
            'expected': True
        },
        {
            'title': 'Traditional Database Migration',
            'content': 'Company migrated their database to RDS for better performance.',
            'expected': False
        },
        {
            'title': 'AWS Infrastructure Case Study',
            'content': 'Scaling compute resources with EC2 and auto-scaling.',
            'expected': False
        }
    ]
    
    print(f"AI Keywords ({len(scraper.ai_keywords)}): {', '.join(list(scraper.ai_keywords)[:8])}...")
    print("\nTesting AI story detection:")
    
    from bs4 import BeautifulSoup
    
    for i, case in enumerate(test_cases, 1):
        # Create mock HTML content
        html_content = f"""
        <html>
            <head><title>{case['title']}</title></head>
            <body>
                <h1>{case['title']}</h1>
                <p>{case['content']}</p>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        result = scraper._is_ai_story(soup, html_content)
        
        status = "✅ PASS" if result == case['expected'] else "❌ FAIL"
        print(f"{i}. {case['title']}")
        print(f"   Expected: {case['expected']}, Got: {result} {status}")

def main():
    # Setup logging
    Config.setup_logging()
    logging.getLogger().setLevel(logging.INFO)
    
    print("AWS Scraper Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: URL Discovery
        urls = test_aws_url_discovery()
        
        # Test 2: AI Filtering
        test_ai_filtering()
        
        # Test 3: Story Scraping (if URLs found)
        if urls:
            stories = test_aws_story_scraping(urls, limit=3)
            
            if stories:
                print("\n" + "=" * 60)
                print("DETAILED STORY ANALYSIS")
                print("=" * 60)
                
                for i, story in enumerate(stories, 1):
                    print(f"\nStory {i}: {story['customer_name']}")
                    print(f"Title: {story['title']}")
                    print(f"URL: {story['url']}")
                    print(f"Publish Date: {story['publish_date']}")
                    
                    raw_content = story['raw_content']
                    print(f"Word Count: {raw_content.get('metadata', {}).get('word_count', 'N/A')}")
                    
                    # Show first 200 chars of content
                    text_content = raw_content.get('text', '')
                    print(f"Content Preview: {text_content[:200]}...")
                    print("-" * 40)
        
        print("\n" + "=" * 60)
        print("AWS SCRAPER TEST COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()