#!/usr/bin/env python3
"""
Basic Query Interface for AI Customer Stories Database
Provides command-line interface for exploring and searching stored data
"""

import sys
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations
from utils.deduplication import DeduplicationEngine

class QueryInterface:
    def __init__(self):
        self.db = DatabaseConnection()
        self.db_ops = DatabaseOperations(self.db)
        self.dedup = DeduplicationEngine(self.db_ops)
        
    def show_summary_stats(self):
        """Display database summary statistics"""
        print("\n" + "="*60)
        print("AI CUSTOMER STORIES DATABASE SUMMARY")
        print("="*60)
        
        with self.db.get_cursor() as cursor:
            # Total stories by source
            cursor.execute("""
                SELECT s.name, COUNT(cs.id) as story_count,
                       MIN(cs.publish_date) as earliest_story,
                       MAX(cs.publish_date) as latest_story
                FROM sources s 
                LEFT JOIN customer_stories cs ON s.id = cs.source_id 
                GROUP BY s.name, s.id
                ORDER BY story_count DESC
            """)
            
            print("\nSTORIES BY SOURCE:")
            print("-" * 40)
            total_stories = 0
            for row in cursor.fetchall():
                earliest = row['earliest_story'].strftime('%Y-%m-%d') if row['earliest_story'] else 'N/A'
                latest = row['latest_story'].strftime('%Y-%m-%d') if row['latest_story'] else 'N/A'
                print(f"{row['name']:<15}: {row['story_count']:>3} stories ({earliest} to {latest})")
                total_stories += row['story_count']
            
            print(f"{'TOTAL':<15}: {total_stories:>3} stories")
            
            # Industry breakdown
            cursor.execute("""
                SELECT industry, COUNT(*) as count 
                FROM customer_stories 
                WHERE industry IS NOT NULL 
                GROUP BY industry 
                ORDER BY count DESC 
                LIMIT 10
            """)
            
            print("\nTOP INDUSTRIES:")
            print("-" * 40)
            for row in cursor.fetchall():
                print(f"{row['industry']:<20}: {row['count']:>3} stories")
            
            # Company size breakdown
            cursor.execute("""
                SELECT company_size, COUNT(*) as count 
                FROM customer_stories 
                WHERE company_size IS NOT NULL 
                GROUP BY company_size 
                ORDER BY count DESC
            """)
            
            print("\nCOMPANY SIZES:")
            print("-" * 40)
            for row in cursor.fetchall():
                print(f"{row['company_size']:<15}: {row['count']:>3} stories")
            
            # Recent stories
            cursor.execute("""
                SELECT customer_name, s.name as source, publish_date, scraped_date
                FROM customer_stories cs
                JOIN sources s ON cs.source_id = s.id
                ORDER BY cs.scraped_date DESC 
                LIMIT 5
            """)
            
            print("\nRECENT STORIES:")
            print("-" * 40)
            for row in cursor.fetchall():
                pub_date = row['publish_date'].strftime('%Y-%m-%d') if row['publish_date'] else 'Unknown'
                scraped_date = row['scraped_date'].strftime('%Y-%m-%d')
                print(f"{row['customer_name']:<20} ({row['source']}) - Published: {pub_date}, Scraped: {scraped_date}")
    
    def search_stories(self, query: str, limit: int = 10) -> List[Dict]:
        """Search stories using full-text search"""
        print(f"\nSearching for: '{query}' (limit: {limit})")
        print("-" * 50)
        
        stories = self.db_ops.search_stories(query, limit)
        
        if not stories:
            print("No stories found matching your search.")
            return []
        
        results = []
        for i, story in enumerate(stories, 1):
            result = {
                'rank': i,
                'customer_name': story.customer_name,
                'title': story.title,
                'industry': story.industry,
                'url': story.url,
                'publish_date': story.publish_date.strftime('%Y-%m-%d') if story.publish_date else 'Unknown',
                'summary': story.extracted_data.get('summary', 'No summary available') if story.extracted_data else 'No summary available'
            }
            results.append(result)
            
            print(f"{i}. {story.customer_name}")
            print(f"   Industry: {story.industry or 'Unknown'}")
            print(f"   Published: {result['publish_date']}")
            print(f"   Summary: {result['summary'][:150]}...")
            print(f"   URL: {story.url}")
            print()
        
        return results
    
    def show_customer_details(self, customer_name: str):
        """Show detailed information about a specific customer"""
        print(f"\nCUSTOMER DETAILS: {customer_name}")
        print("="*60)
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT cs.*, s.name as source_name
                FROM customer_stories cs
                JOIN sources s ON cs.source_id = s.id
                WHERE LOWER(cs.customer_name) LIKE LOWER(%s)
                ORDER BY cs.publish_date DESC
            """, (f"%{customer_name}%",))
            
            stories = cursor.fetchall()
            
            if not stories:
                print(f"No stories found for customer: {customer_name}")
                return
            
            for story in stories:
                print(f"\nSource: {story['source_name']}")
                print(f"Title: {story['title'] or 'No title'}")
                print(f"Industry: {story['industry'] or 'Unknown'}")
                print(f"Company Size: {story['company_size'] or 'Unknown'}")
                print(f"Published: {story['publish_date'].strftime('%Y-%m-%d') if story['publish_date'] else 'Unknown'}")
                print(f"URL: {story['url']}")
                
                if story['extracted_data']:
                    extracted = story['extracted_data']
                    print(f"Summary: {extracted.get('summary', 'No summary')}")
                    print(f"Technologies: {', '.join(extracted.get('technologies_used', []))}")
                    print(f"Use Cases: {', '.join(extracted.get('use_cases', []))}")
                    
                    business_outcomes = extracted.get('business_outcomes', [])
                    if business_outcomes:
                        print("Business Outcomes:")
                        for outcome in business_outcomes:
                            print(f"  - {outcome.get('description', 'No description')}")
                
                print("-" * 50)
    
    def show_technology_usage(self, technology: str = None):
        """Show technology usage across stories"""
        if technology:
            print(f"\nSTORIES USING TECHNOLOGY: {technology}")
            print("="*60)
            
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT customer_name, industry, extracted_data->'technologies_used' as technologies, url
                    FROM customer_stories
                    WHERE extracted_data->'technologies_used' @> %s
                    ORDER BY customer_name
                """, (json.dumps([technology]),))
                
                stories = cursor.fetchall()
                
                for story in stories:
                    print(f"• {story['customer_name']} ({story['industry'] or 'Unknown industry'})")
                    print(f"  Technologies: {', '.join(story['technologies'])}")
                    print(f"  URL: {story['url']}")
                    print()
        else:
            print("\nTECHNOLOGY USAGE SUMMARY")
            print("="*60)
            
            # Get all technologies mentioned
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT jsonb_array_elements_text(extracted_data->'technologies_used') as technology,
                           COUNT(*) as usage_count
                    FROM customer_stories
                    WHERE extracted_data->'technologies_used' IS NOT NULL
                    GROUP BY technology
                    ORDER BY usage_count DESC
                    LIMIT 15
                """)
                
                print("Top Technologies Mentioned:")
                print("-" * 40)
                for row in cursor.fetchall():
                    print(f"{row['technology']:<30}: {row['usage_count']:>3} stories")
    
    def show_business_outcomes(self):
        """Show summary of business outcomes"""
        print("\nBUSINESS OUTCOMES SUMMARY")
        print("="*60)
        
        with self.db.get_cursor() as cursor:
            # Get outcome types
            cursor.execute("""
                SELECT 
                    jsonb_array_elements(extracted_data->'business_outcomes')->>'type' as outcome_type,
                    COUNT(*) as count
                FROM customer_stories
                WHERE extracted_data->'business_outcomes' IS NOT NULL
                GROUP BY outcome_type
                ORDER BY count DESC
            """)
            
            print("Outcome Types:")
            print("-" * 40)
            for row in cursor.fetchall():
                print(f"{row['outcome_type']:<25}: {row['count']:>3} mentions")
            
            # Show specific outcomes with values
            cursor.execute("""
                SELECT 
                    customer_name,
                    jsonb_array_elements(extracted_data->'business_outcomes') as outcome
                FROM customer_stories
                WHERE extracted_data->'business_outcomes' IS NOT NULL
                LIMIT 10
            """)
            
            print("\nExample Outcomes:")
            print("-" * 40)
            for row in cursor.fetchall():
                outcome = row['outcome']
                description = outcome.get('description', 'No description')
                print(f"• {row['customer_name']}: {description}")
    
    def run_deduplication_analysis(self):
        """Run and display deduplication analysis"""
        print("\nRUNNING DEDUPLICATION ANALYSIS")
        print("="*60)
        
        results = self.dedup.run_full_deduplication_analysis()
        
        # Show per-source duplicates
        print("\nPER-SOURCE DUPLICATES:")
        print("-" * 40)
        total_duplicates = 0
        for source_id, duplicates in results['per_source_duplicates'].items():
            source_name = self.dedup._get_source_name_by_id(source_id)
            print(f"{source_name}: {len(duplicates)} duplicate pairs found")
            total_duplicates += len(duplicates)
            
            for dup in duplicates[:3]:  # Show first 3 examples
                print(f"  • {dup['canonical_story'].customer_name} vs {dup['duplicate_story'].customer_name}")
                print(f"    Similarity: {dup['similarity_score']:.2f}, Reason: {dup['duplicate_reason']}")
        
        if total_duplicates == 0:
            print("No per-source duplicates found.")
        
        # Show cross-source customers
        print(f"\nCROSS-SOURCE CUSTOMERS:")
        print("-" * 40)
        cross_source = results['cross_source_customers']
        
        if cross_source:
            print(f"Found {len(cross_source)} customers across multiple sources:")
            for customer in cross_source[:10]:  # Show first 10
                print(f"• {customer['normalized_name']}")
                print(f"  Sources: {', '.join(customer['source_names'])}")
                print(f"  Total stories: {customer['total_stories']}")
        else:
            print("No customers found across multiple sources.")
        
        # Customer profiles
        profiles_created = len(results['customer_profiles_created'])
        print(f"\nCUSTOMER PROFILES: {profiles_created} profiles created/updated")
    
    def interactive_mode(self):
        """Run interactive query mode"""
        print("\n" + "="*60)
        print("AI CUSTOMER STORIES - INTERACTIVE QUERY INTERFACE")
        print("="*60)
        print("Commands:")
        print("  stats         - Show database summary")
        print("  search <term> - Search stories")  
        print("  customer <name> - Show customer details")
        print("  tech [name]   - Show technology usage")
        print("  outcomes      - Show business outcomes")
        print("  dedup         - Run deduplication analysis")
        print("  help          - Show this help")
        print("  quit          - Exit")
        print()
        
        while True:
            try:
                command = input("Query> ").strip().lower()
                
                if command == 'quit' or command == 'exit':
                    break
                elif command == 'stats':
                    self.show_summary_stats()
                elif command.startswith('search '):
                    query = command[7:].strip()
                    if query:
                        self.search_stories(query)
                    else:
                        print("Please provide a search term.")
                elif command.startswith('customer '):
                    customer = command[9:].strip()
                    if customer:
                        self.show_customer_details(customer)
                    else:
                        print("Please provide a customer name.")
                elif command == 'tech':
                    self.show_technology_usage()
                elif command.startswith('tech '):
                    tech = command[5:].strip()
                    self.show_technology_usage(tech)
                elif command == 'outcomes':
                    self.show_business_outcomes()
                elif command == 'dedup':
                    self.run_deduplication_analysis()
                elif command == 'help':
                    print("\nAvailable commands:")
                    print("  stats         - Database summary statistics")
                    print("  search <term> - Full-text search for stories")
                    print("  customer <name> - Detailed customer information")
                    print("  tech [name]   - Technology usage (all or specific)")
                    print("  outcomes      - Business outcomes summary")
                    print("  dedup         - Run deduplication analysis")
                    print("  quit          - Exit interface")
                elif command:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main entry point"""
    interface = QueryInterface()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'stats':
            interface.show_summary_stats()
        elif command == 'search' and len(sys.argv) > 2:
            query = ' '.join(sys.argv[2:])
            interface.search_stories(query)
        elif command == 'dedup':
            interface.run_deduplication_analysis()
        else:
            print("Usage: python query_interface.py [stats|search <term>|dedup]")
            print("Or run without arguments for interactive mode")
    else:
        interface.interactive_mode()

if __name__ == "__main__":
    main()