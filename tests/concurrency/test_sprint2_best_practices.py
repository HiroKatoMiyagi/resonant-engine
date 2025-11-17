import asyncio
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio

from bridge.core.constants import IntentStatusEnum, TechnicalActor
from bridge.core.exceptions import InvalidStatusError
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
        intent_type="best-practice",
        payload={"status": status.value},
        technical_actor=TechnicalActor.TEST_SUITE,
        status=status,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_best_practice_lock_before_validation(data_bridge: MockDataBridge) -> None:
    intent = await _create_intent(data_bridge)

    async def stale_validation(intent_id: str) -> None:
        snapshot = await data_bridge.get_intent(intent_id)
        IntentModel.validate_status_transition(snapshot.status, IntentStatusEnum.PROCESSED)
        await asyncio.sleep(0.05)
        await data_bridge.update_intent_status(intent_id, IntentStatusEnum.PROCESSED)

    async def fast_completion(intent_id: str) -> None:
        await asyncio.sleep(0.01)
        await data_bridge.update_intent_status(intent_id, IntentStatusEnum.NORMALIZED)
        await data_bridge.update_intent_status(intent_id, IntentStatusEnum.COMPLETED)

    with pytest.raises(InvalidStatusError):
        await asyncio.gather(stale_validation(intent.intent_id), fast_completion(intent.intent_id))

    locked_intent = await _create_intent(data_bridge)
    await data_bridge.update_intent_status(locked_intent.intent_id, IntentStatusEnum.NORMALIZED)
    await data_bridge.update_intent_status(locked_intent.intent_id, IntentStatusEnum.COMPLETED)

    async def lock_before_validation(intent_id: str) -> bool:
        async with data_bridge.lock_intent_for_update(intent_id) as session:
            try:
                IntentModel.validate_status_transition(session.intent.status, IntentStatusEnum.PROCESSED)
            except InvalidStatusError:
                return False
            updated = session.intent.with_updates(status=IntentStatusEnum.PROCESSED)
            updated.increment_version()
            session.replace(updated)
            return True

    result = await lock_before_validation(locked_intent.intent_id)
    assert result is False
    final = await data_bridge.get_intent(locked_intent.intent_id)
    assert final.status == IntentStatusEnum.COMPLETED


@pytest.mark.asyncio
async def test_best_practice_idempotent_correction(data_bridge: MockDataBridge) -> None:
    intent = await _create_intent(data_bridge)
    correction_id = str(uuid4())

    first = await data_bridge.save_correction(
        intent.intent_id,
        {
            "correction_id": correction_id,
            "status": IntentStatusEnum.CORRECTED.value,
            "diff": {"payload": {"note": "initial"}},
        },
    )
    second = await data_bridge.save_correction(
        intent.intent_id,
        {
            "correction_id": correction_id,
            "status": IntentStatusEnum.CORRECTED.value,
            "diff": {"payload": {"note": "initial"}},
        },
    )

    assert len(first.correction_history) == 1
    assert len(second.correction_history) == 1
    assert second.version == first.version
    persisted = await data_bridge.get_intent(intent.intent_id)
    assert str(persisted.correction_history[-1].correction_id) == correction_id
    assert persisted.version == first.version
