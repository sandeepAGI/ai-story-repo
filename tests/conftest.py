#!/usr/bin/env python3
"""
Shared test configuration and fixtures
Provides common test setup for the AI Customer Stories test suite
"""

import pytest
import pandas as pd
import sys
import os
from datetime import datetime, date
from unittest.mock import Mock, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_stories_data():
    """Sample customer stories data for testing"""
    return [
        {
            'id': 1,
            'source_id': 1,
            'source_name': 'Anthropic',
            'customer_name': 'Test Company 1',
            'title': 'AI Implementation Success with Claude',
            'url': 'https://example.com/story1',
            'industry': 'technology',
            'company_size': 'startup',
            'publish_date': date(2024, 1, 15),
            'publish_year': 2024,
            'publish_month': 1,
            'scraped_date': datetime(2024, 7, 31, 10, 0, 0),
            'is_gen_ai': True,
            'content': 'This company implemented Claude AI for customer service automation...',
            'extracted_data': {
                'summary': 'Company implemented Claude AI successfully for customer service',
                'content_quality_score': 0.85,
                'ai_type': 'GenAI',
                'technologies_used': ['Claude', 'API', 'Anthropic'],
                'gen_ai_superpowers': ['create_content', 'automate_with_agents'],
                'business_impacts': ['efficiency', 'speed'],
                'adoption_enablers': ['data_and_digital', 'innovation_culture'],
                'business_function': 'service',
                'quantified_business_outcomes': [
                    {
                        'type': 'cost_savings',
                        'value': 100000,
                        'unit': 'USD',
                        'description': '40% reduction in customer service costs'
                    }
                ]
            }
        },
        {
            'id': 2,
            'source_id': 2,
            'source_name': 'OpenAI',
            'customer_name': 'Test Company 2', 
            'title': 'ChatGPT Integration for Healthcare',
            'url': 'https://example.com/story2',
            'industry': 'healthcare',
            'company_size': 'enterprise',
            'publish_date': date(2024, 6, 20),
            'publish_year': 2024,
            'publish_month': 6,
            'scraped_date': datetime(2024, 7, 31, 11, 0, 0),
            'is_gen_ai': True,
            'content': 'Healthcare provider uses GPT-4 for medical documentation...',
            'extracted_data': {
                'summary': 'Healthcare AI transformation with GPT-4',
                'content_quality_score': 0.92,
                'ai_type': 'GenAI',
                'technologies_used': ['GPT-4', 'OpenAI API', 'ChatGPT'],
                'gen_ai_superpowers': ['find_data_insights', 'natural_language'],
                'business_impacts': ['quality', 'client_satisfaction'],
                'adoption_enablers': ['policy_and_governance', 'risk_management'],
                'business_function': 'service',
                'quantified_business_outcomes': [
                    {
                        'type': 'time_savings',
                        'value': 50,
                        'unit': 'percent',
                        'description': '50% faster medical documentation'
                    }
                ]
            }
        },
        {
            'id': 3,
            'source_id': 3,
            'source_name': 'Microsoft',
            'customer_name': 'Test Company 3',
            'title': 'Traditional ML Implementation',
            'url': 'https://example.com/story3',
            'industry': 'financial_services',
            'company_size': 'enterprise',
            'publish_date': date(2023, 12, 10),
            'publish_year': 2023,
            'publish_month': 12,
            'scraped_date': datetime(2024, 7, 31, 12, 0, 0),
            'is_gen_ai': False,
            'content': 'Traditional machine learning for fraud detection...',
            'extracted_data': {
                'summary': 'Traditional ML for fraud detection',
                'content_quality_score': 0.78,
                'ai_type': 'Non-GenAI',
                'technologies_used': ['Azure ML', 'Python', 'Scikit-learn'],
                'business_outcomes': [
                    {
                        'type': 'fraud_reduction',
                        'value': 25,
                        'unit': 'percent',
                        'description': '25% reduction in fraudulent transactions'
                    }
                ]
            }
        }
    ]


@pytest.fixture
def sample_df(sample_stories_data):
    """Sample DataFrame for testing"""
    return pd.DataFrame(sample_stories_data)


@pytest.fixture
def sample_source_stats():
    """Sample source statistics for testing"""
    return {
        'Anthropic': {
            'story_count': 129,
            'earliest_story': date(2024, 2, 17),
            'latest_story': date(2025, 7, 23),
            'estimated_dates': 0,
            'avg_quality_score': 0.84
        },
        'OpenAI': {
            'story_count': 33,
            'earliest_story': date(2024, 12, 11),
            'latest_story': date(2025, 7, 17),
            'estimated_dates': 0,
            'avg_quality_score': 0.89
        },
        'Microsoft': {
            'story_count': 648,
            'earliest_story': date(2020, 1, 1),
            'latest_story': date(2025, 7, 20),
            'estimated_dates': 50,
            'avg_quality_score': 0.76
        }
    }


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for testing"""
    # Mock all streamlit modules that might be imported
    sys.modules['streamlit'] = MagicMock()
    sys.modules['plotly.express'] = MagicMock()
    sys.modules['plotly.graph_objects'] = MagicMock()
    sys.modules['plotly.subplots'] = MagicMock()
    return sys.modules['streamlit']


@pytest.fixture
def mock_database_operations():
    """Mock database operations for testing"""
    mock_db_ops = Mock()
    mock_cursor = Mock()
    
    # Setup cursor context manager
    mock_cursor.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor.__exit__ = Mock(return_value=None)
    
    mock_db_ops.db.get_cursor.return_value = mock_cursor
    return mock_db_ops, mock_cursor


@pytest.fixture  
def classification_test_cases():
    """Test cases for AI classification testing"""
    return {
        'definitive_genai': [
            {
                'title': 'Company uses GPT-4 for customer service',
                'content': 'Implementation of gpt-4 for automated responses and chat',
                'expected_classification': 'GenAI',
                'expected_confidence': 'medium'  # Only 1 keyword match
            },
            {
                'title': 'Claude integration for document analysis', 
                'content': 'document processing with claude ai for insights and automation',
                'expected_classification': 'GenAI',
                'expected_confidence': 'medium'  # 1 keyword match
            },
            {
                'title': 'LLM-powered content generation',
                'content': 'large language model generates marketing content automatically',
                'expected_classification': 'GenAI',
                'expected_confidence': 'high'  # 2 keyword matches (llm + large language model)
            }
        ],
        'definitive_non_genai': [
            {
                'title': 'Traditional ML for fraud detection',
                'content': 'machine learning algorithms for fraud detection using historical data',
                'expected_classification': 'Non-GenAI',
                'expected_confidence': 'high'
            },
            {
                'title': 'Computer vision for quality control',
                'content': 'image recognition system for manufacturing quality control',
                'expected_classification': 'Non-GenAI',
                'expected_confidence': 'high'
            }
        ],
        'edge_cases': [
            {
                'title': 'AI-powered analytics platform',
                'content': 'advanced analytics using artificial intelligence for business insights',
                'expected_classification': 'Non-GenAI',
                'expected_confidence': 'medium'
            },
            {
                'title': 'Intelligent automation system',
                'content': 'automated system with intelligent decision making capabilities',
                'expected_classification': 'Non-GenAI', 
                'expected_confidence': 'low'
            }
        ]
    }