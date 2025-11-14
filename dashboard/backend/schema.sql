-- dashboard/backend/schema.sql

-- ユーザー
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 仕様書
CREATE TABLE IF NOT EXISTS specs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  content TEXT,
  status TEXT DEFAULT 'draft',
  sync_trigger BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- メッセージ
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  thread_id UUID,
  sender TEXT NOT NULL,
  content TEXT NOT NULL,
  intent_id UUID,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Intent
CREATE TABLE IF NOT EXISTS intents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  type TEXT NOT NULL,
  data JSONB,
  status TEXT DEFAULT 'pending',
  source TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);

-- 通知
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  body TEXT,
  link TEXT,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_specs_user_id ON specs(user_id);
CREATE INDEX IF NOT EXISTS idx_specs_sync_trigger ON specs(sync_trigger) WHERE sync_trigger = TRUE;
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_intents_status ON intents(status);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id_read ON notifications(user_id, read);

-- WebSocket通知用のNOTIFY関数
CREATE OR REPLACE FUNCTION notify_table_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify(
    'table_changes',
    json_build_object(
      'table', TG_TABLE_NAME,
      'operation', TG_OP,
      'id', COALESCE(NEW.id::text, OLD.id::text),
      'timestamp', CURRENT_TIMESTAMP
    )::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Intent変更時のNOTIFYトリガー
DROP TRIGGER IF EXISTS intent_change_notify ON intents;
CREATE TRIGGER intent_change_notify
AFTER INSERT OR UPDATE OR DELETE ON intents
FOR EACH ROW EXECUTE FUNCTION notify_table_change();

-- Message変更時のNOTIFYトリガー
DROP TRIGGER IF EXISTS message_change_notify ON messages;
CREATE TRIGGER message_change_notify
AFTER INSERT OR UPDATE OR DELETE ON messages
FOR EACH ROW EXECUTE FUNCTION notify_table_change();

-- Spec変更時のNOTIFYトリガー
DROP TRIGGER IF EXISTS spec_change_notify ON specs;
CREATE TRIGGER spec_change_notify
AFTER INSERT OR UPDATE OR DELETE ON specs
FOR EACH ROW EXECUTE FUNCTION notify_table_change();
