import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from src.database.models import DatabaseOperations, DiscoveredUrl

logger = logging.getLogger(__name__)

class OpenAIUrlDiscovery:
    """
    Phase 1 of OpenAI scraping: Discover URLs, names, and dates
    Store in discovered_urls table for later patient scraping
    """
    
    def __init__(self, db_ops: DatabaseOperations):
        self.db_ops = db_ops
        self.driver = None
        self.source_id = None
        self._setup_driver()
        self._get_source_id()
        
    def _setup_driver(self):
        """Setup Selenium WebDriver with Chrome for URL discovery"""
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
            logger.info("URL Discovery WebDriver initialized successfully")
            
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
    
    def discover_story_urls(self) -> List[DiscoveredUrl]:
        """
        Phase 1: Discover story URLs from OpenAI stories page using dynamic loading
        Extract URLs, customer names, dates, and titles for later scraping
        """
        discovered_urls = []
        
        try:
            logger.info("Starting OpenAI URL discovery with dynamic content loading...")
            self.driver.get("https://openai.com/stories")
            
            # Wait for initial page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give initial content time to load
            time.sleep(3)
            
            # Discovery loop with optimized incremental processing
            previous_count = 0
            no_new_content_rounds = 0
            max_no_content_rounds = 8  # Stop after 8 rounds of no new content (more persistent)
            max_total_attempts = 50  # Higher safety limit for comprehensive discovery
            successful_load_more_clicks = 0
            max_load_more_clicks = 20  # Maximum number of successful load-more clicks
            attempt = 0
            
            # Use set for fast duplicate checking
            discovered_urls_set = set()
            
            while (no_new_content_rounds < max_no_content_rounds and 
                   attempt < max_total_attempts and 
                   successful_load_more_clicks < max_load_more_clicks):
                attempt += 1
                logger.info(f"Discovery attempt {attempt} (total URLs: {len(discovered_urls)})...")
                
                # Find all story links currently on page
                story_links = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "a[href*='/index/']"
                )
                
                logger.info(f"Found {len(story_links)} total links on page")
                
                # Process only new links (optimization for appended content)
                new_urls_found = 0
                for link in story_links:
                    url_data = self._extract_url_metadata(link)
                    if url_data and url_data['url'] not in discovered_urls_set:
                        # This is a genuinely new URL
                        discovered_urls.append(url_data)
                        discovered_urls_set.add(url_data['url'])
                        new_urls_found += 1
                        
                        # Log new discovery with date for tracking
                        logger.info(f"NEW: {url_data['customer_name']} ({url_data['publish_date']}) - {url_data['url']}")
                
                # Update counters based on new URLs found
                if new_urls_found > 0:
                    no_new_content_rounds = 0
                    logger.info(f"Attempt {attempt}: Found {new_urls_found} NEW URLs (total: {len(discovered_urls)})")
                else:
                    no_new_content_rounds += 1
                    logger.info(f"Attempt {attempt}: No new URLs found (round {no_new_content_rounds}/{max_no_content_rounds})")
                
                # Try to load more content
                more_content_loaded, load_more_clicked = self._try_load_more_content()
                
                if load_more_clicked:
                    successful_load_more_clicks += 1
                    logger.info(f"Successful load-more clicks: {successful_load_more_clicks}/{max_load_more_clicks}")
                
                if not more_content_loaded and len(discovered_urls) == previous_count:
                    no_new_content_rounds += 1
                    logger.info(f"No content loaded and no new URLs - no-content round {no_new_content_rounds}/{max_no_content_rounds}")
                else:
                    # Reset counter if we found new content
                    if len(discovered_urls) > previous_count:
                        no_new_content_rounds = 0
                
                previous_count = len(discovered_urls)
                
                # Longer delay between attempts to let content load properly
                time.sleep(3)
            
            if no_new_content_rounds >= max_no_content_rounds:
                logger.info(f"Stopped discovery after {no_new_content_rounds} rounds with no new content")
            elif attempt >= max_total_attempts:
                logger.info(f"Stopped discovery after reaching max attempts ({max_total_attempts})")
            elif successful_load_more_clicks >= max_load_more_clicks:
                logger.info(f"Stopped discovery after {successful_load_more_clicks} successful load-more clicks")
            
            # Show discovery summary with date range
            if discovered_urls:
                dates = [url_data['publish_date'] for url_data in discovered_urls if url_data['publish_date']]
                if dates:
                    earliest_date = min(dates)
                    latest_date = max(dates)
                    logger.info(f"Date range discovered: {earliest_date} to {latest_date}")
            
            logger.info(f"URL discovery completed. Found {len(discovered_urls)} story URLs")
            
            # Convert to DiscoveredUrl objects
            discovered_url_objects = []
            for url_data in discovered_urls:
                discovered_url = DiscoveredUrl(
                    id=None,
                    source_id=self.source_id,
                    url=url_data['url'],
                    inferred_customer_name=url_data['customer_name'],
                    inferred_title=url_data['title'],
                    publish_date=url_data['publish_date'],
                    notes=f"Discovered via stories page scan"
                )
                discovered_url_objects.append(discovered_url)
            
            return discovered_url_objects
            
        except Exception as e:
            logger.error(f"Error during URL discovery: {e}")
            return []
    
    def _extract_url_metadata(self, link_element) -> Optional[Dict[str, Any]]:
        """Extract metadata from a story link element"""
        try:
            href = link_element.get_attribute('href')
            if not href or '/index/' not in href:
                return None
            
            # Ensure it's a story, not API/docs pages
            company_part = href.split('/index/')[-1].rstrip('/')
            if not company_part or company_part.startswith('api') or company_part.startswith('docs'):
                return None
            
            # Only filter obvious Sora system pages at URL level
            if self._is_obvious_sora_page(href):
                return None
            
            # Extract customer name from URL
            customer_name = company_part.replace('-', ' ').title()
            
            # Try to extract title and date from link context
            title = self._extract_title_from_link(link_element)
            publish_date = self._extract_date_from_link(link_element)
            
            return {
                'url': href,
                'customer_name': customer_name,
                'title': title,
                'publish_date': publish_date
            }
            
        except Exception as e:
            logger.debug(f"Error extracting metadata from link: {e}")
            return None
    
    def _is_obvious_sora_page(self, url: str) -> bool:
        """Filter only obvious Sora system pages, not customer stories"""
        obvious_sora_indicators = ['sora-system-card', 'sora-red-teaming', 'sora-technical-report']
        url_lower = url.lower()
        
        for indicator in obvious_sora_indicators:
            if indicator in url_lower:
                logger.info(f"Filtering out obvious Sora system page: {url}")
                return True
        
        return False
    
    def _extract_title_from_link(self, link_element) -> Optional[str]:
        """Extract title from link element or surrounding context"""
        try:
            # Try title attribute
            title = link_element.get_attribute('title')
            if title and title.strip():
                return title.strip()
            
            # Try link text
            link_text = link_element.text
            if link_text and link_text.strip():
                return link_text.strip()
            
            # Try to find title in parent elements
            parent = link_element.find_element(By.XPATH, "./..")
            if parent:
                # Look for heading elements in parent
                headings = parent.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
                for heading in headings:
                    heading_text = heading.text.strip()
                    if heading_text and len(heading_text) > 5:  # Reasonable title length
                        return heading_text
            
            return None
            
        except Exception:
            return None
    
    def _extract_date_from_link(self, link_element) -> Optional[datetime]:
        """Extract publication date from link element or surrounding context"""
        try:
            # Look for time elements near the link
            parent = link_element.find_element(By.XPATH, "./..")
            time_elements = parent.find_elements(By.CSS_SELECTOR, "time")
            
            for time_elem in time_elements:
                datetime_attr = time_elem.get_attribute('datetime')
                if datetime_attr:
                    try:
                        # Parse the datetime attribute
                        if 'T' in datetime_attr:
                            date_part = datetime_attr.split('T')[0]
                        else:
                            date_part = datetime_attr
                        
                        # Convert to datetime object
                        return datetime.strptime(date_part, '%Y-%m-%d').date()
                    except ValueError:
                        continue
            
            # Look for date patterns in nearby text
            nearby_text = parent.text
            if nearby_text:
                import re
                date_patterns = [
                    r'(\d{4}-\d{2}-\d{2})',
                    r'(\w+ \d{1,2}, \d{4})',  # "January 15, 2024"
                ]
                
                for pattern in date_patterns:
                    matches = re.findall(pattern, nearby_text)
                    if matches:
                        date_str = matches[0]
                        try:
                            if '-' in date_str:
                                return datetime.strptime(date_str, '%Y-%m-%d').date()
                            else:
                                return datetime.strptime(date_str, '%B %d, %Y').date()
                        except ValueError:
                            continue
            
            return None
            
        except Exception:
            return None
    
    def _try_load_more_content(self) -> tuple[bool, bool]:
        """
        Try multiple strategies to load more content dynamically
        Returns (content_loaded, load_more_clicked) tuple
        """
        content_loaded = False
        load_more_clicked = False
        
        # Strategy 1: Look for and click "Load More" or similar buttons (more aggressive)
        load_more_selectors = [
            # More specific button text searches
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'more stories')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load')]",
            # Class-based searches
            "//button[contains(@class, 'load-more') or contains(@class, 'show-more') or contains(@class, 'load_more')]",
            "//div[contains(@class, 'load-more') or contains(@class, 'pagination')]//button",
            # Generic buttons at bottom of page
            "//button[position()=last()]",
            "//div[contains(@class, 'stories') or contains(@class, 'content')]//button[last()]",
            # Links that might trigger loading
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]"
        ]
        
        for selector in load_more_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                logger.debug(f"Found {len(buttons)} buttons with selector: {selector}")
                
                for button in buttons:
                    try:
                        if button.is_enabled() and button.is_displayed():
                            # Get current content count for comparison
                            current_links = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
                            
                            # Scroll button into view
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(2)
                            
                            # Try multiple click methods
                            button_text = button.text.strip()
                            logger.info(f"Attempting to click button: '{button_text}' with selector: {selector}")
                            
                            # Method 1: JavaScript click
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                load_more_clicked = True
                                logger.info(f"JavaScript clicked button: '{button_text}'")
                            except:
                                # Method 2: Regular click
                                try:
                                    button.click()
                                    load_more_clicked = True
                                    logger.info(f"Regular clicked button: '{button_text}'")
                                except:
                                    continue
                            
                            # Wait longer for content to load (OpenAI might be slow)
                            time.sleep(6)
                            
                            # Check if more content appeared
                            new_links = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
                            if new_links > current_links:
                                logger.info(f"SUCCESS: Content loaded after button click: {current_links} -> {new_links} links")
                                content_loaded = True
                                return (True, True)
                            else:
                                logger.info(f"Button clicked but no new content: {current_links} links remain")
                            
                    except Exception as e:
                        logger.debug(f"Could not click button with selector {selector}: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        # Strategy 2: Scroll to bottom to trigger infinite scroll
        if not content_loaded:
            try:
                current_links = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
                
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(4)
                
                # Check if more content loaded
                new_links = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
                if new_links > current_links:
                    logger.info(f"Infinite scroll triggered: {current_links} -> {new_links} links")
                    content_loaded = True
            except Exception as e:
                logger.debug(f"Infinite scroll failed: {e}")
        
        # Strategy 3: Try to trigger AJAX by scrolling and waiting
        if not content_loaded:
            try:
                # Multiple scroll positions to trigger lazy loading
                scroll_positions = [0.5, 0.7, 0.9, 1.0]
                
                for position in scroll_positions:
                    current_links = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
                    
                    # Scroll to position
                    self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {position});")
                    time.sleep(3)
                    
                    # Check for new content
                    new_links = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
                    if new_links > current_links:
                        logger.info(f"Lazy loading triggered at {position*100}%: {current_links} -> {new_links} links")
                        content_loaded = True
                        break
                        
            except Exception as e:
                logger.debug(f"Lazy loading strategy failed: {e}")
        
        if not content_loaded and not load_more_clicked:
            logger.debug("No additional content could be loaded and no buttons were clicked")
        elif not content_loaded and load_more_clicked:
            logger.debug("Buttons were clicked but no new content appeared")
            
        return (content_loaded, load_more_clicked)
    
    def save_discovered_urls(self, discovered_urls: List[DiscoveredUrl]) -> int:
        """Save discovered URLs to database"""
        saved_count = 0
        
        for discovered_url in discovered_urls:
            try:
                self.db_ops.insert_discovered_url(discovered_url)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save discovered URL {discovered_url.url}: {e}")
        
        logger.info(f"Saved {saved_count} discovered URLs to database")
        return saved_count
    
    def run_discovery_phase(self) -> Dict[str, Any]:
        """Run the complete URL discovery phase"""
        logger.info("Starting OpenAI URL discovery phase...")
        
        try:
            # Discover URLs
            discovered_urls = self.discover_story_urls()
            
            if not discovered_urls:
                logger.warning("No URLs discovered")
                return {'discovered': 0, 'saved': 0}
            
            # Save to database
            saved_count = self.save_discovered_urls(discovered_urls)
            
            # Get statistics
            stats = self.db_ops.get_discovery_stats(self.source_id)
            
            result = {
                'discovered': len(discovered_urls),
                'saved': saved_count,
                'stats': stats
            }
            
            logger.info(f"Discovery phase completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Discovery phase failed: {e}")
            raise
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()