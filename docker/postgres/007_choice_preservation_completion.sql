-- ========================================
-- Sprint 10: Choice Preservation Completion
-- ========================================
-- Author: Kana (Claude Sonnet 4.5)
-- Date: 2025-11-20
-- Purpose: Extend choice_points table for historical query and context integration

-- 1. choice_points テーブル拡張
ALTER TABLE choice_points
ADD COLUMN IF NOT EXISTS user_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS context_type VARCHAR(50) DEFAULT 'general';

-- user_idをNOT NULLに設定（既存レコードがある場合はデフォルト値設定）
UPDATE choice_points SET user_id = 'legacy_user' WHERE user_id IS NULL;
ALTER TABLE choice_points ALTER COLUMN user_id SET NOT NULL;

-- インデックス追加
CREATE INDEX IF NOT EXISTS idx_choice_points_user_id ON choice_points(user_id);
CREATE INDEX IF NOT EXISTS idx_choice_points_tags ON choice_points USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_choice_points_context_type ON choice_points(context_type);
CREATE INDEX IF NOT EXISTS idx_choice_points_decided_at ON choice_points(decided_at);

-- 2. フルテキスト検索用インデックス
CREATE INDEX IF NOT EXISTS idx_choice_points_question_fulltext
    ON choice_points USING GIN(to_tsvector('english', question));

-- 3. choices配列のJSONB検索用インデックス
-- (既にJSONBカラムの場合のみ)
CREATE INDEX IF NOT EXISTS idx_choice_points_choices_gin
    ON choice_points USING GIN(choices);

-- 4. コメント追加
COMMENT ON COLUMN choice_points.user_id IS 'User who created this choice point';
COMMENT ON COLUMN choice_points.tags IS 'Categorization tags (e.g., ["technology_stack", "database"])';
COMMENT ON COLUMN choice_points.context_type IS 'Context type: "architecture", "feature", "bug_fix", "general"';

-- 5. 既存データの確認クエリ（実行しなくてもOK）
-- SELECT
--     COUNT(*) as total_choice_points,
--     COUNT(DISTINCT user_id) as unique_users,
--     COUNT(*) FILTER (WHERE tags IS NOT NULL AND array_length(tags, 1) > 0) as tagged_points
-- FROM choice_points;
