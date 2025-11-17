from __future__ import annotations

import json
import time
from typing import List, Optional
from uuid import uuid4

import anyio
import httpx
import pytest

from bridge.api.app import app
from bridge.realtime import EventChannel, get_event_distributor, shutdown_event_distributor
from bridge.realtime.websocket_manager import websocket_manager

CLIENT_COUNT = 25
LATENCY_CLIENTS = 15


@pytest.fixture(autouse=True)
def _in_memory_realtime(monkeypatch):
    monkeypatch.setenv("BRIDGE_RT_IN_MEMORY", "1")
    monkeypatch.delenv("BRIDGE_SKIP_REALTIME_STARTUP", raising=False)
    yield
    anyio.run(websocket_manager.reset)
    anyio.run(shutdown_event_distributor)


async def _read_first_event(stream_response: httpx.Response) -> dict:
    async for line in stream_response.aiter_lines():
        if not line or line.startswith(":"):
            continue
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    raise AssertionError("SSE stream closed without data event")


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_sse_intent_stream_handles_multiple_clients():
    intent_id = str(uuid4())
    transport = httpx.ASGITransport(app=app)

    async def _subscribe(client: httpx.AsyncClient, slot: int, results: List[Optional[dict]]) -> None:
        async with client.stream("GET", f"/events/intents/{intent_id}?close_after=1") as response:
            results[slot] = await _read_first_event(response)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        results: List[Optional[dict]] = [None] * CLIENT_COUNT

        async with anyio.create_task_group() as tg:
            for idx in range(CLIENT_COUNT):
                tg.start_soon(_subscribe, client, idx, results)

            async def publish_event() -> None:
                await anyio.sleep(0.2)
                distributor = await get_event_distributor()
                await distributor.publish(
                    EventChannel.INTENT_CHANGED,
                    {"intent_id": intent_id, "status": "completed"},
                )

            tg.start_soon(publish_event)

        assert all(result is not None for result in results)
        assert {payload["status"] for payload in results if payload} == {"completed"}


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_sse_audit_log_latency_under_load():
    transport = httpx.ASGITransport(app=app)
    payload = {"log_id": 7, "intent_id": str(uuid4()), "actor": "system"}

    latencies: list[float] = []

    async def _subscribe(client: httpx.AsyncClient) -> None:
        async with client.stream("GET", "/events/audit-logs?close_after=1") as response:
            await _read_first_event(response)
            latencies.append(time.perf_counter() - start)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with anyio.create_task_group() as tg:
            for _ in range(LATENCY_CLIENTS):
                tg.start_soon(_subscribe, client)

            async def publish_event() -> None:
                await anyio.sleep(0.2)
                nonlocal start
                start = time.perf_counter()
                distributor = await get_event_distributor()
                await distributor.publish(EventChannel.AUDIT_LOG_CREATED, payload)

            start = 0.0
            tg.start_soon(publish_event)

    assert latencies, "No SSE clients recorded latency"
    avg_latency = sum(latencies) / len(latencies)
    p95_index = max(0, int(len(latencies) * 0.95) - 1)
    p95_latency = sorted(latencies)[p95_index]

    assert avg_latency < 0.5, f"avg latency {avg_latency:.3f}s exceeds 0.5s budget"
    assert p95_latency < 1.0, f"p95 latency {p95_latency:.3f}s exceeds 1.0s budget"
