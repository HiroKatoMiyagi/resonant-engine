import asyncio
from typing import Dict

import pytest

from bridge.providers.mock_bridge import MockAIBridge, MockDataBridge, MockFeedbackBridge


@pytest.mark.asyncio
async def test_mock_data_bridge_intent_flow() -> None:
    data_bridge = MockDataBridge()
    await data_bridge.connect()

    intent_id = await data_bridge.save_intent(
        intent_type="review",
        data={"target": "test.py"},
    )
    intent = await data_bridge.get_intent(intent_id)
    assert intent is not None
    assert intent["status"] == "pending"

    await data_bridge.update_intent_status(intent_id, status="processing")
    intent = await data_bridge.get_intent(intent_id)
    assert intent is not None
    assert intent["status"] == "processing"

    feedback_payload: Dict[str, object] = {
        "kana_response": "レビュー完了",
        "processing_time_ms": 1200,
    }
    await data_bridge.save_feedback(intent_id, feedback_payload)

    intent = await data_bridge.get_intent(intent_id)
    assert intent is not None
    assert intent["status"] == "waiting_reevaluation"
    assert intent["feedback"] == feedback_payload

    pending = await data_bridge.get_pending_reevaluations(limit=5)
    assert any(item["id"] == intent_id for item in pending)

    reevaluation_payload: Dict[str, object] = {
        "yuno_judgment": "approved",
        "reason": "OK",
    }
    await data_bridge.save_reevaluation(intent_id, reevaluation_payload)

    await data_bridge.update_reevaluation_status(
        intent_id,
        status="approved",
        judgment="approved",
        reason="OK",
    )

    intent = await data_bridge.get_intent(intent_id)
    assert intent is not None
    assert intent["status"] == "approved"
    assert intent["reevaluation"]["yuno_judgment"] == "approved"

    message_id = await data_bridge.save_message("hello", sender="user", intent_id=intent_id)
    assert message_id

    messages = await data_bridge.get_messages()
    assert len(messages) == 1
    assert messages[0]["intent_id"] == intent_id

    await data_bridge.disconnect()


@pytest.mark.asyncio
async def test_mock_bridges_compose() -> None:
    data_bridge = MockDataBridge()
    ai_bridge = MockAIBridge(static_response="Result")
    feedback_bridge = MockFeedbackBridge()

    await data_bridge.connect()
    intent_type = "review"
    intent_id = await data_bridge.save_intent(intent_type, data={"target": "app.py"})
    prompt = f"Process intent {intent_type}"
    ai_response = await ai_bridge.call_ai(prompt)
    assert ai_response is not None

    feedback = {
        "kana_response": ai_response,
        "processing_time_ms": 1000,
    }
    await data_bridge.save_feedback(intent_id, feedback)

    intent_snapshot = await data_bridge.get_intent(intent_id)
    assert intent_snapshot is not None
    reevaluation = await feedback_bridge.request_reevaluation(
        intent_id,
        intent_snapshot,
        feedback,
    )
    assert reevaluation is not None
    await data_bridge.save_reevaluation(intent_id, reevaluation)

    final_status = (
        "approved"
        if reevaluation["yuno_judgment"] in {"approved", "approved_with_notes"}
        else "rejected"
    )

    await data_bridge.update_reevaluation_status(
        intent_id,
        final_status,
        reevaluation["yuno_judgment"],
        reevaluation["reason"],
    )

    final = await data_bridge.get_intent(intent_id)
    assert final is not None
    assert final["status"] == final_status
    await data_bridge.disconnect()
