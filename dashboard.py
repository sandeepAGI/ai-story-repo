#!/usr/bin/env python3
"""
AI Customer Stories Dashboard
Streamlit-based web interface for exploring and analyzing AI customer stories
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys
import os
import numpy as np
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import io

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations, CustomerStory
from brand_styles import apply_brand_styling, BRAND_COLORS, PLOTLY_COLOR_SCHEMES, get_brand_color_discrete_map, get_plotly_theme

# Configure Streamlit page
st.set_page_config(
    page_title="AI Customer Stories Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_database_connection():
    """Initialize database connection with caching"""
    return DatabaseOperations()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_all_stories() -> pd.DataFrame:
    """Load all stories into a pandas DataFrame"""
    db_ops = get_database_connection()
    
    with db_ops.db.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                cs.*,
                s.name as source_name,
                EXTRACT(YEAR FROM cs.publish_date) as publish_year,
                EXTRACT(MONTH FROM cs.publish_date) as publish_month
            FROM customer_stories cs
            JOIN sources s ON cs.source_id = s.id
            ORDER BY cs.scraped_date DESC
        """)
        
        rows = cursor.fetchall()
        return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def get_source_stats() -> Dict:
    """Get summary statistics by source"""
    db_ops = get_database_connection()
    
    with db_ops.db.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                s.name,
                COUNT(cs.id) as story_count,
                MIN(cs.publish_date) as earliest_story,
                MAX(cs.publish_date) as latest_story,
                COUNT(CASE WHEN cs.publish_date_estimated = TRUE THEN 1 END) as estimated_dates,
                AVG(CASE 
                    WHEN cs.extracted_data->'content_quality_score' IS NOT NULL 
                    THEN (cs.extracted_data->>'content_quality_score')::float 
                    ELSE NULL 
                END) as avg_quality_score
            FROM sources s 
            LEFT JOIN customer_stories cs ON s.id = cs.source_id 
            GROUP BY s.name, s.id
            ORDER BY story_count DESC
        """)
        
        return {row['name']: dict(row) for row in cursor.fetchall()}

@st.cache_data(ttl=300)
def get_aileron_analytics() -> Dict:
    """Get Aileron framework analytics - only for Gen AI stories with complete Aileron data"""
    db_ops = get_database_connection()
    
    with db_ops.db.get_cursor() as cursor:
        # SuperPowers distribution
        cursor.execute("""
            SELECT 
                jsonb_array_elements_text(extracted_data->'gen_ai_superpowers') as superpower,
                COUNT(*) as count
            FROM customer_stories
            WHERE is_gen_ai = TRUE 
            AND extracted_data->'gen_ai_superpowers' IS NOT NULL
            GROUP BY superpower
            ORDER BY count DESC
        """)
        superpowers = {row['superpower']: row['count'] for row in cursor.fetchall()}
        
        # Business Impacts distribution
        cursor.execute("""
            SELECT 
                jsonb_array_elements_text(extracted_data->'business_impacts') as impact,
                COUNT(*) as count
            FROM customer_stories
            WHERE is_gen_ai = TRUE 
            AND extracted_data->'business_impacts' IS NOT NULL
            GROUP BY impact
            ORDER BY count DESC
        """)
        impacts = {row['impact']: row['count'] for row in cursor.fetchall()}
        
        # Adoption Enablers distribution
        cursor.execute("""
            SELECT 
                jsonb_array_elements_text(extracted_data->'adoption_enablers') as enabler,
                COUNT(*) as count
            FROM customer_stories
            WHERE is_gen_ai = TRUE 
            AND extracted_data->'adoption_enablers' IS NOT NULL
            GROUP BY enabler
            ORDER BY count DESC
        """)
        enablers = {row['enabler']: row['count'] for row in cursor.fetchall()}
        
        # Business Function distribution
        cursor.execute("""
            SELECT 
                extracted_data->>'business_function' as function,
                COUNT(*) as count
            FROM customer_stories
            WHERE is_gen_ai = TRUE 
            AND extracted_data->'business_function' IS NOT NULL
            GROUP BY function
            ORDER BY count DESC
        """)
        functions = {row['function']: row['count'] for row in cursor.fetchall() if row['function']}
        
        return {
            'superpowers': superpowers,
            'impacts': impacts,
            'enablers': enablers,
            'functions': functions
        }

def create_download_data(df: pd.DataFrame, format_type: str) -> bytes:
    """Create downloadable data in specified format"""
    if format_type == 'csv':
        return df.to_csv(index=False).encode('utf-8')
    elif format_type == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Stories')
        return output.getvalue()
    elif format_type == 'json':
        return df.to_json(orient='records', indent=2).encode('utf-8')

def main():
    """Main dashboard application"""
    
    # Apply brand styling
    apply_brand_styling()
    
    # Sidebar navigation
    st.sidebar.title("🤖 AI Stories Dashboard")
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["📊 Overview", "🔍 Story Explorer", "📈 Analytics", "🎯 Aileron Insights", "💾 Data Export"]
    )
    
    # Load data
    try:
        df = load_all_stories()
        source_stats = get_source_stats()
        aileron_data = get_aileron_analytics()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Please ensure your database is running and accessible.")
        return
    
    if page == "📊 Overview":
        show_overview(df, source_stats)
    elif page == "🔍 Story Explorer":
        show_story_explorer(df)
    elif page == "📈 Analytics":
        show_analytics(df, source_stats)
    elif page == "🎯 Aileron Insights":
        show_aileron_insights(df, aileron_data)
    elif page == "💾 Data Export":
        show_data_export(df)

def show_overview(df: pd.DataFrame, source_stats: Dict):
    """Display overview dashboard"""
    st.title("📊 AI Customer Stories - Overview")
    st.markdown("---")
    
    # Calculate Gen AI stories count using is_gen_ai boolean field
    gen_ai_count = len(df[df['is_gen_ai'] == True])
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Stories", len(df))
    
    with col2:
        st.metric("Gen AI Stories", gen_ai_count)
    
    with col3:
        st.metric("AI Providers", len(source_stats))
    
    with col4:
        industries = df['industry'].nunique()
        st.metric("Industries", industries)
    
    with col5:
        avg_quality = df['extracted_data'].apply(
            lambda x: x.get('content_quality_score', 0) if isinstance(x, dict) else 0
        ).mean()
        st.metric("Avg Quality Score", f"{avg_quality:.2f}")
    
    # Source distribution chart with Gen AI breakdown
    st.subheader("Stories by AI Provider")
    
    # Calculate Gen AI vs Non Gen AI breakdown by source
    source_breakdown = []
    for name, stats in source_stats.items():
        source_df_filtered = df[df['source_name'] == name]
        gen_ai_stories = len(source_df_filtered[source_df_filtered['is_gen_ai'] == True])
        non_gen_ai_stories = stats['story_count'] - gen_ai_stories
        
        # Add Gen AI stories
        if gen_ai_stories > 0:
            source_breakdown.append({
                'Source': name, 
                'Stories': gen_ai_stories, 
                'Type': 'Gen AI',
                'Avg Quality': stats['avg_quality_score'] or 0
            })
        
        # Add Non Gen AI stories
        if non_gen_ai_stories > 0:
            source_breakdown.append({
                'Source': name, 
                'Stories': non_gen_ai_stories, 
                'Type': 'Non Gen AI',
                'Avg Quality': stats['avg_quality_score'] or 0
            })
    
    source_df = pd.DataFrame(source_breakdown)
    
    if not source_df.empty:
        fig = px.bar(
            source_df, 
            x='Source', 
            y='Stories',
            color='Type',
            color_discrete_map=PLOTLY_COLOR_SCHEMES['gen_ai_colors'],
            title="Story Count by AI Provider (Gen AI vs Non Gen AI breakdown)"
        )
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
    else:
        st.info("No data available for source breakdown")
    
    # Recent activity - sorted by publish date
    st.subheader("Recent Stories")
    
    # Sort by publish_date (latest first), handle nulls
    df_sorted = df.copy()
    df_sorted['publish_date_sort'] = pd.to_datetime(df_sorted['publish_date'])
    df_sorted = df_sorted.sort_values('publish_date_sort', ascending=False, na_position='last')
    
    recent_df = df_sorted.head(10)[['customer_name', 'source_name', 'industry', 'publish_date', 'url']].copy()
    recent_df['publish_date'] = pd.to_datetime(recent_df['publish_date']).dt.strftime('%Y-%m-%d')
    
    # Add numbering starting from 1
    recent_df.reset_index(drop=True, inplace=True)
    recent_df.index = recent_df.index + 1
    recent_df.index.name = '#'
    
    # Display table using Streamlit's native dataframe function
    display_df = recent_df.copy()
    display_df['Link'] = display_df['url'].apply(lambda x: f"🔗 [View Story]({x})")
    display_columns = ['customer_name', 'source_name', 'industry', 'publish_date', 'Link']
    display_df = display_df[display_columns]
    
    # Rename columns for better display
    display_df.columns = ['Customer Name', 'AI Provider', 'Industry', 'Publish Date', 'Link']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Link": st.column_config.LinkColumn(
                "Link",
                help="Click to view the story",
                display_text="🔗 View Story"
            )
        },
        hide_index=False
    )

def show_story_explorer(df: pd.DataFrame):
    """Display story search and exploration interface"""
    st.title("🔍 Story Explorer")
    st.markdown("---")
    
    # Search and filters
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search stories", placeholder="Enter keywords...")
    
    with col2:
        source_filter = st.selectbox("Filter by Source", ["All"] + df['source_name'].unique().tolist())
    
    # Additional filters
    col3, col4, col5 = st.columns(3)
    
    with col3:
        industry_filter = st.selectbox("Industry", ["All"] + sorted(df['industry'].dropna().unique().tolist()))
    
    with col4:
        size_filter = st.selectbox("Company Size", ["All"] + sorted(df['company_size'].dropna().unique().tolist()))
    
    with col5:
        ai_type_filter = st.selectbox("AI Type", ["All", "Gen AI", "Non Gen AI"])
    
    # Apply filters
    filtered_df = df.copy()
    
    if source_filter != "All":
        filtered_df = filtered_df[filtered_df['source_name'] == source_filter]
    
    if industry_filter != "All":
        filtered_df = filtered_df[filtered_df['industry'] == industry_filter]
    
    if size_filter != "All":
        filtered_df = filtered_df[filtered_df['company_size'] == size_filter]
    
    if ai_type_filter == "Gen AI":
        filtered_df = filtered_df[filtered_df['is_gen_ai'] == True]
    elif ai_type_filter == "Non Gen AI":
        filtered_df = filtered_df[filtered_df['is_gen_ai'] == False]
    
    # Search functionality
    if search_term:
        search_mask = (
            filtered_df['customer_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['title'].str.contains(search_term, case=False, na=False) |
            filtered_df['industry'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    st.info(f"Found {len(filtered_df)} stories matching your criteria")
    
    # Display results
    for idx, row in filtered_df.iterrows():
        with st.expander(f"🏢 {row['customer_name']} ({row['source_name']})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Industry:** {row['industry'] or 'Unknown'}")
                st.write(f"**Company Size:** {row['company_size'] or 'Unknown'}")
                st.write(f"**Published:** {row['publish_date'] or 'Unknown'}")
                
                if isinstance(row['extracted_data'], dict):
                    summary = row['extracted_data'].get('summary', 'No summary available')
                    st.write(f"**Summary:** {summary}")
                    
                    technologies = row['extracted_data'].get('technologies_used', [])
                    if technologies:
                        st.write(f"**Technologies:** {', '.join(technologies)}")
                    
                    # Display business outcomes
                    business_outcomes = row['extracted_data'].get('business_outcomes', [])
                    if business_outcomes:
                        st.write("**Business Outcomes:**")
                        for outcome in business_outcomes:
                            if isinstance(outcome, dict):
                                outcome_type = outcome.get('type', 'Unknown')
                                value = outcome.get('value')
                                unit = outcome.get('unit', '')
                                description = outcome.get('description', '')
                                
                                if value and unit:
                                    outcome_text = f"• **{outcome_type.replace('_', ' ').title()}**: {value} {unit}"
                                else:
                                    outcome_text = f"• **{outcome_type.replace('_', ' ').title()}**"
                                
                                if description:
                                    outcome_text += f" - {description}"
                                
                                st.write(outcome_text)
            
            with col2:
                st.write(f"**URL:** [Link]({row['url']})")
                
                if isinstance(row['extracted_data'], dict):
                    quality_score = row['extracted_data'].get('content_quality_score', 0)
                    st.metric("Quality Score", f"{quality_score:.2f}")

def show_analytics(df: pd.DataFrame, source_stats: Dict):
    """Display analytics dashboard"""
    st.title("📈 Analytics Dashboard")
    
    # Gen AI Filter Toggle at the top
    st.markdown("### 🔬 Filter by AI Type")
    ai_filter = st.radio(
        "Show data for:",
        ["All Stories", "Gen AI Only", "Non Gen AI Only"],
        horizontal=True,
        help="Filter all charts and analysis on this page by AI type"
    )
    
    # Apply the filter to the dataframe
    if ai_filter == "Gen AI Only":
        df_filtered = df[df['is_gen_ai'] == True].copy()
        filter_suffix = " (Gen AI Only)"
    elif ai_filter == "Non Gen AI Only":
        df_filtered = df[df['is_gen_ai'] == False].copy()
        filter_suffix = " (Non Gen AI Only)"
    else:
        df_filtered = df.copy()
        filter_suffix = ""
    
    # Show current filter stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Stories", len(df_filtered), f"of {len(df)} total")
    with col2:
        if len(df_filtered) > 0:
            industries = df_filtered['industry'].nunique()
            st.metric("Industries", industries)
    with col3:
        if len(df_filtered) > 0:
            sources = df_filtered['source_name'].nunique()
            st.metric("AI Providers", sources)
    
    st.markdown("---")
    
    # Check if we have data after filtering
    if len(df_filtered) == 0:
        st.warning(f"No stories found for '{ai_filter}' filter. Please select a different filter.")
        return
    
    # Industry analysis
    st.subheader("Industry Distribution")
    industry_counts = df_filtered['industry'].value_counts().head(10)
    
    fig = px.pie(
        values=industry_counts.values,
        names=industry_counts.index,
        title=f"Top 10 Industries{filter_suffix}",
        color_discrete_sequence=PLOTLY_COLOR_SCHEMES['diverse_discrete']
    )
    fig.update_layout(get_plotly_theme()['layout'])
    st.plotly_chart(fig, use_container_width=True)
    
    # Company size and Use Case analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Company Size Distribution")
        size_counts = df_filtered['company_size'].value_counts()
        fig = px.bar(x=size_counts.index, y=size_counts.values, title=f"Stories by Company Size{filter_suffix}",
                    color=size_counts.values, color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues'])
        fig.update_layout(get_plotly_theme()['layout'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Use Case Categories")
        use_case_counts = df_filtered['use_case_category'].value_counts().head(8)
        fig = px.bar(x=use_case_counts.values, y=use_case_counts.index, 
                    orientation='h', title=f"Top AI Use Cases{filter_suffix}",
                    color=use_case_counts.values, color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues'])
        fig.update_layout(get_plotly_theme()['layout'])
        st.plotly_chart(fig, use_container_width=True)
    
    # Technology usage by source - Multiple alternatives
    st.subheader("Technology Usage Analysis")
    
    # Extract technologies with source attribution
    tech_source_data = []
    source_tech_counts = {}
    
    for idx, row in df_filtered.iterrows():
        if isinstance(row['extracted_data'], dict):
            techs = row['extracted_data'].get('technologies_used', [])
            source = row['source_name']
            
            # Initialize source if not exists
            if source not in source_tech_counts:
                source_tech_counts[source] = {}
            
            for tech in techs:
                tech_source_data.append({'Technology': tech, 'Source': source})
                # Count technologies per source
                source_tech_counts[source][tech] = source_tech_counts[source].get(tech, 0) + 1
    
    # Choose implementation based on data availability
    if tech_source_data:
        tech_df = pd.DataFrame(tech_source_data)
        
        # Alternative 1: Top Technologies by Each Source (Side-by-side)
        st.markdown("**Top Technologies by AI Provider**")
        
        col1, col2 = st.columns(2)
        sources = list(source_tech_counts.keys())
        
        # Show top 3 sources in first column, rest in second
        mid_point = len(sources) // 2 + len(sources) % 2
        
        with col1:
            for source in sources[:mid_point]:
                if source_tech_counts[source]:
                    top_techs = dict(sorted(source_tech_counts[source].items(), 
                                          key=lambda x: x[1], reverse=True)[:5])
                    
                    st.markdown(f"**{source}:**")
                    for tech, count in top_techs.items():
                        st.markdown(f"• {tech}: {count}")
                    st.markdown("")
        
        with col2:
            for source in sources[mid_point:]:
                if source_tech_counts[source]:
                    top_techs = dict(sorted(source_tech_counts[source].items(), 
                                          key=lambda x: x[1], reverse=True)[:5])
                    
                    st.markdown(f"**{source}:**")
                    for tech, count in top_techs.items():
                        st.markdown(f"• {tech}: {count}")
                    st.markdown("")
        
        # Alternative 2: Overall Top Technologies (Simple approach)
        st.markdown("**Overall Technology Usage**")
        overall_tech_counts = tech_df['Technology'].value_counts().head(15)
        
        fig = px.bar(
            x=overall_tech_counts.values,
            y=overall_tech_counts.index,
            orientation='h',
            title=f"Top 15 Technologies Mentioned{filter_suffix}",
            color=overall_tech_counts.values,
            color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues']
        )
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No technology data available in stories")
    
    # Business Outcomes Analysis by Use Case
    st.subheader("🎯 Business Outcomes by Use Case")
    
    # Extract business outcomes data with use case context
    use_case_outcomes = {}
    outcome_types_overall = {}
    quantitative_outcomes = []
    qualitative_outcomes = []
    
    for idx, row in df_filtered.iterrows():
        if isinstance(row['extracted_data'], dict):
            outcomes = row['extracted_data'].get('business_outcomes', [])
            use_case = row.get('use_case_category', 'Unknown')
            source = row['source_name']
            
            # Initialize use case if not exists
            if use_case not in use_case_outcomes:
                use_case_outcomes[use_case] = {'quantitative': [], 'qualitative': [], 'types': {}}
            
            for outcome in outcomes:
                if isinstance(outcome, dict):
                    outcome_type = outcome.get('type', 'Unknown')
                    value = outcome.get('value')
                    unit = outcome.get('unit', '')
                    description = outcome.get('description', '')
                    
                    # Track overall outcome types
                    outcome_types_overall[outcome_type] = outcome_types_overall.get(outcome_type, 0) + 1
                    
                    # Track by use case
                    use_case_outcomes[use_case]['types'][outcome_type] = use_case_outcomes[use_case]['types'].get(outcome_type, 0) + 1
                    
                    # Separate quantitative vs qualitative (filter out non-financial outcomes)
                    if (value and isinstance(value, (int, float)) and value > 0 and
                        # Filter out operational/scale metrics that aren't financial
                        outcome_type not in ['scale', 'operational', 'performance', 'user_reach', 'user_adoption', 
                                           'user_growth', 'engagement', 'capacity', 'throughput', 'volume'] and
                        unit not in ['events', 'pages', 'sessions', 'users', 'requests', 'queries', 
                                   'files', 'documents'] and
                        # Keep reasonable financial values (less than $1B for sanity)
                        value < 1000000000):
                        
                        quantitative_outcomes.append({
                            'Use_Case': use_case,
                            'Type': outcome_type.replace('_', ' ').title(),
                            'Value': value,
                            'Unit': unit,
                            'Source': source,
                            'Description': description
                        })
                        use_case_outcomes[use_case]['quantitative'].append(outcome)
                    else:
                        qualitative_outcomes.append({
                            'Use_Case': use_case,
                            'Type': outcome_type.replace('_', ' ').title(),
                            'Description': description,
                            'Source': source
                        })
                        use_case_outcomes[use_case]['qualitative'].append(outcome)
    
    # Top Use Cases with Outcomes
    st.markdown("**Top Use Cases by Story Count:**")
    top_use_cases = sorted([(k, len(v['quantitative']) + len(v['qualitative'])) 
                           for k, v in use_case_outcomes.items() 
                           if k != 'Unknown'], key=lambda x: x[1], reverse=True)[:8]
    
    cols = st.columns(4)
    for i, (use_case, count) in enumerate(top_use_cases):
        with cols[i % 4]:
            st.metric(use_case.replace('_', ' ').title(), f"{count} outcomes")
    
    # Top Financial Highlights
    st.subheader("💰 Top Financial Outcomes - Individual Highlights")
    
    if quantitative_outcomes:
        quant_df = pd.DataFrame(quantitative_outcomes)
        
        # Sort by value to get top individual achievements
        top_financial = quant_df.nlargest(8, 'Value').copy()
        
        if not top_financial.empty:
            # Add customer names by looking up from original df
            top_financial_enhanced = []
            for idx, row in top_financial.iterrows():
                # Find matching customer for this outcome
                matching_customer = "Unknown"
                for df_idx, df_row in df_filtered.iterrows():
                    if (isinstance(df_row['extracted_data'], dict) and 
                        df_row.get('use_case_category') == row['Use_Case'] and
                        df_row['source_name'] == row['Source']):
                        matching_customer = df_row.get('customer_name', 'Unknown')
                        break
                
                top_financial_enhanced.append({
                    'Customer': matching_customer,
                    'Use_Case': row['Use_Case'].replace('_', ' ').title(),
                    'Achievement': row['Type'],
                    'Value': row['Value'],
                    'Unit': row['Unit'],
                    'Description': row['Description'],
                    'AI_Provider': row['Source'],
                    'Formatted_Value': f"{row['Value']:,.0f}{'%' if row['Unit'] == 'percent' else ' ' + row['Unit']}"
                })
            
            highlights_df = pd.DataFrame(top_financial_enhanced)
            
            # Display as cards/highlights
            st.markdown("**🏆 Top Individual Financial Achievements:**")
            
            cols = st.columns(2)
            for i, (_, row) in enumerate(highlights_df.head(6).iterrows()):
                with cols[i % 2]:
                    with st.container():
                        st.markdown(f"""
                        **🏢 {row['Customer']}** ({row['AI_Provider']})
                        
                        **{row['Achievement']}**: {row['Formatted_Value']}
                        
                        *{row['Use_Case']}* | {row['Description'][:100]}{'...' if len(row['Description']) > 100 else ''}
                        
                        ---
                        """)
            
            # Network-style visualization of relationships
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔄 Use Case → Outcome Flow")
                # Show top outcomes for each major use case with percentages
                flow_data = []
                
                # Get top 5 use cases by total outcomes
                top_flow_cases = sorted([(k, sum(v['types'].values())) 
                                       for k, v in use_case_outcomes.items() 
                                       if k != 'Unknown'], key=lambda x: x[1], reverse=True)[:5]
                
                for use_case, total_outcomes in top_flow_cases:
                    case_data = use_case_outcomes[use_case]
                    # Get top 3 outcome types for this use case
                    top_case_outcomes = sorted(case_data['types'].items(), 
                                             key=lambda x: x[1], reverse=True)[:3]
                    
                    st.markdown(f"**📂 {use_case.replace('_', ' ').title()}:**")
                    
                    for outcome_type, count in top_case_outcomes:
                        # Calculate percentage within this use case
                        percentage = (count / total_outcomes) * 100
                        outcome_display = outcome_type.replace('_', ' ').title()
                        
                        # Create a visual progress bar effect
                        bar_width = int(percentage / 2)  # Scale down for display
                        bar_visual = "█" * bar_width + "░" * (50 - bar_width) if bar_width < 50 else "█" * 50
                        
                        st.markdown(f"  • **{outcome_display}**: {percentage:.0f}% ({count} stories)")
                        st.progress(percentage / 100)
                    
                    st.markdown("")  # Add spacing
            
            with col2:
                st.subheader("📊 Value Distribution")
                # Show distribution of financial outcome values
                value_ranges = []
                for _, row in highlights_df.iterrows():
                    value = row['Value']
                    if value < 10:
                        range_label = "< 10"
                    elif value < 50:
                        range_label = "10-50"
                    elif value < 100:
                        range_label = "50-100"
                    elif value < 500:
                        range_label = "100-500"
                    elif value < 1000:
                        range_label = "500-1K"
                    else:
                        range_label = "1K+"
                    
                    value_ranges.append({
                        'Range': range_label,
                        'Achievement': row['Achievement'],
                        'Value': value
                    })
                
                if value_ranges:
                    range_df = pd.DataFrame(value_ranges)
                    range_counts = range_df.groupby(['Range', 'Achievement']).size().reset_index(name='Count')
                    
                    fig = px.sunburst(
                        range_counts,
                        path=['Range', 'Achievement'],
                        values='Count',
                        title=f"Financial Outcomes: Value Ranges → Achievement Types{filter_suffix}",
                        color_discrete_sequence=PLOTLY_COLOR_SCHEMES['diverse_discrete']
                    )
                    fig.update_layout(get_plotly_theme()['layout'])
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("No quantitative financial outcomes available")
    else:
        st.info("No quantitative outcomes data available")
    
    # Alternative Word Cloud Representations
    st.subheader("💬 Qualitative Outcomes Insights")
    
    if qualitative_outcomes:
        qual_df = pd.DataFrame(qualitative_outcomes)
        
        # Alternative 1: Outcome Types by Use Case Matrix
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔍 Top Qualitative Outcomes by Use Case**")
            
            # Show top qualitative outcomes for each major use case
            for use_case, count in top_use_cases[:4]:
                if use_case in use_case_outcomes and use_case_outcomes[use_case]['qualitative']:
                    st.markdown(f"**{use_case.replace('_', ' ').title()}:**")
                    
                    # Get top outcome types for this use case
                    case_types = use_case_outcomes[use_case]['types']
                    top_types = sorted(case_types.items(), key=lambda x: x[1], reverse=True)[:3]
                    
                    for outcome_type, freq in top_types:
                        st.markdown(f"• {outcome_type.replace('_', ' ').title()}: {freq} stories")
                    st.markdown("")
        
        with col2:
            st.markdown("**📋 Outcome Frequency Heatmap**")
            
            # Get top outcome types from the overall data
            if outcome_types_overall:
                top_outcome_types_list = sorted(outcome_types_overall.items(), key=lambda x: x[1], reverse=True)[:6]
                
                # Create a matrix of use cases vs outcome types
                matrix_data = []
                for use_case in [uc[0] for uc in top_use_cases[:5]]:
                    for outcome_type, _ in top_outcome_types_list:
                        count = use_case_outcomes.get(use_case, {}).get('types', {}).get(outcome_type, 0)
                        matrix_data.append({
                            'Use_Case': use_case.replace('_', ' ').title()[:15] + '...' if len(use_case.replace('_', ' ').title()) > 15 else use_case.replace('_', ' ').title(),
                            'Outcome_Type': outcome_type.replace('_', ' ').title()[:12] + '...' if len(outcome_type.replace('_', ' ').title()) > 12 else outcome_type.replace('_', ' ').title(),
                            'Count': count
                        })
                
                if matrix_data:
                    matrix_df = pd.DataFrame(matrix_data)
                    pivot_matrix = matrix_df.pivot(index='Use_Case', columns='Outcome_Type', values='Count').fillna(0)
                    
                    fig = px.imshow(
                        pivot_matrix.values,
                        x=pivot_matrix.columns,
                        y=pivot_matrix.index,
                        color_continuous_scale='Blues',
                        title="Use Case vs Outcome Type Matrix",
                        labels=dict(color="Story Count")
                    )
                    fig.update_layout(get_plotly_theme()['layout'])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No matrix data available")
            else:
                st.info("No outcome types data available for heatmap")
    
    else:
        st.info("No qualitative outcomes data available")
    
    # Operational Scale Highlights
    st.subheader("🚀 Operational Scale Achievements - The Big Numbers!")
    st.markdown("*Massive scale achievements (events, users, sessions processed)*")
    
    # Extract operational metrics that we filtered out above
    operational_metrics = []
    for idx, row in df_filtered.iterrows():
        if isinstance(row['extracted_data'], dict):
            outcomes = row['extracted_data'].get('business_outcomes', [])
            use_case = row.get('use_case_category', 'Unknown')
            customer = row.get('customer_name', 'Unknown')
            source = row['source_name']
            
            for outcome in outcomes:
                if isinstance(outcome, dict):
                    outcome_type = outcome.get('type', 'Unknown')
                    value = outcome.get('value')
                    unit = outcome.get('unit', '')
                    description = outcome.get('description', '')
                    
                    # Include the operational metrics we filtered out
                    if (value and isinstance(value, (int, float)) and value > 0 and
                        (outcome_type in ['scale', 'operational', 'performance', 'user_reach', 'user_adoption', 
                                        'user_growth', 'engagement', 'capacity', 'throughput', 'volume'] or
                         unit in ['events', 'pages', 'sessions', 'users', 'requests', 'queries', 
                                'files', 'documents'] or
                         value >= 1000000000)):  # Values >= 1B are likely operational
                        
                        operational_metrics.append({
                            'Customer': customer,
                            'Use_Case': use_case.replace('_', ' ').title(),
                            'Type': outcome_type.replace('_', ' ').title(),
                            'Value': value,
                            'Unit': unit,
                            'Description': description,
                            'Source': source
                        })
    
    if operational_metrics:
        # Sort by value descending to show biggest individual achievements
        ops_df = pd.DataFrame(operational_metrics)
        top_ops = ops_df.nlargest(6, 'Value')
        
        # Display as highlight cards
        st.markdown("**🏆 Most Impressive Scale Achievements:**")
        
        cols = st.columns(3)
        for i, (_, row) in enumerate(top_ops.iterrows()):
            with cols[i % 3]:
                # Format the big numbers nicely
                if row['Value'] >= 1e12:
                    formatted_val = f"{row['Value']/1e12:.1f}T"
                elif row['Value'] >= 1e9:
                    formatted_val = f"{row['Value']/1e9:.1f}B"
                elif row['Value'] >= 1e6:
                    formatted_val = f"{row['Value']/1e6:.1f}M"
                else:
                    formatted_val = f"{row['Value']:,.0f}"
                
                st.metric(
                    label=f"🏢 {row['Customer'][:20]}{'...' if len(row['Customer']) > 20 else ''}",
                    value=f"{formatted_val} {row['Unit']}",
                    delta=f"{row['Type']} | {row['Source']}"
                )
                if row['Description']:
                    st.caption(row['Description'][:80] + ('...' if len(row['Description']) > 80 else ''))
        
    
    else:
        st.info("No operational scale metrics found")
    
    # Industry vs Company Size Matrix
    st.subheader("Industry vs Company Size Cross-Analysis")
    
    # Create cross-tabulation
    if 'industry' in df_filtered.columns and 'company_size' in df_filtered.columns:
        cross_tab = pd.crosstab(df_filtered['industry'], df_filtered['company_size'], margins=False)
        
        if not cross_tab.empty:
            fig = px.imshow(
                cross_tab.values,
                x=cross_tab.columns,
                y=cross_tab.index,
                color_continuous_scale='Blues',
                title=f"Story Count: Industry vs Company Size Matrix{filter_suffix}",
                labels=dict(x="Company Size", y="Industry", color="Story Count")
            )
            fig.update_layout(get_plotly_theme()['layout'])
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for cross-analysis")
    else:
        st.info("Industry or company size data not available")

def show_aileron_insights(df: pd.DataFrame, aileron_data: Dict):
    """Display Aileron framework insights"""
    st.title("🎯 Aileron GenAI SuperPowers Framework")
    st.markdown("*Aileron Group's tool for generating and prioritizing opportunities*")
    st.markdown("---")
    
    if not any(aileron_data.values()):
        st.warning("No Aileron framework data found. Stories may need reprocessing with updated framework.")
        return
    
    # SuperPowers analysis with icons
    st.subheader("🔗 SuperPowers (Drive) - AI Capabilities Being Used")
    st.markdown("*What AI capabilities are being deployed*")
    
    if aileron_data['superpowers']:
        # Add icons and better labels for SuperPowers
        superpower_icons = {
            'code': '🔗 Code',
            'create_content': '✨ Create Content',
            'automate_with_agents': '🤖 Automate with Agents', 
            'find_data_insights': '📊 Find Data Insights',
            'research': '🔍 Research',
            'brainstorm': '💡 Brainstorm',
            'natural_language': '💬 Use Natural Language'
        }
        
        powers_df = pd.DataFrame(list(aileron_data['superpowers'].items()), 
                                columns=['SuperPower', 'Count'])
        powers_df['Display_Name'] = powers_df['SuperPower'].map(
            lambda x: superpower_icons.get(x, f"❓ {x.replace('_', ' ').title()}")
        )
        
        fig = px.bar(
            powers_df,
            x='Display_Name',
            y='Count',
            color='Count',
            color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues'],
            title="SuperPowers Distribution - What AI Capabilities Are Used"
        )
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_xaxes(tickangle=45)
        fig.update_layout(xaxis_title="AI SuperPowers", yaxis_title="Number of Stories")
        st.plotly_chart(fig, use_container_width=True)
    
    # Business Impacts and Functions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Business Impacts (Constrain) - Outcomes Achieved")
        st.markdown("*What business value is being delivered*")
        
        if aileron_data['impacts']:
            # Add icons for business impacts
            impact_icons = {
                'innovation': '🚀 Innovation',
                'efficiency': '⚡ Efficiency', 
                'speed': '🏃 Speed',
                'quality': '⭐ Quality',
                'client_satisfaction': '😊 Client Satisfaction',
                'risk_reduction': '⚠️ Risk Reduction'
            }
            
            impacts_df = pd.DataFrame(list(aileron_data['impacts'].items()),
                                    columns=['Impact', 'Count'])
            impacts_df['Display_Name'] = impacts_df['Impact'].map(
                lambda x: impact_icons.get(x, f"📈 {x.replace('_', ' ').title()}")
            )
            
            fig = px.pie(impacts_df, values='Count', names='Display_Name', 
                        title="Business Impacts Distribution",
                        color_discrete_sequence=PLOTLY_COLOR_SCHEMES['qualitative_set3'])
            fig.update_layout(get_plotly_theme()['layout'])
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏢 Business Value Chain - Functions Benefiting")
        st.markdown("*Which departments are seeing AI benefits*")
        
        if aileron_data['functions']:
            # Add icons for business functions
            function_icons = {
                'marketing': '📱 Marketing',
                'sales': '💰 Sales',
                'production': '🏭 Production', 
                'distribution': '🚚 Distribution',
                'service': '🎧 Service',
                'finance_and_accounting': '📊 Finance & Accounting'
            }
            
            functions_df = pd.DataFrame(list(aileron_data['functions'].items()),
                                      columns=['Function', 'Count'])
            functions_df['Display_Name'] = functions_df['Function'].map(
                lambda x: function_icons.get(x, f"🏢 {x.replace('_', ' ').title()}")
            )
            
            fig = px.pie(functions_df, values='Count', names='Display_Name',
                        title="Business Functions Distribution",
                        color_discrete_sequence=PLOTLY_COLOR_SCHEMES['qualitative_set1'])
            fig.update_layout(get_plotly_theme()['layout'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Adoption Enablers
    st.subheader("🛡️ Adoption Enablers - Organizational Success Factors")
    st.markdown("*What organizational capabilities enable AI success*")
    
    if aileron_data['enablers']:
        # Add icons for adoption enablers
        enabler_icons = {
            'data_and_digital': '💾 Data and Digital',
            'innovation_culture': '🔬 Innovation Culture',
            'ecosystem_partners': '🤝 Ecosystem Partners',
            'policy_and_governance': '📋 Policy & Governance',
            'risk_management': '🛡️ Risk Management'
        }
        
        enablers_df = pd.DataFrame(list(aileron_data['enablers'].items()),
                                 columns=['Enabler', 'Count'])
        enablers_df['Display_Name'] = enablers_df['Enabler'].map(
            lambda x: enabler_icons.get(x, f"🔧 {x.replace('_', ' ').title()}")
        )
        
        fig = px.bar(
            enablers_df,
            x='Display_Name',
            y='Count',
            color='Count',
            color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues'],
            title="Adoption Enablers Distribution"
        )
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_xaxes(tickangle=45)
        fig.update_layout(xaxis_title="Organizational Enablers", yaxis_title="Number of Stories")
        st.plotly_chart(fig, use_container_width=True)
    
    # Cross-analysis matrix
    st.subheader("🔄 Cross-Analysis: SuperPowers → Business Impacts")
    st.markdown("*How AI capabilities drive business outcomes across customer stories*")
    
    # Create cross-tabulation with icons - only for Gen AI stories
    cross_data = []
    for idx, row in df.iterrows():
        if (row.get('is_gen_ai') == True and 
            isinstance(row['extracted_data'], dict)):
            powers = row['extracted_data'].get('gen_ai_superpowers', [])
            impacts = row['extracted_data'].get('business_impacts', [])
            
            for power in powers:
                for impact in impacts:
                    cross_data.append({'SuperPower': power, 'Impact': impact})
    
    if cross_data:
        cross_df = pd.DataFrame(cross_data)
        pivot_table = cross_df.groupby(['SuperPower', 'Impact']).size().unstack(fill_value=0)
        
        # Create heatmap with better labels
        fig = px.imshow(
            pivot_table.values,
            x=[impact_icons.get(col, col.replace('_', ' ').title()) for col in pivot_table.columns],
            y=[superpower_icons.get(idx, idx.replace('_', ' ').title()) for idx in pivot_table.index],
            color_continuous_scale='RdYlBu_r',
            title="SuperPowers → Business Impacts Cross-Analysis Matrix",
            labels=dict(x="Business Impacts (Outcomes)", y="SuperPowers (Capabilities)", color="Stories Count")
        )
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_layout(
            height=600,
            xaxis_title="Business Impacts Achieved",
            yaxis_title="AI SuperPowers Used"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary insights
        st.markdown("### 📋 Key Insights from Cross-Analysis")
        
        # Find top combinations
        cross_summary = cross_df.groupby(['SuperPower', 'Impact']).size().reset_index(name='Count')
        top_combinations = cross_summary.nlargest(5, 'Count')
        
        st.markdown("**Top 5 SuperPower → Impact Combinations:**")
        for idx, row in top_combinations.iterrows():
            power_display = superpower_icons.get(row['SuperPower'], row['SuperPower'])
            impact_display = impact_icons.get(row['Impact'], row['Impact'])
            st.markdown(f"• **{power_display}** → **{impact_display}**: {row['Count']} stories")
    
    else:
        st.info("Cross-analysis data not available. Stories may need reprocessing with Aileron framework.")
    
    # Framework summary
    st.markdown("---")
    st.markdown("### 📊 Aileron Framework Summary")
    
    # Calculate Gen AI stories with complete Aileron data
    gen_ai_stories = len([row for idx, row in df.iterrows() if row.get('is_gen_ai') == True])
    
    total_stories_with_aileron = len([
        row for idx, row in df.iterrows()
        if row.get('is_gen_ai') == True and 
        isinstance(row.get('extracted_data'), dict) and 
        row['extracted_data'].get('gen_ai_superpowers')
    ])
    
    missing_aileron = gen_ai_stories - total_stories_with_aileron
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Gen AI Stories Analyzed", 
            total_stories_with_aileron,
            f"of {gen_ai_stories} Gen AI"
        )
        if missing_aileron > 0:
            st.warning(f"⚠️ {missing_aileron} Gen AI stories missing Aileron data")
    
    with col2:
        if aileron_data['superpowers']:
            st.metric(
                "Unique SuperPowers", 
                len(aileron_data['superpowers']),
                "AI capabilities identified"
            )
    
    with col3:
        if aileron_data['impacts']:
            st.metric(
                "Business Impacts", 
                len(aileron_data['impacts']),
                "outcome types measured"
            )
    
    with col4:
        if aileron_data['enablers']:
            st.metric(
                "Success Enablers", 
                len(aileron_data['enablers']),
                "organizational factors"
            )

def show_data_export(df: pd.DataFrame):
    """Display data export interface"""
    st.title("💾 Data Export")
    st.markdown("---")
    
    st.subheader("Export Options")
    
    # Export format selection
    export_format = st.selectbox("Select Export Format", ["CSV", "Excel", "JSON"])
    
    # Data selection
    export_option = st.radio(
        "What data to export?",
        ["All Stories", "Filtered Stories", "Summary Statistics"]
    )
    
    if export_option == "Filtered Stories":
        st.subheader("Apply Filters")
        
        col1, col2 = st.columns(2)
        with col1:
            source_filter = st.multiselect("Sources", df['source_name'].unique())
            industry_filter = st.multiselect("Industries", df['industry'].dropna().unique())
        
        with col2:
            size_filter = st.multiselect("Company Sizes", df['company_size'].dropna().unique())
            year_filter = st.multiselect("Years", df['publish_year'].dropna().unique())
        
        # Apply filters
        export_df = df.copy()
        if source_filter:
            export_df = export_df[export_df['source_name'].isin(source_filter)]
        if industry_filter:
            export_df = export_df[export_df['industry'].isin(industry_filter)]
        if size_filter:
            export_df = export_df[export_df['company_size'].isin(size_filter)]
        if year_filter:
            export_df = export_df[export_df['publish_year'].isin(year_filter)]
        
        st.info(f"Filtered dataset contains {len(export_df)} stories")
    
    elif export_option == "Summary Statistics":
        # Create summary dataset
        summary_data = []
        for source in df['source_name'].unique():
            source_df = df[df['source_name'] == source]
            summary_data.append({
                'Source': source,
                'Total_Stories': len(source_df),
                'Unique_Industries': source_df['industry'].nunique(),
                'Avg_Quality_Score': source_df['extracted_data'].apply(
                    lambda x: x.get('content_quality_score', 0) if isinstance(x, dict) else 0
                ).mean(),
                'Date_Range_Start': source_df['publish_date'].min(),
                'Date_Range_End': source_df['publish_date'].max()
            })
        export_df = pd.DataFrame(summary_data)
    else:
        export_df = df.copy()
    
    # Generate download
    if st.button("Generate Download"):
        try:
            if export_format.lower() == 'csv':
                data = create_download_data(export_df, 'csv')
                filename = f"ai_stories_{export_option.lower().replace(' ', '_')}.csv"
                mime_type = "text/csv"
            
            elif export_format.lower() == 'excel':
                data = create_download_data(export_df, 'excel')
                filename = f"ai_stories_{export_option.lower().replace(' ', '_')}.xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            else:  # JSON
                data = create_download_data(export_df, 'json')
                filename = f"ai_stories_{export_option.lower().replace(' ', '_')}.json"
                mime_type = "application/json"
            
            st.download_button(
                label=f"📥 Download {export_format} File",
                data=data,
                file_name=filename,
                mime=mime_type
            )
            
            st.success(f"✅ {export_format} file ready for download!")
            
        except Exception as e:
            st.error(f"Export failed: {e}")
    
    # Preview data
    st.subheader("Data Preview")
    st.dataframe(export_df.head(10), use_container_width=True)

if __name__ == "__main__":
    main()