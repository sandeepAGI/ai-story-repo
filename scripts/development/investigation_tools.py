#!/usr/bin/env python3
"""
Investigation Tools
Consolidated tools for investigating data quality, content issues, and system behavior
"""

import sys
import os
import requests
import re
import json
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import DatabaseOperations

class InvestigationTools:
    """Unified investigation tools for data quality and content analysis"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    def investigate_blog_content(self, url: str = None):
        """
        Investigate blog post content to understand extraction issues
        
        Args:
            url: Blog URL to analyze (defaults to Microsoft 1000+ stories blog)
        """
        if url is None:
            url = "https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/07/24/ai-powered-success-with-1000-stories-of-customer-transformation-and-innovation/"
        
        print("🔍 INVESTIGATING BLOG CONTENT")
        print("="*50)
        print(f"URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=8',
        }
        
        try:
            print("Fetching blog post...")
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Content Length: {len(response.text):,} characters")
            print(f"Content Type: {response.headers.get('Content-Type', 'Unknown')}")
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch content: {response.status_code}")
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for specific mentions
            print("\n" + "="*50)
            print("SEARCHING FOR KEY MENTIONS")
            print("="*50)
            
            text_content = soup.get_text()
            
            # Search for story count mentions
            story_patterns = ['1000', '1,000', 'thousand', 'stories', 'customers']
            for pattern in story_patterns:
                lines_with_pattern = []
                for i, line in enumerate(text_content.split('\n')):
                    if pattern.lower() in line.lower():
                        lines_with_pattern.append(f"Line {i}: {line.strip()}")
                
                if lines_with_pattern:
                    print(f"\n📝 Lines containing '{pattern}':")
                    for line in lines_with_pattern[:5]:  # Show first 5 matches
                        print(f"   {line}")
                    if len(lines_with_pattern) > 5:
                        print(f"   ... and {len(lines_with_pattern) - 5} more")
            
            # Check for dynamic content indicators
            print("\n" + "="*50)
            print("CHECKING FOR DYNAMIC CONTENT")
            print("="*50)
            
            # Look for JavaScript that might load content
            scripts = soup.find_all('script')
            js_indicators = ['ajax', 'fetch', 'xhr', 'load', 'dynamic']
            
            dynamic_content_found = False
            for script in scripts:
                if script.string:
                    script_text = script.string.lower()
                    for indicator in js_indicators:
                        if indicator in script_text:
                            dynamic_content_found = True
                            print(f"   📄 Found {indicator} in JavaScript")
                            break
            
            if not dynamic_content_found:
                print("   ✅ No obvious dynamic content loading detected")
            
            # Look for pagination or load-more buttons
            load_more = soup.find_all(['button', 'a'], string=re.compile(r'load|more|next', re.I))
            if load_more:
                print(f"   🔄 Found {len(load_more)} potential load-more elements")
                for elem in load_more[:3]:
                    print(f"      {elem.name}: {elem.get_text()}")
            
        except Exception as e:
            print(f"❌ Error investigating blog content: {e}")
    
    def investigate_missing_aileron(self, limit: int = 20):
        """
        Investigate Gen AI stories missing Aileron framework data
        
        Args:
            limit: Maximum number of stories to show in detail
        """
        print("🔍 INVESTIGATING MISSING AILERON FRAMEWORK DATA")
        print("="*60)
        
        with self.db_ops.db.get_cursor() as cursor:
            # Get Gen AI stories and their Aileron status
            cursor.execute("""
                SELECT 
                    id,
                    customer_name,
                    source,
                    title,
                    scraped_date,
                    extracted_data,
                    CASE 
                        WHEN extracted_data->'gen_ai_superpowers' IS NOT NULL THEN 'HAS_SUPERPOWERS'
                        ELSE 'MISSING_SUPERPOWERS'
                    END as aileron_status
                FROM customer_stories 
                WHERE is_gen_ai = TRUE
                ORDER BY scraped_date DESC
            """)
            
            stories = cursor.fetchall()
            
            # Count by status
            status_counts = {}
            for story in stories:
                status = story['aileron_status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("📊 AILERON STATUS SUMMARY")
            print("-" * 30)
            for status, count in status_counts.items():
                print(f"{status}: {count}")
            
            total_genai = len(stories)
            missing_count = status_counts.get('MISSING_SUPERPOWERS', 0)
            coverage_pct = ((total_genai - missing_count) / total_genai * 100) if total_genai > 0 else 0
            
            print(f"\nTotal Gen AI Stories: {total_genai}")
            print(f"Missing Aileron Data: {missing_count}")
            print(f"Coverage: {coverage_pct:.1f}%")
            
            # Show detailed breakdown by source
            print("\n📊 BREAKDOWN BY SOURCE")
            print("-" * 30)
            source_breakdown = {}
            for story in stories:
                source = story['source']
                status = story['aileron_status']
                
                if source not in source_breakdown:
                    source_breakdown[source] = {'HAS_SUPERPOWERS': 0, 'MISSING_SUPERPOWERS': 0}
                source_breakdown[source][status] += 1
            
            for source, counts in source_breakdown.items():
                total = counts['HAS_SUPERPOWERS'] + counts['MISSING_SUPERPOWERS']
                missing = counts['MISSING_SUPERPOWERS']
                pct_missing = (missing / total * 100) if total > 0 else 0
                print(f"{source}: {missing}/{total} missing ({pct_missing:.1f}%)")
            
            # Show sample of missing stories
            missing_stories = [s for s in stories if s['aileron_status'] == 'MISSING_SUPERPOWERS']
            if missing_stories:
                print(f"\n📝 SAMPLE MISSING STORIES (showing {min(limit, len(missing_stories))}):")
                print("-" * 50)
                
                for i, story in enumerate(missing_stories[:limit]):
                    print(f"{i+1}. ID {story['id']}: {story['customer_name']}")
                    print(f"   Source: {story['source']}")
                    print(f"   Date: {story['scraped_date']}")
                    if story['title']:
                        print(f"   Title: {story['title'][:80]}...")
                    print()
    
    def investigate_customer_names(self, source: str = None, pattern: str = None):
        """
        Investigate customer naming patterns and potential issues
        
        Args:
            source: Filter by specific source
            pattern: Search for specific pattern in names
        """
        print("🔍 INVESTIGATING CUSTOMER NAMES")
        print("="*40)
        
        with self.db_ops.db.get_cursor() as cursor:
            # Build query based on parameters
            where_clause = "WHERE 1=1"
            params = []
            
            if source:
                where_clause += " AND source = %s"
                params.append(source)
                
            if pattern:
                where_clause += " AND customer_name ILIKE %s"
                params.append(f"%{pattern}%")
            
            query = f"""
                SELECT 
                    id,
                    customer_name,
                    source,
                    scraped_date,
                    title
                FROM customer_stories 
                {where_clause}
                ORDER BY customer_name
            """
            
            cursor.execute(query, params)
            stories = cursor.fetchall()
            
            print(f"Found {len(stories)} stories")
            if source:
                print(f"Source filter: {source}")
            if pattern:
                print(f"Pattern filter: {pattern}")
            
            # Analyze naming patterns
            print("\n📊 NAMING PATTERN ANALYSIS")
            print("-" * 30)
            
            patterns = {
                'Contains colon (:)': 0,
                'Contains pipe (|)': 0,
                'Contains dash (-)': 0,
                'Contains numbers': 0,
                'Contains special chars': 0,
                'Very short (<=3 chars)': 0,
                'Very long (>50 chars)': 0,
                'Empty or null': 0
            }
            
            unusual_names = []
            
            for story in stories:
                name = story['customer_name'] or ""
                
                if ':' in name:
                    patterns['Contains colon (:)'] += 1
                if '|' in name:
                    patterns['Contains pipe (|)'] += 1
                if '-' in name:
                    patterns['Contains dash (-)'] += 1
                if re.search(r'\d', name):
                    patterns['Contains numbers'] += 1
                if re.search(r'[^\w\s\-\.]', name):
                    patterns['Contains special chars'] += 1
                    unusual_names.append((story['id'], name))
                if len(name) <= 3:
                    patterns['Very short (<=3 chars)'] += 1
                if len(name) > 50:
                    patterns['Very long (>50 chars)'] += 1
                if not name.strip():
                    patterns['Empty or null'] += 1
            
            for pattern_name, count in patterns.items():
                if count > 0:
                    pct = (count / len(stories) * 100) if stories else 0
                    print(f"{pattern_name}: {count} ({pct:.1f}%)")
            
            # Show unusual names
            if unusual_names:
                print(f"\n📝 UNUSUAL NAMES (showing first 10):")
                print("-" * 40)
                for story_id, name in unusual_names[:10]:
                    print(f"ID {story_id}: '{name}'")
    
    def investigate_high_value_outcomes(self, min_stories: int = 5):
        """
        Investigate high-value business outcomes and their patterns
        
        Args:
            min_stories: Minimum number of stories to consider outcome significant
        """
        print("🔍 INVESTIGATING HIGH-VALUE BUSINESS OUTCOMES")
        print("="*50)
        
        with self.db_ops.db.get_cursor() as cursor:
            # Get all business outcomes
            cursor.execute("""
                SELECT 
                    id,
                    customer_name,
                    source,
                    extracted_data->>'business_outcomes' as outcomes,
                    extracted_data->>'ai_type' as ai_type,
                    is_gen_ai
                FROM customer_stories 
                WHERE extracted_data->>'business_outcomes' IS NOT NULL
                AND extracted_data->>'business_outcomes' != '[]'
                AND extracted_data->>'business_outcomes' != 'null'
                ORDER BY source, customer_name
            """)
            
            stories = cursor.fetchall()
            
            print(f"Found {len(stories)} stories with business outcomes data")
            
            # Parse and count outcomes
            outcome_counts = {}
            outcome_by_source = {}
            outcome_by_ai_type = {}
            
            for story in stories:
                try:
                    outcomes_str = story['outcomes']
                    if outcomes_str:
                        outcomes = json.loads(outcomes_str)
                        if isinstance(outcomes, list):
                            for outcome in outcomes:
                                if outcome and isinstance(outcome, str):
                                    # Overall counts
                                    outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
                                    
                                    # By source
                                    source = story['source']
                                    if source not in outcome_by_source:
                                        outcome_by_source[source] = {}
                                    outcome_by_source[source][outcome] = outcome_by_source[source].get(outcome, 0) + 1
                                    
                                    # By AI type
                                    ai_type = story['ai_type'] or ('Gen AI' if story['is_gen_ai'] else 'Traditional')
                                    if ai_type not in outcome_by_ai_type:
                                        outcome_by_ai_type[ai_type] = {}
                                    outcome_by_ai_type[ai_type][outcome] = outcome_by_ai_type[ai_type].get(outcome, 0) + 1
                
                except (json.JSONDecodeError, TypeError) as e:
                    continue
            
            # Show high-value outcomes
            print("\n📊 TOP BUSINESS OUTCOMES")
            print("-" * 30)
            sorted_outcomes = sorted(outcome_counts.items(), key=lambda x: x[1], reverse=True)
            
            for outcome, count in sorted_outcomes:
                if count >= min_stories:
                    pct = (count / len(stories) * 100) if stories else 0
                    print(f"{outcome}: {count} stories ({pct:.1f}%)")
            
            # Show breakdown by source for top outcomes
            print("\n📊 TOP OUTCOMES BY SOURCE")
            print("-" * 35)
            
            top_outcomes = [outcome for outcome, count in sorted_outcomes[:5] if count >= min_stories]
            
            for source, source_outcomes in outcome_by_source.items():
                print(f"\n{source}:")
                source_sorted = sorted(source_outcomes.items(), key=lambda x: x[1], reverse=True)
                for outcome, count in source_sorted[:3]:
                    if outcome in top_outcomes:
                        print(f"  {outcome}: {count}")
            
            # Show AI type breakdown
            print("\n📊 OUTCOMES BY AI TYPE")
            print("-" * 25)
            
            for ai_type, ai_outcomes in outcome_by_ai_type.items():
                print(f"\n{ai_type}:")
                ai_sorted = sorted(ai_outcomes.items(), key=lambda x: x[1], reverse=True)
                for outcome, count in ai_sorted[:5]:
                    print(f"  {outcome}: {count}")

def main():
    """Main CLI interface"""
    tools = InvestigationTools()
    
    print("🔍 INVESTIGATION TOOLS")
    print("="*30)
    print("1. Investigate blog content")
    print("2. Investigate missing Aileron data") 
    print("3. Investigate customer names")
    print("4. Investigate high-value outcomes")
    print()
    
    choice = input("Select option (1-4): ").strip()
    
    print()
    
    if choice == '1':
        url = input("Blog URL (press Enter for default Microsoft blog): ").strip()
        tools.investigate_blog_content(url if url else None)
    elif choice == '2':
        limit = input("Number of sample stories to show (default: 20): ").strip()
        limit = int(limit) if limit.isdigit() else 20
        tools.investigate_missing_aileron(limit=limit)
    elif choice == '3':
        source = input("Source filter (press Enter for all): ").strip() or None
        pattern = input("Pattern to search for (press Enter for none): ").strip() or None
        tools.investigate_customer_names(source=source, pattern=pattern)
    elif choice == '4':
        min_stories = input("Minimum stories for significant outcome (default: 5): ").strip()
        min_stories = int(min_stories) if min_stories.isdigit() else 5
        tools.investigate_high_value_outcomes(min_stories=min_stories)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()