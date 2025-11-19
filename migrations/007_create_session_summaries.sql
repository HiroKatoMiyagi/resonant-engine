-- Sprint 7: Session Summaries テーブル作成
-- セッション単位の会話要約を保存するテーブル

CREATE TABLE IF NOT EXISTS session_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id UUID NOT NULL,
    summary TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    CONSTRAINT unique_session_summary UNIQUE (user_id, session_id),
    CONSTRAINT positive_message_count CHECK (message_count >= 0)
);

-- インデックス
CREATE INDEX idx_session_summaries_user_id
    ON session_summaries(user_id);

CREATE INDEX idx_session_summaries_session_id
    ON session_summaries(session_id);

CREATE INDEX idx_session_summaries_created_at
    ON session_summaries(created_at DESC);

-- コメント
COMMENT ON TABLE session_summaries IS 'セッション単位の会話要約';
COMMENT ON COLUMN session_summaries.summary IS '要約テキスト（Claude生成）';
COMMENT ON COLUMN session_summaries.message_count IS '要約に含まれるメッセージ数';
COMMENT ON COLUMN session_summaries.start_time IS 'セッション開始時刻';
COMMENT ON COLUMN session_summaries.end_time IS 'セッション終了時刻';
