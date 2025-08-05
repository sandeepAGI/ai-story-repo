#!/usr/bin/env python3
"""
Refined Claude Prompt for AI Classification

This creates an improved prompt that addresses the accuracy issues
identified in our analysis, particularly around virtual assistants,
chatbots, and other ambiguous AI terms.
"""

REFINED_GEN_AI_DETERMINATION_PROMPT = """
Analyze this AI customer story and determine if it describes Generative AI or Traditional AI technology.

**CRITICAL: Use evidence-based classification, not just keywords**

**DEFINITIVE Generative AI (GenAI) indicators:**
- **LLM Platforms**: Vertex AI, Gemini, GPT-4/3.5, Claude, ChatGPT, Bard, PaLM, LLaMA
- **Generative Technologies**: Large Language Models, Foundation Models, Transformer Models
- **Generative Capabilities**: Content generation, text generation, code generation, creative writing, natural language generation
- **Modern GenAI Services**: Vertex AI Search, Gemini API, Document AI with generation, AI-powered content creation

**DEFINITIVE Traditional AI indicators:**
- **Classic ML**: AutoML Tables, supervised learning models, classification/regression only, clustering
- **Rule-based Systems**: Decision trees, if-then logic, scripted responses, keyword matching
- **Traditional Analytics**: BigQuery analytics, data warehousing, business intelligence dashboards
- **Traditional Services**: Cloud Vision OCR, Speech-to-Text API, basic recommendation engines

**AMBIGUOUS terms requiring evidence (DO NOT auto-classify):**
- **Virtual Assistant**: Could be rule-based (Traditional) OR LLM-powered (GenAI)
- **Chatbot**: Could be scripted (Traditional) OR conversational AI (GenAI)  
- **Document Processing**: Could be OCR (Traditional) OR AI generation (GenAI)
- **Speech Recognition**: Could be basic STT (Traditional) OR conversational (GenAI)
- **Personalization**: Could be basic recommendations (Traditional) OR AI-generated content (GenAI)

**For ambiguous terms, look for EVIDENCE:**

*GenAI Evidence:*
- Mentions LLM platforms (Vertex AI, Gemini, GPT, etc.)
- Generative capabilities (creates content, writes text, generates responses)
- Natural conversation, contextual understanding, creative responses
- Modern timeframe (2023+) with advanced AI features
- Terms: "prompt engineering", "foundation models", "conversational AI", "generates"

*Traditional AI Evidence:*
- Rule-based logic, predefined responses, decision trees
- Classification/prediction only, no content generation
- Keyword matching, template responses, scripted interactions
- Statistical analysis, pattern matching, supervised learning
- Terms: "rule-based", "scripted", "predefined", "classification model"

**Decision Framework:**
1. **Check for definitive indicators first** → Classify immediately
2. **If ambiguous terms found** → Look for supporting evidence
3. **Strong evidence present** → Classify with medium confidence
4. **Insufficient evidence** → Mark as unclear/requires human review

**Timeline Context:**
- Pre-2022: Likely Traditional AI unless definitive GenAI evidence
- 2023+: Could be either, examine specific technologies mentioned
- Don't assume recency = GenAI without supporting evidence

**Story content to analyze:**
{story_content}

**Return only a JSON object:**
{{
  "is_gen_ai": true/false,
  "confidence": 0.0-1.0,
  "classification_method": "definitive_genai|definitive_traditional|evidence_based_genai|evidence_based_traditional|insufficient_evidence",
  "reasoning": "Detailed explanation of the determination with specific evidence cited",
  "key_indicators": ["List of specific technologies, platforms, or capabilities that influenced the decision"],
  "ambiguous_terms_found": ["List any ambiguous terms that required evidence analysis"],
  "supporting_evidence": ["List of evidence that helped resolve ambiguous terms"],
  "confidence_factors": {{
    "definitive_indicators": ["Clear GenAI or Traditional indicators found"],
    "supporting_context": ["Additional context that supports classification"],
    "uncertainty_factors": ["Any factors that create doubt about classification"]
  }}
}}
"""

def test_refined_prompt():
    """Test the refined prompt against problematic cases"""
    
    test_cases = [
        {
            'title': 'Wells Fargo Virtual Assistant',
            'content': 'Wells Fargo virtual assistant uses AI and cloud to support meaningful financial conversations anytime, anywhere. The assistant helps customers with banking queries and financial advice.',
            'expected_classification': 'insufficient_evidence',
            'expected_confidence': 'low',
            'reasoning': 'Virtual assistant mentioned but no evidence of LLM/GenAI technology'
        },
        {
            'title': 'Gemini-powered Virtual Assistant',
            'content': 'Company implements virtual assistant powered by Gemini to provide conversational AI customer support with natural language understanding and response generation.',
            'expected_classification': 'definitive_genai',
            'expected_confidence': 'high',
            'reasoning': 'Gemini is definitive GenAI platform'
        },
        {
            'title': 'Rule-based Chatbot',
            'content': 'Customer service chatbot uses rule-based logic with predefined responses and keyword matching to handle common customer inquiries through scripted interactions.',
            'expected_classification': 'definitive_traditional',
            'expected_confidence': 'high',
            'reasoning': 'Rule-based, predefined responses, scripted = Traditional AI'
        },
        {
            'title': 'Basic Document OCR',
            'content': 'Document processing system uses Cloud Vision API for text extraction and form field recognition to digitize paper documents.',
            'expected_classification': 'evidence_based_traditional',
            'expected_confidence': 'medium',
            'reasoning': 'Document processing with OCR evidence = Traditional'
        },
        {
            'title': 'Vertex AI Document Generation',
            'content': 'Document processing with Vertex AI to generate summaries and create new content based on extracted information from legal documents.',
            'expected_classification': 'definitive_genai',
            'expected_confidence': 'high',
            'reasoning': 'Vertex AI + content generation = Definitive GenAI'
        }
    ]
    
    print("🧪 Testing Refined Claude Prompt")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['title']}")
        print(f"   Content: {case['content']}")
        print(f"   Expected: {case['expected_classification']} ({case['expected_confidence']} confidence)")
        print(f"   Reasoning: {case['reasoning']}")
    
    print(f"\n💡 KEY PROMPT IMPROVEMENTS:")
    print("1. ✅ Explicitly warns against auto-classifying ambiguous terms")
    print("2. ✅ Requires evidence for virtual assistants, chatbots, etc.")
    print("3. ✅ Provides clear evidence categories for GenAI vs Traditional")
    print("4. ✅ Includes decision framework with step-by-step process")
    print("5. ✅ Adds detailed JSON response structure with confidence factors")
    print("6. ✅ Emphasizes timeline context without assuming recency = GenAI")

def main():
    """Display the refined prompt and test cases"""
    print("🚀 Refined Claude Prompt for AI Classification")
    print("=" * 60)
    
    print("\n📝 REFINED PROMPT STRUCTURE:")
    print("1. Definitive indicators (high confidence classification)")
    print("2. Ambiguous terms requiring evidence")
    print("3. Evidence categories for resolving ambiguity")
    print("4. Decision framework with clear steps")
    print("5. Enhanced JSON response with confidence factors")
    
    test_refined_prompt()
    
    print(f"\n✅ NEXT STEPS:")
    print("1. Update src/ai_integration/prompts.py with refined prompt")
    print("2. Test refined classification on Wells Fargo case")
    print("3. Validate improved accuracy before universal rollout")
    print("4. Document classification methodology for future reference")

if __name__ == "__main__":
    main()