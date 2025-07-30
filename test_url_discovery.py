#!/usr/bin/env python3
"""
Test OpenAI URL Discovery Phase
Tests the first phase of two-phase scraping: discovering URLs with metadata
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
from src.config import Config
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations
from src.scrapers.openai_url_discovery import OpenAIUrlDiscovery

def test_url_discovery():
    """Test OpenAI URL discovery phase"""
    
    # Setup logging
    Config.setup_logging()
    logger = logging.getLogger(__name__)
    
    print("="*70)
    print("TESTING OPENAI URL DISCOVERY PHASE")
    print("="*70)
    
    try:
        # Test database connection
        print("1. Testing database connection...")
        db_connection = DatabaseConnection()
        if not db_connection.test_connection():
            print("❌ Database connection failed - please ensure PostgreSQL is running")
            return
        print("✅ Database connection successful")
        
        # Initialize database operations
        db_ops = DatabaseOperations(db_connection)
        
        # Check if OpenAI source exists
        print("\n2. Checking OpenAI source in database...")
        openai_source = db_ops.get_source_by_name("OpenAI")
        if not openai_source:
            print("❌ OpenAI source not found in database - please run database setup")
            return
        print(f"✅ OpenAI source found (ID: {openai_source.id})")
        
        # Initialize URL discovery
        print("\n3. Initializing URL discovery...")
        url_discovery = OpenAIUrlDiscovery(db_ops)
        print("✅ URL discovery initialized successfully")
        
        # Run discovery phase
        print("\n4. Running URL discovery phase...")
        print("   This may take 1-2 minutes to scan all stories...")
        
        result = url_discovery.run_discovery_phase()
        
        print("\n" + "="*50)
        print("DISCOVERY RESULTS")
        print("="*50)
        print(f"URLs discovered this run: {result['discovered']}")
        print(f"URLs saved to database: {result['saved']}")
        
        if 'stats' in result:
            stats = result['stats']
            print(f"\nOverall statistics:")
            print(f"  Total URLs in database: {stats.get('total', 0)}")
            print(f"  Pending scraping: {stats.get('pending', 0)}")
            print(f"  Successfully scraped: {stats.get('scraped', 0)}")
            print(f"  Failed attempts: {stats.get('failed', 0)}")
            print(f"  Filtered out: {stats.get('filtered_out', 0)}")
        
        # Show sample discovered URLs
        print(f"\n📋 Sample discovered URLs:")
        pending_urls = db_ops.get_pending_urls(openai_source.id, limit=5)
        
        if pending_urls:
            for i, url in enumerate(pending_urls, 1):
                print(f"  {i}. {url.inferred_customer_name}")
                print(f"     URL: {url.url}")
                print(f"     Date: {url.publish_date or 'Not found'}")
                print(f"     Title: {url.inferred_title or 'Not found'}")
                print()
        else:
            print("  No pending URLs found")
        
        print("="*70)
        print("URL DISCOVERY PHASE COMPLETED SUCCESSFULLY")
        print("="*70)
        print("Next step: Run the patient scraping phase to process these URLs")
        
    except KeyboardInterrupt:
        print("\n❌ Discovery cancelled by user")
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_url_discovery()