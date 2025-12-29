import asyncio
import random
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio

from app.services.intent.bridge_set import BridgeSet
from app.services.shared.constants import TechnicalActor
from app.services.shared.errors import DeadlockError
from app.models.intent import IntentModel
from app.services.intent.retry import retry_on_deadlock
from app.integrations import MockAIBridge
from app.integrations import MockAuditLogger
from app.integrations import MockDataBridge
from app.integrations import MockFeedbackBridge


class FlakyLockDataBridge(MockDataBridge):
    def __init__(self, *, failures_before_success: int) -> None:
        super().__init__()
        self._remaining_failures = failures_before_success

    @asynccontextmanager
    async def lock_intent_for_update(self, intent_id: str, *, timeout: float = 5.0):
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            raise DeadlockError("simulated deadlock", deadlock_info={"intent_id": intent_id})
        async with super().lock_intent_for_update(intent_id, timeout=timeout) as session:
            yield session


class AlwaysDeadlockingDataBridge(MockDataBridge):
    @asynccontextmanager
    async def lock_intent_for_update(self, intent_id: str, *, timeout: float = 5.0):
        raise DeadlockError("permanent deadlock", deadlock_info={"intent_id": intent_id})
        yield  # pragma: no cover


class NoopBridgeSet(BridgeSet):
    async def _execute_pipeline(self, intent: IntentModel, *, mode=None):  # type: ignore[override]
        return intent


@pytest_asyncio.fixture
async def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()


async def _create_intent(data_bridge: MockDataBridge) -> IntentModel:
    intent = IntentModel.new(
        intent_type="deadlock-test",
        payload={"stage": "initial"},
        technical_actor=TechnicalActor.TEST_SUITE,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_execute_with_lock_retries_after_deadlock(audit_logger: MockAuditLogger) -> None:
    data_bridge = FlakyLockDataBridge(failures_before_success=1)
    await data_bridge.connect()

    bridge_set = NoopBridgeSet(
        data=data_bridge,
        ai=MockAIBridge(),
        feedback=MockFeedbackBridge(),
        audit=audit_logger,
    )

    try:
        intent = await _create_intent(data_bridge)
        result = await bridge_set.execute_with_lock(intent.intent_id, initial_intent=intent)

        assert result.intent_id == intent.intent_id
        assert data_bridge._remaining_failures == 0
    finally:
        await data_bridge.disconnect()


@pytest.mark.asyncio
async def test_execute_with_lock_deadlock_max_retries(audit_logger: MockAuditLogger) -> None:
    data_bridge = AlwaysDeadlockingDataBridge()
    await data_bridge.connect()

    bridge_set = NoopBridgeSet(
        data=data_bridge,
        ai=MockAIBridge(),
        feedback=MockFeedbackBridge(),
        audit=audit_logger,
    )

    try:
        intent = await _create_intent(data_bridge)

        with pytest.raises(DeadlockError):
            await bridge_set.execute_with_lock(intent.intent_id, initial_intent=intent)
    finally:
        await data_bridge.disconnect()


@pytest.mark.asyncio
async def test_sorted_lock_order_prevents_deadlock() -> None:
    data_bridge = MockDataBridge()
    await data_bridge.connect()

    intents = [await _create_intent(data_bridge) for _ in range(5)]
    intent_ids = [intent.intent_id for intent in intents]

    @retry_on_deadlock(max_retries=2, base_delay=0.01, jitter=0.0)
    async def update_batch(ids: list[str]) -> None:
        for intent_id in sorted(ids):
            async with data_bridge.lock_intent_for_update(intent_id) as session:
                session.intent.increment_version()

    try:
        tasks = []
        for _ in range(5):
            shuffled = intent_ids[:]
            random.shuffle(shuffled)
            tasks.append(asyncio.create_task(update_batch(shuffled)))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert not any(isinstance(result, DeadlockError) for result in results)
    finally:
        await data_bridge.disconnect()
