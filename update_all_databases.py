#!/usr/bin/env python3
"""
Comprehensive CLI Program for AI Customer Stories Database Management
Simple wrapper around existing tested utilities
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def run_command(cmd: list, description: str = None) -> bool:
    """Run a command and return success status"""
    if description:
        print(f"\n{description}")
        print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='AI Customer Stories Database Manager - Wrapper for existing utilities')
    parser.add_argument('command', choices=['status', 'update', 'dedup', 'purge'], 
                       help='Command to execute')
    parser.add_argument('--source', choices=['anthropic', 'microsoft', 'aws', 'googlecloud', 'openai', 'all'],
                       help='Source to update (for update command)')
    parser.add_argument('--limit', type=int, help='Limit number of stories to process')
    parser.add_argument('--test', action='store_true', help='Test mode - process limited data')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    print("="*70)
    print("AI CUSTOMER STORIES DATABASE MANAGER")
    print("="*70)
    
    if args.command == 'status':
        # Use existing query_stories.py utility
        success = run_command(['python', 'query_stories.py', 'stats'], 
                            "Getting database status...")
        
    elif args.command == 'update':
        if not args.source:
            print("Error: --source required for update command")
            return 1
        
        if args.source == 'all':
            # Update all scraped sources
            sources = ['anthropic', 'microsoft', 'aws', 'googlecloud']
            all_success = True
            
            for source in sources:
                cmd = ['python', 'run_scraper.py', '--source', source]
                if args.limit:
                    cmd.extend(['--limit', str(args.limit)])
                if args.test:
                    cmd.append('--test')
                
                success = run_command(cmd, f"Updating {source.upper()} source...")
                if not success:
                    all_success = False
                    print(f"❌ Failed to update {source}")
            
            # Process OpenAI HTML files
            cmd = ['python', 'process_openai_html.py']
            if args.limit:
                cmd.extend(['--limit', str(args.limit)])
            if args.test:
                cmd.append('--test')
            
            success = run_command(cmd, "Processing OpenAI HTML files...")
            if not success:
                all_success = False
                print("❌ Failed to process OpenAI files")
            
            if not all_success:
                return 1
                
        elif args.source == 'openai':
            # Process OpenAI HTML files
            cmd = ['python', 'process_openai_html.py']
            if args.limit:
                cmd.extend(['--limit', str(args.limit)])
            if args.test:
                cmd.append('--test')
            
            success = run_command(cmd, "Processing OpenAI HTML files...")
            if not success:
                return 1
        else:
            # Update specific source using run_scraper.py
            cmd = ['python', 'run_scraper.py', '--source', args.source]
            if args.limit:
                cmd.extend(['--limit', str(args.limit)])
            if args.test:
                cmd.append('--test')
            
            success = run_command(cmd, f"Updating {args.source.upper()} source...")
            if not success:
                return 1
                
    elif args.command == 'dedup':
        # Use existing query_stories.py deduplication
        success = run_command(['python', 'query_stories.py', 'dedup'], 
                            "Running deduplication analysis...")
        if not success:
            return 1
            
    elif args.command == 'purge':
        if not args.confirm:
            print("\n⚠️  WARNING: This will DELETE ALL customer stories and reload from scratch!")
            response = input("Type 'PURGE' to confirm: ")
            if response != 'PURGE':
                print("Operation cancelled.")
                return 0
        
        print("\n🚨 PURGE AND RELOAD OPERATION")
        print("This will:")
        print("1. Delete all customer stories")
        print("2. Reset all sources")  
        print("3. Reload all data from scratch")
        print("\nThis is a destructive operation and will take significant time.")
        print("Consider backing up your database first.")
        
        if not args.confirm:
            final_confirm = input("\nAre you absolutely sure? Type 'YES' to proceed: ")
            if final_confirm != 'YES':
                print("Operation cancelled.")
                return 0
        
        print("\n❌ PURGE operation not implemented in wrapper.")
        print("This requires direct database access and is too dangerous to automate.")
        print("Please manually:")
        print("1. Backup your database")
        print("2. Run: DELETE FROM customer_stories; (in SQL)")
        print("3. Run: python update_all_databases.py update --source all")
        return 1
    
    # Show final status using existing utility
    print("\n" + "="*70)
    print("FINAL STATUS")
    print("="*70)
    run_command(['python', 'query_stories.py', 'stats'])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())