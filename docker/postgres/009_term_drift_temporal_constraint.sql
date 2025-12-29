-- ========================================
-- Sprint 12: Term Drift & Temporal Constraint Tables
-- ========================================

-- ========================================
-- Part 1: Term Drift Detection
-- ========================================

-- 1. term_definitions（用語定義履歴）
CREATE TABLE IF NOT EXISTS term_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- 用語情報
    term_name VARCHAR(255) NOT NULL,
    term_category VARCHAR(100),  -- 'domain_object', 'technical', 'process', 'custom'
    
    -- 定義内容
    definition_text TEXT NOT NULL,
    definition_context TEXT,  -- どこで定義されたか
    definition_source VARCHAR(255),  -- ファイル名、Intent ID等
    
    -- 構造化定義（オプション）
    structured_definition JSONB,  -- {fields: [], methods: [], relations: []}
    
    -- バージョン管理
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES term_definitions(id),
    
    -- タイムスタンプ
    defined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_term_definitions_user ON term_definitions(user_id);
CREATE INDEX IF NOT EXISTS idx_term_definitions_term ON term_definitions(term_name);
CREATE INDEX IF NOT EXISTS idx_term_definitions_current ON term_definitions(is_current) WHERE is_current = TRUE;
CREATE INDEX IF NOT EXISTS idx_term_definitions_category ON term_definitions(term_category);

-- 2. term_drifts（検出されたドリフト）
CREATE TABLE IF NOT EXISTS term_drifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- 用語情報
    term_name VARCHAR(255) NOT NULL,
    
    -- 変化情報
    original_definition_id UUID REFERENCES term_definitions(id),
    new_definition_id UUID REFERENCES term_definitions(id),
    drift_type VARCHAR(50) NOT NULL,  -- 'expansion', 'contraction', 'semantic_shift', 'context_change'
    
    -- 分析結果
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    change_summary TEXT,
    impact_analysis JSONB,  -- {affected_files: [], affected_intents: [], severity: 'high'}
    
    -- ステータス
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'acknowledged', 'resolved', 'dismissed'
    resolution_action VARCHAR(100),  -- 'intentional_change', 'rollback', 'migration_needed'
    resolution_note TEXT,
    resolved_by VARCHAR(255),
    
    -- タイムスタンプ
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_term_drifts_user ON term_drifts(user_id);
CREATE INDEX IF NOT EXISTS idx_term_drifts_term ON term_drifts(term_name);
CREATE INDEX IF NOT EXISTS idx_term_drifts_status ON term_drifts(status);
CREATE INDEX IF NOT EXISTS idx_term_drifts_detected ON term_drifts(detected_at DESC);

-- ========================================
-- Part 2: Temporal Constraint Layer
-- ========================================

-- 3. file_verifications（ファイル検証履歴）
CREATE TABLE IF NOT EXISTS file_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- ファイル情報
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64),  -- SHA-256
    
    -- 検証情報
    verification_type VARCHAR(100),  -- 'unit_test', 'integration_test', 'manual_test', 'production_stable'
    verification_description TEXT,
    test_hours_invested FLOAT DEFAULT 0,  -- テストに費やした時間
    
    -- 制約レベル
    constraint_level VARCHAR(50) DEFAULT 'low',  -- 'critical', 'high', 'medium', 'low'
    
    -- タイムスタンプ
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stable_since TIMESTAMP WITH TIME ZONE,  -- 安定稼働開始日
    
    -- メタデータ
    verified_by VARCHAR(255),
    metadata JSONB
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_file_verifications_file ON file_verifications(user_id, file_path);
CREATE INDEX IF NOT EXISTS idx_file_verifications_level ON file_verifications(constraint_level);
CREATE INDEX IF NOT EXISTS idx_file_verifications_verified ON file_verifications(verified_at DESC);

-- 4. temporal_constraint_logs（制約ログ）
CREATE TABLE IF NOT EXISTS temporal_constraint_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- ファイル情報
    file_path VARCHAR(500) NOT NULL,
    file_verification_id UUID REFERENCES file_verifications(id),
    
    -- リクエスト情報
    modification_type VARCHAR(50),  -- 'edit', 'delete', 'rename'
    modification_reason TEXT,
    requested_by VARCHAR(255),  -- 'user', 'ai_agent', 'system'
    
    -- 制約チェック結果
    constraint_level_at_check VARCHAR(50),
    check_result VARCHAR(50),  -- 'approved', 'rejected', 'pending'
    
    -- 承認情報
    approval_required BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approval_note TEXT,
    
    -- タイムスタンプ
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decided_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_temporal_logs_user ON temporal_constraint_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_temporal_logs_file ON temporal_constraint_logs(file_path);
CREATE INDEX IF NOT EXISTS idx_temporal_logs_result ON temporal_constraint_logs(check_result);
CREATE INDEX IF NOT EXISTS idx_temporal_logs_time ON temporal_constraint_logs(requested_at DESC);

-- ========================================
-- Functions
-- ========================================

-- 用語の最新定義を取得
CREATE OR REPLACE FUNCTION get_current_term_definition(
    p_user_id VARCHAR,
    p_term_name VARCHAR
) RETURNS TABLE (
    id UUID,
    definition_text TEXT,
    version INTEGER,
    defined_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT td.id, td.definition_text, td.version, td.defined_at
    FROM term_definitions td
    WHERE td.user_id = p_user_id
        AND td.term_name = p_term_name
        AND td.is_current = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ファイルの制約レベルを取得
CREATE OR REPLACE FUNCTION get_file_constraint_level(
    p_user_id VARCHAR,
    p_file_path VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_level VARCHAR;
BEGIN
    SELECT constraint_level INTO v_level
    FROM file_verifications
    WHERE user_id = p_user_id
        AND file_path = p_file_path;
    
    RETURN COALESCE(v_level, 'low');
END;
$$ LANGUAGE plpgsql;
