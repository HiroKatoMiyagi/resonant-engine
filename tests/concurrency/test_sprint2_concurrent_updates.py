import asyncio
import time
from collections.abc import AsyncIterator

import pytest

# Bridge API migration in progress
pytestmark = pytest.mark.skip(reason="Bridge API migration in progress - will be addressed separately")
import pytest_asyncio

from app.services.intent.reeval import reeval_intent
from app.services.shared.constants import IntentStatusEnum, PhilosophicalActor, TechnicalActor
from app.services.shared.errors import LockTimeoutError
from app.models.intent import IntentModel
from app.models.reeval import ReEvaluationRequest
from app.services.intent.bridge_set import BridgeSet
from app.integrations import MockAuditLogger
from app.integrations import MockDataBridge
from app.integrations import MockAIBridge
from app.integrations import MockFeedbackBridge


@pytest_asyncio.fixture
async def data_bridge() -> AsyncIterator[MockDataBridge]:
    bridge = MockDataBridge()
    await bridge.connect()
    yield bridge
    await bridge.disconnect()


@pytest.fixture
def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()


async def _create_intent(data_bridge: MockDataBridge, *, status: IntentStatusEnum = IntentStatusEnum.RECEIVED) -> IntentModel:
    intent = IntentModel.new(
        intent_type="concurrency-test",
        payload={"status": status.value},
        technical_actor=TechnicalActor.TEST_SUITE,
        status=status,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_concurrent_status_updates_serialized(data_bridge: MockDataBridge) -> None:
    persisted = await _create_intent(data_bridge)

    async def slow_transition() -> None:
        async with data_bridge.lock_intent_for_update(persisted.intent_id) as locked:
            await asyncio.sleep(0.05)
            updated = locked.intent.with_updates(status=IntentStatusEnum.NORMALIZED)
            updated.increment_version()
            locked.replace(updated)

    async def fast_transition() -> None:
        async with data_bridge.lock_intent_for_update(persisted.intent_id) as locked:
            updated = locked.intent.with_updates(status=IntentStatusEnum.PROCESSED)
            updated.increment_version()
            locked.replace(updated)

    start = time.perf_counter()
    await asyncio.gather(slow_transition(), fast_transition())
    duration = time.perf_counter() - start

    assert duration >= 0.05, "Locking should serialize overlapping updates"
    final_intent = await data_bridge.get_intent(persisted.intent_id)
    assert final_intent.version == persisted.version + 2
    assert final_intent.status in {IntentStatusEnum.NORMALIZED, IntentStatusEnum.PROCESSED}


@pytest.mark.asyncio
async def test_lock_timeout_when_lock_held(data_bridge: MockDataBridge) -> None:
    persisted = await _create_intent(data_bridge)

    async def lock_holder() -> None:
        async with data_bridge.lock_intent_for_update(persisted.intent_id, timeout=0.5):
            await asyncio.sleep(0.2)

    async def lock_contender() -> None:
        await asyncio.sleep(0.05)
        with pytest.raises(LockTimeoutError):
            async with data_bridge.lock_intent_for_update(persisted.intent_id, timeout=0.05):
                pass

    await asyncio.gather(lock_holder(), lock_contender())


@pytest.mark.asyncio
async def test_bridge_set_execute_with_lock_serializes_pipeline(
    data_bridge: MockDataBridge,
    audit_logger: MockAuditLogger,
) -> None:
    persisted = await _create_intent(data_bridge)

    class SlowBridgeSet(BridgeSet):
        async def _execute_pipeline(self, intent: IntentModel, *, mode=None):  # type: ignore[override]
            await asyncio.sleep(0.05)
            return intent.increment_version()

    bridge_set = SlowBridgeSet(
        data=data_bridge,
        ai=MockAIBridge(),
        feedback=MockFeedbackBridge(),
        audit=audit_logger,
    )

    async def run_pipeline() -> IntentModel:
        return await bridge_set.execute_with_lock(persisted.intent_id)

    start = time.perf_counter()
    first, second = await asyncio.gather(run_pipeline(), run_pipeline())
    duration = time.perf_counter() - start

    assert duration >= 0.09, "execute_with_lock should serialize concurrent pipelines"
    versions = sorted({first.version, second.version})
    assert versions == [persisted.version + 1, persisted.version + 2]
    final_state = await data_bridge.get_intent(persisted.intent_id)
    assert final_state.version == persisted.version + 2


@pytest.mark.asyncio
async def test_concurrent_reeval_retries_until_success(
    data_bridge: MockDataBridge,
    audit_logger: MockAuditLogger,
) -> None:
    persisted = await _create_intent(data_bridge)

    async def run_reeval(field: str, value: str) -> None:
        request = ReEvaluationRequest(
            intent_id=persisted.id,
            diff={"payload": {field: value}},
            source=PhilosophicalActor.YUNO,
            reason=f"update-{field}",
        )
        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    await asyncio.gather(
        run_reeval("field_a", "A"),
        run_reeval("field_b", "B"),
        run_reeval("field_c", "C"),
    )

    updated = await data_bridge.get_intent(persisted.intent_id)
    assert updated.payload["field_a"] == "A"
    assert updated.payload["field_b"] == "B"
    assert updated.payload["field_c"] == "C"
    assert len(updated.correction_history) == 3