GEN_AI_DETERMINATION_PROMPT = """
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

**Return only a valid JSON object with proper formatting:**

CRITICAL JSON FORMATTING RULES:
- All array elements must be quoted strings only
- No unquoted parenthetical comments in arrays  
- No trailing commas
- Use proper JSON syntax throughout

{{
  "is_gen_ai": true/false,
  "confidence": 0.0-1.0,
  "classification_method": "definitive_genai|definitive_traditional|evidence_based_genai|evidence_based_traditional|insufficient_evidence",
  "reasoning": "Detailed explanation of the determination with specific evidence cited",
  "key_indicators": ["Technology 1", "Technology 2", "Capability 3"],
  "ambiguous_terms_found": ["AI", "Virtual Assistant", "Chatbot"],
  "supporting_evidence": ["Evidence 1", "Evidence 2", "Evidence 3"],
  "confidence_factors": {{
    "definitive_indicators": ["Indicator 1", "Indicator 2"],
    "supporting_context": ["Context 1", "Context 2"],
    "uncertainty_factors": ["Uncertainty 1", "Uncertainty 2"]
  }}
}}

EXAMPLE - Correct array formatting:
✅ CORRECT: "ambiguous_terms_found": ["AI", "Virtual Assistant"]
❌ INCORRECT: "ambiguous_terms_found": ["AI" (generic mention), "Virtual Assistant"]
"""

EXTRACTION_PROMPT = """
Analyze this AI customer story and extract structured information. Return a valid JSON object with the following structure:

{{
  "customer_name": "Company name",
  "industry": "Industry sector (e.g., healthcare, finance, technology, retail, manufacturing, etc.)",
  "company_size": "startup, mid-market, enterprise, or government",  
  "summary": "2-3 sentence summary of the story",
  "problem_statement": "What challenge or problem did the customer face?",
  "solution_description": "How did AI/cloud services solve the problem?",
  "technologies_used": ["List of specific AI services, models, or technologies mentioned"],
  "business_outcomes": [
    {{
      "type": "cost_reduction|time_savings|revenue_increase|productivity_gain|efficiency_improvement|accuracy_improvement|other",
      "value": numeric_value_if_available,
      "unit": "percent|dollars|hours|minutes|days|x_times_faster|other",
      "description": "Detailed description of the outcome"
    }}
  ],
  "use_cases": ["List of AI use case categories like customer_service, document_processing, automation, analytics, etc."],
  "key_quote": "Most impactful customer quote from the story (if available)",
  "implementation_timeline": "How long implementation took (if mentioned)",
  "company_info": {{
    "estimated_size": "startup|mid-market|enterprise|government",
    "industry_sector": "More specific industry classification", 
    "geography": "Geographic region if mentioned (e.g., north_america, europe, asia, global)"
  }},
  "content_quality_score": 0.0-1.0,
  "estimated_publish_date": "YYYY-MM-DD or null if no date context available",
  "date_confidence": "high|medium|low - confidence in estimated date",
  "date_reasoning": "Brief explanation of how date was estimated",
  "gen_ai_superpowers": ["List from: code, create_content, automate_with_agents, find_data_insights, research, brainstorm, natural_language"],
  "superpowers_other": "Description of novel capabilities not in predefined list (null if none)",
  "business_impacts": ["List from: innovation, efficiency, speed, quality, client_satisfaction, risk_reduction"],
  "impacts_other": "Description of unique business benefits not in predefined list (null if none)",
  "adoption_enablers": ["List from: data_and_digital, innovation_culture, ecosystem_partners, policy_and_governance, risk_management"],
  "enablers_other": "Description of unique organizational factors not in predefined list (null if none)",
  "business_function": "Primary function from: marketing, sales, production, distribution, service, finance_and_accounting",
  "function_other": "Description if cross-functional or unique departmental use (null if fits predefined)",
  "classification_confidence": {{
    "superpowers": 0.0-1.0,
    "impacts": 0.0-1.0,
    "enablers": 0.0-1.0,
    "function": 0.0-1.0
  }},
  "last_processed": "timestamp",
  "ai_type": "generative"
}}

Guidelines for extraction:
1. Focus on extracting specific, quantified business outcomes and metrics
2. If numeric values are mentioned (like "50% reduction" or "$2M savings"), include them in business_outcomes
3. Be conservative with company_size estimation - use available context clues
4. For content_quality_score: 1.0 = very detailed with specific metrics, 0.5 = moderate detail, 0.0 = vague or minimal content
5. If information is not available, use null or empty arrays appropriately
6. Extract ALL technologies mentioned, including specific AI models, cloud services, databases, etc.
7. Use lowercase with underscores for categorical values (e.g., "customer_service" not "Customer Service")
8. For estimated_publish_date: Look for date clues in content like:
   - "In 2023, we implemented..." or "Since early 2024..."
   - Technology releases mentioned (e.g., "using GPT-4" suggests 2023+, "Claude 3" suggests 2024+)
   - Events referenced (conferences, product launches, etc.)
   - Business context (pandemic references suggest 2020-2022, etc.)
   - If no date context exists, use null
9. Date confidence levels:
   - high: Explicit dates or clear time references in content
   - medium: Technology timeline or contextual clues provide reasonable estimate
   - low: Vague indicators or educated guess based on technology maturity

10. Gen AI Classification Guidelines (Aileron GenAI SuperPowers Framework):
    **Superpowers** - What AI capabilities are being used:
    - code: Design, develop, test and deploy working applications using GenAI tools like Claude Code and GitHub CoPilot to write, understand, test, and optimize code across the software development lifecycle
    - create_content: Write, illustrate, and produce original or derivative works, such as emails, articles, ads, videos, and graphics, using GenAI tools
    - automate_with_agents: Train AI agents to autonomously perform repetitive and manual tasks, make intelligent recommendations, and apply contextual judgment at scale - leveraging natural language, learning capabilities, and low-code/no-code visual tools for seamless integration and control
    - find_data_insights: Explore your data using natural language prompts to search, summarize, analyze and create dynamic reports and graphics to represent new insights
    - research: Guide AI Agents to structure, conduct, synthesize and validate research using curated sources of information or the resources of the internet - while maintaining relevance, reliability, and transparency
    - brainstorm: Use AI as a thought partner to explore challenging problems or ideas - quickly generating hypotheses, testing them with public or private data, and designing a systematic path to informed decisions
    - natural_language: GenAI tools increasingly offer the ability to add a natural language interface to almost any technology or experience. If you can say it, you can probably get AI to help you do it
    
    **Business Impacts** - What outcomes were achieved:
    - innovation: Create new revenue streams by developing novel products, services, or business models. Enhance delivery capabilities to support rapid scale and differentiated value
    - efficiency: Lower the cost of delivering products and services through automation, simplification, scalable operations, and optimized resource allocation
    - speed: Accelerate time to value by enabling faster decision-making, shortening cycle times, and automating key processes
    - quality: Improve the consistency and reliability of deliverables through enhanced review, validation, and quality assurance mechanisms
    - client_satisfaction: Enhance client satisfaction by delivering more personalized, responsive, and high-value experiences across products and services
    - risk_reduction: Reduce business and operational risk by improving the design, execution, and real-time monitoring of processes, performance, and controls
    
    **Adoption Enablers** - What organizational factors enabled success:
    - data_and_digital: Understanding your data estate, making it secure and accessible to clients and employees via digital tools and channels is often a prerequisite to AI excellence. Perfection is often the enemy of the good, though
    - innovation_culture: AI innovation thrives on experimentation and experiential learning. Teams and Individuals must be empowered to explore new ideas, take calculated risks, and learn from failure in a supportive environment
    - ecosystem_partners: The wide and expanding range of AI solutions and service providers is overwhelming, and progress often depends on making a few key decisions about the tools and resources you will need to transform your business. Managing vendor risk and relationships is becoming more critical every day
    - policy_and_governance: Clear policies and governance frameworks are essential to guide responsible AI use. From defining acceptable use and data handling standards to managing transparency and accountability, strong governance builds trust and protects the business
    - risk_management: Adopting AI at scale requires reevaluating risks across data privacy, model bias, regulatory compliance, and operational integrity. Robust risk management not only ensures effective AI outcomes, but is also essential for building and maintaining trust with all key stakeholders
    
    **Business Function** - Which department/area benefited (choose PRIMARY):
    - marketing: Brand, campaigns, content marketing, market research
    - sales: Lead generation, customer acquisition, sales processes
    - production: Manufacturing, operations, supply chain, quality control
    - distribution: Logistics, delivery, inventory management
    - service: Customer support, technical service, maintenance
    - finance_and_accounting: Financial analysis, accounting, reporting, budgeting

11. **CRITICAL: "Other" Field Usage Guidelines (USE SPARINGLY)**:
    - **Only use "other" fields for truly novel capabilities** that don't fit ANY existing category
    - **Strongly prefer existing categories** - try to fit capabilities into predefined lists first
    - **"Other" must be similar in spirit** to existing categories in that dimension
    - **Examples of what should NOT go in "other":**
      - "Travel planning/recommendations" → use `find_data_insights`
      - "Process automation" → use `automate_with_agents`
      - "Cross-functional impact" → pick the PRIMARY function, don't use function_other
      - "Content generation for marketing" → use `create_content`
      - "Customer analytics" → use `find_data_insights`
    - **Valid "other" examples** (rare cases only):
      - Entirely new AI capabilities not covered by the 7 superpowers
      - Novel business impacts beyond the 6 standard categories
      - Unique organizational factors not in the 5 enabler categories
      - Business functions genuinely outside the 6 standard departments

12. Classification confidence scoring:
    - 1.0: Very clear evidence in story content
    - 0.7-0.9: Strong indicators and context clues
    - 0.4-0.6: Some evidence but requires interpretation
    - 0.0-0.3: Weak evidence or educated guess

Story content to analyze:

{story_content}

Return only the JSON object, no additional text or explanation.
"""

TRADITIONAL_AI_EXTRACTION_PROMPT = """
Analyze this Traditional AI customer story and extract structured information. Return a valid JSON object with the following structure:

{{
  "customer_name": "Company name",
  "industry": "Industry sector (e.g., healthcare, finance, technology, retail, manufacturing, etc.)",
  "company_size": "startup, mid-market, enterprise, or government",  
  "summary": "2-3 sentence summary of the story",
  "problem_statement": "What challenge or problem did the customer face?",
  "solution_description": "How did AI/ML/cloud services solve the problem?",
  "technologies_used": ["List of specific AI services, models, or technologies mentioned"],
  "business_outcomes": [
    {{
      "type": "cost_reduction|time_savings|revenue_increase|productivity_gain|efficiency_improvement|accuracy_improvement|other",
      "value": numeric_value_if_available,
      "unit": "percent|dollars|hours|minutes|days|x_times_faster|other",
      "description": "Detailed description of the outcome"
    }}
  ],
  "use_cases": ["List of AI use case categories like customer_service, document_processing, automation, analytics, etc."],
  "key_quote": "Most impactful customer quote from the story (if available)",
  "implementation_timeline": "How long implementation took (if mentioned)",
  "company_info": {{
    "estimated_size": "startup|mid-market|enterprise|government",
    "industry_sector": "More specific industry classification", 
    "geography": "Geographic region if mentioned (e.g., north_america, europe, asia, global)"
  }},
  "content_quality_score": 0.0-1.0,
  "estimated_publish_date": "YYYY-MM-DD or null if no date context available",
  "date_confidence": "high|medium|low - confidence in estimated date",
  "date_reasoning": "Brief explanation of how date was estimated",
  "ai_type": "traditional",
  "last_processed": "timestamp"
}}

Guidelines for extraction:
1. Focus on extracting specific, quantified business outcomes and metrics
2. If numeric values are mentioned (like "50% reduction" or "$2M savings"), include them in business_outcomes
3. Be conservative with company_size estimation - use available context clues
4. For content_quality_score: 1.0 = very detailed with specific metrics, 0.5 = moderate detail, 0.0 = vague or minimal content
5. If information is not available, use null or empty arrays appropriately
6. Extract ALL technologies mentioned, including specific AI models, cloud services, databases, etc.
7. Use lowercase with underscores for categorical values (e.g., "customer_service" not "Customer Service")
8. For estimated_publish_date: Look for date clues in content like:
   - "In 2023, we implemented..." or "Since early 2024..."
   - Technology releases mentioned (e.g., "using TensorFlow" suggests 2015+, "PyTorch" suggests 2016+)
   - Events referenced (conferences, product launches, etc.)
   - Business context (pandemic references suggest 2020-2022, etc.)
   - If no date context exists, use null
9. Date confidence levels:
   - high: Explicit dates or clear time references in content
   - medium: Technology timeline or contextual clues provide reasonable estimate
   - low: Vague indicators or educated guess based on technology maturity
10. This is a Traditional AI story - do NOT include Gen AI superpowers or Aileron framework fields
11. Focus on traditional AI/ML capabilities: prediction, classification, automation, analytics, etc.

Story content to analyze:

{story_content}

Return only the JSON object, no additional text or explanation.
"""

COMPANY_NORMALIZATION_PROMPT = """
Normalize this company name to its canonical form. Consider common variations and return the most standard business name.

Company name to normalize: {company_name}

Examples:
- "accenture plc" -> "Accenture"
- "amazon web services" -> "Amazon Web Services"
- "google llc" -> "Google"
- "microsoft corporation" -> "Microsoft"

Return only the normalized company name, nothing else.
"""

DEDUPLICATION_PROMPT = """
Compare these two customer stories and determine if they represent the same case study or customer implementation.

Story 1:
Customer: {customer1}
Title: {title1}
Content snippet: {content1}

Story 2:
Customer: {customer2}
Title: {title2}
Content snippet: {content2}

Return a JSON object with:
{
  "is_duplicate": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Explanation of why they are or aren't duplicates",
  "similarity_factors": ["List of factors that make them similar or different"]
}

Consider duplicates if:
- Same customer with same use case and technologies
- Same story republished or updated
- Minor variations in title but same content

Consider different if:
- Different customers (even if similar names)
- Same customer but different projects/use cases
- Different technologies or outcomes
"""