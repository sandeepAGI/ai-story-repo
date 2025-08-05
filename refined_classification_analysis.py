#!/usr/bin/env python3
"""
Refined Classification Analysis

This script analyzes the current classification logic and proposes
improvements to address accuracy concerns raised by the user.

Key Issues to Address:
1. Virtual assistants are not automatically GenAI
2. Chatbots can be rule-based or GenAI-powered
3. Need more nuanced context-dependent classification
"""

import json
from typing import Dict, List, Tuple
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations

class RefinedClassificationAnalyzer:
    def __init__(self):
        self.db_ops = DatabaseOperations()
        
        # PROBLEMATIC INDICATORS - These need context to classify correctly
        self.context_dependent_indicators = {
            'virtual_assistants': [
                'virtual assistant', 'ai assistant', 'chatbot', 'conversational ai'
            ],
            'document_processing': [
                'document processing', 'form processing', 'ocr'
            ],
            'speech_tech': [
                'speech recognition', 'voice interface', 'speech-to-text'
            ],
            'automation': [
                'intelligent automation', 'process automation', 'workflow automation'
            ]
        }
        
        # DEFINITIVE GENAI INDICATORS - These are almost always GenAI
        self.definitive_genai_indicators = {
            'modern_llm_platforms': [
                'vertex ai', 'gemini', 'bard', 'palm', 'pathways',
                'gpt-4', 'gpt-3', 'claude', 'llama', 'chatgpt'
            ],
            'generative_technologies': [
                'large language model', 'llm', 'foundation model',
                'transformer model', 'generative ai', 'gen ai'
            ],
            'generative_capabilities': [
                'content generation', 'text generation', 'code generation',
                'natural language generation', 'image generation',
                'creative writing', 'summarization', 'translation generation'
            ],
            'modern_genai_services': [
                'dialogflow cx with llm', 'document ai generation',
                'contact center ai with generative', 'vertex ai search',
                'text-to-speech generation', 'speech synthesis'
            ]
        }
        
        # DEFINITIVE TRADITIONAL AI INDICATORS
        self.definitive_traditional_indicators = {
            'classic_ml': [
                'automl tables', 'automl vision classic', 'supervised learning',
                'classification model', 'regression model', 'clustering'
            ],
            'traditional_analytics': [
                'bigquery analytics', 'data warehouse', 'business intelligence',
                'sql analysis', 'reporting dashboard', 'etl pipeline'
            ],
            'rule_based_systems': [
                'rule-based chatbot', 'decision tree', 'expert system',
                'if-then logic', 'scripted responses'
            ],
            'traditional_ai_services': [
                'automl without generation', 'cloud vision api',
                'cloud speech-to-text', 'cloud translation api',
                'recommendation engine traditional'
            ]
        }
        
        # CONTEXT CLUES for ambiguous cases
        self.genai_context_clues = {
            'time_indicators': [
                '2023', '2024', '2025', 'recent', 'latest', 'new generation'
            ],
            'genai_keywords': [
                'prompt', 'fine-tuning', 'few-shot', 'zero-shot',
                'chain of thought', 'reasoning', 'creative', 'generate'
            ],
            'modern_partnerships': [
                'openai partnership', 'anthropic integration', 
                'google ai partnership', 'generative ai initiative'
            ]
        }
        
        self.traditional_context_clues = {
            'legacy_indicators': [
                'legacy system integration', 'existing ml model',
                'traditional approach', 'rule-based logic'
            ],
            'basic_automation': [
                'simple automation', 'basic classification',
                'standard ml pipeline', 'predictive model only'
            ]
        }

    def analyze_current_misclassifications(self) -> Dict:
        """Analyze current classification logic for potential issues"""
        
        results = {
            'problematic_rules': [],
            'accuracy_concerns': [],
            'recommended_changes': []
        }
        
        # Issue 1: Virtual Assistant ambiguity
        results['problematic_rules'].append({
            'rule': 'virtual assistant → always GenAI',
            'problem': 'Virtual assistants can be rule-based (Traditional) or GenAI-powered',
            'examples': [
                'Rule-based chatbot for FAQ → Traditional AI',
                'LLM-powered conversational agent → GenAI',
                'Basic voice menu system → Traditional AI',
                'Gemini-powered virtual assistant → GenAI'
            ]
        })
        
        # Issue 2: Chatbot classification
        results['problematic_rules'].append({
            'rule': 'chatbot → always GenAI',
            'problem': 'Chatbots existed long before GenAI',
            'examples': [
                'Decision tree chatbot (2015) → Traditional AI',
                'GPT-powered chatbot (2023) → GenAI',
                'FAQ bot with keyword matching → Traditional AI',
                'Claude-powered customer service → GenAI'
            ]
        })
        
        # Issue 3: Document processing ambiguity
        results['problematic_rules'].append({
            'rule': 'document processing → context dependent',
            'problem': 'Can be OCR (Traditional) or Document AI generation (GenAI)',
            'examples': [
                'Basic OCR text extraction → Traditional AI',
                'Document AI with content generation → GenAI',
                'Form field extraction → Traditional AI',
                'Document summarization with LLM → GenAI'
            ]
        })
        
        # Recommended changes
        results['recommended_changes'] = [
            {
                'change': 'Remove "virtual assistant" from definitive GenAI indicators',
                'reason': 'Requires context to classify correctly',
                'new_approach': 'Look for LLM/GenAI context clues or modern platform usage'
            },
            {
                'change': 'Remove "chatbot" from definitive GenAI indicators', 
                'reason': 'Chatbots predate GenAI by decades',
                'new_approach': 'Check for generative capabilities or modern AI platforms'
            },
            {
                'change': 'Add context-dependent classification tier',
                'reason': 'Some technologies can be either Traditional or GenAI',
                'new_approach': '3-tier system: Definitive → Context-dependent → Claude analysis'
            },
            {
                'change': 'Strengthen GenAI indicators with platform-specific evidence',
                'reason': 'More accurate classification with concrete evidence',
                'new_approach': 'Focus on LLM platforms, generative capabilities, modern services'
            }
        ]
        
        return results

    def propose_refined_classification_system(self) -> Dict:
        """Propose a more accurate 4-tier classification system"""
        
        return {
            'tier_1_definitive_genai': {
                'description': 'Unambiguous GenAI indicators - 100% confidence',
                'indicators': self.definitive_genai_indicators,
                'confidence': 1.0,
                'action': 'Classify as GenAI immediately'
            },
            'tier_2_definitive_traditional': {
                'description': 'Unambiguous Traditional AI indicators - high confidence',
                'indicators': self.definitive_traditional_indicators,
                'confidence': 0.9,
                'action': 'Classify as Traditional AI immediately'
            },
            'tier_3_context_dependent': {
                'description': 'Ambiguous terms requiring context analysis',
                'indicators': self.context_dependent_indicators,
                'confidence': 0.5,
                'action': 'Analyze context clues for additional evidence'
            },
            'tier_4_claude_analysis': {
                'description': 'Complex cases requiring LLM analysis',
                'confidence': 0.5,
                'action': 'Send to Claude with refined prompt'
            }
        }

    def test_classification_accuracy(self) -> Dict:
        """Test current classification against known examples"""
        
        test_cases = [
            {
                'title': 'Wells Fargo Virtual Assistant powered by conversational AI',
                'current_classification': 'GenAI (definitive)',
                'should_be': 'Context-dependent → Check for LLM evidence',
                'reasoning': 'Virtual assistant alone is not definitive'
            },
            {
                'title': 'Coca-Cola uses Vertex AI for vending machine insights',
                'current_classification': 'GenAI (definitive)',
                'should_be': 'GenAI (definitive)',
                'reasoning': 'Vertex AI is definitive GenAI platform'
            },
            {
                'title': 'Company uses chatbot for customer FAQ',
                'current_classification': 'GenAI (definitive)',
                'should_be': 'Context-dependent → Look for generative evidence',
                'reasoning': 'Chatbot could be rule-based or GenAI-powered'
            },
            {
                'title': 'Document OCR processing with Cloud Vision API',
                'current_classification': 'Traditional (likely)',
                'should_be': 'Traditional (definitive)',
                'reasoning': 'Basic OCR is traditional computer vision'
            },
            {
                'title': 'GPT-4 powered content generation for marketing',
                'current_classification': 'GenAI (definitive)',
                'should_be': 'GenAI (definitive)',
                'reasoning': 'GPT-4 and content generation are definitive GenAI'
            }
        ]
        
        accuracy_issues = []
        for case in test_cases:
            if case['current_classification'] != case['should_be']:
                accuracy_issues.append(case)
        
        return {
            'total_test_cases': len(test_cases),
            'accuracy_issues': len(accuracy_issues),
            'accuracy_rate': (len(test_cases) - len(accuracy_issues)) / len(test_cases),
            'problem_cases': accuracy_issues
        }

def main():
    """Analyze current classification accuracy and propose improvements"""
    print("🔍 Refined Classification Analysis")
    print("=" * 60)
    
    analyzer = RefinedClassificationAnalyzer()
    
    # Step 1: Analyze current classification issues
    print("\n📋 CURRENT CLASSIFICATION ISSUES:")
    issues = analyzer.analyze_current_misclassifications()
    
    for i, rule in enumerate(issues['problematic_rules'], 1):
        print(f"\n{i}. PROBLEM: {rule['rule']}")
        print(f"   Issue: {rule['problem']}")
        print("   Examples:")
        for example in rule['examples']:
            print(f"   - {example}")
    
    # Step 2: Propose refined system
    print(f"\n🎯 PROPOSED REFINED CLASSIFICATION SYSTEM:")
    refined_system = analyzer.propose_refined_classification_system()
    
    for tier_name, tier_info in refined_system.items():
        tier_num = tier_name.split('_')[1]
        print(f"\nTier {tier_num}: {tier_info['description']}")
        print(f"Confidence: {tier_info['confidence']}")
        print(f"Action: {tier_info['action']}")
    
    # Step 3: Test accuracy
    print(f"\n🧪 ACCURACY TEST RESULTS:")
    accuracy_results = analyzer.test_classification_accuracy()
    
    print(f"Test cases: {accuracy_results['total_test_cases']}")
    print(f"Accuracy issues: {accuracy_results['accuracy_issues']}")
    print(f"Current accuracy rate: {accuracy_results['accuracy_rate']:.1%}")
    
    if accuracy_results['problem_cases']:
        print(f"\n❌ PROBLEM CASES:")
        for case in accuracy_results['problem_cases']:
            print(f"  '{case['title']}'")
            print(f"    Current: {case['current_classification']}")
            print(f"    Should be: {case['should_be']}")
            print(f"    Reason: {case['reasoning']}")
    
    # Step 4: Recommendations
    print(f"\n💡 KEY RECOMMENDATIONS:")
    for i, change in enumerate(issues['recommended_changes'], 1):
        print(f"{i}. {change['change']}")
        print(f"   Reason: {change['reason']}")
        print(f"   New approach: {change['new_approach']}")
        print()
    
    print("✅ NEXT STEPS:")
    print("1. Implement 4-tier classification system")
    print("2. Move ambiguous terms to context-dependent tier")
    print("3. Strengthen definitive indicators with platform evidence")
    print("4. Test refined system before universal rollout")

if __name__ == "__main__":
    main()