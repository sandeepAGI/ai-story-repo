#!/usr/bin/env python3
"""
Enhanced AI Classification System

Implements refined 4-tier classification:
1. Tier 1: Definitive GenAI (specific models & capabilities)
2. Tier 2: Definitive Traditional AI 
3. Tier 3: Context-dependent (requires evidence analysis)
4. Tier 4: Claude analysis (only when others fail)
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
        self.claude_processor = None  # Only initialize if needed
        
        # TIER 1: DEFINITIVE GENAI INDICATORS (100% confidence)
        # Specific models and capabilities that are unambiguously GenAI
        self.definitive_genai_indicators = {
            'llm_models': [
                # OpenAI models
                'gpt', 'gpt-4', 'gpt-3.5', 'gpt-3', 'chatgpt', 'davinci', 'curie',
                # Google models  
                'gemini', 'bard', 'palm', 'pathways',
                # Anthropic models
                'claude', 'claude-3', 'claude-2', 'claude instant',
                # Meta models
                'llama', 'llama-2', 'llama-3', 'code llama',
                # Mistral models
                'mistral', 'mixtral', 'mistral-7b',
                # Microsoft GenAI products
                'copilot', 'microsoft copilot', 'github copilot', 'copilot for microsoft 365', 'microsoft 365 copilot',
                # Other models
                'cohere', 'command'
            ],
            'genai_technologies': [
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
            'specific_genai_services': [
                'vertex ai search', 'document ai generation',
                'dialogflow cx', 'contact center ai with generative',
                'gemini api', 'palm api', 'bard api',
                'azure openai', 'azure openai service', 'openai service'
            ]
        }
        
        # TIER 2: DEFINITIVE TRADITIONAL AI INDICATORS (90% confidence)
        self.definitive_traditional_indicators = {
            'classic_ml_explicit': [
                'automl tables', 'automl vision classic', 'automl translate classic',
                'supervised learning model', 'classification model only',
                'regression analysis', 'clustering algorithm',
                'decision tree model', 'random forest model', 'svm model'
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
                'deterministic algorithm', 'finite state machine'
            ],
            'traditional_cloud_services': [
                'compute engine only', 'cloud storage migration',
                'cloud sql database', 'kubernetes deployment',
                'load balancer', 'networking configuration',
                'basic ocr', 'simple speech-to-text'
            ]
        }
        
        # TIER 3: CONTEXT-DEPENDENT INDICATORS (requires evidence analysis)
        self.context_dependent_indicators = {
            'ambiguous_ai_terms': [
                'virtual assistant', 'ai assistant', 'chatbot', 'conversational ai',
                'intelligent agent', 'dialogue system', 'voice interface'
            ],
            'ambiguous_platforms': [
                'vertex ai', 'bedrock', 'azure openai', 'hugging face',
                'sagemaker', 'databricks'
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
        
        # CONTEXT CLUES for resolving ambiguous cases
        self.genai_context_clues = {
            'strong_genai_evidence': [
                'using llm', 'powered by gpt', 'gemini integration',
                'foundation model', 'transformer architecture',
                'prompt-based', 'generative model', 'large language',
                'conversational ai with generative', 'ai-generated content',
                'creates content', 'generates responses', 'writes content'
            ],
            'genai_capabilities': [
                'understands context', 'natural conversation',
                'creative responses', 'generates new content',
                'adaptive responses', 'contextual understanding',
                'human-like interaction', 'reasoning capabilities'
            ],
            'genai_timeframe': [
                '2023', '2024', '2025', 'recent breakthrough',
                'latest ai advancement', 'next-generation ai',
                'modern ai capabilities', 'cutting-edge ai'
            ]
        }
        
        self.traditional_context_clues = {
            'traditional_evidence': [
                'rule-based logic', 'predefined responses',
                'decision tree', 'classification only',
                'pattern matching', 'statistical model',
                'supervised learning', 'feature engineering',
                'basic ocr', 'simple classification'
            ],
            'traditional_limitations': [
                'limited responses', 'scripted interactions',
                'predefined workflows', 'structured data only',
                'keyword-based', 'template responses'
            ],
            'traditional_timeframe': [
                '2019', '2020', '2021', 'established ai',
                'proven ai techniques', 'traditional ml',
                'conventional approach', 'standard ai methods'
            ]
        }

    def classify_story(self, story_id: int, title: str, url: str, customer: str, raw_content: str = '') -> Dict:
        """
        Enhanced 4-tier classification system
        """
        # For high-confidence indicators, prioritize title and URL first
        primary_text = f"{title} {url}".lower()
        
        # Check definitive indicators in primary text first (most reliable)
        definitive_genai_primary = self._check_indicators(primary_text, self.definitive_genai_indicators)
        definitive_traditional_primary = self._check_indicators(primary_text, self.definitive_traditional_indicators)
        
        # If we find definitive indicators in title/URL, use them (high confidence)
        if definitive_genai_primary:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'GenAI',
                'confidence': 1.0,
                'method': 'tier_1_definitive_genai_primary',
                'evidence': definitive_genai_primary,
                'reasoning': f"Definitive GenAI indicators in title/URL: {definitive_genai_primary[:2]}",
                'requires_claude': False
            }
        
        if definitive_traditional_primary:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'Traditional',
                'confidence': 0.9,
                'method': 'tier_2_definitive_traditional_primary',
                'evidence': definitive_traditional_primary,
                'reasoning': f"Definitive Traditional AI indicators in title/URL: {definitive_traditional_primary[:2]}",
                'requires_claude': False
            }
        
        # If no definitive indicators in primary text, carefully check content
        cleaned_content = self._clean_raw_content(raw_content)
        full_text = f"{primary_text} {cleaned_content}".lower()
        
        # TIER 1: Check for definitive GenAI indicators
        definitive_genai = self._check_indicators(full_text, self.definitive_genai_indicators)
        if definitive_genai:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'GenAI',
                'confidence': 1.0,
                'method': 'tier_1_definitive_genai',
                'evidence': definitive_genai,
                'reasoning': f"Definitive GenAI indicators: {definitive_genai[:2]}",
                'requires_claude': False
            }
        
        # TIER 2: Check for definitive Traditional AI indicators
        definitive_traditional = self._check_indicators(full_text, self.definitive_traditional_indicators)
        if definitive_traditional:
            return {
                'story_id': story_id,
                'customer': customer,
                'recommendation': 'Traditional',
                'confidence': 0.9,
                'method': 'tier_2_definitive_traditional',
                'evidence': definitive_traditional,
                'reasoning': f"Definitive Traditional AI indicators: {definitive_traditional[:2]}",
                'requires_claude': False
            }
        
        # TIER 3: Check for context-dependent indicators
        context_dependent = self._check_indicators(full_text, self.context_dependent_indicators)
        if context_dependent:
            # Analyze context clues
            genai_score = self._calculate_context_score(full_text, self.genai_context_clues)
            traditional_score = self._calculate_context_score(full_text, self.traditional_context_clues)
            
            # Strong context evidence provides confident classification
            if genai_score >= 2.0:  # Strong GenAI evidence
                return {
                    'story_id': story_id,
                    'customer': customer,
                    'recommendation': 'GenAI',
                    'confidence': min(0.85, 0.6 + genai_score * 0.1),
                    'method': 'tier_3_context_genai',
                    'evidence': context_dependent + self._get_context_evidence(full_text, self.genai_context_clues),
                    'reasoning': f"Context-dependent with strong GenAI evidence (score: {genai_score:.1f})",
                    'requires_claude': False
                }
            elif traditional_score >= 2.0:  # Strong Traditional evidence
                return {
                    'story_id': story_id,
                    'customer': customer,
                    'recommendation': 'Traditional',
                    'confidence': min(0.85, 0.6 + traditional_score * 0.1),
                    'method': 'tier_3_context_traditional',
                    'evidence': context_dependent + self._get_context_evidence(full_text, self.traditional_context_clues),
                    'reasoning': f"Context-dependent with strong Traditional evidence (score: {traditional_score:.1f})",
                    'requires_claude': False
                }
        
        # TIER 4: Claude analysis required (only when others fail)
        return {
            'story_id': story_id,
            'customer': customer,
            'recommendation': 'Unclear',
            'confidence': 0.5,
            'method': 'tier_4_needs_claude',
            'evidence': context_dependent if context_dependent else [],
            'reasoning': f"No definitive indicators found. Context evidence insufficient (GenAI: {genai_score:.1f}, Traditional: {traditional_score:.1f})" if context_dependent else "No clear AI indicators found",
            'requires_claude': True
        }

    def classify_with_claude_fallback(self, story_id: int, title: str, url: str, customer: str, raw_content: Dict = None) -> Dict:
        """
        Full classification with Claude fallback when needed
        """
        # First try rule-based classification
        raw_text = raw_content.get('text', '') if raw_content else ''
        result = self.classify_story(story_id, title, url, customer, raw_text)
        
        # If Claude analysis is required, use it
        if result['requires_claude']:
            if not self.claude_processor:
                # Import here to avoid circular import
                from src.ai_integration.claude_processor import ClaudeProcessor
                self.claude_processor = ClaudeProcessor()
            
            # Use the direct Claude classification to avoid recursion
            claude_result = self.claude_processor._claude_gen_ai_classification(raw_content or {})
            if claude_result:
                result.update({
                    'recommendation': 'GenAI' if claude_result.get('is_gen_ai') else 'Traditional',
                    'confidence': claude_result.get('confidence', 0.5),
                    'method': 'tier_4_claude_analysis',
                    'claude_reasoning': claude_result.get('reasoning', ''),
                    'claude_indicators': claude_result.get('key_indicators', []),
                    'requires_claude': False  # Completed
                })
        
        return result

    def _check_indicators(self, text: str, indicator_dict: Dict) -> List[str]:
        """Check for indicators in text using word boundaries to avoid false positives"""
        found_indicators = []
        for category, terms in indicator_dict.items():
            for term in terms:
                # Use word boundaries for better matching
                if self._is_term_present(text, term):
                    found_indicators.append(f"{category}:{term}")
        return found_indicators
    
    def _is_term_present(self, text: str, term: str) -> bool:
        """Check if term is present as whole words, avoiding substring false positives"""
        import re
        
        # For multi-word terms, check exact phrase with word boundaries
        if ' ' in term:
            pattern = r'\b' + re.escape(term) + r'\b'
            return bool(re.search(pattern, text, re.IGNORECASE))
        
        # For single words, use word boundaries
        # Special handling for terms with hyphens or special characters
        if '-' in term or '.' in term:
            # For terms like "vertex-ai" or "gpt-4", match as exact phrase
            pattern = r'\b' + re.escape(term) + r'\b'
            return bool(re.search(pattern, text, re.IGNORECASE))
        
        # For simple single words, use word boundaries
        pattern = r'\b' + re.escape(term) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _clean_raw_content(self, raw_content: str) -> str:
        """Clean raw content to focus on main story content, avoiding navigation contamination"""
        if not raw_content:
            return ""
        
        # More aggressive navigation/footer filtering
        text = raw_content.lower()
        
        # Remove common navigation sections entirely
        navigation_sections = [
            'customer stories home all stories',
            'stories by product ai & microsoft copilot',
            'explore solutions follow microsoft',
            'surface pro surface laptop',
            'stay organized with collections',
            'save and categorize content',
            'skip to main content',
            'microsoft customer stories',
            'this is the trace id'
        ]
        
        for section in navigation_sections:
            text = text.replace(section, ' ')
        
        # Split into sentences and filter
        sentences = text.split('.')
        cleaned_sentences = []
        
        # Enhanced navigation indicators to skip
        navigation_indicators = [
            'microsoft.com/', 'customer stories', 'all stories', 'stories by product',
            'home customers', 'explore solutions', 'follow microsoft', 'surface pro',
            'surface laptop', 'what\'s new', 'stay organized', 'save and categorize',
            'learn more about', 'skip to main', 'trace id', 'dynamics 365',
            'microsoft 365', 'azure', 'windows', 'xbox'  # But only if in navigation context
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip very short sentences (likely navigation fragments)
            if len(sentence) < 30:
                continue
            
            # Skip sentences with multiple navigation indicators (likely nav menus)
            nav_count = sum(1 for indicator in navigation_indicators if indicator in sentence)
            if nav_count >= 2:  # Multiple navigation terms = likely navigation
                continue
                
            # Skip sentences that are mostly navigation
            if any(indicator in sentence and len(sentence) < 100 for indicator in navigation_indicators):
                continue
                
            # Keep sentences that seem like main content
            cleaned_sentences.append(sentence)
        
        # Return meaningful content, focusing on story substance
        cleaned_content = '. '.join(cleaned_sentences[:8])  # First 8 substantial sentences
        return cleaned_content[:800]  # Reasonable length limit

    def _calculate_context_score(self, text: str, context_clues: Dict) -> float:
        """Calculate context score based on evidence strength"""
        total_score = 0.0
        for category, terms in context_clues.items():
            category_weight = {
                'strong_genai_evidence': 1.0,
                'genai_capabilities': 0.7,
                'genai_timeframe': 0.3,
                'traditional_evidence': 1.0,
                'traditional_limitations': 0.6,
                'traditional_timeframe': 0.3
            }.get(category, 0.5)
            
            for term in terms:
                if self._is_term_present(text, term):
                    total_score += category_weight
        
        return total_score

    def _get_context_evidence(self, text: str, context_clues: Dict) -> List[str]:
        """Get list of context evidence found"""
        evidence = []
        for category, terms in context_clues.items():
            for term in terms:
                if self._is_term_present(text, term):
                    evidence.append(f"context:{category}:{term}")
        return evidence

    def analyze_database_stories(self, provider: str = None, limit: int = None) -> Dict:
        """Analyze stories from database using enhanced classification"""
        results = {
            'tier_1_definitive_genai': [],
            'tier_2_definitive_traditional': [],
            'tier_3_context_resolved': [],
            'tier_4_needs_claude': [],
            'total_analyzed': 0,
            'classification_efficiency': {}
        }
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                query = """
                    SELECT id, customer_name, title, url, is_gen_ai, raw_content
                    FROM customer_stories 
                """
                params = []
                
                if provider:
                    query += " WHERE url LIKE %s"
                    params.append(f'%{provider}%')
                
                query += " ORDER BY id DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                stories = cursor.fetchall()
                
                for story in stories:
                    raw_content = story.get('raw_content', {}) or {}
                    raw_text = raw_content.get('text', '') if isinstance(raw_content, dict) else ''
                    
                    analysis = self.classify_story(
                        story['id'],
                        story['title'] or '',
                        story['url'],
                        story['customer_name'],
                        raw_text
                    )
                    
                    # Categorize by classification method
                    if analysis['method'].startswith('tier_1'):
                        results['tier_1_definitive_genai'].append(analysis)
                    elif analysis['method'].startswith('tier_2'):
                        results['tier_2_definitive_traditional'].append(analysis)
                    elif analysis['method'].startswith('tier_3'):
                        results['tier_3_context_resolved'].append(analysis)
                    else:
                        results['tier_4_needs_claude'].append(analysis)
                    
                    results['total_analyzed'] += 1
                
                # Calculate efficiency metrics
                total = results['total_analyzed']
                if total > 0:
                    results['classification_efficiency'] = {
                        'tier_1_rate': len(results['tier_1_definitive_genai']) / total,
                        'tier_2_rate': len(results['tier_2_definitive_traditional']) / total,
                        'tier_3_rate': len(results['tier_3_context_resolved']) / total,
                        'tier_4_rate': len(results['tier_4_needs_claude']) / total,
                        'claude_avoidance_rate': (total - len(results['tier_4_needs_claude'])) / total
                    }
                
        except Exception as e:
            print(f"Error analyzing database stories: {e}")
            import traceback
            traceback.print_exc()
        
        return results