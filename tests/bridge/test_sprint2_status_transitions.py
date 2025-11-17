from collections.abc import AsyncIterator

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


async def _persist_intent(
    data_bridge: MockDataBridge,
    *,
    status: IntentStatusEnum,
    technical_actor: TechnicalActor = TechnicalActor.TEST_SUITE,
) -> IntentModel:
    intent = IntentModel.new(
        intent_type="status-transition",
        payload={"test": True},
        status=status,
        technical_actor=technical_actor,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_received_to_normalized_is_valid(data_bridge: MockDataBridge) -> None:
    persisted = await _persist_intent(data_bridge, status=IntentStatusEnum.RECEIVED)

    updated = await data_bridge.update_intent_status(persisted.intent_id, IntentStatusEnum.NORMALIZED)

    assert updated.status == IntentStatusEnum.NORMALIZED
    assert updated.version == persisted.version + 1


@pytest.mark.asyncio
async def test_processed_to_completed_is_valid(data_bridge: MockDataBridge) -> None:
    persisted = await _persist_intent(data_bridge, status=IntentStatusEnum.PROCESSED)

    updated = await data_bridge.update_intent_status(persisted.intent_id, IntentStatusEnum.COMPLETED)

    assert updated.status == IntentStatusEnum.COMPLETED


@pytest.mark.asyncio
async def test_corrected_to_completed_is_valid(data_bridge: MockDataBridge) -> None:
    persisted = await _persist_intent(data_bridge, status=IntentStatusEnum.CORRECTED)

    updated = await data_bridge.update_intent_status(persisted.intent_id, IntentStatusEnum.COMPLETED)

    assert updated.status == IntentStatusEnum.COMPLETED


@pytest.mark.asyncio
async def test_completed_to_anything_else_is_invalid(data_bridge: MockDataBridge) -> None:
    persisted = await _persist_intent(data_bridge, status=IntentStatusEnum.COMPLETED)

    with pytest.raises(InvalidStatusError):
        await data_bridge.update_intent_status(persisted.intent_id, IntentStatusEnum.NORMALIZED)

    stored = await data_bridge.get_intent(persisted.intent_id)
    assert stored.status == IntentStatusEnum.COMPLETED
