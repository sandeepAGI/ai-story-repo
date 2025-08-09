#!/usr/bin/env python3
"""
Consolidated Maintenance Tools
Unified interface for all classification fixes and maintenance operations
"""

import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import DatabaseOperations

class MaintenanceTools:
    """Unified maintenance tools for classification fixes and data consistency"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        
        # Definitive GenAI indicators
        self.definitive_genai_indicators = {
            'modern_platforms': [
                'vertex ai', 'vertex-ai', 'vertexai',
                'gemini', 'bard', 'palm', 'pathways',
                'chatgpt', 'gpt-4', 'claude', 'llama'
            ],
            'genai_technologies': [
                'large language model', 'llm', 'foundation model', 
                'transformer model', 'generative ai', 'gen ai', 'genai'
            ],
            'genai_capabilities': [
                'conversational ai', 'chatbot', 'virtual assistant',
                'content generation', 'text generation', 'code generation',
                'natural language generation', 'dialogue system'
            ]
        }
    
    def fix_classification_consistency(self, story_ids=None, dry_run=True):
        """
        Fix is_gen_ai field consistency with ai_type classification
        
        Args:
            story_ids: List of specific story IDs to fix, or None for all
            dry_run: If True, only show what would be changed without making changes
        """
        if story_ids is None:
            story_ids = [1001, 978, 977, 302]  # Default problematic stories
        
        with self.db_ops.db.get_cursor() as cursor:
            print("🔧 CHECKING is_gen_ai FIELD CONSISTENCY WITH AI_TYPE")
            print("="*60)
            
            changes_made = 0
            
            for story_id in story_ids:
                cursor.execute("""
                    SELECT id, customer_name, is_gen_ai, extracted_data->>'ai_type' as ai_type
                    FROM customer_stories 
                    WHERE id = %s
                """, [story_id])
                story = cursor.fetchone()
                
                if story:
                    print(f"📝 Story ID {story['id']}: {story['customer_name']}")
                    print(f"   Current is_gen_ai: {story['is_gen_ai']}")
                    print(f"   Current ai_type: {story['ai_type']}")
                    
                    needs_fix = False
                    new_value = None
                    
                    if story['ai_type'] == 'traditional' and story['is_gen_ai'] == True:
                        needs_fix = True
                        new_value = False
                        print(f"   ⚠️  Inconsistency: Traditional AI marked as GenAI")
                        
                    elif story['ai_type'] == 'generative' and story['is_gen_ai'] == False:
                        needs_fix = True
                        new_value = True
                        print(f"   ⚠️  Inconsistency: GenAI marked as Traditional")
                    
                    if needs_fix:
                        if not dry_run:
                            cursor.execute("""
                                UPDATE customer_stories 
                                SET is_gen_ai = %s
                                WHERE id = %s
                            """, [new_value, story_id])
                            print(f"   ✅ Updated: is_gen_ai = {new_value}")
                            changes_made += 1
                        else:
                            print(f"   🔍 Would update: is_gen_ai = {new_value}")
                    else:
                        print(f"   ✅ Consistent")
                    
                    print()
            
            if not dry_run and changes_made > 0:
                print(f"✅ Fixed {changes_made} inconsistencies")
            elif dry_run:
                print("🔍 Dry run complete. Use dry_run=False to apply changes.")
                
    def fix_google_cloud_classifications(self, dry_run=True):
        """Fix Google Cloud story classifications using enhanced logic"""
        
        with self.db_ops.db.get_cursor() as cursor:
            print("🔧 FIXING GOOGLE CLOUD CLASSIFICATIONS")
            print("="*50)
            
            # Get Google Cloud stories that need classification
            cursor.execute("""
                SELECT id, customer_name, content, extracted_data 
                FROM customer_stories 
                WHERE source = 'Google Cloud' 
                AND (extracted_data->>'ai_type' IS NULL 
                     OR extracted_data->>'ai_type' = '')
                ORDER BY id
            """)
            
            stories = cursor.fetchall()
            print(f"Found {len(stories)} Google Cloud stories needing classification")
            
            changes_made = 0
            
            for story in stories:
                story_id = story['id']
                customer_name = story['customer_name']
                content = story['content'].lower() if story['content'] else ""
                
                print(f"\n📝 Story {story_id}: {customer_name}")
                
                # Check for definitive GenAI indicators
                is_genai = self._contains_genai_indicators(content)
                ai_type = 'generative' if is_genai else 'traditional'
                
                print(f"   Classification: {ai_type.upper()}")
                
                if not dry_run:
                    # Update the story
                    extracted_data = story['extracted_data'] or {}
                    extracted_data['ai_type'] = ai_type
                    
                    cursor.execute("""
                        UPDATE customer_stories 
                        SET is_gen_ai = %s, extracted_data = %s
                        WHERE id = %s
                    """, [is_genai, json.dumps(extracted_data), story_id])
                    
                    changes_made += 1
                    print(f"   ✅ Updated")
                else:
                    print(f"   🔍 Would classify as: {ai_type}")
            
            if not dry_run and changes_made > 0:
                print(f"\n✅ Updated {changes_made} Google Cloud stories")
            elif dry_run:
                print("\n🔍 Dry run complete. Use dry_run=False to apply changes.")
    
    def fix_customer_names(self, source="Google Cloud", dry_run=True):
        """Fix customer names with special characters or formatting issues"""
        
        with self.db_ops.db.get_cursor() as cursor:
            print(f"🔧 FIXING CUSTOMER NAMES FOR {source.upper()}")
            print("="*50)
            
            # Get stories with potential name issues
            cursor.execute("""
                SELECT id, customer_name, content
                FROM customer_stories 
                WHERE source = %s 
                AND (customer_name LIKE '%:%' 
                     OR customer_name LIKE '%|%'
                     OR customer_name LIKE '%-%'
                     OR customer_name ~ '[^\x00-\x7F]')
                ORDER BY id
            """, [source])
            
            stories = cursor.fetchall()
            print(f"Found {len(stories)} stories with potential name issues")
            
            changes_made = 0
            
            for story in stories:
                story_id = story['id']
                original_name = story['customer_name']
                
                # Clean up the customer name
                cleaned_name = self._clean_customer_name(original_name)
                
                if cleaned_name != original_name:
                    print(f"\n📝 Story {story_id}:")
                    print(f"   Original: {original_name}")
                    print(f"   Cleaned:  {cleaned_name}")
                    
                    if not dry_run:
                        cursor.execute("""
                            UPDATE customer_stories 
                            SET customer_name = %s
                            WHERE id = %s
                        """, [cleaned_name, story_id])
                        
                        changes_made += 1
                        print(f"   ✅ Updated")
                    else:
                        print(f"   🔍 Would update")
            
            if not dry_run and changes_made > 0:
                print(f"\n✅ Updated {changes_made} customer names")
            elif dry_run:
                print("\n🔍 Dry run complete. Use dry_run=False to apply changes.")
    
    def fix_business_outcomes_filtering(self, dry_run=True):
        """Fix business outcomes that may have filtering issues"""
        
        with self.db_ops.db.get_cursor() as cursor:
            print("🔧 FIXING BUSINESS OUTCOMES FILTERING")
            print("="*40)
            
            # Get stories with potential business outcome issues
            cursor.execute("""
                SELECT id, customer_name, extracted_data->>'business_outcomes' as outcomes
                FROM customer_stories 
                WHERE extracted_data->>'business_outcomes' IS NOT NULL
                AND (extracted_data->>'business_outcomes' LIKE '%null%'
                     OR extracted_data->>'business_outcomes' LIKE '%undefined%'
                     OR extracted_data->>'business_outcomes' = '[]')
                ORDER BY id
            """)
            
            stories = cursor.fetchall()
            print(f"Found {len(stories)} stories with potential outcome issues")
            
            changes_made = 0
            
            for story in stories:
                story_id = story['id']
                customer_name = story['customer_name']
                current_outcomes = story['outcomes']
                
                print(f"\n📝 Story {story_id}: {customer_name}")
                print(f"   Current outcomes: {current_outcomes}")
                
                # Fix the outcomes
                if current_outcomes in ['null', 'undefined', '[]', None]:
                    if not dry_run:
                        cursor.execute("""
                            UPDATE customer_stories 
                            SET extracted_data = jsonb_set(
                                extracted_data, 
                                '{business_outcomes}', 
                                '["Operational Efficiency"]'
                            )
                            WHERE id = %s
                        """, [story_id])
                        
                        changes_made += 1
                        print(f"   ✅ Set default: Operational Efficiency")
                    else:
                        print(f"   🔍 Would set default: Operational Efficiency")
            
            if not dry_run and changes_made > 0:
                print(f"\n✅ Updated {changes_made} business outcomes")
            elif dry_run:
                print("\n🔍 Dry run complete. Use dry_run=False to apply changes.")
    
    def _contains_genai_indicators(self, content: str) -> bool:
        """Check if content contains definitive GenAI indicators"""
        content_lower = content.lower()
        
        for category, indicators in self.definitive_genai_indicators.items():
            for indicator in indicators:
                if indicator in content_lower:
                    return True
        return False
    
    def _clean_customer_name(self, name: str) -> str:
        """Clean customer name of special characters and formatting issues"""
        if not name:
            return name
            
        # Remove common separators and extra text
        cleaned = re.sub(r'^[^a-zA-Z0-9]*', '', name)  # Remove leading non-alphanumeric
        cleaned = re.sub(r'[:|].*$', '', cleaned)      # Remove everything after : or |
        cleaned = re.sub(r'\s*-\s*.*$', '', cleaned)   # Remove everything after -
        cleaned = cleaned.strip()
        
        # Handle special cases
        if not cleaned:
            cleaned = "Unknown Customer"
            
        return cleaned

def main():
    """Main CLI interface"""
    tools = MaintenanceTools()
    
    print("🔧 CONSOLIDATED MAINTENANCE TOOLS")
    print("="*40)
    print("1. Fix classification consistency")
    print("2. Fix Google Cloud classifications") 
    print("3. Fix customer names")
    print("4. Fix business outcomes filtering")
    print("5. Run all fixes")
    print()
    
    choice = input("Select option (1-5): ").strip()
    dry_run = input("Dry run? (y/n): ").strip().lower() != 'n'
    
    print()
    
    if choice == '1':
        tools.fix_classification_consistency(dry_run=dry_run)
    elif choice == '2':
        tools.fix_google_cloud_classifications(dry_run=dry_run)
    elif choice == '3':
        source = input("Source (default: Google Cloud): ").strip() or "Google Cloud"
        tools.fix_customer_names(source=source, dry_run=dry_run)
    elif choice == '4':
        tools.fix_business_outcomes_filtering(dry_run=dry_run)
    elif choice == '5':
        print("Running all fixes...")
        tools.fix_classification_consistency(dry_run=dry_run)
        print("\n" + "="*50 + "\n")
        tools.fix_google_cloud_classifications(dry_run=dry_run)
        print("\n" + "="*50 + "\n")
        tools.fix_customer_names(dry_run=dry_run)
        print("\n" + "="*50 + "\n")
        tools.fix_business_outcomes_filtering(dry_run=dry_run)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()