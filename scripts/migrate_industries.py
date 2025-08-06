#!/usr/bin/env python3
"""
Industry Migration Script with Audit Trail
Safely migrates existing industry data to standardized categories
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import List, Dict

# Add project root to path and import with src prefix (like working scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.database.models import DatabaseOperations
from src.utils.industry_mapper import IndustryMapper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'industry_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IndustryMigrator:
    """Handles industry migration with audit trail and rollback capability"""
    
    def __init__(self, dry_run: bool = True):
        self.db_ops = DatabaseOperations()
        self.mapper = IndustryMapper()
        self.dry_run = dry_run
        self.migration_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_audit_table(self):
        """Create audit trail table if it doesn't exist"""
        try:
            with self.db_ops.db.get_cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS industry_migration_audit (
                        id SERIAL PRIMARY KEY,
                        migration_id VARCHAR(50) NOT NULL,
                        story_id INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT NOW(),
                        old_industry VARCHAR(255),
                        new_industry VARCHAR(100),
                        mapping_confidence FLOAT,
                        matched_terms JSONB,
                        migration_method VARCHAR(50),
                        rollback_completed BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (story_id) REFERENCES customer_stories(id)
                    )
                """)
                
                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_migration_audit_migration_id 
                    ON industry_migration_audit(migration_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_migration_audit_story_id 
                    ON industry_migration_audit(story_id)
                """)
                
            logger.info("Audit table created/verified successfully")
            
        except Exception as e:
            logger.error(f"Failed to create audit table: {e}")
            raise
    
    def backup_current_data(self) -> str:
        """Create a backup of current industry data"""
        backup_file = f"industry_backup_{self.migration_id}.json"
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, industry, customer_name, url
                    FROM customer_stories 
                    WHERE industry IS NOT NULL
                    ORDER BY id
                """)
                
                backup_data = {
                    'migration_id': self.migration_id,
                    'backup_timestamp': datetime.now().isoformat(),
                    'total_records': 0,
                    'records': []
                }
                
                for row in cursor.fetchall():
                    backup_data['records'].append({
                        'id': row['id'],
                        'industry': row['industry'],
                        'customer_name': row['customer_name'],
                        'url': row['url']
                    })
                
                backup_data['total_records'] = len(backup_data['records'])
                
                # Save backup file
                with open(backup_file, 'w') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                
                logger.info(f"Backup created: {backup_file} ({backup_data['total_records']} records)")
                return backup_file
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def get_migration_plan(self) -> Dict:
        """Analyze and create migration plan"""
        logger.info("Analyzing current industry data...")
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, industry, customer_name
                    FROM customer_stories 
                    WHERE industry IS NOT NULL
                    ORDER BY industry, id
                """)
                
                records = cursor.fetchall()
                
                migration_plan = {
                    'migration_id': self.migration_id,
                    'total_records': len(records),
                    'changes': [],
                    'stats': {
                        'no_change_needed': 0,
                        'will_be_updated': 0,
                        'low_confidence': 0
                    }
                }
                
                for record in records:
                    story_id = record['id']
                    current_industry = record['industry']
                    customer_name = record['customer_name']
                    
                    # Get mapping suggestion
                    mapping = self.mapper.suggest_mapping(current_industry)
                    new_industry = mapping['category']
                    
                    # Check if change is needed
                    current_standardized = current_industry.lower().replace(' ', '_').replace('-', '_')
                    
                    if current_standardized == new_industry:
                        migration_plan['stats']['no_change_needed'] += 1
                        continue
                    
                    change_record = {
                        'story_id': story_id,
                        'customer_name': customer_name,
                        'old_industry': current_industry,
                        'new_industry': new_industry,
                        'confidence': mapping['confidence'],
                        'matched_terms': mapping['matches']
                    }
                    
                    migration_plan['changes'].append(change_record)
                    migration_plan['stats']['will_be_updated'] += 1
                    
                    if mapping['confidence'] < 0.5:
                        migration_plan['stats']['low_confidence'] += 1
                
                return migration_plan
                
        except Exception as e:
            logger.error(f"Failed to create migration plan: {e}")
            raise
    
    def execute_migration(self, migration_plan: Dict, min_confidence: float = 0.3) -> Dict:
        """Execute the migration with audit trail"""
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
        
        results = {
            'migration_id': self.migration_id,
            'started_at': datetime.now().isoformat(),
            'total_planned': len(migration_plan['changes']),
            'successful_updates': 0,
            'skipped_low_confidence': 0,
            'errors': [],
            'completed_at': None
        }
        
        try:
            for change in migration_plan['changes']:
                story_id = change['story_id']
                old_industry = change['old_industry']
                new_industry = change['new_industry']
                confidence = change['confidence']
                matched_terms = change['matched_terms']
                
                # Skip low confidence mappings
                if confidence < min_confidence:
                    logger.warning(f"Skipping low confidence mapping for story {story_id}: "
                                 f"'{old_industry}' → '{new_industry}' (confidence: {confidence:.2f})")
                    results['skipped_low_confidence'] += 1
                    continue
                
                try:
                    if not self.dry_run:
                        with self.db_ops.db.get_cursor() as cursor:
                            # Update the story
                            cursor.execute("""
                                UPDATE customer_stories 
                                SET industry = %s 
                                WHERE id = %s
                            """, (new_industry, story_id))
                            
                            # Create audit record
                            cursor.execute("""
                                INSERT INTO industry_migration_audit 
                                (migration_id, story_id, old_industry, new_industry, 
                                 mapping_confidence, matched_terms, migration_method)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                self.migration_id, story_id, old_industry, new_industry,
                                confidence, json.dumps(matched_terms), 'regex_pattern_matching'
                            ))
                    
                    logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Updated story {story_id}: "
                              f"'{old_industry}' → '{new_industry}' (confidence: {confidence:.2f})")
                    
                    results['successful_updates'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to update story {story_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            results['completed_at'] = datetime.now().isoformat()
            logger.info(f"Migration completed: {results['successful_updates']} updates, "
                       f"{results['skipped_low_confidence']} skipped, {len(results['errors'])} errors")
            
            return results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            results['fatal_error'] = str(e)
            results['completed_at'] = datetime.now().isoformat()
            return results
    
    def rollback_migration(self, migration_id: str = None) -> Dict:
        """Rollback a migration using audit trail"""
        
        target_migration_id = migration_id or self.migration_id
        
        logger.info(f"Starting rollback for migration: {target_migration_id}")
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                # Get audit records for the migration
                cursor.execute("""
                    SELECT story_id, old_industry, new_industry
                    FROM industry_migration_audit 
                    WHERE migration_id = %s AND rollback_completed = FALSE
                    ORDER BY id
                """, (target_migration_id,))
                
                audit_records = cursor.fetchall()
                
                if not audit_records:
                    logger.warning(f"No audit records found for migration {target_migration_id}")
                    return {'error': 'No audit records found'}
                
                rollback_results = {
                    'migration_id': target_migration_id,
                    'rollback_started': datetime.now().isoformat(),
                    'total_records': len(audit_records),
                    'successful_rollbacks': 0,
                    'errors': []
                }
                
                for record in audit_records:
                    story_id = record['story_id']
                    original_industry = record['old_industry']
                    
                    try:
                        # Restore original industry
                        cursor.execute("""
                            UPDATE customer_stories 
                            SET industry = %s 
                            WHERE id = %s
                        """, (original_industry, story_id))
                        
                        # Mark audit record as rolled back
                        cursor.execute("""
                            UPDATE industry_migration_audit 
                            SET rollback_completed = TRUE 
                            WHERE migration_id = %s AND story_id = %s
                        """, (target_migration_id, story_id))
                        
                        rollback_results['successful_rollbacks'] += 1
                        logger.info(f"Rolled back story {story_id} to '{original_industry}'")
                        
                    except Exception as e:
                        error_msg = f"Failed to rollback story {story_id}: {e}"
                        logger.error(error_msg)
                        rollback_results['errors'].append(error_msg)
                
                rollback_results['completed_at'] = datetime.now().isoformat()
                logger.info(f"Rollback completed: {rollback_results['successful_rollbacks']} records restored")
                
                return rollback_results
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {'error': str(e)}


def main():
    """Command line interface for industry migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Industry Migration Tool with Audit Trail')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze current industries and create migration plan')
    parser.add_argument('--migrate', action='store_true',
                       help='Execute the migration')
    parser.add_argument('--rollback', type=str, metavar='MIGRATION_ID',
                       help='Rollback a specific migration')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Run in dry-run mode (default)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually execute changes (disables dry-run)')
    parser.add_argument('--min-confidence', type=float, default=0.3,
                       help='Minimum confidence threshold for mapping (default: 0.3)')
    parser.add_argument('--output', type=str, default='migration_plan.json',
                       help='Output file for migration plan')
    
    args = parser.parse_args()
    
    # Set dry run mode
    dry_run = not args.execute
    
    migrator = IndustryMigrator(dry_run=dry_run)
    
    try:
        # Create audit table
        migrator.create_audit_table()
        
        if args.rollback:
            # Rollback migration
            result = migrator.rollback_migration(args.rollback)
            print(json.dumps(result, indent=2, default=str))
            
        elif args.analyze:
            # Analyze and create migration plan
            plan = migrator.get_migration_plan()
            
            print(f"Migration Analysis Results:")
            print(f"=" * 50)
            print(f"Total records: {plan['total_records']}")
            print(f"No change needed: {plan['stats']['no_change_needed']}")
            print(f"Will be updated: {plan['stats']['will_be_updated']}")
            print(f"Low confidence: {plan['stats']['low_confidence']}")
            
            # Save plan to file
            with open(args.output, 'w') as f:
                json.dump(plan, f, indent=2, default=str)
            
            print(f"\nDetailed migration plan saved to: {args.output}")
            
            # Show sample changes
            if plan['changes']:
                print(f"\nSample changes (first 10):")
                for change in plan['changes'][:10]:
                    print(f"  '{change['old_industry']}' → '{change['new_industry']}' "
                          f"(confidence: {change['confidence']:.2f})")
            
        elif args.migrate:
            # Load migration plan
            try:
                with open(args.output, 'r') as f:
                    plan = json.load(f)
            except FileNotFoundError:
                print(f"Migration plan file not found: {args.output}")
                print("Run with --analyze first to create a migration plan")
                return
            
            # Create backup
            backup_file = migrator.backup_current_data()
            
            # Execute migration
            result = migrator.execute_migration(plan, args.min_confidence)
            
            print(f"Migration Results:")
            print(f"=" * 50)
            print(json.dumps(result, indent=2, default=str))
            
            # Save results
            result_file = f"migration_results_{migrator.migration_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\nResults saved to: {result_file}")
            print(f"Backup saved to: {backup_file}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Migration tool error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()