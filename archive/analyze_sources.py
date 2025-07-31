#!/usr/bin/env python3
"""
Analyze different AI provider sources to understand:
1. How to filter for AI-specific stories
2. What publish date formats are available
3. Source-specific patterns and structures
"""

import requests
import time
from bs4 import BeautifulSoup

def analyze_source(name, url, sample_story_url=None):
    """Analyze a source for AI story patterns and date formats"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {name}")
    print(f"Base URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for AI-related keywords in page structure
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'claude', 'gpt', 'openai', 'azure ai', 'bedrock']
        
        # Check titles and headings
        titles = [tag.get_text().lower() for tag in soup.find_all(['h1', 'h2', 'h3', 'title'])]
        ai_in_titles = [title for title in titles if any(kw in title for kw in ai_keywords)]
        
        print(f"AI-related titles found: {len(ai_in_titles)}")
        for title in ai_in_titles[:3]:
            print(f"  - {title[:100]}...")
        
        # Look for date patterns
        date_elements = soup.find_all(['time', 'span', 'div'], attrs={
            'class': lambda x: x and any(word in str(x).lower() for word in ['date', 'time', 'publish', 'created', 'updated'])
        })
        
        print(f"\nDate elements found: {len(date_elements)}")
        for elem in date_elements[:5]:
            print(f"  - {elem.name}: {elem.get('class')} = '{elem.get_text().strip()[:50]}'")
        
        # Look for story/case study links
        story_links = soup.find_all('a', href=True)
        story_urls = []
        for link in story_links:
            href = link.get('href', '')
            text = link.get_text().lower()
            if any(pattern in href.lower() or pattern in text for pattern in ['case-study', 'customer', 'story', 'case']):
                if href.startswith('http') or href.startswith('/'):
                    story_urls.append(href)
        
        print(f"\nPotential story URLs found: {len(story_urls)}")
        for url in story_urls[:5]:
            print(f"  - {url}")
        
        # If we have a sample story URL, analyze its structure
        if sample_story_url:
            print(f"\n--- ANALYZING SAMPLE STORY ---")
            print(f"URL: {sample_story_url}")
            try:
                story_response = requests.get(sample_story_url, timeout=30)
                story_soup = BeautifulSoup(story_response.text, 'html.parser')
                
                # Look for publish dates in sample story
                story_dates = story_soup.find_all(['time', 'span', 'div'], attrs={
                    'datetime': True
                }) + story_soup.find_all(['time', 'span', 'div'], attrs={
                    'class': lambda x: x and any(word in str(x).lower() for word in ['date', 'publish', 'created'])
                })
                
                print(f"Date elements in story: {len(story_dates)}")
                for date_elem in story_dates[:3]:
                    datetime_attr = date_elem.get('datetime', '')
                    text_content = date_elem.get_text().strip()
                    print(f"  - {date_elem.name}: datetime='{datetime_attr}', text='{text_content}'")
                
                # Look for AI keywords in story
                story_text = story_soup.get_text().lower()
                ai_mentions = sum(story_text.count(kw) for kw in ai_keywords)
                print(f"AI keyword mentions in story: {ai_mentions}")
                
            except Exception as e:
                print(f"Error analyzing sample story: {e}")
        
        time.sleep(2)  # Rate limiting
        
    except Exception as e:
        print(f"Error analyzing {name}: {e}")

def main():
    """Analyze all major AI provider sources"""
    
    sources = [
        {
            'name': 'Anthropic',
            'url': 'https://www.anthropic.com/customers',
            'sample': 'https://www.anthropic.com/customers/hume'
        },
        {
            'name': 'OpenAI', 
            'url': 'https://openai.com/stories/',
            'sample': 'https://openai.com/index/moderna/'
        },
        {
            'name': 'Microsoft Azure AI',
            'url': 'https://www.microsoft.com/en-us/ai/ai-customer-stories',
            'sample': None  # We'll analyze structure first
        },
        {
            'name': 'AWS AI/ML',
            'url': 'https://aws.amazon.com/ai/generative-ai/customers/',
            'sample': None
        },
        {
            'name': 'Google Cloud AI', 
            'url': 'https://cloud.google.com/ai/generative-ai/stories',
            'sample': None
        }
    ]
    
    for source in sources:
        analyze_source(source['name'], source['url'], source.get('sample'))
        
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()