#!/usr/bin/env python3
"""
Data Processing Module for AI Customer Stories Dashboard  
Handles data filtering, transformation, and export functionality
"""

import pandas as pd
import io
from typing import Dict, Any, List, Optional
from .config import MAX_CHART_TITLE_LENGTH, SVG_EXPORT_CONFIG


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


def format_chart_title(title: str, max_length: int = None) -> str:
    """Format chart title with word wrapping for long titles"""
    if max_length is None:
        max_length = MAX_CHART_TITLE_LENGTH
        
    if len(title) <= max_length:
        return title
    
    # Split into words and create wrapped lines
    words = title.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        # Check if adding this word would exceed max_length
        word_length = len(word) + (1 if current_line else 0)  # +1 for space
        
        if current_length + word_length <= max_length:
            current_line.append(word)
            current_length += word_length
        else:
            # Start new line
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    # Add the last line
    if current_line:
        lines.append(' '.join(current_line))
    
    # Join lines with HTML line breaks for Plotly
    return '<br>'.join(lines)


def get_svg_export_config(chart_title: str = "chart") -> Dict:
    """Get Plotly configuration for SVG export (PowerPoint editable)"""
    return {
        'displayModeBar': True,
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': chart_title.lower().replace(' ', '_').replace('→', '_to_'),
            'height': SVG_EXPORT_CONFIG['height'],
            'width': SVG_EXPORT_CONFIG['width'],
            'scale': SVG_EXPORT_CONFIG['scale']
        },
        'displaylogo': False,
        'modeBarButtonsToAdd': ['downloadSVG']
    }


def apply_chart_formatting(fig, title: str):
    """Apply consistent formatting to charts: centered, wrapped titles"""
    formatted_title = format_chart_title(title)
    fig.update_layout(
        title=dict(
            text=formatted_title,
            x=0.5,  # Center the title
            xanchor='center',
            font=dict(size=16)
        )
    )


def filter_stories_by_genai(df: pd.DataFrame, filter_type: str) -> pd.DataFrame:
    """Filter stories by Gen AI classification
    
    Args:
        df: Stories DataFrame
        filter_type: 'all', 'genai_only', or 'non_genai_only'
    """
    if filter_type == 'genai_only':
        return df[df['is_gen_ai'] == True]
    elif filter_type == 'non_genai_only': 
        return df[df['is_gen_ai'] == False]
    else:  # 'all'
        return df


def filter_stories_by_source(df: pd.DataFrame, selected_sources: List[str]) -> pd.DataFrame:
    """Filter stories by selected sources"""
    if not selected_sources:
        return df
    return df[df['source_name'].isin(selected_sources)]


def filter_stories_by_industry(df: pd.DataFrame, selected_industries: List[str]) -> pd.DataFrame:
    """Filter stories by selected industries"""
    if not selected_industries:
        return df
    return df[df['industry'].isin(selected_industries)]


def filter_stories_by_company_size(df: pd.DataFrame, selected_sizes: List[str]) -> pd.DataFrame:
    """Filter stories by selected company sizes"""
    if not selected_sizes:
        return df
    return df[df['company_size'].isin(selected_sizes)]


def search_stories(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    """Search stories by customer name, title, or content"""
    if not search_term.strip():
        return df
    
    search_term = search_term.lower()
    mask = (
        df['customer_name'].str.lower().str.contains(search_term, na=False) |
        df['title'].str.lower().str.contains(search_term, na=False) |
        df['content'].str.lower().str.contains(search_term, na=False)
    )
    return df[mask]


def extract_technologies(df: pd.DataFrame) -> Dict[str, int]:
    """Extract and count all technologies mentioned in stories"""
    all_technologies = []
    
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            techs = row['extracted_data'].get('technologies_used', [])
            if isinstance(techs, list):
                all_technologies.extend(techs)
    
    return pd.Series(all_technologies).value_counts().to_dict()


def extract_business_outcomes(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract quantified business outcomes from stories"""
    outcomes = []
    
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            outcome_data = row['extracted_data'].get('quantified_business_outcomes', [])
            if isinstance(outcome_data, list):
                for outcome in outcome_data:
                    if isinstance(outcome, dict):
                        outcomes.append({
                            **outcome,
                            'customer_name': row['customer_name'],
                            'source_name': row['source_name'],
                            'industry': row['industry']
                        })
    
    return outcomes


def get_cross_analysis_data(df: pd.DataFrame, dimension1: str, dimension2: str) -> pd.DataFrame:
    """Create cross-analysis matrix data between two dimensions"""
    cross_data = []
    
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            dim1_values = row['extracted_data'].get(dimension1, [])
            dim2_values = row['extracted_data'].get(dimension2, [])
            
            # Handle single values vs lists
            if not isinstance(dim1_values, list):
                dim1_values = [dim1_values] if dim1_values else []
            if not isinstance(dim2_values, list):
                dim2_values = [dim2_values] if dim2_values else []
            
            # Create cross-combinations
            for val1 in dim1_values:
                for val2 in dim2_values:
                    if val1 and val2:
                        cross_data.append({
                            dimension1: val1,
                            dimension2: val2,
                            'customer_name': row['customer_name'],
                            'source_name': row['source_name']
                        })
    
    return pd.DataFrame(cross_data)


def calculate_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate summary statistics for the dataset"""
    total_stories = len(df)
    genai_stories = len(df[df['is_gen_ai'] == True]) if 'is_gen_ai' in df.columns else 0
    
    # Quality score statistics
    quality_scores = []
    for _, row in df.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            score = row['extracted_data'].get('content_quality_score')
            if isinstance(score, (int, float)):
                quality_scores.append(score)
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    # Date range
    date_range = {
        'earliest': df['publish_date'].min() if 'publish_date' in df.columns else None,
        'latest': df['publish_date'].max() if 'publish_date' in df.columns else None
    }
    
    return {
        'total_stories': total_stories,
        'genai_stories': genai_stories,
        'non_genai_stories': total_stories - genai_stories,
        'genai_percentage': (genai_stories / total_stories * 100) if total_stories > 0 else 0,
        'avg_quality_score': avg_quality,
        'date_range': date_range,
        'unique_industries': df['industry'].nunique() if 'industry' in df.columns else 0,
        'unique_sources': df['source_name'].nunique() if 'source_name' in df.columns else 0
    }