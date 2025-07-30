import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from src.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

@dataclass
class Source:
    id: int
    name: str
    base_url: str
    last_scraped: Optional[datetime] = None
    active: bool = True

@dataclass
class DiscoveredUrl:
    id: Optional[int]
    source_id: int
    url: str
    inferred_customer_name: Optional[str] = None
    inferred_title: Optional[str] = None
    publish_date: Optional[datetime] = None
    discovered_date: Optional[datetime] = None
    last_scrape_attempt: Optional[datetime] = None
    scrape_attempts: int = 0
    scrape_status: str = 'pending'  # 'pending', 'scraped', 'failed', 'filtered_out'
    scrape_error: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class CustomerStory:
    id: Optional[int]
    source_id: int
    customer_name: str
    title: Optional[str]
    url: str
    content_hash: Optional[str]
    industry: Optional[str] = None
    company_size: Optional[str] = None
    use_case_category: Optional[str] = None
    raw_content: Dict[str, Any] = None
    extracted_data: Optional[Dict[str, Any]] = None
    scraped_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    publish_date: Optional[datetime] = None

class DatabaseOperations:
    def __init__(self, db_connection: DatabaseConnection = None):
        self.db = db_connection or DatabaseConnection()
    
    def get_sources(self, active_only: bool = True) -> List[Source]:
        """Retrieve all sources from database"""
        query = "SELECT * FROM sources"
        if active_only:
            query += " WHERE active = true"
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [Source(**row) for row in rows]
    
    def get_source_by_name(self, name: str) -> Optional[Source]:
        """Get source by name"""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM sources WHERE name = %s", (name,))
            row = cursor.fetchone()
            return Source(**row) if row else None
    
    def insert_customer_story(self, story: CustomerStory) -> int:
        """Insert a new customer story and return its ID"""
        insert_query = """
        INSERT INTO customer_stories (
            source_id, customer_name, title, url, content_hash,
            industry, company_size, use_case_category,
            raw_content, extracted_data, publish_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        values = (
            story.source_id,
            story.customer_name,
            story.title,
            story.url,
            story.content_hash,
            story.industry,
            story.company_size,
            story.use_case_category,
            json.dumps(story.raw_content) if story.raw_content else None,
            json.dumps(story.extracted_data) if story.extracted_data else None,
            story.publish_date
        )
        
        with self.db.get_cursor() as cursor:
            cursor.execute(insert_query, values)
            story_id = cursor.fetchone()['id']
            logger.info(f"Inserted customer story ID: {story_id}")
            return story_id
    
    def get_story_by_url(self, url: str) -> Optional[CustomerStory]:
        """Get story by URL"""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM customer_stories WHERE url = %s", (url,))
            row = cursor.fetchone()
            if row:
                return CustomerStory(
                    id=row['id'],
                    source_id=row['source_id'],
                    customer_name=row['customer_name'],
                    title=row['title'],
                    url=row['url'],
                    content_hash=row['content_hash'],
                    industry=row['industry'],
                    company_size=row['company_size'],
                    use_case_category=row['use_case_category'],
                    raw_content=row['raw_content'],
                    extracted_data=row['extracted_data'],
                    scraped_date=row['scraped_date'],
                    last_updated=row['last_updated'],
                    publish_date=row['publish_date']
                )
            return None
    
    def update_story_extracted_data(self, story_id: int, extracted_data: Dict[str, Any]):
        """Update extracted data for a story"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE customer_stories SET extracted_data = %s, last_updated = CURRENT_TIMESTAMP WHERE id = %s",
                (json.dumps(extracted_data), story_id)
            )
            logger.info(f"Updated extracted data for story ID: {story_id}")
    
    def check_story_exists(self, url: str) -> bool:
        """Check if story already exists by URL"""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM customer_stories WHERE url = %s", (url,))
            return cursor.fetchone()['count'] > 0
    
    def get_stories_by_source(self, source_id: int, limit: int = None) -> List[CustomerStory]:
        """Get all stories for a source"""
        query = "SELECT * FROM customer_stories WHERE source_id = %s ORDER BY scraped_date DESC"
        params = [source_id]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_story(row) for row in rows]
    
    def search_stories(self, search_term: str, limit: int = 50) -> List[CustomerStory]:
        """Full-text search for stories"""
        query = """
        SELECT * FROM customer_stories 
        WHERE search_vector @@ plainto_tsquery('english', %s)
        ORDER BY ts_rank(search_vector, plainto_tsquery('english', %s)) DESC
        LIMIT %s
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (search_term, search_term, limit))
            rows = cursor.fetchall()
            return [self._row_to_story(row) for row in rows]
    
    def update_source_last_scraped(self, source_id: int):
        """Update last_scraped timestamp for a source"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE sources SET last_scraped = CURRENT_TIMESTAMP WHERE id = %s",
                (source_id,)
            )
    
    # Discovered URLs operations for two-phase scraping
    
    def insert_discovered_url(self, discovered_url: DiscoveredUrl) -> int:
        """Insert a new discovered URL and return its ID"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO discovered_urls 
                (source_id, url, inferred_customer_name, inferred_title, publish_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    inferred_customer_name = EXCLUDED.inferred_customer_name,
                    inferred_title = EXCLUDED.inferred_title,
                    publish_date = EXCLUDED.publish_date,
                    notes = EXCLUDED.notes
                RETURNING id
            """, (
                discovered_url.source_id,
                discovered_url.url,
                discovered_url.inferred_customer_name,
                discovered_url.inferred_title,
                discovered_url.publish_date,
                discovered_url.notes
            ))
            
            row = cursor.fetchone()
            discovered_id = row['id']
            logger.info(f"Inserted/updated discovered URL ID: {discovered_id}")
            return discovered_id
    
    def get_pending_urls(self, source_id: int, limit: int = None) -> List[DiscoveredUrl]:
        """Get URLs that are pending scraping"""
        query = """
            SELECT * FROM discovered_urls 
            WHERE source_id = %s AND scrape_status = 'pending'
            ORDER BY publish_date DESC NULLS LAST, discovered_date ASC
        """
        params = [source_id]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_discovered_url(row) for row in rows]
    
    def update_discovered_url_status(self, url_id: int, status: str, error: str = None):
        """Update scrape status and attempt count for discovered URL"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE discovered_urls 
                SET scrape_status = %s, 
                    scrape_attempts = scrape_attempts + 1,
                    last_scrape_attempt = CURRENT_TIMESTAMP,
                    scrape_error = %s
                WHERE id = %s
            """, (status, error, url_id))
            logger.info(f"Updated discovered URL {url_id} status to: {status}")
    
    def get_discovered_url_by_url(self, url: str) -> Optional[DiscoveredUrl]:
        """Get discovered URL by URL string"""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM discovered_urls WHERE url = %s", (url,))
            row = cursor.fetchone()
            if row:
                return self._row_to_discovered_url(row)
            return None
    
    def get_discovery_stats(self, source_id: int) -> Dict[str, int]:
        """Get statistics about discovered URLs for a source"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    scrape_status,
                    COUNT(*) as count
                FROM discovered_urls 
                WHERE source_id = %s 
                GROUP BY scrape_status
            """, (source_id,))
            
            stats = {row['scrape_status']: row['count'] for row in cursor.fetchall()}
            
            # Get total count
            cursor.execute(
                "SELECT COUNT(*) as total FROM discovered_urls WHERE source_id = %s", 
                (source_id,)
            )
            stats['total'] = cursor.fetchone()['total']
            
            return stats
    
    def _row_to_story(self, row: Dict) -> CustomerStory:
        """Convert database row to CustomerStory object"""
        return CustomerStory(
            id=row['id'],
            source_id=row['source_id'],
            customer_name=row['customer_name'],
            title=row['title'],
            url=row['url'],
            content_hash=row['content_hash'],
            industry=row['industry'],
            company_size=row['company_size'],
            use_case_category=row['use_case_category'],
            raw_content=row['raw_content'],
            extracted_data=row['extracted_data'],
            scraped_date=row['scraped_date'],
            last_updated=row['last_updated'],
            publish_date=row['publish_date']
        )
    
    def _row_to_discovered_url(self, row: Dict) -> DiscoveredUrl:
        """Convert database row to DiscoveredUrl object"""
        return DiscoveredUrl(
            id=row['id'],
            source_id=row['source_id'],
            url=row['url'],
            inferred_customer_name=row['inferred_customer_name'],
            inferred_title=row['inferred_title'],
            publish_date=row['publish_date'],
            discovered_date=row['discovered_date'],
            last_scrape_attempt=row['last_scrape_attempt'],
            scrape_attempts=row['scrape_attempts'],
            scrape_status=row['scrape_status'],
            scrape_error=row['scrape_error'],
            notes=row['notes']
        )

def generate_content_hash(content: str) -> str:
    """Generate SHA256 hash of content for change detection"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()