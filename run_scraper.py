#!/usr/bin/env python3
"""
AI Customer Stories Scraper - Main Runner Script

Usage:
    python run_scraper.py --setup-db        # Initialize database
    python run_scraper.py --test            # Test with 3 stories
    python run_scraper.py --limit 10        # Process up to 10 stories
    python run_scraper.py                   # Process all available stories
"""

import argparse
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import AIStoriesProcessor
from src.config import Config

def main():
    parser = argparse.ArgumentParser(description='AI Customer Stories Scraper')
    parser.add_argument('--setup-db', action='store_true', 
                       help='Initialize database with schema')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: process only 3 stories')
    parser.add_argument('--limit', type=int, metavar='N',
                       help='Limit number of stories to process')
    
    args = parser.parse_args()
    
    try:
        processor = AIStoriesProcessor()
        
        if args.setup_db:
            print("Setting up database...")
            processor.setup_database()
            print("Database setup completed successfully!")
            return
        
        # Determine limit
        limit = None
        if args.test:
            limit = 3
            print("Running in test mode (3 stories)")
        elif args.limit:
            limit = args.limit
            print(f"Processing up to {limit} stories")
        else:
            print("Processing all available stories")
        
        # Run the pipeline
        processor.run_full_pipeline(limit=limit)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()