import pytest

from app.services.shared.constants import IntentStatusEnum, TechnicalActor
from app.models.intent import IntentModel
from app.integrations import MockDataBridge
from app.integrations import MockFeedbackBridge


@pytest.mark.asyncio
async def test_mock_data_bridge_round_trip() -> None:
    data_bridge = MockDataBridge()
    await data_bridge.connect()

    payload = {"details": {"target": "test.py"}}
    intent = IntentModel.new(
        intent_type="review",
        payload=payload,
        technical_actor=TechnicalActor.DAEMON,
    )
    persisted = await data_bridge.save_intent(intent)
    fetched = await data_bridge.get_intent(persisted.intent_id)
    assert fetched.payload["details"]["target"] == "test.py"

    correction = {
    "status": IntentStatusEnum.CORRECTED.value,
        "issues": ["Missing regression tests"],
        "recommended_changes": [
            {
                "description": "Add regression tests for bug fix",
                "priority": "high",
            }
        ],
    }
    updated = await data_bridge.save_correction(persisted.intent_id, correction)

    assert updated.status == IntentStatusEnum.CORRECTED
    assert updated.corrections[0]["issues"][0] == "Missing regression tests"

    all_intents = await data_bridge.list_intents()
    assert any(item.intent_id == persisted.intent_id for item in all_intents)

    corrected_only = await data_bridge.list_intents(status=IntentStatusEnum.CORRECTED)
    assert corrected_only[0].intent_id == persisted.intent_id

    await data_bridge.disconnect()


@pytest.mark.asyncio
async def test_mock_feedback_bridge_generate_correction() -> None:
    feedback_bridge = MockFeedbackBridge(judgment="approved_with_notes")
    intent = {"id": "intent-1", "type": "review"}

    reevaluation = await feedback_bridge.request_reevaluation(intent)
    assert reevaluation["judgment"] == "approved_with_notes"

    history = [{"feedback": "Looks good"}]
    correction = await feedback_bridge.generate_correction(intent, history)
    assert correction["recommended_changes"][0]["priority"] == "low"
    assert correction["feedback_history_length"] == 1
