#!/usr/bin/env python3
"""
Add discovered_urls table to existing database
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.connection import DatabaseConnection

def add_discovered_urls_table():
    """Add the discovered_urls table and indexes"""
    
    db = DatabaseConnection()
    
    # SQL to create the discovered_urls table and indexes
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS discovered_urls (
            id SERIAL PRIMARY KEY,
            source_id INTEGER REFERENCES sources(id),
            url VARCHAR(500) UNIQUE NOT NULL,
            inferred_customer_name VARCHAR(255),
            inferred_title VARCHAR(500),
            publish_date DATE,
            discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_scrape_attempt TIMESTAMP,
            scrape_attempts INTEGER DEFAULT 0,
            scrape_status VARCHAR(20) DEFAULT 'pending',
            scrape_error TEXT,
            notes TEXT
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_discovered_urls_source_status 
        ON discovered_urls(source_id, scrape_status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_discovered_urls_status 
        ON discovered_urls(scrape_status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_discovered_urls_publish_date 
        ON discovered_urls(publish_date);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_discovered_urls_discovered_date 
        ON discovered_urls(discovered_date);
        """
    ]
    
    try:
        with db.get_cursor() as cursor:
            for sql in sql_commands:
                cursor.execute(sql)
                
        print("✅ Successfully added discovered_urls table and indexes")
        
        # Check if table was created
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count FROM information_schema.tables 
                WHERE table_name = 'discovered_urls'
            """)
            result = cursor.fetchone()
            if result['count'] > 0:
                print("✅ Table discovered_urls exists and is ready")
            else:
                print("❌ Table creation may have failed")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_discovered_urls_table()