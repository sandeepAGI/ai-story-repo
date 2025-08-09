#!/usr/bin/env python3
"""
Analytics Page Module for AI Customer Stories Dashboard
Comprehensive data analysis and visualizations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'components'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.dashboard.core.data_processor import filter_stories_by_genai, get_svg_export_config, apply_chart_formatting
from src.dashboard.components.charts import (
    create_industry_pie_chart, 
    create_technology_usage_chart,
    create_business_outcomes_chart,
    create_metric_cards,
    apply_industry_chart_options
)
from src.dashboard.core.brand_styles import PLOTLY_COLOR_SCHEMES, get_plotly_theme


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
        df_filtered = filter_stories_by_genai(df, 'genai_only')
        filter_suffix = " (Gen AI Only)"
    elif ai_filter == "Non Gen AI Only":
        df_filtered = filter_stories_by_genai(df, 'non_genai_only')
        filter_suffix = " (Non Gen AI Only)"
    else:
        df_filtered = df.copy()
        filter_suffix = ""
    
    # Show current filter stats
    _display_filter_metrics(df, df_filtered)
    
    st.markdown("---")
    
    # Check if we have data after filtering
    if len(df_filtered) == 0:
        st.warning(f"No stories found for '{ai_filter}' filter. Please select a different filter.")
        return
    
    # Industry analysis with improved labeling
    _display_industry_analysis(df_filtered, filter_suffix)
    
    # Company size and use case analysis
    _display_company_and_usecase_analysis(df_filtered, filter_suffix)
    
    # Technology usage analysis
    _display_technology_analysis(df_filtered, filter_suffix)
    
    # Business outcomes analysis
    _display_business_outcomes_analysis(df_filtered, filter_suffix)
    
    # Advanced analytics
    _display_advanced_analytics(df_filtered, filter_suffix)


def _display_filter_metrics(df: pd.DataFrame, df_filtered: pd.DataFrame):
    """Display metrics for current filter"""
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


def _display_industry_analysis(df_filtered: pd.DataFrame, filter_suffix: str):
    """Display industry distribution analysis"""
    st.subheader(f"Industry Distribution{filter_suffix}")
    industry_counts = df_filtered['industry'].value_counts().head(10)
    
    # Add chart options for better space utilization
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("**Display Options:**")
        label_style = st.selectbox(
            "Labels:", 
            options=["Direct on chart", "Compact legend", "Bottom legend", "No legend"],
            index=2,  # Default to "Bottom legend"
            key="industry_labels"
        )
    
    with col1:
        fig = create_industry_pie_chart(df_filtered, "Top 10 Industries")
        fig = apply_industry_chart_options(fig, label_style)
        fig.update_layout(get_plotly_theme()['layout'])
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Industry_Distribution"))
        
        # Add summary table for "No legend" option
        if label_style == "No legend":
            st.markdown("**Industry Breakdown:**")
            summary_df = pd.DataFrame({
                'Industry': industry_counts.index,
                'Count': industry_counts.values,
                'Percentage': [f"{(v/industry_counts.sum()*100):.1f}%" for v in industry_counts.values]
            })
            st.dataframe(summary_df, use_container_width=True, hide_index=True)


def _display_company_and_usecase_analysis(df_filtered: pd.DataFrame, filter_suffix: str):
    """Display company size and use case analysis"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Company Size Distribution{filter_suffix}")
        size_counts = df_filtered['company_size'].value_counts()
        
        fig = px.bar(
            x=size_counts.index, 
            y=size_counts.values,
            color=size_counts.values, 
            color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues']
        )
        
        apply_chart_formatting(fig, "Stories by Company Size")
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_xaxes(title_text="")
        fig.update_yaxes(title_text="")
        fig.update_coloraxes(colorbar_title="Count")
        
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Company_Size_Distribution"))
    
    with col2:
        st.subheader(f"Use Case Categories{filter_suffix}")
        
        if 'use_case_category' in df_filtered.columns:
            use_case_counts = df_filtered['use_case_category'].value_counts().head(8)
            
            fig = px.bar(
                x=use_case_counts.values, 
                y=use_case_counts.index, 
                orientation='h', 
                color=use_case_counts.values, 
                color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues']
            )
            
            apply_chart_formatting(fig, "Top AI Use Cases")
            fig.update_layout(get_plotly_theme()['layout'])
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            fig.update_coloraxes(colorbar_title="Count")
            
            st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Top_AI_Use_Cases"))
        else:
            st.info("Use case category data not available")


def _display_technology_analysis(df_filtered: pd.DataFrame, filter_suffix: str):
    """Display technology usage analysis"""
    st.subheader(f"Technology Usage Analysis{filter_suffix}")
    
    # Extract technologies with source attribution
    tech_source_data = []
    source_tech_counts = {}
    
    for idx, row in df_filtered.iterrows():
        if isinstance(row['extracted_data'], dict):
            techs = row['extracted_data'].get('technologies_used', [])
            source = row['source_name']
            
            if source not in source_tech_counts:
                source_tech_counts[source] = {}
            
            for tech in techs:
                tech_source_data.append({'Technology': tech, 'Source': source})
                source_tech_counts[source][tech] = source_tech_counts[source].get(tech, 0) + 1
    
    if tech_source_data:
        # Top Technologies by Each Source (Side-by-side)
        st.markdown("**Top Technologies by AI Provider**")
        
        sources = list(source_tech_counts.keys())
        
        # Create columns for each source
        if len(sources) <= 3:
            cols = st.columns(len(sources))
        else:
            cols = st.columns(3)
            # Show only top 3 sources by story count
            sources = sorted(sources, key=lambda s: sum(source_tech_counts[s].values()), reverse=True)[:3]
        
        for i, source in enumerate(sources):
            if i < len(cols):
                with cols[i]:
                    st.markdown(f"**{source}**")
                    source_techs = source_tech_counts[source]
                    top_techs = sorted(source_techs.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    for tech, count in top_techs:
                        st.write(f"• {tech}: {count}")
        
        # Overall technology usage chart
        st.markdown("**Overall Technology Usage**")
        fig = create_technology_usage_chart(df_filtered, "Most Used Technologies")
        fig.update_layout(get_plotly_theme()['layout'])
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Technology_Usage"))
    
    else:
        st.info("No technology usage data available")


def _display_business_outcomes_analysis(df_filtered: pd.DataFrame, filter_suffix: str):
    """Display business outcomes analysis"""
    st.subheader(f"Business Outcomes Analysis{filter_suffix}")
    
    # Extract financial outcomes
    financial_outcomes = []
    operational_outcomes = []
    
    for _, row in df_filtered.iterrows():
        if isinstance(row['extracted_data'], dict):
            outcomes = row['extracted_data'].get('quantified_business_outcomes', [])
            
            for outcome in outcomes:
                if isinstance(outcome, dict):
                    outcome_data = {
                        **outcome,
                        'customer': row['customer_name'],
                        'source': row['source_name'],
                        'industry': row['industry']
                    }
                    
                    # Categorize by outcome type
                    outcome_type = outcome.get('type', '').lower()
                    if any(keyword in outcome_type for keyword in ['cost', 'saving', 'revenue', 'profit', 'financial']):
                        financial_outcomes.append(outcome_data)
                    elif any(keyword in outcome_type for keyword in ['time', 'efficiency', 'productivity', 'operational']):
                        operational_outcomes.append(outcome_data)
    
    if financial_outcomes or operational_outcomes:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💰 Top Financial Achievements**")
            if financial_outcomes:
                for outcome in financial_outcomes[:5]:
                    value = outcome.get('value', 'N/A')
                    unit = outcome.get('unit', '')
                    customer = outcome.get('customer', 'Unknown')
                    outcome_type = outcome.get('type', 'Financial Benefit').replace('_', ' ').title()
                    
                    st.write(f"• **{customer}**: {value} {unit} ({outcome_type})")
            else:
                st.info("No financial outcomes available")
        
        with col2:
            st.markdown("**🚀 Top Operational Improvements**")
            if operational_outcomes:
                for outcome in operational_outcomes[:5]:
                    value = outcome.get('value', 'N/A')
                    unit = outcome.get('unit', '')
                    customer = outcome.get('customer', 'Unknown')
                    outcome_type = outcome.get('type', 'Operational Benefit').replace('_', ' ').title()
                    
                    st.write(f"• **{customer}**: {value} {unit} ({outcome_type})")
            else:
                st.info("No operational outcomes available")
    
    else:
        st.info("No quantified business outcomes available")


def _display_advanced_analytics(df_filtered: pd.DataFrame, filter_suffix: str):
    """Display advanced analytics and insights"""
    st.subheader(f"Advanced Analytics{filter_suffix}")
    
    # Publication timeline
    if 'publish_date' in df_filtered.columns:
        st.markdown("**📅 Publication Timeline**")
        
        df_dates = df_filtered.dropna(subset=['publish_date']).copy()
        if not df_dates.empty:
            df_dates['publish_date'] = pd.to_datetime(df_dates['publish_date'])
            df_dates['year_month'] = df_dates['publish_date'].dt.to_period('M')
            
            timeline_counts = df_dates.groupby('year_month').size()
            
            fig = px.line(
                x=timeline_counts.index.astype(str),
                y=timeline_counts.values,
                title="Stories Published Over Time"
            )
            
            apply_chart_formatting(fig, "Stories Published Over Time")
            fig.update_layout(get_plotly_theme()['layout'])
            fig.update_layout(xaxis_title="Publication Date", yaxis_title="Story Count")
            
            st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Publication_Timeline"))
        else:
            st.info("No publication date data available")
    
    # Quality score distribution
    st.markdown("**⭐ Content Quality Distribution**")
    quality_scores = []
    
    for _, row in df_filtered.iterrows():
        if isinstance(row['extracted_data'], dict):
            score = row['extracted_data'].get('content_quality_score')
            if isinstance(score, (int, float)):
                quality_scores.append(score)
    
    if quality_scores:
        fig = px.histogram(
            x=quality_scores,
            nbins=20,
            title="Content Quality Score Distribution"
        )
        
        apply_chart_formatting(fig, "Content Quality Score Distribution")
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_layout(xaxis_title="Quality Score", yaxis_title="Number of Stories")
        
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Quality_Distribution"))
        
        # Quality statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Quality", f"{sum(quality_scores)/len(quality_scores):.3f}")
        with col2:
            st.metric("Median Quality", f"{sorted(quality_scores)[len(quality_scores)//2]:.3f}")
        with col3:
            st.metric("Min Quality", f"{min(quality_scores):.3f}")
        with col4:
            st.metric("Max Quality", f"{max(quality_scores):.3f}")
    
    else:
        st.info("No quality score data available")