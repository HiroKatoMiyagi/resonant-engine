import pytest

from bridge.core.constants import BridgeTypeEnum, LogSeverity
from bridge.providers.audit import MockAuditLogger


@pytest.mark.asyncio
async def test_mock_audit_logger_records_entries() -> None:
    logger = MockAuditLogger()
    await logger.log(
        bridge_type=BridgeTypeEnum.INPUT,
        operation="save_intent",
        details={"intent_type": "review"},
        intent_id="intent-123",
        correlation_id="corr-123",
    )
    assert len(logger.entries) == 1
    entry = logger.entries[0]
    assert entry["bridge_type"] == BridgeTypeEnum.INPUT.value
    assert entry["operation"] == "save_intent"
    assert entry["severity"] == LogSeverity.INFO.value

    await logger.cleanup()
    assert not logger.entries
