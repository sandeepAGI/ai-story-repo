#!/usr/bin/env python3
"""
Test Script for Claude Industry Classification Changes
Tests the updated prompts to ensure they work correctly with new standardized taxonomy
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add project root to path and import with src prefix (like working scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.ai_integration.claude_processor import ClaudeProcessor
from src.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndustryClassificationTester:
    """Test Claude's industry classification with new prompts"""
    
    def __init__(self):
        self.claude_processor = ClaudeProcessor()
        
        # Expected standard industries
        self.standard_industries = {
            'technology', 'financial_services', 'healthcare', 'retail_ecommerce',
            'manufacturing', 'government_public_sector', 'media_communications',
            'energy_utilities', 'transportation_logistics', 'professional_services', 'other'
        }
        
        # Test cases - realistic customer story snippets
        self.test_cases = [
            {
                'name': 'Technology Company',
                'story_content': """
                TechCorp Solutions is a leading software development company specializing in cloud-based SaaS platforms. 
                The company implemented Claude AI to automate their code review process, reducing development time by 40% 
                and improving code quality. Their engineering team uses the AI for generating unit tests, documentation, 
                and optimizing database queries. The solution has enabled faster deployment cycles and better software reliability.
                """,
                'expected_industry': 'technology'
            },
            {
                'name': 'Bank',
                'story_content': """
                First National Bank deployed an AI-powered fraud detection system to monitor transactions in real-time. 
                The system analyzes customer spending patterns, geographic data, and transaction timing to identify 
                suspicious activities. Since implementation, the bank has reduced false positives by 60% and improved 
                customer satisfaction while maintaining security. The AI processes millions of transactions daily 
                across their credit card, debit card, and online banking platforms.
                """,
                'expected_industry': 'financial_services'
            },
            {
                'name': 'Hospital System',
                'story_content': """
                Regional Medical Center implemented an AI diagnostic assistant to help radiologists analyze medical imaging. 
                The system reviews X-rays, CT scans, and MRIs to flag potential abnormalities for physician review. 
                The hospital reports 25% faster diagnosis times and improved accuracy in detecting early-stage cancers. 
                Patient outcomes have improved significantly, and the radiology department can handle 40% more cases 
                with the same staff size.
                """,
                'expected_industry': 'healthcare'
            },
            {
                'name': 'E-commerce Retailer',
                'story_content': """
                ShopMart, a leading online retailer, uses AI for personalized product recommendations and inventory optimization. 
                The system analyzes customer browsing history, purchase patterns, and seasonal trends to suggest relevant products. 
                Revenue has increased by 30% through better conversion rates, and inventory costs have decreased by 20% 
                through improved demand forecasting. The AI also powers their customer service chatbot handling 80% of inquiries.
                """,
                'expected_industry': 'retail_ecommerce'
            },
            {
                'name': 'Manufacturing Plant',
                'story_content': """
                Global Manufacturing Inc. deployed predictive maintenance AI across their automotive production lines. 
                The system monitors equipment sensors, vibration data, and temperature readings to predict machine failures 
                before they occur. Unplanned downtime has been reduced by 70%, saving millions in lost production. 
                The factory now maintains 99.5% uptime and has extended equipment lifespan by 30%.
                """,
                'expected_industry': 'manufacturing'
            },
            {
                'name': 'City Government',
                'story_content': """
                The City of Springfield implemented an AI system for traffic optimization and public safety. 
                The solution analyzes traffic camera feeds, emergency response data, and public event schedules 
                to optimize traffic light timing and emergency vehicle routing. Response times have improved by 25%, 
                traffic congestion has decreased by 35%, and citizen satisfaction scores have increased significantly.
                """,
                'expected_industry': 'government_public_sector'
            },
            {
                'name': 'Media Company',
                'story_content': """
                National Broadcasting Network uses AI for content curation and audience engagement analysis. 
                The system analyzes viewer preferences, social media sentiment, and trending topics to recommend 
                programming schedules and content creation priorities. Viewership has increased by 20%, and advertising 
                revenue has grown by 15% through better audience targeting and content placement.
                """,
                'expected_industry': 'media_communications'
            },
            {
                'name': 'Electric Utility',
                'story_content': """
                PowerGrid Utilities implemented AI for smart grid management and renewable energy integration. 
                The system predicts energy demand, optimizes power distribution, and manages solar and wind energy inputs. 
                Grid efficiency has improved by 25%, renewable energy utilization has increased by 40%, and power outages 
                have been reduced by 50% through predictive maintenance of transmission lines.
                """,
                'expected_industry': 'energy_utilities'
            },
            {
                'name': 'Logistics Company',
                'story_content': """
                FastShip Logistics uses AI for route optimization and delivery scheduling across their nationwide network. 
                The system analyzes traffic patterns, weather conditions, and package volumes to optimize truck routes 
                and delivery times. Delivery efficiency has improved by 35%, fuel costs have decreased by 20%, and 
                customer satisfaction scores have reached all-time highs with 95% on-time deliveries.
                """,
                'expected_industry': 'transportation_logistics'
            },
            {
                'name': 'Consulting Firm',
                'story_content': """
                Strategic Advisors LLC, a management consulting firm, implemented AI to enhance their client research 
                and proposal generation processes. The system analyzes industry reports, market data, and competitor 
                information to support consultant recommendations. Proposal quality has improved significantly, 
                research time has been reduced by 50%, and client satisfaction scores have increased by 30%.
                """,
                'expected_industry': 'professional_services'
            },
            {
                'name': 'Agriculture Cooperative',
                'story_content': """
                Midwest Farmers Cooperative deployed AI for crop yield prediction and pest management across member farms. 
                The system analyzes satellite imagery, soil sensors, and weather data to optimize planting schedules 
                and identify pest infestations early. Crop yields have increased by 20%, pesticide usage has decreased 
                by 30%, and overall farm profitability has improved significantly for cooperative members.
                """,
                'expected_industry': 'other'
            }
        ]
    
    def test_single_story(self, test_case: dict) -> dict:
        """Test classification of a single story"""
        logger.info(f"Testing: {test_case['name']}")
        
        # Create raw content structure
        raw_content = {
            'text': test_case['story_content'],
            'metadata': {
                'title': f"{test_case['name']} AI Success Story",
                'word_count': len(test_case['story_content'].split())
            }
        }
        
        try:
            # Extract data using Claude processor
            extracted_data = self.claude_processor.extract_story_data(raw_content)
            
            if not extracted_data:
                return {
                    'test_case': test_case['name'],
                    'status': 'failed',
                    'error': 'No data extracted',
                    'expected_industry': test_case['expected_industry'],
                    'actual_industry': None,
                    'is_correct': False
                }
            
            actual_industry = extracted_data.get('industry')
            is_correct = actual_industry == test_case['expected_industry']
            is_valid_category = actual_industry in self.standard_industries
            
            result = {
                'test_case': test_case['name'],
                'status': 'success',
                'expected_industry': test_case['expected_industry'],
                'actual_industry': actual_industry,
                'is_correct': is_correct,
                'is_valid_category': is_valid_category,
                'customer_name': extracted_data.get('customer_name'),
                'ai_type': extracted_data.get('ai_type'),
                'is_gen_ai': extracted_data.get('is_gen_ai'),
                'content_quality_score': extracted_data.get('content_quality_score')
            }
            
            if is_correct:
                logger.info(f"✅ PASS: {test_case['name']} correctly classified as {actual_industry}")
            elif is_valid_category:
                logger.warning(f"⚠️  PARTIAL: {test_case['name']} classified as {actual_industry}, expected {test_case['expected_industry']}")
            else:
                logger.error(f"❌ FAIL: {test_case['name']} classified as invalid category: {actual_industry}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ ERROR: {test_case['name']} failed with error: {e}")
            return {
                'test_case': test_case['name'],
                'status': 'error',
                'error': str(e),
                'expected_industry': test_case['expected_industry'],
                'actual_industry': None,
                'is_correct': False
            }
    
    def run_all_tests(self) -> dict:
        """Run all test cases and generate report"""
        logger.info("Starting Claude Industry Classification Tests")
        logger.info("=" * 60)
        
        test_results = {
            'test_run_timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_cases),
            'passed': 0,
            'partial': 0,  # Valid category but not expected
            'failed': 0,
            'errors': 0,
            'accuracy': 0.0,
            'valid_category_rate': 0.0,
            'results': []
        }
        
        for test_case in self.test_cases:
            result = self.test_single_story(test_case)
            test_results['results'].append(result)
            
            if result['status'] == 'error':
                test_results['errors'] += 1
            elif result['is_correct']:
                test_results['passed'] += 1
            elif result.get('is_valid_category', False):
                test_results['partial'] += 1
            else:
                test_results['failed'] += 1
        
        # Calculate metrics
        successful_tests = test_results['passed'] + test_results['partial']
        test_results['accuracy'] = (test_results['passed'] / test_results['total_tests']) * 100
        test_results['valid_category_rate'] = (successful_tests / test_results['total_tests']) * 100
        
        return test_results
    
    def generate_report(self, results: dict) -> str:
        """Generate a formatted test report"""
        report = f"""
Claude Industry Classification Test Report
==========================================
Test Run: {results['test_run_timestamp']}

Summary:
--------
Total Tests: {results['total_tests']}
Passed (exact match): {results['passed']}
Partial (valid category): {results['partial']}
Failed (invalid category): {results['failed']}
Errors: {results['errors']}

Metrics:
--------
Accuracy (exact match): {results['accuracy']:.1f}%
Valid Category Rate: {results['valid_category_rate']:.1f}%

Detailed Results:
-----------------
"""
        
        for result in results['results']:
            status_icon = "✅" if result['is_correct'] else ("⚠️" if result.get('is_valid_category') else "❌")
            report += f"{status_icon} {result['test_case']}: {result['expected_industry']} → {result['actual_industry']}\n"
            
            if result['status'] == 'error':
                report += f"   Error: {result['error']}\n"
            elif result.get('customer_name'):
                report += f"   Customer: {result['customer_name']}, AI Type: {result.get('ai_type', 'N/A')}\n"
        
        return report


def main():
    """Run the industry classification tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Claude Industry Classification')
    parser.add_argument('--output', type=str, default='claude_industry_test_results.json',
                       help='Output file for test results')
    parser.add_argument('--report', type=str, default='claude_industry_test_report.txt',
                       help='Output file for human-readable report')
    
    args = parser.parse_args()
    
    # Check if Claude API key is configured
    try:
        Config.validate()
    except Exception as e:
        print(f"Configuration error: {e}")
        print("Please ensure ANTHROPIC_API_KEY is set in your environment")
        return
    
    tester = IndustryClassificationTester()
    
    try:
        # Run tests
        results = tester.run_all_tests()
        
        # Generate and display report
        report = tester.generate_report(results)
        print(report)
        
        # Save results to files
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        with open(args.report, 'w') as f:
            f.write(report)
        
        print(f"\nDetailed results saved to: {args.output}")
        print(f"Report saved to: {args.report}")
        
        # Exit with appropriate code
        if results['valid_category_rate'] >= 90:
            print("\n🎉 Test suite PASSED - Claude is correctly using standardized industries!")
            sys.exit(0)
        elif results['valid_category_rate'] >= 70:
            print("\n⚠️  Test suite PARTIAL - Most classifications are valid but may need refinement")
            sys.exit(0)
        else:
            print("\n❌ Test suite FAILED - Claude industry classification needs attention")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test suite failed with error: {e}")
        print(f"Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()