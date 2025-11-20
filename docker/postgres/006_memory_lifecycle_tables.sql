-- ========================================
-- Sprint 9: Memory Lifecycle Management
-- ========================================

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. semantic_memories テーブル（新規作成 + Sprint 9拡張）
CREATE TABLE IF NOT EXISTS semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 基本フィールド
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    memory_type VARCHAR(50) DEFAULT 'longterm',  -- 'working', 'longterm'
    source_type VARCHAR(50),  -- 'intent', 'thought', 'correction', 'decision'
    metadata JSONB DEFAULT '{}',

    -- タイムスタンプ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_archived BOOLEAN DEFAULT FALSE,

    -- Sprint 9: Memory Lifecycle Management 追加フィールド
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0 CHECK (access_count >= 0),
    decay_applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE semantic_memories IS 'Semantic Memory Storage with Lifecycle Management';
COMMENT ON COLUMN semantic_memories.importance_score IS 'Memory importance score (0.0 - 1.0), decays over time, boosted by access';
COMMENT ON COLUMN semantic_memories.last_accessed_at IS 'Last accessed timestamp for boost calculation';
COMMENT ON COLUMN semantic_memories.access_count IS 'Number of times this memory has been accessed';
COMMENT ON COLUMN semantic_memories.decay_applied_at IS 'Last time decay was applied to importance score';

-- インデックス
CREATE INDEX IF NOT EXISTS idx_semantic_memories_user_id ON semantic_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_memory_type ON semantic_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_created_at ON semantic_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_is_archived ON semantic_memories(is_archived);

-- Sprint 9: 重要度スコア関連インデックス
CREATE INDEX IF NOT EXISTS idx_semantic_memories_importance ON semantic_memories(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_decay ON semantic_memories(decay_applied_at);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_access ON semantic_memories(last_accessed_at);

-- pgvector用のインデックス（コサイン類似度検索用）
CREATE INDEX IF NOT EXISTS idx_semantic_memories_embedding ON semantic_memories
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 2. memory_archive テーブル（新規）
CREATE TABLE IF NOT EXISTS memory_archive (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 元メモリ情報
    original_memory_id UUID NOT NULL,
    original_content TEXT NOT NULL,
    original_embedding VECTOR(1536),

    -- 圧縮情報
    compressed_summary TEXT NOT NULL,
    compression_method VARCHAR(50) DEFAULT 'claude_haiku',
    compressed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- サイズ情報
    original_size_bytes INTEGER,
    compressed_size_bytes INTEGER,
    compression_ratio FLOAT,

    -- スコア情報
    final_importance_score FLOAT,

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archive_reason VARCHAR(100),  -- 'low_importance', 'capacity_limit', 'manual'

    -- 保持期限
    retention_until TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE memory_archive IS 'Archived and compressed memories';
COMMENT ON COLUMN memory_archive.compression_ratio IS 'Compression ratio: (original - compressed) / original';
COMMENT ON COLUMN memory_archive.archive_reason IS 'Reason for archiving: low_importance, capacity_limit, manual';

CREATE INDEX IF NOT EXISTS idx_memory_archive_user_id ON memory_archive(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_archive_original_id ON memory_archive(original_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_archive_retention ON memory_archive(retention_until);
CREATE INDEX IF NOT EXISTS idx_memory_archive_compressed_at ON memory_archive(compressed_at DESC);

-- 3. memory_lifecycle_log テーブル（新規）
CREATE TABLE IF NOT EXISTS memory_lifecycle_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    memory_id UUID NOT NULL,

    -- イベント情報
    event_type VARCHAR(50) NOT NULL,  -- 'score_update', 'compress', 'archive', 'delete'
    event_details JSONB,

    -- スコア変動
    score_before FLOAT,
    score_after FLOAT,

    -- タイムスタンプ
    event_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE memory_lifecycle_log IS 'Memory lifecycle event log';
COMMENT ON COLUMN memory_lifecycle_log.event_type IS 'Event type: score_update, compress, archive, delete';

CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_user ON memory_lifecycle_log(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_memory ON memory_lifecycle_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_event ON memory_lifecycle_log(event_type);
CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_time ON memory_lifecycle_log(event_at DESC);

-- 既存メモリのスコア初期化（テーブルが既に存在する場合）
UPDATE semantic_memories
SET importance_score = 0.5
WHERE importance_score IS NULL;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Sprint 9: Memory Lifecycle tables created successfully!';
    RAISE NOTICE '   - semantic_memories (with lifecycle fields)';
    RAISE NOTICE '   - memory_archive';
    RAISE NOTICE '   - memory_lifecycle_log';
END $$;
