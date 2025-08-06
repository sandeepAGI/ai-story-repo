#!/usr/bin/env python3
"""
GoogleCloud Customer Name Investigation Script
Phase 1: Read-only analysis of affected records
"""

import sys
import os
from typing import List, Dict, Any
import re

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations

class GoogleCloudNameInvestigator:
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    def analyze_affected_records(self) -> Dict[str, Any]:
        """Analyze GoogleCloud records with problematic customer names"""
        
        with self.db_ops.db.get_cursor() as cursor:
            # Get GoogleCloud source ID
            cursor.execute("SELECT id FROM sources WHERE name = 'Google Cloud'")
            source_result = cursor.fetchone()
            
            if not source_result:
                return {"error": "Google Cloud source not found in database"}
            
            source_id = source_result['id']
            
            # Find all GoogleCloud stories
            cursor.execute("""
                SELECT id, customer_name, url, title, scraped_date
                FROM customer_stories 
                WHERE source_id = %s
                ORDER BY scraped_date DESC
            """, (source_id,))
            
            all_records = cursor.fetchall()
            
            # Analyze patterns
            problematic_records = []
            url_as_name_records = []
            clean_records = []
            
            for record in all_records:
                customer_name = record['customer_name']
                url = record['url']
                
                # Check if customer name looks like a URL
                if customer_name.startswith('http'):
                    url_as_name_records.append(record)
                    problematic_records.append(record)
                # Check if customer name has URL-like patterns
                elif ('.' in customer_name and 
                      ('Cloud.Google.Com' in customer_name or 
                       'Blog' in customer_name or
                       len(customer_name) > 100)):
                    problematic_records.append(record)
                else:
                    clean_records.append(record)
            
            return {
                "total_records": len(all_records),
                "problematic_records": len(problematic_records),
                "url_as_name_records": len(url_as_name_records),
                "clean_records": len(clean_records),
                "sample_problematic": problematic_records[:10],
                "sample_clean": clean_records[:5],
                "analysis": self._analyze_patterns(problematic_records)
            }
    
    def _analyze_patterns(self, problematic_records: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in problematic records"""
        
        blog_urls = []
        customer_urls = []
        other_patterns = []
        
        for record in problematic_records:
            url = record['url']
            customer_name = record['customer_name']
            
            if '/blog/' in url:
                blog_urls.append(record)
            elif '/customers/' in url:
                customer_urls.append(record)
            else:
                other_patterns.append(record)
        
        return {
            "blog_url_issues": len(blog_urls),
            "customer_url_issues": len(customer_urls),
            "other_issues": len(other_patterns),
            "sample_blog_issues": blog_urls[:5],
            "sample_customer_issues": customer_urls[:3],
            "sample_other_issues": other_patterns[:3]
        }
    
    def extract_company_from_blog_url(self, url: str, title: str = None) -> str:
        """Test extraction logic for blog URLs"""
        
        # Strategy 1: Extract from URL path
        # Example: /blog/topics/retail/how-google-cloud-services-helped-lowes-transform-ecommerce
        url_patterns = [
            r'/blog/[^/]+/[^/]+/[^/]*?([a-zA-Z]+(?:-[a-zA-Z]+)*)[^/]*?(?:transform|improve|help|use|implement|deploy)',
            r'/blog/[^/]+/[^/]+/.*?-([a-zA-Z]+(?:-[a-zA-Z]+)*)-(?:transform|improve|help|case|story)',
            r'/([a-zA-Z]+(?:-[a-zA-Z]+)*)-(?:case-study|customer-story|success)',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                company = match.group(1).replace('-', ' ').title()
                # Filter out common words
                if company.lower() not in ['google', 'cloud', 'services', 'help', 'how', 'with', 'and', 'the']:
                    return company
        
        # Strategy 2: Extract from title if available
        if title:
            # Look for company names in titles
            title_patterns = [
                r'(?:how\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:uses?|transforms?|improves?|leverages?)',
                r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:case\s+study|success\s+story)',
                r'(?:case\s+study:?\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, title)
                if match:
                    company = match.group(1).strip()
                    if len(company) > 2 and company.lower() not in ['google', 'cloud', 'how']:
                        return company
        
        # Strategy 3: Fallback - try to extract any recognizable company name from URL
        url_parts = url.split('/')
        for part in reversed(url_parts):
            # Look for parts that might be company names
            if len(part) > 3 and '-' in part:
                words = part.split('-')
                potential_companies = []
                
                for word in words:
                    if (len(word) > 3 and 
                        word.lower() not in ['google', 'cloud', 'how', 'with', 'help', 'case', 'study', 'story', 'uses', 'transforms', 'improves']):
                        potential_companies.append(word.title())
                
                if potential_companies:
                    return ' '.join(potential_companies[:2])  # Take first 1-2 words
        
        return "Unknown Company"
    
    def test_extraction_on_samples(self, sample_records: List[Dict]) -> List[Dict]:
        """Test extraction logic on sample problematic records"""
        
        results = []
        
        for record in sample_records:
            original_name = record['customer_name']
            url = record['url']
            title = record.get('title', '')
            
            extracted_name = self.extract_company_from_blog_url(url, title)
            
            results.append({
                'id': record['id'],
                'original_name': original_name,
                'extracted_name': extracted_name,
                'url': url,
                'title': title,
                'improvement': len(extracted_name) < len(original_name) / 2
            })
        
        return results

def main():
    """Run the investigation"""
    print("🔍 GoogleCloud Customer Name Investigation")
    print("=" * 50)
    
    investigator = GoogleCloudNameInvestigator()
    
    try:
        # Phase 1: Analyze affected records
        print("\n📊 Analyzing GoogleCloud records...")
        analysis = investigator.analyze_affected_records()
        
        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            return
        
        # Display summary
        print(f"\n📈 SUMMARY:")
        print(f"  Total GoogleCloud stories: {analysis['total_records']}")
        print(f"  Problematic records: {analysis['problematic_records']}")
        print(f"  Records with URL as name: {analysis['url_as_name_records']}")
        print(f"  Clean records: {analysis['clean_records']}")
        
        # Display pattern analysis
        patterns = analysis['analysis']
        print(f"\n🔍 PATTERN ANALYSIS:")
        print(f"  Blog URL issues: {patterns['blog_url_issues']}")
        print(f"  Customer URL issues: {patterns['customer_url_issues']}")
        print(f"  Other issues: {patterns['other_issues']}")
        
        # Show sample problematic records
        print(f"\n❌ SAMPLE PROBLEMATIC RECORDS:")
        for i, record in enumerate(analysis['sample_problematic'], 1):
            print(f"  {i}. ID: {record['id']}")
            print(f"     Customer Name: {record['customer_name'][:100]}...")
            print(f"     URL: {record['url']}")
            print(f"     Title: {record.get('title', 'N/A')}")
            print()
        
        # Show sample clean records for comparison
        print(f"\n✅ SAMPLE CLEAN RECORDS (for comparison):")
        for i, record in enumerate(analysis['sample_clean'], 1):
            print(f"  {i}. {record['customer_name']} - {record['url']}")
        
        # Test extraction logic
        print(f"\n🧪 TESTING EXTRACTION LOGIC:")
        test_results = investigator.test_extraction_on_samples(
            patterns['sample_blog_issues'][:5]
        )
        
        improvements = 0
        for result in test_results:
            print(f"\n  Record ID: {result['id']}")
            print(f"    Original: {result['original_name'][:80]}...")
            print(f"    Extracted: {result['extracted_name']}")
            print(f"    URL: {result['url']}")
            if result['improvement']:
                print(f"    ✅ IMPROVEMENT: Much shorter and cleaner")
                improvements += 1
            else:
                print(f"    ❓ Needs review")
        
        print(f"\n📊 EXTRACTION TEST RESULTS:")
        print(f"  Records tested: {len(test_results)}")
        print(f"  Clear improvements: {improvements}")
        print(f"  Success rate: {improvements/len(test_results)*100:.1f}%" if test_results else "N/A")
        
        print(f"\n✅ Investigation complete. Ready for Phase 2 (Fix Scraper).")
        
    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()