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
   - Technology releases mentioned (e.g., "using GPT-4" suggests 2023+, "Claude 3" suggests 2024+)
   - Events referenced (conferences, product launches, etc.)
   - Business context (pandemic references suggest 2020-2022, etc.)
   - If no date context exists, use null
9. Date confidence levels:
   - high: Explicit dates or clear time references in content
   - medium: Technology timeline or contextual clues provide reasonable estimate
   - low: Vague indicators or educated guess based on technology maturity

10. Gen AI Classification Guidelines:
    **Superpowers** - What AI capabilities are being used:
    - code: Programming, software development, code generation/review
    - create_content: Text, images, videos, marketing materials, documentation
    - automate_with_agents: AI agents, workflows, process automation
    - find_data_insights: Analytics, pattern recognition, data discovery, recommendations
    - research: Information gathering, market research, literature review
    - brainstorm: Ideation, creative thinking, problem solving
    - natural_language: Conversational AI, language understanding, translation
    
    **Business Impacts** - What outcomes were achieved:
    - innovation: New products, services, or breakthrough capabilities
    - efficiency: Streamlined processes, reduced waste, optimized operations
    - speed: Faster time-to-market, accelerated processes, quick responses
    - quality: Improved accuracy, better outcomes, enhanced standards
    - client_satisfaction: Better customer experience, satisfaction scores
    - risk_reduction: Lower risks, better compliance, improved security
    
    **Adoption Enablers** - What organizational factors enabled success:
    - data_and_digital: Data infrastructure, digital maturity, tech stack
    - innovation_culture: Change readiness, experimentation mindset, leadership support
    - ecosystem_partners: Vendor relationships, system integrators, consultants
    - policy_and_governance: Guidelines, standards, approval processes
    - risk_management: Security measures, compliance frameworks, risk controls
    
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