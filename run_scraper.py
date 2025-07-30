#!/usr/bin/env python3
"""
AI Customer Stories Scraper - Main Runner Script

Usage:
    python run_scraper.py --setup-db                    # Initialize database
    python run_scraper.py --test                        # Test with 3 Anthropic stories
    python run_scraper.py --test --source openai        # Test with 3 OpenAI stories
    python run_scraper.py --limit 10                    # Process up to 10 Anthropic stories
    python run_scraper.py --source openai --limit 5     # Process up to 5 OpenAI stories
    python run_scraper.py                               # Process all available Anthropic stories
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
    parser.add_argument('--source', choices=['anthropic', 'openai'], default='anthropic',
                       help='Source to scrape: anthropic (default) or openai')
    
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
            print(f"Running in test mode (3 {args.source} stories)")
        elif args.limit:
            limit = args.limit
            print(f"Processing up to {limit} {args.source} stories")
        else:
            print(f"Processing all available {args.source} stories")
        
        # Run the pipeline
        processor.run_full_pipeline(source=args.source, limit=limit)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()