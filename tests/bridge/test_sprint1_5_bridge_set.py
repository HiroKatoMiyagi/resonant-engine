import pytest

from app.services.shared.constants import IntentStatusEnum, TechnicalActor
from app.models.intent import IntentModel
from app.services.intent.reeval import ReEvalClient
from app.services.intent.bridge_set import BridgeSet
from app.integrations import MockAIBridge
from app.integrations import MockAuditLogger
from app.integrations import MockDataBridge
from app.integrations import MockFeedbackBridge


@pytest.mark.asyncio
async def test_sprint1_5_bridge_set_feedback_triggers_reeval() -> None:
    data_bridge = MockDataBridge()
    await data_bridge.connect()
    audit_logger = MockAuditLogger()

    bridge_set = BridgeSet(
        data=data_bridge,
        ai=MockAIBridge(),
        feedback=MockFeedbackBridge(
            judgment="requires_changes",
            correction_diff={"status": "corrected"},
            reeval_client=ReEvalClient(data_bridge, audit_logger),
        ),
        audit=audit_logger,
    )

    intent = IntentModel.new(
        intent_type="demo",
        payload={"status": "received"},
        technical_actor=TechnicalActor.DAEMON,
    )

    result = await bridge_set.execute(intent)

    stored = await data_bridge.get_intent(result.intent_id)
    # Feedback stage should have applied correction before output completion
    assert stored.payload["status"] == "corrected"
    assert stored.status == IntentStatusEnum.COMPLETED
    assert stored.correction_history, "Expected correction history to be populated"
    assert stored.correction_history[-1].diff["payload"]["status"] == "corrected"
