import time
import logging
import random
import re
from typing import Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from src.database.models import DatabaseOperations, DiscoveredUrl, generate_content_hash
from src.ai_integration.claude_processor import ClaudeProcessor

logger = logging.getLogger(__name__)

class OpenAIContentScraper:
    """
    Phase 2 of OpenAI scraping: Scrape individual story content with enhanced anti-bot protection
    """
    
    def __init__(self, db_ops: DatabaseOperations):
        self.db_ops = db_ops
        self.driver = None
        self.claude_processor = ClaudeProcessor()
        self.source_id = None
        self._setup_driver()
        self._get_source_id()
        
    def _setup_driver(self):
        """Setup Selenium WebDriver with maximum anti-bot protection"""
        try:
            chrome_options = Options()
            
            # Enhanced browser fingerprinting (most human-like)
            # chrome_options.add_argument("--headless")  # Disable headless for debugging
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Latest realistic user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
            
            # Maximum anti-detection measures
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins-discovery")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Realistic browser preferences
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "geolocation": 2,
                },
                "profile.managed_default_content_settings": {
                    "images": 1  # Load images for complete content
                }
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Auto-install ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute advanced anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            # Set realistic viewport
            self.driver.set_window_size(1920, 1080)
            
            logger.info("Enhanced Content Scraper WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def _get_source_id(self):
        """Get OpenAI source ID from database"""
        source = self.db_ops.get_source_by_name("OpenAI")
        if not source:
            raise ValueError("OpenAI source not found in database")
        self.source_id = source.id
        logger.info(f"Using OpenAI source ID: {self.source_id}")
    
    def __del__(self):
        """Cleanup WebDriver on object destruction"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def _human_like_wait(self, min_seconds=2, max_seconds=5):
        """Add random human-like delays"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)
    
    def _simulate_human_page_interaction(self):
        """Simulate human-like page interaction to avoid bot detection"""
        try:
            # Random scroll behavior
            scroll_actions = random.randint(2, 4)
            for _ in range(scroll_actions):
                # Random scroll distance
                scroll_distance = random.randint(200, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                time.sleep(random.uniform(0.5, 2))
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
            
            # Random mouse movements
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                actions = ActionChains(self.driver)
                
                for _ in range(random.randint(1, 3)):
                    random_x = random.randint(100, 800)
                    random_y = random.randint(100, 600)
                    actions.move_to_element_with_offset(body, random_x, random_y)
                    actions.pause(random.uniform(0.2, 0.8))
                
                actions.perform()
            except Exception as e:
                logger.debug(f"Mouse movement simulation failed: {e}")
                
        except Exception as e:
            logger.debug(f"Human interaction simulation failed: {e}")
    
    def scrape_story_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual story content with enhanced anti-bot protection"""
        try:
            logger.info(f"Scraping OpenAI story with enhanced protection: {url}")
            
            # Human-like delay before loading
            self._human_like_wait(1, 3)
            
            # Load the story page
            self.driver.get(url)
            
            # Wait for content to load with better conditions
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Wait for page to fully load
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            self._human_like_wait(5, 8)
            
            # Debug: Check what we actually loaded
            logger.info(f"Page title: {self.driver.title}")
            logger.info(f"Current URL: {self.driver.current_url}")
            logger.info(f"Page source length: {len(self.driver.page_source)} chars")
            
            # Simulate human interaction to avoid bot detection
            self._simulate_human_page_interaction()
            
            # Get page source and parse with BeautifulSoup
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract comprehensive content
            story_data = self._extract_story_data(soup, url, html_content)
            
            if story_data:
                logger.info(f"Successfully scraped story: {story_data['customer_name']}")
                return story_data
            else:
                logger.warning(f"Failed to extract story data from: {url}")
                return None
                
        except TimeoutException:
            logger.error(f"Timeout loading story page: {url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping story {url}: {e}")
            return None
    
    def _extract_story_data(self, soup: BeautifulSoup, url: str, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract comprehensive story data from parsed HTML"""
        try:
            # Extract text content
            text_content = self._extract_text_content(soup)
            
            # Validate content quality (filter out system pages, etc.)
            if not self._is_valid_customer_story(soup, url, text_content):
                logger.info(f"Filtering out non-customer story: {url}")
                return None
            
            # Extract customer name
            customer_name = self._extract_customer_name(soup, url)
            
            # Extract publish date
            publish_date = self._extract_publish_date(soup)
            
            # Extract title
            title = self._extract_title(soup)
            
            # Create raw content structure
            raw_content = self._create_raw_content(html_content, soup, url, text_content)
            
            # Generate content hash
            content_hash = generate_content_hash(text_content)
            
            return {
                'url': url,
                'customer_name': customer_name,
                'title': title,
                'raw_content': raw_content,
                'content_hash': content_hash,
                'publish_date': publish_date,
                'text_content': text_content
            }
            
        except Exception as e:
            logger.error(f"Error extracting story data: {e}")
            return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _is_valid_customer_story(self, soup: BeautifulSoup, url: str, text_content: str) -> bool:
        """Validate that this is a legitimate customer story"""
        # Check content length
        word_count = len(text_content.split())
        if word_count < 100:
            logger.info(f"Skipping story with insufficient content ({word_count} words): {url}")
            return False
        
        # Check for system/technical pages
        url_lower = url.lower()
        system_indicators = ['system-card', 'technical-report', 'api-reference', 'documentation']
        if any(indicator in url_lower for indicator in system_indicators):
            return False
        
        # Check for customer story indicators in content
        text_lower = text_content.lower()
        customer_indicators = [
            'customer', 'company', 'business', 'organization', 'team',
            'using openai', 'with gpt', 'chatgpt', 'api', 'implementation',
            'solution', 'challenge', 'results', 'success', 'improved'
        ]
        
        indicator_count = sum(1 for indicator in customer_indicators if indicator in text_lower)
        
        if indicator_count < 3:
            logger.info(f"Skipping page with few customer story indicators ({indicator_count}): {url}")
            return False
        
        return True
    
    def _extract_customer_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract customer name from the story"""
        # Try URL-based extraction first (most reliable for OpenAI)
        if '/index/' in url:
            company_slug = url.split('/index/')[-1].rstrip('/')
            if company_slug:
                # Convert slug to proper name
                customer_name = company_slug.replace('-', ' ').title()
                
                # Handle special cases
                if customer_name.lower() == 'gpt':
                    customer_name = 'OpenAI'  # System announcements
                elif 'gpt' in customer_name.lower() and len(customer_name.split()) > 1:
                    # e.g., "Gpt 4o System Card" -> extract actual customer if present
                    pass
                
                logger.info(f"Extracted customer name from URL: {customer_name}")
                return customer_name
        
        # Try to find customer name in page content
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text().strip()
            if text and len(text) < 100 and not text.lower().startswith('how'):
                logger.info(f"Extracted customer name from H1: {text}")
                return text
        
        # Fallback to URL slug
        if '/index/' in url:
            company_slug = url.split('/index/')[-1].rstrip('/')
            return company_slug.replace('-', ' ').title()
        
        logger.warning(f"Could not extract customer name from {url}")
        return "Unknown"
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date from the story"""
        # Try time tags with datetime attribute
        time_tags = soup.find_all('time')
        for time_tag in time_tags:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                try:
                    if 'T' in datetime_attr:
                        date_part = datetime_attr.split('T')[0]
                    else:
                        date_part = datetime_attr
                    logger.info(f"Extracted publish date from time tag: {date_part}")
                    return date_part
                except:
                    continue
        
        # Try meta tags
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
        
        # Try JSON-LD structured data
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
        
        # Try date patterns in text
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
                    if '-' in date_str:
                        logger.info(f"Extracted publish date from text: {date_str}")
                        return date_str
                    else:
                        # Parse other formats
                        parsed_date = datetime.strptime(date_str, '%B %d, %Y')
                        formatted_date = parsed_date.strftime('%Y-%m-%d')
                        logger.info(f"Extracted and formatted publish date: {formatted_date}")
                        return formatted_date
                except:
                    continue
        
        logger.warning("Could not extract publish date")
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from the story"""
        # Try title tag
        title_element = soup.find('title')
        if title_element:
            title_text = title_element.get_text().strip()
            if title_text:
                # Clean up title (remove site name, etc.)
                if ' | ' in title_text:
                    title_text = title_text.split(' | ')[0].strip()
                logger.info(f"Extracted title: {title_text}")
                return title_text
        
        # Try h1 tags
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text().strip()
            if text and len(text) < 200:
                logger.info(f"Extracted title from H1: {text}")
                return text
        
        logger.warning("Could not extract title")
        return "Untitled"
    
    def _create_raw_content(self, html_content: str, soup: BeautifulSoup, url: str, text_content: str) -> Dict[str, Any]:
        """Create standardized raw content structure"""
        # Extract metadata
        title = self._extract_title(soup)
        
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
                "title": title,
                "description": description,
                "word_count": len(text_content.split()),
                "images": images[:10],  # Limit to first 10 images
                "external_links": external_links[:20]  # Limit to first 20 links
            },
            "scraping_info": {
                "scraper_version": "2.0-enhanced",
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "method": "selenium-enhanced",
                "final_url": url,
                "errors": []
            }
        }
    
    def scrape_and_store_story(self, discovered_url: DiscoveredUrl) -> Dict[str, Any]:
        """Scrape story content and store in database with Claude processing"""
        try:
            logger.info(f"Processing discovered URL: {discovered_url.url}")
            
            # Update URL status to scraping
            self.db_ops.update_discovered_url_status(discovered_url.id, 'scraping', 'Starting content scraping')
            
            # Scrape content
            story_data = self.scrape_story_content(discovered_url.url)
            
            if not story_data:
                self.db_ops.update_discovered_url_status(discovered_url.id, 'failed', 'Failed to scrape content')
                return {'success': False, 'error': 'Failed to scrape content'}
            
            # Process with Claude
            logger.info("Processing content with Claude AI...")
            extracted_data = self.claude_processor.process_story_content(
                story_data['text_content'], 
                story_data['customer_name']
            )
            
            # Store in database
            story_id = self.db_ops.insert_customer_story(
                source_id=self.source_id,
                customer_name=story_data['customer_name'],
                title=story_data['title'],
                url=story_data['url'],
                content_hash=story_data['content_hash'],
                raw_content=story_data['raw_content'],
                extracted_data=extracted_data,
                publish_date=story_data['publish_date']
            )
            
            # Update discovered URL status
            self.db_ops.update_discovered_url_status(discovered_url.id, 'scraped', f'Successfully scraped as story ID {story_id}')
            
            logger.info(f"Story successfully stored with ID: {story_id}")
            
            return {
                'success': True,
                'story_id': story_id,
                'customer_name': story_data['customer_name'],
                'title': story_data['title'],
                'content': story_data['text_content'],
                'claude_data': extracted_data
            }
            
        except Exception as e:
            error_msg = f"Error processing story: {e}"
            logger.error(error_msg)
            self.db_ops.update_discovered_url_status(discovered_url.id, 'failed', error_msg)
            return {'success': False, 'error': error_msg}