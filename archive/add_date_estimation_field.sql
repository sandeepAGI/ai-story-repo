-- Add date estimation transparency fields to customer_stories table
ALTER TABLE customer_stories 
ADD COLUMN publish_date_estimated BOOLEAN DEFAULT FALSE,
ADD COLUMN publish_date_confidence VARCHAR(10) DEFAULT NULL, -- 'high', 'medium', 'low'
ADD COLUMN publish_date_reasoning TEXT DEFAULT NULL;

-- Add comments for clarity
COMMENT ON COLUMN customer_stories.publish_date_estimated IS 'True if publish_date was estimated by AI, false if extracted from source';
COMMENT ON COLUMN customer_stories.publish_date_confidence IS 'Confidence level in estimated date: high, medium, low';
COMMENT ON COLUMN customer_stories.publish_date_reasoning IS 'Brief explanation of how the date was estimated';