import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
from src.database.models import DatabaseOperations, CustomerStory
from src.ai_integration.claude_processor import ClaudeProcessor

logger = logging.getLogger(__name__)

class DeduplicationEngine:
    def __init__(self, db_ops: DatabaseOperations, claude_processor: ClaudeProcessor = None):
        self.db_ops = db_ops
        self.claude_processor = claude_processor or ClaudeProcessor()
        
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase and remove common suffixes
        normalized = name.lower().strip()
        
        # Remove common business suffixes
        suffixes = [
            r'\s+(inc\.?|incorporated)$',
            r'\s+(ltd\.?|limited)$', 
            r'\s+(llc\.?)$',
            r'\s+(corp\.?|corporation)$',
            r'\s+(co\.?)$',
            r'\s+plc$',
            r'\s+group$',
            r'\s+company$',
            r'\s+technologies?$',
            r'\s+solutions?$',
            r'\s+systems?$',
            r'\s+labs?$'
        ]
        
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized)
        
        # Remove special characters and extra whitespace
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Use SequenceMatcher for basic similarity
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def find_per_source_duplicates(self, source_id: int, similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
        """Find duplicate stories within the same source"""
        logger.info(f"Finding duplicates for source ID: {source_id}")
        
        # Get all stories for this source
        stories = self.db_ops.get_stories_by_source(source_id)
        duplicates = []
        
        for i, story1 in enumerate(stories):
            for j, story2 in enumerate(stories[i + 1:], i + 1):
                duplicate_info = self.compare_stories(story1, story2, similarity_threshold)
                
                if duplicate_info['is_duplicate']:
                    duplicate_group = {
                        'source_id': source_id,
                        'canonical_story': story1,
                        'duplicate_story': story2,
                        'similarity_score': duplicate_info['similarity_score'],
                        'duplicate_reason': duplicate_info['reason']
                    }
                    duplicates.append(duplicate_group)
        
        logger.info(f"Found {len(duplicates)} duplicate pairs for source {source_id}")
        return duplicates
    
    def compare_stories(self, story1: CustomerStory, story2: CustomerStory, threshold: float = 0.85) -> Dict[str, Any]:
        """Compare two stories to determine if they are duplicates"""
        
        # Quick checks first
        if story1.url == story2.url:
            return {
                'is_duplicate': True,
                'similarity_score': 1.0,
                'reason': 'identical_url'
            }
        
        # Normalize company names for comparison
        norm_name1 = self.normalize_company_name(story1.customer_name)
        norm_name2 = self.normalize_company_name(story2.customer_name)
        
        # If company names are very different, likely not duplicates
        name_similarity = self.calculate_text_similarity(norm_name1, norm_name2)
        if name_similarity < 0.7:
            return {
                'is_duplicate': False,
                'similarity_score': name_similarity,
                'reason': 'different_companies'
            }
        
        # Compare content similarity
        content1 = story1.raw_content.get('text', '') if story1.raw_content else ''
        content2 = story2.raw_content.get('text', '') if story2.raw_content else ''
        
        content_similarity = self.calculate_text_similarity(content1[:2000], content2[:2000])  # Compare first 2000 chars
        
        # Compare titles if available
        title_similarity = 0.0
        if story1.title and story2.title:
            title_similarity = self.calculate_text_similarity(story1.title, story2.title)
        
        # Calculate overall similarity score
        overall_similarity = (name_similarity * 0.3 + content_similarity * 0.5 + title_similarity * 0.2)
        
        is_duplicate = overall_similarity >= threshold
        
        # Determine reason
        reason = 'content_similarity' if is_duplicate else 'insufficient_similarity'
        if content_similarity > 0.95:
            reason = 'identical_content'
        elif title_similarity > 0.9 and name_similarity > 0.8:
            reason = 'same_story_updated'
        
        return {
            'is_duplicate': is_duplicate,
            'similarity_score': overall_similarity,
            'reason': reason,
            'details': {
                'name_similarity': name_similarity,
                'content_similarity': content_similarity,
                'title_similarity': title_similarity
            }
        }
    
    def find_cross_source_customers(self) -> List[Dict[str, Any]]:
        """Find customers that appear across multiple sources"""
        logger.info("Finding customers across multiple sources")
        
        # Get all stories grouped by normalized customer names
        with self.db_ops.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    customer_name,
                    source_id,
                    COUNT(*) as story_count,
                    ARRAY_AGG(id) as story_ids,
                    ARRAY_AGG(url) as urls
                FROM customer_stories 
                GROUP BY customer_name, source_id
                ORDER BY customer_name
            """)
            
            results = cursor.fetchall()
        
        # Group by normalized customer names
        customer_groups = {}
        for row in results:
            normalized_name = self.normalize_company_name(row['customer_name'])
            
            if normalized_name not in customer_groups:
                customer_groups[normalized_name] = []
            
            customer_groups[normalized_name].append({
                'original_name': row['customer_name'],
                'source_id': row['source_id'],
                'story_count': row['story_count'],
                'story_ids': row['story_ids'],
                'urls': row['urls']
            })
        
        # Find groups with multiple sources
        cross_source_customers = []
        for normalized_name, sources in customer_groups.items():
            if len(sources) > 1:  # Customer appears in multiple sources
                source_names = []
                total_stories = 0
                all_story_ids = []
                
                for source_info in sources:
                    source = self.db_ops.get_source_by_name(self._get_source_name_by_id(source_info['source_id']))
                    source_names.append(source.name if source else f"Source {source_info['source_id']}")
                    total_stories += source_info['story_count']
                    all_story_ids.extend(source_info['story_ids'])
                
                cross_source_customers.append({
                    'normalized_name': normalized_name,
                    'sources': sources,
                    'source_names': source_names,
                    'total_stories': total_stories,
                    'story_ids': all_story_ids
                })
        
        logger.info(f"Found {len(cross_source_customers)} customers across multiple sources")
        return cross_source_customers
    
    def _get_source_name_by_id(self, source_id: int) -> str:
        """Helper to get source name by ID"""
        source_map = {1: "Anthropic", 2: "Microsoft", 3: "AWS", 4: "Google Cloud", 5: "OpenAI"}
        return source_map.get(source_id, "Unknown")
    
    def create_customer_profiles(self, cross_source_customers: List[Dict[str, Any]]) -> List[int]:
        """Create customer profiles for cross-source customers"""
        logger.info("Creating customer profiles for cross-source customers")
        
        profile_ids = []
        
        for customer in cross_source_customers:
            # Check if profile already exists
            with self.db_ops.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM customer_profiles WHERE canonical_name = %s",
                    (customer['normalized_name'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    profile_id = existing['id']
                    logger.info(f"Customer profile already exists: {customer['normalized_name']}")
                else:
                    # Create new profile
                    alternative_names = list(set(source['original_name'] for source in customer['sources']))
                    
                    cursor.execute("""
                        INSERT INTO customer_profiles (canonical_name, alternative_names, story_count, sources_present)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        customer['normalized_name'],
                        alternative_names,
                        customer['total_stories'],
                        customer['source_names']
                    ))
                    
                    profile_id = cursor.fetchone()['id']
                    logger.info(f"Created customer profile ID {profile_id}: {customer['normalized_name']}")
                
                # Link stories to profile
                for story_id in customer['story_ids']:
                    cursor.execute("""
                        INSERT INTO customer_story_links (customer_profile_id, story_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (profile_id, story_id))
                
                profile_ids.append(profile_id)
        
        logger.info(f"Created/updated {len(profile_ids)} customer profiles")
        return profile_ids
    
    def run_full_deduplication_analysis(self, source_id: int = None) -> Dict[str, Any]:
        """Run complete deduplication analysis"""
        logger.info("Starting full deduplication analysis")
        
        results = {
            'per_source_duplicates': {},
            'cross_source_customers': [],
            'customer_profiles_created': []
        }
        
        # Per-source deduplication
        if source_id:
            sources = [source_id]
        else:
            all_sources = self.db_ops.get_sources()
            sources = [source.id for source in all_sources if source.active]
        
        for src_id in sources:
            duplicates = self.find_per_source_duplicates(src_id)
            if duplicates:
                results['per_source_duplicates'][src_id] = duplicates
        
        # Cross-source customer analysis
        cross_source = self.find_cross_source_customers()
        results['cross_source_customers'] = cross_source
        
        # Create customer profiles
        if cross_source:
            profile_ids = self.create_customer_profiles(cross_source)
            results['customer_profiles_created'] = profile_ids
        
        logger.info("Deduplication analysis completed")
        return results