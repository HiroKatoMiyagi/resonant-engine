import pytest
from fastapi import HTTPException, status
from uuid import uuid4

from bridge.api.reeval import reeval_intent
from bridge.core.constants import IntentStatusEnum, PhilosophicalActor, TechnicalActor
from bridge.core.models.intent_model import IntentModel
from bridge.core.models.reeval import ReEvaluationRequest
from bridge.providers.audit import MockAuditLogger
from bridge.providers.data import MockDataBridge


async def _persist_intent(data_bridge: MockDataBridge, payload: dict, *, status: IntentStatusEnum | None = None) -> IntentModel:
    intent = IntentModel.new(
        intent_type="review",
        payload=payload,
        technical_actor=TechnicalActor.DAEMON,
        status=status,
    )
    return await data_bridge.save_intent(intent)


@pytest.mark.asyncio
async def test_reeval_simple_field_update(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    persisted = await _persist_intent(data_bridge, {"status_message": "original"})

    request = ReEvaluationRequest(
        intent_id=persisted.id,
        diff={"payload": {"status_message": "updated"}},
        source=PhilosophicalActor.YUNO,
        reason="Status alignment",
    )

    response = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert response.status == IntentStatusEnum.CORRECTED
    assert response.already_applied is False
    updated = await data_bridge.get_intent(persisted.intent_id)
    assert updated.payload["status_message"] == "updated"
    assert len(updated.correction_history) == 1
    assert audit_logger.entries[-1]["event"] == "reevaluated"


@pytest.mark.asyncio
async def test_reeval_nested_field_update(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    persisted = await _persist_intent(data_bridge, {"config": {"timeout": 10, "retries": 3}})

    request = ReEvaluationRequest(
        intent_id=persisted.id,
        diff={"payload": {"config.timeout": 30}},
        source=PhilosophicalActor.KANA,
        reason="Timeout adjustment",
    )

    response = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert response.status == IntentStatusEnum.CORRECTED
    updated = await data_bridge.get_intent(persisted.intent_id)
    assert updated.payload["config"]["timeout"] == 30
    assert updated.payload["config"]["retries"] == 3


@pytest.mark.asyncio
async def test_reeval_multiple_fields_update(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    persisted = await _persist_intent(
        data_bridge,
        {"priority": "low", "assigned_to": None, "tags": []},
    )

    request = ReEvaluationRequest(
        intent_id=persisted.id,
        diff={"payload": {
            "priority": "high",
            "assigned_to": "KANA",
            "tags": ["urgent", "reviewed"],
        }},
        source=PhilosophicalActor.YUNO,
        reason="Priority escalation",
        metadata={"ticket": "OPS-42"},
    )

    response = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert response.correction_count == 1
    updated = await data_bridge.get_intent(persisted.intent_id)
    assert updated.payload["priority"] == "high"
    assert updated.payload["assigned_to"] == "KANA"
    assert updated.payload["tags"] == ["urgent", "reviewed"]
    assert updated.corrections[0]["metadata"]["ticket"] == "OPS-42"


@pytest.mark.asyncio
async def test_reeval_idempotency_same_diff(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    persisted = await _persist_intent(data_bridge, {"state": "draft"})

    request = ReEvaluationRequest(
        intent_id=persisted.id,
        diff={"payload": {"state": "corrected"}},
        source=PhilosophicalActor.YUNO,
        reason="Initial correction",
    )

    first = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)
    second = await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert first.already_applied is False
    assert second.already_applied is True
    assert first.correction_id == second.correction_id
    updated = await data_bridge.get_intent(persisted.intent_id)
    assert len(updated.correction_history) == 1
    assert audit_logger.entries[-1]["details"]["already_applied"] is True


@pytest.mark.asyncio
async def test_reeval_intent_not_found(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    request = ReEvaluationRequest(
        intent_id=uuid4(),
        diff={"payload": {"status": "corrected"}},
        source=PhilosophicalActor.YUNO,
        reason="Missing intent",
    )

    with pytest.raises(HTTPException) as exc:
        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_reeval_invalid_status(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    persisted = await _persist_intent(
        data_bridge,
        {"summary": "completed task"},
        status=IntentStatusEnum.COMPLETED,
    )

    request = ReEvaluationRequest(
        intent_id=persisted.id,
        diff={"payload": {"summary": "updated"}},
        source=PhilosophicalActor.KANA,
        reason="Attempt to correct completed intent",
    )

    with pytest.raises(HTTPException) as exc:
        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert exc.value.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_reeval_unauthorized_source(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    persisted = await _persist_intent(data_bridge, {"note": "requires approval"})

    request = ReEvaluationRequest(
        intent_id=persisted.id,
        diff={"payload": {"note": "modified"}},
        source=PhilosophicalActor.TSUMU,
        reason="Unauthorized actor",
    )

    with pytest.raises(HTTPException) as exc:
        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_reeval_invalid_diff_rejected(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    persisted = await _persist_intent(data_bridge, {"count": 10})

    request = ReEvaluationRequest(
        intent_id=persisted.id,
        diff={"payload": {"count": "+5"}},
        source=PhilosophicalActor.YUNO,
        reason="Invalid diff",
    )

    with pytest.raises(HTTPException) as exc:
        await reeval_intent(request, data_bridge=data_bridge, audit_logger=audit_logger)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail["error_code"] == "INVALID_DIFF"
