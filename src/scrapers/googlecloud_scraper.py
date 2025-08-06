import re
import json
import os
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
    
    def _load_pre_collected_urls(self) -> List[str]:
        """Load pre-collected URLs from extraction utility (similar to Microsoft approach)"""
        try:
            # Check for pre-collected URLs file in the project root
            urls_file = 'google_cloud_story_urls_urls_only.json'
            if os.path.exists(urls_file):
                with open(urls_file, 'r', encoding='utf-8') as f:
                    urls = json.load(f)
                    if isinstance(urls, list) and urls:
                        logger.info(f"Loaded {len(urls)} pre-collected URLs from {urls_file}")
                        return urls
                    else:
                        logger.warning(f"Invalid format or empty URLs list in {urls_file}")
            else:
                logger.debug(f"Pre-collected URLs file {urls_file} not found")
        except Exception as e:
            logger.warning(f"Error loading pre-collected URLs: {e}")
        
        return []
    
    def _is_pre_collected_url(self, url: str) -> bool:
        """Check if URL is from pre-collected list (no AI filtering needed)"""
        # Cache pre-collected URLs for performance
        if not hasattr(self, '_pre_collected_urls_cache'):
            self._pre_collected_urls_cache = set(self._load_pre_collected_urls())
        return url in self._pre_collected_urls_cache
    
    def get_customer_story_urls(self) -> List[str]:
        """Get list of Google Cloud AI/ML customer story URLs"""
        logger.info(f"Fetching customer story URLs from Google Cloud")
        
        all_story_urls = []
        
        # Strategy 1: Load pre-collected URLs from extraction utility (similar to Microsoft approach)
        pre_collected_urls = self._load_pre_collected_urls()
        if pre_collected_urls:
            logger.info(f"Loaded {len(pre_collected_urls)} pre-collected URLs from extraction")
            all_story_urls.extend(pre_collected_urls)
        else:
            logger.info("No pre-collected URLs found, using fallback discovery methods")
            
            # Fallback Strategy 1: Start with known AI customer URLs
            logger.info(f"Adding {len(self.known_ai_customers)} known AI customer URLs")
            for url in self.known_ai_customers:
                if url not in all_story_urls:
                    all_story_urls.append(url)
            
            # Fallback Strategy 2: Try to discover additional URLs from listing pages
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
        """Check if URL is a valid Google Cloud customer story (expanded for web search results)"""
        if not url or not url.startswith('https://cloud.google.com/'):
            return False
            
        # Accept broader range of content types (for web search enhancement)
        valid_patterns = [
            '/customers/',
            '/blog/',
            '/solutions/',
            '/case-studies/',
            '/success-stories/'
        ]
        
        if not any(pattern in url for pattern in valid_patterns):
            return False
            
        # Exclude listing pages and non-story URLs
        exclusions = [
            '/customers?', '/customers#', '/search', '/browse', '/filter', 
            '/category', '/industry', '/size', '/tag',
            'cloud.google.com/blog/rss', 'cloud.google.com/blog/feed'
        ]
        
        # Special case: exclude base pages
        if url.endswith('/customers') or url.endswith('/customers/') or url.endswith('/blog') or url.endswith('/blog/'):
            return False
        
        for exclusion in exclusions:
            if url.endswith(exclusion) or exclusion + '?' in url:
                return False
        
        # For customer URLs, must have a customer name/slug after /customers/
        if '/customers/' in url:
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
        
        # Smart AI filtering: skip for discovered URLs but not for pre-collected URLs
        # (similar to Microsoft approach - pre-collected URLs are verified AI stories)
        if not self._is_pre_collected_url(url):
            full_text = soup.get_text().lower()
            if not self._is_ai_story(full_text):
                logger.info(f"Skipping non-AI story: {url}")
                return None
        else:
            logger.debug(f"Pre-collected URL - skipping AI content filter: {url}")
        
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
        
        # Strategy 1: Handle different URL types
        if '/customers/' in url:
            # Customer page URLs: https://cloud.google.com/customers/company-name
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
        
        elif '/blog/' in url:
            # Blog URLs: https://cloud.google.com/blog/topics/retail/how-google-cloud-services-helped-lowes-transform-ecommerce
            title = self._extract_title(soup)
            
            # Strategy 1a: Extract from title first (most reliable for blog posts)
            if title:
                extracted_name = self._extract_company_from_title(title)
                if extracted_name:
                    return extracted_name
            
            # Strategy 1b: Extract from URL patterns
            extracted_name = self._extract_company_from_blog_url(url)
            if extracted_name:
                return extracted_name
        
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
    
    def _extract_company_from_title(self, title: str) -> str:
        """Extract company name from blog post title"""
        if not title:
            return None
            
        # Common patterns in GoogleCloud blog titles
        patterns = [
            # "How Lowe's improved incident response processes with SRE"
            r"How\s+([A-Z][a-zA-Z.'&\s]+?)\s+(?:uses?|improved?|transforms?|leverages?|builds?|reduces?|collects?)",
            # "Learn how Google Cloud Services helped Lowe's transform ecommerce"  
            r"(?:how\s+Google\s+Cloud\s+(?:Services?\s+)?helped\s+)([A-Z][a-zA-Z.'&\s]+?)\s+(?:transform|improve|build|reduce)",
            # "Coca-Cola Bottlers Japan collects insights from 700,000 vending machines"
            r"^([A-Z][a-zA-Z.'&\s-]+?)\s+(?:uses?|collects?|builds?|reduces?|improves?|transforms?|leverages?)",
            # "Ford reduces routine database management with Google Cloud"
            r"^([A-Z][a-zA-Z.'&\s]+?)\s+reduces?",
            # "The Home Depot uses Google Cloud to personalize"
            r"^(The\s+[A-Z][a-zA-Z.'&\s]+?)\s+uses?",
            # "Wells Fargo's head of tech infrastructure"
            r"^([A-Z][a-zA-Z.'&\s]+?)'s\s+",
            # Company name at start followed by action
            r"^([A-Z][a-zA-Z.'&\s]+?)\s+(?:and|on|profile|\|)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                
                # Clean up the company name
                company = self._clean_company_name(company)
                
                # Validate it's a reasonable company name
                if self._is_valid_company_name(company):
                    return company
        
        return None
    
    def _extract_company_from_blog_url(self, url: str) -> str:
        """Extract company name from blog URL path"""
        
        # Common URL patterns in GoogleCloud blog URLs
        patterns = [
            # /how-google-cloud-services-helped-lowes-transform-ecommerce
            r"/(?:how-)?(?:google-cloud-(?:services?-)?helped-)?([a-z]+(?:-[a-z]+)*)-(?:transform|improve|build|reduce|use)",
            # /how-lowes-improved-incident-response-processes-with-sre
            r"/how-([a-z]+(?:-[a-z]+)*)-(?:improved?|transforms?|builds?|reduces?|uses?)",
            # /coca-cola-bottlers-japan-collects-insights
            r"/([a-z]+(?:-[a-z]+)*)-(?:collects?|builds?|reduces?|uses?|transforms?)",
            # /ford-reduces-routine-database-management
            r"/([a-z]+(?:-[a-z]+)*)-reduces?",
            # General pattern: company name followed by action
            r"/([a-z]+(?:-[a-z]+)*)-(?:case-study|success|story|profile|winner)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                company_slug = match.group(1)
                
                # Convert slug to proper company name
                company = company_slug.replace('-', ' ').title()
                
                # Clean up the company name
                company = self._clean_company_name(company)
                
                # Validate it's a reasonable company name
                if self._is_valid_company_name(company):
                    return company
        
        return None
    
    def _clean_company_name(self, company: str) -> str:
        """Clean and normalize company name"""
        if not company:
            return company
            
        # Remove common suffixes that might be included
        company = re.sub(r'\s*\|\s*Google\s+Cloud.*$', '', company, flags=re.IGNORECASE)
        company = re.sub(r'\s*-\s*Google\s+Cloud.*$', '', company, flags=re.IGNORECASE)
        
        # Handle special cases
        company = company.strip()
        
        # Fix common company name patterns
        if company.lower() == 'the home depot':
            return 'The Home Depot'
        elif company.lower() in ['coca cola', 'coca-cola']:
            return 'Coca-Cola'
        elif company.lower() == 'wells fargo':
            return 'Wells Fargo'
        elif 'lowes' in company.lower():
            return "Lowe's"  # Add apostrophe
        
        return company
    
    def _is_valid_company_name(self, company: str) -> bool:
        """Validate if the extracted text is a reasonable company name"""
        if not company or len(company) < 2:
            return False
            
        # Filter out common non-company words
        invalid_words = {
            'google', 'cloud', 'services', 'service', 'how', 'with', 'and', 'the', 
            'to', 'of', 'for', 'in', 'on', 'at', 'by', 'from', 'up', 'about', 
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'blog', 'topics', 'customers', 'products', 'solutions', 'case', 'study'
        }
        
        company_lower = company.lower()
        
        # Don't accept if it's just a common word
        if company_lower in invalid_words:
            return False
            
        # Don't accept if it's too long (probably extracted too much text)
        if len(company) > 50:
            return False
        
        # Must start with a capital letter or number
        if not company[0].isupper() and not company[0].isdigit():
            return False
            
        return True
    
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