#!/usr/bin/env python3
"""
AI Customer Stories Dashboard - Modular Version
Streamlit-based web interface for exploring and analyzing AI customer stories

This is the refactored modular dashboard using the new component structure.
"""

import streamlit as st
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import core modules
from src.dashboard.core.data_loader import (
    get_database_connection, 
    load_all_stories, 
    get_source_stats, 
    get_aileron_analytics
)
from src.dashboard.core.config import PAGE_CONFIG, DASHBOARD_PAGES

# Import page modules
from src.dashboard.pages.overview import show_overview
from src.dashboard.pages.explorer import show_story_explorer  
from src.dashboard.pages.analytics import show_analytics
from src.dashboard.pages.aileron import show_aileron_insights
from src.dashboard.pages.export import show_data_export

# Import brand styling
sys.path.insert(0, os.path.dirname(__file__))
from brand_styles import apply_brand_styling

# Configure Streamlit page
st.set_page_config(**PAGE_CONFIG)


def main():
    """Main dashboard application"""
    
    # Apply brand styling
    apply_brand_styling()
    
    # Sidebar navigation
    st.sidebar.title("🤖 AI Stories Dashboard")
    page = st.sidebar.selectbox("Navigate to:", DASHBOARD_PAGES)
    
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


# Add diagnostic tools for development
if __name__ == "__main__":
    main()