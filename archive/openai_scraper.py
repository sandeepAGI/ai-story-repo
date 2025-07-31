import time
import logging
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from .base_scraper import BaseScraper
from src.database.models import generate_content_hash

logger = logging.getLogger(__name__)

class OpenAIScraper(BaseScraper):
    def __init__(self):
        super().__init__("OpenAI", "https://openai.com/stories")
        self.driver = None
        self._setup_driver()
        
    def _setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Auto-install ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def __del__(self):
        """Cleanup WebDriver on object destruction"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def _is_sora_story_by_url(self, url: str) -> bool:
        """Light URL-based filtering - only filter obvious Sora system pages"""
        # Only filter very obvious Sora technical pages, not customer stories
        obvious_sora_indicators = ['sora-system-card', 'sora-red-teaming']
        url_lower = url.lower()
        
        for indicator in obvious_sora_indicators:
            if indicator in url_lower:
                logger.info(f"Filtering out obvious Sora system page: {url}")
                return True
        
        return False
    
    def _is_sora_story_by_content(self, soup: BeautifulSoup, url: str, text_content: str) -> bool:
        """Content-based filtering - check if page is video-only with insufficient text"""
        # Check for minimum content length (video-only stories have very little text)
        word_count = len(text_content.split())
        if word_count < 100:
            logger.info(f"Skipping story with insufficient text content ({word_count} words): {url}")
            return True
        
        # Check if content is heavily video-focused with minimal business content
        text_lower = text_content.lower()
        title = soup.find('title')
        title_text = title.get_text().strip().lower() if title else ""
        
        # Look for video-heavy content with minimal business case information
        video_heavy_indicators = [
            'video generation', 'generating video', 'video model', 'text-to-video'
        ]
        
        business_indicators = [
            'customer', 'company', 'business', 'use case', 'solution', 'implementation',
            'results', 'outcome', 'challenge', 'problem', 'efficiency', 'productivity'
        ]
        
        video_score = sum(1 for indicator in video_heavy_indicators if indicator in text_lower or indicator in title_text)
        business_score = sum(1 for indicator in business_indicators if indicator in text_lower)
        
        # If it's heavily video-focused with no business content, likely a Sora demo
        if video_score >= 2 and business_score == 0:
            logger.info(f"Filtering out video-heavy story with no business content: {url}")
            return True
        
        return False
    
    def get_customer_story_urls(self) -> List[str]:
        """Get list of customer story URLs from OpenAI stories page, filtering out Sora videos"""
        try:
            logger.info("Loading OpenAI stories page...")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Handle infinite scroll/load more functionality
            story_data = []
            previous_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 10
            
            while scroll_attempts < max_scroll_attempts:
                # Find all story links with the expected pattern
                story_links = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "a[href*='/index/']"
                )
                
                # Extract URLs with minimal filtering
                current_stories = []
                for link in story_links:
                    href = link.get_attribute('href')
                    if href and '/index/' in href and len(href.split('/index/')[-1]) > 0:
                        # Ensure it's a story, not API/docs pages
                        company_part = href.split('/index/')[-1].rstrip('/')
                        if company_part and not company_part.startswith('api') and not company_part.startswith('docs'):
                            
                            # Only filter obvious Sora system pages at URL level
                            if not self._is_sora_story_by_url(href):
                                current_stories.append({
                                    'url': href,
                                    'title': link.get_attribute('title') or "",
                                    'preview': link.text or ""
                                })
                
                # Update our story data
                existing_urls = {story['url'] for story in story_data}
                new_stories = [story for story in current_stories if story['url'] not in existing_urls]
                story_data.extend(new_stories)
                
                # Check if we found new stories
                if len(story_data) == previous_count:
                    scroll_attempts += 1
                    logger.info(f"No new stories found, scroll attempt {scroll_attempts}")
                else:
                    scroll_attempts = 0
                    previous_count = len(story_data)
                    logger.info(f"Found {len(story_data)} text-based story URLs so far...")
                
                # Scroll down to trigger more content loading
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Try to click "Load More" button if present
                try:
                    load_more_buttons = self.driver.find_elements(
                        By.XPATH, 
                        "//button[contains(text(), 'Load') or contains(text(), 'More') or contains(text(), 'Show')]"
                    )
                    
                    for button in load_more_buttons:
                        try:
                            if button.is_enabled() and button.is_displayed():
                                # Scroll button into view first
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                time.sleep(1)
                                
                                # Try clicking the button
                                button.click()
                                time.sleep(3)
                                scroll_attempts = 0  # Reset counter since we found a button
                                break
                        except Exception as click_error:
                            logger.debug(f"Could not click button: {click_error}")
                            continue
                            
                except NoSuchElementException:
                    pass
            
            # Extract just the URLs
            story_urls = [story['url'] for story in story_data]
            logger.info(f"Found {len(story_urls)} text-based customer story URLs (Sora stories filtered out)")
            
            # Log first few URLs for debugging
            for i, url in enumerate(story_urls[:5]):
                logger.info(f"Sample URL {i+1}: {url}")
            
            return story_urls
            
        except TimeoutException:
            logger.error("Timeout waiting for OpenAI stories page to load")
            return []
        except Exception as e:
            logger.error(f"Error getting customer story URLs: {e}")
            return []
    
    def scrape_story(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual customer story using Selenium"""
        try:
            logger.info(f"Scraping OpenAI story: {url}")
            
            # Load the story page
            self.driver.get(url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Get page source and parse with BeautifulSoup
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content for filtering
            text_content = self.extract_text_content(soup)
            
            # Check if this is a Sora story based on content
            if self._is_sora_story_by_content(soup, url, text_content):
                return None
            
            # Extract customer name
            customer_name = self.extract_customer_name(soup, url)
            
            # Extract publish date
            publish_date = self.extract_publish_date(soup)
            
            # Extract title
            title_element = soup.find('title')
            title_text = title_element.get_text().strip() if title_element else ""
            
            # Create raw content structure
            raw_content = self.create_selenium_raw_content(html_content, soup, url)
            
            # Generate content hash
            content_hash = generate_content_hash(raw_content.get('text', ''))
            
            return {
                'url': url,
                'customer_name': customer_name,
                'title': title_text,
                'raw_content': raw_content,
                'content_hash': content_hash,
                'publish_date': publish_date
            }
            
        except TimeoutException:
            logger.error(f"Timeout loading story page: {url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping story {url}: {e}")
            return None
    
    def extract_customer_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract customer name from OpenAI story page"""
        # Try URL-based extraction first (most reliable)
        if '/index/' in url:
            company_slug = url.split('/index/')[-1].rstrip('/')
            if company_slug:
                # Convert slug to proper name (e.g., "moderna" -> "Moderna")
                customer_name = company_slug.replace('-', ' ').title()
                logger.info(f"Extracted customer name from URL: {customer_name}")
                return customer_name
        
        # Try to find customer name in page content
        # Look for h1 tags that might contain the company name
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text().strip()
            if text and len(text) < 100:  # Reasonable company name length
                logger.info(f"Extracted customer name from H1: {text}")
                return text
        
        # Look for title tags
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # Try to extract company name from title
            if ' | ' in title_text:
                potential_name = title_text.split(' | ')[0].strip()
                if potential_name:
                    logger.info(f"Extracted customer name from title: {potential_name}")
                    return potential_name
        
        # Fallback: use URL slug
        if '/index/' in url:
            company_slug = url.split('/index/')[-1].rstrip('/')
            return company_slug.replace('-', ' ').title()
        
        logger.warning(f"Could not extract customer name from {url}")
        return "Unknown"
    
    def extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date from OpenAI story page"""
        # Try different date extraction strategies
        
        # 1. Look for time tags with datetime attribute
        time_tags = soup.find_all('time')
        for time_tag in time_tags:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                # Convert to date format (YYYY-MM-DD)
                try:
                    if 'T' in datetime_attr:
                        date_part = datetime_attr.split('T')[0]
                    else:
                        date_part = datetime_attr
                    logger.info(f"Extracted publish date from time tag: {date_part}")
                    return date_part
                except:
                    continue
        
        # 2. Look for meta tags with publication date
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('property') in ['article:published_time', 'article:published']:
                content = meta.get('content')
                if content:
                    try:
                        if 'T' in content:
                            date_part = content.split('T')[0]
                        else:
                            date_part = content
                        logger.info(f"Extracted publish date from meta tag: {date_part}")
                        return date_part
                    except:
                        continue
        
        # 3. Look for JSON-LD structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    date_published = data.get('datePublished')
                    if date_published:
                        if 'T' in date_published:
                            date_part = date_published.split('T')[0]
                        else:
                            date_part = date_published
                        logger.info(f"Extracted publish date from JSON-LD: {date_part}")
                        return date_part
            except:
                continue
        
        # 4. Look for date patterns in text content
        text_content = soup.get_text()
        date_patterns = [
            r'Published on (\d{4}-\d{2}-\d{2})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\w+ \d{1,2}, \d{4})',  # "January 15, 2024"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                date_str = matches[0]
                try:
                    # Try to parse and standardize the date
                    from datetime import datetime
                    if '-' in date_str:
                        # Already in YYYY-MM-DD format
                        logger.info(f"Extracted publish date from text: {date_str}")
                        return date_str
                    else:
                        # Try to parse other formats
                        parsed_date = datetime.strptime(date_str, '%B %d, %Y')
                        formatted_date = parsed_date.strftime('%Y-%m-%d')
                        logger.info(f"Extracted and formatted publish date: {formatted_date}")
                        return formatted_date
                except:
                    continue
        
        logger.warning("Could not extract publish date")
        return None
    
    def create_selenium_raw_content(self, html_content: str, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Create standardized raw content structure for Selenium-scraped content"""
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
            "html": html_content,
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
                "method": "selenium",
                "final_url": url,
                "errors": []
            }
        }