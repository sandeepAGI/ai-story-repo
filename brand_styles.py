#!/usr/bin/env python3
"""
Brand Styling Configuration for AI Customer Stories Dashboard
Integrates company brand colors and Montserrat font
"""

import streamlit as st

# Brand Color Palette
BRAND_COLORS = {
    'primary_dark': '#2D2042',    # Main navigation, headers
    'primary_blue': '#60B5E5',    # Interactive elements, key metrics
    'light_blue': '#B3DCF3',      # Secondary elements, hover states
    'light_gray': '#F2F2F2',      # Backgrounds, subtle elements
    'white': '#FFFFFF',
    'text_dark': '#2D2042',
    'text_light': '#FFFFFF'
}

# Plotly Color Schemes
PLOTLY_COLOR_SCHEMES = {
    # Keep brand colors for specific 2-category charts (Gen AI vs Non Gen AI)
    'gen_ai_colors': {'Gen AI': BRAND_COLORS['primary_blue'], 'Non Gen AI': BRAND_COLORS['light_blue']},
    
    # Mixed brand/diverse colors for moderate-sized category sets
    'primary_discrete': [BRAND_COLORS['primary_blue'], BRAND_COLORS['primary_dark'], 
                        BRAND_COLORS['light_blue'], '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
    
    # Use diverse color palettes for multi-category charts
    'diverse_discrete': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
    'qualitative_set1': ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF', '#999999'],
    'qualitative_set3': ['#8DD3C7', '#FFFFB3', '#BEBADA', '#FB8072', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5', '#D9D9D9'],
    
    # Single-metric continuous scales (use brand blues for single data series)
    'single_metric_blues': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3', '#1E88E5', '#1976D2'],
    'brand_continuous': [[0, BRAND_COLORS['light_gray']], [0.5, BRAND_COLORS['light_blue']], [1, BRAND_COLORS['primary_blue']]]
}

def apply_brand_styling():
    """Apply custom brand styling to Streamlit dashboard"""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');
        
        /* Global Font */
        html, body, [class*="css"] {{
            font-family: 'Montserrat', sans-serif;
        }}
        
        /* Main Container */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        /* Sidebar Styling */
        .css-1d391kg {{
            background-color: {BRAND_COLORS['primary_dark']};
        }}
        
        .css-1d391kg .css-17eq0hr {{
            color: {BRAND_COLORS['text_light']};
        }}
        
        /* Sidebar Title */
        .css-1d391kg h1 {{
            color: {BRAND_COLORS['text_light']} !important;
            font-weight: 600;
        }}
        
        /* Sidebar Selectbox */
        .css-1d391kg .stSelectbox > label {{
            color: {BRAND_COLORS['text_light']} !important;
        }}
        
        /* Main Title */
        h1 {{
            color: {BRAND_COLORS['primary_dark']} !important;
            font-weight: 600;
            border-bottom: 3px solid {BRAND_COLORS['primary_blue']};
            padding-bottom: 10px;
        }}
        
        /* Subheaders */
        h2, h3 {{
            color: {BRAND_COLORS['primary_dark']} !important;
            font-weight: 500;
        }}
        
        /* Metrics Container */
        [data-testid="metric-container"] {{
            background-color: {BRAND_COLORS['light_gray']};
            border: 1px solid {BRAND_COLORS['light_blue']};
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(45, 32, 66, 0.1);
        }}
        
        [data-testid="metric-container"] > div {{
            color: {BRAND_COLORS['primary_dark']} !important;
        }}
        
        [data-testid="metric-container"] [data-testid="metric-value"] {{
            color: {BRAND_COLORS['primary_blue']} !important;
            font-weight: 600;
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: {BRAND_COLORS['primary_blue']};
            color: {BRAND_COLORS['text_light']};
            border: none;
            border-radius: 6px;
            font-weight: 500;
            font-family: 'Montserrat', sans-serif;
        }}
        
        .stButton > button:hover {{
            background-color: {BRAND_COLORS['primary_dark']};
            color: {BRAND_COLORS['text_light']};
        }}
        
        /* Download Button */
        .stDownloadButton > button {{
            background-color: {BRAND_COLORS['primary_blue']};
            color: {BRAND_COLORS['text_light']};
            border: none;
            border-radius: 6px;
            font-weight: 500;
        }}
        
        .stDownloadButton > button:hover {{
            background-color: {BRAND_COLORS['primary_dark']};
        }}
        
        /* Radio Buttons */
        .stRadio > label {{
            color: {BRAND_COLORS['primary_dark']} !important;
            font-weight: 500;
        }}
        
        /* Selectbox */
        .stSelectbox > label {{
            color: {BRAND_COLORS['primary_dark']} !important;
            font-weight: 500;
        }}
        
        /* Text Input */
        .stTextInput > label {{
            color: {BRAND_COLORS['primary_dark']} !important;
            font-weight: 500;
        }}
        
        /* Multiselect */
        .stMultiSelect > label {{
            color: {BRAND_COLORS['primary_dark']} !important;
            font-weight: 500;
        }}
        
        /* Expandable Sections */
        .streamlit-expanderHeader {{
            background-color: {BRAND_COLORS['light_gray']};
            color: {BRAND_COLORS['primary_dark']} !important;
            font-weight: 500;
        }}
        
        /* Info/Warning/Success Boxes */
        .stInfo {{
            background-color: {BRAND_COLORS['light_blue']}20;
            border-left-color: {BRAND_COLORS['primary_blue']};
        }}
        
        .stWarning {{
            background-color: #FFF3CD;
            border-left-color: #FFC107;
        }}
        
        .stSuccess {{
            background-color: {BRAND_COLORS['light_blue']}30;
            border-left-color: {BRAND_COLORS['primary_blue']};
        }}
        
        /* DataFrame Styling */
        .dataframe {{
            border: 1px solid {BRAND_COLORS['light_blue']} !important;
        }}
        
        .dataframe thead th {{
            background-color: {BRAND_COLORS['primary_dark']} !important;
            color: {BRAND_COLORS['text_light']} !important;
            font-weight: 600;
        }}
        
        /* Progress Bar */
        .stProgress > div > div > div {{
            background-color: {BRAND_COLORS['primary_blue']};
        }}
        
        /* Section Dividers */
        hr {{
            border-color: {BRAND_COLORS['light_blue']} !important;
            margin: 2rem 0;
        }}
        
        /* Chart Containers */
        .js-plotly-plot {{
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(45, 32, 66, 0.1);
        }}
        
    </style>
    """, unsafe_allow_html=True)

def get_brand_color_discrete_map(categories):
    """Generate brand-consistent discrete color mapping for categories"""
    colors = [BRAND_COLORS['primary_blue'], BRAND_COLORS['primary_dark'], 
              BRAND_COLORS['light_blue'], '#8E8E93', '#FF9500', '#FF3B30']
    
    return {cat: colors[i % len(colors)] for i, cat in enumerate(categories)}

def get_plotly_theme():
    """Return Plotly theme configuration matching brand"""
    return {
        'layout': {
            'font': {'family': 'Montserrat, sans-serif', 'color': BRAND_COLORS['primary_dark']},
            'colorway': PLOTLY_COLOR_SCHEMES['primary_discrete'],
            'paper_bgcolor': BRAND_COLORS['white'],
            'plot_bgcolor': BRAND_COLORS['light_gray'],
            'title': {
                'font': {'size': 18, 'color': BRAND_COLORS['primary_dark'], 'family': 'Montserrat'}
            }
        }
    }

# Custom branded components
def branded_metric(label, value, delta=None, help=None):
    """Create a branded metric display"""
    delta_html = f'<div style="color: {BRAND_COLORS["primary_blue"]}; font-size: 0.8rem; margin-top: 4px;">{delta}</div>' if delta else ''
    
    return st.markdown(f"""
    <div style="
        background-color: {BRAND_COLORS['light_gray']};
        border: 1px solid {BRAND_COLORS['light_blue']};
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(45, 32, 66, 0.1);
        text-align: center;
    ">
        <div style="color: {BRAND_COLORS['primary_dark']}; font-size: 0.9rem; font-weight: 500; margin-bottom: 4px;">
            {label}
        </div>
        <div style="color: {BRAND_COLORS['primary_blue']}; font-size: 2rem; font-weight: 600;">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def branded_header(text, level=1):
    """Create a branded header with consistent styling"""
    if level == 1:
        return st.markdown(f"""
        <h1 style="
            color: {BRAND_COLORS['primary_dark']};
            font-weight: 600;
            border-bottom: 3px solid {BRAND_COLORS['primary_blue']};
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-family: 'Montserrat', sans-serif;
        ">{text}</h1>
        """, unsafe_allow_html=True)
    else:
        return st.markdown(f"""
        <h{level} style="
            color: {BRAND_COLORS['primary_dark']};
            font-weight: 500;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            font-family: 'Montserrat', sans-serif;
        ">{text}</h{level}>
        """, unsafe_allow_html=True)