# AI Customer Stories Database - Technical Documentation

## Architecture & Key Technologies

- **Database**: PostgreSQL 14+ with JSONB support and full-text search
- **AI Integration**: Anthropic Claude API for intelligent data extraction
- **Web Scraping**: Provider-specific scrapers with advanced bot protection handling
- **Data Processing**: 4-dimensional Gen AI classification framework
- **Dashboard**: Streamlit-based web interface with Plotly visualizations
- **Deduplication**: Per-source and cross-source customer profiling system

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+ with JSONB support
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-stories

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database credentials

# Initialize database
python scripts/maintenance/setup_database.py

# Start dashboard
streamlit run dashboard.py
```

## Dashboard Launch Methods

### Method 1: Direct Streamlit Command (Recommended)
```bash
streamlit run dashboard.py
```

**Benefits:**
- Fastest startup - No overhead, direct execution
- Simplest command - Standard Streamlit approach
- Maximum flexibility - Full access to all Streamlit CLI options
- Clean output - Direct Streamlit logs without wrapper noise
- Easy debugging - Direct error messages from Streamlit

**Examples:**
```bash
# Basic launch
streamlit run dashboard.py

# Custom port
streamlit run dashboard.py --server.port 8502

# Development mode with file watching
streamlit run dashboard.py --server.runOnSave true

# External access
streamlit run dashboard.py --server.address 0.0.0.0
```

### Method 2: Production Launcher Script
```bash
python scripts/production/run_dashboard.py
```

**Benefits:**
- Pre-flight validation - Checks dependencies and database before starting
- Automatic browser opening - Opens http://localhost:8501 after 3 seconds
- Environment validation - Confirms system is ready to run
- Story count display - Shows how many stories are in your database
- Error prevention - Catches common setup issues early

**Use When:**
- First-time setup or after system changes
- You want validation that everything is working
- Running in production/deployment scenarios
- Troubleshooting connectivity issues

## Language Detection System API

### Core Module (`src/utils/language_detection.py`)

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

**Example Usage:**
```python
from src.utils.language_detection import detect_story_language

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

### Language Statistics Module (`src/utils/language_stats.py`)

#### `LanguageStatistics` Class

Provides comprehensive language analytics for the customer stories database.

##### Key Methods:
- `get_language_distribution(source_name: Optional[str] = None) -> Dict[str, int]`
- `get_language_stats_by_source() -> Dict[str, Dict[str, int]]`
- `get_non_english_stories(limit: int = 50) -> List[Dict]`
- `print_language_summary()`

### Database Integration

#### CustomerStory Dataclass Fields

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

```sql
-- Language detection columns
detected_language VARCHAR(50) DEFAULT 'English',
language_detection_method VARCHAR(50) DEFAULT 'default',
language_confidence FLOAT DEFAULT 0.30
```

## Aileron GenAI Framework (4-Dimensional Analysis)

### Classification Dimensions

1. **Superpowers**: Code, Create Content, Automate with Agents, Find Data Insights, Research, Brainstorm, Natural Language
2. **Business Impacts**: Innovation, Efficiency, Speed, Quality, Client Satisfaction, Risk Reduction  
3. **Adoption Enablers**: Data & Digital, Innovation Culture, Ecosystem Partners, Policy & Governance, Risk Management
4. **Business Function**: Marketing, Sales, Production, Distribution, Service, Finance & Accounting

### Implementation

- **Enhanced prompts.py**: Integrated formal Aileron definitions
- **Updated claude_processor.py**: Extended validation for classification fields
- **Modified models.py**: Added Gen AI fields to CustomerStory dataclass

## Database Management

### Status & Updates
```bash
# Check current status
python scripts/production/update_all_databases.py status

# Update all sources
python scripts/production/update_all_databases.py update --source all

# Update specific source
python scripts/production/update_all_databases.py update --source anthropic

# Run deduplication analysis
python scripts/production/update_all_databases.py dedup
```

### Query & Analytics
```bash
# Interactive query interface
python scripts/production/query_stories.py

# Search stories
python scripts/production/query_stories.py search "machine learning"

# Language statistics
python scripts/production/query_stories.py languages
```

## System Architecture

### Directory Structure
```
ai-stories/
├── dashboard.py                 # Main Streamlit dashboard
├── run_scraper.py              # Main scraper tool
├── requirements.txt            # Python dependencies
├── pytest.ini                 # Test configuration
├── src/                        # Core application code
│   ├── ai_integration/         # Claude API processing
│   ├── classification/         # Enhanced classifier
│   ├── dashboard/              # Modular dashboard components
│   ├── database/               # Database models and operations
│   ├── scrapers/               # Provider-specific scrapers
│   └── utils/                  # Utility modules
├── scripts/                    # Management and utility scripts
│   ├── data_extraction/        # Data extraction tools
│   ├── development/            # Development utilities
│   ├── maintenance/            # Database maintenance
│   └── production/             # Production management
├── tests/                      # Test suite
└── data/                       # Static data files
```

### Dashboard Structure
```
src/dashboard/
├── core/
│   ├── data_loader.py          # Database operations with @st.cache_data
│   ├── data_processor.py       # Data filtering/transformation
│   ├── config.py               # Dashboard configuration constants
│   └── brand_styles.py         # UI styling and branding
├── pages/
│   ├── overview.py             # Overview page logic
│   ├── explorer.py             # Story Explorer page  
│   ├── analytics.py            # Analytics Dashboard page
│   ├── aileron.py              # Aileron GenAI Framework page
│   └── export.py               # Data Export functionality
└── components/
    └── charts.py               # Reusable chart components
```

## Performance Considerations

- **URL Pattern Detection**: O(1) lookup time with regex matching
- **Content Analysis**: O(n) where n is content length, optimized with early termination
- **Database Queries**: Indexed on `detected_language` for efficient filtering
- **Memory Usage**: Minimal overhead, no external language libraries required

## Testing

```bash
# Run full test suite
pytest

# Run language detection tests
pytest tests/ -k language -v

# Run dashboard integration tests
pytest tests/test_dashboard_integration.py -v

# Test specific detection methods
python -c "from src.utils.language_detection import detect_story_language; print(detect_story_language('https://customers.microsoft.com/ja-jp/test', 'テスト', 'テスト内容'))"
```

## Troubleshooting

### Dashboard Launch Issues
1. Check if you're in the right directory (should see `dashboard.py`)
2. Verify Streamlit is installed: `pip install streamlit`
3. Try production launcher for detailed diagnostics: `python scripts/production/run_dashboard.py`

### Database Connection Issues
1. Check PostgreSQL service is running
2. Verify database credentials in `.env` file
3. Test connection: `python -c "from src.database.models import DatabaseOperations; print('DB OK')"`

### Common Issues
- **Missing dependencies** → Run `pip install -r requirements.txt`
- **Database not running** → Start your PostgreSQL service
- **Port conflicts** → Use custom port with `--server.port 8502`

## Error Handling

The system includes comprehensive error handling:

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

## System Features

- ✅ **Incremental Updates**: Only processes new stories
- ✅ **Error Recovery**: Graceful timeout handling with progress preservation
- ✅ **Data Validation**: Claude AI validates all extracted data
- ✅ **Quality Assurance**: 100% business outcome validation
- ✅ **Advanced Deduplication**: Zero duplicate stories across all sources
- ✅ **Cross-Source Analytics**: Customer profiling for competitive intelligence

## Production Status

**Current System Scale**: 191 high-quality customer stories across 5 major AI providers:
- **Anthropic**: 129 stories
- **OpenAI**: 33 stories  
- **AWS AI/ML**: 10 stories
- **Google Cloud AI**: 10 stories
- **Microsoft Azure**: 9 stories

**System Capabilities**:
- 100% Data Completeness: All stories have complete extracted data and classifications
- Aileron GenAI Framework: 4-dimensional classification system fully implemented
- Advanced Analytics: Comprehensive business intelligence across all industries
- Production Ready: Automated scraping, processing, and classification pipeline

---

*For implementation details, see the source code in the respective modules and the comprehensive test suite.*