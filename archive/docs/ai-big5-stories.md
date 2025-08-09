# AI Customer Stories Database - Development Requirements

## Project Overview

Build a Python application to scrape, store, and analyze AI customer stories from 5 major providers: Microsoft Azure, AWS, Google Cloud, Anthropic, and OpenAI. The system will use PostgreSQL for storage and Claude API for intelligent data extraction and analysis.

## Development Approach

### Phase 1: Foundation (Build & Test First)
1. Set up PostgreSQL database with the provided schema
2. Build and test ONE complete scraper (recommend starting with Anthropic)
3. Implement Claude API integration for data extraction
4. Test deduplication logic with sample data
5. Create basic data exploration interface

### Phase 2: Scale & Enhance
1. Build scrapers for remaining 4 sources
2. Add web dashboard for data exploration
3. Implement scheduling for periodic updates
4. Add advanced analytics capabilities

## Technical Stack

- **Language**: Python 3.9+
- **Database**: PostgreSQL 14+ with JSONB support
- **Web Scraping**: BeautifulSoup4, requests, selenium (if needed for dynamic content)
- **AI Integration**: Anthropic Claude API
- **Web Framework**: Flask or FastAPI (for Phase 2 dashboard)
- **Environment**: VS Code with Python extension

## Database Schema

```sql
-- Sources/Companies being tracked
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,  -- 'Microsoft', 'AWS', 'Google Cloud', 'Anthropic', 'OpenAI'
    base_url VARCHAR(255) NOT NULL,
    last_scraped TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Main customer stories table
CREATE TABLE customer_stories (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    customer_name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    url VARCHAR(500) UNIQUE NOT NULL,
    content_hash VARCHAR(64), -- SHA256 of raw content for change detection
    
    -- Structured extracted data
    industry VARCHAR(100),
    company_size VARCHAR(50), -- 'startup', 'mid-market', 'enterprise', 'government'
    use_case_category VARCHAR(100), -- 'customer service', 'data analytics', 'automation', etc.
    
    -- Raw content storage (flexible for analysis)
    raw_content JSONB NOT NULL, -- Full scraped HTML/text
    extracted_data JSONB, -- Claude-processed structured data
    
    -- Metadata
    scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    publish_date DATE, -- When the story was originally published
    
    -- Text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', 
            COALESCE(title, '') || ' ' || 
            COALESCE(customer_name, '') || ' ' || 
            COALESCE(industry, '') || ' ' ||
            COALESCE(extracted_data->>'summary', '')
        )
    ) STORED
);

-- Services/Technologies mentioned in stories
CREATE TABLE technologies (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    name VARCHAR(100) NOT NULL, -- 'Azure OpenAI', 'Claude 3.5 Sonnet', 'Amazon Bedrock'
    category VARCHAR(50), -- 'LLM', 'Database', 'Analytics', 'Infrastructure'
    UNIQUE(source_id, name)
);

-- Many-to-many relationship between stories and technologies
CREATE TABLE story_technologies (
    story_id INTEGER REFERENCES customer_stories(id) ON DELETE CASCADE,
    technology_id INTEGER REFERENCES technologies(id),
    PRIMARY KEY (story_id, technology_id)
);

-- Quantified metrics/outcomes from stories
CREATE TABLE story_metrics (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES customer_stories(id) ON DELETE CASCADE,
    metric_type VARCHAR(100), -- 'cost_reduction', 'time_savings', 'revenue_increase', 'productivity_gain'
    metric_value NUMERIC,
    metric_unit VARCHAR(50), -- 'percent', 'hours_per_week', 'dollars', 'minutes'
    metric_description TEXT
);

-- Cross-source customer tracking (for analysis, not deduplication)
CREATE TABLE customer_profiles (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL, -- Normalized customer name
    alternative_names TEXT[], -- Variations like "Accenture", "Accenture plc", "Accenture Limited"
    story_count INTEGER DEFAULT 0,
    sources_present TEXT[] -- Which sources have stories for this customer
);

-- Links customer profiles to individual stories
CREATE TABLE customer_story_links (
    customer_profile_id INTEGER REFERENCES customer_profiles(id),
    story_id INTEGER REFERENCES customer_stories(id),
    PRIMARY KEY (customer_profile_id, story_id)
);

-- Per-source deduplication (same customer, same source, multiple URLs)
CREATE TABLE source_duplicates (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    canonical_story_id INTEGER REFERENCES customer_stories(id),
    duplicate_story_ids INTEGER[], -- Other story IDs that are duplicates
    merge_reason VARCHAR(100), -- 'same_url_different_path', 'updated_content', 'republished'
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_customer_stories_customer_name ON customer_stories(customer_name);
CREATE INDEX idx_customer_stories_source_scraped ON customer_stories(source_id, scraped_date);
CREATE INDEX idx_customer_stories_industry ON customer_stories(industry);
CREATE INDEX idx_customer_stories_search ON customer_stories USING gin(search_vector);
CREATE INDEX idx_customer_stories_extracted_data ON customer_stories USING gin(extracted_data);
CREATE INDEX idx_story_metrics_type ON story_metrics(metric_type);
CREATE INDEX idx_story_technologies_story ON story_technologies(story_id);

-- Initial data
INSERT INTO sources (name, base_url) VALUES 
('Anthropic', 'https://www.anthropic.com/customers'),
('Microsoft', 'https://www.microsoft.com/en-us/ai/ai-customer-stories'),
('AWS', 'https://aws.amazon.com/solutions/case-studies/'),
('Google Cloud', 'https://cloud.google.com/customers'),
('OpenAI', 'https://openai.com/stories/');
```

## Data Structures

### Raw Content JSONB Structure
```json
{
  "html": "Full HTML content",
  "text": "Extracted plain text",
  "metadata": {
    "title": "Page title",
    "description": "Meta description",
    "author": "Author if available",
    "publish_date": "2025-01-15",
    "word_count": 1250,
    "images": ["image1.jpg", "image2.jpg"],
    "external_links": ["https://customer-site.com"]
  },
  "scraping_info": {
    "scraper_version": "1.0",
    "timestamp": "2025-07-29T10:00:00Z",
    "page_load_time": 1.2,
    "errors": []
  }
}
```

### Extracted Data JSONB Structure (Claude-processed)
```json
{
  "summary": "Brief story summary",
  "problem_statement": "Challenge the customer faced",
  "solution_description": "How AI/cloud services solved it",
  "business_outcomes": [
    {
      "type": "cost_savings",
      "value": 50,
      "unit": "percent",
      "description": "Reduced operational costs by 50%"
    }
  ],
  "technologies_used": [
    "Azure OpenAI Service",
    "Azure AI Search"
  ],
  "use_cases": [
    "customer support automation",
    "document processing"
  ],
  "quote": "Key customer quote if available",
  "implementation_timeline": "3 months",
  "company_info": {
    "estimated_size": "enterprise",
    "industry_sector": "healthcare",
    "geography": "north america"
  },
  "content_quality_score": 0.85,
  "last_processed": "2025-07-29T10:00:00Z"
}
```

## Sample URLs and Patterns

### Anthropic (Start Here - Most Consistent)
- **Base URL**: `https://www.anthropic.com/customers`
- **Individual Stories**: `https://www.anthropic.com/customers/[company]`
- **Examples**:
  - https://www.anthropic.com/customers/hume
  - https://www.anthropic.com/customers/lex
- **Content Pattern**: 650-1050 word structured case studies with clear metrics

### Microsoft Azure
- **Base URLs**: 
  - `https://www.microsoft.com/en-us/ai/ai-customer-stories`
  - `https://azure.microsoft.com/en-us/resources/customer-stories`
- **Individual Stories**: `https://www.microsoft.com/en/customers/story/[id]-[company]-[technology]`
- **Example**: https://www.microsoft.com/en/customers/story/23953-accenture-azure-ai-foundry

### AWS
- **Base URLs**:
  - `https://aws.amazon.com/solutions/case-studies/`
  - `https://aws.amazon.com/ai/generative-ai/customers/`
- **Pattern**: Mix of case studies and blog aggregations

### Google Cloud
- **Base URLs**:
  - `https://cloud.google.com/customers`
  - `https://cloud.google.com/ai/generative-ai/stories`
- **Pattern**: Often aggregated lists with links to detailed stories

### OpenAI
- **Base URL**: `https://openai.com/stories/`
- **Individual Stories**: `https://openai.com/index/[company]/`
- **Example**: https://openai.com/index/moderna/

## Phase 1 Implementation Requirements

### 1. Environment Setup
```bash
# Required packages
pip install psycopg2-binary beautifulsoup4 requests anthropic python-dotenv hashlib
```

### 2. Configuration Management
Create `.env` file support for:
```
DATABASE_URL=postgresql://user:password@localhost/ai_stories
ANTHROPIC_API_KEY=your_api_key
LOG_LEVEL=INFO
```

### 3. Database Connection Module
- PostgreSQL connection handling
- Schema initialization
- Connection pooling for production use

### 4. Anthropic Scraper (Phase 1 Focus)
**Requirements:**
- Scrape customer list from https://www.anthropic.com/customers
- Extract individual story URLs
- Scrape 3-5 individual customer stories
- Handle rate limiting (2-3 requests per second)
- Store raw HTML and extracted text
- Generate content hash for change detection

**Key Functions:**
```python
def scrape_anthropic_customer_list() -> List[str]:
    """Return list of customer story URLs"""

def scrape_anthropic_story(url: str) -> Dict:
    """Scrape individual story, return raw content"""

def extract_story_metadata(html: str) -> Dict:
    """Extract title, customer name, basic metadata"""
```

### 5. Claude API Integration
**Requirements:**
- Connect to Claude API for data extraction
- Handle API rate limits and retries
- Process raw story content into structured data
- Extract: customer info, technologies, metrics, use cases

**Sample Claude Prompt Template:**
```python
EXTRACTION_PROMPT = """
Analyze this AI customer story and extract structured information:

{story_content}

Please extract and return a JSON object with:
1. customer_name: Company name
2. industry: Industry sector
3. company_size: startup/mid-market/enterprise/government
4. summary: 2-3 sentence summary
5. problem_statement: What challenge did they face?
6. solution_description: How did AI solve it?
7. technologies_used: List of specific AI services/models mentioned
8. business_outcomes: List of quantified results (cost savings, time reduction, etc.)
9. use_cases: List of AI use case categories
10. key_quote: Most impactful customer quote
11. content_quality_score: 0-1 score of how detailed/complete this story is

Focus on extracting specific metrics and quantified business outcomes.
"""
```

### 6. Deduplication Logic
**Per-Source Deduplication:**
```python
def check_content_similarity(story1: str, story2: str) -> float:
    """Return similarity score 0-1"""

def find_source_duplicates(story_id: int, source_id: int) -> List[int]:
    """Find potential duplicates within same source"""
```

**Cross-Source Customer Linking:**
```python
def normalize_company_name(name: str) -> str:
    """Normalize company name variations"""

def link_customer_to_profile(story_id: int, customer_name: str):
    """Link story to customer profile across sources"""
```

### 7. Testing & Validation
**Test with these Anthropic stories:**
- https://www.anthropic.com/customers/hume (voice AI platform)
- https://www.anthropic.com/customers/lex (writing platform)
- Pick 2-3 additional stories from the customer list

**Validation checks:**
- Verify all raw content is captured
- Confirm Claude extraction produces valid JSON
- Test database insertion and retrieval
- Validate search functionality

### 8. Basic Query Interface
Simple Python script to:
- List all customers by source
- Search stories by keyword
- Show metrics by company
- Display technology usage patterns

## Phase 2 Requirements (After Phase 1 Success)

### Additional Scrapers
- Microsoft Azure scraper
- AWS scraper  
- Google Cloud scraper
- OpenAI scraper

### Web Dashboard
- Flask/FastAPI web interface
- Story browsing and search
- Analytics views (metrics, technology trends)
- Export capabilities

### Automation
- Scheduling for periodic updates
- Change detection and alerts
- Error monitoring and reporting

## Deduplication Strategy Details

### Cross-Source Analysis (Keep All Stories)
- Same customer (e.g., Accenture) with Microsoft AND AWS = 2 separate stories
- Different technologies, use cases, outcomes
- Enable competitive analysis

### Per-Source Deduplication (Remove True Duplicates)
- Same story appearing at multiple URLs within one source
- Updated versions of the same story
- Content similarity threshold: >85%

## Success Criteria for Phase 1

1. **Database**: Successfully stores 3-5 Anthropic stories with full metadata
2. **Claude Integration**: Extracts structured data with >80% accuracy
3. **Search**: Can find stories by customer name, technology, or keywords  
4. **Deduplication**: Correctly identifies and handles duplicate content
5. **Performance**: Scrapes and processes a story in <30 seconds

## File Structure
```
ai_customer_stories/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── connection.py
│   │   └── schema.sql
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── anthropic_scraper.py
│   │   └── [other_scrapers.py]
│   ├── ai_integration/
│   │   ├── __init__.py
│   │   ├── claude_processor.py
│   │   └── prompts.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── deduplication.py
│   │   ├── text_processing.py
│   │   └── logging_config.py
│   └── main.py
├── tests/
├── requirements.txt
├── .env.example
├── README.md
└── run_scraper.py
```

## Getting Started

1. **Clone/create project structure**
2. **Set up PostgreSQL database** and run schema
3. **Install Python dependencies**
4. **Configure environment variables**
5. **Start with Anthropic scraper** - test with 3-5 stories
6. **Validate data quality** and extraction accuracy
7. **Report back findings** for iteration before scaling

This foundation will give us a solid, tested base before expanding to all 5 sources.