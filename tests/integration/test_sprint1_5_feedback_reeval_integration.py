import asyncio
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from bridge.api.reeval import router, get_audit_logger, get_data_bridge
from bridge.core.constants import IntentStatusEnum, PhilosophicalActor, TechnicalActor
from bridge.core.models.intent_model import IntentModel
from bridge.providers.audit import MockAuditLogger
from bridge.providers.data import MockDataBridge


@pytest.fixture()
def sprint1_5_app_client():
    app = FastAPI()
    app.include_router(router)

    data_bridge = MockDataBridge()
    audit_logger = MockAuditLogger()
    asyncio.run(data_bridge.connect())

    async def override_data_bridge():
        return data_bridge

    async def override_audit_logger():
        return audit_logger

    app.dependency_overrides[get_data_bridge] = override_data_bridge
    app.dependency_overrides[get_audit_logger] = override_audit_logger

    with TestClient(app) as client:
        yield client, data_bridge, audit_logger

    app.dependency_overrides.clear()
    if hasattr(get_data_bridge, "_instance"):
        delattr(get_data_bridge, "_instance")
    if hasattr(get_audit_logger, "_instance"):
        delattr(get_audit_logger, "_instance")
    asyncio.run(data_bridge.disconnect())


def _persist_intent(data_bridge: MockDataBridge, **payload):
    intent = IntentModel.new(
        intent_type="demo",
        payload=payload,
        technical_actor=TechnicalActor.DAEMON,
    )
    return asyncio.run(data_bridge.save_intent(intent))


def test_sprint1_5_http_reeval_success(sprint1_5_app_client):
    client, data_bridge, _ = sprint1_5_app_client
    persisted = _persist_intent(data_bridge, status="received", feedback={})

    response = client.post(
        "/api/v1/intent/reeval",
        json={
            "intent_id": str(persisted.id),
            "diff": {"payload": {"feedback.notes": "added by http test"}},
            "source": PhilosophicalActor.YUNO.value,
            "reason": "Sprint1.5 HTTP integration",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == IntentStatusEnum.CORRECTED.value
    assert body["already_applied"] is False

    refreshed = asyncio.run(data_bridge.get_intent(persisted.intent_id))
    assert refreshed.payload["feedback"]["notes"] == "added by http test"


def test_sprint1_5_http_reeval_idempotent(sprint1_5_app_client):
    client, data_bridge, _ = sprint1_5_app_client
    persisted = _persist_intent(data_bridge, status="processed")

    payload = {
        "intent_id": str(persisted.id),
        "diff": {"payload": {"status": "corrected"}},
        "source": PhilosophicalActor.KANA.value,
        "reason": "Idempotent check",
    }

    first = client.post("/api/v1/intent/reeval", json=payload)
    second = client.post("/api/v1/intent/reeval", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["already_applied"] is False
    assert second.json()["already_applied"] is True


def test_sprint1_5_http_reeval_invalid_diff(sprint1_5_app_client):
    client, _, __ = sprint1_5_app_client

    response = client.post(
        "/api/v1/intent/reeval",
        json={
            "intent_id": str(uuid4()),
            "diff": {"payload": {"count": "+5"}},
            "source": PhilosophicalActor.YUNO.value,
            "reason": "Invalid diff should fail",
        },
    )

    assert response.status_code in {400, 404}
    body = response.json()
    detail = body.get("detail", {})
    if response.status_code == 404:
        assert detail.get("error_code") == "INTENT_NOT_FOUND"
    else:
        assert detail.get("error_code") == "INVALID_DIFF"
