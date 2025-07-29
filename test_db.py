#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import psycopg2
import psycopg2.extras
from src.config import Config

# Test direct connection
try:
    print("Testing direct psycopg2 connection...")
    conn = psycopg2.connect(
        "postgresql://ai_user@localhost/ai_stories",
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1 as test")
    result = cursor.fetchone()
    print(f"Direct connection success: {result}")
    conn.close()
except Exception as e:
    print(f"Direct connection failed: {e}")

# Test config loading
try:
    print(f"Database URL from config: {Config.DATABASE_URL}")
except Exception as e:
    print(f"Config error: {e}")