#!/usr/bin/env python3
"""
Data Export Page Module for AI Customer Stories Dashboard
Provides data export functionality in multiple formats with filtering options
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from src.dashboard.core.data_processor import (
    create_download_data,
    filter_stories_by_source,
    filter_stories_by_industry,
    filter_stories_by_company_size,
    calculate_summary_stats
)
from src.dashboard.core.config import EXPORT_FORMATS


def show_data_export(df: pd.DataFrame):
    """Display data export interface"""
    st.title("💾 Data Export")
    st.markdown("---")
    
    st.subheader("Export Options")
    
    # Export format selection
    export_format = st.selectbox(
        "Select Export Format", 
        list(EXPORT_FORMATS.keys()),
        format_func=lambda x: EXPORT_FORMATS[x]
    )
    
    # Data selection
    export_option = st.radio(
        "What data to export?",
        ["All Stories", "Filtered Stories", "Summary Statistics"]
    )
    
    # Handle different export options
    if export_option == "Filtered Stories":
        export_df = _handle_filtered_export(df)
    elif export_option == "Summary Statistics":
        export_df = _create_summary_statistics(df)
    else:
        export_df = df.copy()
    
    # Show preview and generate download
    _display_preview_and_download(export_df, export_format, export_option)


def _handle_filtered_export(df: pd.DataFrame) -> pd.DataFrame:
    """Handle filtered export option with filter interface"""
    st.subheader("Apply Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_filter = st.multiselect("Sources", df['source_name'].unique())
        industry_filter = st.multiselect("Industries", df['industry'].dropna().unique())
    
    with col2:
        size_filter = st.multiselect("Company Sizes", df['company_size'].dropna().unique())
        
        # Year filter (if publish_year exists)
        if 'publish_year' in df.columns:
            year_filter = st.multiselect("Years", sorted(df['publish_year'].dropna().unique()))
        else:
            year_filter = []
    
    # Additional filters
    col3, col4 = st.columns(2)
    
    with col3:
        ai_type_filter = st.selectbox("AI Type", ["All", "Gen AI Only", "Non Gen AI Only"])
    
    with col4:
        quality_threshold = st.slider(
            "Minimum Quality Score", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.0, 
            step=0.1,
            help="Filter stories by minimum content quality score"
        )
    
    # Apply filters
    export_df = df.copy()
    
    # Source filter
    if source_filter:
        export_df = filter_stories_by_source(export_df, source_filter)
    
    # Industry filter
    if industry_filter:
        export_df = filter_stories_by_industry(export_df, industry_filter)
    
    # Company size filter
    if size_filter:
        export_df = filter_stories_by_company_size(export_df, size_filter)
    
    # Year filter
    if year_filter and 'publish_year' in df.columns:
        export_df = export_df[export_df['publish_year'].isin(year_filter)]
    
    # AI type filter
    if ai_type_filter == "Gen AI Only":
        export_df = export_df[export_df['is_gen_ai'] == True]
    elif ai_type_filter == "Non Gen AI Only":
        export_df = export_df[export_df['is_gen_ai'] == False]
    
    # Quality threshold filter
    if quality_threshold > 0:
        def meets_quality_threshold(row):
            if isinstance(row['extracted_data'], dict):
                score = row['extracted_data'].get('content_quality_score', 0)
                return score >= quality_threshold
            return False
        
        export_df = export_df[export_df.apply(meets_quality_threshold, axis=1)]
    
    st.info(f"Filtered dataset contains {len(export_df)} stories")
    
    # Show filter summary
    _display_filter_summary(export_df, df)
    
    return export_df


def _create_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Create summary statistics dataset"""
    summary_data = []
    
    for source in df['source_name'].unique():
        source_df = df[df['source_name'] == source]
        
        # Calculate statistics for this source
        stats = calculate_summary_stats(source_df)
        
        summary_data.append({
            'Source': source,
            'Total_Stories': stats['total_stories'],
            'Gen_AI_Stories': stats['genai_stories'],
            'Non_Gen_AI_Stories': stats['non_genai_stories'],
            'Gen_AI_Percentage': round(stats['genai_percentage'], 1),
            'Unique_Industries': stats['unique_industries'],
            'Avg_Quality_Score': round(stats['avg_quality_score'], 3),
            'Date_Range_Start': stats['date_range']['earliest'],
            'Date_Range_End': stats['date_range']['latest']
        })
    
    return pd.DataFrame(summary_data)


def _display_filter_summary(filtered_df: pd.DataFrame, original_df: pd.DataFrame):
    """Display summary of applied filters"""
    if len(filtered_df) < len(original_df):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Stories", len(filtered_df), f"-{len(original_df) - len(filtered_df)}")
        
        with col2:
            original_industries = original_df['industry'].nunique()
            filtered_industries = filtered_df['industry'].nunique()
            st.metric("Industries", filtered_industries, f"-{original_industries - filtered_industries}")
        
        with col3:
            original_sources = original_df['source_name'].nunique()
            filtered_sources = filtered_df['source_name'].nunique()
            st.metric("Sources", filtered_sources, f"-{original_sources - filtered_sources}")
        
        with col4:
            if len(filtered_df) > 0:
                avg_quality = filtered_df['extracted_data'].apply(
                    lambda x: x.get('content_quality_score', 0) if isinstance(x, dict) else 0
                ).mean()
                st.metric("Avg Quality", f"{avg_quality:.3f}")


def _display_preview_and_download(export_df: pd.DataFrame, export_format: str, export_option: str):
    """Display data preview and generate download"""
    
    # Generate download
    if st.button("Generate Download", type="primary"):
        try:
            data = create_download_data(export_df, export_format)
            
            # Determine filename and MIME type
            filename_base = f"ai_stories_{export_option.lower().replace(' ', '_')}"
            
            if export_format == 'csv':
                filename = f"{filename_base}.csv"
                mime_type = "text/csv"
            elif export_format == 'excel':
                filename = f"{filename_base}.xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:  # json
                filename = f"{filename_base}.json"
                mime_type = "application/json"
            
            st.download_button(
                label=f"📥 Download {EXPORT_FORMATS[export_format]} File",
                data=data,
                file_name=filename,
                mime=mime_type
            )
            
            st.success(f"✅ {EXPORT_FORMATS[export_format]} file ready for download!")
            
            # Show file info
            file_size = len(data)
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.1f} KB"
            else:
                size_str = f"{file_size/(1024*1024):.1f} MB"
            
            st.info(f"📊 File contains {len(export_df)} records ({size_str})")
            
        except Exception as e:
            st.error(f"Export failed: {e}")
            st.error("Please try a different format or contact support if the issue persists.")
    
    # Preview data
    st.subheader("Data Preview")
    
    if len(export_df) == 0:
        st.warning("No data to preview with current filters.")
    else:
        # Show column information
        st.markdown(f"**Dataset Info:** {len(export_df)} rows × {len(export_df.columns)} columns")
        
        # Column selection for preview
        if len(export_df.columns) > 10:
            st.markdown("**Note:** Showing first 10 columns. Full dataset will be included in download.")
            preview_cols = export_df.columns[:10].tolist()
        else:
            preview_cols = export_df.columns.tolist()
        
        # Display preview
        preview_df = export_df[preview_cols].head(10)
        st.dataframe(preview_df, use_container_width=True)
        
        # Show column names for reference
        if st.expander("View All Column Names"):
            col_list = ", ".join(export_df.columns.tolist())
            st.text(col_list)


def show_export_templates():
    """Display information about export templates and data structure"""
    st.subheader("📋 Export Templates & Data Structure")
    
    templates = {
        "Story Analysis Template": {
            "description": "Optimized for story analysis and research",
            "columns": ["customer_name", "source_name", "industry", "company_size", "publish_date", 
                       "title", "url", "is_gen_ai", "content_quality_score"],
            "use_case": "Research, competitive analysis, content review"
        },
        "Business Outcomes Template": {
            "description": "Focus on quantified business results",
            "columns": ["customer_name", "industry", "quantified_business_outcomes", 
                       "technologies_used", "business_impacts"],
            "use_case": "ROI analysis, outcome tracking, success stories"
        },
        "Technology Usage Template": {
            "description": "Analysis of AI technologies and implementations",
            "columns": ["customer_name", "source_name", "technologies_used", 
                       "gen_ai_superpowers", "use_case_category"],
            "use_case": "Technology adoption research, product analysis"
        }
    }
    
    for template_name, template_info in templates.items():
        with st.expander(template_name):
            st.markdown(f"**Description:** {template_info['description']}")
            st.markdown(f"**Use Case:** {template_info['use_case']}")
            st.markdown(f"**Key Columns:** {', '.join(template_info['columns'])}")