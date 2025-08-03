import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.database.models import generate_content_hash

logger = logging.getLogger(__name__)

class MicrosoftScraper(BaseScraper):
    """Scraper for Microsoft Azure AI customer stories"""
    
    def __init__(self):
        super().__init__(
            source_name="Microsoft",
            base_url="https://www.microsoft.com/en-us/ai/ai-customer-stories"
        )
        
        # Microsoft-specific AI keywords for filtering mixed content
        self.ai_keywords = {
            'azure ai', 'azure openai', 'cognitive services', 'machine learning',
            'artificial intelligence', 'copilot', 'ai foundry', 'generative ai',
            'azure ai search', 'azure ai content safety', 'language models',
            'computer vision', 'speech services', 'bot framework', 'power platform ai',
            'ai builder', 'form recognizer', 'text analytics', 'translator',
            'personalizer', 'anomaly detector', 'metrics advisor', 'immersive reader'
        }
    
    def get_customer_story_urls(self) -> List[str]:
        """Get list of Microsoft AI customer story URLs - Enhanced with pre-collected URLs"""
        
        # First, try to load pre-collected URLs from the 1000+ stories blog extraction
        pre_collected_urls = self._load_pre_collected_urls()
        
        if pre_collected_urls:
            logger.info(f"Using {len(pre_collected_urls)} pre-collected URLs from Microsoft 1000+ stories blog")
            self._using_pre_collected = True  # Flag to skip AI filtering
            return pre_collected_urls
        
        # Fallback to original discovery method if pre-collected URLs not available
        logger.info(f"Pre-collected URLs not found, falling back to original discovery from {self.base_url}")
        
        response = self.make_request(self.base_url)
        if not response:
            return []
        
        soup = self.parse_html(response.text)
        story_urls = []
        
        # Look for story links in the carousel/grid structure
        # Microsoft uses go.microsoft.com/fwlink/?linkid= pattern
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            
            # Look for Microsoft customer story patterns
            if any(pattern in href.lower() for pattern in [
                'go.microsoft.com/fwlink',
                'microsoft.com/en/customers/story',
                'azure.microsoft.com/en-us/resources/customer-stories'
            ]):
                if href not in story_urls:
                    story_urls.append(href)
        
        # Also check for any embedded story data or alternative URL patterns
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                script_content = script.get_text()
                # Look for URLs in JSON data
                potential_urls = re.findall(r'https://[^"]*(?:customers?|story)[^"]*', script_content)
                for url in potential_urls:
                    if url not in story_urls and self._is_valid_story_url(url):
                        story_urls.append(url)
            except Exception as e:
                logger.debug(f"Error parsing script tag: {e}")
        
        logger.info(f"Found {len(story_urls)} potential story URLs using original discovery")
        return story_urls
    
    def _load_pre_collected_urls(self) -> List[str]:
        """Load pre-collected Microsoft story URLs from the 1000+ stories blog extraction"""
        import json
        import os
        
        # Look for the pre-collected URLs file in the project root
        json_file = 'microsoft_story_links.json'
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    urls = data.get('links', [])
                    logger.info(f"Successfully loaded {len(urls)} pre-collected URLs")
                    return urls
            except Exception as e:
                logger.warning(f"Error loading pre-collected URLs: {e}")
        
        return []
    
    def _is_valid_story_url(self, url: str) -> bool:
        """Check if URL is a valid Microsoft customer story URL"""
        invalid_patterns = [
            'javascript:', 'mailto:', '#', 'tel:',
            '/privacy', '/terms', '/support', '/legal'
        ]
        
        return not any(pattern in url.lower() for pattern in invalid_patterns)
    
    def scrape_story(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual Microsoft customer story"""
        logger.info(f"Scraping Microsoft story: {url}")
        
        response = self.make_request(url)
        if not response:
            return None
        
        soup = self.parse_html(response.text)
        
        # Skip AI filtering for pre-collected URLs since Microsoft states all are AI-related
        # Check if this is an AI-related story (only for discovered URLs)
        if not hasattr(self, '_using_pre_collected') and not self._is_ai_story(soup, response.text):
            logger.info(f"Skipping non-AI story: {url}")
            return None
        
        # Extract customer name
        customer_name = self.extract_customer_name(soup, url)
        if not customer_name:
            logger.warning(f"Could not extract customer name from {url}")
            return None
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract publish date
        publish_date = self._extract_publish_date(soup)
        
        # Create raw content structure
        raw_content = self.create_raw_content(response, soup)
        
        # Generate content hash
        content_hash = generate_content_hash(raw_content.get('text', ''))
        
        return {
            'customer_name': customer_name,
            'title': title,
            'url': response.url,  # Use final URL after redirects
            'publish_date': publish_date,
            'raw_content': raw_content,
            'content_hash': content_hash
        }
    
    def extract_customer_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract customer name from Microsoft story page"""
        
        # Strategy 1: Look for customer name in title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # Microsoft titles often follow pattern: "Company Name | Microsoft Customer Story"
            title_parts = title_text.split('|')
            if len(title_parts) > 1:
                potential_name = title_parts[0].strip()
                if potential_name and potential_name.lower() != 'microsoft':
                    return potential_name
        
        # Strategy 2: Look for customer name in main heading
        headings = soup.find_all(['h1', 'h2'], class_=True)
        for heading in headings:
            text = heading.get_text().strip()
            # Look for patterns like "Accenture" or "Company increases efficiency"
            if text and len(text) < 100 and not any(word in text.lower() for word in ['microsoft', 'azure', 'story', 'case study']):
                return text.split()[0] if text.split() else text
        
        # Strategy 3: Look for customer logo or name in specific sections
        customer_sections = soup.find_all(['div', 'section'], class_=re.compile(r'customer|client|company', re.I))
        for section in customer_sections:
            img = section.find('img')
            if img and img.get('alt'):
                alt_text = img.get('alt').strip()
                if alt_text and alt_text.lower() not in ['microsoft', 'azure', 'logo']:
                    # Clean up alt text (often contains "logo" suffix)
                    customer_name = re.sub(r'\s+logo\s*$', '', alt_text, flags=re.I)
                    return customer_name
        
        # Strategy 4: Extract from URL pattern
        url_patterns = [
            r'/([^/]+)-(?:azure|microsoft|customer|story)',
            r'/story/\d+-([^-]+)-',
            r'/customers/([^/]+)/?$'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url, re.I)
            if match:
                customer_name = match.group(1).replace('-', ' ').title()
                if customer_name and customer_name.lower() not in ['azure', 'microsoft', 'story', 'customer']:
                    return customer_name
        
        # Strategy 5: Look for quoted customer statements (often contains company name)
        quotes = soup.find_all(['blockquote', 'q'])
        for quote in quotes:
            quote_text = quote.get_text().strip()
            # Look for attribution patterns
            attribution_match = re.search(r'[-–—]\s*([^,]+),\s*([^,]+)', quote_text)
            if attribution_match:
                potential_company = attribution_match.group(2).strip()
                if potential_company and len(potential_company) < 50:
                    return potential_company
        
        return "Unknown Customer"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract story title from Microsoft page"""
        
        # Strategy 1: Main page title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # Clean up Microsoft title patterns
            title_text = re.sub(r'\s*\|\s*Microsoft.*$', '', title_text)
            if title_text:
                return title_text
        
        # Strategy 2: Main heading (h1)
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # Strategy 3: Hero section heading
        hero_headings = soup.find_all(['h1', 'h2'], class_=re.compile(r'hero|main|title', re.I))
        for heading in hero_headings:
            text = heading.get_text().strip()
            if text and len(text) > 10:  # Reasonable title length
                return text
        
        return "Microsoft Customer Story"
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date from Microsoft story page"""
        
        # Strategy 1: Look for date in meta tags
        date_meta = soup.find('meta', {'name': 'date'}) or soup.find('meta', {'property': 'article:published_time'})
        if date_meta:
            date_str = date_meta.get('content', '')
            parsed_date = self._parse_date_string(date_str)
            if parsed_date:
                return parsed_date
        
        # Strategy 2: Look for date patterns in text content
        text_content = soup.get_text()
        date_patterns = [
            r'Published:?\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Date:?\s*(\d{1,2}/\d{1,2}/\d{4})',  
            r'(\d{1,2}/\d{1,2}/\d{4})',  # Basic MM/DD/YYYY pattern
            r'Published:?\s*([A-Za-z]+ \d{1,2},? \d{4})',  # "January 15, 2025"
            r'(\d{4}-\d{2}-\d{2})'  # ISO format
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                parsed_date = self._parse_date_string(match)
                if parsed_date:
                    return parsed_date
        
        # Strategy 3: Look in time tags
        time_tags = soup.find_all('time')
        for time_tag in time_tags:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                parsed_date = self._parse_date_string(datetime_attr)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date string formats into YYYY-MM-DD"""
        if not date_str:
            return None
        
        # Common date formats to try
        formats = [
            '%m/%d/%Y',      # 5/19/2025
            '%m-%d-%Y',      # 5-19-2025
            '%Y-%m-%d',      # 2025-05-19
            '%B %d, %Y',     # May 19, 2025
            '%b %d, %Y',     # May 19, 2025
            '%d %B %Y',      # 19 May 2025
            '%Y-%m-%dT%H:%M:%S',  # ISO datetime
            '%Y-%m-%dT%H:%M:%SZ'  # ISO datetime with Z
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try to extract just year-month-day from longer strings
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if date_match:
            return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            
        return None
    
    def _is_ai_story(self, soup: BeautifulSoup, html_content: str) -> bool:
        """Check if story is AI-related using keyword analysis"""
        
        # Get full text content for analysis
        text_content = soup.get_text().lower()
        html_lower = html_content.lower()
        
        # Count AI keyword matches
        ai_keyword_count = 0
        for keyword in self.ai_keywords:
            if keyword in text_content or keyword in html_lower:
                ai_keyword_count += 1
        
        # Check title for AI indicators
        title_tag = soup.find('title')
        title_has_ai = False
        if title_tag:
            title_text = title_tag.get_text().lower()
            title_has_ai = any(keyword in title_text for keyword in ['ai', 'artificial intelligence', 'copilot', 'machine learning'])
        
        # Decision logic: story is AI-related if:
        # 1. Has AI keywords in title, OR
        # 2. Has multiple AI keyword matches in content (threshold: 2+)
        is_ai_story = title_has_ai or ai_keyword_count >= 2
        
        logger.debug(f"AI story analysis - Keywords found: {ai_keyword_count}, Title has AI: {title_has_ai}, Result: {is_ai_story}")
        
        return is_ai_story