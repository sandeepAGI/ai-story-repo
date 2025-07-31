import logging
import sys
from typing import List, Dict, Any
from src.config import Config
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations, CustomerStory
from src.scrapers.anthropic_scraper import AnthropicScraper
# OpenAI scraper removed - handled by process_openai_html.py
from src.scrapers.microsoft_scraper import MicrosoftScraper
from src.scrapers.aws_scraper import AWScraper
from src.scrapers.googlecloud_scraper import GoogleCloudScraper
from src.ai_integration.claude_processor import ClaudeProcessor

logger = logging.getLogger(__name__)

class AIStoriesProcessor:
    def __init__(self):
        # Setup configuration and logging
        Config.setup_logging()
        
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        # Initialize components
        self.db_connection = DatabaseConnection()
        self.db_ops = DatabaseOperations(self.db_connection)
        self.claude_processor = ClaudeProcessor()
        
        # Test database connection
        if not self.db_connection.test_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        logger.info("AI Stories Processor initialized successfully")
    
    def setup_database(self, schema_file: str = "src/database/schema.sql"):
        """Initialize database with schema"""
        try:
            self.db_connection.execute_schema(schema_file)
            logger.info("Database schema setup completed")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
    
    # OpenAI stories are handled by process_openai_html.py - no scraping method needed
    
    def scrape_microsoft_stories(self, limit: int = None) -> List[Dict[str, Any]]:
        """Scrape Microsoft Azure AI customer stories"""
        logger.info(f"Starting Microsoft scraping (limit: {limit})")
        
        scraper = MicrosoftScraper()
        
        # Get story URLs
        story_urls = scraper.get_customer_story_urls()
        
        if limit:
            story_urls = story_urls[:limit]
        
        logger.info(f"Found {len(story_urls)} story URLs to scrape")
        
        # Scrape stories
        scraped_stories = []
        for i, url in enumerate(story_urls):
            logger.info(f"Scraping story {i+1}/{len(story_urls)}: {url}")
            
            # Check if story already exists
            if self.db_ops.check_story_exists(url):
                logger.info(f"Story already exists, skipping: {url}")
                continue
            
            story_data = scraper.scrape_story(url)
            if story_data:
                scraped_stories.append(story_data)
            else:
                logger.warning(f"Failed to scrape: {url}")
        
        logger.info(f"Successfully scraped {len(scraped_stories)} new stories")
        return scraped_stories
    
    def scrape_aws_stories(self, limit: int = None) -> List[Dict[str, Any]]:
        """Scrape AWS AI/ML customer stories"""
        logger.info(f"Starting AWS scraping (limit: {limit})")
        
        scraper = AWScraper()
        
        # Get story URLs
        story_urls = scraper.get_customer_story_urls()
        
        if limit:
            story_urls = story_urls[:limit]
        
        logger.info(f"Found {len(story_urls)} story URLs to scrape")
        
        # Scrape stories
        scraped_stories = []
        for i, url in enumerate(story_urls):
            logger.info(f"Scraping story {i+1}/{len(story_urls)}: {url}")
            
            # Check if story already exists
            if self.db_ops.check_story_exists(url):
                logger.info(f"Story already exists, skipping: {url}")
                continue
            
            story_data = scraper.scrape_story(url)
            if story_data:
                scraped_stories.append(story_data)
            else:
                logger.warning(f"Failed to scrape: {url}")
        
        logger.info(f"Successfully scraped {len(scraped_stories)} new stories")
        return scraped_stories
    
    def scrape_anthropic_stories(self, limit: int = None) -> List[Dict[str, Any]]:
        """Scrape Anthropic customer stories with publish dates"""
        logger.info(f"Starting Anthropic scraping (limit: {limit})")
        
        scraper = AnthropicScraper()
        
        # Get story URLs with dates
        if limit and limit <= 5:
            # For testing, use sample URLs
            story_urls_data = [{'url': url, 'publish_date': None} for url in scraper.get_sample_story_urls()[:limit]]
        else:
            story_urls_data = scraper.get_customer_story_urls_with_dates()
            if limit:
                story_urls_data = story_urls_data[:limit]
        
        logger.info(f"Found {len(story_urls_data)} story URLs to scrape")
        
        # Scrape stories
        scraped_stories = []
        for i, story_info in enumerate(story_urls_data):
            url = story_info['url']
            publish_date = story_info['publish_date']
            
            logger.info(f"Scraping story {i+1}/{len(story_urls_data)}: {url}")
            
            # Check if story already exists
            if self.db_ops.check_story_exists(url):
                logger.info(f"Story already exists, skipping: {url}")
                continue
            
            story_data = scraper.scrape_story(url)
            if story_data:
                # Add publish date to story data
                story_data['publish_date'] = publish_date
                scraped_stories.append(story_data)
            else:
                logger.warning(f"Failed to scrape: {url}")
        
        logger.info(f"Successfully scraped {len(scraped_stories)} new stories")
        return scraped_stories
    
    def scrape_googlecloud_stories(self, limit: int = None) -> List[Dict[str, Any]]:
        """Scrape Google Cloud AI customer stories"""
        logger.info(f"Starting Google Cloud scraping (limit: {limit})")
        
        scraper = GoogleCloudScraper()
        
        # Get story URLs
        story_urls = scraper.get_customer_story_urls()
        
        if limit:
            story_urls = story_urls[:limit]
        
        logger.info(f"Found {len(story_urls)} story URLs to scrape")
        
        # Scrape stories
        scraped_stories = []
        for i, url in enumerate(story_urls):
            logger.info(f"Scraping story {i+1}/{len(story_urls)}: {url}")
            
            # Check if story already exists
            if self.db_ops.check_story_exists(url):
                logger.info(f"Story already exists, skipping: {url}")
                continue
            
            story_data = scraper.scrape_story(url)
            if story_data:
                scraped_stories.append(story_data)
            else:
                logger.warning(f"Failed to scrape: {url}")
        
        logger.info(f"Successfully scraped {len(scraped_stories)} new stories")
        return scraped_stories
    
    def process_stories_with_claude(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process scraped stories with Claude for data extraction"""
        logger.info(f"Processing {len(stories)} stories with Claude")
        
        processed_stories = self.claude_processor.batch_process_stories(stories)
        
        logger.info(f"Claude processing completed: {len(processed_stories)} stories processed")
        return processed_stories
    
    def save_stories_to_database(self, stories: List[Dict[str, Any]], source_name: str = "Anthropic") -> List[int]:
        """Save processed stories to database"""
        logger.info(f"Saving {len(stories)} stories to database for source: {source_name}")
        
        # Get source ID
        source = self.db_ops.get_source_by_name(source_name)
        if not source:
            logger.error(f"{source_name} source not found in database")
            return []
        
        saved_story_ids = []
        
        for story in stories:
            try:
                # Extract data from Claude processing
                extracted_data = story.get('extracted_data', {})
                
                # Convert publish_date string to date object if available
                publish_date = None
                publish_date_estimated = False
                publish_date_confidence = None
                publish_date_reasoning = None
                
                if story.get('publish_date'):
                    try:
                        from datetime import datetime
                        publish_date = datetime.strptime(story['publish_date'], "%Y-%m-%d").date()
                    except ValueError:
                        logger.warning(f"Invalid publish date format: {story.get('publish_date')}")
                
                # If no original publish date, try using Claude's estimated date
                if publish_date is None and extracted_data.get('estimated_publish_date'):
                    try:
                        from datetime import datetime
                        estimated_date = extracted_data.get('estimated_publish_date')
                        if estimated_date and estimated_date != 'null':
                            publish_date = datetime.strptime(estimated_date, "%Y-%m-%d").date()
                            publish_date_estimated = True
                            publish_date_confidence = extracted_data.get('date_confidence')
                            publish_date_reasoning = extracted_data.get('date_reasoning')
                            logger.info(f"Using Claude estimated publish date: {estimated_date} (confidence: {publish_date_confidence})")
                    except ValueError:
                        logger.warning(f"Invalid estimated publish date format: {extracted_data.get('estimated_publish_date')}")
                
                # Create CustomerStory object
                customer_story = CustomerStory(
                    id=None,
                    source_id=source.id,
                    customer_name=story['customer_name'],
                    title=story.get('title'),
                    url=story['url'],
                    content_hash=story['content_hash'],
                    industry=extracted_data.get('industry'),
                    company_size=extracted_data.get('company_size'),
                    use_case_category=extracted_data.get('use_cases', [None])[0] if extracted_data.get('use_cases') else None,
                    raw_content=story['raw_content'],
                    extracted_data=extracted_data,
                    publish_date=publish_date,
                    publish_date_estimated=publish_date_estimated,
                    publish_date_confidence=publish_date_confidence,
                    publish_date_reasoning=publish_date_reasoning
                )
                
                # Save to database
                story_id = self.db_ops.insert_customer_story(customer_story)
                saved_story_ids.append(story_id)
                
                logger.info(f"Saved story ID {story_id}: {customer_story.customer_name}")
                
            except Exception as e:
                logger.error(f"Failed to save story {story.get('url', 'unknown')}: {e}")
        
        # Update source last_scraped timestamp
        self.db_ops.update_source_last_scraped(source.id)
        
        logger.info(f"Successfully saved {len(saved_story_ids)} stories to database")
        return saved_story_ids
    
    def run_full_pipeline(self, source: str = "anthropic", limit: int = None):
        """Run the complete scraping and processing pipeline"""
        logger.info(f"Starting full AI Stories pipeline for {source}")
        
        try:
            # Step 1: Scrape stories
            if source.lower() == "openai":
                logger.info("OpenAI stories are handled by process_openai_html.py - skipping scraping")
                return
            elif source.lower() == "microsoft":
                scraped_stories = self.scrape_microsoft_stories(limit)
                source_name = "Microsoft"
            elif source.lower() == "aws":
                scraped_stories = self.scrape_aws_stories(limit)
                source_name = "AWS"
            elif source.lower() == "googlecloud":
                scraped_stories = self.scrape_googlecloud_stories(limit)
                source_name = "Google Cloud"
            else:
                scraped_stories = self.scrape_anthropic_stories(limit)
                source_name = "Anthropic"
            
            if not scraped_stories:
                logger.info("No new stories to process")
                return
            
            # Step 2: Process with Claude
            processed_stories = self.process_stories_with_claude(scraped_stories)
            
            if not processed_stories:
                logger.warning("No stories successfully processed by Claude")
                return
            
            # Step 3: Save to database
            saved_ids = self.save_stories_to_database(processed_stories, source_name)
            
            logger.info(f"Pipeline completed successfully. Saved {len(saved_ids)} stories.")
            
            # Print summary
            self.print_pipeline_summary(processed_stories, saved_ids)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
    
    def print_pipeline_summary(self, stories: List[Dict], saved_ids: List[int]):
        """Print summary of processed stories"""
        print("\n" + "="*60)
        print("AI STORIES PIPELINE SUMMARY")
        print("="*60)
        print(f"Total stories processed: {len(stories)}")
        print(f"Total stories saved: {len(saved_ids)}")
        print("\nProcessed Stories:")
        print("-" * 40)
        
        for i, story in enumerate(stories[:10]):  # Show first 10
            extracted = story.get('extracted_data', {})
            print(f"{i+1}. {story['customer_name']}")
            print(f"   Industry: {extracted.get('industry', 'N/A')}")
            print(f"   Quality Score: {extracted.get('content_quality_score', 'N/A')}")
            print(f"   Use Cases: {', '.join(extracted.get('use_cases', [])[:3])}")
            print(f"   URL: {story['url']}")
            print()
        
        if len(stories) > 10:
            print(f"... and {len(stories) - 10} more stories")
        
        print("="*60)

def main():
    """Main entry point"""
    import sys
    
    processor = AIStoriesProcessor()
    
    # Parse command line arguments
    source = "anthropic"  # default
    limit = 5  # default for testing
    
    if len(sys.argv) > 1:
        source = sys.argv[1].lower()
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            logger.warning("Invalid limit argument, using default of 5")
    
    logger.info(f"Running pipeline with source: {source}, limit: {limit}")
    processor.run_full_pipeline(source=source, limit=limit)

if __name__ == "__main__":
    main()