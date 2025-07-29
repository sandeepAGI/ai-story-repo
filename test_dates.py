#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scrapers.anthropic_scraper import AnthropicScraper

def test_date_extraction():
    """Test the date extraction from Anthropic customer page"""
    scraper = AnthropicScraper()
    
    print("Testing date extraction...")
    stories_with_dates = scraper.get_customer_story_urls_with_dates()
    
    print(f"Found {len(stories_with_dates)} stories")
    
    # Show first 10 with dates
    stories_with_publish_dates = [s for s in stories_with_dates if s['publish_date']]
    print(f"Stories with publish dates: {len(stories_with_publish_dates)}")
    
    for i, story in enumerate(stories_with_dates[:10]):
        print(f"{i+1}. {story['url']} -> {story['publish_date']}")

if __name__ == "__main__":
    test_date_extraction()