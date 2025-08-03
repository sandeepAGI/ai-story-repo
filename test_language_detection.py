#!/usr/bin/env python3
"""
Test language detection functionality before implementing in production
"""

import sys
import os
sys.path.append('src')

from src.utils.language_detection import LanguageDetector, detect_story_language

def test_url_based_detection():
    """Test URL-based language detection"""
    print("=" * 60)
    print("TESTING URL-BASED LANGUAGE DETECTION")
    print("=" * 60)
    
    detector = LanguageDetector()
    
    test_urls = [
        # Known non-English URLs from our database
        ("https://www.microsoft.com/ja-jp/customers/story/18738-konica-minolta-azure-open-ai-service", "Japanese"),
        ("https://www.microsoft.com/ko-kr/customers/story/19276-kt-onedrive", "Korean"),
        ("https://www.microsoft.com/ko-kr/customers/story/19277-krafton-microsoft-365", "Korean"),
        ("https://www.microsoft.com/ko-kr/customers/story/20335-law-and-company-azure-functions", "Korean"),
        ("https://www.microsoft.com/zh-cn/customers/story/1791859496343328428-joyson-microsoft-copilot", "Chinese (Simplified)"),
        
        # English URLs (should return None for URL detection, default to English)
        ("https://www.microsoft.com/en-us/customers/story/some-story", None),
        ("https://customers.microsoft.com/en-us/story/another-story", None),
        
        # Other languages to test
        ("https://www.microsoft.com/de-de/customers/story/german-story", "German"),
        ("https://www.microsoft.com/fr-fr/customers/story/french-story", "French"),
        ("https://www.microsoft.com/es-es/customers/story/spanish-story", "Spanish"),
    ]
    
    passed = 0
    failed = 0
    
    for url, expected in test_urls:
        result = detector.detect_language_from_url(url)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {url}")
        print(f"     Expected: {expected}, Got: {result}")
        print()
    
    print(f"URL Detection Tests: {passed} passed, {failed} failed")
    return failed == 0

def test_content_based_detection():
    """Test content-based language detection"""
    print("=" * 60)
    print("TESTING CONTENT-BASED LANGUAGE DETECTION")
    print("=" * 60)
    
    detector = LanguageDetector()
    
    test_content = [
        # Japanese text
        ("Azure OpenAI Service で価値創造に挑むコニカミノルタの生成 AI 活用", "Japanese"),
        
        # Korean text  
        ("크래프톤, Microsoft 365 Copilot으로 AI와 함께 일하는 차세대 업무 환경 구축", "Korean"),
        
        # Chinese text
        ("装上AI飞轮，微软智能副驾助力均胜电子全球运营再提速", "Chinese"),
        
        # English text (should return None for content detection)
        ("Microsoft Customer Success Story with Azure AI", None),
        
        # Mixed content (mostly English with some non-English)
        ("Microsoft Azure AI で価値創造 - building value with AI", None),  # Not enough non-English chars
    ]
    
    passed = 0
    failed = 0
    
    for content, expected in test_content:
        result = detector.detect_language_from_content(content)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Content: {content[:50]}...")
        print(f"     Expected: {expected}, Got: {result}")
        print()
    
    print(f"Content Detection Tests: {passed} passed, {failed} failed")
    return failed == 0

def test_comprehensive_detection():
    """Test the main detect_language function"""
    print("=" * 60)
    print("TESTING COMPREHENSIVE LANGUAGE DETECTION")
    print("=" * 60)
    
    test_cases = [
        # URL-based detection (highest confidence)
        {
            'url': 'https://www.microsoft.com/ja-jp/customers/story/18738-konica-minolta',
            'title': 'Some English Title',
            'content': 'English content here',
            'expected_lang': 'Japanese',
            'expected_method': 'url_pattern',
            'min_confidence': 0.90
        },
        
        # Title-based detection (medium confidence)
        {
            'url': 'https://www.microsoft.com/en-us/customers/story/some-story',
            'title': '크래프톤, Microsoft 365 Copilot으로 차세대 업무 환경',
            'content': 'English content here',
            'expected_lang': 'Korean',
            'expected_method': 'title_analysis', 
            'min_confidence': 0.70
        },
        
        # English default (lowest confidence)
        {
            'url': 'https://www.microsoft.com/en-us/customers/story/some-story',
            'title': 'English Title Here',
            'content': 'English content with no foreign characters',
            'expected_lang': 'English',
            'expected_method': 'default',
            'min_confidence': 0.20
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = detect_story_language(case['url'], case['title'], case['content'])
        
        lang_match = result['normalized'] == case['expected_lang'] or result['language'] == case['expected_lang']
        method_match = result['method'] == case['expected_method']
        confidence_ok = result['confidence'] >= case['min_confidence']
        
        all_pass = lang_match and method_match and confidence_ok
        status = "✅ PASS" if all_pass else "❌ FAIL"
        
        if all_pass:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Test Case {i}:")
        print(f"     URL: {case['url'][:60]}...")
        print(f"     Title: {case['title'][:40]}...")
        print(f"     Expected: {case['expected_lang']} via {case['expected_method']}")
        print(f"     Got: {result['language']} ({result['normalized']}) via {result['method']}")
        print(f"     Confidence: {result['confidence']:.2f} (min: {case['min_confidence']:.2f})")
        
        if not lang_match:
            print(f"     ❌ Language mismatch")
        if not method_match:
            print(f"     ❌ Method mismatch") 
        if not confidence_ok:
            print(f"     ❌ Confidence too low")
        print()
    
    print(f"Comprehensive Tests: {passed} passed, {failed} failed")
    return failed == 0

def test_with_real_database_stories():
    """Test with actual stories from database"""
    print("=" * 60)
    print("TESTING WITH REAL DATABASE STORIES")
    print("=" * 60)
    
    # Test data from our known non-English stories
    real_stories = [
        {
            'url': 'https://www.microsoft.com/ja-jp/customers/story/18738-konica-minolta-azure-open-ai-service',
            'title': 'Azure OpenAI Service で価値創造に挑むコニカミノルタの生成 AI 活用',
            'customer': 'Konica Minolta',
            'expected': 'Japanese'
        },
        {
            'url': 'https://www.microsoft.com/ko-kr/customers/story/19277-krafton-microsoft-365',
            'title': '크래프톤, Microsoft 365 Copilot으로 AI와 함께 일하는 차세대 업무 환경 구축',
            'customer': 'Krafton',
            'expected': 'Korean'
        },
        {
            'url': 'https://www.microsoft.com/zh-cn/customers/story/1791859496343328428-joyson-microsoft-copilot-for-microsoft-365-discrete-manufacturing-zh-china',
            'title': '装上AI飞轮，微软智能副驾助力均胜电子全球运营再提速',
            'customer': 'Joyson Electronics',
            'expected': 'Chinese'
        }
    ]
    
    passed = 0
    failed = 0
    
    for story in real_stories:
        result = detect_story_language(story['url'], story['title'])
        
        # Check if detected language matches expected (allowing for variations like "Chinese (Simplified)")
        detected = result['normalized']
        expected = story['expected']
        
        is_correct = (detected == expected or 
                     (expected == 'Chinese' and 'Chinese' in detected) or
                     detected in expected)
        
        status = "✅ PASS" if is_correct else "❌ FAIL"
        
        if is_correct:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {story['customer']}")
        print(f"     Expected: {expected}")
        print(f"     Detected: {detected} (confidence: {result['confidence']:.2f})")
        print(f"     Method: {result['method']}")
        print(f"     URL: {story['url'][:60]}...")
        print()
    
    print(f"Real Story Tests: {passed} passed, {failed} failed")
    return failed == 0

def main():
    """Run all language detection tests"""
    print("LANGUAGE DETECTION TESTING SUITE")
    print("=" * 60)
    
    all_passed = True
    
    # Run all test suites
    test_results = [
        test_url_based_detection(),
        test_content_based_detection(), 
        test_comprehensive_detection(),
        test_with_real_database_stories()
    ]
    
    all_passed = all(test_results)
    
    print("=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! Language detection is ready for production use.")
        print()
        print("Next steps:")
        print("1. Add language column to database schema")
        print("2. Implement safe backfill process")
        print("3. Integrate into story processing pipeline")
    else:
        print("❌ SOME TESTS FAILED! Review and fix issues before production use.")
        print()
        print("Failed test suites:")
        test_names = ["URL Detection", "Content Detection", "Comprehensive Detection", "Real Stories"]
        for i, passed in enumerate(test_results):
            if not passed:
                print(f"  - {test_names[i]}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)