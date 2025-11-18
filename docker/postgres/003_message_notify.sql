-- Message LISTEN/NOTIFY Triggers
-- Message Response Feature: Auto-respond to user messages

-- Message作成時に通知を発火（user typeのみ）
CREATE OR REPLACE FUNCTION notify_message_created()
RETURNS TRIGGER AS $$
BEGIN
    -- ユーザーメッセージのみ通知（Kana/Yunoの応答は通知しない）
    IF NEW.message_type = 'user' THEN
        PERFORM pg_notify(
            'message_created',
            json_build_object(
                'id', NEW.id::text,
                'user_id', NEW.user_id,
                'content', substring(NEW.content, 1, 200),
                'message_type', NEW.message_type
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS message_created_trigger ON messages;
CREATE TRIGGER message_created_trigger
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_message_created();

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Message notification triggers created successfully!';
END $$;
