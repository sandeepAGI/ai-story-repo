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
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import io

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations, CustomerStory

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
    """Get Aileron framework analytics"""
    db_ops = get_database_connection()
    
    with db_ops.db.get_cursor() as cursor:
        # SuperPowers distribution
        cursor.execute("""
            SELECT 
                jsonb_array_elements_text(extracted_data->'gen_ai_superpowers') as superpower,
                COUNT(*) as count
            FROM customer_stories
            WHERE extracted_data->'gen_ai_superpowers' IS NOT NULL
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
            WHERE extracted_data->'business_impacts' IS NOT NULL
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
            WHERE extracted_data->'adoption_enablers' IS NOT NULL
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
            WHERE extracted_data->'business_function' IS NOT NULL
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
            color_discrete_map={'Gen AI': '#1f77b4', 'Non Gen AI': '#ff7f0e'},
            title="Story Count by AI Provider (Gen AI vs Non Gen AI breakdown)"
        )
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
    
    # Add clickable link column
    recent_df['Link'] = recent_df['url'].apply(lambda x: f'[View Story]({x})')
    
    # Reorder columns and remove raw url
    display_df = recent_df[['customer_name', 'source_name', 'industry', 'publish_date', 'Link']]
    display_df.columns = ['Customer Name', 'AI Provider', 'Industry', 'Publish Date', 'Link']
    
    st.dataframe(display_df, use_container_width=True)

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
        year_range = st.slider(
            "Publication Year", 
            int(df['publish_year'].min()) if df['publish_year'].notna().any() else 2020,
            int(df['publish_year'].max()) if df['publish_year'].notna().any() else 2025,
            (2020, 2025)
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if source_filter != "All":
        filtered_df = filtered_df[filtered_df['source_name'] == source_filter]
    
    if industry_filter != "All":
        filtered_df = filtered_df[filtered_df['industry'] == industry_filter]
    
    if size_filter != "All":
        filtered_df = filtered_df[filtered_df['company_size'] == size_filter]
    
    filtered_df = filtered_df[
        (filtered_df['publish_year'] >= year_range[0]) & 
        (filtered_df['publish_year'] <= year_range[1])
    ]
    
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
            
            with col2:
                st.write(f"**URL:** [Link]({row['url']})")
                
                if isinstance(row['extracted_data'], dict):
                    quality_score = row['extracted_data'].get('content_quality_score', 0)
                    st.metric("Quality Score", f"{quality_score:.2f}")

def show_analytics(df: pd.DataFrame, source_stats: Dict):
    """Display analytics dashboard"""
    st.title("📈 Analytics Dashboard")
    st.markdown("---")
    
    # Industry analysis
    st.subheader("Industry Distribution")
    industry_counts = df['industry'].value_counts().head(10)
    
    fig = px.pie(
        values=industry_counts.values,
        names=industry_counts.index,
        title="Top 10 Industries"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Company size analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Company Size Distribution")
        size_counts = df['company_size'].value_counts()
        fig = px.bar(x=size_counts.index, y=size_counts.values, title="Stories by Company Size")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Publication Timeline")
        df['year_month'] = pd.to_datetime(df['publish_date']).dt.to_period('M').astype(str)
        timeline = df['year_month'].value_counts().sort_index()
        fig = px.line(x=timeline.index, y=timeline.values, title="Stories Published Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    # Technology usage
    st.subheader("Technology Usage Analysis")
    
    # Extract technologies from JSON data
    all_technologies = []
    for idx, row in df.iterrows():
        if isinstance(row['extracted_data'], dict):
            techs = row['extracted_data'].get('technologies_used', [])
            all_technologies.extend(techs)
    
    if all_technologies:
        tech_counts = pd.Series(all_technologies).value_counts().head(15)
        fig = px.bar(
            x=tech_counts.values,
            y=tech_counts.index,
            orientation='h',
            title="Top 15 Technologies Mentioned"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

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
            color_continuous_scale='Blues',
            title="SuperPowers Distribution - What AI Capabilities Are Used"
        )
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
                        color_discrete_sequence=px.colors.qualitative.Set3)
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
                        color_discrete_sequence=px.colors.qualitative.Pastel)
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
            color_continuous_scale='Greens',
            title="Adoption Enablers Distribution"
        )
        fig.update_xaxes(tickangle=45)
        fig.update_layout(xaxis_title="Organizational Enablers", yaxis_title="Number of Stories")
        st.plotly_chart(fig, use_container_width=True)
    
    # Cross-analysis matrix
    st.subheader("🔄 Cross-Analysis: SuperPowers → Business Impacts")
    st.markdown("*How AI capabilities drive business outcomes across customer stories*")
    
    # Create cross-tabulation with icons
    cross_data = []
    for idx, row in df.iterrows():
        if isinstance(row['extracted_data'], dict):
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
    
    total_stories_with_aileron = len([
        row for idx, row in df.iterrows()
        if isinstance(row.get('extracted_data'), dict) and 
        row['extracted_data'].get('gen_ai_superpowers')
    ])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Stories Analyzed", 
            total_stories_with_aileron,
            f"of {len(df)} total"
        )
    
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