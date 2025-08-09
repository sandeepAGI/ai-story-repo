#!/usr/bin/env python3
"""
Aileron GenAI Framework Page Module for AI Customer Stories Dashboard
Displays Aileron SuperPowers framework analysis with Microsoft competitive filtering
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.dashboard.core.data_loader import get_filtered_aileron_data
from src.dashboard.core.data_processor import apply_chart_formatting, get_svg_export_config, get_cross_analysis_data
from src.dashboard.core.config import AILERON_LABELS
from brand_styles import PLOTLY_COLOR_SCHEMES, get_plotly_theme


def show_aileron_insights(df: pd.DataFrame, aileron_data: Dict):
    """Display Aileron framework insights"""
    st.title("🎯 Aileron GenAI SuperPowers Framework")
    st.markdown("*Aileron Group's tool for generating and prioritizing opportunities*")
    
    # Microsoft filter toggle
    st.markdown("### 🔍 Microsoft Analysis Filter")
    microsoft_filter = st.radio(
        "Analyze stories from:",
        ["All Gen AI Stories", "Microsoft Only", "Non-Microsoft Only"],
        horizontal=True,
        help="Filter analysis to focus on Microsoft AI implementations vs other providers"
    )
    
    # Apply Microsoft filter to dataframe
    if microsoft_filter == "Microsoft Only":
        df_filtered = df[(df['is_gen_ai'] == True) & (df['source_name'] == 'Microsoft')].copy()
        filter_suffix = " (Microsoft Only)"
    elif microsoft_filter == "Non-Microsoft Only":
        df_filtered = df[(df['is_gen_ai'] == True) & (df['source_name'] != 'Microsoft')].copy()
        filter_suffix = " (Non-Microsoft Only)"
    else:
        df_filtered = df[df['is_gen_ai'] == True].copy()
        filter_suffix = ""
    
    # Show current filter stats
    _display_filter_metrics(df, df_filtered)
    
    st.markdown("---")
    
    # Check if we have data after filtering
    if len(df_filtered) == 0:
        st.warning(f"No Gen AI stories found for '{microsoft_filter}' filter.")
        return
        
    # Recalculate aileron_data based on filtered dataset
    filtered_aileron_data = get_filtered_aileron_data(df_filtered)
    
    if not any(filtered_aileron_data.values()):
        st.warning("No Aileron framework data found for the selected filter.")
        return
    
    # SuperPowers analysis
    _display_superpowers_analysis(filtered_aileron_data, filter_suffix)
    
    # Business Impacts and Functions
    _display_impacts_and_functions(filtered_aileron_data, filter_suffix)
    
    # Adoption Enablers
    _display_adoption_enablers(filtered_aileron_data, filter_suffix)
    
    # Cross-analysis matrix
    _display_cross_analysis(df_filtered, filter_suffix)


def _display_filter_metrics(df: pd.DataFrame, df_filtered: pd.DataFrame):
    """Display metrics for current filter"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Filtered Stories", len(df_filtered), f"of {len(df[df['is_gen_ai'] == True])} Gen AI total")
    
    with col2:
        if len(df_filtered) > 0:
            providers = df_filtered['source_name'].nunique()
            st.metric("AI Providers", providers)
    
    with col3:
        if len(df_filtered) > 0:
            companies = df_filtered['customer_name'].nunique()
            st.metric("Unique Companies", companies)


def _display_superpowers_analysis(filtered_aileron_data: Dict, filter_suffix: str):
    """Display SuperPowers analysis with icons"""
    st.subheader("🔗 SuperPowers (Drive) - AI Capabilities Being Used")
    st.markdown("*What AI capabilities are being deployed*")
    
    if filtered_aileron_data['superpowers']:
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
        
        powers_df = pd.DataFrame(list(filtered_aileron_data['superpowers'].items()), 
                                columns=['SuperPower', 'Count'])
        powers_df['Display_Name'] = powers_df['SuperPower'].map(
            lambda x: superpower_icons.get(x, f"❓ {x.replace('_', ' ').title()}")
        )
        
        fig = px.bar(
            powers_df,
            x='Display_Name',
            y='Count',
            color='Count',
            color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues']
        )
        apply_chart_formatting(fig, "SuperPowers Distribution")
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_xaxes(tickangle=45, title_text="")
        fig.update_yaxes(title_text="")
        fig.update_coloraxes(colorbar_title="Count")
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("SuperPowers_Distribution"))
    
    else:
        st.info("No SuperPowers data available for the selected filter.")


def _display_impacts_and_functions(filtered_aileron_data: Dict, filter_suffix: str):
    """Display Business Impacts and Business Functions analysis"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Business Impacts (Constrain) - Outcomes Achieved")
        st.markdown("*What business value is being delivered*")
        
        if filtered_aileron_data['impacts']:
            # Add icons for business impacts
            impact_icons = {
                'innovation': '🚀 Innovation',
                'efficiency': '⚡ Efficiency',
                'speed': '💨 Speed',
                'quality': '⭐ Quality',
                'client_satisfaction': '😊 Client Satisfaction',
                'risk_reduction': '🛡️ Risk Reduction'
            }
            
            impacts_df = pd.DataFrame(list(filtered_aileron_data['impacts'].items()), 
                                    columns=['Impact', 'Count'])
            impacts_df['Display_Name'] = impacts_df['Impact'].map(
                lambda x: impact_icons.get(x, f"📈 {x.replace('_', ' ').title()}")
            )
            
            fig = px.bar(
                impacts_df,
                x='Count',
                y='Display_Name',
                orientation='h',
                color='Count',
                color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues']
            )
            apply_chart_formatting(fig, "Business Impacts Distribution")
            fig.update_layout(get_plotly_theme()['layout'])
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            fig.update_coloraxes(colorbar_title="Count")
            st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Business_Impacts"))
        
        else:
            st.info("No Business Impacts data available")
    
    with col2:
        st.subheader("🏢 Business Function (Context) - Where Applied")
        st.markdown("*Which business areas are using AI*")
        
        if filtered_aileron_data['functions']:
            # Add icons for business functions
            function_icons = {
                'marketing': '📢 Marketing',
                'sales': '💼 Sales', 
                'production': '🏭 Production',
                'distribution': '🚚 Distribution',
                'service': '🤝 Service',
                'finance_and_accounting': '💰 Finance & Accounting'
            }
            
            functions_df = pd.DataFrame(list(filtered_aileron_data['functions'].items()), 
                                      columns=['Function', 'Count'])
            functions_df['Display_Name'] = functions_df['Function'].map(
                lambda x: function_icons.get(x, f"🏢 {x.replace('_', ' ').title()}")
            )
            
            fig = px.pie(
                functions_df,
                values='Count',
                names='Display_Name',
                color_discrete_sequence=PLOTLY_COLOR_SCHEMES['diverse_discrete']
            )
            apply_chart_formatting(fig, "Business Functions Distribution")
            fig.update_layout(get_plotly_theme()['layout'])
            st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Business_Functions"))
        
        else:
            st.info("No Business Functions data available")


def _display_adoption_enablers(filtered_aileron_data: Dict, filter_suffix: str):
    """Display Adoption Enablers analysis"""
    st.subheader("⚙️ Adoption Enablers (Constrain) - Prerequisites for Success")
    st.markdown("*What organizational factors enable successful AI adoption*")
    
    if filtered_aileron_data['enablers']:
        # Add icons for adoption enablers
        enabler_icons = {
            'data_and_digital': '💾 Data & Digital',
            'innovation_culture': '🧪 Innovation Culture',
            'ecosystem_partners': '🤝 Ecosystem Partners',
            'policy_and_governance': '📋 Policy & Governance',
            'risk_management': '🛡️ Risk Management'
        }
        
        enablers_df = pd.DataFrame(list(filtered_aileron_data['enablers'].items()), 
                                 columns=['Enabler', 'Count'])
        enablers_df['Display_Name'] = enablers_df['Enabler'].map(
            lambda x: enabler_icons.get(x, f"⚙️ {x.replace('_', ' ').title()}")
        )
        
        fig = px.bar(
            enablers_df,
            x='Display_Name',
            y='Count',
            color='Count',
            color_continuous_scale=PLOTLY_COLOR_SCHEMES['single_metric_blues']
        )
        apply_chart_formatting(fig, "Adoption Enablers Distribution")
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_xaxes(tickangle=45, title_text="")
        fig.update_yaxes(title_text="")
        fig.update_coloraxes(colorbar_title="Count")
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Adoption_Enablers"))
    
    else:
        st.info("No Adoption Enablers data available")


def _display_cross_analysis(df_filtered: pd.DataFrame, filter_suffix: str):
    """Display cross-analysis matrix"""
    st.subheader(f"🔄 Cross-Analysis: SuperPowers → Business Impacts{filter_suffix}")
    st.markdown("*Which AI capabilities deliver which business outcomes*")
    
    # Create cross-analysis data
    cross_data = []
    for _, row in df_filtered.iterrows():
        if isinstance(row.get('extracted_data'), dict):
            superpowers = row['extracted_data'].get('gen_ai_superpowers', [])
            impacts = row['extracted_data'].get('business_impacts', [])
            
            for power in superpowers:
                for impact in impacts:
                    if power and impact:
                        cross_data.append({
                            'SuperPower': power,
                            'Impact': impact,
                            'Customer': row['customer_name'],
                            'Source': row['source_name']
                        })
    
    if cross_data:
        cross_df = pd.DataFrame(cross_data)
        
        # Create pivot table for heatmap
        pivot_df = cross_df.pivot_table(
            index='SuperPower', 
            columns='Impact', 
            aggfunc='size', 
            fill_value=0
        )
        
        # Apply icon mapping for better readability
        superpower_labels = {
            'code': 'Code',
            'create_content': 'Create Content',
            'automate_with_agents': 'Agents',
            'find_data_insights': 'Data Insights',
            'research': 'Research',
            'brainstorm': 'Brainstorm',
            'natural_language': 'Natural Language'
        }
        
        impact_labels = {
            'innovation': 'Innovation',
            'efficiency': 'Efficiency',
            'speed': 'Speed',
            'quality': 'Quality',
            'client_satisfaction': 'Client Satisfaction',
            'risk_reduction': 'Risk Reduction'
        }
        
        # Rename indices and columns
        pivot_df.index = [superpower_labels.get(x, x.replace('_', ' ').title()) for x in pivot_df.index]
        pivot_df.columns = [impact_labels.get(x, x.replace('_', ' ').title()) for x in pivot_df.columns]
        
        fig = px.imshow(
            pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            aspect="auto",
            color_continuous_scale="Blues",
            text_auto=True
        )
        
        apply_chart_formatting(fig, "SuperPowers → Business Impacts Matrix")
        fig.update_layout(get_plotly_theme()['layout'])
        fig.update_xaxes(title_text="Business Impacts")
        fig.update_yaxes(title_text="SuperPowers")
        
        st.plotly_chart(fig, use_container_width=True, config=get_svg_export_config("Cross_Analysis_Matrix"))
        
        # Show top combinations
        st.markdown("**🏆 Top SuperPower → Impact Combinations:**")
        combination_counts = cross_df.groupby(['SuperPower', 'Impact']).size().reset_index(name='Count')
        top_combinations = combination_counts.nlargest(5, 'Count')
        
        for _, row in top_combinations.iterrows():
            superpower = superpower_labels.get(row['SuperPower'], row['SuperPower'].replace('_', ' ').title())
            impact = impact_labels.get(row['Impact'], row['Impact'].replace('_', ' ').title())
            st.write(f"• **{superpower}** → **{impact}**: {row['Count']} stories")
    
    else:
        st.info("No cross-analysis data available for the selected filter.")