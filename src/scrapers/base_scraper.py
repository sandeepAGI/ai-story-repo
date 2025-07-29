import requests
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.config import Config
from src.database.models import generate_content_hash

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def make_request(self, url: str, retries: int = None) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting"""
        retries = retries or Config.MAX_RETRIES
        
        for attempt in range(retries):
            try:
                logger.info(f"Requesting URL: {url} (attempt {attempt + 1})")
                
                response = self.session.get(
                    url, 
                    timeout=Config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                # Rate limiting
                time.sleep(Config.SCRAPING_DELAY)
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    logger.error(f"All retry attempts failed for {url}")
                    return None
                time.sleep(Config.SCRAPING_DELAY * (attempt + 1))
        
        return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from BeautifulSoup object"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def create_raw_content(self, response: requests.Response, soup: BeautifulSoup) -> Dict[str, Any]:
        """Create standardized raw content structure"""
        text_content = self.extract_text_content(soup)
        
        # Extract metadata
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        # Count images and external links
        images = [img.get('src', '') for img in soup.find_all('img') if img.get('src')]
        external_links = [link.get('href', '') for link in soup.find_all('a', href=True) 
                         if link.get('href', '').startswith('http')]
        
        return {
            "html": response.text,
            "text": text_content,
            "metadata": {
                "title": title_text,
                "description": description,
                "word_count": len(text_content.split()),
                "images": images[:10],  # Limit to first 10 images
                "external_links": external_links[:20]  # Limit to first 20 links
            },
            "scraping_info": {
                "scraper_version": "1.0",
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "page_load_time": response.elapsed.total_seconds(),
                "status_code": response.status_code,
                "final_url": response.url,
                "errors": []
            }
        }
    
    @abstractmethod
    def get_customer_story_urls(self) -> List[str]:
        """Get list of customer story URLs from the main page"""
        pass
    
    @abstractmethod
    def scrape_story(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual customer story"""
        pass
    
    @abstractmethod
    def extract_customer_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract customer name from the story page"""
        pass
    
    def scrape_all_stories(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape all customer stories with optional limit"""
        story_urls = self.get_customer_story_urls()
        
        if limit:
            story_urls = story_urls[:limit]
            
        stories = []
        for url in story_urls:
            story_data = self.scrape_story(url)
            if story_data:
                stories.append(story_data)
            else:
                logger.warning(f"Failed to scrape story: {url}")
        
        logger.info(f"Successfully scraped {len(stories)} stories from {self.source_name}")
        return stories