#!/usr/bin/env python3
"""
Google Cloud Customer Story URL Extraction Utility

This script extracts customer story URLs from multiple Google Cloud sources:
1. The "101 real-world generative AI use cases" blog post - extracts company names and searches for stories
2. The main customers page - systematically discovers AI/ML customer stories  
3. Additional discovery from Google Cloud blog and case study pages

Similar to the Microsoft approach but adapted for Google Cloud's content structure.
"""

import requests
import re
import json
import time
import logging
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GoogleCloudURLExtractor:
    """Enhanced URL extraction for Google Cloud AI customer stories"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # AI/GenAI keywords for filtering
        self.ai_keywords = {
            'artificial intelligence', 'ai', 'machine learning', 'ml', 'generative ai', 'genai',
            'vertex ai', 'gemini', 'palm', 'bard', 'automl', 'natural language', 'computer vision',
            'speech recognition', 'text-to-speech', 'translation', 'document ai', 'contact center ai',
            'recommendations ai', 'deep learning', 'neural network', 'tensorflow', 'large language model',
            'llm', 'chatbot', 'virtual assistant', 'predictive analytics', 'data insights'
        }
        
        # Sources to extract from
        self.sources = {
            'use_cases_blog': 'https://cloud.google.com/transform/101-real-world-generative-ai-use-cases-from-industry-leaders',
            'customers_page': 'https://cloud.google.com/customers?hl=en',
            'ai_solutions': 'https://cloud.google.com/ai',
            'case_studies': 'https://cloud.google.com/customers#case-studies'
        }
        
        self.discovered_urls = set()
        self.company_names = set()
        
    def extract_all_urls(self) -> Dict[str, List[str]]:
        """Extract URLs from all sources"""
        logger.info("Starting comprehensive Google Cloud URL extraction...")
        
        results = {
            'customer_story_urls': [],
            'company_names': [],
            'blog_urls': [],
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'sources_processed': [],
                'total_discovered': 0
            }
        }
        
        # Strategy 1: Extract company names from 101 use cases blog
        logger.info("Extracting from 101 GenAI use cases blog...")
        use_cases_data = self._extract_from_use_cases_blog()
        if use_cases_data:
            results['company_names'].extend(use_cases_data['companies'])
            results['blog_urls'].extend(use_cases_data['urls'])
            results['metadata']['sources_processed'].append('use_cases_blog')
        
        # Strategy 2: Discover from customers page
        logger.info("Discovering from main customers page...")
        customer_urls = self._discover_from_customers_page()
        results['customer_story_urls'].extend(customer_urls)
        if customer_urls:
            results['metadata']['sources_processed'].append('customers_page')
        
        # Strategy 3: Search for customer stories using company names
        logger.info("Searching for customer stories using extracted companies...")
        story_urls = self._search_customer_stories(results['company_names'])
        results['customer_story_urls'].extend(story_urls)
        logger.info(f"Found {len(story_urls)} URLs from company search")
        
        # Strategy 4: Additional discovery from AI/ML focused pages
        logger.info("Additional discovery from AI-focused pages...")
        ai_urls = self._discover_from_ai_pages()
        results['customer_story_urls'].extend(ai_urls)
        if ai_urls:
            results['metadata']['sources_processed'].append('ai_pages')
        
        # Remove duplicates and filter
        before_dedup = len(results['customer_story_urls'])
        results['customer_story_urls'] = list(set(results['customer_story_urls']))
        logger.info(f"Before dedup: {before_dedup}, after dedup: {len(results['customer_story_urls'])}")
        
        before_filter = len(results['customer_story_urls'])
        results['customer_story_urls'] = [url for url in results['customer_story_urls'] 
                                        if self._is_valid_customer_story_url(url)]
        logger.info(f"Before filter: {before_filter}, after filter: {len(results['customer_story_urls'])}")
        
        if before_filter > len(results['customer_story_urls']):
            filtered_out = [url for url in list(set(results['customer_story_urls'] + 
                           [url for url in results['customer_story_urls'] if not self._is_valid_customer_story_url(url)]))]
            logger.info(f"URLs filtered out: {filtered_out[:5]}")
        
        results['metadata']['total_discovered'] = len(results['customer_story_urls'])
        
        logger.info(f"Extraction complete: {len(results['customer_story_urls'])} customer story URLs discovered")
        return results
    
    def _extract_from_use_cases_blog(self) -> Optional[Dict[str, List[str]]]:
        """Extract company names and URLs from the 101 use cases blog post"""
        try:
            response = self.session.get(self.sources['use_cases_blog'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for element in soup.find_all(['script', 'style']):
                element.decompose()
            
            content = soup.get_text()
            
            # Extract company names using various patterns
            companies = set()
            urls = set()
            
            # Manual curation of high-value companies mentioned in the blog
            known_companies = {
                'The Home Depot', 'Target', 'Toyota', 'BBVA', 'Spotify', 'Snap', 'Samsung',
                'Bell Canada', 'Bayer', 'Carrefour', 'PwC', 'Procter & Gamble', 'Etsy',
                'Air Force', 'Rivian', 'Character.ai', 'Typeface', 'Sprinklr', 'ThoughtSpot',
                'Banco BV', 'Intesa Sanpaolo', 'TIM Brasil', 'Hiscox', 'Technogym',
                'Just Salad', 'ScottsMiracle-Gro', 'NewsCorp', 'Six Flags', 'Hand Talk',
                'CytoReason', 'NetRise', 'Arize AI', 'Higgsfield.ai', 'Persistent Systems',
                'Nuts.com', 'Wisconsin Cheese Mart', 'Premier Martial Arts', 'WebFX',
                'Ferret.ai', 'Brandtech Group', 'Moveo.AI', 'Spoon Guru', 'Exabeam',
                'Hydro Ottawa', 'Agromai', 'Moto AI', 'Weights & Biases', 'apree health'
            }
            companies.update(known_companies)
            
            # Improved regex patterns for company extraction
            company_patterns = [
                # Direct company mentions with AI context
                r'\b([A-Z][a-zA-Z0-9\s&\.\-]{2,40})\s+(?:uses?|leverages?|implemented?|deployed?|developed?)\s+(?:gen\s?ai|ai|vertex|gemini)',
                r'\b([A-Z][a-zA-Z0-9\s&\.\-]{2,40})\s+(?:has|is)\s+(?:using|implementing|deploying)\s+(?:gen\s?ai|ai|vertex|gemini)',
                r'(?:At|For)\s+([A-Z][a-zA-Z0-9\s&\.\-]{2,40}),?\s+(?:ai|vertex|gemini|gen\s?ai)',
                # Company names followed by specific AI outcomes
                r'\b([A-Z][a-zA-Z0-9\s&\.\-]{2,40})\s+(?:reduced|increased|improved|enhanced|achieved).{0,50}(?:ai|automation|efficiency)',
                # Company as subject of AI transformation
                r'^([A-Z][a-zA-Z0-9\s&\.\-]{2,40})\s+(?:transforms?|innovates?|modernizes?)',
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    company = match.strip()
                    if self._is_valid_company_name(company):
                        companies.add(company)
            
            # Look for companies in headers and strong tags
            for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']):
                text = tag.get_text().strip()
                if self._is_valid_company_name(text):
                    companies.add(text)
            
            # Extract any existing cloud.google.com URLs
            google_urls = re.findall(r'https?://cloud\.google\.com/[^\s\)"\']*', content)
            for url in google_urls:
                if '/customers/' in url:
                    urls.add(url.rstrip('.,;)'))
            
            # Clean up company names
            cleaned_companies = set()
            for company in companies:
                cleaned = self._clean_company_name(company)
                if cleaned and self._is_valid_company_name(cleaned):
                    cleaned_companies.add(cleaned)
            
            logger.info(f"Extracted {len(cleaned_companies)} companies and {len(urls)} URLs from use cases blog")
            return {
                'companies': list(cleaned_companies),
                'urls': list(urls)
            }
            
        except Exception as e:
            logger.error(f"Error extracting from use cases blog: {e}")
            return None
    
    def _discover_from_customers_page(self) -> List[str]:
        """Discover customer story URLs from the main customers page"""
        discovered_urls = []
        
        try:
            # Try multiple approaches for the customers page
            for page_variant in [
                'https://cloud.google.com/customers?hl=en',
                'https://cloud.google.com/customers',
                'https://cloud.google.com/customers/ai',
                'https://cloud.google.com/customers/ml'
            ]:
                try:
                    response = self.session.get(page_variant)
                    if response.status_code == 200:
                        urls = self._extract_customer_urls_from_page(response.text, page_variant)
                        discovered_urls.extend(urls)
                        time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.debug(f"Could not access {page_variant}: {e}")
                    continue
            
            # Try to find pagination or load-more mechanisms
            discovered_urls.extend(self._discover_paginated_customers())
            
        except Exception as e:
            logger.error(f"Error discovering from customers page: {e}")
        
        return list(set(discovered_urls))
    
    def _extract_customer_urls_from_page(self, html: str, base_url: str) -> List[str]:
        """Extract customer URLs from a page"""
        urls = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for customer story links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
                
            # Convert relative URLs
            if href.startswith('/'):
                href = f"https://cloud.google.com{href}"
            elif not href.startswith('http'):
                continue
            
            # Check if it's a customer story URL
            if '/customers/' in href and self._is_valid_customer_story_url(href):
                # Quick AI relevance check based on link text or surrounding context
                link_text = link.get_text().lower()
                if any(keyword in link_text for keyword in ['ai', 'ml', 'machine learning', 'intelligence']):
                    urls.append(href)
                else:
                    # Check surrounding context
                    parent_text = ''
                    if link.parent:
                        parent_text = link.parent.get_text().lower()
                    if any(keyword in parent_text for keyword in self.ai_keywords):
                        urls.append(href)
        
        # Also look in script tags for dynamically loaded URLs
        for script in soup.find_all('script'):
            script_content = script.get_text()
            google_customer_urls = re.findall(r'https://cloud\.google\.com/customers/[^"\']*', script_content)
            for url in google_customer_urls:
                if self._is_valid_customer_story_url(url):
                    urls.append(url)
        
        return list(set(urls))
    
    def _discover_paginated_customers(self) -> List[str]:
        """Discover customers from paginated results"""
        urls = []
        
        # Try common pagination patterns
        page_variants = [
            'https://cloud.google.com/customers?page={}',
            'https://cloud.google.com/customers?offset={}',
            'https://cloud.google.com/customers/page/{}'
        ]
        
        for pattern in page_variants:
            for page_num in range(1, 6):  # Try first 5 pages
                try:
                    page_url = pattern.format(page_num)
                    response = self.session.get(page_url)
                    if response.status_code == 200:
                        page_urls = self._extract_customer_urls_from_page(response.text, page_url)
                        if page_urls:
                            urls.extend(page_urls)
                        else:
                            break  # No more content
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.debug(f"Pagination attempt failed for {page_url}: {e}")
                    break
        
        return urls
    
    def _search_customer_stories(self, company_names: List[str]) -> List[str]:
        """Search for customer stories using company names and web search"""
        story_urls = []
        
        # Focus on high-value companies first
        priority_companies = [
            'Target', 'Home Depot', 'Toyota', 'BBVA', 'Spotify', 'Snap', 'Samsung',
            'Bell Canada', 'Bayer', 'Carrefour', 'PwC', 'Procter & Gamble', 'Etsy',
            'Rivian', 'Character.ai', 'Typeface', 'Sprinklr', 'ThoughtSpot',
            'Banco BV', 'Intesa Sanpaolo', 'TIM Brasil', 'Hiscox', 'Technogym'
        ]
        
        # Combine priority companies with extracted ones
        all_companies = priority_companies + [c for c in company_names if c not in priority_companies]
        
        # Strategy 1: Direct URL construction (existing approach)
        direct_urls = self._search_direct_urls(all_companies[:40])
        story_urls.extend(direct_urls)
        
        # Strategy 2: Web search for customer stories (NEW!)
        web_search_urls = self._web_search_customer_stories(all_companies[:20])  # Limit for API costs
        story_urls.extend(web_search_urls)
        
        return list(set(story_urls))  # Remove duplicates
    
    def _search_direct_urls(self, companies: List[str]) -> List[str]:
        """Direct URL construction approach (original method)"""
        story_urls = []
        
        for company in companies:
            try:
                # Generate comprehensive slug variants
                base_name = company.lower().replace('the ', '').replace(' inc', '').replace(' corp', '')
                slug_variants = [
                    base_name.replace(' ', '-').replace('&', 'and').replace('.', '').replace(',', ''),
                    base_name.replace(' ', '').replace('&', '').replace('.', '').replace(',', ''),
                    base_name.replace(' ', '_').replace('&', 'and').replace('.', '').replace(',', ''),
                    base_name.replace(' ', '-').replace('&', '').replace('.', '').replace(',', ''),
                    # Handle special cases
                    company.lower().split()[0] if ' ' in company else base_name,  # First word only
                    ''.join(word[0] for word in company.split()) if len(company.split()) > 1 else base_name,  # Acronym
                ]
                
                # Remove duplicates and empty strings
                slug_variants = list(set([s for s in slug_variants if s and len(s) > 1]))
                
                for slug in slug_variants:
                    potential_url = f"https://cloud.google.com/customers/{slug}"
                    try:
                        response = self.session.head(potential_url, timeout=10)
                        if response.status_code == 200:
                            story_urls.append(potential_url)
                            logger.info(f"✓ Direct URL found: {potential_url}")
                            break
                        elif response.status_code == 404:
                            continue  # Try next variant
                    except Exception as e:
                        logger.debug(f"Request failed for {potential_url}: {e}")
                        continue
                
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Error searching for {company}: {e}")
                continue
        
        return story_urls
    
    def _web_search_customer_stories(self, companies: List[str]) -> List[str]:
        """Web search for customer stories using search queries"""
        story_urls = []
        
        logger.info(f"Starting web search for {len(companies)} companies...")
        
        for company in companies:
            try:
                # Create targeted search queries
                search_queries = [
                    f'"{company}" site:cloud.google.com customer story',
                    f'"{company}" site:cloud.google.com case study AI',
                    f'"{company}" site:cloud.google.com generative AI',
                    f'"{company}" site:cloud.google.com vertex AI',
                    f'"{company}" google cloud customer success'
                ]
                
                # Try each search query
                for query in search_queries:
                    try:
                        # Use a simple web search approach
                        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                        
                        # Make request with proper headers to avoid blocking
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                        }
                        
                        response = self.session.get(search_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            # Extract Google Cloud URLs from search results
                            found_urls = re.findall(
                                r'https://cloud\.google\.com/(?:customers|blog|solutions)/[^"\'>\s]*',
                                response.text
                            )
                            
                            for url in found_urls:
                                # Clean up URL and validate
                                clean_url = url.rstrip('.,;)')
                                if self._is_valid_story_url_expanded(clean_url):
                                    story_urls.append(clean_url)
                                    logger.info(f"✓ Web search found: {clean_url}")
                            
                            # Don't overwhelm search with multiple queries per company if we found results
                            if found_urls:
                                break
                        
                        time.sleep(2)  # Be respectful to search engines
                        
                    except Exception as e:
                        logger.debug(f"Web search failed for query '{query}': {e}")
                        continue
                
                time.sleep(1)  # Rate limiting between companies
                
            except Exception as e:
                logger.debug(f"Error in web search for {company}: {e}")
                continue
        
        logger.info(f"Web search completed. Found {len(story_urls)} additional URLs")
        return story_urls
    
    def _is_valid_story_url_expanded(self, url: str) -> bool:
        """Expanded validation for story URLs (includes blog posts, solutions, etc.)"""
        if not url or not url.startswith('https://cloud.google.com/'):
            return False
        
        # Accept broader range of content types
        valid_patterns = [
            '/customers/',
            '/blog/',
            '/solutions/',
            '/case-studies/',
            '/success-stories/'
        ]
        
        if not any(pattern in url for pattern in valid_patterns):
            return False
        
        # Exclude unwanted pages
        exclusions = [
            '/search', '/browse', '/filter', '/category', '/tag',
            'cloud.google.com/blog/rss', 'cloud.google.com/blog/feed'
        ]
        
        for exclusion in exclusions:
            if exclusion in url:
                return False
        
        return True
    
    def _discover_from_ai_pages(self) -> List[str]:
        """Discover customer stories from AI-focused Google Cloud pages"""
        urls = []
        
        ai_pages = [
            'https://cloud.google.com/ai',
            'https://cloud.google.com/vertex-ai',
            'https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview',
            'https://cloud.google.com/blog/products/ai-machine-learning',
            'https://cloud.google.com/solutions/ai'
        ]
        
        for page in ai_pages:
            try:
                response = self.session.get(page)
                if response.status_code == 200:
                    page_urls = self._extract_customer_urls_from_page(response.text, page)
                    urls.extend(page_urls)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.debug(f"Error accessing AI page {page}: {e}")
                continue
        
        return list(set(urls))
    
    def _clean_company_name(self, company: str) -> str:
        """Clean and standardize company name"""
        if not company:
            return ""
        
        # Remove common prefixes/suffixes
        company = re.sub(r'^(?:The\s+)', '', company)
        company = re.sub(r'\s+(?:Inc\.?|Corp\.?|Ltd\.?|LLC|Co\.?)$', '', company)
        
        # Clean whitespace and punctuation
        company = re.sub(r'\s+', ' ', company).strip()
        company = company.rstrip('.,;:')
        
        return company
    
    def _is_valid_company_name(self, company: str) -> bool:
        """Validate if a string is likely a company name"""
        if not company or len(company) < 3 or len(company) > 50:
            return False
        
        # Exclude common false positives
        exclusions = {
            'google', 'cloud', 'ai', 'ml', 'case study', 'customer story', 
            'learn more', 'read more', 'solutions', 'services', 'platform',
            'industries', 'products', 'documentation', 'blog', 'news',
            'vertex ai', 'google cloud', 'generative ai', 'machine learning',
            'artificial intelligence', 'gen ai', 'use cases', 'real world'
        }
        
        if company.lower() in exclusions:
            return False
        
        # Exclude generic phrases
        generic_patterns = [
            r'^(?:this|that|these|those|they|it|we|our|their)\b',
            r'\b(?:has|have|had|is|are|was|were|can|could|will|would)\b',
            r'^(?:using|implementing|deploying|building|creating)\b'
        ]
        
        for pattern in generic_patterns:
            if re.search(pattern, company, re.IGNORECASE):
                return False
        
        # Must start with capital letter and contain reasonable characters
        if not re.match(r'^[A-Z][a-zA-Z0-9\s&\-\.]{2,}$', company):
            return False
        
        return True
    
    def _is_valid_customer_story_url(self, url: str) -> bool:
        """Validate if URL is a customer story"""
        if not url or not url.startswith('https://cloud.google.com/customers/'):
            return False
        
        # Exclude listing pages and non-story URLs (but not individual customer stories)
        exclusions = [
            '/customers?', '/customers#', '/search', '/browse',
            '/filter', '/category', '/industry', '/size'
        ]
        
        # Special case: exclude the base customers page but not individual customer pages
        if url.endswith('/customers') or url.endswith('/customers/'):
            return False
            
        for exclusion in exclusions:
            if exclusion in url:
                return False
        
        # Must have a customer identifier after /customers/
        customer_part = url.replace('https://cloud.google.com/customers/', '').strip('/')
        if not customer_part or '/' in customer_part.split('?')[0]:
            return False
        
        # Exclude URLs with invalid characters (malformed from regex extraction)
        if '\\' in url or '//' in customer_part:
            return False
        
        return True
    
    def save_results(self, results: Dict, filename: str = 'google_cloud_story_urls.json'):
        """Save extraction results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {filename}")
            
            # Also create a simple URLs list for easy integration
            urls_only_file = filename.replace('.json', '_urls_only.json') 
            with open(urls_only_file, 'w', encoding='utf-8') as f:
                json.dump(results['customer_story_urls'], f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def main():
    """Main execution function"""
    logger.info("Starting Google Cloud customer story URL extraction...")
    
    extractor = GoogleCloudURLExtractor()
    results = extractor.extract_all_urls()
    
    # Print summary
    print("\n" + "="*70)
    print("GOOGLE CLOUD URL EXTRACTION SUMMARY")
    print("="*70)
    print(f"Customer Story URLs Discovered: {len(results['customer_story_urls'])}")
    print(f"Company Names Extracted: {len(results['company_names'])}")
    print(f"Blog URLs Found: {len(results['blog_urls'])}")
    print(f"Sources Processed: {', '.join(results['metadata']['sources_processed'])}")
    
    if results['customer_story_urls']:
        print(f"\nFirst 10 Customer Story URLs:")
        for i, url in enumerate(results['customer_story_urls'][:10], 1):
            print(f"{i:2d}. {url}")
        
        if len(results['customer_story_urls']) > 10:
            print(f"... and {len(results['customer_story_urls']) - 10} more")
    
    # Save results
    extractor.save_results(results)
    
    print(f"\nResults saved to google_cloud_story_urls.json")
    print("Ready for integration with enhanced Google Cloud scraper!")

if __name__ == "__main__":
    main()