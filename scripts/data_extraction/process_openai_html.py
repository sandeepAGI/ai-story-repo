#!/usr/bin/env python3
"""
Process OpenAI customer stories from manually collected HTML files
Processes HTML files in openaicases/ subdirectory and adds them to database
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations, CustomerStory
from ai_integration.claude_processor import ClaudeProcessor

class OpenAIHTMLProcessor:
    def __init__(self):
        self.db = DatabaseConnection()
        self.db_ops = DatabaseOperations(self.db)
        self.claude_processor = ClaudeProcessor()
        self.html_dir = Path(__file__).parent / "openaicases"
        
    def extract_story_data_from_html(self, html_content: str, filename: str) -> Dict:
        """Extract story data from OpenAI HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = ""
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = title_elem.get_text().strip()
        
        # Extract customer name from filename and content
        filename_customer = filename.replace(' _ OpenAI.html', '').replace('_', ' ')
        
        # Try to extract customer name from title or content first
        customer_name = self._extract_customer_name_from_content(soup, filename_customer)
        
        # Extract the main content text
        content_text = ""
        
        # Try to find main content area
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=re.compile(r'content|story|article', re.I)) or
            soup.find('body')
        )
        
        if main_content:
            # Remove script and style elements
            for script in main_content(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            content_text = main_content.get_text()
        else:
            content_text = soup.get_text()
        
        # Clean up text
        content_text = re.sub(r'\s+', ' ', content_text).strip()
        
        # Try to extract publish date from content
        publish_date = self._extract_publish_date(soup, content_text)
        
        # Generate a synthetic URL based on customer name
        url_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', customer_name.lower())
        url_slug = re.sub(r'\s+', '-', url_slug)
        synthetic_url = f"https://openai.com/index/{url_slug}/"
        
        return {
            'customer_name': customer_name,
            'title': title,
            'url': synthetic_url,
            'content_text': content_text,
            'html_content': html_content,
            'publish_date': publish_date,
            'filename': filename
        }
    
    def _extract_customer_name_from_content(self, soup: BeautifulSoup, filename_customer: str) -> str:
        """Extract customer name from HTML content, using Claude if needed"""
        
        # First try simple filename cleanup for obvious cases
        customer_name = filename_customer
        
        # Clean up common patterns in customer names
        customer_name = re.sub(r'^(AI helps |Building |Creating |Driving |Using |Supporting |Automating |Bringing |Catching |Enabling |Moving |Personalizing |Shipping |Understanding |Accelerating )', '', customer_name, flags=re.IGNORECASE)
        customer_name = re.sub(r'( with OpenAI| with ChatGPT| with AI| with o1| with GPT| powered by| uses AI).*$', '', customer_name, flags=re.IGNORECASE)
        customer_name = re.sub(r'( and Gaming| and Healthcare| Betting and Gaming| ML is helping).*$', '', customer_name, flags=re.IGNORECASE)
        
        # Handle obvious cases from filename
        obvious_companies = ['John Deere', 'Expedia', 'Canva', 'Nubank', 'Uber', 'Wayfair', 'EliseAI', 'Speak', 'LaunchDarkly', 'Retell AI', 'Invideo AI', 'Genspark', 'Outtake', 'Model ML', 'Unify']
        for company in obvious_companies:
            if company.lower() in customer_name.lower():
                return company
        
        # Special cases for filename patterns
        if 'Lowe' in customer_name:
            return "Lowe's"
        elif 'Spurs' in customer_name:
            return 'San Antonio Spurs'
        elif 'Fanatics' in customer_name:
            return 'Fanatics Betting and Gaming'
        
        # Clean up remaining patterns
        customer_name = re.sub(r'^(s approach to|enables|improves|leverages|puts|ships|makes|is helping)', '', customer_name, flags=re.IGNORECASE)
        customer_name = customer_name.strip()
        
        # If customer name is still unclear (generic words, too long, etc.), use Claude
        if (len(customer_name) < 3 or 
            len(customer_name) > 40 or
            any(word in customer_name.lower() for word in ['engineering', 'finance', 'intelligence', 'math', 'autonomous', 
                                                          'halibut', 'nail art', 'websites', 'growth', 'intent-based',
                                                          'travel', 'sellers', 'complex', 'code', 'approach'])):
            
            print(f"    Using Claude to extract customer name for: {filename_customer}")
            content_text = soup.get_text()[:2000]  # First 2000 chars should be enough
            
            claude_customer_name = self._extract_customer_name_with_claude(content_text, filename_customer)
            if claude_customer_name and claude_customer_name != filename_customer:
                return claude_customer_name
        
        return customer_name if customer_name else filename_customer
    
    def _extract_customer_name_with_claude(self, content_text: str, filename_hint: str) -> Optional[str]:
        """Use Claude to extract customer/company name from content"""
        try:
            prompt = f"""Please identify the main company or customer name from this OpenAI customer story content.

Filename hint: {filename_hint}

Content excerpt:
{content_text}

Instructions:
- Return ONLY the company/customer name (e.g., "GitHub", "Khan Academy", "Bloomberg")
- Do not include descriptive text or explanations
- If multiple companies are mentioned, return the main customer/subject of the story
- If unclear, return the most likely company name based on context

Company name:"""

            response = self.claude_processor.client.messages.create(
                model=self.claude_processor.model,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response.content and response.content[0].text:
                extracted_name = response.content[0].text.strip()
                # Basic validation
                if len(extracted_name) > 2 and len(extracted_name) < 50:
                    return extracted_name
            
        except Exception as e:
            print(f"    Error using Claude for customer name extraction: {e}")
        
        return None

    def _extract_publish_date(self, soup: BeautifulSoup, content_text: str) -> Optional[datetime]:
        """Try to extract publish date from HTML content"""
        
        # Look for time elements with datetime attribute
        time_elements = soup.find_all('time', datetime=True)
        for time_elem in time_elements:
            try:
                date_str = time_elem.get('datetime')
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            except:
                continue
        
        # Look for date patterns in text
        date_patterns = [
            r'(\w+ \d{1,2}, \d{4})',  # "January 15, 2024"
            r'(\d{1,2}/\d{1,2}/\d{4})',  # "01/15/2024"
            r'(\d{4}-\d{2}-\d{2})',  # "2024-01-15"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content_text)
            if matches:
                try:
                    # Try to parse the first match
                    date_str = matches[0]
                    return datetime.strptime(date_str, '%B %d, %Y').date()
                except:
                    try:
                        return datetime.strptime(date_str, '%m/%d/%Y').date()
                    except:
                        try:
                            return datetime.strptime(date_str, '%Y-%m-%d').date()
                        except:
                            continue
        
        return None
    
    def process_html_files(self, limit: Optional[int] = None) -> List[Dict]:
        """Process all HTML files in the openaicases directory"""
        
        if not self.html_dir.exists():
            print(f"Directory {self.html_dir} does not exist")
            return []
        
        html_files = list(self.html_dir.glob("*.html"))
        if limit:
            html_files = html_files[:limit]
        
        print(f"Found {len(html_files)} HTML files to process")
        
        processed_stories = []
        
        for html_file in html_files:
            print(f"\nProcessing: {html_file.name}")
            
            try:
                # Read HTML content
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Extract story data
                story_data = self.extract_story_data_from_html(html_content, html_file.name)
                
                print(f"  Customer: {story_data['customer_name']}")
                print(f"  Title: {story_data['title'][:60]}...")
                print(f"  Content length: {len(story_data['content_text'])} chars")
                print(f"  Publish date: {story_data['publish_date']}")
                
                processed_stories.append(story_data)
                
            except Exception as e:
                print(f"  Error processing {html_file.name}: {e}")
                continue
        
        return processed_stories
    
    def save_stories_to_database(self, processed_stories: List[Dict]) -> int:
        """Save processed stories to database"""
        
        # Get OpenAI source
        openai_source = self.db_ops.get_source_by_name("OpenAI")
        if not openai_source:
            print("OpenAI source not found in database")
            return 0
        
        saved_count = 0
        
        for story_data in processed_stories:
            try:
                # Check if story already exists
                if self.db_ops.check_story_exists(story_data['url']):
                    print(f"  Skipping {story_data['customer_name']} - already exists")
                    continue
                
                print(f"\nProcessing with Claude AI: {story_data['customer_name']}")
                
                # Create temporary raw content structure for Claude processor
                temp_raw_content = {
                    'text': story_data['content_text'],
                    'html': story_data['html_content']
                }
                
                # Process with Claude
                extracted_data = self.claude_processor.extract_story_data(temp_raw_content)
                
                if not extracted_data:
                    print(f"  Failed to extract data for {story_data['customer_name']}")
                    continue
                
                # Create raw content structure
                raw_content = {
                    'html': story_data['html_content'],
                    'text': story_data['content_text'],
                    'metadata': {
                        'title': story_data['title'],
                        'word_count': len(story_data['content_text'].split()),
                        'source_filename': story_data['filename']
                    },
                    'scraping_info': {
                        'scraper_version': 'html_processor_1.0',
                        'timestamp': datetime.now().isoformat(),
                        'source': 'manual_html_collection'
                    }
                }
                
                # Generate content hash
                content_hash = hashlib.sha256(story_data['content_text'].encode()).hexdigest()
                
                # Create CustomerStory object
                customer_story = CustomerStory(
                    id=None,  # Will be assigned by database
                    source_id=openai_source.id,
                    customer_name=story_data['customer_name'],
                    title=story_data['title'],
                    url=story_data['url'],
                    content_hash=content_hash,
                    industry=extracted_data.get('company_info', {}).get('industry_sector'),
                    company_size=extracted_data.get('company_info', {}).get('estimated_size'),
                    use_case_category=', '.join(extracted_data.get('use_cases', [])[:3]),
                    raw_content=raw_content,
                    extracted_data=extracted_data,
                    publish_date=story_data['publish_date'],
                    scraped_date=datetime.now(),
                    last_updated=datetime.now()
                )
                
                # Save to database
                story_id = self.db_ops.insert_customer_story(customer_story)
                
                if story_id:
                    print(f"  ✅ Saved as Story ID {story_id}")
                    print(f"     Quality Score: {extracted_data.get('content_quality_score', 'N/A')}")
                    print(f"     Use Cases: {', '.join(extracted_data.get('use_cases', [])[:3])}")
                    saved_count += 1
                else:
                    print(f"  ❌ Failed to save {story_data['customer_name']}")
                
            except Exception as e:
                print(f"  Error saving {story_data['customer_name']}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return saved_count

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process OpenAI HTML files')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--test', action='store_true', help='Test mode - process only 3 files')
    parser.add_argument('--dry-run', action='store_true', help='Extract data but do not save to database')
    
    args = parser.parse_args()
    
    if args.test:
        args.limit = 3
    
    processor = OpenAIHTMLProcessor()
    
    print("="*60)
    print("OPENAI HTML PROCESSOR")
    print("="*60)
    
    # Process HTML files
    processed_stories = processor.process_html_files(limit=args.limit)
    
    if not processed_stories:
        print("No stories processed")
        return
    
    print(f"\n{'='*60}")
    print(f"PROCESSED {len(processed_stories)} STORIES")
    print(f"{'='*60}")
    
    if args.dry_run:
        print("DRY RUN - Not saving to database")
        for story in processed_stories:
            print(f"• {story['customer_name']}: {len(story['content_text'])} chars")
        return
    
    # Save to database
    print("\nSaving to database...")
    saved_count = processor.save_stories_to_database(processed_stories)
    
    print(f"\n{'='*60}")
    print(f"COMPLETED: {saved_count}/{len(processed_stories)} stories saved to database")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()