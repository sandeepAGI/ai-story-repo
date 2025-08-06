#!/usr/bin/env python3
"""
Investigate Business Outcomes with Values > $500 Billion
Find and analyze stories with extremely high business outcome values
"""

import sys
import os
import json
from decimal import Decimal

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations

class HighValueOutcomeInvestigator:
    def __init__(self):
        self.db = DatabaseConnection()
        self.db_ops = DatabaseOperations(self.db)
        
    def find_high_value_outcomes(self, min_value_billion=500):
        """Find business outcomes with values greater than specified billion threshold"""
        print(f"\n🔍 SEARCHING FOR BUSINESS OUTCOMES > ${min_value_billion} BILLION")
        print("="*80)
        
        min_value = min_value_billion * 1_000_000_000  # Convert to actual value
        
        with self.db.get_cursor() as cursor:
            # Query to find stories with high-value business outcomes
            cursor.execute("""
                SELECT 
                    cs.id,
                    cs.customer_name,
                    cs.title,
                    cs.industry,
                    cs.company_size,
                    cs.url,
                    cs.publish_date,
                    s.name as source_name,
                    outcome_element.value as outcome
                FROM customer_stories cs
                JOIN sources s ON cs.source_id = s.id,
                jsonb_array_elements(cs.extracted_data->'business_outcomes') AS outcome_element
                WHERE 
                    cs.extracted_data->'business_outcomes' IS NOT NULL
                    AND (
                        -- Check for numeric values in different possible formats
                        (outcome_element->>'value' ~ '^[0-9]+\.?[0-9]*$' 
                         AND (outcome_element->>'value')::numeric >= %s)
                        OR
                        (outcome_element->>'value' ~ '^[0-9]+\.?[0-9]*[BMbmKk]?$' 
                         AND CASE 
                            WHEN outcome_element->>'value' ~* 'B$|billion' THEN 
                                regexp_replace(outcome_element->>'value', '[^0-9.]', '', 'g')::numeric * 1000000000 >= %s
                            WHEN outcome_element->>'value' ~* 'M$|million' THEN 
                                regexp_replace(outcome_element->>'value', '[^0-9.]', '', 'g')::numeric * 1000000 >= %s
                            WHEN outcome_element->>'value' ~* 'K$|thousand' THEN 
                                regexp_replace(outcome_element->>'value', '[^0-9.]', '', 'g')::numeric * 1000 >= %s
                            ELSE 
                                regexp_replace(outcome_element->>'value', '[^0-9.]', '', 'g')::numeric >= %s
                         END)
                    )
                ORDER BY cs.customer_name
            """, (min_value, min_value, min_value, min_value, min_value))
            
            high_value_stories = cursor.fetchall()
            
            if not high_value_stories:
                print(f"❌ No business outcomes found with values > ${min_value_billion:,} billion")
                return []
            
            print(f"📊 Found {len(high_value_stories)} stories with high-value outcomes")
            print("\n" + "="*80)
            
            results = []
            for story in high_value_stories:
                result = self._analyze_story_outcome(story)
                results.append(result)
                self._print_story_details(result)
            
            return results
    
    def _analyze_story_outcome(self, story_row):
        """Analyze a specific story's business outcomes in detail"""
        with self.db.get_cursor() as cursor:
            # Get full extracted data for this story
            cursor.execute("""
                SELECT extracted_data, raw_content
                FROM customer_stories 
                WHERE id = %s
            """, (story_row['id'],))
            
            full_story = cursor.fetchone()
            
            extracted_data = full_story['extracted_data'] if full_story else {}
            business_outcomes = extracted_data.get('business_outcomes', [])
            
            # Analyze each outcome
            analyzed_outcomes = []
            for outcome in business_outcomes:
                outcome_analysis = self._parse_outcome_value(outcome)
                analyzed_outcomes.append(outcome_analysis)
            
            return {
                'story_id': story_row['id'],
                'customer_name': story_row['customer_name'],
                'title': story_row['title'],
                'industry': story_row['industry'],
                'company_size': story_row['company_size'],
                'source_name': story_row['source_name'],
                'url': story_row['url'],
                'publish_date': story_row['publish_date'],
                'business_outcomes': analyzed_outcomes,
                'summary': extracted_data.get('summary', ''),
                'content_quality_score': extracted_data.get('content_quality_score', 0)
            }
    
    def _parse_outcome_value(self, outcome):
        """Parse and analyze a business outcome value"""
        if not isinstance(outcome, dict):
            return {'raw_outcome': outcome, 'parsed_value': None, 'analysis': 'Not a valid outcome object'}
        
        outcome_type = outcome.get('type', 'unknown')
        value = outcome.get('value', '')
        unit = outcome.get('unit', '')
        description = outcome.get('description', '')
        
        analysis = {
            'raw_outcome': outcome,
            'type': outcome_type,
            'raw_value': value,
            'unit': unit,
            'description': description,
            'parsed_value': None,
            'value_in_dollars': None,
            'analysis': '',
            'data_quality_issues': []
        }
        
        # Try to parse the value
        try:
            if isinstance(value, (int, float)):
                parsed_value = float(value)
                analysis['parsed_value'] = parsed_value
                
                # Determine actual dollar value based on unit
                if unit and ('dollar' in unit.lower() or '$' in unit):
                    analysis['value_in_dollars'] = parsed_value
                elif unit and ('billion' in unit.lower() or 'b' == unit.lower()):
                    analysis['value_in_dollars'] = parsed_value * 1_000_000_000
                elif unit and ('million' in unit.lower() or 'm' == unit.lower()):
                    analysis['value_in_dollars'] = parsed_value * 1_000_000
                elif unit and ('thousand' in unit.lower() or 'k' == unit.lower()):
                    analysis['value_in_dollars'] = parsed_value * 1_000
                else:
                    analysis['value_in_dollars'] = parsed_value
                    
            elif isinstance(value, str):
                # Try to extract numeric value from string
                import re
                numeric_match = re.search(r'(\d+\.?\d*)', str(value))
                if numeric_match:
                    parsed_value = float(numeric_match.group(1))
                    analysis['parsed_value'] = parsed_value
                    
                    # Check for multiplier in the value string
                    value_str = str(value).lower()
                    if 'billion' in value_str or value_str.endswith('b'):
                        analysis['value_in_dollars'] = parsed_value * 1_000_000_000
                    elif 'million' in value_str or value_str.endswith('m'):
                        analysis['value_in_dollars'] = parsed_value * 1_000_000
                    elif 'thousand' in value_str or value_str.endswith('k'):
                        analysis['value_in_dollars'] = parsed_value * 1_000
                    else:
                        analysis['value_in_dollars'] = parsed_value
                        
        except (ValueError, TypeError) as e:
            analysis['data_quality_issues'].append(f"Value parsing error: {e}")
        
        # Data quality analysis
        if analysis['value_in_dollars'] and analysis['value_in_dollars'] > 500_000_000_000:
            analysis['data_quality_issues'].append("EXTREMELY HIGH VALUE: Potential data quality issue")
            
            # Check if this could be a unit conversion error
            if analysis['value_in_dollars'] > 1_000_000_000_000:
                analysis['data_quality_issues'].append("Value > $1 trillion: Likely unit conversion error")
            
            # Check for context clues
            desc_lower = description.lower() if description else ''
            if 'revenue' in desc_lower and analysis['value_in_dollars'] > 100_000_000_000:
                analysis['data_quality_issues'].append("Revenue > $100B seems unlikely for single customer")
            
        return analysis
    
    def _print_story_details(self, result):
        """Print detailed information about a high-value story"""
        print(f"\n🏢 CUSTOMER: {result['customer_name']}")
        print(f"📰 TITLE: {result['title'] or 'No title'}")
        print(f"🏭 INDUSTRY: {result['industry'] or 'Unknown'}")
        print(f"📈 COMPANY SIZE: {result['company_size'] or 'Unknown'}")
        print(f"📅 PUBLISHED: {result['publish_date'] or 'Unknown'}")
        print(f"🔗 SOURCE: {result['source_name']}")
        print(f"🌐 URL: {result['url']}")
        print(f"⭐ QUALITY SCORE: {result['content_quality_score']}")
        
        if result['summary']:
            print(f"📝 SUMMARY: {result['summary'][:200]}...")
        
        print(f"\n💰 BUSINESS OUTCOMES ({len(result['business_outcomes'])} found):")
        print("-" * 60)
        
        for i, outcome in enumerate(result['business_outcomes'], 1):
            print(f"\n{i}. OUTCOME TYPE: {outcome['type']}")
            print(f"   RAW VALUE: {outcome['raw_value']}")
            print(f"   UNIT: {outcome['unit']}")
            print(f"   DESCRIPTION: {outcome['description']}")
            print(f"   PARSED VALUE: {outcome['parsed_value']}")
            
            if outcome['value_in_dollars']:
                print(f"   💵 DOLLAR VALUE: ${outcome['value_in_dollars']:,.0f}")
                if outcome['value_in_dollars'] > 1_000_000_000:
                    print(f"   💵 IN BILLIONS: ${outcome['value_in_dollars']/1_000_000_000:.2f}B")
            
            if outcome['data_quality_issues']:
                print(f"   ⚠️  DATA QUALITY ISSUES:")
                for issue in outcome['data_quality_issues']:
                    print(f"      • {issue}")
        
        print("\n" + "="*80)
    
    def search_all_outcomes_by_value_range(self, min_millions=100):
        """Search all outcomes above a certain threshold to understand the data distribution"""
        print(f"\n📊 ANALYZING ALL OUTCOMES > ${min_millions}M")
        print("="*80)
        
        min_value = min_millions * 1_000_000
        
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    cs.customer_name,
                    s.name as source_name,
                    outcome_element.value as outcome
                FROM customer_stories cs
                JOIN sources s ON cs.source_id = s.id,
                jsonb_array_elements(cs.extracted_data->'business_outcomes') AS outcome_element
                WHERE 
                    cs.extracted_data->'business_outcomes' IS NOT NULL
                    AND outcome_element->>'value' IS NOT NULL
                    AND outcome_element->>'value' != ''
                ORDER BY cs.customer_name
            """)
            
            all_outcomes = cursor.fetchall()
            
            print(f"Found {len(all_outcomes)} total business outcomes to analyze")
            
            high_value_count = 0
            extremely_high_count = 0
            value_distribution = {}
            
            for row in all_outcomes:
                outcome = row['outcome']
                analysis = self._parse_outcome_value(outcome)
                
                if analysis['value_in_dollars']:
                    value = analysis['value_in_dollars']
                    
                    # Categorize by value ranges
                    if value >= min_value:
                        high_value_count += 1
                        
                        if value >= 500_000_000_000:  # > $500B
                            extremely_high_count += 1
                            print(f"\n🚨 EXTREMELY HIGH VALUE FOUND:")
                            print(f"   Customer: {row['customer_name']}")
                            print(f"   Source: {row['source_name']}")
                            print(f"   Value: ${value:,.0f} (${value/1_000_000_000:.2f}B)")
                            print(f"   Raw data: {outcome}")
                            
                            if analysis['data_quality_issues']:
                                print(f"   Issues: {', '.join(analysis['data_quality_issues'])}")
                    
                    # Build distribution
                    if value < 1_000_000:  # < $1M
                        value_distribution['< $1M'] = value_distribution.get('< $1M', 0) + 1
                    elif value < 10_000_000:  # $1M - $10M
                        value_distribution['$1M - $10M'] = value_distribution.get('$1M - $10M', 0) + 1
                    elif value < 100_000_000:  # $10M - $100M
                        value_distribution['$10M - $100M'] = value_distribution.get('$10M - $100M', 0) + 1
                    elif value < 1_000_000_000:  # $100M - $1B
                        value_distribution['$100M - $1B'] = value_distribution.get('$100M - $1B', 0) + 1
                    elif value < 10_000_000_000:  # $1B - $10B
                        value_distribution['$1B - $10B'] = value_distribution.get('$1B - $10B', 0) + 1
                    elif value < 100_000_000_000:  # $10B - $100B
                        value_distribution['$10B - $100B'] = value_distribution.get('$10B - $100B', 0) + 1
                    else:  # > $100B
                        value_distribution['> $100B'] = value_distribution.get('> $100B', 0) + 1
            
            print(f"\n📈 VALUE DISTRIBUTION SUMMARY:")
            print("-" * 40)
            for range_label, count in sorted(value_distribution.items()):
                print(f"{range_label:<15}: {count:>3} outcomes")
            
            print(f"\n🎯 HIGH VALUE SUMMARY:")
            print(f"Total outcomes analyzed: {len(all_outcomes)}")
            print(f"Outcomes > ${min_millions}M: {high_value_count}")
            print(f"Outcomes > $500B: {extremely_high_count}")
            
            return {
                'total_outcomes': len(all_outcomes),
                'high_value_count': high_value_count,
                'extremely_high_count': extremely_high_count,
                'value_distribution': value_distribution
            }

def main():
    """Main execution"""
    investigator = HighValueOutcomeInvestigator()
    
    print("🎯 AI CUSTOMER STORIES: HIGH-VALUE BUSINESS OUTCOMES INVESTIGATION")
    print("="*80)
    
    # First, search for outcomes > $500B
    high_value_results = investigator.find_high_value_outcomes(min_value_billion=500)
    
    # Then analyze the broader distribution
    distribution_results = investigator.search_all_outcomes_by_value_range(min_millions=100)
    
    print(f"\n🎯 INVESTIGATION COMPLETE")
    print("="*80)
    
    if high_value_results:
        print(f"✅ Found {len(high_value_results)} stories with outcomes > $500B")
        print("📋 Recommendation: Review these outcomes for data quality issues")
        print("🔧 Consider implementing value validation/caps in data processing")
    else:
        print("❌ No outcomes > $500B found in database")
        print("✅ Data appears to be within reasonable ranges")
    
    return high_value_results

if __name__ == "__main__":
    try:
        results = main()
    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        sys.exit(1)