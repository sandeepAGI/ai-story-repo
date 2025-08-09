#!/usr/bin/env python3
"""
Reusable Chart Components for AI Customer Stories Dashboard
Standard chart creation functions with consistent styling
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.dashboard.core.data_processor import apply_chart_formatting, get_svg_export_config
from brand_styles import PLOTLY_COLOR_SCHEMES, get_plotly_theme


def create_industry_pie_chart(df: pd.DataFrame, title: str = "Industry Distribution", top_n: int = 10) -> go.Figure:
    """Create industry distribution pie chart with customizable display options"""
    industry_counts = df['industry'].value_counts().head(top_n)
    
    fig = px.pie(
        values=industry_counts.values,
        names=industry_counts.index,
        color_discrete_sequence=PLOTLY_COLOR_SCHEMES['diverse_discrete']
    )
    
    apply_chart_formatting(fig, title)
    return fig


def create_source_bar_chart(source_stats: Dict, title: str = "Stories by AI Provider") -> go.Figure:
    """Create source distribution bar chart"""
    sources = list(source_stats.keys())
    counts = [stats['story_count'] for stats in source_stats.values()]
    
    fig = px.bar(x=sources, y=counts)
    apply_chart_formatting(fig, title)
    fig.update_layout(xaxis_title="AI Provider", yaxis_title="Story Count")
    
    return fig


def create_technology_usage_chart(df: pd.DataFrame, title: str = "Technology Usage", top_n: int = 15) -> go.Figure:
    """Create technology usage analysis chart"""
    # Extract technologies from stories
    all_technologies = []
    tech_by_source = {}
    
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            techs = row['extracted_data'].get('technologies_used', [])
            if isinstance(techs, list):
                source = row['source_name']
                if source not in tech_by_source:
                    tech_by_source[source] = {}
                
                for tech in techs:
                    all_technologies.append(tech)
                    tech_by_source[source][tech] = tech_by_source[source].get(tech, 0) + 1
    
    # Get top technologies
    tech_counts = pd.Series(all_technologies).value_counts().head(top_n)
    
    fig = px.bar(x=tech_counts.values, y=tech_counts.index, orientation='h')
    apply_chart_formatting(fig, title)
    fig.update_layout(xaxis_title="Usage Count", yaxis_title="Technology")
    
    return fig


def create_business_outcomes_chart(df: pd.DataFrame, title: str = "Business Outcomes Analysis") -> go.Figure:
    """Create business outcomes visualization"""
    outcomes = []
    
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            business_outcomes = row['extracted_data'].get('quantified_business_outcomes', [])
            if isinstance(business_outcomes, list):
                for outcome in business_outcomes:
                    if isinstance(outcome, dict):
                        outcomes.append({
                            **outcome,
                            'customer': row['customer_name'],
                            'source': row['source_name']
                        })
    
    if not outcomes:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No quantified business outcomes available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        apply_chart_formatting(fig, title)
        return fig
    
    # Create outcomes by type
    outcomes_df = pd.DataFrame(outcomes)
    outcome_types = outcomes_df['type'].value_counts() if 'type' in outcomes_df.columns else pd.Series()
    
    fig = px.bar(x=outcome_types.index, y=outcome_types.values)
    apply_chart_formatting(fig, title)
    fig.update_layout(xaxis_title="Outcome Type", yaxis_title="Count")
    
    return fig


def create_cross_analysis_heatmap(df: pd.DataFrame, dim1: str, dim2: str, title: str) -> go.Figure:
    """Create cross-analysis heatmap between two dimensions"""
    cross_data = []
    
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            dim1_values = row['extracted_data'].get(dim1, [])
            dim2_values = row['extracted_data'].get(dim2, [])
            
            # Handle single values vs lists
            if not isinstance(dim1_values, list):
                dim1_values = [dim1_values] if dim1_values else []
            if not isinstance(dim2_values, list):
                dim2_values = [dim2_values] if dim2_values else []
            
            # Create cross-combinations
            for val1 in dim1_values:
                for val2 in dim2_values:
                    if val1 and val2:
                        cross_data.append({dim1: val1, dim2: val2})
    
    if not cross_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No cross-analysis data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        apply_chart_formatting(fig, title)
        return fig
    
    cross_df = pd.DataFrame(cross_data)
    cross_matrix = cross_df.groupby([dim1, dim2]).size().unstack(fill_value=0)
    
    fig = px.imshow(
        cross_matrix.values,
        x=cross_matrix.columns,
        y=cross_matrix.index,
        aspect="auto",
        color_continuous_scale="Blues"
    )
    
    apply_chart_formatting(fig, title)
    return fig


def create_sunburst_chart(df: pd.DataFrame, dimensions: List[str], title: str) -> go.Figure:
    """Create sunburst chart for hierarchical data analysis"""
    # Prepare hierarchical data
    paths = []
    
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            path_values = []
            for dim in dimensions:
                value = row['extracted_data'].get(dim)
                if isinstance(value, list) and value:
                    path_values.append(value[0])  # Take first value if list
                elif value:
                    path_values.append(str(value))
                else:
                    path_values.append("Unknown")
            
            if len(path_values) == len(dimensions):
                paths.append(" / ".join(path_values))
    
    if not paths:
        fig = go.Figure()
        fig.add_annotation(
            text="No hierarchical data available",
            xref="paper", yref="paper", 
            x=0.5, y=0.5, showarrow=False
        )
        apply_chart_formatting(fig, title)
        return fig
    
    # Count paths and create sunburst
    path_counts = pd.Series(paths).value_counts()
    
    # Parse paths for sunburst format
    labels = []
    parents = []
    values = []
    
    for path, count in path_counts.items():
        parts = path.split(" / ")
        
        # Add each level
        for i, part in enumerate(parts):
            if i == 0:
                parent = ""
            else:
                parent = " / ".join(parts[:i])
            
            current_path = " / ".join(parts[:i+1])
            if current_path not in labels:
                labels.append(current_path)
                parents.append(parent)
                # For intermediate nodes, sum up child values
                if i < len(parts) - 1:
                    child_sum = sum(c for p, c in path_counts.items() if p.startswith(current_path))
                    values.append(child_sum)
                else:
                    values.append(count)
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
    ))
    
    apply_chart_formatting(fig, title)
    return fig


def create_metric_cards(stats: Dict[str, Any], columns: int = 4) -> None:
    """Create metric cards display"""
    cols = st.columns(columns)
    
    metrics = list(stats.items())
    for i, (key, value) in enumerate(metrics):
        with cols[i % columns]:
            # Format key for display
            display_key = key.replace('_', ' ').title()
            
            # Format value based on type
            if isinstance(value, float):
                display_value = f"{value:.2f}"
            elif isinstance(value, dict):
                display_value = str(len(value))
            else:
                display_value = str(value)
            
            st.metric(display_key, display_value)


def create_timeline_chart(df: pd.DataFrame, title: str = "Story Timeline") -> go.Figure:
    """Create timeline chart showing story publication over time"""
    # Filter valid dates
    df_dates = df.dropna(subset=['publish_date']).copy()
    df_dates['publish_date'] = pd.to_datetime(df_dates['publish_date'])
    df_dates['year_month'] = df_dates['publish_date'].dt.to_period('M')
    
    timeline_counts = df_dates.groupby('year_month').size()
    
    fig = px.line(
        x=timeline_counts.index.astype(str),
        y=timeline_counts.values,
        title=title
    )
    
    apply_chart_formatting(fig, title)
    fig.update_layout(xaxis_title="Publication Date", yaxis_title="Story Count")
    
    return fig


def apply_industry_chart_options(fig: go.Figure, label_style: str) -> go.Figure:
    """Apply different labeling options to industry pie chart"""
    if label_style == "Direct on chart":
        fig.update_traces(
            textposition='inside',
            textinfo='label+percent',
            textfont_size=10
        )
        fig.update_layout(showlegend=False)
    
    elif label_style == "Compact legend":
        fig.update_traces(textinfo='percent')
        fig.update_layout(
            legend=dict(
                font=dict(size=9),
                itemwidth=30
            )
        )
    
    elif label_style == "Bottom legend":
        fig.update_traces(textinfo='percent')
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
    
    else:  # "No legend"
        fig.update_traces(textinfo='label+percent')
        fig.update_layout(showlegend=False)
    
    return fig