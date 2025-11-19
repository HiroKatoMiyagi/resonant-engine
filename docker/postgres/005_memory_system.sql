-- Sprint 3-7: Memory System Schema
-- Date: 2025-11-19
-- Description: Memory Store, Retrieval, Context Assembler, Session Summary

-- ========================================
-- 1. Enable pgvector extension
-- ========================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ========================================
-- 2. Memories Table (Sprint 3: Memory Store)
-- ========================================
CREATE TABLE IF NOT EXISTS memories (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- text-embedding-3-small dimension
    memory_type VARCHAR(50) NOT NULL,  -- 'working', 'longterm'
    source_type VARCHAR(50),  -- 'intent', 'thought', 'correction', 'decision', 'message'
    user_id VARCHAR(100),
    session_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,  -- Working Memory TTL
    is_archived BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE memories IS 'Memory Store: Vector-based semantic memory storage';
COMMENT ON COLUMN memories.memory_type IS 'working: 24h TTL, longterm: permanent';
COMMENT ON COLUMN memories.embedding IS '1536-dim vector from text-embedding-3-small';
COMMENT ON COLUMN memories.source_type IS 'Source of the memory: intent, thought, message, etc.';

-- Indexes for memories (Sprint 3-4)
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source_type);
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_expires ON memories(expires_at)
WHERE expires_at IS NOT NULL;

-- Full-text search index (Sprint 4: Retrieval Orchestrator)
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS content_tsvector tsvector
GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;

CREATE INDEX IF NOT EXISTS idx_memories_content_tsvector
ON memories USING GIN (content_tsvector);

-- ========================================
-- 3. Sessions Table (Sprint 7: Session Summary)
-- ========================================
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    summary TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE sessions IS 'Conversation sessions for context management';
COMMENT ON COLUMN sessions.summary IS 'AI-generated summary of the session';

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(ended_at)
WHERE ended_at IS NULL;

-- ========================================
-- 4. Extend existing messages table (Sprint 6)
-- ========================================
-- Add role column for message type classification
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';

-- Add session_id for conversation tracking
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS session_id VARCHAR(255);

-- Add index for session queries
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

COMMENT ON COLUMN messages.role IS 'Message role: user, assistant, system';
COMMENT ON COLUMN messages.session_id IS 'Session ID for conversation tracking';

-- ========================================
-- 5. Extend existing intents table (Sprint 6)
-- ========================================
-- Add user_id for user-specific intents
ALTER TABLE intents
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);

-- Add session_id for conversation context
ALTER TABLE intents
ADD COLUMN IF NOT EXISTS session_id VARCHAR(255);

-- Add index for user and session queries
CREATE INDEX IF NOT EXISTS idx_intents_user ON intents(user_id);
CREATE INDEX IF NOT EXISTS idx_intents_session ON intents(session_id);

COMMENT ON COLUMN intents.user_id IS 'User ID who created the intent';
COMMENT ON COLUMN intents.session_id IS 'Session ID for conversation context';

-- ========================================
-- 6. Memory cleanup function (Sprint 3)
-- ========================================
CREATE OR REPLACE FUNCTION cleanup_expired_memories()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Archive expired working memories
    UPDATE memories
    SET is_archived = TRUE
    WHERE memory_type = 'working'
      AND expires_at IS NOT NULL
      AND expires_at < CURRENT_TIMESTAMP
      AND is_archived = FALSE;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_memories() IS 'Archive expired working memories (TTL)';

-- ========================================
-- 7. Success message
-- ========================================
DO $$
BEGIN
    RAISE NOTICE 'Memory System schema created successfully!';
    RAISE NOTICE '- memories table (pgvector enabled)';
    RAISE NOTICE '- sessions table';
    RAISE NOTICE '- messages extended (role, session_id)';
    RAISE NOTICE '- intents extended (user_id, session_id)';
END $$;
