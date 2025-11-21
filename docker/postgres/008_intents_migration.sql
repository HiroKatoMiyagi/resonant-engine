-- ========================================
-- Sprint 10: Intents Table Migration
-- ========================================
-- Purpose: Update intents table to match SQLAlchemy model definition

-- 1. Add session_id column
ALTER TABLE intents
ADD COLUMN IF NOT EXISTS session_id UUID;

-- 2. Add parent_intent_id column (for hierarchical intents)
ALTER TABLE intents
ADD COLUMN IF NOT EXISTS parent_intent_id UUID;

-- 3. Rename columns to match model
ALTER TABLE intents
RENAME COLUMN description TO intent_text;

ALTER TABLE intents
RENAME COLUMN result TO outcome;

ALTER TABLE intents
RENAME COLUMN processed_at TO completed_at;

-- 4. Add foreign key constraints
ALTER TABLE intents
ADD CONSTRAINT intents_session_id_fkey
FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;

ALTER TABLE intents
ADD CONSTRAINT intents_parent_intent_id_fkey
FOREIGN KEY (parent_intent_id) REFERENCES intents(id) ON DELETE SET NULL;

-- 5. Create indexes
CREATE INDEX IF NOT EXISTS idx_intents_session_id ON intents(session_id);
CREATE INDEX IF NOT EXISTS idx_intents_parent ON intents(parent_intent_id);

-- 6. Add comments
COMMENT ON COLUMN intents.session_id IS 'Session this intent belongs to';
COMMENT ON COLUMN intents.parent_intent_id IS 'Parent intent for hierarchical structure';
COMMENT ON COLUMN intents.intent_text IS 'Text description of the intent';
COMMENT ON COLUMN intents.outcome IS 'Result of intent execution (JSONB)';
COMMENT ON COLUMN intents.completed_at IS 'Timestamp when intent was completed';
