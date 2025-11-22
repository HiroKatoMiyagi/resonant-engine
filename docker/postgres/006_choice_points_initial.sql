-- Sprint 8: Choice Preservation System - Initial Schema
-- Author: Kana (Claude Sonnet 4.5)
-- Date: 2025-11-20
-- Purpose: Create choice_points table for preserving decision history

-- choice_points テーブル作成
CREATE TABLE IF NOT EXISTS choice_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    choices JSONB NOT NULL,
    selected_choice_id VARCHAR(100),
    decision_rationale TEXT,
    tags TEXT[] DEFAULT '{}',
    context_type VARCHAR(50) DEFAULT 'general',
    session_id UUID,
    intent_id UUID,
    decided_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_choice_points_user_id ON choice_points(user_id);
CREATE INDEX IF NOT EXISTS idx_choice_points_tags ON choice_points USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_choice_points_context_type ON choice_points(context_type);
CREATE INDEX IF NOT EXISTS idx_choice_points_decided_at ON choice_points(decided_at);
CREATE INDEX IF NOT EXISTS idx_choice_points_session_id ON choice_points(session_id);
CREATE INDEX IF NOT EXISTS idx_choice_points_intent_id ON choice_points(intent_id);

-- フルテキスト検索用インデックス
CREATE INDEX IF NOT EXISTS idx_choice_points_question_fulltext
    ON choice_points USING GIN(to_tsvector('english', question));

-- choices配列のJSONB検索用インデックス
CREATE INDEX IF NOT EXISTS idx_choice_points_choices_gin
    ON choice_points USING GIN(choices);

-- コメント追加
COMMENT ON TABLE choice_points IS 'Sprint 8: Choice Preservation System - Decision history';
COMMENT ON COLUMN choice_points.user_id IS 'User who created this choice point';
COMMENT ON COLUMN choice_points.question IS 'The question or decision to be made';
COMMENT ON COLUMN choice_points.choices IS 'Array of choice options with metadata';
COMMENT ON COLUMN choice_points.selected_choice_id IS 'ID of the selected choice';
COMMENT ON COLUMN choice_points.decision_rationale IS 'Reason for the decision';
COMMENT ON COLUMN choice_points.tags IS 'Categorization tags (e.g., ["technology_stack", "database"])';
COMMENT ON COLUMN choice_points.context_type IS 'Context type: "architecture", "feature", "bug_fix", "general"';
COMMENT ON COLUMN choice_points.session_id IS 'Associated session ID';
COMMENT ON COLUMN choice_points.intent_id IS 'Associated intent ID';
COMMENT ON COLUMN choice_points.decided_at IS 'Timestamp when decision was made';
