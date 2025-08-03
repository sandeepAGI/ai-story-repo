-- Add language detection fields to customer_stories table
-- Run this after testing confirms language detection works correctly

-- Add language column with default 'English' for existing stories
ALTER TABLE customer_stories 
ADD COLUMN detected_language VARCHAR(50) DEFAULT 'English';

-- Add language detection metadata columns
ALTER TABLE customer_stories 
ADD COLUMN language_detection_method VARCHAR(30) DEFAULT 'default';

ALTER TABLE customer_stories 
ADD COLUMN language_confidence DECIMAL(3,2) DEFAULT 0.30;

-- Add index for language-based queries
CREATE INDEX idx_customer_stories_language ON customer_stories(detected_language);

-- Add comments for documentation
COMMENT ON COLUMN customer_stories.detected_language IS 'Detected language of the story content (English, Japanese, Korean, Chinese, etc.)';
COMMENT ON COLUMN customer_stories.language_detection_method IS 'Method used to detect language (url_pattern, title_analysis, content_analysis, default)';
COMMENT ON COLUMN customer_stories.language_confidence IS 'Confidence score for language detection (0.0-1.0)';

-- Verify the schema changes
\d customer_stories;