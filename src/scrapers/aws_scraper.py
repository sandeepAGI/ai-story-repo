import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.database.models import generate_content_hash

logger = logging.getLogger(__name__)

class AWScraper(BaseScraper):
    """Scraper for AWS AI/ML customer stories"""
    
    def __init__(self):
        super().__init__(
            source_name="AWS",
            base_url="https://aws.amazon.com/ai/generative-ai/customers/"
        )
        
        # AWS-specific AI/ML keywords for filtering mixed content
        self.ai_keywords = {
            'generative ai', 'amazon bedrock', 'sagemaker', 'machine learning',
            'artificial intelligence', 'amazon q', 'rekognition', 'comprehend',
            'textract', 'translate', 'polly', 'transcribe', 'lex', 'kendra',
            'personalize', 'forecast', 'fraud detector', 'lookout', 'code guru',
            'deep learning', 'computer vision', 'natural language processing',
            'nlp', 'llm', 'large language model', 'claude', 'llama', 'titan',
            'ai services', 'ml services', 'neural networks', 'aws ai'
        }
        
        # Alternative URLs to try for comprehensive coverage
        self.secondary_urls = [
            "https://aws.amazon.com/solutions/case-studies/",
            "https://aws.amazon.com/machine-learning/customers/",
            "https://aws.amazon.com/ai/customers/"
        ]
    
    def get_customer_story_urls(self) -> List[str]:
        """Get list of AWS AI/ML customer story URLs"""
        logger.info(f"Fetching customer story URLs from AWS")
        
        all_story_urls = []
        
        # Start with the primary generative AI customers page
        urls_to_check = [self.base_url] + self.secondary_urls
        
        for url in urls_to_check:
            logger.info(f"Checking URL: {url}")
            response = self.make_request(url)
            if not response:
                continue
            
            soup = self.parse_html(response.text)
            story_urls = self._extract_urls_from_page(soup, response.text)
            
            for story_url in story_urls:
                if story_url not in all_story_urls:
                    all_story_urls.append(story_url)
        
        logger.info(f"Found {len(all_story_urls)} total AWS story URLs")
        return all_story_urls
    
    def _extract_urls_from_page(self, soup: BeautifulSoup, html_content: str) -> List[str]:
        """Extract story URLs from an AWS page"""
        story_urls = []
        
        # Strategy 1: Look for direct case study links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            
            # Look for AWS case study patterns
            if any(pattern in href.lower() for pattern in [
                'case-studies/',
                'case-study/',
                'customer-stories/',
                'customers/'
            ]):
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = f"https://aws.amazon.com{href}"
                elif not href.startswith('http'):
                    continue
                    
                if self._is_valid_story_url(href) and href not in story_urls:
                    story_urls.append(href)
        
        # Strategy 2: Look for URLs in JSON data structures
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                script_content = script.get_text()
                # Look for case study URLs in JSON
                potential_urls = re.findall(r'https://aws\.amazon\.com[^"]*(?:case-stud|customer)[^"]*', script_content)
                for url in potential_urls:
                    if self._is_valid_story_url(url) and url not in story_urls:
                        story_urls.append(url)
            except Exception as e:
                logger.debug(f"Error parsing script tag: {e}")
        
        # Strategy 3: Look for embedded data attributes
        story_elements = soup.find_all(attrs={"data-href": True})
        for element in story_elements:
            href = element.get('data-href', '')
            if 'case-stud' in href or 'customer' in href:
                if href.startswith('/'):
                    href = f"https://aws.amazon.com{href}"
                if self._is_valid_story_url(href) and href not in story_urls:
                    story_urls.append(href)
        
        return story_urls
    
    def _is_valid_story_url(self, url: str) -> bool:
        """Check if URL is a valid AWS customer story URL"""
        if not url or not isinstance(url, str):
            return False
            
        # Must be AWS domain
        if 'aws.amazon.com' not in url:
            return False
        
        # Invalid patterns to exclude (listing pages, navigation, etc.)
        invalid_patterns = [
            'javascript:', 'mailto:', '#', 'tel:',
            '/privacy', '/terms', '/support', '/legal',
            '/contact', '/signup', '/pricing', '/console',
            'aws.amazon.com/solutions/case-studies/?',  # Landing pages only
            'aws.amazon.com/solutions/case-studies/#',  # Fragment-only URLs
            'aws.amazon.com/ai/generative-ai/customers/?',  # Landing page
            'aws.amazon.com/ai/generative-ai/customers/#',  # Fragment
            'aws.amazon.com/generative-ai/customers/?',     # Landing page 
            'aws.amazon.com/generative-ai/customers/#',     # Fragment
            'aws.amazon.com/machine-learning/customers/?',  # Landing page
            'aws.amazon.com/machine-learning/customers/#',  # Fragment
        ]
        
        for pattern in invalid_patterns:
            if pattern in url.lower():
                return False
        
        # Exclude exact landing page URLs (without trailing paths)
        landing_pages = [
            'aws.amazon.com/ai/generative-ai/customers/',
            'aws.amazon.com/generative-ai/customers/',
            'aws.amazon.com/solutions/case-studies/',
            'aws.amazon.com/machine-learning/customers/'
        ]
        
        for landing in landing_pages:
            if url.lower().rstrip('/').endswith(landing.rstrip('/')):
                return False
        
        # Must contain case study or customer story indicators with actual customer path
        valid_patterns = [
            ('case-studies/', '/'),  # Must have path after case-studies/
            ('customers/', '/'),     # Must have path after customers/
        ]
        
        for pattern, required_suffix in valid_patterns:
            if pattern in url.lower():
                # Check if there's content after the pattern
                pattern_pos = url.lower().find(pattern)
                if pattern_pos >= 0:
                    after_pattern = url[pattern_pos + len(pattern):]
                    # Must have meaningful content after the pattern (not just trailing slash)
                    if after_pattern and after_pattern.strip('/'):
                        return True
        
        return False
    
    def scrape_story(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual AWS customer story"""
        logger.info(f"Scraping AWS story: {url}")
        
        response = self.make_request(url)
        if not response:
            return None
        
        soup = self.parse_html(response.text)
        
        # Check if this is an AI/ML-related story
        if not self._is_ai_story(soup, response.text):
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
        """Extract customer name from AWS story page"""
        
        # Strategy 1: Look for customer name in title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # AWS titles often follow pattern: "Company Case Study | AWS"
            if ' Case Study' in title_text:
                customer_name = title_text.split(' Case Study')[0].strip()
                if customer_name and customer_name.lower() not in ['aws', 'amazon']:
                    return customer_name
            
            # Alternative patterns: "Company | AWS" or "Company Success Story"
            title_parts = title_text.split('|')
            if len(title_parts) > 1:
                potential_name = title_parts[0].strip()
                if potential_name and potential_name.lower() not in ['aws', 'amazon']:
                    return potential_name
        
        # Strategy 2: Look for customer name in main heading
        headings = soup.find_all(['h1', 'h2', 'h3'], class_=True)
        for heading in headings:
            text = heading.get_text().strip()
            # Look for patterns like "Company Case Study" or "How Company..."
            if 'case study' in text.lower():
                customer_name = re.sub(r'\s+case study.*$', '', text, flags=re.I).strip()
                if customer_name and len(customer_name) < 100:
                    return customer_name
            elif text.startswith('How ') and len(text) < 100:
                # Extract company name from "How [Company] achieved..."
                match = re.match(r'How\s+([^,\s]+(?:\s+[^,]+)*)', text)
                if match:
                    return match.group(1).strip()
        
        # Strategy 3: Look for customer logo or company information
        # AWS often has customer logos with alt text
        imgs = soup.find_all('img')
        for img in imgs:
            alt_text = img.get('alt', '').strip()
            if alt_text and 'logo' in alt_text.lower():
                # Clean up alt text (remove "logo" and common suffixes)
                customer_name = re.sub(r'\s+logo\s*$', '', alt_text, flags=re.I)
                customer_name = re.sub(r'\s+customer\s*$', '', customer_name, flags=re.I)
                if customer_name and customer_name.lower() not in ['aws', 'amazon']:
                    return customer_name
        
        # Strategy 4: Extract from URL pattern (AWS specific patterns)
        url_patterns = [
            r'/case-studies/([^/-]+)-(?:case-study|bedrock|sagemaker)',  # /case-studies/company-name-service
            r'/case-studies/([^/]+)/?$',     # /case-studies/company/
            r'/customers/([^/-]+)/?$',       # /customers/company/
            r'/([^/]+)-(?:case-study|success)',  # /company-case-study
            r'/generative-ai/customers/([^/-]+)/?',  # /generative-ai/customers/company/
            r'/ai/generative-ai/customers/([^/-]+)/?'  # /ai/generative-ai/customers/company/
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url, re.I)
            if match:
                customer_name = match.group(1).replace('-', ' ').replace('_', ' ').title()
                # Filter out common AWS terms and generic words
                excluded_terms = ['aws', 'amazon', 'case', 'study', 'customer', 'stories', 'success', 'story', 'bedrock', 'sagemaker']
                if customer_name.lower() not in excluded_terms and len(customer_name) > 2:
                    return customer_name
        
        # Strategy 5: Look for company mentions in content
        text_content = soup.get_text()
        # Look for patterns like "Company is" or "Company uses"
        company_patterns = [
            r'"([^"]+)"\s+is\s+(?:a|an)\s+',
            r'([A-Z][a-zA-Z\s&]+)\s+is\s+(?:a|an)\s+(?:leading|global|major)',
            r'([A-Z][a-zA-Z\s&]+)\s+uses?\s+AWS'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                if len(match) < 50 and match.lower() not in ['aws', 'amazon', 'the company']:
                    return match.strip()
        
        return "Unknown Customer"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract story title from AWS page"""
        
        # Strategy 1: Main page title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # Clean up AWS title patterns
            title_text = re.sub(r'\s*\|\s*AWS.*$', '', title_text)
            title_text = re.sub(r'\s*-\s*Amazon Web Services.*$', '', title_text)
            if title_text:
                return title_text
        
        # Strategy 2: Main heading (h1)
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # Strategy 3: Hero section or case study heading
        headings = soup.find_all(['h1', 'h2'], class_=re.compile(r'hero|main|title|case-study', re.I))
        for heading in headings:
            text = heading.get_text().strip()
            if text and len(text) > 10:  # Reasonable title length
                return text
        
        # Strategy 4: Meta description as fallback
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
            if description and len(description) < 200:
                return description
        
        return "AWS Customer Case Study"
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date from AWS story page"""
        
        # Strategy 1: Look for date in meta tags
        date_meta_selectors = [
            {'name': 'date'},
            {'property': 'article:published_time'},
            {'name': 'publish_date'},
            {'name': 'publication_date'},
            {'property': 'og:updated_time'}
        ]
        
        for selector in date_meta_selectors:
            date_meta = soup.find('meta', selector)
            if date_meta:
                date_str = date_meta.get('content', '')
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return parsed_date
        
        # Strategy 2: Look for time tags with datetime attribute
        time_tags = soup.find_all('time')
        for time_tag in time_tags:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                parsed_date = self._parse_date_string(datetime_attr)
                if parsed_date:
                    return parsed_date
        
        # Strategy 3: Look for date patterns in specific sections
        date_sections = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'date|publish|time', re.I))
        for section in date_sections:
            text = section.get_text()
            parsed_date = self._extract_date_from_text(text)
            if parsed_date:
                return parsed_date
        
        # Strategy 4: Look for date patterns in general text content
        text_content = soup.get_text()
        return self._extract_date_from_text(text_content)
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date from text using various patterns"""
        date_patterns = [
            r'Published:?\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Date:?\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Updated:?\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',  # Basic MM/DD/YYYY pattern
            r'Published:?\s*([A-Za-z]+ \d{1,2},? \d{4})',  # "January 15, 2025"
            r'(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})',  # ISO format
            r'(\d{1,2}-\d{1,2}-\d{4})'  # DD-MM-YYYY or MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                parsed_date = self._parse_date_string(match)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date string formats into YYYY-MM-DD"""
        if not date_str:
            return None
        
        # Clean up the date string
        date_str = date_str.strip()
        
        # Common date formats to try
        formats = [
            '%m/%d/%Y',      # 5/19/2025
            '%m-%d-%Y',      # 5-19-2025
            '%d/%m/%Y',      # 19/5/2025 (European format)
            '%d-%m-%Y',      # 19-5-2025
            '%Y-%m-%d',      # 2025-05-19
            '%B %d, %Y',     # May 19, 2025
            '%b %d, %Y',     # May 19, 2025
            '%d %B %Y',      # 19 May 2025
            '%d %b %Y',      # 19 May 2025
            '%Y-%m-%dT%H:%M:%S',  # ISO datetime
            '%Y-%m-%dT%H:%M:%SZ',  # ISO datetime with Z
            '%Y-%m-%dT%H:%M:%S.%fZ'  # ISO datetime with microseconds
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try to extract just year-month-day from longer strings
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if date_match:
            return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        
        # Try to extract from patterns like "May 19, 2025"
        month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', date_str, re.I)
        if month_match:
            month_name, day, year = month_match.groups()
            try:
                month_num = datetime.strptime(month_name, '%B').month
                return f"{year}-{month_num:02d}-{int(day):02d}"
            except ValueError:
                pass
        
        return None
    
    def _is_ai_story(self, soup: BeautifulSoup, html_content: str) -> bool:
        """Check if story is AI/ML-related using keyword analysis"""
        
        # Get full text content for analysis
        text_content = soup.get_text().lower()
        html_lower = html_content.lower()
        
        # Count AI keyword matches
        ai_keyword_count = 0
        matched_keywords = []
        
        for keyword in self.ai_keywords:
            if keyword in text_content or keyword in html_lower:
                ai_keyword_count += 1
                matched_keywords.append(keyword)
        
        # Check title for AI indicators
        title_tag = soup.find('title')
        title_has_ai = False
        if title_tag:
            title_text = title_tag.get_text().lower()
            title_has_ai = any(keyword in title_text for keyword in [
                'ai', 'artificial intelligence', 'machine learning', 'ml',
                'generative', 'bedrock', 'sagemaker', 'amazon q'
            ])
        
        # Check URL for AI indicators
        url_has_ai = any(indicator in html_content.lower() for indicator in [
            'generative-ai', 'ai/', 'machine-learning', 'ml/'
        ])
        
        # Decision logic: story is AI-related if:
        # 1. Has AI keywords in title OR URL, OR
        # 2. Has multiple AI keyword matches in content (threshold: 3+ for AWS due to mixed content)
        is_ai_story = title_has_ai or url_has_ai or ai_keyword_count >= 3
        
        logger.debug(f"AI story analysis - Keywords found: {ai_keyword_count} {matched_keywords}, Title has AI: {title_has_ai}, URL has AI: {url_has_ai}, Result: {is_ai_story}")
        
        return is_ai_story