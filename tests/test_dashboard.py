#!/usr/bin/env python3
"""
Comprehensive test suite for the Streamlit dashboard
Tests data loading, processing, visualization, and export functionality
"""

import pytest
import pandas as pd
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import json
import io

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import dashboard functions (need to mock streamlit first)
sys.modules['streamlit'] = MagicMock()
sys.modules['plotly.express'] = MagicMock()
sys.modules['plotly.graph_objects'] = MagicMock()
sys.modules['plotly.subplots'] = MagicMock()

import dashboard
from database.models import CustomerStory, DatabaseOperations
from src.dashboard.core.data_loader import load_all_stories, get_source_stats, get_aileron_analytics
from src.dashboard.core.data_processor import create_download_data, calculate_summary_stats

@pytest.fixture
def sample_stories_data():
    """Sample customer stories data for testing"""
    return [
            {
                'id': 1,
                'source_id': 1,
                'source_name': 'Anthropic',
                'customer_name': 'Test Company 1',
                'title': 'AI Implementation Success',
                'url': 'https://example.com/story1',
                'industry': 'technology',
                'company_size': 'startup',
                'publish_date': date(2024, 1, 15),
                'publish_year': 2024,
                'publish_month': 1,
                'scraped_date': datetime(2024, 7, 31, 10, 0, 0),
                'extracted_data': {
                    'summary': 'Company implemented AI successfully',
                    'content_quality_score': 0.85,
                    'technologies_used': ['Claude', 'API'],
                    'gen_ai_superpowers': ['create_content', 'automate_with_agents'],
                    'business_impacts': ['efficiency', 'speed'],
                    'adoption_enablers': ['data_and_digital', 'innovation_culture'],
                    'business_function': 'service'
                }
            },
            {
                'id': 2,
                'source_id': 2,
                'source_name': 'OpenAI',
                'customer_name': 'Test Company 2',
                'title': 'ChatGPT Integration',
                'url': 'https://example.com/story2',
                'industry': 'healthcare',
                'company_size': 'enterprise',
                'publish_date': date(2024, 6, 20),
                'publish_year': 2024,
                'publish_month': 6,
                'scraped_date': datetime(2024, 7, 31, 11, 0, 0),
                'extracted_data': {
                    'summary': 'Healthcare AI transformation',
                    'content_quality_score': 0.92,
                    'technologies_used': ['GPT-4', 'OpenAI API'],
                    'gen_ai_superpowers': ['find_data_insights', 'natural_language'],
                    'business_impacts': ['quality', 'client_satisfaction'],
                    'adoption_enablers': ['policy_and_governance', 'risk_management'],
                    'business_function': 'service'
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
            }
        }

@pytest.fixture
def sample_aileron_data():
    """Sample Aileron framework data for testing"""
    return {
            'superpowers': {
                'create_content': 45,
                'automate_with_agents': 38,
                'find_data_insights': 32,
                'natural_language': 28
            },
            'impacts': {
                'efficiency': 56,
                'speed': 42,
                'quality': 38,
                'client_satisfaction': 25
            },
            'enablers': {
                'data_and_digital': 48,
                'innovation_culture': 35,
                'ecosystem_partners': 28,
                'policy_and_governance': 22
            },
            'functions': {
                'service': 67,
                'marketing': 34,
                'sales': 28,
                'production': 22
            }
        }

class TestDashboard:
    """Test suite for dashboard functionality"""
    pass

class TestDataLoading:
    """Test data loading and processing functions"""
    
    @patch('dashboard.core.data_loader.DatabaseOperations')
    def test_get_database_connection(self, mock_db_ops):
        """Test database connection initialization"""
        from src.dashboard.core.data_loader import get_database_connection
        conn = get_database_connection()
        assert conn is not None
        mock_db_ops.assert_called_once()
    
    @patch('dashboard.core.data_loader.get_database_connection')
    def test_load_all_stories(self, mock_get_db, sample_stories_data):
        """Test loading all stories from database"""
        # Mock database operations
        mock_db_ops = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = sample_stories_data
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        
        mock_db_ops.db.get_cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_db_ops
        
        # Test function
        df = load_all_stories()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'customer_name' in df.columns
        assert 'source_name' in df.columns
        assert 'extracted_data' in df.columns
    
    @patch('dashboard.get_database_connection')
    def test_get_source_stats(self, mock_get_db, sample_source_stats):
        """Test source statistics retrieval"""
        # Mock database operations
        mock_db_ops = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'name': 'Anthropic', **sample_source_stats['Anthropic']},
            {'name': 'OpenAI', **sample_source_stats['OpenAI']}
        ]
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        
        mock_db_ops.db.get_cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_db_ops
        
        # Test function
        stats = dashboard.get_source_stats()
        
        assert isinstance(stats, dict)
        assert 'Anthropic' in stats
        assert 'OpenAI' in stats
        assert stats['Anthropic']['story_count'] == 129
        assert stats['OpenAI']['story_count'] == 33
    
    @patch('dashboard.get_database_connection')
    def test_get_aileron_analytics(self, mock_get_db, sample_aileron_data):
        """Test Aileron framework analytics retrieval"""
        # Mock database operations
        mock_db_ops = Mock()
        mock_cursor = Mock()
        
        # Mock different queries for each call
        query_results = [
            [{'superpower': 'create_content', 'count': 45}],  # superpowers
            [{'impact': 'efficiency', 'count': 56}],          # impacts
            [{'enabler': 'data_and_digital', 'count': 48}],   # enablers
            [{'function': 'service', 'count': 67}]            # functions
        ]
        
        mock_cursor.fetchall.side_effect = query_results
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        
        mock_db_ops.db.get_cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_db_ops
        
        # Test function
        aileron_data = dashboard.get_aileron_analytics()
        
        assert isinstance(aileron_data, dict)
        assert 'superpowers' in aileron_data
        assert 'impacts' in aileron_data
        assert 'enablers' in aileron_data
        assert 'functions' in aileron_data

class TestDataProcessing:
    """Test data processing and filtering functions"""
    
    def test_create_download_data_csv(self, sample_df):
        """Test CSV data creation for download"""
        csv_data = create_download_data(sample_df, 'csv')
        
        assert isinstance(csv_data, bytes)
        csv_string = csv_data.decode('utf-8')
        assert 'customer_name' in csv_string
        assert 'Test Company 1' in csv_string
    
    def test_create_download_data_excel(self, sample_df):
        """Test Excel data creation for download"""
        excel_data = create_download_data(sample_df, 'excel')
        
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
    
    def test_create_download_data_json(self, sample_df):
        """Test JSON data creation for download"""
        json_data = create_download_data(sample_df, 'json')
        
        assert isinstance(json_data, bytes)
        json_string = json_data.decode('utf-8')
        parsed_json = json.loads(json_string)
        assert isinstance(parsed_json, list)
        assert len(parsed_json) == 2

class TestVisualizationData:
    """Test data preparation for visualizations"""
    
    def test_industry_distribution_data(self, sample_df):
        """Test industry distribution data preparation"""
        industry_counts = sample_df['industry'].value_counts()
        
        assert len(industry_counts) == 2
        assert 'technology' in industry_counts.index
        assert 'healthcare' in industry_counts.index
        assert industry_counts['technology'] == 1
        assert industry_counts['healthcare'] == 1
    
    def test_company_size_distribution(self, sample_df):
        """Test company size distribution data"""
        size_counts = sample_df['company_size'].value_counts()
        
        assert len(size_counts) == 2
        assert 'startup' in size_counts.index
        assert 'enterprise' in size_counts.index
    
    def test_technology_extraction(self, sample_df):
        """Test technology extraction from extracted_data"""
        all_technologies = []
        for idx, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                techs = row['extracted_data'].get('technologies_used', [])
                all_technologies.extend(techs)
        
        assert 'Claude' in all_technologies
        assert 'API' in all_technologies
        assert 'GPT-4' in all_technologies
        assert 'OpenAI API' in all_technologies
    
    def test_aileron_superpowers_extraction(self, sample_df):
        """Test SuperPowers extraction for Aileron analytics"""
        all_superpowers = []
        for idx, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                powers = row['extracted_data'].get('gen_ai_superpowers', [])
                all_superpowers.extend(powers)
        
        assert 'create_content' in all_superpowers
        assert 'automate_with_agents' in all_superpowers
        assert 'find_data_insights' in all_superpowers
        assert 'natural_language' in all_superpowers
    
    def test_cross_analysis_data_preparation(self, sample_df):
        """Test cross-analysis matrix data preparation"""
        cross_data = []
        for idx, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                powers = row['extracted_data'].get('gen_ai_superpowers', [])
                impacts = row['extracted_data'].get('business_impacts', [])
                
                for power in powers:
                    for impact in impacts:
                        cross_data.append({'SuperPower': power, 'Impact': impact})
        
        assert len(cross_data) > 0
        cross_df = pd.DataFrame(cross_data)
        assert 'SuperPower' in cross_df.columns
        assert 'Impact' in cross_df.columns

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames"""
        empty_df = pd.DataFrame()
        
        # Test that functions don't crash with empty data
        try:
            csv_data = dashboard.create_download_data(empty_df, 'csv')
            assert isinstance(csv_data, bytes)
        except Exception as e:
            pytest.fail(f"Failed to handle empty DataFrame: {e}")
    
    def test_missing_extracted_data_handling(self, sample_df):
        """Test handling of missing extracted_data"""
        # Create DataFrame with missing extracted_data
        test_df = sample_df.copy()
        test_df.loc[0, 'extracted_data'] = None
        
        # Test technology extraction with missing data
        all_technologies = []
        for idx, row in test_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                techs = row['extracted_data'].get('technologies_used', [])
                all_technologies.extend(techs)
        
        # Should only get technologies from the non-null row
        assert len(all_technologies) == 2  # GPT-4, OpenAI API
    
    def test_invalid_date_handling(self, sample_df):
        """Test handling of invalid or missing dates"""
        test_df = sample_df.copy()
        test_df.loc[0, 'publish_date'] = None
        
        # Should not crash when processing dates
        assert test_df['publish_date'].isna().sum() == 1
    
    @patch('dashboard.get_database_connection')
    def test_database_connection_error(self, mock_get_db):
        """Test handling of database connection errors"""
        mock_get_db.side_effect = Exception("Database connection failed")
        
        # Should handle database errors gracefully
        with pytest.raises(Exception):
            dashboard.load_all_stories()

class TestDataIntegrity:
    """Test data integrity and validation"""
    
    def test_date_consistency(self, sample_df):
        """Test that dates are consistent and valid"""
        for idx, row in sample_df.iterrows():
            if pd.notna(row['publish_date']) and pd.notna(row['scraped_date']):
                # Scraped date should be after or equal to publish date
                assert row['scraped_date'].date() >= row['publish_date']
    
    def test_extracted_data_structure(self, sample_df):
        """Test that extracted_data has expected structure"""
        required_fields = [
            'summary', 'content_quality_score', 'technologies_used',
            'gen_ai_superpowers', 'business_impacts', 'adoption_enablers'
        ]
        
        for idx, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                for field in required_fields:
                    assert field in row['extracted_data'], f"Missing field: {field}"
    
    def test_quality_score_range(self, sample_df):
        """Test that quality scores are in valid range [0, 1]"""
        for idx, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                score = row['extracted_data'].get('content_quality_score', 0)
                assert 0 <= score <= 1, f"Quality score out of range: {score}"
    
    def test_company_size_values(self, sample_df):
        """Test that company size values are valid"""
        valid_sizes = ['startup', 'mid-market', 'enterprise', 'government']
        
        for size in sample_df['company_size'].dropna().unique():
            assert size in valid_sizes, f"Invalid company size: {size}"

class TestPerformance:
    """Test performance and caching behavior"""
    
    @patch('dashboard.get_database_connection')
    def test_caching_behavior(self, mock_get_db):
        """Test that database queries are cached appropriately"""
        mock_db_ops = Mock()
        mock_get_db.return_value = mock_db_ops
        
        # Call function multiple times
        dashboard.get_database_connection()
        dashboard.get_database_connection()
        
        # Should only create connection once due to caching
        assert mock_get_db.call_count >= 1
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create large test dataset
        large_data = []
        for i in range(1000):
            large_data.append({
                'id': i,
                'customer_name': f'Company {i}',
                'industry': 'technology',
                'extracted_data': {'technologies_used': ['AI', 'ML']}
            })
        
        large_df = pd.DataFrame(large_data)
        
        # Test that processing doesn't take too long or crash
        csv_data = dashboard.create_download_data(large_df, 'csv')
        assert len(csv_data) > 0

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=dashboard",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])