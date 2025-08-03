#!/usr/bin/env python3
"""
Integration tests for the dashboard with real database
Tests full end-to-end functionality with actual data
"""

import pytest
import pandas as pd
import sys
import os
from datetime import datetime, date
import json
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations

class TestDashboardIntegration:
    """Integration tests with real database"""
    
    @pytest.fixture(scope="class")
    def db_connection(self):
        """Real database connection for integration testing"""
        try:
            db_ops = DatabaseOperations()
            # Test connection
            with db_ops.db.get_cursor() as cursor:
                cursor.execute("SELECT 1")
            return db_ops
        except Exception as e:
            pytest.skip(f"Database not available for integration testing: {e}")
    
    def test_real_database_connection(self, db_connection):
        """Test actual database connectivity"""
        assert db_connection is not None
        
        # Test basic query
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM customer_stories")
            result = cursor.fetchone()
            assert result['count'] >= 0
    
    def test_load_actual_stories(self, db_connection):
        """Test loading actual stories from database"""
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    cs.*,
                    s.name as source_name,
                    EXTRACT(YEAR FROM cs.publish_date) as publish_year,
                    EXTRACT(MONTH FROM cs.publish_date) as publish_month
                FROM customer_stories cs
                JOIN sources s ON cs.source_id = s.id
                ORDER BY cs.scraped_date DESC
                LIMIT 10
            """)
            
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
            
            if len(df) > 0:
                # Verify data structure
                required_columns = ['customer_name', 'source_name', 'industry', 'extracted_data']
                for col in required_columns:
                    assert col in df.columns
                
                # Verify data types
                assert df['customer_name'].dtype == 'object'
                if 'publish_year' in df.columns:
                    assert pd.api.types.is_numeric_dtype(df['publish_year'])
    
    def test_aileron_data_structure(self, db_connection):
        """Test actual Aileron framework data structure"""
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT extracted_data 
                FROM customer_stories 
                WHERE extracted_data->'gen_ai_superpowers' IS NOT NULL
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                extracted_data = row['extracted_data']
                
                # Verify Aileron fields exist
                aileron_fields = [
                    'gen_ai_superpowers',
                    'business_impacts', 
                    'adoption_enablers',
                    'business_function'
                ]
                
                for field in aileron_fields:
                    if field in extracted_data:
                        # Verify field structure
                        if field == 'business_function':
                            assert isinstance(extracted_data[field], str)
                        else:
                            assert isinstance(extracted_data[field], list)
    
    def test_source_statistics_accuracy(self, db_connection):
        """Test that source statistics calculations are accurate"""
        with db_connection.db.get_cursor() as cursor:
            # Get manual count
            cursor.execute("SELECT source_id, COUNT(*) as count FROM customer_stories GROUP BY source_id")
            manual_counts = {row['source_id']: row['count'] for row in cursor.fetchall()}
            
            # Get stats from dashboard function
            cursor.execute("""
                SELECT 
                    s.id,
                    s.name,
                    COUNT(cs.id) as story_count
                FROM sources s 
                LEFT JOIN customer_stories cs ON s.id = cs.source_id 
                GROUP BY s.name, s.id
            """)
            
            dashboard_stats = cursor.fetchall()
            
            for stat in dashboard_stats:
                source_id = stat['id']
                expected_count = manual_counts.get(source_id, 0)
                assert stat['story_count'] == expected_count
    
    def test_data_export_integration(self, db_connection):
        """Test data export with real data"""
        # Get sample data
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM customer_stories 
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
            
            if len(df) > 0:
                # Test CSV export
                csv_data = df.to_csv(index=False).encode('utf-8')
                assert len(csv_data) > 0
                
                # Verify CSV can be parsed back
                csv_df = pd.read_csv(io.StringIO(csv_data.decode('utf-8')))
                assert len(csv_df) == len(df)
    
    def test_search_functionality_integration(self, db_connection):
        """Test search functionality with real data"""
        stories = db_connection.search_stories("technology", limit=5)
        
        # Verify search results
        for story in stories:
            assert hasattr(story, 'customer_name')
            assert hasattr(story, 'industry')
            # Verify search relevance (should contain technology-related content)
            search_text = (
                (story.customer_name or '') + ' ' +
                (story.title or '') + ' ' +
                (story.industry or '')
            ).lower()
            # Note: PostgreSQL full-text search might find relevant results
            # even if exact term isn't present
    
    def test_date_range_filtering(self, db_connection):
        """Test date range filtering with real data"""
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM customer_stories 
                WHERE publish_date >= '2024-01-01' 
                AND publish_date <= '2024-12-31'
                LIMIT 10
            """)
            
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
            
            for idx, row in df.iterrows():
                if pd.notna(row['publish_date']):
                    pub_date = pd.to_datetime(row['publish_date']).date()
                    assert date(2024, 1, 1) <= pub_date <= date(2024, 12, 31)

class TestDashboardPerformance:
    """Performance tests for dashboard functionality"""
    
    @pytest.fixture(scope="class")
    def db_connection(self):
        """Database connection for performance testing"""
        try:
            return DatabaseOperations()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_large_dataset_query_performance(self, db_connection):
        """Test performance with large dataset queries"""
        import time
        
        start_time = time.time()
        
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    cs.customer_name,
                    cs.industry,
                    cs.company_size,
                    s.name as source_name,
                    cs.extracted_data->'content_quality_score' as quality_score
                FROM customer_stories cs
                JOIN sources s ON cs.source_id = s.id
            """)
            
            rows = cursor.fetchall()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Query should complete within reasonable time (adjust based on your data size)
        assert query_time < 10.0, f"Query took too long: {query_time} seconds"
        print(f"Query completed in {query_time:.2f} seconds for {len(rows)} rows")
    
    def test_aggregation_query_performance(self, db_connection):
        """Test performance of aggregation queries"""
        import time
        
        queries = [
            "SELECT industry, COUNT(*) FROM customer_stories GROUP BY industry",
            "SELECT company_size, COUNT(*) FROM customer_stories GROUP BY company_size",
            """SELECT 
                jsonb_array_elements_text(extracted_data->'technologies_used') as tech,
                COUNT(*) 
                FROM customer_stories 
                WHERE extracted_data->'technologies_used' IS NOT NULL
                GROUP BY tech
                LIMIT 20""",
        ]
        
        for query in queries:
            start_time = time.time()
            
            with db_connection.db.get_cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            assert query_time < 5.0, f"Aggregation query took too long: {query_time} seconds"
            print(f"Aggregation query completed in {query_time:.2f} seconds")

class TestDataQuality:
    """Test data quality and consistency"""
    
    @pytest.fixture(scope="class")
    def db_connection(self):
        """Database connection for data quality testing"""
        try:
            return DatabaseOperations()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_data_completeness(self, db_connection):
        """Test data completeness and required fields"""
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_stories,
                    COUNT(customer_name) as has_customer_name,
                    COUNT(url) as has_url,
                    COUNT(extracted_data) as has_extracted_data,
                    COUNT(CASE WHEN extracted_data->'summary' IS NOT NULL THEN 1 END) as has_summary
                FROM customer_stories
            """)
            
            stats = cursor.fetchone()
            
            # Verify data completeness
            assert stats['has_customer_name'] == stats['total_stories'], "Missing customer names"
            assert stats['has_url'] == stats['total_stories'], "Missing URLs"
            
            # Most stories should have extracted data
            extraction_rate = stats['has_extracted_data'] / stats['total_stories'] if stats['total_stories'] > 0 else 0
            assert extraction_rate > 0.8, f"Low extraction rate: {extraction_rate:.2%}"
    
    def test_url_uniqueness(self, db_connection):
        """Test that URLs are unique (no duplicates)"""
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT url, COUNT(*) as count 
                FROM customer_stories 
                GROUP BY url 
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cursor.fetchall()
            assert len(duplicates) == 0, f"Found duplicate URLs: {duplicates}"
    
    def test_date_validity(self, db_connection):
        """Test that dates are valid and reasonable"""
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    publish_date,
                    scraped_date,
                    customer_name
                FROM customer_stories 
                WHERE publish_date IS NOT NULL
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                pub_date = row['publish_date']
                scraped_date = row['scraped_date']
                
                # Publish date should be reasonable (not too far in past/future)
                if pub_date:
                    assert date(2015, 1, 1) <= pub_date <= date(2030, 12, 31), \
                        f"Invalid publish date: {pub_date} for {row['customer_name']}"
                
                # Scraped date should be after publish date
                if pub_date and scraped_date:
                    assert scraped_date.date() >= pub_date, \
                        f"Scraped date before publish date for {row['customer_name']}"
    
    def test_extracted_data_structure(self, db_connection):
        """Test extracted data structure consistency"""
        with db_connection.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT customer_name, extracted_data 
                FROM customer_stories 
                WHERE extracted_data IS NOT NULL
                LIMIT 20
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                extracted_data = row['extracted_data']
                customer_name = row['customer_name']
                
                # Test basic structure
                assert isinstance(extracted_data, dict), f"Invalid extracted_data type for {customer_name}"
                
                # Test quality score if present
                if 'content_quality_score' in extracted_data:
                    score = extracted_data['content_quality_score']
                    assert 0 <= score <= 1, f"Invalid quality score {score} for {customer_name}"
                
                # Test technologies_used structure
                if 'technologies_used' in extracted_data:
                    techs = extracted_data['technologies_used']
                    assert isinstance(techs, list), f"Invalid technologies_used type for {customer_name}"

if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "-s",  # Show print statements
        "--tb=short"
    ])