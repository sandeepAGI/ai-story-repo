import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.database.models import generate_content_hash

logger = logging.getLogger(__name__)

class GoogleCloudScraper(BaseScraper):
    """Scraper for Google Cloud AI/ML customer stories"""
    
    def __init__(self):
        super().__init__(
            source_name="Google Cloud",
            base_url="https://cloud.google.com/ai/generative-ai/stories"
        )
        
        # Google Cloud AI/ML keywords for filtering mixed content
        self.ai_keywords = {
            'generative ai', 'vertex ai', 'gemini', 'palm', 'bard', 'machine learning',
            'artificial intelligence', 'automl', 'ai platform', 'cloud ai',
            'natural language', 'speech-to-text', 'text-to-speech', 'translation api',
            'vision api', 'video intelligence', 'document ai', 'contact center ai',
            'recommendations ai', 'retail api', 'healthcare nlp api', 'media translation',
            'deep learning', 'computer vision', 'natural language processing',
            'nlp', 'llm', 'large language model', 'tensorflow', 'kubeflow',
            'ai services', 'ml services', 'neural networks', 'google ai'
        }
        
        # Alternative URLs to try for comprehensive coverage
        self.secondary_urls = [
            "https://cloud.google.com/customers",
        ]
        
        # Known AI customer story URLs for direct discovery
        self.known_ai_customers = [
            "https://cloud.google.com/customers/ai-seer",
            "https://cloud.google.com/customers/nextbillion-ai", 
            "https://cloud.google.com/customers/basisai",
            "https://cloud.google.com/customers/intentai",
            "https://cloud.google.com/customers/flowxai",
            "https://cloud.google.com/customers/changing-ai",
            "https://cloud.google.com/customers/allcyte",
            "https://cloud.google.com/customers/doc-ai",
            "https://cloud.google.com/customers/strise-ai",
            "https://cloud.google.com/customers/ai21",
            "https://cloud.google.com/customers/igenius",
            "https://cloud.google.com/customers/seaart"
        ]
    
    def get_customer_story_urls(self) -> List[str]:
        """Get list of Google Cloud AI/ML customer story URLs"""
        logger.info(f"Fetching customer story URLs from Google Cloud")
        
        all_story_urls = []
        
        # Strategy 1: Start with known AI customer URLs
        logger.info(f"Adding {len(self.known_ai_customers)} known AI customer URLs")
        for url in self.known_ai_customers:
            if url not in all_story_urls:
                all_story_urls.append(url)
        
        # Strategy 2: Try to discover additional URLs from listing pages
        urls_to_check = [self.base_url] + self.secondary_urls
        for url in urls_to_check:
            logger.info(f"Checking URL for additional discoveries: {url}")
            response = self.make_request(url)
            if not response:
                continue
            
            soup = self.parse_html(response.text)
            story_urls = self._extract_urls_from_page(soup, response.text)
            
            for story_url in story_urls:
                if story_url not in all_story_urls:
                    all_story_urls.append(story_url)
        
        logger.info(f"Found {len(all_story_urls)} total Google Cloud story URLs")
        return all_story_urls
    
    def _extract_urls_from_page(self, soup: BeautifulSoup, html_content: str) -> List[str]:
        """Extract story URLs from a Google Cloud page"""
        story_urls = []
        
        # Strategy 1: Look for direct customer story links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            
            # Look for Google Cloud customer story patterns
            if any(pattern in href.lower() for pattern in [
                '/customers/',
                '/customer-stories/',
                'cloud.google.com/customers/',
            ]):
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = f"https://cloud.google.com{href}"
                elif not href.startswith('http'):
                    continue
                    
                if self._is_valid_story_url(href) and href not in story_urls:
                    story_urls.append(href)
        
        # Strategy 2: Look for URLs in script tags and data attributes
        script_tags = soup.find_all('script')
        for script in script_tags:
            try:
                script_content = script.get_text()
                # Look for customer story URLs in script content
                potential_urls = re.findall(
                    r'https://cloud\.google\.com/customers/[^"\']*', 
                    script_content
                )
                for url in potential_urls:
                    if self._is_valid_story_url(url) and url not in story_urls:
                        story_urls.append(url)
            except Exception as e:
                logger.debug(f"Error parsing script tag: {e}")
        
        # Strategy 3: Look for data attributes that might contain URLs
        elements_with_data = soup.find_all(attrs={"data-href": True})
        for element in elements_with_data:
            href = element.get('data-href', '')
            if '/customers/' in href:
                if href.startswith('/'):
                    href = f"https://cloud.google.com{href}"
                if self._is_valid_story_url(href) and href not in story_urls:
                    story_urls.append(href)
        
        return story_urls
    
    def _is_valid_story_url(self, url: str) -> bool:
        """Check if URL is a valid Google Cloud customer story"""
        if not url or not url.startswith('https://cloud.google.com/customers/'):
            return False
            
        # Exclude listing pages and non-story URLs
        exclusions = [
            '/customers?',      # Query parameters usually indicate listing pages
            '/customers#',      # Fragment identifiers usually indicate sections
            '/customers/',      # Base customers page
            '/search',          # Search pages
            '/browse',          # Browse pages
        ]
        
        for exclusion in exclusions:
            if url.endswith(exclusion) or exclusion + '?' in url:
                return False
        
        # Must have a customer name/slug after /customers/
        parts = url.replace('https://cloud.google.com/customers/', '').strip('/')
        if not parts or '/' in parts:  # Should be just the customer slug
            return False
            
        return True
    
    def scrape_story(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single Google Cloud customer story"""
        logger.info(f"Scraping Google Cloud story: {url}")
        
        response = self.make_request(url)
        if not response:
            return None
        
        soup = self.parse_html(response.text)
        
        # Extract basic metadata
        title = self._extract_title(soup)
        customer_name = self._extract_customer_name(soup, url)
        
        # Skip non-AI stories based on content filtering
        full_text = soup.get_text().lower()
        if not self._is_ai_story(full_text):
            logger.info(f"Skipping non-AI story: {url}")
            return None
        
        # Extract other metadata
        publish_date = self._extract_publish_date(soup)
        content = self._extract_content(soup)
        
        if not content or len(content.strip()) < 100:
            logger.warning(f"Insufficient content found for {url}")
            return None
        
        # Generate content hash
        content_hash = generate_content_hash(content)
        
        return {
            'url': url,
            'title': title,
            'customer_name': customer_name,
            'content': content,
            'content_hash': content_hash,
            'publish_date': publish_date,
            'raw_content': {
                'html': response.text,
                'text': content,
                'metadata': {
                    'title': title,
                    'customer_name': customer_name,
                    'word_count': len(content.split()),
                    'scraped_date': datetime.now().isoformat()
                }
            }
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the story title"""
        # Try multiple strategies for title extraction
        title_selectors = [
            'title',
            'h1',
            '[data-text="true"]',  # Google Cloud often uses this
            '.gc-analytics-event[data-category="page"] h1',
            'meta[property="og:title"]',
            'meta[name="title"]'
        ]
        
        for selector in title_selectors:
            if selector.startswith('meta'):
                element = soup.find('meta', attrs={'property': 'og:title'} if 'property' in selector else {'name': 'title'})
                if element:
                    return element.get('content', '').strip()
            else:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text().strip()
                    # Clean up Google Cloud title patterns
                    title = re.sub(r'\s*\|\s*Google Cloud\s*$', '', title)
                    if title:
                        return title
        
        return "Google Cloud Customer Story"
    
    def extract_customer_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract customer name from the story page (abstract method implementation)"""
        return self._extract_customer_name(soup, url)
    
    def _extract_customer_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract customer name from content or URL"""
        # Strategy 1: Extract from URL slug
        slug = url.replace('https://cloud.google.com/customers/', '').strip('/')
        if slug:
            # Convert slug to proper name (e.g., 'doc-ai' -> 'doc.ai')
            customer_name = slug.replace('-', '.').title()
            # Special handling for AI company names
            if customer_name.endswith('.Ai'):
                customer_name = customer_name[:-3] + '.ai'
            elif 'ai' in customer_name.lower():
                # Keep AI capitalization for AI companies
                customer_name = re.sub(r'\bAi\b', 'AI', customer_name)
            return customer_name
        
        # Strategy 2: Look for customer name in content
        title = self._extract_title(soup)
        if title and 'Case Study' in title:
            # Extract company name before "Case Study"
            match = re.search(r'^([^|]+?)\s*(?:Case Study|Customer Story)', title)
            if match:
                return match.group(1).strip()
        
        # Strategy 3: Look for company logo alt text or headings
        logo_selectors = ['img[alt*="logo"]', 'img[alt*="Logo"]', 'h1', 'h2']
        for selector in logo_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element.name == 'img':
                    alt_text = element.get('alt', '')
                    if 'logo' in alt_text.lower():
                        # Extract company name from logo alt text
                        company = re.sub(r'\s*logo\s*', '', alt_text, flags=re.IGNORECASE).strip()
                        if company:
                            return company
                else:
                    text = element.get_text().strip()
                    if len(text) < 50 and not any(word in text.lower() for word in ['google', 'cloud', 'case', 'study']):
                        return text
        
        # Fallback: Use URL slug with basic cleanup
        return slug.replace('-', ' ').title() if slug else "Unknown Customer"
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date from the story"""
        # Google Cloud customer stories typically don't have explicit publication dates
        # Most are evergreen content without specific publish dates
        # Let Claude processing handle date extraction from content context
        
        # Try basic meta tag checks first
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="pubdate"]',
            'meta[name="date"]',
            'time[datetime]',
        ]
        
        for selector in date_selectors:
            if selector.startswith('meta'):
                element = soup.find('meta', attrs={
                    'property': 'article:published_time' if 'property' in selector else None,
                    'name': selector.split('[name="')[1].split('"]')[0] if 'name=' in selector else None
                })
                if element:
                    date_str = element.get('content', '')
                    if date_str:
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            return parsed_date
            else:
                element = soup.select_one(selector)
                if element:
                    date_str = element.get('datetime', '')
                    if date_str:
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            return parsed_date
        
        # Google Cloud stories are typically evergreen - return None to let Claude extract context dates
        logger.debug("No explicit publication date found - will rely on Claude processing")
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
            
        # Clean the date string
        date_str = date_str.strip()
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%B %d, %Y',
            '%b %d, %Y',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.debug(f"Could not parse date: {date_str}")
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content of the story"""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Try to find main content area
        main_content_selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.content',
            'article',
            '.case-study-content',
            '.customer-story'
        ]
        
        for selector in main_content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                return content_element.get_text(separator=' ', strip=True)
        
        # Fallback: Get all text content, excluding common non-content elements
        for element in soup.find_all(['nav', 'header', 'footer', 'aside', '.nav', '.menu']):
            element.decompose()
        
        return soup.get_text(separator=' ', strip=True)
    
    def _is_ai_story(self, content: str) -> bool:
        """Check if the story is AI/ML related"""
        content_lower = content.lower()
        
        # Count AI keyword matches
        ai_matches = sum(1 for keyword in self.ai_keywords if keyword in content_lower)
        
        # Require at least 2 AI keyword matches for content filtering
        return ai_matches >= 2