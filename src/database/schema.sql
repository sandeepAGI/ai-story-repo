-- AI Customer Stories Database Schema

-- Sources/Companies being tracked
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,  -- 'Microsoft', 'AWS', 'Google Cloud', 'Anthropic', 'OpenAI'
    base_url VARCHAR(255) NOT NULL,
    last_scraped TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- URL discovery table for two-phase scraping (especially for bot-protected sources)
CREATE TABLE discovered_urls (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    url VARCHAR(500) UNIQUE NOT NULL,
    inferred_customer_name VARCHAR(255), -- Customer name extracted from URL or preview
    inferred_title VARCHAR(500), -- Title from preview or link text
    publish_date DATE, -- Publication date if discoverable
    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scrape_attempt TIMESTAMP,
    scrape_attempts INTEGER DEFAULT 0,
    scrape_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'scraped', 'failed', 'filtered_out'
    scrape_error TEXT, -- Error message from last scrape attempt
    notes TEXT -- Additional metadata or filtering notes
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

-- Indexes for discovered_urls table
CREATE INDEX idx_discovered_urls_source_status ON discovered_urls(source_id, scrape_status);
CREATE INDEX idx_discovered_urls_status ON discovered_urls(scrape_status);
CREATE INDEX idx_discovered_urls_publish_date ON discovered_urls(publish_date);
CREATE INDEX idx_discovered_urls_discovered_date ON discovered_urls(discovered_date);

-- Initial data
INSERT INTO sources (name, base_url) VALUES 
('Anthropic', 'https://www.anthropic.com/customers'),
('Microsoft', 'https://www.microsoft.com/en-us/ai/ai-customer-stories'),
('AWS', 'https://aws.amazon.com/solutions/case-studies/'),
('Google Cloud', 'https://cloud.google.com/customers'),
('OpenAI', 'https://openai.com/stories/');