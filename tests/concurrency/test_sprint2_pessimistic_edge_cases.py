import asyncio
import time
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from bridge.core.constants import IntentStatusEnum, TechnicalActor
from bridge.core.errors import LockTimeoutError
from bridge.core.models.intent_model import IntentModel
from bridge.providers.data import MockDataBridge


@pytest_asyncio.fixture
async def data_bridge() -> AsyncIterator[MockDataBridge]:
    bridge = MockDataBridge()
    await bridge.connect()
    try:
        yield bridge
    finally:
        await bridge.disconnect()


async def _create_intent(
    data_bridge: MockDataBridge,
    *,
    status: IntentStatusEnum = IntentStatusEnum.RECEIVED,
) -> IntentModel:
    intent = IntentModel.new(
        intent_type="pess-lock-test",
        payload={"status": status.value},
        technical_actor=TechnicalActor.TEST_SUITE,
        status=status,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_pessimistic_lock_timeout_configuration(data_bridge: MockDataBridge) -> None:
    intent = await _create_intent(data_bridge)

    async def lock_holder() -> None:
        async with data_bridge.lock_intent_for_update(intent.intent_id, timeout=1.0):
            await asyncio.sleep(0.2)

    holder = asyncio.create_task(lock_holder())
    await asyncio.sleep(0.01)

    short_start = time.perf_counter()
    with pytest.raises(LockTimeoutError):
        async with data_bridge.lock_intent_for_update(intent.intent_id, timeout=0.05):
            pass
    short_elapsed = time.perf_counter() - short_start

    async def long_waiter() -> float:
        long_start = time.perf_counter()
        async with data_bridge.lock_intent_for_update(intent.intent_id, timeout=0.5):
            pass
        return time.perf_counter() - long_start

    long_task = asyncio.create_task(long_waiter())
    await holder
    long_elapsed = await long_task

    assert short_elapsed < 0.2, "Short timeout should fail quickly"
    assert long_elapsed > short_elapsed, "Long timeout should not resolve faster than the short timeout"
    assert long_elapsed >= 0.1, "Long timeout should wait long enough for the initial lock to complete"


@pytest.mark.asyncio
async def test_pessimistic_lock_release_on_exception(data_bridge: MockDataBridge) -> None:
    intent = await _create_intent(data_bridge)

    async def failing_task() -> None:
        async with data_bridge.lock_intent_for_update(intent.intent_id):
            raise RuntimeError("simulated failure inside lock")

    async def follower_task() -> float:
        await asyncio.sleep(0.01)
        follower_start = time.perf_counter()
        async with data_bridge.lock_intent_for_update(intent.intent_id, timeout=0.5):
            pass
        return time.perf_counter() - follower_start

    failing = asyncio.create_task(failing_task())
    follower = asyncio.create_task(follower_task())

    with pytest.raises(RuntimeError):
        await failing

    follower_elapsed = await follower
    assert follower_elapsed < 0.05, "Lock must be released even when exceptions occur"


@pytest.mark.asyncio
async def test_pessimistic_lock_reentrant_behavior(data_bridge: MockDataBridge) -> None:
    intent = await _create_intent(data_bridge)

    async with data_bridge.lock_intent_for_update(intent.intent_id) as session:
        original_version = session.intent.version
        updated = await data_bridge.update_intent_status(intent.intent_id, IntentStatusEnum.NORMALIZED)
        assert updated.version == original_version + 1
        session.replace(updated)

    async with data_bridge.lock_intent_for_update(intent.intent_id):
        pass

    persisted = await data_bridge.get_intent(intent.intent_id)
    assert persisted.version == intent.version + 1
    assert persisted.status == IntentStatusEnum.NORMALIZED
