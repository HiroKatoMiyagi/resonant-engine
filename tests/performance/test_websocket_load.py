import statistics
import time
from datetime import datetime, timezone
from typing import List, Tuple
from uuid import uuid4

import anyio
import pytest
from fastapi.testclient import TestClient

from bridge.api.app import app
from bridge.realtime import Event, EventChannel, shutdown_event_distributor
from bridge.realtime.websocket_manager import websocket_manager

LOAD_CONNECTIONS = 100
LATENCY_CONNECTIONS = 50
TEST_ITERATIONS = 5


def _broadcast_intent(intent_id: str, status: str = "processed") -> None:
    async def _broadcast() -> None:
        event = Event(
            channel=EventChannel.INTENT_CHANGED,
            payload={"intent_id": intent_id, "status": status},
            timestamp=datetime.now(timezone.utc),
        )
        await websocket_manager.broadcast_intent_event(event)

    anyio.run(_broadcast)


@pytest.fixture(autouse=True)
def _in_memory_realtime(monkeypatch):
    monkeypatch.setenv("BRIDGE_RT_IN_MEMORY", "1")
    monkeypatch.delenv("BRIDGE_SKIP_REALTIME_STARTUP", raising=False)
    yield
    anyio.run(websocket_manager.reset)
    anyio.run(shutdown_event_distributor)


def _open_connections(client: TestClient, count: int) -> List[Tuple]:
    sockets: List[Tuple] = []
    for _ in range(count):
        context = client.websocket_connect("/ws/intents")
        websocket = context.__enter__()
        sockets.append((context, websocket))
    return sockets


def _close_connections(sockets: List[Tuple]) -> None:
    for context, _ in sockets:
        try:
            context.__exit__(None, None, None)
        except RuntimeError:
            # socket may already be closed if the test failed early
            pass


@pytest.mark.slow
def test_websocket_handles_hundred_connections():
    """Ensure websocket layer can sustain >=100 active listeners."""
    elapsed = None
    with TestClient(app) as client:
        sockets = _open_connections(client, LOAD_CONNECTIONS)
        intent_id = str(uuid4())
        try:
            start = time.perf_counter()
            _broadcast_intent(intent_id)
            for _, socket in sockets:
                message = socket.receive_json()
                assert message["data"]["intent_id"] == intent_id
            elapsed = time.perf_counter() - start
        finally:
            _close_connections(sockets)

    assert elapsed is not None
    # Expect broadcast fan-out to complete comfortably within a reasonable budget.
    assert elapsed < 1.5, f"fan-out took {elapsed:.2f}s (>1.5s budget)"


@pytest.mark.slow
def test_websocket_latency_under_load():
    """Measure average and p95 latency for a hot path connection."""
    with TestClient(app) as client:
        sockets = _open_connections(client, LATENCY_CONNECTIONS)
        latencies = []
        try:
            for _ in range(TEST_ITERATIONS):
                intent_id = str(uuid4())
                start = time.perf_counter()
                _broadcast_intent(intent_id, status="completed")
                primary_msg = sockets[0][1].receive_json()
                assert primary_msg["data"]["intent_id"] == intent_id
                elapsed = time.perf_counter() - start
                latencies.append(elapsed)

                # Drain remaining sockets to keep buffer sizes bounded
                for _, socket in sockets[1:]:
                    payload = socket.receive_json()
                    assert payload["data"]["intent_id"] == intent_id
        finally:
            _close_connections(sockets)

    avg_latency = statistics.mean(latencies)
    p95_latency = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]

    assert avg_latency < 0.5, f"avg latency {avg_latency:.3f}s exceeds 0.5s budget"
    assert p95_latency < 1.0, f"p95 latency {p95_latency:.3f}s exceeds 1.0s budget"
