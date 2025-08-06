import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import anthropic
from anthropic import APITimeoutError, APIConnectionError, RateLimitError
from src.config import Config
from src.ai_integration.prompts import (
    GEN_AI_DETERMINATION_PROMPT, 
    EXTRACTION_PROMPT, 
    TRADITIONAL_AI_EXTRACTION_PROMPT,
    COMPANY_NORMALIZATION_PROMPT, 
    DEDUPLICATION_PROMPT
)
from src.classification.enhanced_classifier import EnhancedClassifier

logger = logging.getLogger(__name__)

class ClaudeProcessor:
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or Config.ANTHROPIC_API_KEY,
            timeout=60.0  # 60 second timeout for API calls
        )
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        self.enhanced_classifier = EnhancedClassifier()
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
    
    def _make_claude_request_with_retry(self, messages, max_tokens=1500, temperature=0.1):
        """Make Claude API request with retry logic and timeout handling"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Claude API attempt {attempt + 1}/{self.max_retries}")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages
                )
                
                logger.debug(f"Claude API request successful on attempt {attempt + 1}")
                return response
                
            except (APITimeoutError, APIConnectionError) as e:
                last_error = e
                wait_time = self.base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Claude API timeout/connection error on attempt {attempt + 1}: {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    
            except RateLimitError as e:
                last_error = e
                wait_time = self.base_delay * (3 ** attempt)  # Longer wait for rate limits
                logger.warning(f"Claude API rate limit on attempt {attempt + 1}: {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Rate limited - waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Rate limit persists after {self.max_retries} attempts")
                    
            except Exception as e:
                # For other errors, don't retry
                logger.error(f"Claude API error (no retry): {e}")
                raise e
        
        # If we get here, all retries failed
        raise last_error
        
    def determine_gen_ai_classification(self, raw_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhanced Gen AI classification using 4-tier system with Claude fallback"""
        try:
            story_text = raw_content.get('text', '')
            
            if not story_text or len(story_text.strip()) < 100:
                logger.warning("Story content too short for Gen AI classification")
                return None
            
            # Use enhanced classifier first (much faster and often accurate)
            analysis = self.enhanced_classifier.classify_story(
                story_id=0,  # Dummy ID for new stories
                title=raw_content.get('title', ''),
                url=raw_content.get('url', ''),
                customer='',  # Will be extracted later
                raw_content=story_text
            )
            
            # If enhanced classifier can determine classification confidently, use it
            if not analysis['requires_claude']:
                is_gen_ai = analysis['recommendation'] == 'GenAI'
                logger.info(f"Enhanced classifier result: {analysis['recommendation']} "
                           f"(method: {analysis['method']}, confidence: {analysis['confidence']:.2f})")
                
                return {
                    'is_gen_ai': is_gen_ai,
                    'confidence': analysis['confidence'],
                    'reasoning': analysis['reasoning'],
                    'key_indicators': analysis['evidence'],
                    'method': analysis['method'],
                    'classification_source': 'enhanced_classifier'
                }
            
            # Fall back to Claude analysis for unclear cases
            logger.info("Enhanced classifier requires Claude analysis - using Claude fallback")
            return self._claude_gen_ai_classification(raw_content)
                
        except Exception as e:
            logger.error(f"Error in enhanced Gen AI classification: {e}")
            # Fall back to Claude on any error
            return self._claude_gen_ai_classification(raw_content)
    
    def _claude_gen_ai_classification(self, raw_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Original Claude-only classification as fallback"""
        try:
            story_text = raw_content.get('text', '')
            
            # Limit content length for classification
            if len(story_text) > 16000:  # Shorter limit for classification
                story_text = story_text[:16000] + "... [content truncated]"
            
            prompt = GEN_AI_DETERMINATION_PROMPT.format(story_content=story_text)
            
            logger.info("Using Claude API for Gen AI classification")
            
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self._make_claude_request_with_retry(
                messages=messages,
                max_tokens=1500,
                temperature=0.1
            )
            
            response_text = response.content[0].text.strip()
            
            try:
                # Clean response text to handle common JSON formatting issues
                cleaned_response = response_text.strip()
                
                # Try to fix common JSON issues
                if not cleaned_response.startswith('{'):
                    # Extract JSON from text that might have extra content
                    import re
                    json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                    if json_match:
                        cleaned_response = json_match.group(0)
                
                classification_result = json.loads(cleaned_response)
                
                # Validate classification result
                if 'is_gen_ai' not in classification_result:
                    logger.error("Classification result missing 'is_gen_ai' field")
                    return None
                
                # Add metadata about classification source
                classification_result['classification_source'] = 'claude_api'
                
                # Handle both old and new JSON response formats
                # New format has 'key_indicators', old format might not
                if 'key_indicators' not in classification_result:
                    classification_result['key_indicators'] = []
                
                logger.info(f"Claude Gen AI classification: {classification_result['is_gen_ai']} "
                           f"(confidence: {classification_result.get('confidence', 'unknown')})")
                return classification_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude classification response as JSON: {e}")
                logger.error(f"Raw response length: {len(response_text)} characters")
                logger.error(f"Full raw response: {response_text}")
                
                # Check if response was truncated
                if not response_text.rstrip().endswith('}'):
                    logger.error("Response appears to be truncated - missing closing brace")
                
                # Enhanced fallback parsing with regex
                try:
                    import re
                    
                    # For truncated JSON, try to fix it by completing the structure
                    if not response_text.rstrip().endswith('}'):
                        logger.info("Attempting to fix truncated JSON response")
                        # Add missing closing braces/brackets
                        fixed_response = response_text.rstrip()
                        # Count open vs closed braces and brackets
                        open_braces = fixed_response.count('{') 
                        closed_braces = fixed_response.count('}')
                        open_brackets = fixed_response.count('[')
                        closed_brackets = fixed_response.count(']')
                        
                        # Add missing closures
                        if open_brackets > closed_brackets:
                            fixed_response += ']' * (open_brackets - closed_brackets)
                        if open_braces > closed_braces:
                            fixed_response += '}' * (open_braces - closed_braces)
                        
                        # Try parsing the fixed JSON
                        try:
                            classification_result = json.loads(fixed_response)
                            logger.info("Successfully parsed fixed JSON response")
                            
                            if 'is_gen_ai' in classification_result:
                                classification_result['classification_source'] = 'claude_api_fixed'
                                return classification_result
                        except json.JSONDecodeError:
                            logger.debug("Fixed JSON still couldn't be parsed, falling back to regex")
                    
                    # Extract is_gen_ai value using regex
                    gen_ai_match = re.search(r'"is_gen_ai":\s*(true|false)', response_text, re.IGNORECASE)
                    if not gen_ai_match:
                        logger.error("Could not extract is_gen_ai from malformed response")
                        return None
                    
                    is_gen_ai = gen_ai_match.group(1).lower() == 'true'
                    
                    # Extract confidence if available
                    confidence_match = re.search(r'"confidence":\s*([0-9.]+)', response_text)
                    confidence = float(confidence_match.group(1)) if confidence_match else 0.7
                    
                    # Extract reasoning if available (handle truncated text)
                    reasoning_match = re.search(r'"reasoning":\s*"([^"]*)', response_text)
                    reasoning = reasoning_match.group(1) if reasoning_match else 'Extracted from malformed JSON response'
                    if reasoning and not reasoning.endswith('.'):
                        reasoning += '... [truncated]'
                    
                    # Extract key indicators if available (handle partial arrays)
                    key_indicators = []
                    indicators_match = re.search(r'"key_indicators":\s*\[(.*?)(?:\]|$)', response_text, re.DOTALL)
                    if indicators_match:
                        indicators_text = indicators_match.group(1)
                        # Simple extraction of quoted strings
                        key_indicators = re.findall(r'"([^"]*)"', indicators_text)
                    
                    logger.info(f"Successfully extracted from malformed JSON: is_gen_ai={is_gen_ai}, confidence={confidence}")
                    
                    return {
                        'is_gen_ai': is_gen_ai,
                        'confidence': confidence,
                        'reasoning': reasoning,
                        'key_indicators': key_indicators,
                        'classification_source': 'claude_api_fallback'
                    }
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback parsing also failed: {fallback_error}")
                    return None
                
        except Exception as e:
            logger.error(f"Error in Claude Gen AI classification: {e}")
            return None
    
    def extract_story_data(self, raw_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract structured data from raw story content using two-step Claude analysis"""
        try:
            # Step 1: Determine if this is Gen AI or Traditional AI
            classification = self.determine_gen_ai_classification(raw_content)
            
            if not classification:
                logger.error("Failed to classify story as Gen AI or Traditional AI")
                return None
            
            is_gen_ai = classification.get('is_gen_ai', False)
            
            # Step 2: Extract data using appropriate prompt
            story_text = raw_content.get('text', '')
            
            if not story_text or len(story_text.strip()) < 100:
                logger.warning("Story content too short for meaningful extraction")
                return None
            
            # Limit content length to avoid token limits
            if len(story_text) > 32000:  # ~8000 words
                story_text = story_text[:32000] + "... [content truncated]"
            
            # Choose appropriate extraction prompt
            if is_gen_ai:
                prompt = EXTRACTION_PROMPT.format(story_content=story_text)
                logger.info("Using Gen AI extraction prompt (with Aileron framework)")
            else:
                prompt = TRADITIONAL_AI_EXTRACTION_PROMPT.format(story_content=story_text)
                logger.info("Using Traditional AI extraction prompt (no Aileron framework)")
            
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self._make_claude_request_with_retry(
                messages=messages,
                max_tokens=2000,
                temperature=0.1
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON response
            try:
                extracted_data = json.loads(response_text)
                
                # Add processing metadata and classification results
                extracted_data['last_processed'] = datetime.now().isoformat()
                extracted_data['is_gen_ai'] = is_gen_ai
                extracted_data['gen_ai_classification'] = classification
                
                # Validate required fields
                if not self._validate_extracted_data(extracted_data, is_gen_ai):
                    logger.warning("Extracted data failed validation")
                    return None
                
                logger.info(f"Successfully extracted structured data from {'Gen AI' if is_gen_ai else 'Traditional AI'} story")
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
                max_tokens=1000,  # Increased for enhanced JSON response format
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
    
    def _validate_extracted_data(self, data: Dict[str, Any], is_gen_ai: bool = True) -> bool:
        """Validate that extracted data has required fields"""
        required_fields = ['customer_name', 'summary', 'content_quality_score', 'ai_type']
        
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
        
        # Validate ai_type field
        ai_type = data.get('ai_type')
        expected_ai_type = 'generative' if is_gen_ai else 'traditional' 
        if ai_type != expected_ai_type:
            logger.warning(f"AI type mismatch: expected '{expected_ai_type}', got '{ai_type}'")
            return False
        
        # Only validate Gen AI classification fields for Gen AI stories
        if is_gen_ai:
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
        else:
            # For traditional AI stories, ensure Gen AI fields are not present
            gen_ai_fields = ['gen_ai_superpowers', 'business_impacts', 'adoption_enablers', 'business_function', 'classification_confidence']
            for field in gen_ai_fields:
                if field in data:
                    logger.warning(f"Traditional AI story should not have Gen AI field: {field}")
                    # Remove the field rather than failing validation
                    del data[field]
        
        return True
    
    def validate_is_gen_ai_consistency(self, extracted_data: Dict[str, Any], story_identifier: str = "") -> Dict[str, Any]:
        """
        Validate and fix consistency between is_gen_ai field and ai_type classification.
        Returns the corrected extracted_data dictionary.
        """
        is_gen_ai = extracted_data.get('is_gen_ai')
        ai_type = extracted_data.get('ai_type')
        
        if is_gen_ai is not None and ai_type is not None:
            expected_ai_type = 'generative' if is_gen_ai else 'traditional'
            if ai_type != expected_ai_type:
                logger.warning(f"Consistency issue detected for {story_identifier}: "
                             f"is_gen_ai={is_gen_ai} but ai_type='{ai_type}'. "
                             f"Using ai_type as authoritative source.")
                # Use ai_type as the authoritative source and update is_gen_ai accordingly
                corrected_is_gen_ai = (ai_type == 'generative')
                extracted_data['is_gen_ai'] = corrected_is_gen_ai
                logger.info(f"Corrected is_gen_ai: {is_gen_ai} -> {corrected_is_gen_ai} for {story_identifier}")
        
        return extracted_data
    
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