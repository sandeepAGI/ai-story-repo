#!/usr/bin/env python3
"""
Overview Page Module for AI Customer Stories Dashboard
Displays key metrics, source distribution, and recent stories
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
import sys
import os

# Add dashboard core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.dashboard.core.data_processor import apply_chart_formatting, get_svg_export_config
from src.dashboard.core.brand_styles import PLOTLY_COLOR_SCHEMES, get_plotly_theme


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
            color_discrete_map=PLOTLY_COLOR_SCHEMES['gen_ai_colors']
        )
        apply_chart_formatting(fig, "Story Count by AI Provider")
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Story_Count_by_AI_Provider"))
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