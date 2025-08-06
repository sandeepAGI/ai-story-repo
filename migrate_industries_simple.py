#!/usr/bin/env python3
"""
Simple Industry Migration Script
Follows the existing codebase pattern for database updates
"""

import json
import logging
from datetime import datetime
from typing import Dict, List
from src.database.models import DatabaseOperations
from src.utils.industry_mapper import IndustryMapper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleIndustryMigrator:
    """Simple industry migration following existing codebase patterns"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.mapper = IndustryMapper()
    
    def analyze_current_industries(self) -> Dict:
        """Analyze current industry distribution"""
        print("📊 Analyzing current industry distribution...")
        
        with self.db_ops.db.get_cursor() as cursor:
            # Get industry distribution
            cursor.execute("""
                SELECT industry, COUNT(*) as count 
                FROM customer_stories 
                WHERE industry IS NOT NULL 
                GROUP BY industry 
                ORDER BY count DESC
            """)
            
            industries = cursor.fetchall()
            
            print(f"Found {len(industries)} unique industries:")
            print(f"Total stories with industries: {sum(row['count'] for row in industries)}")
            
            # Show top 20
            print("\nTop 20 industries:")
            for i, row in enumerate(industries[:20], 1):
                print(f"  {i:2d}. {row['count']:3d} stories - {row['industry']}")
            
            if len(industries) > 20:
                print(f"  ... and {len(industries) - 20} more industries")
            
            return industries
    
    def create_mapping_plan(self, industries: List[Dict]) -> Dict:
        """Create mapping plan using industry mapper"""
        print("\n🗺️  Creating mapping plan...")
        
        mapping_plan = {
            'total_industries': len(industries),
            'mappings': [],
            'category_distribution': {}
        }
        
        for industry_row in industries:
            industry = industry_row['industry']
            count = industry_row['count']
            
            # Get mapping suggestion
            mapping = self.mapper.suggest_mapping(industry)
            mapped_category = mapping['category']
            confidence = mapping['confidence']
            
            mapping_info = {
                'original': industry,
                'mapped': mapped_category,
                'confidence': confidence,
                'story_count': count,
                'needs_change': industry.lower().replace(' ', '_').replace('-', '_') != mapped_category
            }
            
            mapping_plan['mappings'].append(mapping_info)
            
            # Update category distribution
            if mapped_category not in mapping_plan['category_distribution']:
                mapping_plan['category_distribution'][mapped_category] = 0
            mapping_plan['category_distribution'][mapped_category] += count
        
        # Show mapping summary
        changes_needed = sum(1 for m in mapping_plan['mappings'] if m['needs_change'])
        print(f"Industries needing changes: {changes_needed}/{len(industries)}")
        
        print(f"\nProposed category distribution:")
        for category, count in sorted(mapping_plan['category_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count} stories")
        
        return mapping_plan
    
    def show_mapping_details(self, mapping_plan: Dict, limit: int = 20):
        """Show detailed mapping information"""
        print(f"\n📋 Mapping Details (showing first {limit}):")
        
        changes = [m for m in mapping_plan['mappings'] if m['needs_change']]
        
        for i, mapping in enumerate(changes[:limit], 1):
            confidence_icon = "🔹" if mapping['confidence'] >= 0.7 else "🔸" if mapping['confidence'] >= 0.4 else "🔻"
            print(f"  {i:2d}. {confidence_icon} '{mapping['original']}' → {mapping['mapped']}")
            print(f"      {mapping['story_count']} stories, confidence: {mapping['confidence']:.2f}")
        
        if len(changes) > limit:
            print(f"  ... and {len(changes) - limit} more changes")
    
    def execute_migration(self, mapping_plan: Dict, dry_run: bool = True, min_confidence: float = 0.3):
        """Execute the industry migration"""
        
        mode_text = "DRY RUN" if dry_run else "EXECUTING"
        print(f"\n🚀 {mode_text} - Industry Migration")
        
        changes_to_apply = [
            m for m in mapping_plan['mappings'] 
            if m['needs_change'] and m['confidence'] >= min_confidence
        ]
        
        if not changes_to_apply:
            print("No changes to apply!")
            return {'updated': 0, 'skipped': 0}
        
        print(f"Will update {len(changes_to_apply)} industry mappings (min confidence: {min_confidence})")
        
        results = {'updated': 0, 'skipped': 0, 'errors': []}
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                for mapping in changes_to_apply:
                    original = mapping['original']
                    new_industry = mapping['mapped']
                    confidence = mapping['confidence']
                    story_count = mapping['story_count']
                    
                    try:
                        if not dry_run:
                            # Update stories with this industry
                            cursor.execute("""
                                UPDATE customer_stories 
                                SET industry = %s 
                                WHERE industry = %s
                            """, (new_industry, original))
                            
                            affected_rows = cursor.rowcount
                            
                            if affected_rows != story_count:
                                logger.warning(f"Expected {story_count} updates for '{original}', got {affected_rows}")
                        
                        results['updated'] += story_count
                        
                        # Log the change
                        status = "[DRY RUN]" if dry_run else "✅"
                        print(f"  {status} '{original}' → '{new_industry}' ({story_count} stories, conf: {confidence:.2f})")
                        
                    except Exception as e:
                        error_msg = f"Failed to update '{original}': {e}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                
                # Commit changes if not dry run
                if not dry_run:
                    cursor.connection.commit()
                    print(f"\n✅ Migration completed: {results['updated']} stories updated")
                else:
                    print(f"\n📋 Dry run completed: {results['updated']} stories would be updated")
        
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            results['errors'].append(str(e))
        
        return results


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Industry Migration Tool')
    parser.add_argument('--analyze', action='store_true', 
                       help='Analyze current industries')
    parser.add_argument('--plan', action='store_true',
                       help='Create migration plan')
    parser.add_argument('--migrate', action='store_true',
                       help='Execute migration (dry run by default)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually execute changes (not dry run)')
    parser.add_argument('--min-confidence', type=float, default=0.3,
                       help='Minimum confidence threshold (default: 0.3)')
    
    args = parser.parse_args()
    
    migrator = SimpleIndustryMigrator()
    
    try:
        if args.analyze or args.plan or args.migrate:
            # Step 1: Analyze current industries
            industries = migrator.analyze_current_industries()
            
            if args.plan or args.migrate:
                # Step 2: Create mapping plan
                mapping_plan = migrator.create_mapping_plan(industries)
                migrator.show_mapping_details(mapping_plan)
                
                if args.migrate:
                    # Step 3: Execute migration
                    dry_run = not args.execute
                    results = migrator.execute_migration(
                        mapping_plan, 
                        dry_run=dry_run, 
                        min_confidence=args.min_confidence
                    )
                    
                    if results['errors']:
                        print(f"\n❌ Errors encountered:")
                        for error in results['errors']:
                            print(f"  {error}")
        else:
            parser.print_help()
            print(f"\nExample usage:")
            print(f"  python3 migrate_industries_simple.py --analyze")
            print(f"  python3 migrate_industries_simple.py --plan")
            print(f"  python3 migrate_industries_simple.py --migrate")
            print(f"  python3 migrate_industries_simple.py --migrate --execute")
    
    except Exception as e:
        logger.error(f"Script failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()