#!/usr/bin/env python3
"""
Business Outcomes Filtering - Fix for Non-Financial Metrics in Dashboard
Create filtering logic to separate financial from operational/scale metrics
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import DatabaseConnection

def get_financial_vs_nonfinancial_breakdown():
    """Analyze current business outcomes and categorize as financial vs non-financial"""
    print("🔍 ANALYZING BUSINESS OUTCOMES: FINANCIAL vs NON-FINANCIAL")
    print("="*80)
    
    db = DatabaseConnection()
    
    # Define non-financial outcome types and units
    NON_FINANCIAL_TYPES = {
        'scale', 'operational', 'performance', 'user_reach', 'user_adoption', 
        'user_growth', 'engagement', 'capacity', 'throughput', 'volume'
    }
    
    NON_FINANCIAL_UNITS = {
        'events', 'pages', 'sessions', 'users', 'requests', 'queries',
        'transactions', 'items', 'records', 'files', 'documents',
        'hours', 'minutes', 'seconds', 'days', 'months', 'years',
        'percent', '%', 'percentage', 'ratio', 'factor', 'x', 'times',
        'terabytes', 'gigabytes', 'petabytes', 'megabytes', 'TB', 'GB', 'PB', 'MB',
        'clicks', 'views', 'impressions', 'downloads', 'uploads',
        'connections', 'visits', 'pageviews'
    }
    
    # Financial indicators
    FINANCIAL_UNITS = {
        'dollars', 'dollar', 'usd', '$', 'revenue', 'cost', 'savings', 'profit',
        'million', 'billion', 'thousand', 'k', 'm', 'b'
    }
    
    FINANCIAL_TYPES = {
        'cost_reduction', 'cost_savings', 'revenue_increase', 'profit_increase',
        'savings', 'revenue', 'cost_avoidance', 'roi', 'financial_benefit'
    }
    
    with db.get_cursor() as cursor:
        # Get all business outcomes with details
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
                AND outcome_element.value->>'value' IS NOT NULL
                AND outcome_element.value->>'value' != ''
        """)
        
        outcomes = cursor.fetchall()
        
        financial_outcomes = []
        nonfinancial_outcomes = []
        unclear_outcomes = []
        
        for outcome in outcomes:
            outcome_type = (outcome['outcome_type'] or '').lower()
            outcome_unit = (outcome['outcome_unit'] or '').lower()
            outcome_desc = (outcome['outcome_description'] or '').lower()
            outcome_value = outcome['outcome_value']
            
            # Categorize outcome
            is_financial = False
            is_nonfinancial = False
            
            # Check type first
            if outcome_type in NON_FINANCIAL_TYPES:
                is_nonfinancial = True
            elif outcome_type in FINANCIAL_TYPES:
                is_financial = True
            
            # Check unit
            if outcome_unit in NON_FINANCIAL_UNITS:
                is_nonfinancial = True
            elif outcome_unit in FINANCIAL_UNITS:
                is_financial = True
            elif '$' in str(outcome_value) or 'dollar' in outcome_desc:
                is_financial = True
            
            # Categorize
            if is_nonfinancial and not is_financial:
                nonfinancial_outcomes.append(outcome)
            elif is_financial and not is_nonfinancial:
                financial_outcomes.append(outcome)
            else:
                unclear_outcomes.append(outcome)
        
        # Report results
        print(f"📊 OUTCOME CLASSIFICATION RESULTS:")
        print(f"   Total outcomes analyzed: {len(outcomes)}")
        print(f"   ✅ Financial outcomes: {len(financial_outcomes)}")
        print(f"   📊 Non-financial (operational) outcomes: {len(nonfinancial_outcomes)}")
        print(f"   ❓ Unclear/mixed outcomes: {len(unclear_outcomes)}")
        
        # Show problematic non-financial outcomes with high values
        print(f"\n⚠️  HIGH-VALUE NON-FINANCIAL OUTCOMES (causing dashboard issues):")
        print("-" * 60)
        
        high_value_nonfinancial = []
        for outcome in nonfinancial_outcomes:
            try:
                value = float(outcome['outcome_value']) if outcome['outcome_value'] and str(outcome['outcome_value']).replace('.', '').replace('-', '').isdigit() else 0
                if value > 100_000_000:  # > 100M
                    high_value_nonfinancial.append((outcome, value))
            except:
                pass
        
        # Sort by value descending
        high_value_nonfinancial.sort(key=lambda x: x[1], reverse=True)
        
        for outcome, value in high_value_nonfinancial[:10]:
            print(f"• {outcome['customer_name']} ({outcome['source_name']})")
            print(f"  Type: {outcome['outcome_type']}")
            print(f"  Value: {value:,.0f} {outcome['outcome_unit']}")
            print(f"  ❌ Dashboard shows: ${value:,.0f}")
            print(f"  ✅ Should show: {value:,.0f} {outcome['outcome_unit']}")
            print()
        
        return {
            'total': len(outcomes),
            'financial': financial_outcomes,
            'nonfinancial': nonfinancial_outcomes,
            'unclear': unclear_outcomes,
            'high_value_nonfinancial': high_value_nonfinancial
        }

def create_filtering_sql_functions():
    """Create SQL functions that can be used in the dashboard to filter outcomes"""
    print(f"\n🔧 RECOMMENDED FILTERING LOGIC FOR DASHBOARD:")
    print("="*60)
    
    print("For Analytics Dashboard - Business Outcomes visualization:")
    print()
    print("-- Filter to only include financial business outcomes")
    print("WHERE cs.extracted_data->'business_outcomes' IS NOT NULL")
    print("  AND (")
    print("    -- Include outcomes with financial types")
    print("    outcome_element->>'type' IN (")
    print("      'cost_reduction', 'cost_savings', 'revenue_increase', 'profit_increase',")
    print("      'savings', 'revenue', 'cost_avoidance', 'roi', 'financial_benefit'")
    print("    )")
    print("    OR")
    print("    -- Include outcomes with financial units")
    print("    outcome_element->>'unit' IN (")
    print("      'dollars', 'dollar', 'usd', '$', 'million', 'billion', 'thousand'")
    print("    )")
    print("    OR")
    print("    -- Include outcomes with dollar signs in value")
    print("    outcome_element->>'value' LIKE '%$%'")
    print("  )")
    print("  AND")
    print("  -- Exclude clearly non-financial outcomes")
    print("  outcome_element->>'type' NOT IN (")
    print("    'scale', 'operational', 'performance', 'user_reach', 'user_adoption',")
    print("    'user_growth', 'engagement', 'capacity', 'throughput', 'volume'")
    print("  )")
    print("  AND")
    print("  outcome_element->>'unit' NOT IN (")
    print("    'events', 'pages', 'sessions', 'users', 'requests', 'queries',")
    print("    'files', 'documents', 'hours', 'minutes', 'percent', '%'")
    print("  );")
    
    print(f"\n📊 SEPARATE VISUALIZATION FOR OPERATIONAL METRICS:")
    print("Consider creating a new dashboard section: 'Scale & Performance Metrics'")
    print("This would show non-financial outcomes like:")
    print("  • Events processed")
    print("  • Users reached")
    print("  • Time saved (hours)")
    print("  • Data processed")
    print("  • Performance improvements")

def main():
    """Main analysis and recommendations"""
    print("🎯 BUSINESS OUTCOMES FILTERING ANALYSIS")
    print("="*80)
    
    # Analyze current data
    results = get_financial_vs_nonfinancial_breakdown()
    
    # Create filtering recommendations
    create_filtering_sql_functions()
    
    print(f"\n🎯 EXECUTIVE SUMMARY:")
    print("="*80)
    print("✅ ROOT CAUSE: FullStory's 1.44 trillion events processed appears as $1.44T")
    print("✅ SCOPE: 20+ non-financial outcomes with high values affecting dashboard")
    print("✅ SOLUTION: Implement filtering to separate financial vs operational metrics")
    print()
    print("🔧 IMMEDIATE ACTIONS NEEDED:")
    print("   1. Update dashboard.py to filter out non-financial outcomes")
    print("   2. Add separate section for operational/scale metrics")
    print("   3. Apply filtering to any business outcomes visualizations")
    print()
    print("📊 EXPECTED IMPACT:")
    print("   • Eliminates $1.44T outlier from business outcomes")
    print("   • Provides more realistic financial outcome distributions")
    print("   • Separates operational metrics for appropriate visualization")

if __name__ == "__main__":
    main()