import asyncio
import math
import time
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from bridge.api.reeval import reeval_intent
from bridge.core.constants import IntentStatusEnum, PhilosophicalActor, TechnicalActor
from bridge.core.models.intent_model import IntentModel
from bridge.core.models.reeval import ReEvaluationRequest
from bridge.providers.audit import MockAuditLogger
from bridge.providers.data import MockDataBridge


@pytest_asyncio.fixture
async def data_bridge() -> AsyncIterator[MockDataBridge]:
    bridge = MockDataBridge()
    await bridge.connect()
    try:
        yield bridge
    finally:
        await bridge.disconnect()


@pytest.fixture
def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()


async def _create_intent(
    data_bridge: MockDataBridge,
    *,
    status: IntentStatusEnum = IntentStatusEnum.RECEIVED,
) -> IntentModel:
    intent = IntentModel.new(
        intent_type="performance-test",
        payload={"status": status.value},
        technical_actor=TechnicalActor.TEST_SUITE,
        status=status,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_status_update_throughput_meets_target(data_bridge: MockDataBridge) -> None:
    intents = [await _create_intent(data_bridge) for _ in range(200)]
    batch_size = 25

    start = time.perf_counter()
    for index in range(0, len(intents), batch_size):
        batch = intents[index : index + batch_size]
        await asyncio.gather(
            *[
                data_bridge.update_intent_status(intent.intent_id, IntentStatusEnum.NORMALIZED)
                for intent in batch
            ]
        )
    duration = time.perf_counter() - start

    throughput = len(intents) / duration
    assert throughput >= 100, f"Throughput {throughput:.1f} < 100 updates/sec"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_reeval_latency_under_contention(
    data_bridge: MockDataBridge,
    audit_logger: MockAuditLogger,
) -> None:
    intent = await _create_intent(data_bridge)

    async def run_reeval(index: int) -> IntentModel:
        request = ReEvaluationRequest(
            intent_id=intent.id,
            diff={"payload": {f"field_{index}": f"value_{index}"}},
            source=PhilosophicalActor.YUNO,
            reason=f"perf-{index}",
        )
        return await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    start = time.perf_counter()
    results = await asyncio.gather(*[run_reeval(i) for i in range(50)])
    duration = time.perf_counter() - start

    assert len(results) == 50
    average_latency = duration / 50
    assert average_latency < 0.2, f"Average latency {average_latency:.3f}s > 200ms"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_lock_acquisition_p95_latency(data_bridge: MockDataBridge) -> None:
    intents = [await _create_intent(data_bridge) for _ in range(100)]
    latencies: list[float] = []

    for intent in intents:
        start = time.perf_counter()
        async with data_bridge.lock_intent_for_update(intent.intent_id):
            pass
        latencies.append(time.perf_counter() - start)

    latencies.sort()
    percentile_index = max(0, math.floor(len(latencies) * 0.95) - 1)
    p95_latency = latencies[percentile_index]

    assert p95_latency < 0.05, f"P95 lock latency {p95_latency * 1000:.1f}ms > 50ms"
