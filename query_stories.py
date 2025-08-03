#!/usr/bin/env python3
"""
Query Interface Runner for AI Customer Stories Database
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from query_interface import QueryInterface

if __name__ == "__main__":
    try:
        interface = QueryInterface()
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            if command == 'stats':
                interface.show_summary_stats()
            elif command == 'search' and len(sys.argv) > 2:
                query = ' '.join(sys.argv[2:])
                interface.search_stories(query)
            elif command == 'dedup':
                interface.run_deduplication_analysis()
            elif command == 'customer' and len(sys.argv) > 2:
                customer = ' '.join(sys.argv[2:])
                interface.show_customer_details(customer)
            elif command == 'tech':
                if len(sys.argv) > 2:
                    tech = ' '.join(sys.argv[2:])
                    interface.show_technology_usage(tech)
                else:
                    interface.show_technology_usage()
            elif command == 'outcomes':
                interface.show_business_outcomes()
            elif command == 'languages':
                # Import and show language statistics
                from src.utils.language_stats import print_language_statistics
                print_language_statistics()
            else:
                print("Usage: python query_stories.py [command] [args]")
                print("\nCommands:")
                print("  stats                - Show database summary")
                print("  search <term>        - Search stories")
                print("  customer <name>      - Show customer details")
                print("  tech [technology]    - Show technology usage")
                print("  outcomes             - Show business outcomes")
                print("  languages            - Show language distribution statistics")
                print("  dedup                - Run deduplication analysis")
                print("\nOr run without arguments for interactive mode")
        else:
            interface.interactive_mode()
            
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)