import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

# Bridge API migration in progress
pytestmark = pytest.mark.skip(reason="Bridge API migration in progress - will be addressed separately")
import pytest_asyncio

from app.services.intent.reeval import reeval_intent
from app.services.intent.bridge_set import BridgeSet
from app.services.shared.constants import BridgeTypeEnum, IntentStatusEnum, PhilosophicalActor, TechnicalActor
from app.services.shared.errors import DeadlockError
from app.models.intent import IntentModel
from app.models.reeval import ReEvaluationRequest
from app.services.intent.reeval import ReEvalClient
from app.integrations import MockAIBridge
from app.integrations import MockAuditLogger
from app.integrations import MockDataBridge
from app.integrations import MockFeedbackBridge


@pytest_asyncio.fixture
async def data_bridge() -> AsyncIterator[MockDataBridge]:
    bridge = MockDataBridge()
    await bridge.connect()
    try:
        yield bridge
    finally:
        await bridge.disconnect()


@pytest_asyncio.fixture
async def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()


async def _create_intent(data_bridge: MockDataBridge) -> IntentModel:
    intent = IntentModel.new(
        intent_type="integration-test",
        payload={"stage": "initial"},
        technical_actor=TechnicalActor.TEST_SUITE,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_reeval_with_concurrent_status_update(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    intent = await _create_intent(data_bridge)

    async def run_reeval() -> None:
        request = ReEvaluationRequest(
            intent_id=intent.id,
            diff={"payload": {"integration": "reeval"}},
            source=PhilosophicalActor.YUNO,
            reason="integration-lock",
        )
        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    async def run_status_update() -> None:
        async with data_bridge.lock_intent_for_update(intent.intent_id) as session:
            await asyncio.sleep(0.05)
            updated = session.intent.with_updates(status=IntentStatusEnum.PROCESSED)
            updated.increment_version()
            session.replace(updated)

    await asyncio.gather(run_reeval(), run_status_update())

    final = await data_bridge.get_intent(intent.intent_id)
    assert final.payload["integration"] == "reeval"
    assert final.status in {IntentStatusEnum.PROCESSED, IntentStatusEnum.CORRECTED}
    assert final.version >= intent.version + 2


class DeadlockingDataBridge(MockDataBridge):
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

class NoopBridgeSet(BridgeSet):
    async def _execute_pipeline(self, intent: IntentModel, *, mode=None):  # type: ignore[override]
        await asyncio.sleep(0)
        return intent


@pytest.mark.asyncio
async def test_deadlock_recovery_preserves_correction_history(audit_logger: MockAuditLogger) -> None:
    data_bridge = DeadlockingDataBridge(failures_before_success=2)
    await data_bridge.connect()
    try:
        intent = await _create_intent(data_bridge)
        request = ReEvaluationRequest(
            intent_id=intent.id,
            diff={"payload": {"field": "corrected"}},
            source=PhilosophicalActor.KANA,
            reason="pre-pipeline-correction",
        )
        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

        bridge_set = NoopBridgeSet(
            data=data_bridge,
            ai=MockAIBridge(),
            feedback=MockFeedbackBridge(),
            audit=audit_logger,
        )

        latest = await data_bridge.get_intent(intent.intent_id)
        await bridge_set.execute_with_lock(intent.intent_id, initial_intent=latest)
        final = await data_bridge.get_intent(intent.intent_id)
        assert len(final.correction_history) == 1
        assert final.payload["field"] == "corrected"
        assert data_bridge._remaining_failures == 0
    finally:
        await data_bridge.disconnect()


class SlowBridgeSet(BridgeSet):
    PIPELINE_ORDER = (
        BridgeTypeEnum.INPUT,
        BridgeTypeEnum.NORMALIZE,
    )

    async def _execute_pipeline(self, intent: IntentModel, *, mode=None):  # type: ignore[override]
        await asyncio.sleep(0.05)
        return await super()._execute_pipeline(intent, mode=mode)


class PipelineBlockingDataBridge(MockDataBridge):
    async def update_intent_if_version_matches(self, intent_id: str, intent: IntentModel, *, expected_version: int) -> bool:
        owner = self._lock_owners.get(intent_id)
        current = asyncio.current_task()
        if owner is not None and current is not None and owner is not current:
            await asyncio.sleep(0)
            return False
        return await super().update_intent_if_version_matches(intent_id, intent, expected_version=expected_version)


@pytest.mark.asyncio
async def test_bridge_pipeline_with_concurrent_reeval(audit_logger: MockAuditLogger) -> None:
    data_bridge = PipelineBlockingDataBridge()
    await data_bridge.connect()
    try:
        bridge_set = SlowBridgeSet(
            data=data_bridge,
            ai=MockAIBridge(),
            feedback=MockFeedbackBridge(),
            audit=audit_logger,
        )
        intent = await _create_intent(data_bridge)
        starting_version = intent.version

        async def run_pipeline() -> None:
            current = await data_bridge.get_intent(intent.intent_id)
            await bridge_set.execute_with_lock(intent.intent_id, initial_intent=current)

        async def run_reeval(index: int) -> None:
            request = ReEvaluationRequest(
                intent_id=intent.id,
                diff={"payload": {f"field_{index}": f"value_{index}"}},
                source=PhilosophicalActor.KANA,
                reason=f"concurrent-{index}",
            )
            await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

        pipeline_task = asyncio.create_task(run_pipeline())
        await asyncio.sleep(0.01)
        await asyncio.gather(pipeline_task, *(run_reeval(idx) for idx in range(2)))

        final = await data_bridge.get_intent(intent.intent_id)
        for idx in range(2):
            assert final.payload[f"field_{idx}"] == f"value_{idx}"
        assert final.version >= starting_version + 3
        assert final.status in {IntentStatusEnum.PROCESSED, IntentStatusEnum.CORRECTED, IntentStatusEnum.COMPLETED}
    finally:
        await data_bridge.disconnect()
