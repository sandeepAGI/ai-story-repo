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
- **Industry Analysis**: Sector-specific AI adoption trends with standardized taxonomy
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

# Reprocess stories with Aileron GenAI framework (all missing stories)
python update_all_databases.py reprocess --framework aileron

# Reprocess specific stories by ID (cost-efficient for targeted fixes)
python update_all_databases.py reprocess --framework aileron --story-ids 1001,995,978

# Run complete reprocessing (Gen AI classification + Aileron framework)
python update_all_databases.py reprocess --framework all

# Validate and fix classification consistency issues
python update_all_databases.py validate

# Launch interactive web dashboard
python run_dashboard.py

# Migrate to standardized industry taxonomy
python migrate_industries_simple.py --analyze
python migrate_industries_simple.py --migrate --execute
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

## Industry Standardization System

### Standardized Taxonomy (11 Categories)
The system uses a consolidated industry taxonomy to reduce 130+ raw industry classifications down to 11 standardized categories:

1. **technology** - Software, SaaS, IT services, cloud providers, cybersecurity, AI/ML companies
2. **financial_services** - Banks, insurance, fintech, payments, investment services, credit
3. **healthcare** - Hospitals, pharmaceuticals, medical devices, biotechnology, health tech
4. **retail_ecommerce** - Online/offline retail, consumer goods, fashion, marketplace platforms
5. **manufacturing** - Industrial production, automotive, aerospace, chemicals, materials
6. **government_public_sector** - Federal/state/local government, military, education, non-profits
7. **media_communications** - Telecommunications, broadcasting, publishing, entertainment, advertising  
8. **energy_utilities** - Oil/gas, renewable energy, electric utilities, mining, environmental services
9. **transportation_logistics** - Airlines, shipping, delivery, ride-sharing, freight, warehousing
10. **professional_services** - Consulting, legal, accounting, real estate, architecture, HR
11. **other** - Agriculture, hospitality, sports, unique cross-industry cases

### Migration Features
- **Intelligent Mapping**: Regex-based pattern matching with confidence scoring
- **Safe Execution**: Dry-run mode with confidence thresholds (default: 0.3)
- **Complete Analysis**: Shows before/after distribution and mapping details
- **Database Integration**: Uses existing `DatabaseOperations` patterns

### Migration Commands
```bash
# Analyze current industry distribution (130+ categories)
python migrate_industries_simple.py --analyze

# Create mapping plan showing proposed changes
python migrate_industries_simple.py --plan

# Execute migration with dry-run (safe preview)
python migrate_industries_simple.py --migrate

# Execute actual migration (updates database)
python migrate_industries_simple.py --migrate --execute
```

### Migration Impact
- **Before**: 130 unique industries across 911 stories
- **After**: 11 standardized categories with clear business logic
- **Updated Stories**: 55 stories consolidated in final migration
- **Dashboard Impact**: Industry count standardized to exactly 11 manageable categories
- **Status**: ✅ **COMPLETED** - Migration executed successfully

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

## Web Dashboard

### **Interactive Analytics Platform**
Access the comprehensive web dashboard at `http://localhost:8501` after running `python run_dashboard.py`.

### **Dashboard Pages:**

#### **📊 Overview**
- **Key Metrics**: Total stories, Gen AI vs Non Gen AI breakdown, quality scores
- **Source Distribution**: Stories by AI provider with Gen AI classification  
- **Recent Activity**: Latest 10 stories with customer names and links
- **Industry Coverage**: Standardized 11-category industry taxonomy

#### **🔍 Story Explorer** 
- **Advanced Filtering**: Source, industry, company size, AI type (Gen AI/Non Gen AI)
- **Full-Text Search**: Customer names, titles, industry keywords
- **Detailed Story View**: Complete story details with business outcomes
- **Technology Breakdown**: Specific AI services and tools mentioned

#### **📈 Analytics Dashboard** *(Enhanced)*
- **🔬 Gen AI Filter**: Toggle between All Stories, Gen AI Only, Non Gen AI Only
- **Smart Technology Analysis**: Technology usage by AI provider (addresses Microsoft bias)
- **Business Outcomes by Use Case**: Individual highlights vs averages
- **🔄 Use Case → Outcome Flow**: Visual progress bars showing outcome percentages
- **💰 Top Financial Achievements**: Individual customer highlights with values
- **🚀 Operational Scale Metrics**: Trillion-scale achievements (events, users, sessions)
- **📊 Value Distribution**: Sunburst charts and cross-analysis matrices
- **🏷️ Word Cloud Alternatives**: Tag clouds, heatmaps, network visualizations

#### **🎯 Aileron GenAI SuperPowers Framework** *(Gen AI Only)*
- **SuperPowers Analysis**: 7 AI capabilities (code, create_content, automate_with_agents, etc.)
- **Business Impacts**: 6 outcome categories (innovation, efficiency, speed, quality, etc.)
- **Adoption Enablers**: 5 organizational success factors
- **Business Functions**: Cross-departmental AI impact analysis
- **Cross-Analysis Matrix**: SuperPowers → Business Impacts relationships
- **Filtering**: Automatically filters to Gen AI stories only (700 stories)

#### **💾 Data Export**
- **Multiple Formats**: CSV, Excel, JSON export options
- **Flexible Filtering**: Export all stories, filtered subsets, or summary statistics
- **Downloadable Reports**: Pre-formatted datasets for external analysis

### **Key Dashboard Features:**
- **Consistent Gen AI Filtering**: Analytics page supports Gen AI/Non Gen AI toggle across all charts
- **Individual Highlights**: Shows top achievements rather than diluted averages
- **Cost-Optimized Processing**: Enhanced reprocessing commands prevent unnecessary Claude API calls
- **Real-Time Data**: Direct PostgreSQL integration with caching for performance
- **Mobile Responsive**: Clean Streamlit interface works across devices

## Data Consistency System

### **Classification Consistency Prevention**
The system implements comprehensive validation to ensure database integrity between AI classification fields:

#### **Problem Prevention:**
- **Main Processing Pipeline**: Validates `is_gen_ai` field matches `ai_type` classification during story insertion
- **Reprocessing Pipeline**: Ensures database field stays synchronized during Claude reprocessing
- **Authoritative Source**: Uses `ai_type` from Claude extraction as the definitive classification

#### **Validation Tools:**
```bash
# Run comprehensive consistency validation
python update_all_databases.py validate

# Direct validation script (more detailed output)
python validate_classification_consistency.py
```

#### **Key Features:**
- **Automatic Detection**: Scans database for `is_gen_ai` vs `ai_type` mismatches
- **Smart Correction**: Uses Claude's `ai_type` classification as authoritative source
- **Database Synchronization**: Updates both database field and extracted_data
- **Comprehensive Reporting**: Shows before/after statistics and fix details
- **Prevention Integration**: Built into all story processing pipelines

#### **Technical Implementation:**
- **Enhanced Main Processing** (`src/main.py`): Consistency validation on new stories
- **Enhanced Reprocessing** (`reprocess_with_aileron_framework.py`): Database field updates
- **Utility Function** (`claude_processor.py`): Reusable validation logic
- **CLI Integration** (`update_all_databases.py`): One-command validation

This system prevents dashboard count discrepancies by ensuring the `is_gen_ai` database field always matches the `ai_type` classification from Claude's analysis.

## Development Status

- ✅ **Phase 1**: Anthropic foundation (completed)
- ✅ **Phase 2**: All 5 AI provider scrapers (completed)  
- ✅ **Phase 3**: Gen AI classification enhancement (completed)
- ✅ **Phase 4**: Web dashboard (completed)
- ✅ **Phase 5**: Enhanced Microsoft collection - 10x improvement (completed)
- ✅ **Phase 6**: Language detection system integration (completed)
- ✅ **Phase 7**: Industry standardization system (completed)
- ✅ **Phase 8**: Dashboard Overview page optimization (completed)
- ✅ **Phase 9**: Dashboard Analytics page enhancement (completed)
- ✅ **Phase 10**: Reprocessing system optimization (completed)
- ✅ **Phase 11**: Data consistency system implementation (completed)

### Phase 8 - Dashboard Overview Page Optimization
- **Industry Standardization**: Successfully migrated from 45+ to exactly 11 standardized industry categories
- **Table Rendering Fix**: Replaced custom HTML table with native Streamlit components for better responsive design
- **Data Accuracy**: All 911 stories properly categorized using intelligent industry mapping
- **User Experience**: Overview page now displays clean, properly formatted data tables

### Phase 9 - Dashboard Analytics Page Enhancement
- **Gen AI Filter Toggle**: Added comprehensive filtering across all Analytics charts (All Stories/Gen AI Only/Non Gen AI Only)
- **Enhanced Business Outcomes**: 
  - Individual financial highlights vs diluted averages
  - Use Case → Outcome Flow with visual progress bars
  - Operational scale metrics separated from financial outcomes
  - Fixed $1.44T outlier issue (FullStory's 1.44T events correctly categorized)
- **Technology Analysis**: Source-aware technology usage charts (addresses Microsoft story bias)
- **Advanced Visualizations**: Sunburst charts, heatmaps, network-style visualizations, tag clouds
- **Word Cloud Alternatives**: Multiple visualization options for qualitative outcome analysis

### Phase 10 - Reprocessing System Optimization
- **Cost-Efficient Reprocessing**: Enhanced `reprocess_with_aileron_framework.py` with story ID targeting
- **Integrated CLI Commands**: Added `reprocess` command to main `update_all_databases.py` interface
- **Selective Processing**: Prevent unnecessary Claude API calls (645 → 15 stories for missing Aileron data)
- **Framework-Specific Updates**: Support for Aileron framework, Gen AI classification, and combined reprocessing
- **API Cost Optimization**: Reduced reprocessing costs from $30-60 to $1-2 for targeted fixes

### Phase 11 - Data Consistency System Implementation
- **Classification Consistency Prevention**: Implemented comprehensive validation system to prevent `is_gen_ai`/`ai_type` mismatches
- **Enhanced Processing Pipelines**: Updated main processing and reprocessing to validate and fix inconsistencies automatically  
- **New CLI Command**: `python update_all_databases.py validate` for on-demand consistency checking
- **Database Integrity**: Fixed 4 misclassified stories, resulting in 696 Gen AI stories with 100% Aileron coverage
- **Future Prevention**: Built-in validation ensures dashboard count accuracy and prevents future consistency issues

### GoogleCloud Data Quality Fix (Phase 9)
- **Customer Names Fix**: Resolved URL-as-name issue for 19 customer stories
  - Fixed blog URL parsing in scraper for future prevention
  - Updated existing records: Lowe's, Ford, Toyota, Wayfair, Wells Fargo, etc.
  - Remaining 8 non-customer posts (partnerships/awards/industry) intentionally left as-is

## Known Issues & Future Work

### Non-Customer Content Classification
**Issue**: Some scraped content includes non-customer stories (partnerships, awards, industry posts) that get stored with URL-based names.

**Scope**: Affects GoogleCloud and potentially other sources. Examples:
- Partnership announcements ("Google Cloud and ServiceNow partnership")
- Award announcements ("Winners of 2023 Customer Awards") 
- Industry trend posts ("Google Cloud for Retail overview")

**Current Status**: GoogleCloud customer stories fixed (19/27), non-customer posts remain as-is.

**Future Enhancement**: Implement content type classification to:
1. Detect non-customer content during scraping
2. Flag or categorize differently (partnership/award/industry vs customer story)
3. Apply consistent handling across all AI provider sources
4. Consider excluding non-customer content or storing in separate tables

**Priority**: Low - Does not affect customer story analysis, mainly a data cleanliness issue.

## Future Enhancements

### Code Refactoring & Architecture Improvements
The following items are identified for future development phases to improve maintainability and performance:

#### Dashboard Code Organization
- **Modular Page Structure**: Refactor dashboard.py into separate page modules (overview.py, analytics.py, etc.)
- **Component Library**: Extract reusable chart components and metrics into dedicated modules
- **Configuration Management**: Centralize chart configurations and data processing logic
- **Performance Optimization**: Implement advanced caching strategies for heavy data operations

#### Brand & Styling Improvements
- **Theme System**: Enhance brand_styles.py with comprehensive theme management
- **Responsive Design**: Improve mobile and tablet responsive layouts
- **Custom Components**: Create branded Streamlit components for consistent UI elements
- **Chart Template System**: Standardize chart creation with branded templates

#### Data Processing Optimization
- **Query Optimization**: Review and optimize database queries for faster dashboard loading
- **Data Pipeline**: Implement incremental data refresh for real-time dashboard updates
- **Memory Management**: Optimize DataFrame operations for large datasets
- **Error Handling**: Enhance error handling and user feedback systems

#### Development Infrastructure
- **Testing Framework**: Implement comprehensive unit and integration tests
- **CI/CD Pipeline**: Automated testing and deployment for dashboard updates
- **Documentation**: Expand technical documentation for dashboard architecture
- **Performance Monitoring**: Add performance tracking and optimization metrics

**Estimated Effort**: 2-3 development sprints  
**Priority**: Medium - Will improve maintainability and development velocity  
**Dependencies**: Current production baseline established

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please refer to the project's issue tracker.

---

*Built with Claude AI for intelligent data extraction and analysis.*