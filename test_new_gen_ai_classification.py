#!/usr/bin/env python3
"""
Test the new two-step Gen AI classification system
"""

import sys
import json
import logging
from datetime import datetime

# Add src to path
sys.path.append('src')

from ai_integration.claude_processor import ClaudeProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gen_ai_classification():
    """Test the Gen AI classification with sample stories"""
    
    processor = ClaudeProcessor()
    
    # Test Case 1: Traditional AI story (2020)
    traditional_ai_story = {
        'text': """
        NextBillion AI Case Study
        
        NextBillion AI is a Singapore-based AI platform provider that helps companies build hyperlocal AI applications without infrastructure investment. They offer NextBillion Maps for location-based experiences and NextBillion Tasks for multilingual text annotation.
        
        The company uses Google Cloud services including Kubernetes Engine, Cloud Storage, Cloud SQL, and Vision AI to process and manage large-scale AI workloads. Their platform provides predictive analytics for location data and automated text processing capabilities.
        
        Key outcomes include 50% reduction in infrastructure costs and improved accuracy in location-based recommendations. The solution handles millions of API calls daily for mapping and geospatial analysis.
        
        Technologies used: Google Kubernetes Engine, Cloud Storage, Cloud SQL, Vision AI, TensorFlow, predictive analytics models.
        """
    }
    
    # Test Case 2: Gen AI story (2023+)
    gen_ai_story = {
        'text': """
        Acme Corp Transforms Customer Service with ChatGPT Integration
        
        Acme Corp implemented OpenAI's GPT-4 to revolutionize their customer service operations in 2023. The company integrated ChatGPT into their support platform to automatically generate responses, create help documentation, and assist agents with complex queries.
        
        The AI system can write personalized email responses, generate troubleshooting guides, and provide natural language interfaces for internal tools. Customer service agents now use AI as a thought partner to brainstorm solutions and research customer issues.
        
        Results include 70% reduction in response time, improved customer satisfaction scores, and the ability to handle 3x more inquiries. The system generates consistent, high-quality content across all customer touchpoints.
        
        Technologies used: OpenAI GPT-4, ChatGPT API, natural language processing, content generation models, conversational AI.
        """
    }
    
    print("🧪 Testing Gen AI Classification System")
    print("=" * 60)
    
    # Test 1: Traditional AI Classification
    print("\n1️⃣ Testing Traditional AI Story (NextBillion AI):")
    print("-" * 50)
    
    try:
        # Test just the classification step
        classification = processor.determine_gen_ai_classification(traditional_ai_story)
        if classification:
            print(f"Classification: {classification['is_gen_ai']}")
            print(f"Confidence: {classification.get('confidence', 'N/A')}")
            print(f"Reasoning: {classification.get('reasoning', 'N/A')}")
            print(f"Key Indicators: {classification.get('key_indicators', [])}")
        else:
            print("❌ Classification failed")
            
        # Test full extraction
        print("\nFull extraction:")
        extracted_data = processor.extract_story_data(traditional_ai_story)
        if extracted_data:
            print(f"✅ AI Type: {extracted_data.get('ai_type', 'N/A')}")
            print(f"✅ Is Gen AI: {extracted_data.get('is_gen_ai', 'N/A')}")
            print(f"✅ Customer: {extracted_data.get('customer_name', 'N/A')}")
            print(f"✅ Technologies: {extracted_data.get('technologies_used', [])}")
            
            # Check that Gen AI fields are NOT present
            gen_ai_fields = ['gen_ai_superpowers', 'business_impacts', 'adoption_enablers']
            for field in gen_ai_fields:
                if field in extracted_data:
                    print(f"❌ ERROR: Traditional AI story has Gen AI field: {field}")
                else:
                    print(f"✅ Correctly missing Gen AI field: {field}")
        else:
            print("❌ Extraction failed")
            
    except Exception as e:
        print(f"❌ Error testing traditional AI: {e}")
    
    # Test 2: Gen AI Classification  
    print("\n\n2️⃣ Testing Gen AI Story (Acme Corp ChatGPT):")
    print("-" * 50)
    
    try:
        # Test just the classification step
        classification = processor.determine_gen_ai_classification(gen_ai_story)
        if classification:
            print(f"Classification: {classification['is_gen_ai']}")
            print(f"Confidence: {classification.get('confidence', 'N/A')}")
            print(f"Reasoning: {classification.get('reasoning', 'N/A')}")
            print(f"Key Indicators: {classification.get('key_indicators', [])}")
        else:
            print("❌ Classification failed")
            
        # Test full extraction
        print("\nFull extraction:")
        extracted_data = processor.extract_story_data(gen_ai_story)
        if extracted_data:
            print(f"✅ AI Type: {extracted_data.get('ai_type', 'N/A')}")
            print(f"✅ Is Gen AI: {extracted_data.get('is_gen_ai', 'N/A')}")
            print(f"✅ Customer: {extracted_data.get('customer_name', 'N/A')}")
            print(f"✅ Technologies: {extracted_data.get('technologies_used', [])}")
            
            # Check that Gen AI fields ARE present
            gen_ai_fields = ['gen_ai_superpowers', 'business_impacts', 'adoption_enablers']
            for field in gen_ai_fields:
                if field in extracted_data and extracted_data[field]:
                    print(f"✅ Has Gen AI field: {field} = {extracted_data[field]}")
                else:
                    print(f"⚠️  Missing or empty Gen AI field: {field}")
        else:
            print("❌ Extraction failed")
            
    except Exception as e:
        print(f"❌ Error testing Gen AI: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test Complete")

if __name__ == "__main__":
    test_gen_ai_classification()