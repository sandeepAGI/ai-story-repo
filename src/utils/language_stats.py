#!/usr/bin/env python3
"""
Language statistics and filtering utilities for customer stories
"""

import logging
from typing import Dict, List, Optional
from src.database.models import DatabaseOperations

logger = logging.getLogger(__name__)

class LanguageStatistics:
    """Utilities for language-based statistics and filtering"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    def get_language_distribution(self, source_name: Optional[str] = None) -> Dict[str, int]:
        """Get language distribution across all stories or for a specific source"""
        
        query = """
        SELECT 
            detected_language,
            COUNT(*) as story_count
        FROM customer_stories cs
        """
        
        params = []
        if source_name:
            query += """
            JOIN sources s ON cs.source_id = s.id
            WHERE s.name = %s
            """
            params.append(source_name)
        
        query += """
        GROUP BY detected_language
        ORDER BY story_count DESC
        """
        
        with self.db_ops.db.get_cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
        
        return {row['detected_language']: row['story_count'] for row in results}
    
    def get_language_stats_by_source(self) -> Dict[str, Dict[str, int]]:
        """Get language distribution broken down by source"""
        
        query = """
        SELECT 
            s.name as source_name,
            cs.detected_language,
            COUNT(*) as story_count
        FROM customer_stories cs
        JOIN sources s ON cs.source_id = s.id
        GROUP BY s.name, cs.detected_language
        ORDER BY s.name, story_count DESC
        """
        
        with self.db_ops.db.get_cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        
        # Organize by source
        stats = {}
        for row in results:
            source = row['source_name']
            language = row['detected_language']
            count = row['story_count']
            
            if source not in stats:
                stats[source] = {}
            stats[source][language] = count
        
        return stats
    
    def get_non_english_stories(self, limit: int = 50) -> List[Dict]:
        """Get details of non-English stories"""
        
        query = """
        SELECT 
            cs.customer_name,
            cs.title,
            cs.url,
            cs.detected_language,
            cs.language_detection_method,
            cs.language_confidence,
            s.name as source_name
        FROM customer_stories cs
        JOIN sources s ON cs.source_id = s.id
        WHERE cs.detected_language != 'English'
        ORDER BY cs.language_confidence DESC, cs.detected_language
        LIMIT %s
        """
        
        with self.db_ops.db.get_cursor() as cursor:
            cursor.execute(query, (limit,))
            return cursor.fetchall()
    
    def get_language_confidence_stats(self) -> Dict[str, Dict[str, int]]:
        """Get confidence level distribution by language"""
        
        query = """
        SELECT 
            detected_language,
            CASE 
                WHEN language_confidence >= 0.9 THEN 'High (0.9+)'
                WHEN language_confidence >= 0.7 THEN 'Medium (0.7-0.9)'
                WHEN language_confidence >= 0.5 THEN 'Low (0.5-0.7)'
                ELSE 'Very Low (<0.5)'
            END as confidence_level,
            COUNT(*) as story_count
        FROM customer_stories
        GROUP BY detected_language, confidence_level
        ORDER BY detected_language, confidence_level
        """
        
        with self.db_ops.db.get_cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        
        # Organize by language
        stats = {}
        for row in results:
            language = row['detected_language']
            confidence_level = row['confidence_level']
            count = row['story_count']
            
            if language not in stats:
                stats[language] = {}
            stats[language][confidence_level] = count
        
        return stats
    
    def print_language_summary(self):
        """Print comprehensive language statistics summary"""
        
        print("=" * 70)
        print("LANGUAGE DISTRIBUTION SUMMARY")
        print("=" * 70)
        
        # Overall distribution
        overall_dist = self.get_language_distribution()
        total_stories = sum(overall_dist.values())
        
        print(f"\nOVERALL DISTRIBUTION ({total_stories:,} total stories):")
        print("-" * 50)
        for language, count in overall_dist.items():
            percentage = (count / total_stories) * 100
            print(f"{language:20}: {count:4,} stories ({percentage:5.1f}%)")
        
        # By source breakdown
        print(f"\nLANGUAGE DISTRIBUTION BY SOURCE:")
        print("-" * 50)
        source_stats = self.get_language_stats_by_source()
        
        for source, languages in source_stats.items():
            source_total = sum(languages.values())
            print(f"\n{source} ({source_total:,} stories):")
            for language, count in languages.items():
                percentage = (count / source_total) * 100
                print(f"  {language:18}: {count:4,} stories ({percentage:5.1f}%)")
        
        # Non-English story details
        non_english = self.get_non_english_stories(10)
        if non_english:
            print(f"\nTOP NON-ENGLISH STORIES (showing {len(non_english)} of {sum(v for k, v in overall_dist.items() if k != 'English')}):")
            print("-" * 50)
            
            for i, story in enumerate(non_english, 1):
                print(f"{i:2d}. [{story['detected_language']}] {story['customer_name']}")
                print(f"    {story['title'][:60]}...")
                print(f"    Confidence: {story['language_confidence']:.2f} ({story['language_detection_method']})")
                print(f"    Source: {story['source_name']}")
                print()

def print_language_statistics():
    """Convenience function to print language statistics"""
    stats = LanguageStatistics()
    stats.print_language_summary()

if __name__ == "__main__":
    print_language_statistics()