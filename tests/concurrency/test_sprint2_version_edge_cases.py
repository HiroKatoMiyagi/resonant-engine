import asyncio
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio

from app.services.shared.constants import IntentStatusEnum, TechnicalActor
from app.models.intent import IntentModel
from app.integrations import MockDataBridge


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
        intent_type="version-edge",
        payload={"status": status.value},
        technical_actor=TechnicalActor.TEST_SUITE,
        status=status,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_version_increment_on_correction(data_bridge: MockDataBridge) -> None:
    intent = await _create_intent(data_bridge)
    before_version = intent.version
    correction_id = str(uuid4())

    updated = await data_bridge.save_correction(
        intent.intent_id,
        {
            "correction_id": correction_id,
            "status": IntentStatusEnum.CORRECTED.value,
            "diff": {"payload": {"confidence": 0.42}},
        },
    )

    assert updated.version == before_version + 1
    assert str(updated.correction_history[-1].correction_id) == correction_id
    persisted = await data_bridge.get_intent(intent.intent_id)
    assert persisted.version == updated.version
    assert persisted.correction_history[-1].diff["payload"]["confidence"] == 0.42


@pytest.mark.asyncio
async def test_version_mismatch_returns_false(data_bridge: MockDataBridge) -> None:
    intent = await _create_intent(data_bridge)
    stale_copy = intent.with_updates(status=IntentStatusEnum.NORMALIZED)
    stale_copy.increment_version()

    updated = await data_bridge.update_intent_if_version_matches(
        intent.intent_id,
        stale_copy,
        expected_version=intent.version + 1,
    )

    assert updated is False
    persisted = await data_bridge.get_intent(intent.intent_id)
    assert persisted.version == intent.version
    assert persisted.status == intent.status
