#!/usr/bin/env python3
"""
Enhanced Microsoft Scraper using pre-collected story URLs.
Processes the 656 Microsoft customer story links extracted from the blog post.
"""

import json
import logging
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

from src.scrapers.microsoft_scraper import MicrosoftScraper
from src.database.models import DatabaseOperations, CustomerStory
from src.ai_integration.claude_processor import ClaudeProcessor

logger = logging.getLogger(__name__)

class EnhancedMicrosoftScraper:
    """Enhanced Microsoft scraper that processes pre-collected URLs"""
    
    def __init__(self):
        self.scraper = MicrosoftScraper()
        self.db_ops = DatabaseOperations()
        self.claude_processor = ClaudeProcessor()
        self.story_urls = self._load_story_urls()
        
    def _load_story_urls(self) -> List[str]:
        """Load the pre-collected Microsoft story URLs"""
        try:
            with open('microsoft_story_links.json', 'r') as f:
                data = json.load(f)
                return data.get('links', [])
        except FileNotFoundError:
            logger.error("microsoft_story_links.json not found. Run extract_microsoft_blog_links.py first.")
            return []
        except Exception as e:
            logger.error(f"Error loading story URLs: {e}")
            return []
    
    def filter_ai_related_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs that are likely AI-related based on URL patterns"""
        ai_keywords = [
            'copilot', 'azure-ai', 'openai', 'azure-openai', 'ai-services',
            'machine-learning', 'cognitive-services', 'ai-studio', 'fabric',
            'databricks', 'speech', 'vision', 'language', 'bot-framework'
        ]
        
        ai_urls = []
        for url in urls:
            url_lower = url.lower()
            if any(keyword in url_lower for keyword in ai_keywords):
                ai_urls.append(url)
        
        logger.info(f"Filtered {len(ai_urls)} AI-related URLs from {len(urls)} total URLs")
        return ai_urls
    
    def check_existing_stories(self, urls: List[str]) -> List[str]:
        """Remove URLs that are already in our database"""
        new_urls = []
        
        for url in urls:
            if not self.db_ops.check_story_exists(url):
                new_urls.append(url)
            else:
                logger.debug(f"Story already exists: {url}")
        
        logger.info(f"Found {len(new_urls)} new stories to process (filtered {len(urls) - len(new_urls)} existing)")
        return new_urls
    
    def _scrape_story_no_filter(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape Microsoft story without AI content filtering"""
        logger.debug(f"Scraping Microsoft story (no AI filter): {url}")
        
        response = self.scraper.make_request(url)
        if not response:
            return None
        
        soup = self.scraper.parse_html(response.text)
        
        # Extract customer name (without AI filtering)
        customer_name = self.scraper.extract_customer_name(soup, url)
        if not customer_name:
            logger.warning(f"Could not extract customer name from {url}")
            return None
        
        # Extract title
        title = self.scraper._extract_title(soup)
        
        # Extract publish date
        publish_date = self.scraper._extract_publish_date(soup)
        
        # Create raw content structure
        raw_content = self.scraper.create_raw_content(response, soup)
        
        # Generate content hash
        from src.database.models import generate_content_hash
        content_hash = generate_content_hash(raw_content.get('text', ''))
        
        return {
            'customer_name': customer_name,
            'title': title,
            'url': response.url,  # Use final URL after redirects
            'publish_date': publish_date,
            'raw_content': raw_content,
            'content_hash': content_hash
        }
    
    def process_stories_batch(self, urls: List[str], batch_size: int = 10) -> Dict[str, int]:
        """Process stories in batches with progress tracking"""
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped_non_ai': 0
        }
        
        total_urls = len(urls)
        logger.info(f"Starting to process {total_urls} Microsoft customer stories")
        
        for i in range(0, total_urls, batch_size):
            batch = urls[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_urls + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} stories)")
            
            for j, url in enumerate(batch):
                try:
                    stats['processed'] += 1
                    story_num = i + j + 1
                    
                    logger.info(f"  [{story_num}/{total_urls}] Processing: {url}")
                    
                    # Scrape the story (bypass AI filtering since Microsoft states all are AI-related)
                    story_data = self._scrape_story_no_filter(url)
                    
                    if not story_data:
                        logger.warning(f"    Failed to scrape story: {url}")
                        stats['failed'] += 1
                        continue
                    
                    # Process with Claude AI
                    logger.debug(f"    Processing with Claude AI...")
                    processed_data = self.claude_processor.extract_story_data(story_data['raw_content'])
                    
                    if processed_data:
                        # Get Microsoft source ID
                        source = self.db_ops.get_source_by_name("Microsoft")
                        if not source:
                            logger.error("Microsoft source not found in database")
                            stats['failed'] += 1
                            continue
                        
                        # Create CustomerStory object using correct schema
                        customer_story = CustomerStory(
                            id=None,
                            source_id=source.id,
                            customer_name=story_data['customer_name'],
                            title=story_data.get('title'),
                            url=story_data['url'],
                            content_hash=story_data['content_hash'],
                            industry=processed_data.get('industry', ''),
                            company_size=processed_data.get('company_size', ''),
                            use_case_category=processed_data.get('ai_type', ''),
                            raw_content=story_data['raw_content'],
                            extracted_data=processed_data,  # Store all extracted data here
                            publish_date=story_data.get('publish_date'),
                            is_gen_ai=processed_data.get('is_gen_ai', True),
                            # Gen AI classification fields
                            gen_ai_superpowers=processed_data.get('superpower_category', []),
                            business_impacts=processed_data.get('business_impact', []),
                            adoption_enablers=processed_data.get('adoption_enabler', []),
                            business_function=processed_data.get('business_function', {}).get('primary') if isinstance(processed_data.get('business_function'), dict) else processed_data.get('business_function'),
                        )
                        
                        # Save to database
                        story_id = self.db_ops.insert_customer_story(customer_story)
                        
                        if story_id:
                            logger.info(f"    ✓ Successfully saved: {customer_story.customer_name} (ID: {story_id})")
                            stats['successful'] += 1
                        else:
                            logger.error(f"    Failed to save story to database")
                            stats['failed'] += 1
                    else:
                        logger.error(f"    Claude processing failed")
                        stats['failed'] += 1
                        
                except Exception as e:
                    logger.error(f"    Error processing {url}: {e}")
                    stats['failed'] += 1
                
                # Brief pause between requests
                import time
                time.sleep(1)
            
            # Longer pause between batches
            if batch_num < total_batches:
                logger.info(f"  Batch {batch_num} complete. Pausing before next batch...")
                time.sleep(5)
        
        return stats
    
    def run_enhanced_scraping(self, ai_only: bool = True, max_stories: Optional[int] = None):
        """Run the enhanced Microsoft scraping process"""
        logger.info("=" * 70)
        logger.info("ENHANCED MICROSOFT CUSTOMER STORIES SCRAPING")
        logger.info("=" * 70)
        
        if not self.story_urls:
            logger.error("No story URLs loaded. Cannot proceed.")
            return
        
        logger.info(f"Loaded {len(self.story_urls)} pre-collected Microsoft story URLs")
        
        # Use all URLs since Microsoft states all 1000+ stories are AI-related
        urls_to_process = self.story_urls
        logger.info("Processing all URLs since Microsoft blog states all stories are AI-related")
        
        # Check for existing stories
        urls_to_process = self.check_existing_stories(urls_to_process)
        
        # Limit number of stories if specified
        if max_stories and len(urls_to_process) > max_stories:
            urls_to_process = urls_to_process[:max_stories]
            logger.info(f"Limited to {max_stories} stories for this run")
        
        if not urls_to_process:
            logger.info("No new stories to process!")
            return
        
        logger.info(f"Will process {len(urls_to_process)} stories")
        
        # Process stories
        start_time = datetime.now()
        stats = self.process_stories_batch(urls_to_process)
        end_time = datetime.now()
        
        # Print final statistics
        duration = end_time - start_time
        logger.info("=" * 70)
        logger.info("ENHANCED MICROSOFT SCRAPING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total time: {duration}")
        logger.info(f"Stories processed: {stats['processed']}")
        logger.info(f"Successfully saved: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Skipped (non-AI): {stats['skipped_non_ai']}")
        logger.info(f"Success rate: {stats['successful']/(stats['processed']) * 100:.1f}%")
        
        return stats

def main():
    """Main execution function"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create enhanced scraper
    scraper = EnhancedMicrosoftScraper()
    
    # Run with options (modify as needed)
    scraper.run_enhanced_scraping(
        ai_only=False,         # Process all stories since Microsoft states all are AI-related
        max_stories=None       # Process ALL stories - full production run
    )

if __name__ == "__main__":
    main()