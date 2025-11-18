-- Sprint 4.5: Claude Code API Integration
-- Claude Codeセッション管理とツール実行履歴テーブル

-- Claude Codeセッション管理テーブル
CREATE TABLE IF NOT EXISTS claude_code_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id UUID NOT NULL REFERENCES intents(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'timeout')),
    workspace_path TEXT,
    workspace_mode VARCHAR(50) DEFAULT 'repository',  -- 'repository' or 'isolated'
    metadata JSONB DEFAULT '{}',  -- context_files, branch, etc.
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_duration_seconds INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Claude Code実行履歴テーブル（ツール呼び出し単位）
CREATE TABLE IF NOT EXISTS claude_code_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES claude_code_sessions(id) ON DELETE CASCADE,
    execution_order INTEGER NOT NULL,
    tool_name VARCHAR(100),  -- 'Edit', 'Write', 'Read', 'Bash', 'Grep', etc.
    input_data JSONB,
    output_data JSONB,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES claude_code_sessions(id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_sessions_intent ON claude_code_sessions(intent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON claude_code_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON claude_code_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_session ON claude_code_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_executions_order ON claude_code_executions(session_id, execution_order);
CREATE INDEX IF NOT EXISTS idx_executions_tool ON claude_code_executions(tool_name);

-- updated_atトリガー（既存のupdate_updated_at_column関数を使用）
CREATE TRIGGER update_claude_code_sessions_updated_at
    BEFORE UPDATE ON claude_code_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- コメント
COMMENT ON TABLE claude_code_sessions IS 'Claude Codeセッション管理（Sprint 4.5）';
COMMENT ON TABLE claude_code_executions IS 'Claude Code実行履歴（ツール呼び出し単位）';
COMMENT ON COLUMN claude_code_sessions.workspace_mode IS 'repository: メインリポジトリで実行, isolated: 独立ワークスペース';
COMMENT ON COLUMN claude_code_sessions.metadata IS 'コンテキストファイル、Git branch等の追加情報';
COMMENT ON COLUMN claude_code_executions.tool_name IS 'Claude Codeが使用したツール名';
