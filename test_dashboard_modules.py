#!/usr/bin/env python3
"""
Test script to validate the modular dashboard structure
Tests all imports and basic functionality without requiring database connection
"""

import sys
import os
import traceback

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_core_imports():
    """Test core module imports"""
    print("🧪 Testing core module imports...")
    
    try:
        from src.dashboard.core.config import PAGE_CONFIG, DASHBOARD_PAGES
        print("✅ Config module imported successfully")
        print(f"   - Page config keys: {list(PAGE_CONFIG.keys())}")
        print(f"   - Dashboard pages: {DASHBOARD_PAGES}")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from src.dashboard.core.data_processor import create_download_data, format_chart_title
        print("✅ Data processor module imported successfully")
    except Exception as e:
        print(f"❌ Data processor import failed: {e}")
        return False
    
    return True


def test_page_imports():
    """Test page module imports"""
    print("\n🧪 Testing page module imports...")
    
    pages = ['overview', 'explorer', 'analytics', 'aileron', 'export']
    success_count = 0
    
    for page in pages:
        try:
            module = __import__(f'src.dashboard.pages.{page}', fromlist=[''])
            print(f"✅ {page.capitalize()} page imported successfully")
            success_count += 1
        except Exception as e:
            print(f"❌ {page.capitalize()} page import failed: {e}")
            traceback.print_exc()
    
    return success_count == len(pages)


def test_component_imports():
    """Test component module imports"""
    print("\n🧪 Testing component module imports...")
    
    try:
        from src.dashboard.components.charts import create_industry_pie_chart
        print("✅ Chart components imported successfully")
        return True
    except Exception as e:
        print(f"❌ Chart components import failed: {e}")
        traceback.print_exc()
        return False


def test_data_processor_functions():
    """Test data processor functions"""
    print("\n🧪 Testing data processor functions...")
    
    try:
        import pandas as pd
        from src.dashboard.core.data_processor import format_chart_title, calculate_summary_stats
        
        # Test format_chart_title
        title = "This is a very long chart title that should be wrapped"
        formatted = format_chart_title(title, max_length=20)
        print(f"✅ Chart title formatting works: '{formatted}'")
        
        # Test with sample DataFrame
        sample_data = {
            'customer_name': ['Company A', 'Company B'],
            'industry': ['tech', 'healthcare'],
            'is_gen_ai': [True, False],
            'source_name': ['Anthropic', 'OpenAI'],
            'extracted_data': [
                {'content_quality_score': 0.85},
                {'content_quality_score': 0.92}
            ]
        }
        df = pd.DataFrame(sample_data)
        
        stats = calculate_summary_stats(df)
        print(f"✅ Summary stats calculation works: {stats['total_stories']} total stories")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processor function test failed: {e}")
        traceback.print_exc()
        return False


def test_directory_structure():
    """Test that all expected directories and files exist"""
    print("\n🧪 Testing directory structure...")
    
    expected_files = [
        'src/dashboard/__init__.py',
        'src/dashboard/core/__init__.py',
        'src/dashboard/core/data_loader.py',
        'src/dashboard/core/data_processor.py',
        'src/dashboard/core/config.py',
        'src/dashboard/pages/__init__.py',
        'src/dashboard/pages/overview.py',
        'src/dashboard/pages/explorer.py',
        'src/dashboard/pages/analytics.py',
        'src/dashboard/pages/aileron.py',
        'src/dashboard/pages/export.py',
        'src/dashboard/components/__init__.py',
        'src/dashboard/components/charts.py',
        'src/dashboard/utils/__init__.py',
    ]
    
    success_count = 0
    for file_path in expected_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
            success_count += 1
        else:
            print(f"❌ {file_path} - MISSING")
    
    print(f"\n📊 Directory structure: {success_count}/{len(expected_files)} files present")
    return success_count == len(expected_files)


def main():
    """Run all tests"""
    print("🚀 Testing Modular Dashboard Structure")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Core Imports", test_core_imports),
        ("Page Imports", test_page_imports),
        ("Component Imports", test_component_imports),
        ("Data Processor Functions", test_data_processor_functions),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} - PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "="*50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dashboard modularization successful!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)