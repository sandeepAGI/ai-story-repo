#!/usr/bin/env python3
"""
GoogleCloud Customer Name Fix Script
Phase 3: Database cleanup for existing problematic records
"""

import sys
import os
import re
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.models import DatabaseOperations

class GoogleCloudNameFixer:
    def __init__(self, dry_run: bool = True):
        self.db_ops = DatabaseOperations()
        self.dry_run = dry_run
        self.changes_made = []
        
    def find_problematic_records(self) -> List[Dict[str, Any]]:
        """Find all GoogleCloud records that need fixing"""
        
        with self.db_ops.db.get_cursor() as cursor:
            # Get GoogleCloud source ID
            cursor.execute("SELECT id FROM sources WHERE name = 'Google Cloud'")
            source_result = cursor.fetchone()
            
            if not source_result:
                raise Exception("Google Cloud source not found in database")
            
            source_id = source_result['id']
            
            # Find problematic records
            cursor.execute("""
                SELECT id, customer_name, url, title, scraped_date
                FROM customer_stories 
                WHERE source_id = %s
                AND (
                    customer_name LIKE %s
                    OR customer_name LIKE %s
                    OR (
                        LENGTH(customer_name) > 50 
                        AND customer_name LIKE %s
                    )
                )
                ORDER BY scraped_date DESC
            """, (
                source_id,
                'https://cloud.google.com/blog/%',
                'Https://Cloud.Google.Com/Blog/%', 
                '%Cloud.Google.Com%'
            ))
            
            return cursor.fetchall()
    
    def extract_company_from_title(self, title: str) -> Optional[str]:
        """Extract company name from blog post title using same logic as scraper"""
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
                company = self.clean_company_name(company)
                
                # Validate it's a reasonable company name
                if self.is_valid_company_name(company):
                    return company
        
        return None
    
    def extract_company_from_blog_url(self, url: str) -> Optional[str]:
        """Extract company name from blog URL path using same logic as scraper"""
        
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
                company = self.clean_company_name(company)
                
                # Validate it's a reasonable company name
                if self.is_valid_company_name(company):
                    return company
        
        return None
    
    def clean_company_name(self, company: str) -> str:
        """Clean and normalize company name using same logic as scraper"""
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
        elif company.lower() == 'bayer is':
            return 'Bayer'  # Fix extraction issue
        elif company.lower() == 'snap inc':
            return 'Snap Inc.'
        elif company.startswith('Consumer goods company '):
            return company.replace('Consumer goods company ', '')
        
        return company
    
    def is_valid_company_name(self, company: str) -> bool:
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
        
        # Don't accept obvious non-company patterns
        if (company_lower.startswith('google cloud') or 
            company_lower.startswith('reimagining') or
            company_lower.startswith('devops') or
            'winner' in company_lower):
            return False
            
        # Don't accept if it's too long (probably extracted too much text)
        if len(company) > 50:
            return False
        
        # Must start with a capital letter or number
        if not company[0].isupper() and not company[0].isdigit():
            return False
            
        return True
    
    def extract_fixed_name(self, record: Dict[str, Any]) -> Optional[str]:
        """Extract corrected customer name for a problematic record"""
        
        url = record['url']
        title = record.get('title', '')
        
        # Strategy 1: Extract from title first (most reliable for blog posts)
        if title:
            extracted_name = self.extract_company_from_title(title)
            if extracted_name:
                return extracted_name
        
        # Strategy 2: Extract from URL patterns
        extracted_name = self.extract_company_from_blog_url(url)
        if extracted_name:
            return extracted_name
        
        return None
    
    def preview_changes(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preview what changes would be made without executing them"""
        
        changes = []
        
        for record in records:
            original_name = record['customer_name']
            fixed_name = self.extract_fixed_name(record)
            
            if fixed_name and fixed_name != original_name:
                changes.append({
                    'id': record['id'],
                    'url': record['url'],
                    'title': record.get('title', ''),
                    'original_name': original_name,
                    'fixed_name': fixed_name,
                    'improvement_score': self.calculate_improvement_score(original_name, fixed_name)
                })
        
        return changes
    
    def calculate_improvement_score(self, original: str, fixed: str) -> float:
        """Calculate a score representing how much better the fixed name is"""
        if not fixed:
            return 0.0
        
        # Length improvement (shorter is usually better)
        length_improvement = max(0, (len(original) - len(fixed)) / len(original))
        
        # URL-like original gets high improvement score
        url_improvement = 1.0 if original.startswith('http') else 0.0
        
        # Valid company name gets bonus
        validity_score = 1.0 if self.is_valid_company_name(fixed) else 0.0
        
        return (length_improvement * 0.3) + (url_improvement * 0.5) + (validity_score * 0.2)
    
    def execute_changes(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the database updates"""
        
        if self.dry_run:
            return {
                "status": "dry_run",
                "would_update": len(changes),
                "changes": changes
            }
        
        updated_count = 0
        errors = []
        
        with self.db_ops.db.get_cursor() as cursor:
            for change in changes:
                try:
                    cursor.execute("""
                        UPDATE customer_stories 
                        SET customer_name = %s 
                        WHERE id = %s
                    """, (change['fixed_name'], change['id']))
                    
                    updated_count += 1
                    self.changes_made.append(change)
                    
                except Exception as e:
                    error_msg = f"Failed to update record {change['id']}: {str(e)}"
                    errors.append(error_msg)
        
        return {
            "status": "completed",
            "updated_count": updated_count,
            "errors": errors,
            "changes_made": self.changes_made
        }
    
    def create_backup(self, records: List[Dict[str, Any]]) -> str:
        """Create a backup of the records before changing them"""
        
        backup_data = {
            "backup_timestamp": str(datetime.now()),
            "records_count": len(records),
            "records": records
        }
        
        backup_filename = f"googlecloud_names_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json" 
        
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        return backup_filename

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix GoogleCloud customer names in database")
    parser.add_argument('--execute', action='store_true', help='Actually execute changes (default is dry-run)')
    parser.add_argument('--backup', action='store_true', help='Create backup before changes')
    
    args = parser.parse_args()
    
    print("🔧 GoogleCloud Customer Name Fix Script")
    print("=" * 50)
    
    # Initialize fixer
    fixer = GoogleCloudNameFixer(dry_run=not args.execute)
    
    try:
        # Step 1: Find problematic records
        print("\n📊 Finding problematic records...")
        problematic_records = fixer.find_problematic_records()
        
        if not problematic_records:
            print("✅ No problematic records found!")
            return
        
        print(f"Found {len(problematic_records)} problematic records")
        
        # Step 2: Preview changes
        print("\n🔍 Analyzing potential fixes...")
        changes = fixer.preview_changes(problematic_records)
        
        if not changes:
            print("❌ No valid fixes could be generated")
            return
        
        print(f"Generated {len(changes)} potential fixes")
        
        # Step 3: Show preview
        print(f"\n📋 PREVIEW OF CHANGES:")
        print(f"{'ID':<6} {'Score':<7} {'Original → Fixed'}")
        print("-" * 80)
        
        for change in sorted(changes, key=lambda x: x['improvement_score'], reverse=True):
            score_str = f"{change['improvement_score']:.2f}"
            original_preview = change['original_name'][:30] + "..." if len(change['original_name']) > 30 else change['original_name']
            print(f"{change['id']:<6} {score_str:<7} {original_preview} → {change['fixed_name']}")
        
        # Step 4: Show sample changes in detail
        print(f"\n🔍 DETAILED PREVIEW (Top 5 changes):")
        for i, change in enumerate(changes[:5], 1):
            print(f"\n{i}. Record ID: {change['id']} (Score: {change['improvement_score']:.2f})")
            print(f"   URL: {change['url']}")
            print(f"   Title: {change['title'][:100]}...")
            print(f"   Original: {change['original_name'][:100]}...")
            print(f"   Fixed:    {change['fixed_name']}")
        
        # Step 5: Execute or show dry-run results
        if args.execute:
            print(f"\n⚠️  EXECUTING CHANGES...")
            
            # Create backup if requested
            if args.backup:
                print("📦 Creating backup...")
                backup_file = fixer.create_backup(problematic_records)
                print(f"✅ Backup created: {backup_file}")
            
            # Execute changes
            result = fixer.execute_changes(changes)
            
            print(f"\n✅ CHANGES EXECUTED:")
            print(f"   Updated records: {result['updated_count']}")
            print(f"   Errors: {len(result.get('errors', []))}")
            
            if result.get('errors'):
                print(f"\n❌ ERRORS:")
                for error in result['errors']:
                    print(f"   • {error}")
        
        else:
            print(f"\n🧪 DRY RUN MODE - No changes made")
            print(f"   Would update: {len(changes)} records")
            print(f"   To execute changes, run with --execute flag")
            print(f"   To create backup, add --backup flag")
        
        print(f"\n✅ Operation completed successfully")
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()