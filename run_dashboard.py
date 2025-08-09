#!/usr/bin/env python3
"""
Dashboard Launcher Script
Starts the Streamlit web dashboard for AI Customer Stories
"""

import subprocess
import sys
import os
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser to dashboard URL after a delay"""
    time.sleep(3)  # Wait for Streamlit to start
    webbrowser.open('http://localhost:8501')

def main():
    """Launch the Streamlit dashboard"""
    print("🚀 Starting AI Customer Stories Dashboard...")
    print("="*50)
    
    # Check if required dependencies are installed
    try:
        import streamlit
        import plotly
        import pandas
        print("✅ All dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return 1
    
    # Check database connectivity
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from database.models import DatabaseOperations
        
        db_ops = DatabaseOperations()
        with db_ops.db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM customer_stories")
            result = cursor.fetchone()
            story_count = result['count']
            print(f"✅ Database connected: {story_count} stories available")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please ensure your PostgreSQL database is running and accessible")
        return 1
    
    print("\n📊 Dashboard will be available at: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("="*50)
    
    # Open browser after a delay
    Timer(3.0, open_browser).start()
    
    # Start Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())