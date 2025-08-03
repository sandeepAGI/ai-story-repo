#!/usr/bin/env python3
"""
Investigate the Microsoft blog post content to understand why we only extracted 656 stories
when Microsoft claims 1000+. Check for dynamic loading, missing patterns, etc.
"""

import requests
import re
from bs4 import BeautifulSoup
import json

def analyze_blog_content():
    """Analyze the blog post in detail"""
    url = "https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/07/24/ai-powered-success-with-1000-stories-of-customer-transformation-and-innovation/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    print("Fetching blog post...")
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text):,} characters")
    print(f"Content Type: {response.headers.get('Content-Type', 'Unknown')}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for mentions of "1000" in the content
    print("\n" + "="*50)
    print("SEARCHING FOR '1000' MENTIONS")
    print("="*50)
    
    text_content = soup.get_text()
    lines_with_1000 = []
    for i, line in enumerate(text_content.split('\n')):
        if '1000' in line or '1,000' in line:
            lines_with_1000.append(f"Line {i}: {line.strip()}")
    
    for line in lines_with_1000:
        print(line)
    
    # Check for JavaScript that might load content dynamically
    print("\n" + "="*50)
    print("CHECKING FOR DYNAMIC CONTENT LOADING")
    print("="*50)
    
    script_tags = soup.find_all('script')
    print(f"Found {len(script_tags)} script tags")
    
    # Look for scripts that might load story data
    for i, script in enumerate(script_tags):
        script_content = script.get_text()
        if any(term in script_content.lower() for term in ['stories', 'customer', 'ajax', 'fetch', 'load']):
            print(f"\nScript {i} (potentially relevant):")
            print(script_content[:200] + "..." if len(script_content) > 200 else script_content)
    
    # Check for data attributes or JSON
    print("\n" + "="*50)
    print("CHECKING FOR EMBEDDED DATA")
    print("="*50)
    
    # Look for data attributes
    elements_with_data = soup.find_all(attrs=lambda x: x and any(key.startswith('data-') for key in x.keys()))
    print(f"Found {len(elements_with_data)} elements with data attributes")
    
    # Look for JSON in script tags
    json_scripts = []
    for script in script_tags:
        script_content = script.get_text().strip()
        if script_content.startswith('{') and script_content.endswith('}'):
            json_scripts.append(script_content)
    
    print(f"Found {len(json_scripts)} potential JSON scripts")
    
    # Analyze existing URL patterns in more detail
    print("\n" + "="*50)
    print("DETAILED URL PATTERN ANALYSIS")
    print("="*50)
    
    # All possible Microsoft story URL patterns
    all_patterns = [
        r'https://customers\.microsoft\.com/[^"\s\)]+',
        r'https://www\.microsoft\.com/[^"\s\)]*customers?[^"\s\)]*',
        r'https://go\.microsoft\.com/fwlink/\?linkid=\d+',
        r'https://www\.microsoft\.com/[^"\s\)]*story[^"\s\)]*',
        r'https://azure\.microsoft\.com/[^"\s\)]*customer[^"\s\)]*',
        r'https://techcommunity\.microsoft\.com/[^"\s\)]*customer[^"\s\)]*',
        r'https://[^"\s\)]*\.microsoft\.com/[^"\s\)]*story[^"\s\)]*',
        r'https://[^"\s\)]*\.microsoft\.com/[^"\s\)]*customer[^"\s\)]*'
    ]
    
    found_urls = set()
    for pattern in all_patterns:
        matches = re.findall(pattern, response.text, re.I)
        found_urls.update(matches)
        print(f"Pattern '{pattern}': {len(matches)} matches")
    
    print(f"\nTotal unique URLs found: {len(found_urls)}")
    
    # Check if there are references to other pages or collections
    print("\n" + "="*50)
    print("CHECKING FOR REFERENCES TO OTHER COLLECTIONS")
    print("="*50)
    
    # Look for links to customer story collections
    collection_patterns = [
        r'https://[^"\s]*microsoft\.com/[^"\s]*customer[^"\s]*',
        r'https://[^"\s]*microsoft\.com/[^"\s]*search[^"\s]*',
        r'https://[^"\s]*microsoft\.com/[^"\s]*resource[^"\s]*'
    ]
    
    for pattern in collection_patterns:
        matches = re.findall(pattern, response.text, re.I)
        if matches:
            print(f"Collection pattern '{pattern}': {len(matches)} matches")
            for match in matches[:5]:  # Show first 5
                print(f"  {match}")

def check_story_pagination():
    """Check if the stories are paginated or loaded dynamically"""
    print("\n" + "="*50)
    print("CHECKING MICROSOFT CUSTOMER STORIES PAGINATION")
    print("="*50)
    
    # Check the main customer stories search page
    search_url = "https://www.microsoft.com/en-us/customers/search"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for pagination info
        text = soup.get_text()
        
        # Look for total count indicators
        count_patterns = [
            r'(\d+)\s*of\s*(\d+)',
            r'showing\s*(\d+)',
            r'total\s*(\d+)',
            r'(\d+)\s*results?'
        ]
        
        for pattern in count_patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                print(f"Found count pattern '{pattern}': {matches}")
        
    except Exception as e:
        print(f"Error checking search page: {e}")

if __name__ == "__main__":
    analyze_blog_content()
    check_story_pagination()