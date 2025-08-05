#!/usr/bin/env python3
"""
Universal Cloud Provider AI Classification Fix

This script applies enhanced classification logic to all major cloud providers:
- Google Cloud, AWS, Microsoft Azure, Anthropic, OpenAI, and others
- Uses definitive indicators to minimize Claude API calls
- Handles provider-specific AI services and platforms
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from src.database.connection import DatabaseConnection
from src.database.models import DatabaseOperations

class UniversalCloudClassifier:
    def __init__(self):
        self.db_ops = DatabaseOperations()
        
        # Modern cloud providers and their domains
        self.cloud_providers = {
            'Google Cloud': ['cloud.google.com', 'developers.google.com/ai'],
            'AWS': ['aws.amazon.com', 'amazon.com/aws'],
            'Microsoft Azure': ['azure.microsoft.com', 'microsoft.com/azure', 'docs.microsoft.com/azure'],
            'Anthropic': ['anthropic.com', 'claude.ai'],
            'OpenAI': ['openai.com', 'platform.openai.com'],
            'Hugging Face': ['huggingface.co'],
            'Cohere': ['cohere.ai', 'cohere.com'],
            'Stability AI': ['stability.ai'],
            'Replicate': ['replicate.com'],
            'Together AI': ['together.ai', 'together.xyz'],
            'Anyscale': ['anyscale.com'],
            'Databricks': ['databricks.com'],
            'Snowflake': ['snowflake.com'],
            'IBM Watson': ['ibm.com/watson', 'ibm.com/cloud'],
            'Oracle Cloud': ['oracle.com/cloud'],
            'Salesforce': ['salesforce.com'],
            'Meta AI': ['ai.meta.com', 'facebook.com/ai']
        }
        
        # Provider-specific GenAI services (definitive indicators)
        self.provider_genai_services = {
            'Google Cloud': [
                'vertex ai', 'vertex-ai', 'vertexai', 'gemini', 'bard', 'palm', 'pathways',
                'dialogflow cx', 'contact center ai', 'document ai', 'translation ai',
                'natural language ai', 'speech synthesis', 'text-to-speech generation'
            ],
            'AWS': [
                'bedrock', 'claude on aws', 'anthropic claude', 'titan', 'jurassic',
                'amazon q', 'codewhisperer', 'comprehend medical', 'textract',
                'polly', 'transcribe medical', 'lex', 'kendra', 'personalize'
            ],
            'Microsoft Azure': [
                'azure openai', 'copilot', 'github copilot', 'cognitive services',
                'azure ai', 'language understanding', 'qna maker', 'bot framework',
                'speech services', 'translator', 'form recognizer', 'personalizer'
            ],
            'Anthropic': [
                'claude', 'claude-3', 'claude-2', 'claude instant', 'constitutional ai',
                'harmlessness', 'helpful assistant'
            ],
            'OpenAI': [
                'gpt-4', 'gpt-3.5', 'chatgpt', 'dall-e', 'whisper', 'codex',
                'embedding', 'fine-tuning', 'completions api', 'chat api'
            ],
            'Hugging Face': [
                'transformers', 'diffusers', 'datasets', 'spaces', 'inference api',
                'hub', 'pipeline', 'model hub'
            ],
            'Cohere': [
                'command', 'embed', 'classify', 'generate', 'rerank', 'summarize'
            ],
            'Databricks': [
                'mlflow', 'delta lake', 'lakehouse', 'unity catalog', 'dolly',
                'databricks ai', 'feature store'
            ],
            'Salesforce': [
                'einstein', 'trailhead', 'mulesoft', 'tableau', 'slack ai',
                'salesforce ai', 'crm ai'
            ]
        }
        
        # Provider-specific Traditional AI services
        self.provider_traditional_services = {
            'Google Cloud': [
                'bigquery analytics', 'cloud storage', 'compute engine', 'kubernetes engine',
                'cloud sql', 'dataflow', 'dataproc', 'cloud functions', 'app engine'
            ],
            'AWS': [
                'ec2', 's3', 'rds', 'lambda', 'cloudformation', 'vpc', 'iam',
                'cloudwatch', 'elb', 'autoscaling', 'redshift analytics'
            ],
            'Microsoft Azure': [
                'virtual machines', 'storage account', 'sql database', 'functions',
                'resource groups', 'virtual network', 'load balancer', 'cosmos db'
            ]
        }
        
        # Universal GenAI indicators (any provider)
        self.universal_genai_indicators = {
            'llm_models': [
                'large language model', 'llm', 'foundation model', 'transformer',
                'gpt', 'bert', 'roberta', 't5', 'bart', 'pegasus'
            ],
            'genai_capabilities': [
                'conversational ai', 'chatbot', 'virtual assistant', 'dialogue system',
                'content generation', 'text generation', 'code generation', 'image generation',
                'natural language generation', 'creative ai', 'generative ai', 'gen ai'
            ],
            'genai_applications': [
                'prompt engineering', 'few-shot learning', 'zero-shot learning',
                'in-context learning', 'chain of thought', 'reasoning', 'summarization',
                'question answering', 'sentiment analysis', 'named entity recognition'
            ]
        }
        
        # Heuristic indicators for modern AI (2022+)
        self.modern_ai_heuristics = {
            'modern_terms': [
                ('personalization', 0.6), ('intelligent automation', 0.7),
                ('ai-powered', 0.5), ('ml-driven', 0.4), ('predictive analytics', 0.3),
                ('recommendation engine', 0.4), ('anomaly detection', 0.3),
                ('computer vision', 0.4), ('natural language processing', 0.5)
            ],
            'timeframe': [
                ('2022', 0.2), ('2023', 0.4), ('2024', 0.6), ('2025', 0.7)
            ],
            'partnership_context': [
                ('ai innovation', 0.5), ('digital transformation', 0.3),
                ('next-generation', 0.4), ('cutting-edge', 0.4)
            ]
        }
    
    def identify_provider(self, url: str) -> Optional[str]:
        """Identify cloud provider from URL"""
        url_lower = url.lower()
        for provider, domains in self.cloud_providers.items():
            for domain in domains:
                if domain in url_lower:
                    return provider
        return None
    
    def analyze_story(self, story_id: int, title: str, url: str, customer: str, source: str) -> Dict:
        """Analyze a story for any cloud provider"""
        full_text = f"{title} {url}".lower()
        provider = self.identify_provider(url) or source
        
        # Check provider-specific GenAI services
        provider_genai = self._check_provider_services(full_text, provider, self.provider_genai_services)
        if provider_genai:
            return {
                'story_id': story_id,
                'customer': customer,
                'provider': provider,
                'recommendation': 'GenAI',
                'confidence': 1.0,
                'method': 'provider_definitive',
                'indicators': provider_genai,
                'requires_claude': False
            }
        
        # Check universal GenAI indicators
        universal_genai = self._check_universal_indicators(full_text, self.universal_genai_indicators)
        if universal_genai:
            return {
                'story_id': story_id,
                'customer': customer,
                'provider': provider,
                'recommendation': 'GenAI',
                'confidence': 0.9,
                'method': 'universal_genai',
                'indicators': universal_genai,
                'requires_claude': False
            }
        
        # Check provider-specific Traditional AI services
        provider_traditional = self._check_provider_services(full_text, provider, self.provider_traditional_services)
        if provider_traditional:
            return {
                'story_id': story_id,
                'customer': customer,
                'provider': provider,
                'recommendation': 'Traditional',
                'confidence': 0.8,
                'method': 'provider_traditional',
                'indicators': provider_traditional,
                'requires_claude': False
            }
        
        # Heuristic analysis
        heuristic_score = self._calculate_heuristic_score(full_text)
        
        if heuristic_score['genai_confidence'] >= 0.7:
            return {
                'story_id': story_id,
                'customer': customer,
                'provider': provider,
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
                'provider': provider,
                'recommendation': 'Traditional',
                'confidence': 1.0 - heuristic_score['genai_confidence'],
                'method': 'heuristic',
                'indicators': heuristic_score['indicators'],
                'requires_claude': False
            }
        else:
            return {
                'story_id': story_id,
                'customer': customer,
                'provider': provider,
                'recommendation': 'Unclear',
                'confidence': 0.5,
                'method': 'needs_claude',
                'indicators': heuristic_score['indicators'],
                'requires_claude': True
            }
    
    def _check_provider_services(self, text: str, provider: str, service_dict: Dict) -> List[str]:
        """Check for provider-specific services"""
        if provider not in service_dict:
            return []
        
        found_services = []
        for service in service_dict[provider]:
            if service in text:
                found_services.append(f"{provider}:{service}")
        return found_services
    
    def _check_universal_indicators(self, text: str, indicator_dict: Dict) -> List[str]:
        """Check for universal GenAI indicators"""
        found_indicators = []
        for category, terms in indicator_dict.items():
            for term in terms:
                if term in text:
                    found_indicators.append(f"universal:{category}:{term}")
        return found_indicators
    
    def _calculate_heuristic_score(self, text: str) -> Dict:
        """Calculate GenAI probability using heuristic indicators"""
        total_score = 0.0
        found_indicators = []
        
        for category, terms in self.modern_ai_heuristics.items():
            for term, weight in terms:
                if term in text:
                    total_score += weight
                    found_indicators.append(f"heuristic:{category}:{term}({weight})")
        
        genai_confidence = min(total_score / 2.0, 1.0)
        
        return {
            'genai_confidence': genai_confidence,
            'indicators': found_indicators
        }
    
    def analyze_all_providers(self) -> Dict:
        """Analyze stories from all cloud providers"""
        print("🌐 Analyzing stories from all cloud providers...")
        
        results = {
            'by_provider': {},
            'definitive_fixes': [],
            'needs_claude': [],
            'total_analyzed': 0
        }
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                # Get all stories (not just Google Cloud)
                cursor.execute("""
                    SELECT id, customer_name, title, url, source, is_gen_ai
                    FROM customer_stories 
                    ORDER BY source, id DESC
                """)
                stories = cursor.fetchall()
                
                for story in stories:
                    analysis = self.analyze_story(
                        story['id'],
                        story['title'] or '',
                        story['url'],
                        story['customer_name'],
                        story['source']
                    )
                    
                    provider = analysis['provider']
                    if provider not in results['by_provider']:
                        results['by_provider'][provider] = {
                            'total': 0,
                            'definitive_fixes': [],
                            'needs_claude': [],
                            'already_correct': 0
                        }
                    
                    results['by_provider'][provider]['total'] += 1
                    results['total_analyzed'] += 1
                    
                    current_classification = story['is_gen_ai']
                    recommended_genai = analysis['recommendation'] == 'GenAI'
                    
                    if (analysis['confidence'] >= 0.8 and 
                        current_classification != recommended_genai):
                        results['definitive_fixes'].append(analysis)
                        results['by_provider'][provider]['definitive_fixes'].append(analysis)
                    elif analysis['requires_claude']:
                        results['needs_claude'].append(analysis)
                        results['by_provider'][provider]['needs_claude'].append(analysis)
                    else:
                        results['by_provider'][provider]['already_correct'] += 1
                
        except Exception as e:
            print(f"Error analyzing stories: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def fix_definitive_misclassifications(self, max_fixes: int = 50) -> List[Dict]:
        """Fix definitive misclassifications across all providers"""
        print("🔧 Fixing definitive misclassifications across all providers...")
        
        results = self.analyze_all_providers()
        fixes_to_apply = results['definitive_fixes'][:max_fixes]
        
        if not fixes_to_apply:
            print("✅ No definitive misclassifications found!")
            return []
        
        fixed_stories = []
        
        try:
            with self.db_ops.db.get_cursor() as cursor:
                for fix in fixes_to_apply:
                    recommended_genai = fix['recommendation'] == 'GenAI'
                    
                    print(f"Fixing {fix['provider']} Story ID {fix['story_id']}: {fix['customer']}")
                    print(f"  Current: {'GenAI' if not recommended_genai else 'Traditional'} → New: {fix['recommendation']}")
                    print(f"  Confidence: {fix['confidence']:.2f} | Method: {fix['method']}")
                    print(f"  Indicators: {fix['indicators'][:2]}...")
                    
                    # Update the database
                    cursor.execute("""
                        UPDATE customer_stories 
                        SET is_gen_ai = %s 
                        WHERE id = %s
                    """, (recommended_genai, fix['story_id']))
                    
                    fixed_stories.append(fix)
                    print("  ✅ Updated in database")
                    print()
                
                # Commit changes
                cursor.connection.commit()
                print(f"✅ Successfully fixed {len(fixed_stories)} stories across all providers")
                
        except Exception as e:
            print(f"Error fixing classifications: {e}")
            import traceback
            traceback.print_exc()
        
        return fixed_stories

def main():
    """Main execution"""
    print("🚀 Universal Cloud Provider AI Classification Analysis")
    print("=" * 80)
    
    classifier = UniversalCloudClassifier()
    
    # Step 1: Analyze all providers
    results = classifier.analyze_all_providers()
    
    print(f"\n📊 ANALYSIS RESULTS ACROSS ALL PROVIDERS:")
    print(f"  Total stories analyzed: {results['total_analyzed']}")
    print(f"  Definitive fixes needed: {len(results['definitive_fixes'])}")
    print(f"  Stories needing Claude: {len(results['needs_claude'])}")
    
    # Step 2: Show breakdown by provider
    print(f"\n📋 BREAKDOWN BY PROVIDER:")
    for provider, data in results['by_provider'].items():
        if data['total'] > 0:
            fixes_needed = len(data['definitive_fixes'])
            claude_needed = len(data['needs_claude'])
            print(f"  {provider}:")
            print(f"    Total stories: {data['total']}")
            print(f"    Fixes needed: {fixes_needed}")
            print(f"    Need Claude: {claude_needed}")
            print(f"    Already correct: {data['already_correct']}")
    
    # Step 3: Show top misclassifications
    if results['definitive_fixes']:
        print(f"\n🔧 TOP DEFINITIVE FIXES NEEDED:")
        for i, fix in enumerate(results['definitive_fixes'][:10]):
            print(f"  {i+1}. {fix['provider']} ID {fix['story_id']}: {fix['customer'][:40]}...")
            print(f"     → {fix['recommendation']} (confidence: {fix['confidence']:.2f})")
    
    # Step 4: Apply fixes
    print(f"\n🔧 APPLYING DEFINITIVE FIXES...")
    fixed_stories = classifier.fix_definitive_misclassifications()
    
    # Step 5: Calculate efficiency metrics
    total_needing_attention = len(results['definitive_fixes']) + len(results['needs_claude'])
    if total_needing_attention > 0:
        efficiency = ((len(results['definitive_fixes'])) / total_needing_attention) * 100
        claude_reduction = (1 - len(results['needs_claude']) / total_needing_attention) * 100
        
        print(f"\n💡 EFFICIENCY METRICS:")
        print(f"  Automatic fixes applied: {len(fixed_stories)}")
        print(f"  Automatic classification rate: {efficiency:.1f}%")
        print(f"  Claude API call reduction: {claude_reduction:.1f}%")
        print(f"  Stories still needing Claude: {len(results['needs_claude'])}")

if __name__ == "__main__":
    main()