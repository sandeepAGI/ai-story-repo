#!/usr/bin/env python3
"""
Analysis Tools
Consolidated tools for data analysis, quality checks, and system validation
"""

import sys
import os
import json
import pandas as pd
from typing import Dict, List, Optional
from collections import Counter

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations

class AnalysisTools:
    """Unified analysis tools for comprehensive data analysis"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.db_ops = DatabaseOperations()
    
    def analyze_categorical_data(self, limit: int = 15):
        """
        Analyze all categorical data available in the database
        
        Args:
            limit: Maximum number of categories to show per field
        """
        print("📊 COMPREHENSIVE CATEGORICAL DATA ANALYSIS")
        print("="*80)
        
        with self.db.get_cursor() as cursor:
            # 1. Main table categorical fields
            print("\n1️⃣ MAIN TABLE CATEGORICAL FIELDS:")
            print("-" * 50)
            
            # Industry analysis
            cursor.execute("""
                SELECT industry, COUNT(*) as count 
                FROM customer_stories 
                WHERE industry IS NOT NULL 
                GROUP BY industry 
                ORDER BY count DESC
            """)
            
            industries = cursor.fetchall()
            print(f"🏭 INDUSTRY ({len(industries)} categories, {sum(row['count'] for row in industries)} stories):")
            for row in industries[:limit]:
                print(f"   • {row['industry']}: {row['count']} stories")
            if len(industries) > limit:
                print(f"   ... and {len(industries) - limit} more categories")
            
            # Source analysis
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM customer_stories 
                GROUP BY source 
                ORDER BY count DESC
            """)
            
            sources = cursor.fetchall()
            print(f"\n📡 SOURCE ({len(sources)} sources):")
            for row in sources:
                print(f"   • {row['source']}: {row['count']} stories")
            
            # AI Type analysis
            cursor.execute("""
                SELECT 
                    extracted_data->>'ai_type' as ai_type,
                    COUNT(*) as count 
                FROM customer_stories 
                WHERE extracted_data->>'ai_type' IS NOT NULL
                GROUP BY extracted_data->>'ai_type'
                ORDER BY count DESC
            """)
            
            ai_types = cursor.fetchall()
            print(f"\n🤖 AI TYPE ({len(ai_types)} types):")
            for row in ai_types:
                print(f"   • {row['ai_type']}: {row['count']} stories")
            
            # Language analysis
            cursor.execute("""
                SELECT language, COUNT(*) as count 
                FROM customer_stories 
                WHERE language IS NOT NULL 
                GROUP BY language 
                ORDER BY count DESC
            """)
            
            languages = cursor.fetchall()
            print(f"\n🌐 LANGUAGE ({len(languages)} languages):")
            for row in languages[:limit]:
                print(f"   • {row['language']}: {row['count']} stories")
            
            # 2. Extracted data analysis
            print("\n\n2️⃣ EXTRACTED DATA CATEGORICAL FIELDS:")
            print("-" * 50)
            
            # Business outcomes
            cursor.execute("""
                SELECT extracted_data->>'business_outcomes' as outcomes
                FROM customer_stories 
                WHERE extracted_data->>'business_outcomes' IS NOT NULL
                AND extracted_data->>'business_outcomes' != '[]'
                AND extracted_data->>'business_outcomes' != 'null'
            """)
            
            outcomes_data = cursor.fetchall()
            all_outcomes = []
            
            for row in outcomes_data:
                try:
                    outcomes = json.loads(row['outcomes'])
                    if isinstance(outcomes, list):
                        all_outcomes.extend(outcomes)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            outcome_counts = Counter(all_outcomes)
            print(f"📈 BUSINESS OUTCOMES ({len(outcome_counts)} unique outcomes):")
            for outcome, count in outcome_counts.most_common(limit):
                print(f"   • {outcome}: {count} stories")
            
            # SuperPowers analysis (for Gen AI stories)
            cursor.execute("""
                SELECT extracted_data->'gen_ai_superpowers' as superpowers
                FROM customer_stories 
                WHERE extracted_data->'gen_ai_superpowers' IS NOT NULL
                AND is_gen_ai = TRUE
            """)
            
            superpowers_data = cursor.fetchall()
            all_superpowers = []
            
            for row in superpowers_data:
                try:
                    superpowers = row['superpowers']
                    if isinstance(superpowers, list):
                        all_superpowers.extend(superpowers)
                    elif isinstance(superpowers, str):
                        superpowers_list = json.loads(superpowers)
                        if isinstance(superpowers_list, list):
                            all_superpowers.extend(superpowers_list)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            superpower_counts = Counter(all_superpowers)
            print(f"\n⚡ GEN AI SUPERPOWERS ({len(superpower_counts)} unique powers):")
            for power, count in superpower_counts.most_common(limit):
                print(f"   • {power}: {count} stories")
            
            # 3. Data quality summary
            print("\n\n3️⃣ DATA QUALITY SUMMARY:")
            print("-" * 30)
            
            cursor.execute("SELECT COUNT(*) as total FROM customer_stories")
            total_stories = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as genai FROM customer_stories WHERE is_gen_ai = TRUE")
            genai_stories = cursor.fetchone()['genai']
            
            cursor.execute("SELECT COUNT(*) as with_aileron FROM customer_stories WHERE extracted_data->'gen_ai_superpowers' IS NOT NULL")
            aileron_stories = cursor.fetchone()['with_aileron']
            
            cursor.execute("SELECT COUNT(*) as with_outcomes FROM customer_stories WHERE extracted_data->>'business_outcomes' IS NOT NULL AND extracted_data->>'business_outcomes' != '[]'")
            outcome_stories = cursor.fetchone()['with_outcomes']
            
            print(f"📊 Total Stories: {total_stories}")
            print(f"🤖 Gen AI Stories: {genai_stories} ({genai_stories/total_stories*100:.1f}%)")
            print(f"⚡ With Aileron Data: {aileron_stories} ({aileron_stories/genai_stories*100:.1f}% of GenAI)")
            print(f"📈 With Business Outcomes: {outcome_stories} ({outcome_stories/total_stories*100:.1f}%)")
    
    def check_story_classifications(self, story_ids: List[int] = None):
        """
        Check classification status of specific stories
        
        Args:
            story_ids: List of story IDs to check (defaults to problematic stories)
        """
        if story_ids is None:
            story_ids = [1001, 978, 977, 302]  # Default problematic stories
        
        print("🔍 CHECKING STORY CLASSIFICATIONS")
        print("="*50)
        
        with self.db_ops.db.get_cursor() as cursor:
            for story_id in story_ids:
                cursor.execute("""
                    SELECT id, customer_name, source, is_gen_ai, 
                           extracted_data->>'ai_type' as ai_type,
                           CASE WHEN extracted_data->'gen_ai_superpowers' IS NOT NULL THEN 'HAS' ELSE 'MISSING' END as aileron_status,
                           scraped_date, title
                    FROM customer_stories
                    WHERE id = %s
                """, [story_id])
                
                story = cursor.fetchone()
                if story:
                    print(f"📝 ID {story['id']}: {story['customer_name']}")
                    print(f"   Source: {story['source']}")
                    print(f"   is_gen_ai (DB): {story['is_gen_ai']}")
                    print(f"   ai_type (extracted): {story['ai_type']}")
                    print(f"   Aileron data: {story['aileron_status']}")
                    print(f"   Scraped: {story['scraped_date']}")
                    if story['title']:
                        print(f"   Title: {story['title'][:60]}...")
                    print()
                else:
                    print(f"❌ Story ID {story_id} not found")
    
    def check_language_distribution(self, show_non_english: bool = False):
        """
        Check language distribution across stories
        
        Args:
            show_non_english: If True, show detailed breakdown of non-English stories
        """
        print("🌐 LANGUAGE DISTRIBUTION ANALYSIS")
        print("="*40)
        
        with self.db.get_cursor() as cursor:
            # Overall language distribution
            cursor.execute("""
                SELECT 
                    language,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customer_stories), 2) as percentage
                FROM customer_stories 
                WHERE language IS NOT NULL
                GROUP BY language 
                ORDER BY count DESC
            """)
            
            languages = cursor.fetchall()
            
            print("📊 LANGUAGE BREAKDOWN:")
            print("-" * 25)
            for lang in languages:
                print(f"{lang['language']}: {lang['count']} stories ({lang['percentage']}%)")
            
            if show_non_english:
                print("\n🔍 NON-ENGLISH STORIES DETAILS:")
                print("-" * 35)
                
                cursor.execute("""
                    SELECT id, customer_name, source, language, title
                    FROM customer_stories 
                    WHERE language != 'en' AND language IS NOT NULL
                    ORDER BY language, source
                    LIMIT 20
                """)
                
                non_english = cursor.fetchall()
                for story in non_english:
                    print(f"ID {story['id']}: {story['customer_name']} ({story['language']}, {story['source']})")
                    if story['title']:
                        print(f"   Title: {story['title'][:60]}...")
                    print()
    
    def check_data_consistency(self, detailed: bool = False):
        """
        Comprehensive data consistency checks
        
        Args:
            detailed: If True, show detailed information about inconsistencies
        """
        print("🔍 DATA CONSISTENCY ANALYSIS")
        print("="*40)
        
        with self.db.get_cursor() as cursor:
            print("1️⃣ GenAI Flag vs AI Type Consistency:")
            print("-" * 35)
            
            # Check is_gen_ai vs ai_type consistency
            cursor.execute("""
                SELECT 
                    is_gen_ai,
                    extracted_data->>'ai_type' as ai_type,
                    COUNT(*) as count
                FROM customer_stories 
                WHERE extracted_data->>'ai_type' IS NOT NULL
                GROUP BY is_gen_ai, extracted_data->>'ai_type'
                ORDER BY is_gen_ai, ai_type
            """)
            
            consistency_data = cursor.fetchall()
            inconsistent_count = 0
            
            for row in consistency_data:
                is_genai = row['is_gen_ai']
                ai_type = row['ai_type']
                count = row['count']
                
                # Check for inconsistencies
                is_inconsistent = (
                    (is_genai == True and ai_type == 'traditional') or
                    (is_genai == False and ai_type == 'generative')
                )
                
                status = "❌ INCONSISTENT" if is_inconsistent else "✅ Consistent"
                print(f"is_gen_ai={is_genai}, ai_type={ai_type}: {count} stories {status}")
                
                if is_inconsistent:
                    inconsistent_count += count
            
            print(f"\nTotal inconsistent stories: {inconsistent_count}")
            
            # Check for missing required fields
            print("\n2️⃣ Missing Required Fields:")
            print("-" * 30)
            
            missing_checks = [
                ("customer_name", "Customer Name"),
                ("content", "Content"), 
                ("source", "Source"),
                ("url", "URL")
            ]
            
            for field, display_name in missing_checks:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM customer_stories 
                    WHERE {field} IS NULL OR {field} = ''
                """)
                
                missing_count = cursor.fetchone()['count']
                cursor.execute("SELECT COUNT(*) as total FROM customer_stories")
                total_count = cursor.fetchone()['total']
                
                pct = (missing_count / total_count * 100) if total_count > 0 else 0
                status = "❌" if missing_count > 0 else "✅"
                print(f"{status} Missing {display_name}: {missing_count} ({pct:.1f}%)")
            
            # Check for duplicate URLs
            print("\n3️⃣ Duplicate Content Check:")
            print("-" * 25)
            
            cursor.execute("""
                SELECT url, COUNT(*) as count
                FROM customer_stories 
                WHERE url IS NOT NULL
                GROUP BY url
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 10
            """)
            
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"Found {len(duplicates)} URLs with duplicate stories:")
                for dup in duplicates:
                    print(f"  {dup['url'][:60]}... : {dup['count']} copies")
            else:
                print("✅ No duplicate URLs found")
    
    def analyze_fullstory_issue(self):
        """Analyze potential issues with story processing"""
        print("🔍 FULL STORY PROCESSING ANALYSIS")
        print("="*40)
        
        with self.db.get_cursor() as cursor:
            # Check for stories with processing issues
            cursor.execute("""
                SELECT 
                    source,
                    COUNT(*) as total_stories,
                    COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END) as missing_content,
                    COUNT(CASE WHEN extracted_data IS NULL THEN 1 END) as missing_extracted_data,
                    COUNT(CASE WHEN customer_name IS NULL OR customer_name = '' THEN 1 END) as missing_customer,
                    AVG(LENGTH(content)) as avg_content_length
                FROM customer_stories
                GROUP BY source
                ORDER BY total_stories DESC
            """)
            
            source_analysis = cursor.fetchall()
            
            print("📊 PROCESSING QUALITY BY SOURCE:")
            print("-" * 35)
            
            for row in source_analysis:
                source = row['source']
                total = row['total_stories']
                missing_content = row['missing_content'] or 0
                missing_data = row['missing_extracted_data'] or 0
                missing_customer = row['missing_customer'] or 0
                avg_length = int(row['avg_content_length']) if row['avg_content_length'] else 0
                
                print(f"\n{source}: {total} stories")
                print(f"  Missing content: {missing_content} ({missing_content/total*100:.1f}%)")
                print(f"  Missing extracted data: {missing_data} ({missing_data/total*100:.1f}%)")
                print(f"  Missing customer names: {missing_customer} ({missing_customer/total*100:.1f}%)")
                print(f"  Avg content length: {avg_length:,} chars")
            
            # Check for very short or very long content
            print("\n📏 CONTENT LENGTH ANALYSIS:")
            print("-" * 25)
            
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN LENGTH(content) < 100 THEN 1 END) as very_short,
                    COUNT(CASE WHEN LENGTH(content) BETWEEN 100 AND 1000 THEN 1 END) as short,
                    COUNT(CASE WHEN LENGTH(content) BETWEEN 1000 AND 5000 THEN 1 END) as medium,
                    COUNT(CASE WHEN LENGTH(content) BETWEEN 5000 AND 20000 THEN 1 END) as long,
                    COUNT(CASE WHEN LENGTH(content) > 20000 THEN 1 END) as very_long,
                    COUNT(*) as total
                FROM customer_stories
                WHERE content IS NOT NULL
            """)
            
            length_analysis = cursor.fetchone()
            
            categories = [
                ("Very Short (<100 chars)", length_analysis['very_short']),
                ("Short (100-1K chars)", length_analysis['short']),
                ("Medium (1K-5K chars)", length_analysis['medium']),
                ("Long (5K-20K chars)", length_analysis['long']),
                ("Very Long (>20K chars)", length_analysis['very_long'])
            ]
            
            total = length_analysis['total']
            for category, count in categories:
                pct = (count / total * 100) if total > 0 else 0
                print(f"  {category}: {count} ({pct:.1f}%)")

def main():
    """Main CLI interface"""
    tools = AnalysisTools()
    
    print("📊 ANALYSIS TOOLS")
    print("="*25)
    print("1. Analyze categorical data")
    print("2. Check story classifications") 
    print("3. Check language distribution")
    print("4. Check data consistency")
    print("5. Analyze processing issues")
    print("6. Run all analyses")
    print()
    
    choice = input("Select option (1-6): ").strip()
    
    print()
    
    if choice == '1':
        limit = input("Max categories to show per field (default: 15): ").strip()
        limit = int(limit) if limit.isdigit() else 15
        tools.analyze_categorical_data(limit=limit)
    elif choice == '2':
        story_ids_input = input("Story IDs (comma-separated, press Enter for defaults): ").strip()
        if story_ids_input:
            story_ids = [int(x.strip()) for x in story_ids_input.split(',') if x.strip().isdigit()]
        else:
            story_ids = None
        tools.check_story_classifications(story_ids=story_ids)
    elif choice == '3':
        show_detail = input("Show non-English story details? (y/n): ").strip().lower() == 'y'
        tools.check_language_distribution(show_non_english=show_detail)
    elif choice == '4':
        detailed = input("Show detailed inconsistency info? (y/n): ").strip().lower() == 'y'
        tools.check_data_consistency(detailed=detailed)
    elif choice == '5':
        tools.analyze_fullstory_issue()
    elif choice == '6':
        print("Running all analyses...\n")
        tools.analyze_categorical_data()
        print("\n" + "="*60 + "\n")
        tools.check_story_classifications()
        print("\n" + "="*60 + "\n")
        tools.check_language_distribution()
        print("\n" + "="*60 + "\n")
        tools.check_data_consistency()
        print("\n" + "="*60 + "\n")
        tools.analyze_fullstory_issue()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()