-- Sprint 4.5: Claude Code Integration
-- Database Schema for Claude Code Sessions and Executions

-- 1. Claude Code Sessions テーブル
CREATE TABLE IF NOT EXISTS claude_code_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id UUID NOT NULL REFERENCES intents(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    total_duration_seconds INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE claude_code_sessions IS 'Claude Codeセッション管理';
COMMENT ON COLUMN claude_code_sessions.status IS 'pending, running, completed, failed, timeout';
COMMENT ON COLUMN claude_code_sessions.session_id IS 'Claude Code CLIセッションID';

-- 2. Claude Code Executions テーブル
CREATE TABLE IF NOT EXISTS claude_code_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES claude_code_sessions(id) ON DELETE CASCADE,
    execution_order INTEGER NOT NULL,
    tool_name VARCHAR(100),
    input_data JSONB,
    output_data JSONB,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_ms INTEGER
);

COMMENT ON TABLE claude_code_executions IS 'Claude Code実行履歴';
COMMENT ON COLUMN claude_code_executions.tool_name IS 'Edit, Write, Read, Bash, Grep, etc.';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_claude_code_sessions_intent ON claude_code_sessions(intent_id);
CREATE INDEX IF NOT EXISTS idx_claude_code_sessions_status ON claude_code_sessions(status);
CREATE INDEX IF NOT EXISTS idx_claude_code_sessions_created_at ON claude_code_sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_claude_code_executions_session ON claude_code_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_claude_code_executions_order ON claude_code_executions(session_id, execution_order);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Claude Code tables created successfully!';
END $$;
