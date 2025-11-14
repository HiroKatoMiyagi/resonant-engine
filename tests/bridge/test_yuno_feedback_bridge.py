import json
from types import SimpleNamespace

import pytest

from bridge.providers.yuno_feedback_bridge import YunoFeedbackBridge


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

    intent_data = {
        "type": "review",
        "data": {"target": "module.py"},
    }
    feedback_data = {
        "kana_response": "Performed code review",
        "processing_time_ms": 2345,
    }

    result = await bridge.request_reevaluation("intent-123", intent_data, feedback_data)
    assert result is not None
    assert result["yuno_judgment"] == "approved"
    assert result["evaluation_score"] == pytest.approx(0.93)
    assert result["evaluation_criteria"]["code_quality"] == pytest.approx(0.9)
    assert result["reason"] == "Intent meets expectations."
    assert "reevaluated_at" in result


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

    result = await bridge.request_reevaluation(
        "intent",
        {"type": "review", "data": {}},
        {"kana_response": "ok"},
    )
    assert result is None
