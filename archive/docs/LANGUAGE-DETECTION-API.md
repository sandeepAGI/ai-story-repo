# Language Detection System API Documentation

## Overview

The AI Customer Stories Database includes a comprehensive language detection system that automatically identifies and classifies story languages with confidence scoring. This document provides detailed API documentation for developers working with the language detection features.

## Core Components

### 1. Language Detection Module (`src/utils/language_detection.py`)

#### `detect_story_language(url: str, title: str, content: str) -> Dict[str, Any]`

Detects the language of a customer story using multiple detection methods.

**Parameters:**
- `url` (str): The story URL for pattern analysis
- `title` (str): The story title for content analysis  
- `content` (str): The story content for character analysis

**Returns:**
```python
{
    'language': str,        # Full language name (e.g., 'Japanese')
    'method': str,          # Detection method used
    'confidence': float,    # Confidence score (0.30-0.95)
    'normalized': str       # Normalized language name
}
```

**Detection Methods:**

1. **URL Pattern Detection** (Confidence: 0.95)
   ```python
   # Microsoft URL patterns
   '/ja-jp/' -> Japanese
   '/ko-kr/' -> Korean  
   '/zh-cn/' -> Chinese
   ```

2. **Content Analysis** (Confidence: 0.70)
   ```python
   # Unicode character range detection
   CJK_RANGES = [
       (0x4E00, 0x9FFF),   # CJK Unified Ideographs
       (0x3400, 0x4DBF),   # CJK Extension A
       (0x20000, 0x2A6DF), # CJK Extension B
       (0x3040, 0x309F),   # Hiragana (Japanese)
       (0x30A0, 0x30FF),   # Katakana (Japanese)
       (0xAC00, 0xD7AF)    # Hangul (Korean)
   ]
   ```

3. **Default Assignment** (Confidence: 0.30)
   - English fallback for unknown patterns
   - Maintains backward compatibility

**Example Usage:**
```python
from src.utils.language_detection import detect_story_language

# Detect language from story data
result = detect_story_language(
    url='https://customers.microsoft.com/ja-jp/story/example',
    title='テストタイトル',
    content='テスト内容'
)

print(result)
# Output: {
#     'language': 'Japanese',
#     'method': 'url_pattern', 
#     'confidence': 0.95,
#     'normalized': 'Japanese'
# }
```

### 2. Language Statistics Module (`src/utils/language_stats.py`)

#### `LanguageStatistics` Class

Provides comprehensive language analytics for the customer stories database.

##### `get_language_distribution(source_name: Optional[str] = None) -> Dict[str, int]`

Get language distribution across all stories or for a specific source.

**Parameters:**
- `source_name` (Optional[str]): Filter by source name (e.g., 'Microsoft')

**Returns:**
```python
{
    'English': 848,
    'Korean': 3,
    'Japanese': 1,
    'Chinese': 1
}
```

##### `get_language_stats_by_source() -> Dict[str, Dict[str, int]]`

Get language distribution broken down by AI provider source.

**Returns:**
```python
{
    'Microsoft': {'English': 645, 'Korean': 3, 'Japanese': 1, 'Chinese': 1},
    'Anthropic': {'English': 129},
    'OpenAI': {'English': 33},
    'AWS': {'English': 25},
    'Google Cloud': {'English': 18}
}
```

##### `get_non_english_stories(limit: int = 50) -> List[Dict]`

Get details of non-English stories with confidence scores.

**Returns:**
```python
[
    {
        'customer_name': 'Company Name',
        'title': 'Story Title',
        'url': 'https://example.com/story',
        'detected_language': 'Korean',
        'language_detection_method': 'url_pattern',
        'language_confidence': 0.95,
        'source_name': 'Microsoft'
    }
]
```

##### `print_language_summary()`

Print comprehensive language statistics to console.

**Example Output:**
```
======================================================================
LANGUAGE DISTRIBUTION SUMMARY
======================================================================

OVERALL DISTRIBUTION (853 total stories):
--------------------------------------------------
English             :  848 stories (99.4%)
Korean              :    3 stories ( 0.4%)
Japanese            :    1 stories ( 0.1%)
Chinese             :    1 stories ( 0.1%)

LANGUAGE DISTRIBUTION BY SOURCE:
--------------------------------------------------

Microsoft (648 stories):
  English           :  645 stories (99.5%)
  Korean            :    3 stories ( 0.5%)
  Japanese          :    1 stories ( 0.2%)
  Chinese           :    1 stories ( 0.2%)
```

### 3. Database Integration

#### CustomerStory Dataclass Fields

Language detection adds three fields to the `CustomerStory` dataclass:

```python
@dataclass
class CustomerStory:
    # ... existing fields ...
    
    # Language detection fields
    detected_language: Optional[str] = 'English'
    language_detection_method: Optional[str] = 'default'
    language_confidence: Optional[float] = 0.30
```

#### Database Schema

The `customer_stories` table includes language columns:

```sql
-- Language detection columns
detected_language VARCHAR(50) DEFAULT 'English',
language_detection_method VARCHAR(50) DEFAULT 'default',
language_confidence FLOAT DEFAULT 0.30
```

#### Database Operations

Language fields are automatically included in all database operations:

```python
# Insert story with language detection
story_id = db_ops.insert_customer_story(customer_story)

# Query stories by language
stories = db_ops.search_stories("korean story example")
```

### 4. CLI Integration

#### Language Statistics Command

```bash
# View comprehensive language distribution
python query_stories.py languages
```

#### Available Query Commands

```bash
# Database summary with language info
python query_stories.py stats

# Search stories (language-aware)
python query_stories.py search "korean"

# Customer details (includes language)
python query_stories.py customer "Company Name"
```

## Integration Examples

### Processing Pipeline Integration

Language detection is automatically integrated into the main processing pipeline:

```python
# In src/main.py:L267-278
language_info = detect_story_language(
    story['url'], 
    story.get('title', ''),
    story.get('raw_content', {}).get('text', '')
)

# Update customer_story with language information
customer_story.detected_language = language_info['normalized']
customer_story.language_detection_method = language_info['method']
customer_story.language_confidence = language_info['confidence']
```

### Custom Analytics Integration

```python
from src.utils.language_stats import LanguageStatistics

# Initialize statistics engine
stats = LanguageStatistics()

# Get language distribution for Microsoft stories
ms_languages = stats.get_language_distribution('Microsoft')

# Get all non-English stories
non_english = stats.get_non_english_stories(limit=10)

# Print comprehensive summary
stats.print_language_summary()
```

### Filtering and Querying

```python
from src.database.models import DatabaseOperations

db_ops = DatabaseOperations()

# Custom query for non-English stories
query = """
SELECT customer_name, title, detected_language, language_confidence
FROM customer_stories 
WHERE detected_language != 'English'
ORDER BY language_confidence DESC
"""

with db_ops.db.get_cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()
```

## Error Handling

The language detection system includes comprehensive error handling:

```python
try:
    result = detect_story_language(url, title, content)
    # Process result
except Exception as e:
    # Falls back to English with low confidence
    result = {
        'language': 'English',
        'method': 'error_fallback',
        'confidence': 0.30,
        'normalized': 'English'
    }
```

## Performance Considerations

- **URL Pattern Detection**: O(1) lookup time with regex matching
- **Content Analysis**: O(n) where n is content length, optimized with early termination
- **Database Queries**: Indexed on `detected_language` for efficient filtering
- **Memory Usage**: Minimal overhead, no external language libraries required

## Testing

Comprehensive test coverage with 28+ test cases:

```bash
# Run language detection tests
python -m pytest tests/ -k language -v

# Test specific detection methods
python -c "from src.utils.language_detection import detect_story_language; print(detect_story_language('https://customers.microsoft.com/ja-jp/test', 'テスト', 'テスト内容'))"
```

## Future Enhancements

- **Machine Learning Integration**: Advanced language detection using ML models
- **Translation Support**: Automatic translation for cross-language analysis
- **Regional Analytics**: Geographic AI adoption pattern analysis based on language
- **Confidence Tuning**: Dynamic confidence adjustment based on multiple factors

## Version History

- **v1.0** (2025-08-03): Initial implementation with URL pattern and content analysis
- Multi-method detection with confidence scoring
- Full database and pipeline integration
- Comprehensive analytics and CLI support

---

*For implementation details, see the source code in `src/utils/language_detection.py` and `src/utils/language_stats.py`*