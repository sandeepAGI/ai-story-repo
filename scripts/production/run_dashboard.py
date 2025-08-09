#!/usr/bin/env python3
"""
Enhanced Dashboard Launcher Script
Starts the Streamlit web dashboard with validation and enhanced features

This provides an alternative to the simple 'streamlit run dashboard.py' command
with additional validation, automatic browser opening, and production settings.

For simple daily use: streamlit run dashboard.py
For enhanced mode: python scripts/production/run_dashboard.py
"""

import subprocess
import sys
import os
import webbrowser
import time
import argparse
from threading import Timer

# Add project root to path (so src.database.models works correctly)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import database operations at module level
try:
    from src.database.models import DatabaseOperations
    DB_IMPORT_SUCCESS = True
    DB_IMPORT_ERROR = None
except Exception as e:
    DB_IMPORT_SUCCESS = False
    DB_IMPORT_ERROR = str(e)

def open_browser(port=8501):
    """Open browser to dashboard URL after a delay"""
    time.sleep(3)  # Wait for Streamlit to start
    webbrowser.open(f'http://localhost:{port}')

def main():
    """Launch the Streamlit dashboard with enhanced features"""
    parser = argparse.ArgumentParser(
        description='Enhanced AI Customer Stories Dashboard Launcher',
        epilog='''
This launcher provides validation and enhanced features.
For simple daily use, you can also run: streamlit run dashboard.py

Examples:
  python scripts/production/run_dashboard.py           # Full validation + auto browser
  python scripts/production/run_dashboard.py --port 8502  # Custom port
  python scripts/production/run_dashboard.py --no-browser # Skip auto browser
  python scripts/production/run_dashboard.py --skip-checks # Skip validation
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int, 
        default=8501,
        help='Port number for dashboard (default: 8501)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Skip automatic browser opening'
    )
    
    parser.add_argument(
        '--skip-checks',
        action='store_true', 
        help='Skip dependency and database validation (faster startup)'
    )
    
    args = parser.parse_args()
    print("🚀 AI Customer Stories Dashboard (Enhanced Mode)")
    print("="*55)
    print("💡 For simple daily use: streamlit run dashboard.py")
    print("="*55)
    
    # Skip validation if requested
    if not args.skip_checks:
        print("🔍 Running pre-flight validation...")
        
        # Check if required dependencies are installed
        try:
            import streamlit
            import plotly
            import pandas
            print("✅ All dependencies found")
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("   Run: pip install -r requirements.txt")
            print("   Or use --skip-checks to bypass validation")
            return 1
        
        # Check database connectivity
        if not DB_IMPORT_SUCCESS:
            print(f"❌ Database module import failed: {DB_IMPORT_ERROR}")
            print("   Ensure the src directory structure is correct")
            print("   Or use --skip-checks to bypass validation")
            return 1
            
        try:
            db_ops = DatabaseOperations()
            with db_ops.db.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM customer_stories")
                result = cursor.fetchone()
                story_count = result['count']
                print(f"✅ Database connected: {story_count:,} stories available")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("   Ensure PostgreSQL is running and accessible")
            print("   Or use --skip-checks to bypass validation")
            return 1
        
        print("✅ All validation checks passed!")
    else:
        print("⚡ Skipping validation checks (--skip-checks enabled)")
    
    print(f"\n📊 Dashboard will be available at: http://localhost:{args.port}")
    if not args.no_browser:
        print("🌐 Browser will open automatically in 3 seconds...")
    else:
        print("🌐 Open the URL above in your browser") 
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("="*55)
    
    # Open browser after a delay (unless disabled)
    if not args.no_browser:
        Timer(3.0, lambda: open_browser(args.port)).start()
    
    # Start Streamlit (change to project root directory first)
    try:
        # Change to project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        dashboard_path = os.path.join(project_root, "dashboard.py")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", dashboard_path,
            "--server.port", str(args.port),
            "--server.address", "localhost", 
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())