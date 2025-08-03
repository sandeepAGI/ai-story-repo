#!/usr/bin/env python3
"""
Extract all Microsoft customer story links from the 1000+ stories blog post.
This script will scrape the full blog post content to extract every story link.
"""

import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set
import time

def get_full_blog_content(url: str) -> str:
    """Fetch the full blog post content with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching blog content: {e}")
        return ""

def extract_customer_story_links(html_content: str) -> Set[str]:
    """Extract all customer story links from the blog post"""
    soup = BeautifulSoup(html_content, 'html.parser')
    story_links = set()
    
    # Common Microsoft customer story URL patterns
    story_patterns = [
        r'https://customers\.microsoft\.com/[^"\s]+',
        r'https://www\.microsoft\.com/[^"\s]*customers?[^"\s]*',
        r'https://go\.microsoft\.com/fwlink/\?linkid=\d+',
        r'https://www\.microsoft\.com/[^"\s]*story[^"\s]*',
        r'https://azure\.microsoft\.com/[^"\s]*customer[^"\s]*'
    ]
    
    # Extract from all links
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').strip()
        if href and any(re.search(pattern, href, re.I) for pattern in story_patterns):
            story_links.add(href)
    
    # Extract from text content using regex
    text_content = soup.get_text()
    for pattern in story_patterns:
        matches = re.findall(pattern, text_content, re.I)
        story_links.update(matches)
    
    # Extract from script tags (JSON data)
    for script in soup.find_all('script'):
        script_content = script.get_text()
        for pattern in story_patterns:
            matches = re.findall(pattern, script_content, re.I)
            story_links.update(matches)
    
    return story_links

def clean_and_validate_links(links: Set[str]) -> List[str]:
    """Clean and validate the extracted links"""
    cleaned_links = []
    
    for link in links:
        # Remove common suffixes and clean up
        link = link.rstrip('.,;)')
        link = re.sub(r'["\']$', '', link)
        
        # Skip obvious non-story links
        skip_patterns = [
            r'/privacy[^/]*$',
            r'/terms[^/]*$',
            r'/support[^/]*$',
            r'/legal[^/]*$',
            r'/contact[^/]*$',
            r'\.css$',
            r'\.js$',
            r'\.png$',
            r'\.jpg$',
            r'\.gif$'
        ]
        
        if any(re.search(pattern, link, re.I) for pattern in skip_patterns):
            continue
        
        # Validate URL structure
        try:
            parsed = urlparse(link)
            if parsed.scheme and parsed.netloc:
                cleaned_links.append(link)
        except Exception:
            continue
    
    return sorted(list(set(cleaned_links)))

def save_links_to_files(links: List[str]):
    """Save the extracted links to both JSON and text files"""
    
    # Save as JSON with metadata
    data = {
        'extracted_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'source_url': 'https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/07/24/ai-powered-success-with-1000-stories-of-customer-transformation-and-innovation/',
        'total_links': len(links),
        'links': links
    }
    
    with open('microsoft_story_links.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save as plain text for easy viewing
    with open('microsoft_story_links.txt', 'w') as f:
        f.write(f"Microsoft Customer Story Links - Extracted on {data['extracted_date']}\n")
        f.write(f"Source: {data['source_url']}\n")
        f.write(f"Total Links: {data['total_links']}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, link in enumerate(links, 1):
            f.write(f"{i:3d}. {link}\n")

def main():
    """Main execution function"""
    blog_url = "https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/07/24/ai-powered-success-with-1000-stories-of-customer-transformation-and-innovation/"
    
    print("Extracting Microsoft customer story links from 1000+ stories blog post...")
    print(f"Source: {blog_url}")
    print()
    
    # Fetch full blog content
    print("1. Fetching full blog post content...")
    html_content = get_full_blog_content(blog_url)
    
    if not html_content:
        print("Failed to fetch blog content. Exiting.")
        return
    
    print(f"   ✓ Retrieved {len(html_content):,} characters of content")
    
    # Extract story links
    print("2. Extracting customer story links...")
    raw_links = extract_customer_story_links(html_content)
    print(f"   ✓ Found {len(raw_links)} potential story links")
    
    # Clean and validate
    print("3. Cleaning and validating links...")
    final_links = clean_and_validate_links(raw_links)
    print(f"   ✓ {len(final_links)} valid customer story links")
    
    # Save results
    print("4. Saving results...")
    save_links_to_files(final_links)
    print("   ✓ Saved to microsoft_story_links.json and microsoft_story_links.txt")
    
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Total Microsoft customer story links extracted: {len(final_links)}")
    print("\nFirst 10 links:")
    for i, link in enumerate(final_links[:10], 1):
        print(f"  {i:2d}. {link}")
    
    if len(final_links) > 10:
        print(f"  ... and {len(final_links) - 10} more")
    
    print(f"\nNext steps:")
    print("1. Review microsoft_story_links.txt for all extracted links")  
    print("2. Modify Microsoft scraper to process these pre-collected URLs")
    print("3. Run enhanced scraping to capture all stories")

if __name__ == "__main__":
    main()