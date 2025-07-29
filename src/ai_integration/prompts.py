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