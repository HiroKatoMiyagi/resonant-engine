"""Server-Sent Event endpoints for Bridge Lite real-time updates."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Callable, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from bridge.realtime import Event, EventChannel, get_event_distributor

router = APIRouter()
logger = logging.getLogger(__name__)


async def _event_stream(
    channel: EventChannel,
    *,
    predicate: Callable[[Event], bool],
    close_after: Optional[int] = None,
) -> AsyncIterator[str]:
    queue: asyncio.Queue[Event] = asyncio.Queue()

    async def handler(event: Event) -> None:
        if predicate(event):
            await queue.put(event)

    distributor = await get_event_distributor()
    distributor.subscribe(channel, handler)

    try:
        # Send an initial comment to ensure the HTTP response is flushed immediately.
        yield ":ok\n\n"
        delivered = 0
        while True:
            event = await queue.get()
            payload = json.dumps(event.payload)
            yield f"data: {payload}\n\n"
            delivered += 1
            if close_after is not None and delivered >= close_after:
                break
    finally:
        distributor.unsubscribe(channel, handler)


@router.get("/events/intents/{intent_id}")
async def intent_event_stream(
    intent_id: str,
    close_after: Optional[int] = Query(
        default=None,
        ge=1,
        include_in_schema=False,
        description="Test-only parameter to close the stream after N events.",
    ),
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(
            EventChannel.INTENT_CHANGED,
            predicate=lambda event: event.payload.get("intent_id") == intent_id,
            close_after=close_after,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/events/audit-logs")
async def audit_log_stream(
    close_after: Optional[int] = Query(
        default=None,
        ge=1,
        include_in_schema=False,
        description="Test-only parameter to close the stream after N events.",
    ),
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(
            EventChannel.AUDIT_LOG_CREATED,
            predicate=lambda _event: True,
            close_after=close_after,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
