"""SQL helpers for PostgreSQL triggers used by the real-time layer."""

from __future__ import annotations

import asyncpg

INTENT_CHANGED_FUNCTION = """
CREATE OR REPLACE FUNCTION notify_intent_changed()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'intent_changed',
        json_build_object(
            'event_type', TG_OP,
            'intent_id', NEW.id,
            'status', NEW.status,
            'type', NEW.type,
            'version', COALESCE(NEW.version, 0),
            'updated_at', NEW.updated_at,
            'correlation_id', NEW.correlation_id
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

INTENT_CHANGED_TRIGGER = """
DROP TRIGGER IF EXISTS intent_changed_trigger ON intents;
CREATE TRIGGER intent_changed_trigger
AFTER INSERT OR UPDATE ON intents
FOR EACH ROW
EXECUTE FUNCTION notify_intent_changed();
"""

AUDIT_LOG_CREATED_FUNCTION = """
CREATE OR REPLACE FUNCTION notify_audit_log_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'audit_log_created',
        json_build_object(
            'event_type', TG_OP,
            'log_id', NEW.id,
            'intent_id', NEW.intent_id,
            'operation', NEW.operation,
            'level', NEW.level,
            'bridge_type', NEW.bridge_type,
            'correlation_id', NEW.correlation_id,
            'created_at', NEW.timestamp
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

AUDIT_LOG_CREATED_TRIGGER = """
DROP TRIGGER IF EXISTS audit_log_created_trigger ON audit_logs;
CREATE TRIGGER audit_log_created_trigger
AFTER INSERT ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION notify_audit_log_created();
"""


def get_trigger_statements() -> tuple[str, str, str, str]:
    """Return SQL statements used to bootstrap LISTEN/NOTIFY triggers."""

    return (
        INTENT_CHANGED_FUNCTION,
        INTENT_CHANGED_TRIGGER,
        AUDIT_LOG_CREATED_FUNCTION,
        AUDIT_LOG_CREATED_TRIGGER,
    )


async def ensure_realtime_triggers(database_url: str | None) -> None:
    """Ensure trigger functions exist before LISTEN/NOTIFY begins."""

    if not database_url:
        raise ValueError("database_url is required to install triggers")
    connection = await asyncpg.connect(database_url)
    try:
        for statement in get_trigger_statements():
            await connection.execute(statement)
    finally:
        await connection.close()
