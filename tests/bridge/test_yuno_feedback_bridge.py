import json
from types import SimpleNamespace

import pytest

from bridge.providers.feedback.yuno_feedback_bridge import YunoFeedbackBridge


class FakeChatCompletions:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def create(self, *args, **kwargs):  # noqa: D401 - pytest fixture
        content = json.dumps(self.payload)
        choice = SimpleNamespace(message={"content": content})
        return SimpleNamespace(choices=[choice])


class FakeChat:
    def __init__(self, payload: dict) -> None:
        self.completions = FakeChatCompletions(payload)


class FakeClient:
    def __init__(self, payload: dict) -> None:
        self.chat = FakeChat(payload)


@pytest.mark.asyncio
async def test_yuno_feedback_bridge_parses_response() -> None:
    payload = {
        "judgment": "approved",
        "evaluation_score": 0.93,
        "criteria": {
            "intent_alignment": 0.95,
            "code_quality": 0.9,
            "test_coverage": 0.92,
            "documentation": 0.94,
        },
        "reason": "Intent meets expectations.",
        "suggestions": ["Add more docstrings"],
    }
    bridge = YunoFeedbackBridge(client=FakeClient(payload))

    intent = {
        "id": "intent-123",
        "type": "review",
        "payload": {"target": "module.py"},
    }

    result = await bridge.request_reevaluation(intent)
    assert result["status"] == "ok"
    assert result["judgment"] == "approved"
    assert result["evaluation_score"] == pytest.approx(0.93)
    assert result["criteria"]["code_quality"] == pytest.approx(0.9)
    assert result["reason"] == "Intent meets expectations."
    assert "reevaluated_at" in result

    correction = await bridge.generate_correction(intent, feedback_history=[{"note": "fine"}])
    assert correction["recommended_changes"][0]["priority"] == "medium"
    assert correction["confidence"] == pytest.approx(0.93)


@pytest.mark.asyncio
async def test_yuno_feedback_bridge_handles_invalid_json() -> None:
    class BadCompletions:
        async def create(self, *args, **kwargs):
            choice = SimpleNamespace(message={"content": "not-json"})
            return SimpleNamespace(choices=[choice])

    class BadClient:
        def __init__(self) -> None:
            self.chat = SimpleNamespace(completions=BadCompletions())

    bridge = YunoFeedbackBridge(client=BadClient())

    intent = {"id": "intent", "type": "review", "payload": {}}
    result = await bridge.request_reevaluation(intent)
    assert result["status"] == "error"
