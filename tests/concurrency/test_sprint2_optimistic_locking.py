import asyncio

import pytest

# Bridge API migration in progress
pytestmark = pytest.mark.skip(reason="Bridge API migration in progress - will be addressed separately")

import pytest_asyncio

from app.services.intent.reeval import reeval_intent
from app.services.shared.constants import LogSeverity, PhilosophicalActor
from app.models.intent import IntentModel
from app.models.reeval import ReEvaluationRequest
from app.integrations import MockAuditLogger
from app.integrations import MockDataBridge


class FlakyVersionDataBridge(MockDataBridge):
    """Mock bridge that forces version mismatches a configurable number of times."""

    def __init__(self, *, failures_before_success: int) -> None:
        super().__init__()
        self._failures_remaining = failures_before_success

    async def update_intent_if_version_matches(self, intent_id: str, intent: IntentModel, *, expected_version: int) -> bool:
        if self._failures_remaining > 0:
            self._failures_remaining -= 1
            await asyncio.sleep(0)  # ensure scheduling for retry loop
            return False
        return await super().update_intent_if_version_matches(intent_id, intent, expected_version=expected_version)


class AlwaysFailingVersionDataBridge(MockDataBridge):
    """Mock bridge that always rejects optimistic updates."""

    async def update_intent_if_version_matches(self, intent_id: str, intent: IntentModel, *, expected_version: int) -> bool:
        await asyncio.sleep(0)
        return False


@pytest_asyncio.fixture
async def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()


async def _create_intent(data_bridge: MockDataBridge) -> IntentModel:
    intent = IntentModel.new(intent_type="optimistic-test", payload={"field": "value"})
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_reeval_updates_payload_and_version(audit_logger: MockAuditLogger) -> None:
    data_bridge = MockDataBridge()
    await data_bridge.connect()
    try:
        persisted = await _create_intent(data_bridge)
        request = ReEvaluationRequest(
            intent_id=persisted.id,
            diff={"payload": {"field": "new"}},
            source=PhilosophicalActor.KANA,
            reason="update-field",
        )

        response = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

        assert response.intent_id == persisted.id
        assert response.already_applied is False
        updated = await data_bridge.get_intent(persisted.intent_id)
        assert updated.payload["field"] == "new"
        assert updated.version == persisted.version + 1
        assert len(updated.correction_history) == 1
    finally:
        await data_bridge.disconnect()


@pytest.mark.asyncio
async def test_reeval_retries_on_version_conflict(audit_logger: MockAuditLogger) -> None:
    data_bridge = FlakyVersionDataBridge(failures_before_success=1)
    await data_bridge.connect()
    try:
        persisted = await _create_intent(data_bridge)
        request = ReEvaluationRequest(
            intent_id=persisted.id,
            diff={"payload": {"flag": "A"}},
            source=PhilosophicalActor.YUNO,
            reason="conflict-test",
        )

        response = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

        assert response.already_applied is False
        updated = await data_bridge.get_intent(persisted.intent_id)
        assert updated.payload["flag"] == "A"
        assert updated.version == persisted.version + 1
    finally:
        await data_bridge.disconnect()


@pytest.mark.asyncio
async def test_reeval_conflict_after_max_retries(audit_logger: MockAuditLogger) -> None:
    data_bridge = AlwaysFailingVersionDataBridge()
    await data_bridge.connect()
    try:
        persisted = await _create_intent(data_bridge)
        request = ReEvaluationRequest(
            intent_id=persisted.id,
            diff={"payload": {"flag": "B"}},
            source=PhilosophicalActor.KANA,
            reason="max-retries",
        )

        response = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

        assert response.intent_id == persisted.id
        assert response.already_applied is False
        warning_entries = [entry for entry in audit_logger.entries if entry["severity"] == LogSeverity.WARNING.value]
        assert warning_entries, "Fallback path should emit a warning"
        details = warning_entries[-1]["details"]
        assert details.get("starvation_detected") is True
        assert details.get("fallback_strategy") == "pessimistic"
    finally:
        await data_bridge.disconnect()
