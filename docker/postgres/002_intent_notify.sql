-- Intent LISTEN/NOTIFY Triggers
-- Sprint 4: Intent Processing Daemon

-- Intent作成時に通知を発火
CREATE OR REPLACE FUNCTION notify_intent_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'intent_created',
        json_build_object(
            'id', NEW.id::text,
            'description', substring(NEW.description, 1, 100),
            'priority', NEW.priority
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS intent_created_trigger ON intents;
CREATE TRIGGER intent_created_trigger
    AFTER INSERT ON intents
    FOR EACH ROW
    EXECUTE FUNCTION notify_intent_created();

-- ステータス変更通知
CREATE OR REPLACE FUNCTION notify_intent_status_changed()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status != NEW.status THEN
        PERFORM pg_notify(
            'intent_status_changed',
            json_build_object(
                'id', NEW.id::text,
                'old_status', OLD.status,
                'new_status', NEW.status
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS intent_status_trigger ON intents;
CREATE TRIGGER intent_status_trigger
    AFTER UPDATE ON intents
    FOR EACH ROW
    EXECUTE FUNCTION notify_intent_status_changed();

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Intent notification triggers created successfully!';
END $$;
