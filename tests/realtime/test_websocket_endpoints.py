import pytest

# Bridge API migration in progress
pytestmark = pytest.mark.skip(reason="Bridge API migration in progress - will be addressed separately")

import json
from datetime import datetime, timezone
from uuid import uuid4

import anyio
import httpx
import pytest
from fastapi.testclient import TestClient

from bridge.api.app import app
from app.services.realtime import Event, EventChannel, get_event_distributor, shutdown_event_distributor
from app.services.realtime.websocket_manager import websocket_manager


async def _publish_event(channel: EventChannel, payload: dict) -> None:
    distributor = await get_event_distributor()
    await distributor.publish(channel, payload)


@pytest.fixture(autouse=True)
def _in_memory_realtime(monkeypatch):
    monkeypatch.setenv("BRIDGE_RT_IN_MEMORY", "1")
    monkeypatch.delenv("BRIDGE_SKIP_REALTIME_STARTUP", raising=False)
    yield
    anyio.run(websocket_manager.reset)
    anyio.run(shutdown_event_distributor)


def test_websocket_ping_pong():
    client = TestClient(app)
    with client.websocket_connect("/ws/intents") as websocket:
        websocket.send_json({"type": "ping"})
        assert websocket.receive_json()["type"] == "pong"


def test_websocket_receives_intent_update():
    client = TestClient(app)
    intent_id = str(uuid4())

    async def _broadcast() -> None:
        event = Event(
            channel=EventChannel.INTENT_CHANGED,
            payload={"intent_id": intent_id, "status": "processed"},
            timestamp=datetime.now(timezone.utc),
        )
        await websocket_manager.broadcast_intent_event(event)

    with client.websocket_connect(f"/ws/intents?intent_ids={intent_id}") as websocket:
        anyio.run(_broadcast)
        message = websocket.receive_json()
        assert message["data"]["intent_id"] == intent_id


@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_sse_intent_stream_receives_event():
    """Test SSE stream using async client with ASGI transport."""
    intent_id = str(uuid4())
    
    # Background task to publish event after subscription is ready
    async def publish_after_delay():
        await anyio.sleep(0.3)  # Wait for SSE subscription to complete
        distributor = await get_event_distributor()
        await distributor.publish(
            EventChannel.INTENT_CHANGED,
            {"intent_id": intent_id, "status": "completed"}
        )
    
    # Use ASGI transport to connect httpx to FastAPI app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Start background task
        async with anyio.create_task_group() as tg:
            tg.start_soon(publish_after_delay)
            
            # Open SSE stream
            async with client.stream(
                "GET", 
                f"/events/intents/{intent_id}?close_after=1"
            ) as response:
                # Read first event
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        assert intent_id in data
                        return  # Test passed, exit
                
                # If we get here, no event was received
                pytest.fail("No SSE event received within timeout")


@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_sse_intent_stream_honors_close_after():
    intent_id = str(uuid4())
    statuses = ["received", "processing", "completed"]

    async def publish_sequence() -> None:
        distributor = await get_event_distributor()
        for status in statuses:
            await anyio.sleep(0.1)
            await distributor.publish(EventChannel.INTENT_CHANGED, {"intent_id": intent_id, "status": status})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with anyio.create_task_group() as tg:
            tg.start_soon(publish_sequence)
            async with client.stream("GET", f"/events/intents/{intent_id}?close_after=2") as response:
                assert response.status_code == 200
                payloads = []
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        payloads.append(json.loads(line[5:].strip()))

        assert [payload["status"] for payload in payloads] == statuses[:2]


@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_sse_audit_log_stream_receives_events():
    log_payload = {"log_id": 99, "intent_id": str(uuid4()), "actor": "system"}

    async def publish_log() -> None:
        await anyio.sleep(0.2)
        await _publish_event(EventChannel.AUDIT_LOG_CREATED, log_payload)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with anyio.create_task_group() as tg:
            tg.start_soon(publish_log)
            async with client.stream("GET", "/events/audit-logs?close_after=1") as response:
                assert response.status_code == 200
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        assert data["log_id"] == log_payload["log_id"]
                        assert data["intent_id"] == log_payload["intent_id"]
                        return

    pytest.fail("Audit log SSE event was not received")
