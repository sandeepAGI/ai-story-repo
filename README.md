# AI Customer Stories Database

A comprehensive database and analysis platform for AI customer success stories from the world's leading AI providers: Anthropic, OpenAI, Microsoft Azure, AWS, and Google Cloud Platform.

## Overview

This project scrapes, processes, and analyzes AI customer stories to provide competitive intelligence and market insights. Using Claude AI for intelligent data extraction, it creates a structured database of real-world AI implementations with detailed business outcomes and metrics.

## Features

### 🎯 **Multi-Provider Coverage**
- **Anthropic**: Customer success stories with Claude AI implementations
- **OpenAI**: GPT and AI platform customer cases  
- **Microsoft Azure**: Azure AI and Copilot implementations
- **AWS**: Amazon Bedrock and AI/ML customer stories
- **Google Cloud**: Vertex AI and Gemini customer implementations

### 🤖 **Intelligent Data Processing**
- **Claude AI Integration**: Automated extraction of structured data from raw content
- **4-Dimensional Gen AI Classification**: Superpowers, Business Impacts, Adoption Enablers, Business Functions
- **Content Quality Scoring**: Automated assessment of story completeness and detail
- **Language Detection System**: Automated detection of story language with confidence scoring
- **Deduplication System**: Two-tiered approach with URL-based insertion prevention and post-processing analysis

### 📊 **Rich Analytics**
- **Business Outcomes Tracking**: Quantified metrics (cost savings, time reduction, productivity gains)
- **Technology Usage Patterns**: AI services and tools mentioned across stories
- **Industry Analysis**: Sector-specific AI adoption trends
- **Language Distribution Analytics**: Multi-language story analysis with confidence metrics
- **Competitive Intelligence**: Cross-provider comparison and analysis

### 🛠️ **Production-Ready Architecture**
- **PostgreSQL Database**: Full-text search with JSONB support for flexible content storage
- **Robust Scraping**: Rate-limited, error-handling web scrapers for each provider
- **CLI Management Tools**: Comprehensive command-line utilities for database operations
- **Automated Updates**: Incremental processing with change detection

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
# Edit .env with your database URL and Anthropic API key
```

### Database Setup

```bash
# Initialize PostgreSQL database with schema
psql -d your_database < src/database/schema.sql
```

### Basic Usage

```bash
# Update all AI provider databases
python update_all_databases.py update --source all

# Check database status
python update_all_databases.py status

# Query specific stories
python query_stories.py search "machine learning"

# Show detailed analytics
python show_stories.py --analytics

# View language distribution statistics
python query_stories.py languages
```

## Database Schema

### Core Tables
- **`sources`**: AI provider information and scraping metadata
- **`customer_stories`**: Main stories with full content, extracted data, and language information
- **`technologies`**: AI services and tools mentioned in stories
- **`story_metrics`**: Quantified business outcomes and metrics

### Advanced Features
- **Full-text search** with PostgreSQL tsvector
- **JSONB storage** for flexible raw content and extracted data
- **Language detection** with URL pattern analysis and content-based detection
- **Cross-source customer profiling** for competitive analysis
- **Publication date estimation** with confidence levels

## Gen AI Classification Framework

### Four Dimensions
1. **Superpowers** (Capabilities): Code, Create Content, Automate with Agents, Find Data Insights, Research, Brainstorm, Natural Language
2. **Business Impacts** (Outcomes): Innovation, Efficiency, Speed, Quality, Client Satisfaction, Risk Reduction  
3. **Adoption Enablers** (Prerequisites): Data & Digital, Innovation Culture, Ecosystem Partners, Policy & Governance, Risk Management
4. **Business Function** (Context): Marketing, Sales, Production, Distribution, Service, Finance & Accounting

## Language Detection System

### Detection Methods
1. **URL Pattern Analysis** (High Confidence: 0.95)
   - Microsoft: `/ja-jp/`, `/ko-kr/`, `/zh-cn/` patterns
   - Other providers: Similar locale-based URL patterns

2. **Content Analysis** (Medium Confidence: 0.70)
   - Character range detection for CJK languages
   - Unicode block analysis for East Asian characters

3. **Default Assignment** (Low Confidence: 0.30)
   - English default for undetectable cases
   - Maintains backward compatibility

### Language Statistics Command
```bash
# View comprehensive language distribution
python query_stories.py languages
```

**Sample Output**:
- Overall distribution by language with percentages
- Language breakdown by AI provider source
- Top non-English stories with confidence scores
- Language detection method statistics

### Database Integration
- **Language Fields**: `detected_language`, `language_detection_method`, `language_confidence`
- **Automatic Processing**: All new stories get language detection
- **Query Support**: Filter and analyze stories by language
- **Analytics Integration**: Language distribution in dashboard

## Current Database Stats

- **850+ High-Quality Stories** across all 5 major AI providers (with Phase 5 Microsoft enhancement)
- **100% Data Completeness** with zero missing critical fields
- **Average Quality Score**: 0.863 (range: 0.70-0.90)
- **Multi-Language Support**: Language detection with 5 non-English stories identified
- **Rich Business Outcomes**: All stories contain quantified metrics
- **Date Range**: 2016-2025 with transparent estimated vs. actual dates

### Enhanced Microsoft Collection (Phase 5)
- **Pre-Phase 5**: 60 Microsoft stories
- **Post-Phase 5**: 648 Microsoft stories (10x improvement)
- **Multi-Language Stories**: 5 non-English stories (3 Korean, 1 Japanese, 1 Chinese)
- **Source**: Microsoft's official 1000+ AI stories blog post
- **Method**: Pre-collected URL approach with smart fallback

## Deduplication System

The system implements a **two-tiered deduplication approach** with distinct purposes:

### 1. Pre-Insert Duplicate Prevention
- **Function**: `check_story_exists()` in database operations
- **Purpose**: Prevents duplicate URLs from being inserted during scraping
- **Scope**: Exact URL matching only
- **When**: During scraping/insertion process
- **Action**: Blocks duplicate insertion

### 2. Post-Insert Deduplication Analysis  
- **Function**: `DeduplicationEngine` class in `src/utils/deduplication.py`
- **Purpose**: Analytical tool for finding sophisticated duplicates in existing data
- **Scope**: Content similarity, company name normalization, cross-source analysis
- **When**: Run manually via `python query_stories.py dedup`
- **Action**: **Reports findings but does NOT remove duplicates**

### Key Features
- **Company Name Normalization**: Removes business suffixes, special characters
- **Content Similarity**: Compares story content using sequence matching
- **Cross-Source Analysis**: Identifies customers appearing across multiple AI providers
- **Customer Profiling**: Creates unified profiles for multi-source customers
- **Weighted Scoring**: 30% company name + 50% content + 20% title similarity

### Important Note
⚠️ **The sophisticated deduplication analysis does NOT prevent database insertion.** It identifies duplicates for reporting and analysis purposes while preserving all original stories in the database.

## Architecture

```
ai_customer_stories/
├── src/
│   ├── database/          # Database models and operations
│   ├── scrapers/          # Provider-specific scrapers
│   ├── ai_integration/    # Claude AI processing
│   └── utils/             # Utilities and helpers
│       ├── language_detection.py    # Language detection system
│       └── language_stats.py        # Language analytics
├── tests/                 # Test frameworks
├── query_stories.py       # Interactive query interface
├── update_all_databases.py # Management utility
└── requirements.txt
```

## Enhanced Collection Methods

### Microsoft Pre-collected URLs (Phase 5)
The Microsoft scraper now features an **enhanced collection approach**:

- **Primary Method**: Loads 656 pre-collected URLs from Microsoft's official 1000+ AI stories blog
- **Fallback Method**: Original page scraping if pre-collected URLs unavailable
- **Smart AI Filtering**: Disabled for Microsoft-verified stories, enabled for discovered URLs
- **Backward Compatible**: Works seamlessly with existing `update_all_databases.py` commands

**Usage**: Standard command automatically uses enhanced approach:
```bash
python update_all_databases.py update --source microsoft
# Now processes 656 stories instead of ~60
```

**Files**:
- `microsoft_story_links.json` - Pre-collected story URLs with metadata
- `extract_microsoft_blog_links.py` - URL extraction utility for blog updates

## Contributing

This project uses a modular architecture with clear separation between scraping, AI processing, and database operations. Each AI provider has its own specialized scraper following the common `BaseScraper` interface.

## Development Status

- ✅ **Phase 1**: Anthropic foundation (completed)
- ✅ **Phase 2**: All 5 AI provider scrapers (completed)  
- ✅ **Phase 3**: Gen AI classification enhancement (completed)
- ✅ **Phase 4**: Web dashboard (completed)
- ✅ **Phase 5**: Enhanced Microsoft collection - 10x improvement (completed)
- ✅ **Phase 6**: Language detection system integration (completed)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please refer to the project's issue tracker.

---

*Built with Claude AI for intelligent data extraction and analysis.*