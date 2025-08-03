#!/usr/bin/env python3
"""
Check if Claude successfully analyzed the 5 non-English Microsoft stories
"""

import psycopg2
import os
import json
from urllib.parse import urlparse

# Get database connection
database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/ai_stories')
parsed = urlparse(database_url)

conn = psycopg2.connect(
    host=parsed.hostname or 'localhost',
    database=parsed.path.lstrip('/') or 'ai_stories',
    user=parsed.username,
    password=parsed.password,
    port=parsed.port or 5432
)

cur = conn.cursor()

# Get the 5 non-English Microsoft stories with their analysis data
non_english_urls = [
    'https://www.microsoft.com/ja-jp/customers/story/18738-konica-minolta-azure-open-ai-service',
    'https://www.microsoft.com/ko-kr/customers/story/19276-kt-onedrive', 
    'https://www.microsoft.com/ko-kr/customers/story/19277-krafton-microsoft-365',
    'https://www.microsoft.com/ko-kr/customers/story/20335-law-and-company-azure-functions',
    'https://www.microsoft.com/zh-cn/customers/story/1791859496343328428-joyson-microsoft-copilot-for-microsoft-365-discrete-manufacturing-zh-china'
]

for i, url in enumerate(non_english_urls, 1):
    cur.execute('''
        SELECT 
            cs.customer_name,
            cs.title, 
            cs.industry,
            cs.company_size,
            cs.use_case_category,
            cs.extracted_data,
            cs.url
        FROM customer_stories cs
        JOIN sources s ON cs.source_id = s.id
        WHERE s.name = 'Microsoft' AND cs.url = %s
    ''', (url,))
    
    result = cur.fetchone()
    
    if result:
        customer_name, title, industry, company_size, use_case_category, extracted_data, story_url = result
        
        # Determine language from URL
        if '/ja-jp/' in url:
            language = 'Japanese'
        elif '/ko-kr/' in url:
            language = 'Korean'
        elif '/zh-cn/' in url:
            language = 'Chinese'
        else:
            language = 'Unknown'
        
        print(f"{i}. [{language}] {customer_name}")
        print(f"   Title: {title}")
        print(f"   Industry: {industry or 'Not extracted'}")
        print(f"   Company Size: {company_size or 'Not extracted'}")
        print(f"   Use Case: {use_case_category or 'Not extracted'}")
        
        # Check if extracted_data exists and has content
        if extracted_data:
            try:
                data = json.loads(extracted_data) if isinstance(extracted_data, str) else extracted_data
                
                # Check key fields
                has_summary = bool(data.get('summary'))
                has_business_outcomes = bool(data.get('business_outcomes'))
                has_technologies = bool(data.get('technologies'))
                has_quality_score = data.get('content_quality_score', 0) > 0
                
                print(f"   ✅ Claude Analysis: SUCCESS")
                print(f"   - Summary: {'✅' if has_summary else '❌'}")
                print(f"   - Business Outcomes: {'✅' if has_business_outcomes else '❌'}")
                print(f"   - Technologies: {'✅' if has_technologies else '❌'}")
                print(f"   - Quality Score: {data.get('content_quality_score', 'N/A')}")
                
                # Check Gen AI classification
                is_gen_ai = data.get('is_gen_ai')
                print(f"   - Gen AI Classification: {is_gen_ai}")
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f"   ❌ Claude Analysis: FAILED - Invalid extracted_data")
                print(f"   Error: {e}")
        else:
            print(f"   ❌ Claude Analysis: FAILED - No extracted_data")
        
        print(f"   URL: {story_url}")
        print()
    else:
        print(f"{i}. Story not found in database: {url}")
        print()

conn.close()