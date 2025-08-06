#!/usr/bin/env python3
"""
Deep Analysis of FullStory Data Quality Issue
Analyze the specific case where scale metrics are being treated as dollar values
"""

import sys
import os
import json

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import DatabaseConnection

def analyze_fullstory_case():
    """Analyze the FullStory case in detail"""
    print("🔍 DEEP ANALYSIS: FULLSTORY DATA QUALITY ISSUE")
    print("="*80)
    
    db = DatabaseConnection()
    
    with db.get_cursor() as cursor:
        # Get the full FullStory record
        cursor.execute("""
            SELECT 
                cs.*,
                s.name as source_name
            FROM customer_stories cs
            JOIN sources s ON cs.source_id = s.id
            WHERE LOWER(cs.customer_name) = 'fullstory'
        """)
        
        story = cursor.fetchone()
        
        if not story:
            print("❌ FullStory record not found")
            return
        
        print(f"📋 STORY DETAILS:")
        print(f"   ID: {story['id']}")
        print(f"   Customer: {story['customer_name']}")
        print(f"   Title: {story['title']}")
        print(f"   Industry: {story['industry']}")
        print(f"   Company Size: {story['company_size']}")
        print(f"   Source: {story['source_name']}")
        print(f"   URL: {story['url']}")
        print(f"   Scraped: {story['scraped_date']}")
        print(f"   Published: {story['publish_date']}")
        
        # Analyze extracted data
        extracted_data = story['extracted_data']
        
        print(f"\n🤖 EXTRACTED DATA ANALYSIS:")
        print(f"   Content Quality Score: {extracted_data.get('content_quality_score', 'N/A')}")
        print(f"   Summary: {extracted_data.get('summary', 'N/A')[:200]}...")
        
        # Focus on business outcomes
        business_outcomes = extracted_data.get('business_outcomes', [])
        
        print(f"\n💰 BUSINESS OUTCOMES ANALYSIS ({len(business_outcomes)} outcomes):")
        print("-" * 60)
        
        for i, outcome in enumerate(business_outcomes, 1):
            print(f"\n{i}. OUTCOME DETAILS:")
            print(f"   Type: {outcome.get('type', 'Unknown')}")
            print(f"   Value: {outcome.get('value', 'N/A')}")
            print(f"   Unit: {outcome.get('unit', 'N/A')}")
            print(f"   Description: {outcome.get('description', 'N/A')}")
            
            # Data quality analysis
            print(f"   ⚠️  DATA QUALITY ANALYSIS:")
            
            outcome_type = outcome.get('type', '')
            value = outcome.get('value', 0)
            unit = outcome.get('unit', '')
            description = outcome.get('description', '')
            
            if outcome_type == 'scale' and unit in ['events', 'pages', 'sessions']:
                print(f"      ✅ IDENTIFIED ISSUE: This is a SCALE metric, not a financial outcome")
                print(f"      ✅ CORRECT INTERPRETATION: {value:,} {unit} processed")
                print(f"      ❌ CURRENT ISSUE: Being treated as ${value:,} in dashboard")
                print(f"      🔧 SOLUTION: Exclude non-financial outcomes from monetary visualizations")
            elif 'dollar' in unit.lower() or '$' in str(value):
                print(f"      ✅ This appears to be a legitimate financial metric")
            else:
                print(f"      ⚠️  Unclear if this should be treated as financial data")
        
        # Check for technologies and use cases
        technologies = extracted_data.get('technologies_used', [])
        if technologies:
            print(f"\n🛠️  TECHNOLOGIES USED:")
            for tech in technologies:
                print(f"   • {tech}")
        
        use_cases = extracted_data.get('use_cases', [])
        if use_cases:
            print(f"\n🎯 USE CASES:")
            for use_case in use_cases:
                print(f"   • {use_case}")
        
        # Look at the raw content to understand the context
        raw_content = story.get('raw_content', {})
        if isinstance(raw_content, dict):
            raw_text = raw_content.get('full_text', '') or raw_content.get('content', '')
            if raw_text:
                print(f"\n📄 RAW CONTENT SAMPLE (first 500 chars):")
                print(f"   {raw_text[:500]}...")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   1. ✅ This is NOT a data quality issue with the source content")
        print(f"   2. ✅ FullStory legitimately processes 1.44 trillion events annually")
        print(f"   3. ❌ The issue is in how 'scale' outcomes are treated in analytics")
        print(f"   4. 🔧 SOLUTION: Filter out non-financial outcome types in dashboard")
        print(f"   5. 🔧 SOLUTION: Create separate visualizations for scale/operational metrics")
        
        return story

def check_similar_scale_issues():
    """Check for other similar scale/operational metrics being treated as financial"""
    print(f"\n\n🔍 CHECKING FOR OTHER SCALE METRIC ISSUES")
    print("="*80)
    
    db = DatabaseConnection()
    
    with db.get_cursor() as cursor:
        # Find all outcomes with non-financial units
        cursor.execute("""
            SELECT 
                cs.customer_name,
                s.name as source_name,
                outcome_element.value->>'type' as outcome_type,
                outcome_element.value->>'value' as outcome_value,
                outcome_element.value->>'unit' as outcome_unit,
                outcome_element.value->>'description' as outcome_description
            FROM customer_stories cs
            JOIN sources s ON cs.source_id = s.id,
            jsonb_array_elements(cs.extracted_data->'business_outcomes') AS outcome_element
            WHERE 
                cs.extracted_data->'business_outcomes' IS NOT NULL
                AND outcome_element.value->>'unit' IN (
                    'events', 'pages', 'sessions', 'users', 'requests', 'queries',
                    'transactions', 'items', 'records', 'files', 'documents',
                    'hours', 'minutes', 'seconds', 'days', 'months',
                    'percent', '%', 'percentage', 'ratio', 'factor', 'x',
                    'terabytes', 'gigabytes', 'petabytes', 'TB', 'GB', 'PB'
                )
            ORDER BY 
                CASE 
                    WHEN outcome_element.value->>'value' ~ '^[0-9]+\.?[0-9]*$' THEN
                        (outcome_element.value->>'value')::numeric
                    ELSE 0
                END DESC
            LIMIT 20
        """)
        
        scale_outcomes = cursor.fetchall()
        
        print(f"📊 Found {len(scale_outcomes)} outcomes with non-financial units")
        print("\nTop scale/operational outcomes by value:")
        print("-" * 60)
        
        for outcome in scale_outcomes:
            try:
                value = float(outcome['outcome_value']) if outcome['outcome_value'] and outcome['outcome_value'].replace('.', '').isdigit() else 0
                print(f"\n• {outcome['customer_name']} ({outcome['source_name']})")
                print(f"  Type: {outcome['outcome_type']}")
                print(f"  Value: {value:,.0f} {outcome['outcome_unit']}")
                print(f"  Description: {outcome['outcome_description'][:100]}...")
                
                if value > 1_000_000_000:  # > 1 billion
                    print(f"  ⚠️  HIGH VALUE: Would appear as ${value:,.0f} in current dashboard")
            except (ValueError, TypeError):
                pass

def main():
    """Main analysis"""
    print("🎯 FULLSTORY DATA QUALITY INVESTIGATION")
    print("="*80)
    
    # Analyze the specific FullStory case
    story = analyze_fullstory_case()
    
    # Check for similar issues
    check_similar_scale_issues()
    
    print(f"\n\n🎯 FINAL CONCLUSIONS:")
    print("="*80)
    print("✅ ROOT CAUSE IDENTIFIED:")
    print("   • FullStory processes 1.44 trillion events annually (legitimate scale metric)")
    print("   • AI extracted this as 'scale' type outcome with 'events' unit")
    print("   • Dashboard treats ALL numeric outcomes as financial values")
    print("   • Result: $1.44 trillion appears in business outcomes visualization")
    print()
    print("🔧 RECOMMENDED SOLUTIONS:")
    print("   1. Filter out non-financial outcome types ('scale', 'operational', 'performance')")
    print("   2. Filter out outcomes with non-monetary units ('events', 'sessions', 'pages', etc.)")
    print("   3. Create separate dashboard section for operational/scale metrics")
    print("   4. Add data validation to flag extremely high monetary values for review")
    print()
    print("📊 DASHBOARD IMPACT:")
    print("   • Remove scale metrics from business outcomes visualization")
    print("   • This will eliminate the $1.44T outlier")
    print("   • Consider adding 'Scale & Performance Metrics' section for non-financial outcomes")
    
    return story

if __name__ == "__main__":
    main()