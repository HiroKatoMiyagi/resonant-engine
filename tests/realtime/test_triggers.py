from app.services.realtime.triggers import (
    AUDIT_LOG_CREATED_FUNCTION,
    AUDIT_LOG_CREATED_TRIGGER,
    INTENT_CHANGED_FUNCTION,
    INTENT_CHANGED_TRIGGER,
    get_trigger_statements,
)


def test_trigger_statements_cover_all_channels():
    statements = get_trigger_statements()
    assert INTENT_CHANGED_FUNCTION in statements
    assert INTENT_CHANGED_TRIGGER in statements
    assert AUDIT_LOG_CREATED_FUNCTION in statements
    assert AUDIT_LOG_CREATED_TRIGGER in statements
    assert len(statements) == 4


def test_intent_trigger_notifies_expected_fields():
    assert "'intent_changed'" in INTENT_CHANGED_FUNCTION
    assert "NEW.status" in INTENT_CHANGED_FUNCTION
    assert "NEW.correlation_id" in INTENT_CHANGED_FUNCTION


def test_audit_trigger_notifies_expected_fields():
    assert "'audit_log_created'" in AUDIT_LOG_CREATED_FUNCTION
    assert "NEW.operation" in AUDIT_LOG_CREATED_FUNCTION
    assert "NEW.timestamp" in AUDIT_LOG_CREATED_FUNCTION
