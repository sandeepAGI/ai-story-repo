#!/usr/bin/env python3
"""
Test OpenAI URL scraping with requests (no browser automation)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import time
import random
from bs4 import BeautifulSoup
from src.config import Config
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations

def test_requests_scraping():
    """Test scraping with requests library"""
    
    print("="*70)
    print("TESTING OPENAI REQUESTS-BASED SCRAPING")
    print("="*70)
    
    try:
        # Database setup
        print("1. Testing database connection...")
        db_connection = DatabaseConnection()
        if not db_connection.test_connection():
            print("❌ Database connection failed")
            return
        print("✅ Database connection successful")
        
        db_ops = DatabaseOperations(db_connection)
        openai_source = db_ops.get_source_by_name("OpenAI")
        pending_urls = db_ops.get_pending_urls(openai_source.id, limit=3)
        
        print(f"✅ Found {len(pending_urls)} URLs to test")
        
        # Setup session with realistic headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        for i, url_obj in enumerate(pending_urls, 1):
            url = url_obj.url
            print(f"\n--- Testing URL {i}/{len(pending_urls)} ---")
            print(f"Customer: {url_obj.inferred_customer_name}")
            print(f"URL: {url}")
            
            try:
                # Human-like delay
                time.sleep(random.uniform(2, 5))
                
                # Make request
                print("Making request...")
                response = session.get(url, timeout=30)
                
                print(f"Status code: {response.status_code}")
                print(f"Content length: {len(response.content)} bytes")
                
                if response.status_code == 200:
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract text content
                    for script in soup(["script", "style", "nav", "header", "footer"]):
                        script.decompose()
                    
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    clean_text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    word_count = len(clean_text.split())
                    
                    print(f"✅ Content extracted successfully!")
                    print(f"   Word count: {word_count}")
                    print(f"   Title: {soup.title.string if soup.title else 'No title'}")
                    
                    # Show sample content
                    if len(clean_text) > 200:
                        print(f"   Content sample: {clean_text[:200]}...")
                    else:
                        print(f"   Full content: {clean_text}")
                        
                    # Check for bot detection indicators
                    if any(indicator in clean_text.lower() for indicator in ['blocked', 'access denied', 'captcha', 'please verify']):
                        print("⚠️  Possible bot detection detected in content")
                    
                elif response.status_code == 403:
                    print("❌ 403 Forbidden - Bot detection likely")
                elif response.status_code == 429:
                    print("❌ 429 Rate Limited - Too many requests")
                else:
                    print(f"❌ HTTP {response.status_code} - {response.reason}")
                    
            except requests.exceptions.Timeout:
                print("❌ Request timeout")
            except Exception as e:
                print(f"❌ Request failed: {e}")
        
        print(f"\n{'-'*70}")
        print("REQUESTS-BASED SCRAPING TEST COMPLETED")
        print(f"{'-'*70}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_requests_scraping()