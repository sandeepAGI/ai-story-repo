#!/usr/bin/env python3
"""
Data Loading Module for AI Customer Stories Dashboard
Handles all database operations with caching for optimal performance
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
import sys
import os

# Add src directory to path for database imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database.models import DatabaseOperations


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


def get_filtered_aileron_data(df_filtered: pd.DataFrame) -> Dict:
    """Get Aileron framework analytics from filtered DataFrame"""
    # SuperPowers analysis
    all_superpowers = []
    for idx, row in df_filtered.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            superpowers = row['extracted_data'].get('gen_ai_superpowers', [])
            if isinstance(superpowers, list):
                all_superpowers.extend(superpowers)
    
    superpower_counts = pd.Series(all_superpowers).value_counts().to_dict()
    
    # Business Impacts analysis
    all_impacts = []
    for idx, row in df_filtered.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            impacts = row['extracted_data'].get('business_impacts', [])
            if isinstance(impacts, list):
                all_impacts.extend(impacts)
    
    impact_counts = pd.Series(all_impacts).value_counts().to_dict()
    
    # Adoption Enablers analysis
    all_enablers = []
    for idx, row in df_filtered.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            enablers = row['extracted_data'].get('adoption_enablers', [])
            if isinstance(enablers, list):
                all_enablers.extend(enablers)
    
    enabler_counts = pd.Series(all_enablers).value_counts().to_dict()
    
    # Business Function analysis
    all_functions = []
    for idx, row in df_filtered.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            function = row['extracted_data'].get('business_function')
            if function:
                all_functions.append(function)
    
    function_counts = pd.Series(all_functions).value_counts().to_dict()
    
    return {
        'superpowers': superpower_counts,
        'impacts': impact_counts,
        'enablers': enabler_counts,
        'functions': function_counts
    }