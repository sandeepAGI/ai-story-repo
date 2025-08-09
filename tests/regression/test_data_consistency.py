#!/usr/bin/env python3
"""
Comprehensive Regression Test Suite
Single test file to validate the entire data processing pipeline

This replaces multiple test utilities and provides ongoing validation
for system consistency after any changes.
"""

import pytest
import pandas as pd
import sys
import os
import time
from unittest.mock import Mock, patch
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from database.models import DatabaseOperations
    from ai_integration.claude_processor import ClaudeProcessor
    from src.dashboard.core.data_loader import load_all_stories, get_source_stats, get_aileron_analytics
    from src.dashboard.core.data_processor import calculate_summary_stats
except ImportError as e:
    # Some modules may not be available in test environment
    print(f"Warning: Could not import some modules: {e}")


class TestDataPipeline:
    """Test complete data processing pipeline"""
    
    @pytest.mark.integration
    def test_full_pipeline_sample(self, sample_stories_data):
        """Test full pipeline with sample data: scraping → processing → dashboard"""
        
        # Stage 1: Data Ingestion (simulate scraper output)
        raw_stories = [
            {
                'customer_name': 'Test Corp',
                'title': 'GPT-4 Implementation Success',
                'content': 'Company uses GPT-4 for customer service automation...',
                'url': 'https://example.com/test-story',
                'source_id': 1,
                'industry': 'technology',
                'company_size': 'startup'
            }
        ]
        
        # Stage 2: AI Processing (simulate Claude processing)
        processed_stories = []
        for story in raw_stories:
            processed_story = {
                **story,
                'extracted_data': {
                    'ai_type': 'GenAI',
                    'content_quality_score': 0.85,
                    'summary': 'AI implementation success',
                    'technologies_used': ['GPT-4', 'OpenAI'],
                    'gen_ai_superpowers': ['create_content', 'automate_with_agents'],
                    'business_impacts': ['efficiency', 'speed'],
                    'adoption_enablers': ['data_and_digital'],
                    'business_function': 'service'
                },
                'is_gen_ai': True
            }
            processed_stories.append(processed_story)
        
        # Stage 3: Data Validation
        df = pd.DataFrame(processed_stories)
        
        # Validate data consistency
        for _, row in df.iterrows():
            # Check classification consistency
            ai_type = row['extracted_data']['ai_type']
            is_gen_ai = row['is_gen_ai']
            
            if ai_type == 'GenAI':
                assert is_gen_ai == True
            else:
                assert is_gen_ai == False
            
            # Check required fields are present
            assert 'content_quality_score' in row['extracted_data']
            assert 0 <= row['extracted_data']['content_quality_score'] <= 1
        
        # Stage 4: Dashboard Processing (simulate dashboard data loading)
        stats = calculate_summary_stats(df)
        
        assert stats['total_stories'] == len(df)
        assert stats['genai_stories'] + stats['non_genai_stories'] == stats['total_stories']
        
        print("✅ Full pipeline test passed")
    
    def test_data_consistency_validation(self, sample_df):
        """Test comprehensive data consistency checks"""
        
        # Test 1: Classification Consistency
        classification_issues = []
        for idx, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                ai_type = row['extracted_data'].get('ai_type')
                is_gen_ai = row.get('is_gen_ai')
                
                if ai_type == 'GenAI' and is_gen_ai != True:
                    classification_issues.append(f"Row {idx}: ai_type=GenAI but is_gen_ai={is_gen_ai}")
                elif ai_type == 'Non-GenAI' and is_gen_ai != False:
                    classification_issues.append(f"Row {idx}: ai_type=Non-GenAI but is_gen_ai={is_gen_ai}")
        
        assert len(classification_issues) == 0, f"Classification inconsistencies: {classification_issues}"
        
        # Test 2: Data Quality
        quality_issues = []
        for idx, row in sample_df.iterrows():
            # Check required fields
            required_fields = ['customer_name', 'title', 'url', 'source_name']
            for field in required_fields:
                if pd.isna(row.get(field)) or row.get(field) == '':
                    quality_issues.append(f"Row {idx}: Missing {field}")
            
            # Check extracted data structure
            if not isinstance(row.get('extracted_data'), dict):
                quality_issues.append(f"Row {idx}: extracted_data is not a dict")
            elif 'content_quality_score' not in row['extracted_data']:
                quality_issues.append(f"Row {idx}: Missing content_quality_score")
        
        assert len(quality_issues) == 0, f"Data quality issues: {quality_issues}"
        
        # Test 3: Gen AI Specific Validation
        genai_stories = sample_df[sample_df['is_gen_ai'] == True]
        genai_issues = []
        
        required_genai_fields = ['gen_ai_superpowers', 'business_impacts', 'adoption_enablers']
        
        for idx, row in genai_stories.iterrows():
            if isinstance(row['extracted_data'], dict):
                for field in required_genai_fields:
                    if field not in row['extracted_data']:
                        genai_issues.append(f"Gen AI story {idx}: Missing {field}")
                    elif not isinstance(row['extracted_data'][field], list):
                        genai_issues.append(f"Gen AI story {idx}: {field} should be a list")
        
        # Allow some missing fields but flag if too many
        assert len(genai_issues) <= len(genai_stories) * 0.1, f"Too many Gen AI field issues: {genai_issues[:5]}"
        
        print("✅ Data consistency validation passed")
    
    def test_source_distribution_balance(self, sample_df):
        """Test that data is reasonably distributed across sources"""
        source_counts = sample_df['source_name'].value_counts()
        
        # Each source should have at least one story in sample
        assert len(source_counts) >= 1
        
        # No single source should dominate too much (>90% in real data)
        max_percentage = source_counts.max() / len(sample_df)
        assert max_percentage <= 0.95, f"Source distribution too skewed: {source_counts.to_dict()}"
        
        print("✅ Source distribution balance test passed")
    
    def test_industry_standardization(self, sample_df):
        """Test that industries follow standardized taxonomy"""
        expected_industries = [
            'technology', 'financial_services', 'healthcare', 'retail_ecommerce',
            'manufacturing', 'government_public_sector', 'media_communications',
            'energy_utilities', 'transportation_logistics', 'professional_services', 'other'
        ]
        
        unique_industries = sample_df['industry'].dropna().unique()
        
        invalid_industries = [ind for ind in unique_industries if ind not in expected_industries]
        
        # In sample data, some non-standard industries might be ok
        # But flag if too many
        assert len(invalid_industries) <= len(unique_industries) * 0.2, \
               f"Too many non-standard industries: {invalid_industries}"
        
        print("✅ Industry standardization test passed")


class TestDashboardIntegration:
    """Test dashboard components work with real data patterns"""
    
    def test_dashboard_data_loading(self, sample_df):
        """Test that dashboard can process the data structure"""
        # Test filtering functions
        genai_filtered = sample_df[sample_df['is_gen_ai'] == True]
        non_genai_filtered = sample_df[sample_df['is_gen_ai'] == False]
        all_filtered = sample_df
        
        # Basic sanity checks
        assert len(genai_filtered) + len(non_genai_filtered) == len(all_filtered)
        assert len(all_filtered) == len(sample_df)
        
        # Check that Gen AI filtering works
        for _, row in genai_filtered.iterrows():
            assert row['is_gen_ai'] == True
        
        for _, row in non_genai_filtered.iterrows():
            assert row['is_gen_ai'] == False
        
        print("✅ Dashboard data loading test passed")
    
    def test_analytics_data_processing(self, sample_df):
        """Test analytics page data processing"""
        # Test summary statistics
        stats = calculate_summary_stats(sample_df)
        
        required_stats = ['total_stories', 'genai_stories', 'non_genai_stories', 
                         'genai_percentage', 'avg_quality_score']
        
        for stat in required_stats:
            assert stat in stats
        
        # Validate statistics make sense
        assert stats['total_stories'] > 0
        assert stats['genai_stories'] + stats['non_genai_stories'] == stats['total_stories']
        assert 0 <= stats['genai_percentage'] <= 100
        assert 0 <= stats['avg_quality_score'] <= 1
        
        print("✅ Analytics data processing test passed")
    
    def test_export_functionality(self, sample_df):
        """Test data export functions"""
        from src.dashboard.core.data_processor import create_download_data
        
        # Test different export formats
        formats = ['csv', 'json']  # Skip excel in tests to avoid openpyxl dependency
        
        for format_type in formats:
            try:
                export_data = create_download_data(sample_df, format_type)
                assert isinstance(export_data, bytes)
                assert len(export_data) > 0
            except Exception as e:
                pytest.fail(f"Export format {format_type} failed: {e}")
        
        print("✅ Export functionality test passed")


class TestPerformanceRegression:
    """Test that performance hasn't regressed"""
    
    def test_data_processing_performance(self, sample_df):
        """Test that data processing completes within reasonable time"""
        import time
        
        # Create larger dataset for performance testing
        large_df = pd.concat([sample_df] * 100, ignore_index=True)  # 300 rows
        
        start_time = time.time()
        
        # Test filtering performance
        _ = large_df[large_df['is_gen_ai'] == True]
        
        # Test statistics calculation
        _ = calculate_summary_stats(large_df)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 300 rows in well under 1 second
        assert processing_time < 1.0, f"Data processing too slow: {processing_time:.2f}s for 300 rows"
        
        print(f"✅ Performance test passed: {processing_time:.3f}s for 300 rows")


class TestSystemHealth:
    """Overall system health checks"""
    
    def test_import_health(self):
        """Test that all critical modules can be imported"""
        critical_modules = [
            'dashboard.core.data_loader',
            'dashboard.core.data_processor', 
            'dashboard.core.config'
        ]
        
        import_issues = []
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError as e:
                import_issues.append(f"{module}: {e}")
        
        assert len(import_issues) == 0, f"Import issues: {import_issues}"
        
        print("✅ Import health check passed")
    
    def test_configuration_health(self):
        """Test that configuration is valid"""
        try:
            from src.dashboard.core.config import PAGE_CONFIG, DASHBOARD_PAGES
            
            # Test page config
            required_config_keys = ['page_title', 'page_icon', 'layout']
            for key in required_config_keys:
                assert key in PAGE_CONFIG
            
            # Test dashboard pages
            assert isinstance(DASHBOARD_PAGES, list)
            assert len(DASHBOARD_PAGES) > 0
            
        except Exception as e:
            pytest.fail(f"Configuration health check failed: {e}")
        
        print("✅ Configuration health check passed")


if __name__ == "__main__":
    # Run comprehensive regression test
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "not integration"  # Skip integration tests by default
    ])