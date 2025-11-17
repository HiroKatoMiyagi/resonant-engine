import asyncio
from datetime import datetime, timezone

import pytest

from bridge.realtime.event_distributor import Event, EventChannel, EventDistributor


@pytest.mark.asyncio
async def test_publish_invokes_async_subscribers():
    distributor = EventDistributor("postgresql://example")
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    distributor.subscribe(EventChannel.INTENT_CHANGED, handler)
    await distributor.publish(EventChannel.INTENT_CHANGED, {"intent_id": "abc"})

    assert received
    assert received[0].payload["intent_id"] == "abc"


@pytest.mark.asyncio
async def test_unsubscribe_stops_callbacks():
    distributor = EventDistributor("postgresql://example")
    called = False

    async def handler(event: Event) -> None:  # pragma: no cover - defensive
        nonlocal called
        called = True

    distributor.subscribe(EventChannel.AUDIT_LOG_CREATED, handler)
    distributor.unsubscribe(EventChannel.AUDIT_LOG_CREATED, handler)

    await distributor.publish(EventChannel.AUDIT_LOG_CREATED, {"log_id": 1})
    await asyncio.sleep(0)  # allow async tasks (if any) to run

    assert called is False


@pytest.mark.asyncio
async def test_distribute_handles_sync_handlers():
    distributor = EventDistributor("postgresql://example")
    sink: list[str] = []

    def handler(event: Event) -> None:
        sink.append(event.channel.value)

    distributor.subscribe(EventChannel.METRICS_UPDATED, handler)
    await distributor.publish(EventChannel.METRICS_UPDATED, {"metric": "active"})

    assert sink == [EventChannel.METRICS_UPDATED.value]
