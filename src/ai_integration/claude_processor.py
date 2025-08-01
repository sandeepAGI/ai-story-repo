import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import anthropic
from src.config import Config
from src.ai_integration.prompts import EXTRACTION_PROMPT, COMPANY_NORMALIZATION_PROMPT, DEDUPLICATION_PROMPT

logger = logging.getLogger(__name__)

class ClaudeProcessor:
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or Config.ANTHROPIC_API_KEY
        )
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        
    def extract_story_data(self, raw_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract structured data from raw story content using Claude"""
        try:
            # Prepare content for analysis
            story_text = raw_content.get('text', '')
            
            if not story_text or len(story_text.strip()) < 100:
                logger.warning("Story content too short for meaningful extraction")
                return None
            
            # Limit content length to avoid token limits (roughly 8000 words max)
            if len(story_text) > 32000:  # ~8000 words
                story_text = story_text[:32000] + "... [content truncated]"
            
            prompt = EXTRACTION_PROMPT.format(story_content=story_text)
            
            logger.info("Sending content to Claude for extraction")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent extraction
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON response
            try:
                extracted_data = json.loads(response_text)
                
                # Add processing metadata
                extracted_data['last_processed'] = datetime.now().isoformat()
                
                # Validate required fields
                if not self._validate_extracted_data(extracted_data):
                    logger.warning("Extracted data failed validation")
                    return None
                
                logger.info("Successfully extracted structured data from story")
                return extracted_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                logger.error(f"Raw response: {response_text[:1000]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error in Claude extraction: {e}")
            if 'response_text' in locals():
                logger.error(f"Raw Claude response: {response_text[:1000]}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def normalize_company_name(self, company_name: str) -> str:
        """Normalize company name using Claude"""
        try:
            prompt = COMPANY_NORMALIZATION_PROMPT.format(company_name=company_name)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.0,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            normalized_name = response.content[0].text.strip()
            return normalized_name if normalized_name else company_name
            
        except Exception as e:
            logger.error(f"Error normalizing company name: {e}")
            return company_name
    
    def check_story_similarity(self, story1: Dict, story2: Dict) -> Dict[str, Any]:
        """Check if two stories are duplicates using Claude"""
        try:
            # Prepare content snippets
            content1 = story1.get('raw_content', {}).get('text', '')[:1000]
            content2 = story2.get('raw_content', {}).get('text', '')[:1000]
            
            prompt = DEDUPLICATION_PROMPT.format(
                customer1=story1.get('customer_name', ''),
                title1=story1.get('title', ''),
                content1=content1,
                customer2=story2.get('customer_name', ''),
                title2=story2.get('title', ''),
                content2=content2
            )
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text.strip()
            return json.loads(response_text)
            
        except Exception as e:
            logger.error(f"Error checking story similarity: {e}")
            return {
                "is_duplicate": False,
                "confidence": 0.0,
                "reasoning": f"Error in analysis: {e}",
                "similarity_factors": []
            }
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> bool:
        """Validate that extracted data has required fields"""
        required_fields = ['customer_name', 'summary', 'content_quality_score']
        
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate content quality score
        quality_score = data.get('content_quality_score', 0)
        if not isinstance(quality_score, (int, float)) or not (0 <= quality_score <= 1):
            logger.warning(f"Invalid content quality score: {quality_score}")
            return False
        
        # Validate business outcomes structure
        outcomes = data.get('business_outcomes', [])
        if not isinstance(outcomes, list):
            logger.warning("business_outcomes should be a list")
            return False
        
        for outcome in outcomes:
            if not isinstance(outcome, dict) or 'type' not in outcome:
                logger.warning("Invalid business outcome structure")
                return False
        
        # Validate Gen AI classification fields
        classification_fields = {
            'gen_ai_superpowers': ['code', 'create_content', 'automate_with_agents', 'find_data_insights', 'research', 'brainstorm', 'natural_language'],
            'business_impacts': ['innovation', 'efficiency', 'speed', 'quality', 'client_satisfaction', 'risk_reduction'],
            'adoption_enablers': ['data_and_digital', 'innovation_culture', 'ecosystem_partners', 'policy_and_governance', 'risk_management']
        }
        
        for field_name, valid_values in classification_fields.items():
            field_data = data.get(field_name, [])
            if not isinstance(field_data, list):
                logger.warning(f"{field_name} should be a list")
                return False
            
            # Check if values are valid (allow empty lists)
            for value in field_data:
                if value not in valid_values:
                    logger.warning(f"Invalid value '{value}' in {field_name}. Valid values: {valid_values}")
                    # Don't fail validation - just log warning for flexibility
        
        # Validate business function
        business_function = data.get('business_function')
        if business_function:
            valid_functions = ['marketing', 'sales', 'production', 'distribution', 'service', 'finance_and_accounting']
            if business_function not in valid_functions:
                logger.warning(f"Invalid business_function '{business_function}'. Valid values: {valid_functions}")
                # Don't fail validation - just log warning
        
        # Validate classification confidence structure
        confidence = data.get('classification_confidence', {})
        if confidence and isinstance(confidence, dict):
            for conf_field, conf_value in confidence.items():
                if not isinstance(conf_value, (int, float)) or not (0 <= conf_value <= 1):
                    logger.warning(f"Invalid confidence score for {conf_field}: {conf_value}")
        
        return True
    
    def batch_process_stories(self, stories: list, delay: float = 1.0) -> list:
        """Process multiple stories with rate limiting"""
        processed_stories = []
        
        for i, story in enumerate(stories):
            logger.info(f"Processing story {i+1}/{len(stories)}: {story.get('customer_name', 'Unknown')}")
            
            extracted_data = self.extract_story_data(story.get('raw_content', {}))
            
            if extracted_data:
                story['extracted_data'] = extracted_data
                processed_stories.append(story)
            else:
                logger.warning(f"Failed to process story: {story.get('url', 'unknown URL')}")
            
            # Rate limiting between requests
            if i < len(stories) - 1:
                time.sleep(delay)
        
        logger.info(f"Successfully processed {len(processed_stories)}/{len(stories)} stories")
        return processed_stories