#!/usr/bin/env python3
"""
Story Explorer Page Module for AI Customer Stories Dashboard
Provides search and detailed story browsing functionality
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
import sys
import os

# Add dashboard core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from src.dashboard.core.data_processor import (
    filter_stories_by_genai, 
    filter_stories_by_source, 
    filter_stories_by_industry,
    filter_stories_by_company_size,
    search_stories
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
    
    # Source filter
    if source_filter != "All":
        filtered_df = filter_stories_by_source(filtered_df, [source_filter])
    
    # Industry filter
    if industry_filter != "All":
        filtered_df = filter_stories_by_industry(filtered_df, [industry_filter])
    
    # Company size filter
    if size_filter != "All":
        filtered_df = filter_stories_by_company_size(filtered_df, [size_filter])
    
    # AI type filter
    if ai_type_filter == "Gen AI":
        filtered_df = filter_stories_by_genai(filtered_df, 'genai_only')
    elif ai_type_filter == "Non Gen AI":
        filtered_df = filter_stories_by_genai(filtered_df, 'non_genai_only')
    
    # Search functionality
    if search_term:
        filtered_df = search_stories(filtered_df, search_term)
    
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
                    
                    # Display Aileron framework data if available (Gen AI stories)
                    if row.get('is_gen_ai', False):
                        _display_aileron_data(row['extracted_data'])
            
            with col2:
                st.write(f"**URL:** [Link]({row['url']})")
                
                if isinstance(row['extracted_data'], dict):
                    quality_score = row['extracted_data'].get('content_quality_score', 0)
                    st.metric("Quality Score", f"{quality_score:.2f}")
                    
                    # Show Gen AI classification
                    ai_type = row['extracted_data'].get('ai_type', 'Unknown')
                    is_gen_ai = "✅ Gen AI" if row.get('is_gen_ai', False) else "⚪ Non Gen AI"
                    st.write(f"**AI Type:** {is_gen_ai}")


def _display_aileron_data(extracted_data: dict):
    """Display Aileron framework data for Gen AI stories"""
    st.write("**🎯 Aileron GenAI Framework:**")
    
    # SuperPowers
    superpowers = extracted_data.get('gen_ai_superpowers', [])
    if superpowers:
        st.write(f"• **SuperPowers:** {', '.join(superpowers)}")
    
    # Business Impacts
    impacts = extracted_data.get('business_impacts', [])
    if impacts:
        st.write(f"• **Business Impacts:** {', '.join(impacts)}")
    
    # Adoption Enablers
    enablers = extracted_data.get('adoption_enablers', [])
    if enablers:
        st.write(f"• **Adoption Enablers:** {', '.join(enablers)}")
    
    # Business Function
    function = extracted_data.get('business_function')
    if function:
        st.write(f"• **Business Function:** {function}")


def show_story_details(story_data: dict, show_full_content: bool = False):
    """Display detailed view of a single story"""
    st.subheader(f"📖 {story_data.get('title', 'Untitled Story')}")
    
    # Basic info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Customer:** {story_data.get('customer_name', 'Unknown')}")
        st.write(f"**Source:** {story_data.get('source_name', 'Unknown')}")
    
    with col2:
        st.write(f"**Industry:** {story_data.get('industry', 'Unknown')}")
        st.write(f"**Company Size:** {story_data.get('company_size', 'Unknown')}")
    
    with col3:
        st.write(f"**Published:** {story_data.get('publish_date', 'Unknown')}")
        if story_data.get('url'):
            st.write(f"**URL:** [View Original]({story_data['url']})")
    
    # Content
    if show_full_content and story_data.get('content'):
        st.subheader("Full Content")
        st.text_area("Story Content", story_data['content'], height=300, disabled=True)
    
    # Extracted data
    if isinstance(story_data.get('extracted_data'), dict):
        extracted_data = story_data['extracted_data']
        
        st.subheader("Analysis Results")
        
        # Summary
        summary = extracted_data.get('summary')
        if summary:
            st.write(f"**Summary:** {summary}")
        
        # Quality score
        quality_score = extracted_data.get('content_quality_score', 0)
        st.metric("Content Quality Score", f"{quality_score:.2f}")
        
        # Technologies
        technologies = extracted_data.get('technologies_used', [])
        if technologies:
            st.write(f"**Technologies Used:** {', '.join(technologies)}")
        
        # If Gen AI story, show Aileron framework
        if story_data.get('is_gen_ai', False):
            _display_aileron_data(extracted_data)