#!/usr/bin/env python3
"""
Debug script to analyze the JSON parsing failure
"""
import json

# The exact JSON response that's failing (from the error log)
failing_json = """{
  "is_gen_ai": false,
  "confidence": 0.9,
  "classification_method": "definitive_traditional",
  "reasoning": "The story describes traditional AI and analytics applications focused on satellite imagery analysis, data processing, and business intelligence. The use cases center around data analysis, pattern recognition, and geospatial insights rather than generative capabilities. The technologies mentioned (BigQuery, Earth Engine, Cloud Storage) are classic cloud computing and analytics tools.",
  "key_indicators": [
    "BigQuery analytics",
    "Earth Engine for satellite imagery analysis",
    "Cloud Storage",
    "Search analytics for marketing insights",
    "Geospatial data processing",
    "Data analysis and visualization"
  ],
  "ambiguous_terms_found": [
    "AI" (generic mention without specific capabilities)
  ],
  "supporting_evidence": [
    "Focus on data analysis rather than content generation",
    "Use of traditional analytics platforms (BigQuery)",
    "Emphasis on data processing and visualization",
    "Marketing insights derived from search analytics rather than generative content"
  ],
  "confidence_factors": {
    "definitive_indicators": [
      "BigQuery",
      "Cloud Storage",
      "Earth Engine",
      "Traditional analytics workflows"
    ],
    "supporting_context": [
      "Use case focuses on data analysis and visualization",
      "No mention of LLMs or generative capabilities",
      "Implementation predates widespread GenAI adoption"
    ],
    "uncertainty_factors": [
      "Generic mentions of 'AI' without specific implementation details"
    ]
  }
}"""

def analyze_json_error():
    print("=== JSON Parsing Debug Analysis ===")
    print(f"JSON length: {len(failing_json)} characters")
    print()
    
    # Try to parse and catch the exact error
    try:
        parsed = json.loads(failing_json)
        print("✅ JSON parsing successful!")
        print(f"Keys found: {list(parsed.keys())}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"Error position: {e.pos}")
        print(f"Line number: {e.lineno}")
        print(f"Column number: {e.colno}")
        print()
        
        # Analyze the character at the error position
        if e.pos < len(failing_json):
            error_char = failing_json[e.pos]
            print(f"Character at error position {e.pos}: '{error_char}' (ASCII: {ord(error_char)})")
            
            # Show context around the error
            start = max(0, e.pos - 50)
            end = min(len(failing_json), e.pos + 50)
            context = failing_json[start:end]
            print(f"Context around error (±50 chars):")
            print(f"'{context}'")
            print(" " * (e.pos - start) + "^" + " ERROR HERE")
            print()
            
            # Show the specific line where error occurs
            lines = failing_json.split('\n')
            if e.lineno <= len(lines):
                error_line = lines[e.lineno - 1]  # lineno is 1-based
                print(f"Error line {e.lineno}: '{error_line}'")
                print(" " * (e.colno - 1) + "^" + " ERROR COLUMN")
                print()
        
        return False

def check_for_hidden_characters():
    print("=== Hidden Character Analysis ===")
    
    # Check for common problematic characters
    problematic_chars = []
    for i, char in enumerate(failing_json):
        # Check for non-printable characters (except standard whitespace)
        if not char.isprintable() and char not in ['\n', '\r', '\t', ' ']:
            problematic_chars.append((i, char, ord(char)))
    
    if problematic_chars:
        print(f"Found {len(problematic_chars)} problematic characters:")
        for pos, char, ascii_val in problematic_chars:
            print(f"  Position {pos}: '{repr(char)}' (ASCII: {ascii_val})")
    else:
        print("No hidden/non-printable characters found")
    print()

def identify_json_structure_issue():
    print("=== JSON Structure Analysis ===")
    
    # Look for common JSON issues
    issues = []
    
    # Check for unescaped quotes in string values
    import re
    
    # Find string values that might have unescaped content
    string_pattern = r'"[^"]*"'
    matches = re.finditer(string_pattern, failing_json)
    
    for match in matches:
        string_content = match.group()
        # Check if this string contains parentheses without proper escaping
        if '(' in string_content and ')' in string_content:
            # Check if it's in an array context where it might be causing issues
            start_pos = match.start()
            # Look backwards to see if we're in an array
            preceding_text = failing_json[max(0, start_pos-20):start_pos]
            if '[' in preceding_text and ']' not in preceding_text:
                issues.append(f"Potential unescaped content in array at position {start_pos}: {string_content}")
    
    if issues:
        print("Potential JSON structure issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("No obvious JSON structure issues detected")
    print()

def test_fixes():
    print("=== Testing Potential Fixes ===")
    
    # Fix 1: The issue might be the parentheses in array elements
    # Looking at the JSON, this line is suspicious:
    # "AI" (generic mention without specific capabilities)
    # This is not valid JSON - should be quoted
    
    fixed_json = failing_json.replace(
        '"AI" (generic mention without specific capabilities)',
        '"AI (generic mention without specific capabilities)"'
    )
    
    print("Testing fix for unquoted parenthetical content...")
    try:
        parsed = json.loads(fixed_json)
        print("✅ Fix successful! The issue was unquoted parenthetical content in array.")
        return fixed_json
    except json.JSONDecodeError as e:
        print(f"❌ Fix failed: {e}")
    
    return None

if __name__ == "__main__":
    # Run all analysis
    success = analyze_json_error()
    if not success:
        check_for_hidden_characters()
        identify_json_structure_issue()
        fixed_json = test_fixes()
        
        if fixed_json:
            print("=== Suggested Fix ===")
            print("The JSON contains unquoted parenthetical content in array elements.")
            print("This needs to be properly quoted to be valid JSON.")