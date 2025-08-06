#!/usr/bin/env python3
"""
Industry Mapper Utility
Maps existing industry values to standardized taxonomy with audit trail
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add project root to path for src imports (when called from scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(src_dir)
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

class IndustryMapper:
    """Maps various industry formats to standardized categories"""
    
    def __init__(self):
        # Standardized industry categories
        self.standard_industries = {
            'technology',
            'financial_services', 
            'healthcare',
            'retail_ecommerce',
            'manufacturing',
            'government_public_sector',
            'media_communications',
            'energy_utilities',
            'transportation_logistics',
            'professional_services',
            'other'
        }
        
        # Industry mapping rules - maps patterns to standard categories
        self.mapping_rules = {
            # Technology
            'technology': [
                r'technology', r'software', r'saas', r'it services', r'cloud', 
                r'cybersecurity', r'artificial intelligence', r'machine learning',
                r'ai', r'ml', r'tech', r'information technology', r'computer',
                r'data science', r'analytics platform', r'digital platform',
                r'startup', r'fintech platform', r'healthtech', r'edtech'
            ],
            
            # Financial Services
            'financial_services': [
                r'financial', r'finance', r'banking', r'bank', r'insurance',
                r'fintech', r'payment', r'investment', r'credit', r'wealth',
                r'capital', r'asset management', r'financial services',
                r'trading', r'securities', r'mortgage', r'lending'
            ],
            
            # Healthcare
            'healthcare': [
                r'healthcare', r'health care', r'medical', r'hospital',
                r'pharmaceutical', r'pharma', r'biotech', r'biotechnology',
                r'clinical', r'patient', r'doctor', r'physician', r'nurse',
                r'telemedicine', r'health tech', r'medical device',
                r'diagnostics', r'therapeutics', r'life sciences'
            ],
            
            # Retail & E-commerce
            'retail_ecommerce': [
                r'retail', r'e-commerce', r'ecommerce', r'consumer goods',
                r'fashion', r'apparel', r'marketplace', r'shopping',
                r'brand', r'consumer', r'merchandising', r'grocery',
                r'food retail', r'luxury goods', r'beauty', r'cosmetics'
            ],
            
            # Manufacturing
            'manufacturing': [
                r'manufacturing', r'industrial', r'automotive', r'aerospace',
                r'chemicals', r'materials', r'production', r'factory',
                r'supply chain', r'logistics manufacturing', r'steel',
                r'mining', r'construction materials', r'heavy industry',
                r'defense manufacturing', r'food processing'
            ],
            
            # Government & Public Sector
            'government_public_sector': [
                r'government', r'public sector', r'federal', r'state',
                r'municipal', r'city', r'county', r'military', r'defense',
                r'education', r'university', r'school', r'public',
                r'non-profit', r'nonprofit', r'charity', r'ngo'
            ],
            
            # Media & Communications
            'media_communications': [
                r'telecommunications', r'telecom', r'media', r'broadcasting',
                r'publishing', r'entertainment', r'advertising', r'marketing',
                r'communications', r'content', r'news', r'journalism',
                r'social media', r'digital marketing', r'pr'
            ],
            
            # Energy & Utilities
            'energy_utilities': [
                r'energy', r'utilities', r'oil', r'gas', r'petroleum',
                r'renewable', r'solar', r'wind', r'electric', r'power',
                r'utility', r'water', r'environmental', r'mining',
                r'natural gas', r'nuclear', r'hydroelectric'
            ],
            
            # Transportation & Logistics
            'transportation_logistics': [
                r'transportation', r'logistics', r'shipping', r'freight',
                r'delivery', r'airline', r'aviation', r'rail', r'trucking',
                r'warehousing', r'distribution', r'supply chain logistics',
                r'ride sharing', r'mobility', r'transport'
            ],
            
            # Professional Services
            'professional_services': [
                r'consulting', r'legal', r'law', r'accounting', r'audit',
                r'real estate', r'architecture', r'engineering services',
                r'human resources', r'hr', r'recruitment', r'staffing',
                r'professional services', r'advisory', r'tax services',
                r'professional_services'
            ],
            
            # Other - catch remaining industries
            'other': [
                r'gaming', r'agriculture', r'food_and_beverage', r'food and beverage',
                r'developer_tools', r'life_sciences', r'sports', r'travel_and_tourism',
                r'research_and_development', r'online travel booking', r'petrochemical',
                r'philanthropy', r'professional_sports', r'semiconductor',
                r'sports_betting_and_gaming', r'travel', r'website_building_platform',
                r'agriculture_and_heavy_equipment', r'hospitality', r'tourism',
                r'food', r'beverage', r'entertainment_gaming', r'real_estate_and_hospitality'
            ]
        }
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = {}
        for category, patterns in self.mapping_rules.items():
            combined_pattern = '|'.join([f'({pattern})' for pattern in patterns])
            self.compiled_patterns[category] = re.compile(combined_pattern, re.IGNORECASE)
    
    def map_industry(self, raw_industry: Optional[str]) -> str:
        """
        Map a raw industry string to standardized category
        
        Args:
            raw_industry: Original industry string from database
            
        Returns:
            Standardized industry category or 'other'
        """
        if not raw_industry or not isinstance(raw_industry, str):
            return 'other'
        
        # If already standardized, return as-is
        clean_industry = raw_industry.lower().replace(' ', '_').replace('-', '_')
        if clean_industry in self.standard_industries:
            return clean_industry
        
        # Check for exact matches first (higher priority)
        industry_normalized = raw_industry.lower().replace(' ', '_').replace('-', '_')
        for category, patterns in self.mapping_rules.items():
            for pattern in patterns:
                pattern_normalized = pattern.replace(' ', '_').replace('-', '_')
                if industry_normalized == pattern_normalized:
                    return category
        
        # Try to match against patterns
        industry_lower = raw_industry.lower()
        
        # Score each category based on matches
        category_scores = {}
        for category, pattern in self.compiled_patterns.items():
            matches = pattern.findall(industry_lower)
            if matches:
                # Count total character matches for scoring
                total_chars = sum(len(match) for match_group in matches for match in match_group if match)
                category_scores[category] = total_chars
        
        # Return category with highest score, or 'other' if no matches
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            return best_category
        
        return 'other'
    
    def create_audit_entry(self, story_id: int, old_industry: str, new_industry: str, 
                          mapping_confidence: float, matched_terms: List[str]) -> Dict:
        """Create an audit trail entry for industry update"""
        return {
            'story_id': story_id,
            'timestamp': datetime.now().isoformat(),
            'change_type': 'industry_standardization',
            'old_value': old_industry,
            'new_value': new_industry,
            'mapping_confidence': mapping_confidence,
            'matched_terms': matched_terms,
            'mapper_version': '1.0',
            'mapping_method': 'regex_pattern_matching'
        }
    
    def analyze_database_industries(self) -> Dict:
        """
        Analyze current database industries and suggest mappings
        
        Returns:
            Dictionary with analysis results
        """
        try:
            from database.models import DatabaseOperations
            
            db_ops = DatabaseOperations()
            
            with db_ops.db.get_cursor() as cursor:
                # Get all unique industries with counts and sample story IDs
                cursor.execute("""
                    SELECT 
                        industry,
                        COUNT(*) as story_count,
                        ARRAY_AGG(id ORDER BY id LIMIT 3) as sample_story_ids
                    FROM customer_stories 
                    WHERE industry IS NOT NULL 
                    GROUP BY industry 
                    ORDER BY story_count DESC
                """)
                
                industries_data = cursor.fetchall()
                
                # Analyze mappings
                mapping_analysis = {
                    'total_unique_industries': len(industries_data),
                    'total_stories': sum(row['story_count'] for row in industries_data),
                    'mapping_results': [],
                    'category_distribution': {cat: 0 for cat in self.standard_industries}
                }
                
                for row in industries_data:
                    industry = row['industry']
                    count = row['story_count']
                    sample_ids = row['sample_story_ids']
                    
                    # Get mapping suggestion
                    mapping = self.suggest_mapping(industry)
                    
                    mapping_result = {
                        'original_industry': industry,
                        'mapped_category': mapping['category'],
                        'confidence': mapping['confidence'],
                        'matched_terms': mapping['matches'],
                        'story_count': count,
                        'sample_story_ids': sample_ids
                    }
                    
                    mapping_analysis['mapping_results'].append(mapping_result)
                    mapping_analysis['category_distribution'][mapping['category']] += count
                
                return mapping_analysis
                
        except Exception as e:
            logger.error(f"Error analyzing database industries: {e}")
            return {'error': str(e)}
    
    def suggest_mapping(self, raw_industry: str) -> Dict:
        """
        Get detailed mapping suggestion with confidence scores
        
        Args:
            raw_industry: Original industry string
            
        Returns:
            Dictionary with mapping details and confidence
        """
        if not raw_industry:
            return {'category': 'other', 'confidence': 0.0, 'matches': []}
        
        industry_lower = raw_industry.lower()
        category_details = {}
        
        # Get match details for each category
        for category, pattern in self.compiled_patterns.items():
            matches = pattern.findall(industry_lower)
            if matches:
                matched_terms = [match for match_group in matches for match in match_group if match]
                score = sum(len(term) for term in matched_terms)
                category_details[category] = {
                    'score': score,
                    'matches': matched_terms,
                    'confidence': min(1.0, score / len(raw_industry))
                }
        
        if category_details:
            best_category = max(category_details.items(), key=lambda x: x[1]['score'])[0]
            return {
                'category': best_category,
                'confidence': category_details[best_category]['confidence'],
                'matches': category_details[best_category]['matches'],
                'all_matches': category_details
            }
        
        return {
            'category': 'other',
            'confidence': 0.0,
            'matches': [],
            'all_matches': {}
        }


def main():
    """Test the industry mapper and analyze database"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Industry Mapping Analysis Tool')
    parser.add_argument('--analyze', action='store_true', 
                       help='Analyze current database industries')
    parser.add_argument('--test', action='store_true',
                       help='Run test with sample industries')
    parser.add_argument('--output', type=str, default='industry_analysis.json',
                       help='Output file for analysis results')
    
    args = parser.parse_args()
    
    mapper = IndustryMapper()
    
    if args.test:
        # Test samples
        test_industries = [
            "Healthcare Technology",
            "Financial Services",
            "Retail and Consumer Goods", 
            "Manufacturing and Industrial",
            "Software Development",
            "Government Agency",
            "Telecommunications",
            "Energy and Utilities",
            "Transportation and Logistics",
            "Professional Services Consulting",
            "Agriculture Technology",
            "Hospitality and Tourism"
        ]
        
        print("Industry Mapping Test Results:")
        print("=" * 50)
        
        for industry in test_industries:
            result = mapper.suggest_mapping(industry)
            print(f"'{industry}' → {result['category']} (confidence: {result['confidence']:.2f})")
            if result['matches']:
                print(f"  Matched terms: {result['matches']}")
            print()
    
    if args.analyze:
        print("Analyzing database industries...")
        analysis = mapper.analyze_database_industries()
        
        if 'error' in analysis:
            print(f"Error: {analysis['error']}")
            return
        
        print(f"\nDatabase Industry Analysis:")
        print(f"Total unique industries: {analysis['total_unique_industries']}")
        print(f"Total stories: {analysis['total_stories']}")
        print(f"\nProposed category distribution:")
        
        for category, count in analysis['category_distribution'].items():
            percentage = (count / analysis['total_stories']) * 100
            print(f"  {category}: {count} stories ({percentage:.1f}%)")
        
        # Save detailed analysis to file
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"\nDetailed analysis saved to: {args.output}")
        
        # Show top mappings that need review
        low_confidence = [r for r in analysis['mapping_results'] 
                         if r['confidence'] < 0.5 and r['story_count'] > 1]
        
        if low_confidence:
            print(f"\nLow confidence mappings needing review:")
            for result in low_confidence[:10]:
                print(f"  '{result['original_industry']}' → {result['mapped_category']} "
                      f"({result['confidence']:.2f}, {result['story_count']} stories)")


if __name__ == "__main__":
    main()