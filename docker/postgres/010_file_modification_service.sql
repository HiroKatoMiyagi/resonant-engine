-- ========================================
-- Phase 3: FileModificationService Tables
-- 作成日: 2025-12-30
-- 作成者: Kana (Claude Opus 4.5)
-- ========================================

-- file_operation_logs（操作ログ）
CREATE TABLE IF NOT EXISTS file_operation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    operation VARCHAR(50) NOT NULL,  -- write, delete, rename, read
    reason TEXT,
    requested_by VARCHAR(100),  -- user, ai_agent, system
    constraint_level VARCHAR(50),
    result VARCHAR(50) NOT NULL,  -- approved, rejected, blocked
    old_content_hash VARCHAR(64),
    new_content_hash VARCHAR(64),
    backup_path VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_file_op_logs_user
    ON file_operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_file
    ON file_operation_logs(file_path);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_time
    ON file_operation_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_operation
    ON file_operation_logs(operation);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_result
    ON file_operation_logs(result);

-- file_backups（バックアップ管理）
CREATE TABLE IF NOT EXISTS file_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    original_path VARCHAR(500) NOT NULL,
    backup_path VARCHAR(500) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    operation_log_id UUID REFERENCES file_operation_logs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE  -- 自動削除用
);

CREATE INDEX IF NOT EXISTS idx_file_backups_user
    ON file_backups(user_id);
CREATE INDEX IF NOT EXISTS idx_file_backups_original
    ON file_backups(original_path);
CREATE INDEX IF NOT EXISTS idx_file_backups_expires
    ON file_backups(expires_at);

-- 操作統計ビュー
CREATE OR REPLACE VIEW file_operation_stats AS
SELECT
    user_id,
    operation,
    result,
    constraint_level,
    COUNT(*) as count,
    DATE_TRUNC('day', created_at) as day
FROM file_operation_logs
GROUP BY user_id, operation, result, constraint_level, DATE_TRUNC('day', created_at);

-- ユーザー別の最近の操作を取得する関数
CREATE OR REPLACE FUNCTION get_recent_file_operations(
    p_user_id VARCHAR,
    p_limit INT DEFAULT 50
) RETURNS TABLE (
    id UUID,
    file_path VARCHAR,
    operation VARCHAR,
    result VARCHAR,
    constraint_level VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fol.id,
        fol.file_path,
        fol.operation,
        fol.result,
        fol.constraint_level,
        fol.created_at
    FROM file_operation_logs fol
    WHERE fol.user_id = p_user_id
    ORDER BY fol.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
