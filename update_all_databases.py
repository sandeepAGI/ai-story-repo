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
    parser.add_argument('command', choices=['status', 'update', 'dedup', 'purge', 'reprocess', 'validate'], 
                       help='Command to execute')
    parser.add_argument('--source', choices=['anthropic', 'microsoft', 'aws', 'googlecloud', 'openai', 'all'],
                       help='Source to update (for update command)')
    parser.add_argument('--framework', choices=['aileron', 'gen-ai', 'all'],
                       help='Framework to reprocess (for reprocess command)')
    parser.add_argument('--story-ids', type=str,
                       help='Comma-separated list of story IDs to reprocess (for reprocess command)')
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
            
    elif args.command == 'reprocess':
        if not args.framework:
            print("Error: --framework required for reprocess command")
            print("Available frameworks: aileron, gen-ai, all") 
            return 1
        
        # Build reprocess command
        if args.framework == 'aileron':
            cmd = ['python', 'reprocess_with_aileron_framework.py']
            description = "Reprocessing stories with Aileron GenAI SuperPowers framework..."
        elif args.framework == 'gen-ai':
            cmd = ['python', 'reprocess_all_with_gen_ai_classification.py']
            description = "Reprocessing stories with Gen AI classification..."
        elif args.framework == 'all':
            # Run both frameworks in sequence
            print("Running complete reprocessing with all frameworks...")
            
            # First Gen AI classification
            success1 = run_command(['python', 'reprocess_all_with_gen_ai_classification.py'], 
                                 "Step 1: Gen AI Classification...")
            if not success1:
                print("❌ Gen AI classification failed, stopping reprocessing")
                return 1
            
            # Then Aileron framework  
            success2 = run_command(['python', 'reprocess_with_aileron_framework.py'],
                                 "Step 2: Aileron Framework...")
            if not success2:
                print("❌ Aileron framework processing failed")
                return 1
            
            print("✅ Complete reprocessing finished successfully!")
            return 0
        
        # Add story IDs if specified
        if args.story_ids:
            story_ids = args.story_ids.split(',')
            print(f"🎯 Targeting specific stories: {len(story_ids)} IDs")
            cmd.extend(['--story-ids', args.story_ids])
        
        # Run the reprocess command
        success = run_command(cmd, description)
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
        
    elif args.command == 'validate':
        # Run classification consistency validation
        success = run_command(['python', 'validate_classification_consistency.py'], 
                            "Validating classification consistency...")
        if not success:
            return 1
    
    # Show final status using existing utility
    print("\n" + "="*70)
    print("FINAL STATUS")
    print("="*70)
    run_command(['python', 'query_stories.py', 'stats'])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())