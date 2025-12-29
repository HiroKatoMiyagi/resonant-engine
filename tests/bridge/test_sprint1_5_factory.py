import pytest

from app.dependencies import create_bridge_set, create_data_bridge, create_ai_bridge, create_feedback_bridge
from app.services.shared.constants import TechnicalActor
from app.models.intent import IntentModel
from app.services.intent.reeval import ReEvalClient
from app.integrations import MockFeedbackBridge


@pytest.mark.asyncio
async def test_sprint1_5_factory_attaches_reeval_to_mock(monkeypatch):
    bridge_set = BridgeFactory.create_all(
        data_bridge="mock",
        ai_bridge="mock",
        feedback_bridge="mock",
        audit_logger="mock",
    )

    assert isinstance(bridge_set.feedback, MockFeedbackBridge)
    assert isinstance(bridge_set.feedback.reeval_client, ReEvalClient)

    intent = await bridge_set.data.save_intent(
        IntentModel.new(
            intent_type="demo",
            payload={"note": "pending"},
            technical_actor=TechnicalActor.DAEMON,
        )
    )
    # Ensure the attached client shares the same data bridge instance
    fetched = await bridge_set.feedback.reeval_client.get_intent(intent.id)
    assert fetched.intent_id == intent.intent_id


@pytest.mark.asyncio
async def test_sprint1_5_factory_attaches_reeval_to_yuno(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    bridge_set = BridgeFactory.create_all(
        data_bridge="mock",
        ai_bridge="mock",
        feedback_bridge="yuno",
        audit_logger="mock",
    )

    try:
        assert bridge_set.feedback.reeval_client is not None
        assert isinstance(bridge_set.feedback.reeval_client, ReEvalClient)
        # client should reference same data bridge instance
        fetched = await bridge_set.feedback.reeval_client.get_intent(
            (await bridge_set.data.save_intent(
                IntentModel.new(
                    intent_type="demo",
                    payload={"note": "check"},
                    technical_actor=TechnicalActor.DAEMON,
                )
            )).id
        )
        assert fetched.payload["note"] == "check"
    finally:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
