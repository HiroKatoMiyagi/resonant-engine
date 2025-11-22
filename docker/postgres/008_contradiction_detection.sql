-- Sprint 11: Contradiction Detection Layer
-- 矛盾検出層のデータベーススキーマ

-- contradictions テーブル
CREATE TABLE IF NOT EXISTS contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 新規Intent / New Intent
    new_intent_id UUID NOT NULL,
    new_intent_content TEXT NOT NULL,

    -- 矛盾するIntent / Conflicting Intent
    conflicting_intent_id UUID,
    conflicting_intent_content TEXT,

    -- 矛盾情報 / Contradiction Information
    contradiction_type VARCHAR(50) NOT NULL,  -- 'tech_stack', 'policy_shift', 'duplicate', 'dogma'
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 詳細情報 / Details
    details JSONB DEFAULT '{}',

    -- 解決情報 / Resolution Information
    resolution_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'modified'
    resolution_action VARCHAR(50),  -- 'policy_change', 'mistake', 'coexist'
    resolution_rationale TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),

    -- メタデータ / Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約 / Constraints
    CHECK (contradiction_type IN ('tech_stack', 'policy_shift', 'duplicate', 'dogma')),
    CHECK (resolution_status IN ('pending', 'approved', 'rejected', 'modified'))
);

-- intent_relations テーブル
CREATE TABLE IF NOT EXISTS intent_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- Intent関係 / Intent Relationship
    source_intent_id UUID NOT NULL,
    target_intent_id UUID NOT NULL,
    relation_type VARCHAR(50) NOT NULL,  -- 'contradicts', 'duplicates', 'extends', 'replaces'

    -- 関係強度 / Relationship Strength
    similarity_score FLOAT CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),

    -- メタデータ / Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約 / Constraints
    CHECK (relation_type IN ('contradicts', 'duplicates', 'extends', 'replaces')),
    UNIQUE(source_intent_id, target_intent_id, relation_type)
);

-- インデックス作成 / Create Indexes
CREATE INDEX IF NOT EXISTS idx_contradictions_user_id ON contradictions(user_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_new_intent ON contradictions(new_intent_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_conflicting_intent ON contradictions(conflicting_intent_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON contradictions(contradiction_type);
CREATE INDEX IF NOT EXISTS idx_contradictions_status ON contradictions(resolution_status);
CREATE INDEX IF NOT EXISTS idx_contradictions_detected_at ON contradictions(detected_at);

CREATE INDEX IF NOT EXISTS idx_intent_relations_source ON intent_relations(source_intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_relations_target ON intent_relations(target_intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_relations_type ON intent_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_intent_relations_user_id ON intent_relations(user_id);

-- コメント追加 / Add Comments
COMMENT ON TABLE contradictions IS 'Sprint 11: Detected contradictions between intents';
COMMENT ON COLUMN contradictions.contradiction_type IS 'Type: tech_stack, policy_shift, duplicate, dogma';
COMMENT ON COLUMN contradictions.confidence_score IS 'Detection confidence (0.0 - 1.0)';
COMMENT ON COLUMN contradictions.resolution_status IS 'Status: pending, approved, rejected, modified';
COMMENT ON COLUMN contradictions.details IS 'JSON details about the contradiction (old_tech, new_tech, etc.)';

COMMENT ON TABLE intent_relations IS 'Sprint 11: Relationships between intents';
COMMENT ON COLUMN intent_relations.relation_type IS 'Type: contradicts, duplicates, extends, replaces';
COMMENT ON COLUMN intent_relations.similarity_score IS 'Similarity score for duplicate detection (0.0 - 1.0)';
