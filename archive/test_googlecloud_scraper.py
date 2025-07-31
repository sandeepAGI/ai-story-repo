#!/usr/bin/env python3
"""Test script for Google Cloud scraper"""

import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scrapers.googlecloud_scraper import GoogleCloudScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_url_discovery():
    """Test URL discovery functionality"""
    scraper = GoogleCloudScraper()
    
    print("=== Testing Google Cloud URL Discovery ===")
    urls = scraper.get_customer_story_urls()
    
    print(f"\nFound {len(urls)} customer story URLs:")
    for i, url in enumerate(urls[:10], 1):  # Show first 10
        print(f"{i}. {url}")
    
    if len(urls) > 10:
        print(f"... and {len(urls) - 10} more URLs")
    
    return urls

def test_story_scraping():
    """Test scraping specific customer stories"""
    scraper = GoogleCloudScraper()
    
    # Test URLs we know exist
    test_urls = [
        "https://cloud.google.com/customers/doc-ai",
        "https://cloud.google.com/customers/strise-ai", 
        "https://cloud.google.com/customers/ai21"
    ]
    
    print("\n=== Testing Google Cloud Story Scraping ===")
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        
        try:
            story_data = scraper.scrape_story(url)
            
            if story_data:
                print(f"✅ Success!")
                print(f"   Title: {story_data['title']}")
                print(f"   Customer: {story_data['customer_name']}")
                print(f"   Content length: {len(story_data['content'])} chars")
                print(f"   Publish date: {story_data['publish_date']}")
                print(f"   Word count: {story_data['raw_content']['metadata']['word_count']}")
                
                # Show first 200 chars of content
                content_preview = story_data['content'][:200] + "..." if len(story_data['content']) > 200 else story_data['content']
                print(f"   Content preview: {content_preview}")
            else:
                print("❌ Failed to scrape or not an AI story")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_ai_filtering():
    """Test AI content filtering"""
    scraper = GoogleCloudScraper()
    
    print("\n=== Testing AI Content Filtering ===")
    
    # Test content that should pass AI filtering
    ai_content = """
    This company uses Google Cloud Vertex AI and machine learning to process 
    natural language and build generative AI applications with Gemini.
    They implemented artificial intelligence solutions for computer vision.
    """
    
    # Test content that should fail AI filtering
    non_ai_content = """
    This company uses Google Cloud Storage and Compute Engine to host their
    web application. They migrated their database to Cloud SQL and use
    Google Kubernetes Engine for container orchestration.
    """
    
    print(f"AI content passes filter: {scraper._is_ai_story(ai_content.lower())}")
    print(f"Non-AI content passes filter: {scraper._is_ai_story(non_ai_content.lower())}")

if __name__ == "__main__":
    # Test AI filtering first (quick test)
    test_ai_filtering()
    
    # Test URL discovery
    urls = test_url_discovery()
    
    # Test story scraping with known URLs
    test_story_scraping()
    
    print("\n=== Google Cloud Scraper Testing Complete ===")