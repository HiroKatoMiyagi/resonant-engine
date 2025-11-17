-- Resonant Dashboard Database Schema
-- Sprint 1: Docker Compose + PostgreSQL Environment Setup

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Messages (Slack風メッセージ)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'user',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE messages IS 'Slack風メッセージシステム';
COMMENT ON COLUMN messages.message_type IS 'user, yuno, kana, system';

-- 2. Specifications (仕様書管理)
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

COMMENT ON TABLE specifications IS 'Notion代替の仕様書管理';
COMMENT ON COLUMN specifications.status IS 'draft, review, approved';

-- 3. Intents (Intent管理)
CREATE TABLE IF NOT EXISTS intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    intent_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    result JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE intents IS 'Intent自動処理システム';
COMMENT ON COLUMN intents.status IS 'pending, processing, completed, failed';

-- 4. Notifications (通知システム)
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

COMMENT ON TABLE notifications IS 'リアルタイム通知';
COMMENT ON COLUMN notifications.notification_type IS 'info, success, warning, error';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);

CREATE INDEX IF NOT EXISTS idx_specifications_status ON specifications(status);
CREATE INDEX IF NOT EXISTS idx_specifications_tags ON specifications USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_specifications_created_at ON specifications(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_intents_status ON intents(status);
CREATE INDEX IF NOT EXISTS idx_intents_created_at ON intents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_intents_priority ON intents(priority DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Initial test data
INSERT INTO messages (user_id, content, message_type)
VALUES ('hiroki', 'Dashboard system initialized', 'system');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database schema created successfully!';
END $$;
