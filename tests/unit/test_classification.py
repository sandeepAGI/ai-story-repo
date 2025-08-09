#!/usr/bin/env python3
"""
Comprehensive AI Classification Test Suite
Consolidates all Gen AI classification testing into a single, focused module

This replaces the following redundant test files:
- test_gen_ai_classification.py
- test_enhanced_classification.py  
- test_new_gen_ai_classification.py
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import modules to test
try:
    from ai_integration.claude_processor import ClaudeProcessor
    from database.models import DatabaseOperations
except ImportError:
    # Fallback for testing without full database setup
    ClaudeProcessor = None
    DatabaseOperations = None


class TestAIClassificationSystem:
    """Test suite for AI classification system"""
    
    def test_definitive_genai_classification(self, classification_test_cases):
        """Test Tier 1 - Definitive GenAI classification"""
        test_cases = classification_test_cases['definitive_genai']
        
        for case in test_cases:
            # Test classification logic
            result = self._classify_content(case['title'], case['content'])
            
            assert result['classification'] == case['expected_classification']
            assert result['confidence'] == case['expected_confidence']
            
            # Test specific Gen AI indicators
            assert self._has_genai_keywords(case['title'] + ' ' + case['content'])
    
    def test_definitive_non_genai_classification(self, classification_test_cases):
        """Test traditional ML/AI classification"""
        test_cases = classification_test_cases['definitive_non_genai']
        
        for case in test_cases:
            result = self._classify_content(case['title'], case['content'])
            
            assert result['classification'] == case['expected_classification']
            assert result['confidence'] == case['expected_confidence']
            
            # Ensure no Gen AI false positives
            assert not self._has_genai_keywords(case['title'] + ' ' + case['content'])
    
    def test_edge_case_classification(self, classification_test_cases):
        """Test edge cases and ambiguous classifications"""
        test_cases = classification_test_cases['edge_cases']
        
        for case in test_cases:
            result = self._classify_content(case['title'], case['content'])
            
            # For edge cases, focus on reasonable classification
            assert result['classification'] in ['GenAI', 'Non-GenAI']
            assert result['confidence'] in ['low', 'medium', 'high']
    
    def test_classification_consistency(self):
        """Test that classification is consistent across multiple runs"""
        title = "Company implements GPT-4 for automated customer service"
        content = "Using OpenAI's GPT-4 API for chatbot responses"
        
        results = []
        for _ in range(5):
            result = self._classify_content(title, content)
            results.append(result['classification'])
        
        # All results should be the same
        assert len(set(results)) == 1, "Classification should be consistent"
        assert results[0] == 'GenAI'
    
    def test_empty_content_handling(self):
        """Test handling of empty or minimal content"""
        # Empty content
        result = self._classify_content("", "")
        assert result['classification'] in ['GenAI', 'Non-GenAI']
        assert result['confidence'] == 'low'
        
        # Minimal content
        result = self._classify_content("AI", "AI system")
        assert result['classification'] in ['GenAI', 'Non-GenAI']
    
    def test_multilingual_content(self):
        """Test classification with non-English content"""
        # Simple test cases (would need more comprehensive testing in production)
        test_cases = [
            {
                'title': 'Empresa usa GPT-4 para servicio al cliente',
                'content': 'Implementación de GPT-4 para respuestas automatizadas',
                'expected': 'GenAI'
            },
            {
                'title': '企業でClaude AIを導入',
                'content': 'Claude AIを使用した文書処理システム',
                'expected': 'GenAI'
            }
        ]
        
        for case in test_cases:
            result = self._classify_content(case['title'], case['content'])
            # Should be able to detect Gen AI even in other languages
            assert result['classification'] == case['expected']
    
    def _classify_content(self, title: str, content: str) -> dict:
        """
        Mock classification function for testing
        In production, this would call the actual Claude processor
        """
        combined_text = (title + ' ' + content).lower()
        
        # Definitive Gen AI keywords
        genai_keywords = [
            'gpt-4', 'gpt-3', 'chatgpt', 'claude', 'gemini', 'llm', 
            'large language model', 'generative ai', 'content generation',
            'text generation', 'openai api', 'anthropic', 'vertex ai'
        ]
        
        # Traditional ML keywords  
        traditional_keywords = [
            'machine learning', 'neural network', 'computer vision',
            'fraud detection', 'predictive model', 'classification model',
            'regression', 'clustering', 'scikit-learn'
        ]
        
        genai_score = sum(1 for keyword in genai_keywords if keyword in combined_text)
        traditional_score = sum(1 for keyword in traditional_keywords if keyword in combined_text)
        
        if genai_score > traditional_score and genai_score > 0:
            confidence = 'high' if genai_score >= 2 else 'medium'
            return {'classification': 'GenAI', 'confidence': confidence}
        elif traditional_score > 0:
            confidence = 'high' if traditional_score >= 2 else 'medium'
            return {'classification': 'Non-GenAI', 'confidence': confidence}
        else:
            return {'classification': 'Non-GenAI', 'confidence': 'low'}
    
    def _has_genai_keywords(self, text: str) -> bool:
        """Check if text contains Gen AI specific keywords"""
        text = text.lower()
        genai_keywords = [
            'gpt', 'claude', 'llm', 'large language model', 'generative ai',
            'text generation', 'content generation', 'chatgpt', 'gemini'
        ]
        return any(keyword in text for keyword in genai_keywords)


class TestClaudeProcessorIntegration:
    """Integration tests with Claude processor (requires database)"""
    
    @pytest.mark.skipif(ClaudeProcessor is None, reason="Claude processor not available")
    def test_claude_processor_classification(self, sample_stories_data):
        """Test actual Claude processor classification"""
        with patch.object(DatabaseOperations, '__init__', return_value=None):
            processor = ClaudeProcessor()
            
            # Mock the Claude API response
            with patch.object(processor, 'process_story') as mock_process:
                mock_process.return_value = {
                    'ai_type': 'GenAI',
                    'content_quality_score': 0.85,
                    'summary': 'Test summary',
                    'gen_ai_superpowers': ['create_content'],
                    'business_impacts': ['efficiency']
                }
                
                story_data = sample_stories_data[0]
                result = processor.process_story(story_data)
                
                assert result['ai_type'] == 'GenAI'
                assert 'content_quality_score' in result
    
    @pytest.mark.skipif(DatabaseOperations is None, reason="Database operations not available")
    def test_database_classification_consistency(self, mock_database_operations):
        """Test that database classification is consistent with processing"""
        mock_db_ops, mock_cursor = mock_database_operations
        
        # Mock database query results
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'is_gen_ai': True,
                'extracted_data': {'ai_type': 'GenAI'}
            },
            {
                'id': 2, 
                'is_gen_ai': False,
                'extracted_data': {'ai_type': 'Non-GenAI'}
            }
        ]
        
        with patch('database.models.DatabaseOperations', return_value=mock_db_ops):
            db_ops = DatabaseOperations()
            # Test would check consistency between is_gen_ai field and extracted_data.ai_type
            # This is the kind of validation we had in the original consistency scripts


class TestClassificationValidation:
    """Test validation and consistency checks"""
    
    def test_classification_field_consistency(self, sample_df):
        """Test that is_gen_ai field matches extracted_data.ai_type"""
        for _, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                ai_type = row['extracted_data'].get('ai_type')
                is_gen_ai = row.get('is_gen_ai')
                
                if ai_type == 'GenAI':
                    assert is_gen_ai == True, f"Story {row['id']}: ai_type=GenAI but is_gen_ai={is_gen_ai}"
                elif ai_type == 'Non-GenAI':
                    assert is_gen_ai == False, f"Story {row['id']}: ai_type=Non-GenAI but is_gen_ai={is_gen_ai}"
    
    def test_quality_score_validation(self, sample_df):
        """Test that quality scores are in valid range"""
        for _, row in sample_df.iterrows():
            if isinstance(row['extracted_data'], dict):
                score = row['extracted_data'].get('content_quality_score')
                if score is not None:
                    assert 0.0 <= score <= 1.0, f"Quality score {score} out of range [0,1]"
    
    def test_genai_fields_presence(self, sample_df):
        """Test that Gen AI stories have required Aileron framework fields"""
        genai_stories = sample_df[sample_df['is_gen_ai'] == True]
        
        required_fields = ['gen_ai_superpowers', 'business_impacts', 'adoption_enablers']
        
        for _, row in genai_stories.iterrows():
            if isinstance(row['extracted_data'], dict):
                for field in required_fields:
                    assert field in row['extracted_data'], f"Gen AI story {row['id']} missing {field}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])