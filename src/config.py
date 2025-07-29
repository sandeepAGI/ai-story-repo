import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/ai_stories')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    SCRAPING_DELAY = 2.0  # seconds between requests
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )