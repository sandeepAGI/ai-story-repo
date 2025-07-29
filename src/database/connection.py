import psycopg2
import psycopg2.extras
from contextlib import contextmanager
import logging
from typing import Dict, Any, List, Optional
from src.config import Config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self._connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self._connection = psycopg2.connect(
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            logger.info("Database connection established")
            return self._connection
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursors with transaction handling"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_schema(self, schema_file_path: str):
        """Execute schema SQL file"""
        try:
            with open(schema_file_path, 'r') as file:
                schema_sql = file.read()
            
            with self.get_cursor() as cursor:
                cursor.execute(schema_sql)
            
            logger.info("Database schema executed successfully")
        except Exception as e:
            logger.error(f"Schema execution failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                return result['test'] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False