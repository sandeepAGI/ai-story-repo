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
- **Deduplication Engine**: Cross-source and per-source duplicate detection

### 📊 **Rich Analytics**
- **Business Outcomes Tracking**: Quantified metrics (cost savings, time reduction, productivity gains)
- **Technology Usage Patterns**: AI services and tools mentioned across stories
- **Industry Analysis**: Sector-specific AI adoption trends
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
```

## Database Schema

### Core Tables
- **`sources`**: AI provider information and scraping metadata
- **`customer_stories`**: Main stories with full content and extracted data
- **`technologies`**: AI services and tools mentioned in stories
- **`story_metrics`**: Quantified business outcomes and metrics

### Advanced Features
- **Full-text search** with PostgreSQL tsvector
- **JSONB storage** for flexible raw content and extracted data
- **Cross-source customer profiling** for competitive analysis
- **Publication date estimation** with confidence levels

## Gen AI Classification Framework

### Four Dimensions
1. **Superpowers** (Capabilities): Code, Create Content, Automate with Agents, Find Data Insights, Research, Brainstorm, Natural Language
2. **Business Impacts** (Outcomes): Innovation, Efficiency, Speed, Quality, Client Satisfaction, Risk Reduction  
3. **Adoption Enablers** (Prerequisites): Data & Digital, Innovation Culture, Ecosystem Partners, Policy & Governance, Risk Management
4. **Business Function** (Context): Marketing, Sales, Production, Distribution, Service, Finance & Accounting

## Current Database Stats

- **52 High-Quality Stories** across all 5 major AI providers
- **100% Data Completeness** with zero missing critical fields
- **Average Quality Score**: 0.863 (range: 0.70-0.90)
- **Rich Business Outcomes**: All stories contain quantified metrics
- **Date Range**: 2016-2025 with transparent estimated vs. actual dates

## Architecture

```
ai_customer_stories/
├── src/
│   ├── database/          # Database models and operations
│   ├── scrapers/          # Provider-specific scrapers
│   ├── ai_integration/    # Claude AI processing
│   └── utils/             # Utilities and helpers
├── tests/                 # Test frameworks
├── query_stories.py       # Interactive query interface
├── update_all_databases.py # Management utility
└── requirements.txt
```

## Contributing

This project uses a modular architecture with clear separation between scraping, AI processing, and database operations. Each AI provider has its own specialized scraper following the common `BaseScraper` interface.

## Development Status

- ✅ **Phase 1**: Anthropic foundation (completed)
- ✅ **Phase 2**: All 5 AI provider scrapers (completed)  
- 🔄 **Phase 3**: Gen AI classification enhancement (in progress)
- ⏳ **Phase 4**: Web dashboard (planned)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please refer to the project's issue tracker.

---

*Built with Claude AI for intelligent data extraction and analysis.*