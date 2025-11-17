import asyncio
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio

from bridge.api.reeval import reeval_intent
from bridge.core.constants import LogSeverity, PhilosophicalActor
from bridge.core.models.intent_model import IntentModel
from bridge.core.models.reeval import ReEvaluationRequest
from bridge.providers.audit import MockAuditLogger
from bridge.providers.data import MockDataBridge


class StarvingDataBridge(MockDataBridge):
    def __init__(self) -> None:
        super().__init__()
        self.fallback_lock_calls = 0

    async def update_intent_if_version_matches(self, intent_id: str, intent: IntentModel, *, expected_version: int) -> bool:
        await asyncio.sleep(0)
        return False

    @asynccontextmanager
    async def lock_intent_for_update(self, intent_id: str, *, timeout: float = 5.0):
        self.fallback_lock_calls += 1
        async with super().lock_intent_for_update(intent_id, timeout=timeout) as session:
            yield session


class PartialStarvationDataBridge(StarvingDataBridge):
    def __init__(self, failures_before_success: int) -> None:
        super().__init__()
        self._remaining_failures = failures_before_success

    async def update_intent_if_version_matches(self, intent_id: str, intent: IntentModel, *, expected_version: int) -> bool:
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            return await super().update_intent_if_version_matches(intent_id, intent, expected_version=expected_version)
        return await MockDataBridge.update_intent_if_version_matches(self, intent_id, intent, expected_version=expected_version)


@pytest_asyncio.fixture
async def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()


async def _create_intent(data_bridge: MockDataBridge) -> IntentModel:
    intent = IntentModel.new(intent_type="optimistic-fallback", payload={"field": "initial"})
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_optimistic_lock_starvation_detection(audit_logger: MockAuditLogger) -> None:
    data_bridge = PartialStarvationDataBridge(failures_before_success=3)
    await data_bridge.connect()
    try:
        persisted = await _create_intent(data_bridge)
        request = ReEvaluationRequest(
            intent_id=persisted.id,
            diff={"payload": {"field": "updated"}},
            source=PhilosophicalActor.KANA,
            reason="starvation-detection",
        )

        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

        warning_entries = [entry for entry in audit_logger.entries if entry["severity"] == LogSeverity.WARNING.value]
        assert warning_entries, "Starvation should emit a warning audit entry"
        details = warning_entries[-1]["details"]
        assert details.get("starvation_detected") is True
        assert details.get("retry_count") >= 3
        final = await data_bridge.get_intent(persisted.intent_id)
        assert final.payload["field"] == "updated"
    finally:
        await data_bridge.disconnect()


@pytest.mark.asyncio
async def test_optimistic_to_pessimistic_fallback(audit_logger: MockAuditLogger) -> None:
    data_bridge = StarvingDataBridge()
    await data_bridge.connect()
    try:
        persisted = await _create_intent(data_bridge)
        request = ReEvaluationRequest(
            intent_id=persisted.id,
            diff={"payload": {"extra": "fallback"}},
            source=PhilosophicalActor.YUNO,
            reason="fallback-path",
        )

        response = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

        assert response.already_applied is False
        assert data_bridge.fallback_lock_calls >= 1, "Fallback must acquire pessimistic lock"
        updated = await data_bridge.get_intent(persisted.intent_id)
        assert updated.payload["extra"] == "fallback"
    finally:
        await data_bridge.disconnect()
