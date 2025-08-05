#!/usr/bin/env python3
"""
Enhanced GenAI Reclassification Utility

Uses the new 4-tier classification system to reclassify stories in the database.
This replaces the older classification utilities with improved accuracy.

Usage:
  python reclassify_genai_enhanced.py --provider google --limit 50 --dry-run
  python reclassify_genai_enhanced.py --all --apply-changes
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List
from src.classification.enhanced_classifier import EnhancedClassifier
from src.database.models import DatabaseOperations

class EnhancedReclassifier:
    def __init__(self, dry_run: bool = True):
        self.classifier = EnhancedClassifier()
        self.db_ops = DatabaseOperations()
        self.dry_run = dry_run
        
    def reclassify_stories(self, provider: str = None, limit: int = None, confidence_threshold: float = 0.8, log_all_changes: bool = True, use_claude: bool = False, claude_only: bool = False) -> Dict:
        """
        Reclassify stories using enhanced 4-tier system
        """
        print(f"🚀 Enhanced GenAI Reclassification")
        print(f"   Mode: {'DRY RUN' if self.dry_run else 'APPLYING CHANGES'}")
        print(f"   Provider: {provider or 'All'}")
        print(f"   Limit: {limit or 'No limit'}")
        print(f"   Confidence Threshold: {confidence_threshold}")
        print(f"   Claude API: {'Enabled' if use_claude else 'Disabled'}")
        print(f"   Claude Only: {'Yes' if claude_only else 'No'}")
        print("=" * 60)
        
        results = {
            'total_analyzed': 0,
            'classification_changes': [],
            'high_confidence_fixes': [],
            'needs_claude': [],
            'unchanged': [],
            'classification_breakdown': {
                'tier_1_definitive_genai': 0,
                'tier_2_definitive_traditional': 0,
                'tier_3_context_resolved': 0,
                'tier_4_needs_claude': 0,
                'claude_completed': 0
            },
            'accuracy_improvements': {
                'fixed_misclassifications': 0,
                'claude_avoidance': 0,
                'claude_api_calls': 0
            }
        }
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                # Build query
                query = """
                    SELECT id, customer_name, title, url, is_gen_ai, raw_content
                    FROM customer_stories 
                """
                params = []
                
                if provider:
                    if provider.lower() == 'google':
                        query += " WHERE url LIKE %s"
                        params.append('%cloud.google.com%')
                    elif provider.lower() == 'microsoft':
                        query += " WHERE url LIKE %s"
                        params.append('%microsoft.com%')
                    elif provider.lower() == 'aws':
                        query += " WHERE url LIKE %s"
                        params.append('%aws.amazon.com%')
                
                query += " ORDER BY id DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                stories = cursor.fetchall()
                
                print(f"📊 Found {len(stories)} stories to analyze\n")
                
                for i, story in enumerate(stories, 1):
                    print(f"🔍 Processing story {i}/{len(stories)}: ID {story['id']} - {story['customer_name'][:40]}...")
                    try:
                        self._process_story(story, results, confidence_threshold, use_claude, claude_only)
                        print(f"   ✅ Completed story {i}/{len(stories)}")
                    except Exception as e:
                        print(f"   ❌ Error processing story {i}: {e}")
                        logger.error(f"Error processing story ID {story['id']}: {e}")
                        # Continue processing other stories
                        continue
                
                # Apply changes if not dry run
                if not self.dry_run and results['classification_changes']:
                    self._apply_classification_changes(results['classification_changes'])
                    if log_all_changes:
                        self._log_classification_changes(results['classification_changes'])
                
        except Exception as e:
            print(f"❌ Error during reclassification: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def _process_story(self, story: Dict, results: Dict, confidence_threshold: float, use_claude: bool = False, claude_only: bool = False):
        """Process individual story classification"""
        results['total_analyzed'] += 1
        
        # Get raw content
        raw_content = story.get('raw_content', {}) or {}
        raw_text = raw_content.get('text', '') if isinstance(raw_content, dict) else ''
        
        # Current classification
        current_is_genai = story['is_gen_ai']
        current_classification = 'GenAI' if current_is_genai else 'Traditional'
        
        # First check if we should skip this story for claude_only mode
        if claude_only:
            # Quick check to see if this story needs Claude
            quick_analysis = self.classifier.classify_story(
                story['id'],
                story['title'] or '',
                story['url'],
                story['customer_name'],
                raw_text
            )
            if not quick_analysis['requires_claude']:
                # Skip stories that don't need Claude in claude_only mode
                results['total_analyzed'] -= 1  # Don't count skipped stories
                return
        
        # New classification using enhanced system
        if use_claude:
            # Use Claude fallback for stories that need it
            analysis = self.classifier.classify_with_claude_fallback(
                story['id'],
                story['title'] or '',
                story['url'],
                story['customer_name'],
                raw_content
            )
        else:
            # Use rule-based classification only
            analysis = self.classifier.classify_story(
                story['id'],
                story['title'] or '',
                story['url'],
                story['customer_name'],
                raw_text
            )
        
        # Track classification method
        method = analysis['method']
        if method.startswith('tier_1'):
            results['classification_breakdown']['tier_1_definitive_genai'] += 1
        elif method.startswith('tier_2'):
            results['classification_breakdown']['tier_2_definitive_traditional'] += 1
        elif method.startswith('tier_3'):
            results['classification_breakdown']['tier_3_context_resolved'] += 1
        else:
            results['classification_breakdown']['tier_4_needs_claude'] += 1
        
        # Determine if classification should change
        new_is_genai = analysis['recommendation'] == 'GenAI'
        new_classification = analysis['recommendation']
        confidence = analysis['confidence']
        
        # Check if change is needed and meets confidence threshold
        classification_changed = current_is_genai != new_is_genai
        high_confidence = confidence >= confidence_threshold
        
        if analysis['requires_claude']:
            # Story needs Claude analysis
            results['needs_claude'].append({
                'story_id': story['id'],
                'customer': story['customer_name'][:50],
                'current': current_classification,
                'method': method,
                'reasoning': analysis['reasoning']
            })
            results['accuracy_improvements']['claude_avoidance'] -= 1  # Count as requiring Claude
        
        # Track Claude API usage
        if 'claude' in method.lower():
            results['accuracy_improvements']['claude_api_calls'] += 1
            results['classification_breakdown']['claude_completed'] += 1
            
        elif classification_changed and high_confidence:
            # High confidence classification change
            change_info = {
                'story_id': story['id'],
                'customer': story['customer_name'][:50],
                'current_classification': current_classification,
                'new_classification': new_classification,
                'confidence': confidence,
                'method': method,
                'evidence': analysis['evidence'][:3],
                'reasoning': analysis['reasoning']
            }
            
            results['classification_changes'].append(change_info)
            results['high_confidence_fixes'].append(change_info)
            results['accuracy_improvements']['fixed_misclassifications'] += 1
            
            print(f"🔧 ID {story['id']}: {story['customer_name'][:40]}...")
            print(f"   {current_classification} → {new_classification} (confidence: {confidence:.2f})")
            print(f"   Method: {method}")
            print(f"   Evidence: {analysis['evidence'][:2]}")
            print()
            
        elif classification_changed and not high_confidence:
            # Low confidence change - flag for review
            print(f"⚠️  ID {story['id']}: {story['customer_name'][:40]}... (LOW CONFIDENCE)")
            print(f"   {current_classification} → {new_classification} (confidence: {confidence:.2f})")
            print(f"   Method: {method} - Consider manual review")
            print()
            
        else:
            # No change needed
            results['unchanged'].append({
                'story_id': story['id'],
                'classification': current_classification,
                'confirmed_by': method,
                'confidence': confidence
            })
            results['accuracy_improvements']['claude_avoidance'] += 1  # Avoided Claude call
    
    def _apply_classification_changes(self, changes: List[Dict]):
        """Apply classification changes to database"""
        print(f"💾 Applying {len(changes)} classification changes...")
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                for change in changes:
                    new_is_genai = change['new_classification'] == 'GenAI'
                    
                    cursor.execute("""
                        UPDATE customer_stories 
                        SET is_gen_ai = %s,
                            last_updated = NOW()
                        WHERE id = %s
                    """, (new_is_genai, change['story_id']))
                
                cursor.connection.commit()
                print(f"✅ Successfully applied {len(changes)} changes to database")
                
        except Exception as e:
            print(f"❌ Error applying changes: {e}")
            raise
    
    def _log_classification_changes(self, changes: List[Dict]):
        """Log detailed audit trail of classification changes"""
        if not changes:
            return
            
        from datetime import datetime
        import json
        
        log_file = f"classification_changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        audit_log = {
            'timestamp': datetime.now().isoformat(),
            'total_changes': len(changes),
            'changes': []
        }
        
        for change in changes:
            audit_entry = {
                'story_id': change['story_id'],
                'customer': change['customer'],
                'old_classification': change['current_classification'],
                'new_classification': change['new_classification'],
                'confidence': change['confidence'],
                'method': change['method'],
                'evidence': change['evidence'],
                'reasoning': change['reasoning'],
                'change_timestamp': datetime.now().isoformat()
            }
            audit_log['changes'].append(audit_entry)
        
        try:
            with open(log_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
            print(f"📝 Audit log saved to {log_file}")
        except Exception as e:
            print(f"⚠️ Could not save audit log: {e}")
    
    def _create_classification_summary(self, results: Dict) -> str:
        """Create a summary comment for database audit trail"""
        total = results['total_analyzed']
        changes = len(results['classification_changes'])
        claude_needed = len(results['needs_claude'])
        
        breakdown = results.get('classification_breakdown', {})
        tier1 = breakdown.get('tier_1_definitive_genai', 0)
        tier2 = breakdown.get('tier_2_definitive_traditional', 0)
        tier3 = breakdown.get('tier_3_context_resolved', 0)
        tier4 = breakdown.get('tier_4_needs_claude', 0)
        
        summary = f"Enhanced classification: {changes}/{total} changes. "
        summary += f"T1:{tier1} T2:{tier2} T3:{tier3} T4:{tier4}. "
        summary += f"Claude avoidance: {((total-tier4)/total*100):.1f}%"
        
        return summary
    
    def print_summary(self, results: Dict):
        """Print comprehensive summary of reclassification results"""
        print(f"\n📋 RECLASSIFICATION SUMMARY")
        print("=" * 50)
        
        print(f"Total stories analyzed: {results['total_analyzed']}")
        print(f"Classification changes needed: {len(results['classification_changes'])}")
        print(f"Stories needing Claude: {len(results['needs_claude'])}")
        print(f"Stories unchanged: {len(results['unchanged'])}")
        
        print(f"\n🎯 CLASSIFICATION BREAKDOWN:")
        breakdown = results['classification_breakdown']
        total = results['total_analyzed']
        if total > 0:
            print(f"  Tier 1 (Definitive GenAI): {breakdown['tier_1_definitive_genai']} ({breakdown['tier_1_definitive_genai']/total:.1%})")
            print(f"  Tier 2 (Definitive Traditional): {breakdown['tier_2_definitive_traditional']} ({breakdown['tier_2_definitive_traditional']/total:.1%})")
            print(f"  Tier 3 (Context Resolved): {breakdown['tier_3_context_resolved']} ({breakdown['tier_3_context_resolved']/total:.1%})")
            print(f"  Tier 4 (Needs Claude): {breakdown['tier_4_needs_claude']} ({breakdown['tier_4_needs_claude']/total:.1%})")
        
        print(f"\n💡 EFFICIENCY METRICS:")
        claude_avoidance_rate = (total - breakdown['tier_4_needs_claude']) / total if total > 0 else 0
        claude_api_calls = results['accuracy_improvements']['claude_api_calls']
        print(f"  Claude avoidance rate: {claude_avoidance_rate:.1%}")
        print(f"  Claude API calls made: {claude_api_calls}")
        print(f"  Misclassifications fixed: {results['accuracy_improvements']['fixed_misclassifications']}")
        
        if results['high_confidence_fixes']:
            print(f"\n🔧 TOP HIGH-CONFIDENCE FIXES:")
            for fix in results['high_confidence_fixes'][:5]:
                print(f"  ID {fix['story_id']}: {fix['current_classification']} → {fix['new_classification']} ({fix['confidence']:.2f})")
        
        if results['needs_claude']:
            print(f"\n🤖 STORIES NEEDING CLAUDE ANALYSIS ({len(results['needs_claude'])}):")
            for story in results['needs_claude'][:3]:
                print(f"  ID {story['story_id']}: {story['customer']}... (Current: {story['current']})")
        
        if self.dry_run:
            print(f"\n⚠️  DRY RUN MODE - No changes applied to database")
            print(f"   Run with --apply-changes to execute modifications")

def main():
    parser = argparse.ArgumentParser(description='Enhanced GenAI Reclassification Utility')
    parser.add_argument('--provider', choices=['google', 'microsoft', 'aws', 'all'], 
                       help='Cloud provider to focus on')
    parser.add_argument('--limit', type=int, help='Limit number of stories to process')
    parser.add_argument('--confidence-threshold', type=float, default=0.8,
                       help='Minimum confidence for auto-applying changes (default: 0.8)')
    parser.add_argument('--apply-changes', action='store_true',
                       help='Apply changes to database (default: dry run)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Run in dry run mode (default)')
    parser.add_argument('--use-claude', action='store_true',
                       help='Use Claude API for stories that need deeper analysis')
    parser.add_argument('--claude-only', action='store_true',
                       help='Only process stories that need Claude analysis')
    
    args = parser.parse_args()
    
    # Override dry_run if apply_changes is specified
    dry_run = not args.apply_changes
    
    # Create reclassifier
    reclassifier = EnhancedReclassifier(dry_run=dry_run)
    
    # Run reclassification
    results = reclassifier.reclassify_stories(
        provider=args.provider,
        limit=args.limit,
        confidence_threshold=args.confidence_threshold,
        use_claude=args.use_claude,
        claude_only=args.claude_only
    )
    
    # Print summary
    reclassifier.print_summary(results)

if __name__ == "__main__":
    main()