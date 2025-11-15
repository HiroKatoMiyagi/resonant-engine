import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from bridge.core.constants import IntentStatusEnum, TechnicalActor
from bridge.core.models.intent_model import IntentModel
from bridge.core.reeval_client import ReEvalClient
from bridge.providers.audit import MockAuditLogger
from bridge.providers.data import MockDataBridge
from bridge.providers.feedback.yuno_feedback_bridge import YunoFeedbackBridge


class FakeChatCompletions:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def create(self, *args, **kwargs):
        content = json.dumps(self.payload)
        choice = SimpleNamespace(message={"content": content})
        return SimpleNamespace(choices=[choice])


class FakeChat:
    def __init__(self, payload: dict) -> None:
        self.completions = FakeChatCompletions(payload)


class FakeOpenAI:
    def __init__(self, payload: dict) -> None:
        self.chat = FakeChat(payload)


class ErrorChatCompletions:
    async def create(self, *args, **kwargs):
        raise RuntimeError("yuno-offline")


class ErrorChat:
    def __init__(self) -> None:
        self.completions = ErrorChatCompletions()


class ErrorOpenAI:
    def __init__(self) -> None:
        self.chat = ErrorChat()


@pytest.mark.asyncio
async def test_sprint1_5_yuno_execute_applies_correction() -> None:
    data_bridge = MockDataBridge()
    await data_bridge.connect()
    audit_logger = MockAuditLogger()

    intent = IntentModel.new(
        intent_type="code_review",
        payload={"status": "received", "feedback": {}},
        technical_actor=TechnicalActor.DAEMON,
    )
    persisted = await data_bridge.save_intent(intent)

    evaluation_payload = {
        "status": "ok",
        "judgment": "requires_changes",
        "evaluation_score": 0.82,
        "reason": "Add missing tests",
        "suggestions": ["Add integration test for feedback stage"],
        "issues": ["test_coverage"],
        "root_causes": [],
        "alternatives": [],
        "criteria": {
            "intent_alignment": 0.9,
            "code_quality": 0.75,
            "test_coverage": 0.6,
            "documentation": 0.8,
        },
    }

    reeval_client = ReEvalClient(data_bridge, audit_logger)
    bridge = YunoFeedbackBridge(client=FakeOpenAI(evaluation_payload), reeval_client=reeval_client)

    updated = await bridge.execute(persisted)

    assert updated.status == IntentStatusEnum.CORRECTED
    stored = await data_bridge.get_intent(persisted.intent_id)
    feedback_block = stored.payload["feedback"]["yuno"]
    assert feedback_block["reason"] == "Add missing tests"
    assert feedback_block["recommended_changes"][0]["description"].startswith("Add integration test")
    latest = feedback_block["latest"]
    assert latest["judgment"] == "requires_changes"
    assert latest["evaluation_score"] == pytest.approx(0.82, abs=1e-6)
    assert stored.correction_history[-1].diff["payload"]["feedback.yuno.reason"] == "Add missing tests"


@pytest.mark.asyncio
async def test_sprint1_5_yuno_execute_skips_on_error() -> None:
    data_bridge = MockDataBridge()
    await data_bridge.connect()
    audit_logger = MockAuditLogger()

    intent = IntentModel.new(
        intent_type="code_review",
        payload={"status": "received"},
        technical_actor=TechnicalActor.DAEMON,
    )
    persisted = await data_bridge.save_intent(intent)

    error_payload = {"status": "error", "reason": "model-offline"}
    bridge = YunoFeedbackBridge(client=FakeOpenAI(error_payload), reeval_client=ReEvalClient(data_bridge, audit_logger))

    result = await bridge.execute(persisted)
    assert result.status == IntentStatusEnum.RECEIVED
    stored = await data_bridge.get_intent(persisted.intent_id)
    assert stored.status == IntentStatusEnum.RECEIVED
    assert "feedback" not in stored.payload or "yuno" not in stored.payload.get("feedback", {})


def test_sprint1_5_yuno_requires_api_key_when_client_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        YunoFeedbackBridge()


@pytest.mark.asyncio
async def test_sprint1_5_yuno_invoke_handles_exception() -> None:
    bridge = YunoFeedbackBridge(client=ErrorOpenAI())
    result = await bridge._invoke("prompt")
    assert result["status"] == "error"
    assert "yuno-offline" in result["reason"]


def test_sprint1_5_yuno_parse_evaluation_invalid_json() -> None:
    bridge = YunoFeedbackBridge(client=FakeOpenAI({}))
    result = bridge._parse_evaluation("not-json")
    assert result["status"] == "error"
    assert result["reason"] == "invalid-json"


@pytest.mark.asyncio
async def test_sprint1_5_yuno_request_reevaluation_sets_timestamp() -> None:
    payload = {
        "status": "ok",
        "judgment": "approved",
        "evaluation_score": 0.9,
    }
    bridge = YunoFeedbackBridge(client=FakeOpenAI(payload))
    evaluation = await bridge.request_reevaluation({"id": "intent-1", "payload": {}})
    assert evaluation["status"] == "ok"
    # ISO timestamp sanity check
    datetime.fromisoformat(evaluation["reevaluated_at"])


def test_sprint1_5_yuno_build_prompt_with_history() -> None:
    bridge = YunoFeedbackBridge(client=FakeOpenAI({}))
    prompt = bridge._build_prompt(
        {"id": "intent-1", "type": "code_review", "payload": {"foo": "bar"}},
        feedback_history=[{"step": "one"}],
    )
    assert "## Feedback History" in prompt
    assert "## Instructions" in prompt


def test_sprint1_5_yuno_build_correction_defaults() -> None:
    bridge = YunoFeedbackBridge(client=FakeOpenAI({}))
    evaluation = {
        "status": "ok",
        "evaluation_score": 0.55,
        "criteria": {},
        "suggestions": [],
    }
    correction = bridge._build_correction(
        {"id": "intent-1", "payload": {}},
        evaluation,
        feedback_history=[],
    )
    assert correction["recommended_changes"][0]["description"] == "Monitor intent outcome"
    assert correction["diff"]["payload"]["feedback.yuno.reason"] == "Yuno feedback correction"
    assert correction["diff"]["payload"]["feedback.yuno.latest"]["history_count"] == 0


@pytest.mark.asyncio
async def test_sprint1_5_yuno_submit_feedback_structure() -> None:
    bridge = YunoFeedbackBridge(client=FakeOpenAI({}))
    result = await bridge.submit_feedback("intent-1", {"score": 0.8})
    assert result["intent_id"] == "intent-1"
    datetime.fromisoformat(result["recorded_at"])
