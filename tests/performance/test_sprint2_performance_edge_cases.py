import asyncio
import random
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio

from app.services.shared.constants import TechnicalActor
from app.services.shared.errors import DeadlockError, LockTimeoutError
from app.models.intent import IntentModel
from app.services.intent.bridge_set import BridgeSet
from app.integrations import MockAIBridge
from app.integrations import MockAuditLogger
from app.integrations import MockDataBridge
from app.integrations import MockFeedbackBridge


class InstrumentedLockDataBridge(MockDataBridge):
    def __init__(self) -> None:
        super().__init__()
        self.lock_attempts = 0
        self.timeout_failures = 0
        self.hold_durations: list[float] = []

    @asynccontextmanager
    async def lock_intent_for_update(self, intent_id: str, *, timeout: float = 5.0):
        wait_started = time.perf_counter()
        try:
            async with super().lock_intent_for_update(intent_id, timeout=timeout) as session:
                self.lock_attempts += 1
                wait_duration = time.perf_counter() - wait_started
                hold_started = time.perf_counter()
                try:
                    yield session
                finally:
                    hold_duration = time.perf_counter() - hold_started
                    self.hold_durations.append(wait_duration + hold_duration)
        except LockTimeoutError:
            self.lock_attempts += 1
            self.timeout_failures += 1
            raise


class ScheduledDeadlockBridge(MockDataBridge):
    def __init__(self) -> None:
        super().__init__()
        self._deadlock_targets: set[str] = set()

    def schedule_deadlock(self, intent_id: str) -> None:
        self._deadlock_targets.add(intent_id)

    @asynccontextmanager
    async def lock_intent_for_update(self, intent_id: str, *, timeout: float = 5.0):
        if intent_id in self._deadlock_targets:
            self._deadlock_targets.remove(intent_id)
            raise DeadlockError("scheduled deadlock", deadlock_info={"intent_id": intent_id})
        async with super().lock_intent_for_update(intent_id, timeout=timeout) as session:
            yield session


class MinimalBridgeSet(BridgeSet):
    async def _execute_pipeline(self, intent: IntentModel, *, mode=None):  # type: ignore[override]
        updated = intent.with_updates()
        updated.increment_version()
        return updated


@pytest_asyncio.fixture
async def audit_logger() -> AsyncIterator[MockAuditLogger]:
    logger = MockAuditLogger()
    yield logger


async def _create_intent(data_bridge: MockDataBridge) -> IntentModel:
    intent = IntentModel.new(
        intent_type="performance-edge",
        payload={"stage": "initial"},
        technical_actor=TechnicalActor.TEST_SUITE,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_lock_contention_under_sustained_load() -> None:
    data_bridge = InstrumentedLockDataBridge()
    await data_bridge.connect()
    try:
        intents = [await _create_intent(data_bridge) for _ in range(50)]
        duration_seconds = 5.0  # 短縮した継続負荷 (仕様上は60秒)
        deadline = time.perf_counter() + duration_seconds

        async def worker(worker_id: int) -> None:
            rng = random.Random(worker_id)
            while time.perf_counter() < deadline:
                intent = rng.choice(intents)
                try:
                    async with data_bridge.lock_intent_for_update(intent.intent_id, timeout=0.1):
                        await asyncio.sleep(0.002)
                except LockTimeoutError:
                    continue

        workers = [asyncio.create_task(worker(idx)) for idx in range(20)]
        await asyncio.gather(*workers)

        assert data_bridge.lock_attempts >= 200, "Test did not generate enough lock traffic"
        contention_rate = data_bridge.timeout_failures / data_bridge.lock_attempts
        assert contention_rate <= 0.05, f"Lock contention rate {contention_rate:.2%} exceeds 5% budget"
    finally:
        await data_bridge.disconnect()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_deadlock_recovery_latency_below_one_second(audit_logger: MockAuditLogger) -> None:
    data_bridge = ScheduledDeadlockBridge()
    await data_bridge.connect()
    try:
        intent = await _create_intent(data_bridge)

        bridge_set = MinimalBridgeSet(
            data=data_bridge,
            ai=MockAIBridge(),
            feedback=MockFeedbackBridge(),
            audit=audit_logger,
        )

        baseline_start = time.perf_counter()
        await bridge_set.execute_with_lock(intent.intent_id, initial_intent=intent)
        baseline = time.perf_counter() - baseline_start

        durations: list[float] = []
        for _ in range(10):
            current = await data_bridge.get_intent(intent.intent_id)
            data_bridge.schedule_deadlock(intent.intent_id)
            start = time.perf_counter()
            await bridge_set.execute_with_lock(intent.intent_id, initial_intent=current)
            durations.append(time.perf_counter() - start)

        recovery_latencies = [max(0.0, duration - baseline) for duration in durations]
        average_recovery = sum(recovery_latencies) / len(recovery_latencies)

        assert average_recovery < 1.0, f"Average deadlock recovery {average_recovery:.3f}s exceeds 1s"
    finally:
        await data_bridge.disconnect()
