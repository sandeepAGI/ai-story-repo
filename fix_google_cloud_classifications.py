#!/usr/bin/env python3
"""
Enhanced Google Cloud Story Classification Fix

This script implements a 3-tier classification system:
1. Definitive indicators (automatic classification)
2. Heuristic analysis (rule-based with confidence scores)  
3. Claude analysis (only for truly unclear cases)

This approach minimizes API calls while maximizing accuracy.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations

class EnhancedClassifier:
    def __init__(self):
        self.db_ops = DatabaseOperations()
        
        # Definitive GenAI indicators (100% confidence)
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
            ],
            'genai_services': [
                'dialogflow cx', 'contact center ai', 'document ai generation',
                'translation ai', 'speech synthesis', 'text-to-speech generation'
            ]
        }
        
        # Definitive Traditional AI indicators (high confidence)
        self.definitive_traditional_indicators = {
            'traditional_ml': [
                'automl tables', 'automl vision classic', 'automl translation classic',
                'bigquery ml basic', 'classic ml', 'supervised learning only'
            ],
            'pure_analytics': [
                'bigquery analytics', 'data warehouse', 'business intelligence',
                'reporting dashboard', 'data migration', 'etl pipeline'
            ],
            'infrastructure': [
                'compute engine', 'cloud storage', 'kubernetes engine',
                'cloud sql', 'devops', 'ci/cd', 'infrastructure migration'
            ]
        }
        
        # Heuristic indicators (require analysis)
        self.heuristic_genai_indicators = {
            'modern_ai_terms': [
                ('personalization', 0.7),  # Often GenAI-powered in 2023+
                ('intelligent workflow', 0.8),
                ('ai acceleration', 0.6),
                ('document processing', 0.7),  # Google Document AI is GenAI
                ('marketing optimization', 0.6),  # Often uses GenAI for content
                ('customer experience ai', 0.7),
                ('predictive personalization', 0.8),
                ('recommendation ai', 0.5)  # Could be either
            ],
            'modern_timeframe': [
                ('2023', 0.3),  # GenAI adoption year
                ('2024', 0.4),  # Strong GenAI era
                ('2025', 0.5)   # Future GenAI era
            ],
            'partnership_context': [
                ('strategic ai partnership', 0.6),
                ('ai innovation', 0.5),
                ('next generation ai', 0.7)
            ]
        }
    
    def analyze_story(self, story_id: int, title: str, url: str, customer: str) -> Dict:
        """
        Analyze a story and return classification recommendation
        """
        full_text = f"{title} {url}".lower()
        
        # Step 1: Check for definitive indicators
        definitive_genai = self._check_definitive_indicators(full_text, self.definitive_genai_indicators)
        definitive_traditional = self._check_definitive_indicators(full_text, self.definitive_traditional_indicators)
        
        if definitive_genai:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'GenAI',
                'confidence': 1.0,
                'method': 'definitive',
                'indicators': definitive_genai,
                'requires_claude': False
            }
        
        if definitive_traditional:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'Traditional',
                'confidence': 0.9,
                'method': 'definitive',
                'indicators': definitive_traditional,
                'requires_claude': False
            }
        
        # Step 2: Heuristic analysis
        heuristic_score = self._calculate_heuristic_score(full_text)
        
        if heuristic_score['genai_confidence'] >= 0.7:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'GenAI',
                'confidence': heuristic_score['genai_confidence'],
                'method': 'heuristic',
                'indicators': heuristic_score['indicators'],
                'requires_claude': False
            }
        elif heuristic_score['genai_confidence'] <= 0.3:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'Traditional',
                'confidence': 1.0 - heuristic_score['genai_confidence'],
                'method': 'heuristic',
                'indicators': heuristic_score['indicators'],
                'requires_claude': False
            }
        else:
            # Step 3: Needs Claude analysis
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'Unclear',
                'confidence': 0.5,
                'method': 'needs_claude',
                'indicators': heuristic_score['indicators'],
                'requires_claude': True
            }
    
    def _check_definitive_indicators(self, text: str, indicator_dict: Dict) -> List[str]:
        """Check for definitive classification indicators"""
        found_indicators = []
        for category, terms in indicator_dict.items():
            for term in terms:
                if term in text:
                    found_indicators.append(f"{category}:{term}")
        return found_indicators
    
    def _calculate_heuristic_score(self, text: str) -> Dict:
        """Calculate GenAI probability using heuristic indicators"""
        total_score = 0.0
        found_indicators = []
        
        for category, terms in self.heuristic_genai_indicators.items():
            for term, weight in terms:
                if term in text:
                    total_score += weight
                    found_indicators.append(f"{category}:{term}({weight})")
        
        # Normalize score to 0-1 range
        genai_confidence = min(total_score / 2.0, 1.0)  # Max expected score ~2.0
        
        return {
            'genai_confidence': genai_confidence,
            'indicators': found_indicators
        }
    
    def fix_definitive_misclassifications(self) -> List[Dict]:
        """Fix stories with definitive misclassifications"""
        print("🔧 Fixing definitive misclassifications...")
        
        fixed_stories = []
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                # Get all Google Cloud stories
                cursor.execute("""
                    SELECT id, customer_name, title, url, is_gen_ai
                    FROM customer_stories 
                    WHERE url LIKE '%cloud.google.com%'
                """)
                stories = cursor.fetchall()
                
                for story in stories:
                    analysis = self.analyze_story(
                        story['id'],
                        story['title'] or '',
                        story['url'],
                        story['customer_name']
                    )
                    
                    current_classification = story['is_gen_ai']
                    recommended_genai = analysis['recommendation'] == 'GenAI'
                    
                    # Fix definitive misclassifications
                    if (analysis['method'] == 'definitive' and 
                        analysis['confidence'] >= 0.9 and
                        current_classification != recommended_genai):
                        
                        print(f"Fixing Story ID {analysis['story_id']}: {analysis['customer']}")
                        print(f"  Current: {'GenAI' if current_classification else 'Traditional'} → New: {analysis['recommendation']}")
                        print(f"  Confidence: {analysis['confidence']:.2f}")
                        print(f"  Indicators: {analysis['indicators']}")
                        
                        # Update the database
                        cursor.execute("""
                            UPDATE customer_stories 
                            SET is_gen_ai = %s 
                            WHERE id = %s
                        """, (recommended_genai, analysis['story_id']))
                        
                        fixed_stories.append(analysis)
                        print("  ✅ Updated in database")
                        print()
                
                # Commit changes
                cursor.connection.commit()
                
        except Exception as e:
            print(f"Error fixing classifications: {e}")
            import traceback
            traceback.print_exc()
        
        return fixed_stories
    
    def analyze_all_stories(self) -> Dict:
        """Analyze all Google Cloud stories and categorize by classification method"""
        print("📊 Analyzing all Google Cloud stories...")
        
        results = {
            'definitive_fixes': [],
            'heuristic_recommendations': [],
            'needs_claude_analysis': []
        }
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, customer_name, title, url, is_gen_ai
                    FROM customer_stories 
                    WHERE url LIKE '%cloud.google.com%'
                    ORDER BY id DESC
                """)
                stories = cursor.fetchall()
                
                for story in stories:
                    analysis = self.analyze_story(
                        story['id'],
                        story['title'] or '',
                        story['url'],
                        story['customer_name']
                    )
                    
                    current_classification = story['is_gen_ai']
                    recommended_genai = analysis['recommendation'] == 'GenAI'
                    
                    if (analysis['method'] == 'definitive' and 
                        current_classification != recommended_genai):
                        results['definitive_fixes'].append(analysis)
                    
                    elif analysis['method'] == 'heuristic':
                        analysis['current_classification'] = 'GenAI' if current_classification else 'Traditional'
                        results['heuristic_recommendations'].append(analysis)
                    
                    elif analysis['requires_claude']:
                        analysis['current_classification'] = 'GenAI' if current_classification else 'Traditional'
                        results['needs_claude_analysis'].append(analysis)
                
        except Exception as e:
            print(f"Error analyzing stories: {e}")
            import traceback
            traceback.print_exc()
        
        return results

def main():
    """Main execution"""
    print("🚀 Enhanced Google Cloud Story Classification Analysis")
    print("=" * 70)
    
    classifier = EnhancedClassifier()
    
    # Step 1: Analyze all stories
    results = classifier.analyze_all_stories()
    
    print(f"\n📋 ANALYSIS RESULTS:")
    print(f"  Definitive fixes needed: {len(results['definitive_fixes'])}")
    print(f"  Heuristic recommendations: {len(results['heuristic_recommendations'])}")
    print(f"  Need Claude analysis: {len(results['needs_claude_analysis'])}")
    
    # Step 2: Show definitive fixes
    if results['definitive_fixes']:
        print(f"\n🔧 DEFINITIVE FIXES NEEDED ({len(results['definitive_fixes'])}):")
        for fix in results['definitive_fixes']:
            print(f"  ID {fix['story_id']}: {fix['customer']} → {fix['recommendation']}")
            print(f"    Confidence: {fix['confidence']:.2f} | Indicators: {fix['indicators'][:2]}...")
    
    # Step 3: Show heuristic recommendations
    if results['heuristic_recommendations']:
        print(f"\n🤔 HEURISTIC RECOMMENDATIONS ({len(results['heuristic_recommendations'])}):")
        for rec in results['heuristic_recommendations'][:5]:  # Show first 5
            print(f"  ID {rec['story_id']}: {rec['customer']} → {rec['recommendation']}")
            print(f"    Current: {rec['current_classification']} | Confidence: {rec['confidence']:.2f}")
    
    # Step 4: Apply definitive fixes
    print(f"\n🔧 APPLYING DEFINITIVE FIXES...")
    fixed_stories = classifier.fix_definitive_misclassifications()
    
    print(f"\n✅ COMPLETED: Fixed {len(fixed_stories)} definitive misclassifications")
    
    # Step 5: Calculate efficiency metrics
    total_stories = len(results['definitive_fixes']) + len(results['heuristic_recommendations']) + len(results['needs_claude_analysis'])
    automatic_fixes = len(results['definitive_fixes'])
    claude_needed = len(results['needs_claude_analysis'])
    
    if total_stories > 0:
        efficiency = ((total_stories - claude_needed) / total_stories) * 100
        print(f"\n💡 EFFICIENCY METRICS:")
        print(f"  Automatic classification: {efficiency:.1f}% of stories")
        print(f"  Claude API calls reduced: {100 - (claude_needed/total_stories)*100:.1f}%")
        print(f"  Stories requiring Claude: {claude_needed}")

if __name__ == "__main__":
    main()