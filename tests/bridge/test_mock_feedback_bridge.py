from types import SimpleNamespace

import pytest

from app.services.shared.constants import IntentStatusEnum
from app.models.intent import IntentModel
from app.models.reeval import ReEvaluationRequest
from app.integrations import MockFeedbackBridge


class FakeReEvalClient:
    def __init__(self, updated_intent: IntentModel) -> None:
        self.requests = []
        self._intent = updated_intent

    async def reeval(self, request: ReEvaluationRequest) -> SimpleNamespace:
        self.requests.append(request)
        return SimpleNamespace(intent_id=request.intent_id, already_applied=False)

    async def get_intent(self, intent_id: str) -> IntentModel:
        assert str(self._intent.id) == intent_id
        return self._intent


@pytest.mark.asyncio
async def test_execute_returns_original_when_no_client() -> None:
    bridge = MockFeedbackBridge()
    intent = IntentModel.new(intent_type="test", payload={"foo": "bar"})

    result = await bridge.execute(intent)

    assert result is intent


@pytest.mark.asyncio
async def test_execute_applies_mock_correction_via_client() -> None:
    original = IntentModel.new(intent_type="test", payload={"foo": "bar"})
    updated = original.with_updates(status=IntentStatusEnum.CORRECTED)

    client = FakeReEvalClient(updated)
    bridge = MockFeedbackBridge(
        judgment="changes requested",
        correction_diff={"status": "corrected"},
        reeval_client=client,
        correction_reason="Adjust status",
    )

    result = await bridge.execute(original)

    assert client.requests, "Re-evaluation should have been triggered"
    request = client.requests[0]
    assert request.intent_id == original.id
    assert request.diff == {"payload": {"status": "corrected"}}
    assert request.reason == "Adjust status"
    assert result.status == IntentStatusEnum.CORRECTED
    assert result is updated
