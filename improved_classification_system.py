#!/usr/bin/env python3
"""
Improved Classification System

This implements a refined 4-tier classification system that addresses
the accuracy concerns identified in the analysis.

Key improvements:
1. Removes ambiguous terms from definitive classification
2. Adds context-dependent analysis tier
3. Strengthens evidence requirements for definitive classification
4. Provides better accuracy through nuanced analysis
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations

class ImprovedClassifier:
    def __init__(self):
        self.db_ops = DatabaseOperations()
        
        # TIER 1: DEFINITIVE GENAI INDICATORS (100% confidence)
        # These are unambiguous and almost always indicate GenAI
        self.definitive_genai_indicators = {
            'modern_llm_platforms': [
                'vertex ai', 'vertex-ai', 'vertexai',
                'gemini', 'bard', 'palm', 'pathways',
                'gpt-4', 'gpt-3.5', 'gpt-3', 'chatgpt',
                'claude', 'claude-3', 'claude-2',
                'llama', 'llama-2', 'llama-3'
            ],
            'generative_technologies': [
                'large language model', 'llm', 'foundation model',
                'transformer model', 'generative ai', 'gen ai', 'genai',
                'generative artificial intelligence'
            ],
            'generative_capabilities': [
                'content generation', 'text generation', 'code generation',
                'natural language generation', 'image generation',
                'creative writing', 'automated writing', 'content creation',
                'prompt engineering', 'few-shot learning', 'zero-shot learning'
            ],
            'modern_genai_services': [
                'vertex ai search', 'vertex ai conversation',
                'dialogflow cx with llm', 'document ai generation',
                'contact center ai with generative capabilities',
                'gemini api', 'palm api', 'bard api'
            ]
        }
        
        # TIER 2: DEFINITIVE TRADITIONAL AI INDICATORS (90% confidence)  
        # These clearly indicate traditional/classical AI
        self.definitive_traditional_indicators = {
            'classic_ml_explicit': [
                'automl tables', 'automl vision classic', 'automl translate classic',
                'supervised learning model', 'classification model only',
                'regression analysis', 'clustering algorithm',
                'decision tree model', 'random forest model'
            ],
            'traditional_analytics': [
                'bigquery analytics only', 'data warehouse reporting',
                'business intelligence dashboard', 'sql-based analysis',
                'statistical analysis', 'descriptive analytics'
            ],
            'rule_based_systems': [
                'rule-based system', 'decision tree logic',
                'if-then rules', 'expert system',
                'scripted responses', 'keyword matching',
                'deterministic algorithm'
            ],
            'traditional_cloud_services': [
                'compute engine only', 'cloud storage migration',
                'cloud sql database', 'kubernetes deployment',
                'load balancer', 'networking configuration'
            ]
        }
        
        # TIER 3: CONTEXT-DEPENDENT INDICATORS (requires analysis)
        # These terms can indicate either GenAI or Traditional AI depending on context
        self.context_dependent_indicators = {
            'ambiguous_ai_terms': [
                'virtual assistant', 'ai assistant', 'chatbot', 'conversational ai',
                'intelligent agent', 'dialogue system', 'voice interface'
            ],
            'processing_capabilities': [
                'document processing', 'form processing', 'text processing',
                'speech recognition', 'speech-to-text', 'language processing',
                'natural language processing', 'nlp'
            ],
            'automation_terms': [
                'intelligent automation', 'process automation', 
                'workflow automation', 'ai-powered automation',
                'smart automation', 'cognitive automation'
            ],
            'ai_applications': [
                'recommendation system', 'personalization engine',
                'search optimization', 'content optimization',
                'customer insights', 'predictive analytics'
            ]
        }
        
        # CONTEXT CLUES to determine GenAI vs Traditional for ambiguous cases
        self.genai_context_clues = {
            'strong_genai_evidence': [
                'using llm', 'powered by gpt', 'gemini integration',
                'foundation model', 'transformer architecture',
                'prompt-based', 'generative model', 'large language',
                'conversational ai with generative', 'ai-generated content'
            ],
            'genai_timeframe': [
                '2023', '2024', '2025', 'recent breakthrough',
                'latest ai advancement', 'next-generation ai',
                'modern ai capabilities', 'cutting-edge ai'
            ],
            'genai_capabilities': [
                'understands context', 'natural conversation',
                'creative responses', 'generates new content',
                'adaptive responses', 'contextual understanding',
                'human-like interaction', 'reasoning capabilities'
            ]
        }
        
        self.traditional_context_clues = {
            'traditional_evidence': [
                'rule-based logic', 'predefined responses',
                'decision tree', 'classification only',
                'pattern matching', 'statistical model',
                'supervised learning', 'feature engineering'
            ],
            'traditional_timeframe': [
                '2019', '2020', '2021', 'established ai',
                'proven ai techniques', 'traditional ml',
                'conventional approach', 'standard ai methods'
            ],
            'traditional_limitations': [
                'limited responses', 'scripted interactions',
                'predefined workflows', 'structured data only',
                'keyword-based', 'template responses'
            ]
        }

    def analyze_story_improved(self, story_id: int, title: str, url: str, customer: str, raw_content: str = '') -> Dict:
        """
        Improved story analysis using 4-tier classification system
        """
        # Combine all available text for analysis
        full_text = f"{title} {url} {raw_content}".lower()
        
        # TIER 1: Check for definitive GenAI indicators
        definitive_genai = self._check_definitive_indicators(full_text, self.definitive_genai_indicators)
        if definitive_genai:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'GenAI',
                'confidence': 1.0,
                'method': 'definitive_genai',
                'evidence': definitive_genai,
                'reasoning': f"Definitive GenAI indicators found: {definitive_genai[:2]}",
                'requires_claude': False
            }
        
        # TIER 2: Check for definitive Traditional AI indicators
        definitive_traditional = self._check_definitive_indicators(full_text, self.definitive_traditional_indicators)
        if definitive_traditional:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'Traditional',
                'confidence': 0.9,
                'method': 'definitive_traditional',
                'evidence': definitive_traditional,
                'reasoning': f"Definitive Traditional AI indicators found: {definitive_traditional[:2]}",
                'requires_claude': False
            }
        
        # TIER 3: Check for context-dependent indicators
        context_dependent = self._check_definitive_indicators(full_text, self.context_dependent_indicators)
        if context_dependent:
            # Analyze context clues to determine classification
            genai_context_score = self._calculate_context_score(full_text, self.genai_context_clues)
            traditional_context_score = self._calculate_context_score(full_text, self.traditional_context_clues)
            
            # Strong context evidence can provide confident classification
            if genai_context_score >= 2.0:  # Strong GenAI evidence
                return {
                    'story_id': story_id,
                    'customer': customer,
                    'recommendation': 'GenAI',
                    'confidence': min(0.8, 0.5 + genai_context_score * 0.15),
                    'method': 'context_analysis_genai',
                    'evidence': context_dependent + self._get_context_evidence(full_text, self.genai_context_clues),
                    'reasoning': f"Context-dependent terms with strong GenAI evidence (score: {genai_context_score:.1f})",
                    'requires_claude': False
                }
            elif traditional_context_score >= 2.0:  # Strong Traditional evidence
                return {
                    'story_id': story_id,
                    'customer': customer,
                    'recommendation': 'Traditional',
                    'confidence': min(0.8, 0.5 + traditional_context_score * 0.15),
                    'method': 'context_analysis_traditional',
                    'evidence': context_dependent + self._get_context_evidence(full_text, self.traditional_context_clues),
                    'reasoning': f"Context-dependent terms with strong Traditional evidence (score: {traditional_context_score:.1f})",
                    'requires_claude': False
                }
            else:
                # Insufficient context - needs Claude analysis
                return {
                    'story_id': story_id,
                    'customer': customer,
                    'recommendation': 'Unclear',
                    'confidence': 0.5,
                    'method': 'context_insufficient',
                    'evidence': context_dependent,
                    'reasoning': f"Context-dependent terms found but insufficient context clues (GenAI: {genai_context_score:.1f}, Traditional: {traditional_context_score:.1f})",
                    'requires_claude': True
                }
        
        # TIER 4: No clear indicators - needs Claude analysis
        return {
            'story_id': story_id,
            'customer': customer,
            'recommendation': 'Unclear',
            'confidence': 0.5,
            'method': 'no_clear_indicators',
            'evidence': [],
            'reasoning': "No definitive or context-dependent AI indicators found",
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

    def _calculate_context_score(self, text: str, context_clues: Dict) -> float:
        """Calculate context score based on evidence strength"""
        total_score = 0.0
        for category, terms in context_clues.items():
            category_weight = {
                'strong_genai_evidence': 1.0,
                'genai_timeframe': 0.3,
                'genai_capabilities': 0.7,
                'traditional_evidence': 1.0,
                'traditional_timeframe': 0.3,
                'traditional_limitations': 0.6
            }.get(category, 0.5)
            
            for term in terms:
                if term in text:
                    total_score += category_weight
        
        return total_score

    def _get_context_evidence(self, text: str, context_clues: Dict) -> List[str]:
        """Get list of context evidence found"""
        evidence = []
        for category, terms in context_clues.items():
            for term in terms:
                if term in text:
                    evidence.append(f"context:{category}:{term}")
        return evidence

    def test_improved_classification(self) -> Dict:
        """Test the improved classification system against known examples"""
        
        test_cases = [
            {
                'title': 'Wells Fargo Virtual Assistant for customer service',
                'content': 'virtual assistant uses AI and cloud to support financial conversations',
                'expected': 'Context-dependent → Needs Claude (insufficient GenAI evidence)',
                'should_require_claude': True
            },
            {
                'title': 'Coca-Cola uses Vertex AI for vending machine insights',
                'content': 'vertex ai platform analyzes data from vending machines',
                'expected': 'GenAI (definitive - Vertex AI)',
                'should_require_claude': False
            },
            {
                'title': 'Company uses Gemini-powered chatbot for customer support',
                'content': 'chatbot powered by gemini provides conversational ai responses',
                'expected': 'GenAI (definitive - Gemini)',
                'should_require_claude': False
            },
            {
                'title': 'Basic rule-based chatbot for FAQ responses',
                'content': 'rule-based chatbot with predefined responses and keyword matching',
                'expected': 'Traditional (context analysis - rule-based evidence)',
                'should_require_claude': False
            },
            {
                'title': 'Document processing with Cloud Vision OCR',
                'content': 'document processing using cloud vision api for text extraction',
                'expected': 'Context-dependent → Needs Claude (insufficient evidence)',
                'should_require_claude': True
            },
            {
                'title': 'Content generation using GPT-4 for marketing',
                'content': 'gpt-4 powered content generation and creative writing',
                'expected': 'GenAI (definitive - GPT-4)',
                'should_require_claude': False
            }
        ]
        
        results = []
        for i, case in enumerate(test_cases):
            analysis = self.analyze_story_improved(
                story_id=i,
                title=case['title'],
                url='',
                customer='Test Company',
                raw_content=case['content']
            )
            
            results.append({
                'title': case['title'],
                'expected': case['expected'],
                'actual': f"{analysis['recommendation']} ({analysis['method']}) - {analysis['reasoning']}",
                'requires_claude_expected': case['should_require_claude'],
                'requires_claude_actual': analysis['requires_claude'],
                'confidence': analysis['confidence'],
                'evidence': analysis['evidence'][:3],  # Show first 3 pieces of evidence
                'correct_claude_requirement': case['should_require_claude'] == analysis['requires_claude']
            })
        
        # Calculate accuracy metrics
        claude_accuracy = sum(1 for r in results if r['correct_claude_requirement']) / len(results)
        
        return {
            'test_results': results,
            'claude_requirement_accuracy': claude_accuracy,
            'total_cases': len(results),
            'cases_needing_claude': sum(1 for r in results if r['requires_claude_actual']),
            'efficiency_improvement': f"Reduced Claude calls from ambiguous classification to targeted analysis"
        }

def main():
    """Test and demonstrate the improved classification system"""
    print("🚀 Improved Classification System Test")
    print("=" * 60)
    
    classifier = ImprovedClassifier()
    
    # Run test cases
    print("\n🧪 TESTING IMPROVED CLASSIFICATION:")
    test_results = classifier.test_improved_classification()
    
    print(f"Total test cases: {test_results['total_cases']}")
    print(f"Cases needing Claude: {test_results['cases_needing_claude']}")
    print(f"Claude requirement accuracy: {test_results['claude_requirement_accuracy']:.1%}")
    
    print(f"\n📋 DETAILED TEST RESULTS:")
    for i, result in enumerate(test_results['test_results'], 1):
        status = "✅" if result['correct_claude_requirement'] else "❌"
        print(f"\n{i}. {status} {result['title']}")
        print(f"   Expected: {result['expected']}")
        print(f"   Actual: {result['actual']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Evidence: {result['evidence']}")
        print(f"   Claude needed: {result['requires_claude_actual']}")
    
    print(f"\n💡 KEY IMPROVEMENTS:")
    print("1. ✅ Removed 'virtual assistant' and 'chatbot' from definitive GenAI indicators")
    print("2. ✅ Added context-dependent analysis tier for ambiguous terms")
    print("3. ✅ Strengthened definitive indicators with concrete platform evidence")
    print("4. ✅ Improved accuracy by requiring evidence for classification")
    print("5. ✅ Reduced unnecessary Claude API calls through better rule-based analysis")
    
    print(f"\n🎯 CLASSIFICATION TIERS:")
    print("Tier 1: Definitive GenAI (LLM platforms, generative capabilities)")
    print("Tier 2: Definitive Traditional (rule-based, classic ML, analytics)")
    print("Tier 3: Context-dependent (analyze surrounding evidence)")
    print("Tier 4: Claude analysis (complex or unclear cases)")

if __name__ == "__main__":
    main()