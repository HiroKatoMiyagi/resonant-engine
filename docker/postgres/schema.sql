-- ========================================
-- Resonant Engine - Complete Database Schema
-- Version: 2.0.0
-- Date: 2025-11-30
-- Description: 完全な最新スキーマ定義
-- ========================================

-- このファイルは全マイグレーションを統合した「あるべき姿」のスキーマです
-- 新規環境構築時はこのファイルのみを実行してください

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector (ankane/pgvector:latest使用)

-- ========================================
-- 1. Messages (Slack風メッセージ)
-- ========================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'user',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);

COMMENT ON TABLE messages IS 'Slack風メッセージシステム';
COMMENT ON COLUMN messages.message_type IS 'user, yuno, kana, system';

-- ========================================
-- 2. Specifications (仕様書管理)
-- ========================================
CREATE TABLE IF NOT EXISTS specifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_specifications_status ON specifications(status);
CREATE INDEX IF NOT EXISTS idx_specifications_tags ON specifications USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_specifications_created_at ON specifications(created_at DESC);

COMMENT ON TABLE specifications IS 'Notion代替の仕様書管理';
COMMENT ON COLUMN specifications.status IS 'draft, review, approved';

-- ========================================
-- 3. Intents (Intent管理)
-- ========================================
CREATE TABLE IF NOT EXISTS intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,  -- YUNO, KANA, SYSTEM
    type VARCHAR(100) NOT NULL,   -- FEATURE_REQUEST, BUG_FIX, etc.
    data JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',  -- PENDING, NORMALIZED, PROCESSED, COMPLETED, FAILED
    correlation_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_intents_status ON intents(status);
CREATE INDEX IF NOT EXISTS idx_intents_created_at ON intents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_intents_type ON intents(type);
CREATE INDEX IF NOT EXISTS idx_intents_source ON intents(source);
CREATE INDEX IF NOT EXISTS idx_intents_correlation ON intents(correlation_id);

COMMENT ON TABLE intents IS 'Intent自動処理システム';
COMMENT ON COLUMN intents.status IS 'PENDING, NORMALIZED, PROCESSED, COMPLETED, FAILED';

-- ========================================
-- 4. Corrections (修正履歴)
-- ========================================
CREATE TABLE IF NOT EXISTS corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id UUID NOT NULL REFERENCES intents(id) ON DELETE CASCADE,
    correction_id UUID NOT NULL,
    source VARCHAR(50) NOT NULL,  -- YUNO, KANA
    reason TEXT NOT NULL,
    diff JSONB NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_corrections_intent ON corrections(intent_id);
CREATE INDEX IF NOT EXISTS idx_corrections_source ON corrections(source);
CREATE INDEX IF NOT EXISTS idx_corrections_applied_at ON corrections(applied_at DESC);

COMMENT ON TABLE corrections IS 'Intent修正履歴';

-- ========================================
-- 5. Notifications (通知システム)
-- ========================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

COMMENT ON TABLE notifications IS 'リアルタイム通知';
COMMENT ON COLUMN notifications.notification_type IS 'info, success, warning, error';

-- ========================================
-- 6. Contradictions (矛盾検出)
-- ========================================
CREATE TABLE IF NOT EXISTS contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- 新規Intent
    new_intent_id UUID NOT NULL,
    new_intent_content TEXT NOT NULL,
    
    -- 矛盾するIntent
    conflicting_intent_id UUID,
    conflicting_intent_content TEXT,
    
    -- 矛盾情報
    contradiction_type VARCHAR(50) NOT NULL,  -- tech_stack, policy_shift, duplicate, dogma
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 詳細情報
    details JSONB DEFAULT '{}',
    
    -- 解決情報
    resolution_status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected, modified
    resolution_action VARCHAR(50),  -- policy_change, mistake, coexist
    resolution_rationale TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (contradiction_type IN ('tech_stack', 'policy_shift', 'duplicate', 'dogma')),
    CHECK (resolution_status IN ('pending', 'approved', 'rejected', 'modified'))
);

CREATE INDEX IF NOT EXISTS idx_contradictions_user_id ON contradictions(user_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_new_intent ON contradictions(new_intent_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_conflicting_intent ON contradictions(conflicting_intent_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON contradictions(contradiction_type);
CREATE INDEX IF NOT EXISTS idx_contradictions_status ON contradictions(resolution_status);
CREATE INDEX IF NOT EXISTS idx_contradictions_detected_at ON contradictions(detected_at);

COMMENT ON TABLE contradictions IS '矛盾検出システム - Detected contradictions between intents';
COMMENT ON COLUMN contradictions.contradiction_type IS 'Type: tech_stack, policy_shift, duplicate, dogma';

-- ========================================
-- 7. Intent Relations (Intent関係性)
-- ========================================
CREATE TABLE IF NOT EXISTS intent_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    source_intent_id UUID NOT NULL,
    target_intent_id UUID NOT NULL,
    relation_type VARCHAR(50) NOT NULL,  -- contradicts, duplicates, extends, replaces
    similarity_score FLOAT CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (relation_type IN ('contradicts', 'duplicates', 'extends', 'replaces')),
    UNIQUE(source_intent_id, target_intent_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_intent_relations_source ON intent_relations(source_intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_relations_target ON intent_relations(target_intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_relations_type ON intent_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_intent_relations_user_id ON intent_relations(user_id);

COMMENT ON TABLE intent_relations IS 'Intent間の関係性';

-- ========================================
-- 8. Choice Points (選択保存システム)
-- ========================================
CREATE TABLE IF NOT EXISTS choice_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    choices JSONB NOT NULL,
    selected_choice_id VARCHAR(100),
    decision_rationale TEXT,
    
    -- カテゴリ・コンテキスト
    tags TEXT[] DEFAULT '{}',
    context_type VARCHAR(50) DEFAULT 'general',
    
    -- 関連情報
    session_id UUID,
    intent_id UUID,
    
    -- タイムスタンプ
    decided_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_choice_points_user_id ON choice_points(user_id);
CREATE INDEX IF NOT EXISTS idx_choice_points_tags ON choice_points USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_choice_points_context_type ON choice_points(context_type);
CREATE INDEX IF NOT EXISTS idx_choice_points_decided_at ON choice_points(decided_at);
CREATE INDEX IF NOT EXISTS idx_choice_points_session_id ON choice_points(session_id);
CREATE INDEX IF NOT EXISTS idx_choice_points_intent_id ON choice_points(intent_id);
CREATE INDEX IF NOT EXISTS idx_choice_points_question_fulltext ON choice_points USING GIN(to_tsvector('english', question));
CREATE INDEX IF NOT EXISTS idx_choice_points_choices_gin ON choice_points USING GIN(choices);

COMMENT ON TABLE choice_points IS 'Choice Preservation System - 意思決定の記録';
COMMENT ON COLUMN choice_points.question IS '質問・決定事項';
COMMENT ON COLUMN choice_points.choices IS '選択肢配列（JSONB） - 各選択肢にrejection_reason含む';
COMMENT ON COLUMN choice_points.tags IS 'カテゴリタグ (例: ["technology_stack", "database"])';
COMMENT ON COLUMN choice_points.context_type IS 'Context type: architecture, feature, bug_fix, general';

-- ========================================
-- 9. Memories (メモリシステム)
-- ========================================
CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- pgvector使用（OpenAI embedding次元）
    memory_type VARCHAR(50) NOT NULL,  -- WORKING, LONGTERM
    source_type VARCHAR(50),  -- INTENT, THOUGHT, CORRECTION, DECISION
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    archived BOOLEAN DEFAULT FALSE,
    user_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_expires_at ON memories(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE memories IS 'メモリシステム - セマンティック検索対応';
COMMENT ON COLUMN memories.embedding IS 'OpenAI embedding (1536次元)';
COMMENT ON COLUMN memories.memory_type IS 'WORKING (短期), LONGTERM (長期)';

-- ========================================
-- 10. User Profiles (ユーザープロファイル)
-- ========================================
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    persistent_context JSONB DEFAULT '{}',
    cognitive_traits JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE user_profiles IS 'ユーザーの永続的コンテキスト・認知特性';

-- ========================================
-- Triggers for NOTIFY
-- ========================================

-- Intent変更通知
CREATE OR REPLACE FUNCTION notify_intent_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('intent_updates', json_build_object(
        'id', NEW.id,
        'status', NEW.status,
        'type', NEW.type
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER intent_change_trigger
AFTER INSERT OR UPDATE ON intents
FOR EACH ROW
EXECUTE FUNCTION notify_intent_change();

-- Message変更通知
CREATE OR REPLACE FUNCTION notify_message_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('message_updates', json_build_object(
        'id', NEW.id,
        'user_id', NEW.user_id,
        'message_type', NEW.message_type
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER message_change_trigger
AFTER INSERT OR UPDATE ON messages
FOR EACH ROW
EXECUTE FUNCTION notify_message_change();

-- ========================================
-- Initial test data
-- ========================================
INSERT INTO messages (user_id, content, message_type)
VALUES ('system', 'Resonant Engine Database initialized', 'system')
ON CONFLICT DO NOTHING;

-- ========================================
-- Schema version tracking
-- ========================================
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('2.0.0', 'Complete schema - Backend API integration完了後の統合スキーマ')
ON CONFLICT (version) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Resonant Engine Database Schema v2.0.0 created successfully!';
    RAISE NOTICE 'Tables created: messages, specifications, intents, corrections, notifications, contradictions, intent_relations, choice_points, memories, user_profiles';
END $$;
