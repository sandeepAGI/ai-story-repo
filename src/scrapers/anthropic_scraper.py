import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from src.scrapers.base_scraper import BaseScraper
from src.database.models import generate_content_hash

logger = logging.getLogger(__name__)

class AnthropicScraper(BaseScraper):
    def __init__(self):
        super().__init__("Anthropic", "https://www.anthropic.com/customers")
        
    def get_customer_story_urls_with_dates(self) -> List[Dict[str, str]]:
        """Get list of customer story URLs with publish dates from Anthropic customers page"""
        logger.info("Fetching Anthropic customer story URLs with dates")
        
        response = self.make_request(self.base_url)
        if not response:
            logger.error("Failed to fetch customer list page")
            return []
        
        soup = self.parse_html(response.text)
        story_data = []
        
        # Look for story cards that contain both URLs and dates
        story_cards = soup.find_all('a', class_=lambda x: x and 'post-card' in str(x))
        
        for card in story_cards:
            href = card.get('href', '')
            
            # Match customer story URLs pattern
            if '/customers/' in href and href != '/customers' and href != '/customers/':
                # Convert relative URLs to absolute
                full_url = urljoin(self.base_url, href)
                
                # Look for date in this card
                date_element = card.find('div', class_=lambda x: x and 'post-date' in str(x))
                publish_date = None
                
                if date_element:
                    date_text = date_element.get_text().strip()
                    # Convert "Jul 23, 2025" format to ISO date
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(date_text, "%b %d, %Y")
                        publish_date = parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        logger.warning(f"Could not parse date: {date_text}")
                
                story_info = {
                    'url': full_url,
                    'publish_date': publish_date
                }
                
                # Avoid duplicates
                if not any(s['url'] == full_url for s in story_data):
                    story_data.append(story_info)
        
        # Fallback: Look for any customer links without dates
        if not story_data:
            customer_links = soup.find_all('a', href=re.compile(r'/customers/[^/]+$'))
            for link in customer_links:
                href = link.get('href', '')
                full_url = urljoin(self.base_url, href)
                if not any(s['url'] == full_url for s in story_data):
                    story_data.append({'url': full_url, 'publish_date': None})
        
        logger.info(f"Found {len(story_data)} customer stories with date info")
        return story_data
    
    def get_customer_story_urls(self) -> List[str]:
        """Get list of customer story URLs (backward compatibility)"""
        story_data = self.get_customer_story_urls_with_dates()
        return [story['url'] for story in story_data]
    
    def scrape_story(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual Anthropic customer story"""
        logger.info(f"Scraping Anthropic story: {url}")
        
        response = self.make_request(url)
        if not response:
            return None
        
        soup = self.parse_html(response.text)
        
        try:
            # Extract customer name from URL and/or page content
            customer_name = self.extract_customer_name(soup, url)
            
            # Extract title
            title = self.extract_title(soup)
            
            # Create raw content structure
            raw_content = self.create_raw_content(response, soup)
            
            # Generate content hash for deduplication
            content_hash = generate_content_hash(raw_content['text'])
            
            return {
                'url': url,
                'customer_name': customer_name,
                'title': title,
                'raw_content': raw_content,
                'content_hash': content_hash,
                'source_name': self.source_name
            }
            
        except Exception as e:
            logger.error(f"Error scraping story {url}: {e}")
            return None
    
    def extract_customer_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract customer name from Anthropic story page"""
        # Method 1: Extract from URL (most reliable for Anthropic)
        url_path = urlparse(url).path
        if '/customers/' in url_path:
            # Extract company name from URL path
            company_slug = url_path.split('/customers/')[-1].split('/')[0]
            # Convert slug to proper name (basic capitalization)
            customer_name = company_slug.replace('-', ' ').replace('_', ' ').title()
        else:
            customer_name = "Unknown"
        
        # Method 2: Try to find customer name in page content
        # Look for common patterns in Anthropic customer stories
        
        # Check for customer name in title tag
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            # Common pattern: "Company Name - Anthropic" or "How Company Name uses Claude"
            if ' - Anthropic' in title_text:
                potential_name = title_text.split(' - Anthropic')[0].strip()
                if len(potential_name) > 2 and len(potential_name) < 50:
                    customer_name = potential_name
        
        # Look for h1 or main heading that might contain company name
        h1_tag = soup.find('h1')
        if h1_tag and customer_name == "Unknown":
            h1_text = h1_tag.get_text().strip()
            # If H1 looks like a company name, use it
            if len(h1_text) > 2 and len(h1_text) < 50 and not h1_text.lower().startswith('how '):
                customer_name = h1_text
        
        # Method 3: Look for specific selectors that Anthropic might use
        company_selectors = [
            '[data-company]',
            '.customer-name',
            '.company-name',
            '[class*="customer"]',
            '[class*="company"]'
        ]
        
        for selector in company_selectors:
            element = soup.select_one(selector)
            if element and customer_name == "Unknown":
                text = element.get_text().strip()
                if text and len(text) > 2 and len(text) < 50:
                    customer_name = text
                    break
        
        # Clean up the customer name
        customer_name = self.clean_customer_name(customer_name)
        
        logger.info(f"Extracted customer name: {customer_name}")
        return customer_name
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract story title from Anthropic page"""
        # Try different title extraction methods
        
        # Method 1: Page title tag
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # Clean up Anthropic-specific title patterns
            if ' - Anthropic' in title:
                title = title.replace(' - Anthropic', '').strip()
            if title and len(title) > 10:
                return title
        
        # Method 2: H1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_text = h1_tag.get_text().strip()
            if h1_text and len(h1_text) > 5:
                return h1_text
        
        # Method 3: Look for article title or main heading
        title_selectors = [
            'article h1',
            '.story-title',
            '.customer-story-title',
            'main h1',
            '[class*="title"]',
            'h2'  # Fallback to h2 if h1 not found
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                if text and len(text) > 5 and len(text) < 200:
                    return text
        
        return "Untitled Story"
    
    def clean_customer_name(self, name: str) -> str:
        """Clean and normalize customer name"""
        if not name or name == "Unknown":
            return name
        
        # Remove common suffixes and prefixes
        cleaning_patterns = [
            r'\s*-\s*Customer Story.*$',
            r'\s*-\s*Case Study.*$',
            r'^How\s+',
            r'\s+uses?\s+Claude.*$',
            r'\s+uses?\s+Anthropic.*$',
            r'\s*\|\s*Anthropic.*$',
        ]
        
        cleaned_name = name
        for pattern in cleaning_patterns:
            cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE).strip()
        
        # Basic capitalization for known company formats
        if cleaned_name.lower() in ['amazon', 'google', 'microsoft', 'apple', 'meta']:
            cleaned_name = cleaned_name.capitalize()
        
        return cleaned_name if cleaned_name else name
    
    def get_sample_story_urls(self) -> List[str]:
        """Get a few sample story URLs for testing"""
        sample_urls = [
            "https://www.anthropic.com/customers/hume",
            "https://www.anthropic.com/customers/lex"
        ]
        
        # Try to get a few more from the main page
        try:
            all_urls = self.get_customer_story_urls()
            # Add a few more URLs if available
            for url in all_urls[:5]:
                if url not in sample_urls:
                    sample_urls.append(url)
        except Exception as e:
            logger.warning(f"Could not fetch additional sample URLs: {e}")
        
        return sample_urls[:5]  # Return max 5 for testing