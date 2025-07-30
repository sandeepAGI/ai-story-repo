import time
import logging
import random
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
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
        """Setup Selenium WebDriver with enhanced anti-bot protection"""
        try:
            chrome_options = Options()
            
            # Enhanced browser fingerprinting to avoid detection
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # More realistic user agent (current Chrome version)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
            
            # Anti-detection measures
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins-discovery")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Realistic browser preferences
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "geolocation": 2,
                },
                "profile.managed_default_content_settings": {
                    "images": 2
                }
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Auto-install ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set realistic viewport and properties
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            logger.info("Enhanced URL Discovery WebDriver initialized successfully")
            
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
    
    def _human_like_scroll(self, scroll_pause_time=None):
        """Simulate human-like scrolling behavior"""
        if scroll_pause_time is None:
            scroll_pause_time = random.uniform(1.5, 3.5)
        
        # Get current scroll position and page height
        current_scroll = self.driver.execute_script("return window.pageYOffset;")
        total_height = self.driver.execute_script("return document.body.scrollHeight;")
        
        # Calculate scroll increments (human-like variable scrolling)
        scroll_increments = random.randint(3, 5)
        increment_size = (total_height - current_scroll) / scroll_increments
        
        for i in range(scroll_increments):
            # Add some randomness to scroll distance
            scroll_distance = current_scroll + (increment_size * (i + 1)) + random.randint(-50, 50)
            scroll_distance = min(scroll_distance, total_height)
            
            self.driver.execute_script(f"window.scrollTo(0, {scroll_distance});")
            time.sleep(random.uniform(0.3, 0.8))
        
        time.sleep(scroll_pause_time)
    
    def _human_like_wait(self, min_seconds=1, max_seconds=3):
        """Add random human-like delays"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)
    
    def _simulate_mouse_movement(self, element):
        """Simulate realistic mouse movement before clicking"""
        try:
            actions = ActionChains(self.driver)
            
            # Move to a random nearby position first
            random_x = random.randint(-20, 20)
            random_y = random.randint(-20, 20)
            actions.move_to_element_with_offset(element, random_x, random_y)
            
            # Pause briefly (human-like hesitation)
            actions.pause(random.uniform(0.3, 0.8))
            
            # Move to the actual element
            actions.move_to_element(element)
            actions.pause(random.uniform(0.2, 0.5))
            
            actions.perform()
            logger.debug("Simulated human-like mouse movement")
            
        except Exception as e:
            logger.debug(f"Mouse movement simulation failed: {e}")
    
    def _wait_for_content_change(self, initial_count, max_wait=15):
        """Wait for content to change after clicking load more"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                current_count = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
                if current_count > initial_count:
                    logger.info(f"Content loaded: {initial_count} -> {current_count} links")
                    return True
                
                # Check for loading indicators
                loading_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".loading, .spinner, [class*='load'], [aria-label*='load' i]")
                if loading_elements:
                    logger.debug("Loading indicator detected, waiting...")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"Error checking content change: {e}")
                time.sleep(0.5)
        
        return False
    
    def discover_story_urls(self) -> List[DiscoveredUrl]:
        """
        Phase 1: Discover story URLs from OpenAI stories page using dynamic loading
        Extract URLs, customer names, dates, and titles for later scraping
        """
        discovered_urls = []
        
        try:
            logger.info("Starting enhanced OpenAI URL discovery with human-like behavior...")
            self.driver.get("https://openai.com/stories")
            
            # Wait for initial page to load with better conditions
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for stories to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/index/']"))
            )
            
            # Human-like initial page interaction
            self._human_like_wait(2, 4)
            self._human_like_scroll()
            
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
                
                # Try to load more content with enhanced methods
                more_content_loaded, load_more_clicked = self._try_load_more_content_enhanced()
                
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
                
                # Human-like delay between attempts
                self._human_like_wait(3, 6)
            
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
    
    def _try_load_more_content_enhanced(self) -> tuple[bool, bool]:
        """
        Try multiple strategies to load more content dynamically
        Returns (content_loaded, load_more_clicked) tuple
        """
        content_loaded = False
        load_more_clicked = False
        
        # Get initial content count for validation
        initial_count = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/index/']"))
        
        # First, try human-like scrolling to reveal more content
        self._human_like_scroll()
        self._human_like_wait(1, 2)
        
        # Strategy 1: Enhanced load more button detection with better selectors
        load_more_selectors = [
            # Most specific - exact text matches
            "//button[normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')) = 'load more']",
            "//button[normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')) = 'show more']",
            # Contains but more specific
            "//button[contains(normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')), 'load more')]",
            # Class-based approaches
            "//button[contains(@class, 'load-more') or contains(@class, 'show-more') or contains(@class, 'load_more')]",
            # ARIA labels
            "//button[contains(@aria-label, 'load') or contains(@aria-label, 'more')]",
            # Data attributes that might indicate load more functionality
            "//button[contains(@data-testid, 'load') or contains(@data-testid, 'more')]"
        ]
        
        for selector in load_more_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                logger.debug(f"Found {len(buttons)} buttons with selector: {selector}")
                
                for button in buttons:
                    try:
                        # Enhanced button validation
                        if not (button.is_enabled() and button.is_displayed()):
                            continue
                            
                        # Get button text and validate it's a load more button
                        button_text = button.text.strip().lower()
                        
                        # Skip buttons that are clearly not load more buttons
                        skip_buttons = ['log in', 'sign up', 'sort', 'manage cookies', 'done', 'english', 'united states', 'menu', 'search', 'close', 'cancel']
                        if any(skip_text in button_text for skip_text in skip_buttons):
                            logger.debug(f"Skipping non-load-more button: '{button_text}'")
                            continue
                        
                        # Only proceed if it looks like a load more button
                        valid_button_indicators = ['load', 'more', 'show']
                        if not (any(indicator in button_text for indicator in valid_button_indicators) or button_text == ''):
                            logger.debug(f"Skipping button that doesn't contain load/more/show: '{button_text}'")
                            continue
                        
                        logger.info(f"Found potential load more button: '{button_text}' with selector: {selector}")
                        
                        # Enhanced human-like clicking approach
                        try:
                            # 1. Scroll button into view with human-like behavior
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                            self._human_like_wait(1, 2)
                            
                            # 2. Simulate mouse movement to button
                            self._simulate_mouse_movement(button)
                            
                            # 3. Wait for any overlapping elements to disappear
                            try:
                                WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable(button)
                                )
                            except TimeoutException:
                                logger.debug("Button not immediately clickable, trying anyway")
                            
                            # 4. Multiple click methods with validation
                            click_successful = False
                            
                            # Method 1: ActionChains click (most human-like)
                            try:
                                actions = ActionChains(self.driver)
                                actions.move_to_element(button).pause(random.uniform(0.1, 0.3)).click().perform()
                                click_successful = True
                                load_more_clicked = True
                                logger.info(f"ActionChains clicked button: '{button_text}'")
                            except (ElementClickInterceptedException, Exception) as e:
                                logger.debug(f"ActionChains click failed: {e}")
                                
                                # Method 2: JavaScript click with validation
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    click_successful = True
                                    load_more_clicked = True
                                    logger.info(f"JavaScript clicked button: '{button_text}'")
                                except Exception as e:
                                    logger.debug(f"JavaScript click failed: {e}")
                                    
                                    # Method 3: Direct click as last resort
                                    try:
                                        button.click()
                                        click_successful = True
                                        load_more_clicked = True
                                        logger.info(f"Direct clicked button: '{button_text}'")
                                    except Exception as e:
                                        logger.debug(f"Direct click failed: {e}")
                                        continue
                            
                            if click_successful:
                                # Wait for content change with enhanced validation
                                if self._wait_for_content_change(initial_count, max_wait=20):
                                    content_loaded = True
                                    logger.info("SUCCESS: Load more button click resulted in new content")
                                    return (True, True)
                                else:
                                    logger.info(f"Button clicked successfully but no new content detected")
                                    # Continue trying other buttons
                            
                        except Exception as e:
                            logger.debug(f"Error clicking button '{button_text}': {e}")
                            continue
                            
                    except Exception as e:
                        logger.debug(f"Could not click button with selector {selector}: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        # Strategy 2: Enhanced infinite scroll with human-like behavior
        if not content_loaded:
            try:
                logger.info("Trying enhanced infinite scroll approach...")
                
                # Human-like gradual scrolling to bottom
                self._human_like_scroll()
                
                # Wait and check for content changes
                if self._wait_for_content_change(initial_count, max_wait=10):
                    content_loaded = True
                    logger.info("SUCCESS: Infinite scroll triggered new content")
                else:
                    logger.debug("Infinite scroll did not trigger new content")
                    
            except Exception as e:
                logger.debug(f"Enhanced infinite scroll failed: {e}")
        
        # Strategy 3: Multiple scroll positions with human-like timing
        if not content_loaded:
            try:
                logger.info("Trying multiple scroll positions...")
                scroll_positions = [0.3, 0.5, 0.7, 0.85, 1.0]
                
                for i, position in enumerate(scroll_positions):
                    # Human-like scroll to position
                    target_position = self.driver.execute_script("return document.body.scrollHeight;") * position
                    self.driver.execute_script(f"window.scrollTo({{top: {target_position}, behavior: 'smooth'}});")
                    
                    # Human-like wait with variation
                    self._human_like_wait(2, 4)
                    
                    # Check for new content
                    if self._wait_for_content_change(initial_count, max_wait=8):
                        logger.info(f"SUCCESS: Scroll to {position*100}% triggered new content")
                        content_loaded = True
                        break
                    
                    # Add small random movements to seem more human
                    if i < len(scroll_positions) - 1:
                        random_scroll = random.randint(-100, 100)
                        self.driver.execute_script(f"window.scrollBy(0, {random_scroll});")
                        time.sleep(random.uniform(0.2, 0.5))
                        
            except Exception as e:
                logger.debug(f"Multiple scroll positions failed: {e}")
        
        # Strategy 4: Try to find pagination or navigation elements
        if not content_loaded and not load_more_clicked:
            try:
                logger.info("Looking for pagination or navigation elements...")
                
                # Look for pagination elements
                pagination_selectors = [
                    "//nav[contains(@class, 'pagination') or contains(@aria-label, 'pagination')]//button",
                    "//div[contains(@class, 'paging') or contains(@class, 'nav')]//button",
                    "//button[contains(@class, 'next') or contains(text(), 'Next') or contains(@aria-label, 'next')]"
                ]
                
                for selector in pagination_selectors:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_enabled() and button.is_displayed():
                            button_text = button.text.strip().lower()
                            if 'next' in button_text or 'more' in button_text:
                                logger.info(f"Found pagination button: {button_text}")
                                try:
                                    self._simulate_mouse_movement(button)
                                    button.click()
                                    if self._wait_for_content_change(initial_count, max_wait=15):
                                        content_loaded = True
                                        load_more_clicked = True
                                        logger.info("SUCCESS: Pagination click triggered new content")
                                        break
                                except Exception as e:
                                    logger.debug(f"Pagination click failed: {e}")
                    if content_loaded:
                        break
                        
            except Exception as e:
                logger.debug(f"Pagination strategy failed: {e}")
        
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