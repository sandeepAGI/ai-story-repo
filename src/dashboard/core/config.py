#!/usr/bin/env python3
"""
Dashboard Configuration
Central configuration for the AI Customer Stories Dashboard
"""

# Cache settings
CACHE_TTL = 300  # 5 minutes

# Chart formatting
MAX_CHART_TITLE_LENGTH = 50
CHART_HEIGHT = 400
CHART_WIDTH = 600

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "AI Customer Stories Dashboard",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Dashboard sections
DASHBOARD_PAGES = [
    "📊 Overview",
    "🔍 Story Explorer", 
    "📈 Analytics",
    "🎯 Aileron Insights",
    "💾 Data Export"
]

# Filter options
COMPANY_SIZES = ['startup', 'mid-market', 'enterprise', 'government']

# Aileron framework labels
AILERON_LABELS = {
    'superpowers': {
        'code': 'Code Generation',
        'create_content': 'Content Creation', 
        'automate_with_agents': 'Agent Automation',
        'find_data_insights': 'Data Insights',
        'research': 'Research & Analysis',
        'brainstorm': 'Brainstorming',
        'natural_language': 'Natural Language'
    },
    'impacts': {
        'innovation': 'Innovation',
        'efficiency': 'Efficiency',
        'speed': 'Speed',
        'quality': 'Quality', 
        'client_satisfaction': 'Client Satisfaction',
        'risk_reduction': 'Risk Reduction'
    },
    'enablers': {
        'data_and_digital': 'Data & Digital',
        'innovation_culture': 'Innovation Culture',
        'ecosystem_partners': 'Ecosystem Partners',
        'policy_and_governance': 'Policy & Governance',
        'risk_management': 'Risk Management'
    },
    'functions': {
        'marketing': 'Marketing',
        'sales': 'Sales',
        'production': 'Production',
        'distribution': 'Distribution',
        'service': 'Service',
        'finance_and_accounting': 'Finance & Accounting'
    }
}

# Export formats
EXPORT_FORMATS = {
    'csv': 'CSV',
    'excel': 'Excel (XLSX)',
    'json': 'JSON'
}

# Chart export configuration
SVG_EXPORT_CONFIG = {
    'width': 800,
    'height': 600,
    'scale': 2
}