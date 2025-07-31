#!/usr/bin/env python3
"""
Test script for Gen AI Classification Enhancement
Tests the enhanced Claude processing with existing stories WITHOUT database changes
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import DatabaseConnection
from database.models import DatabaseOperations
from ai_integration.claude_processor import ClaudeProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_classification():
    """Test enhanced Claude processing with 2-3 existing stories"""
    
    print("🧪 TESTING ENHANCED GEN AI CLASSIFICATION")
    print("=" * 60)
    
    try:
        # Initialize database and Claude processor
        db_ops = DatabaseOperations()
        claude_processor = ClaudeProcessor()
        
        # Get a few existing stories for testing
        print("\n📚 Fetching existing stories for testing...")
        
        # Get stories from different sources for diversity
        sources = db_ops.get_sources()
        test_stories = []
        
        for source in sources[:3]:  # Test with first 3 sources
            stories = db_ops.get_stories_by_source(source.id, limit=1)
            if stories:
                test_stories.extend(stories)
        
        if not test_stories:
            print("❌ No existing stories found for testing")
            return False
        
        print(f"✅ Found {len(test_stories)} stories for testing")
        
        # Test each story with enhanced processing
        for i, story in enumerate(test_stories, 1):
            print(f"\n🔍 Testing Story {i}/{len(test_stories)}")
            print(f"   Customer: {story.customer_name}")
            print(f"   Source: {story.source_id}")
            print(f"   URL: {story.url}")
            
            # Process with enhanced Claude prompt
            enhanced_data = claude_processor.extract_story_data(story.raw_content)
            
            if enhanced_data:
                print("✅ Successfully processed with enhanced classification")
                
                # Display new Gen AI classification fields
                print("\n📊 GEN AI CLASSIFICATION RESULTS:")
                print("-" * 40)
                
                superpowers = enhanced_data.get('gen_ai_superpowers', [])
                print(f"🔧 Superpowers: {superpowers}")
                if enhanced_data.get('superpowers_other'):
                    print(f"   Other: {enhanced_data['superpowers_other']}")
                
                impacts = enhanced_data.get('business_impacts', [])
                print(f"💼 Business Impacts: {impacts}")
                if enhanced_data.get('impacts_other'):
                    print(f"   Other: {enhanced_data['impacts_other']}")
                
                enablers = enhanced_data.get('adoption_enablers', [])
                print(f"🚀 Adoption Enablers: {enablers}")
                if enhanced_data.get('enablers_other'):
                    print(f"   Other: {enhanced_data['enablers_other']}")
                
                function = enhanced_data.get('business_function')
                print(f"🏢 Business Function: {function}")
                if enhanced_data.get('function_other'):
                    print(f"   Other: {enhanced_data['function_other']}")
                
                # Show confidence scores
                confidence = enhanced_data.get('classification_confidence', {})
                print(f"📈 Classification Confidence:")
                for dim, score in confidence.items():
                    print(f"   {dim}: {score:.2f}")
                
                # Save test results to file for review
                test_result = {
                    'story_info': {
                        'customer_name': story.customer_name,
                        'source_id': story.source_id,
                        'url': story.url
                    },
                    'enhanced_classification': enhanced_data
                }
                
                filename = f"test_result_story_{i}.json"
                with open(filename, 'w') as f:
                    json.dump(test_result, f, indent=2, default=str)
                print(f"💾 Test results saved to: {filename}")
                
            else:
                print("❌ Failed to process story with enhanced classification")
                return False
            
            print("-" * 60)
        
        print("\n🎉 TESTING COMPLETED SUCCESSFULLY!")
        print("✅ Enhanced Gen AI classification is working correctly")
        print("✅ All test results saved to JSON files for review")
        print("\n📋 NEXT STEPS:")
        print("1. Review test result JSON files")
        print("2. If satisfied, proceed with database schema updates")
        print("3. Backfill all 52 existing stories with new classifications")
        
        return True
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main function"""
    success = test_enhanced_classification()
    
    if success:
        print("\n🚀 Ready to proceed with database schema updates!")
        print("Run this test again to validate before making DB changes.")
    else:
        print("\n⚠️  Fix issues before proceeding with database changes.")
        sys.exit(1)

if __name__ == "__main__":
    main()