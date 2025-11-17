-- Sprint 4: Add ts_vector column for full-text search
-- Migration: 004_add_tsvector.sql
-- Date: 2025-11-17

-- Add ts_vector column to memories table
-- Note: Using 'simple' configuration for better multi-language support
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS content_tsvector tsvector
GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;

-- Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_memories_content_tsvector
ON memories USING GIN (content_tsvector);

-- Reindex to ensure existing data is indexed
REINDEX INDEX idx_memories_content_tsvector;

-- Verify the column and index were created
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'memories'
  AND column_name = 'content_tsvector';

-- Test ts_vector search
-- SELECT to_tsvector('simple', 'Resonant Engineは呼吸のリズムで動作する');
