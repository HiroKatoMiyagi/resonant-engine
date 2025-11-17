"""WebSocket endpoints for real-time intent updates."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import List, Optional, Set

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from bridge.realtime import EventChannel, get_event_distributor
from bridge.realtime.websocket_manager import websocket_manager

router = APIRouter()
logger = logging.getLogger(__name__)
_subscription_lock = asyncio.Lock()


async def ensure_websocket_subscription() -> None:
    """Ensure the WebSocket manager is subscribed to INTENT_CHANGED events."""

    async with _subscription_lock:
        distributor = await get_event_distributor()
        distributor.subscribe(EventChannel.INTENT_CHANGED, websocket_manager.broadcast_intent_event)


@router.websocket("/ws/intents")
async def websocket_intents(
    websocket: WebSocket,
    intent_ids: Optional[List[str]] = Query(default=None),
) -> None:
    subscriptions = set(intent_ids) if intent_ids else None
    await websocket_manager.connect(websocket, subscriptions)
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            message_type = data.get("type")
            if message_type == "ping":
                await websocket_manager.send_pong(websocket)
            elif message_type == "subscribe":
                new_ids = data.get("intent_ids") or []
                await websocket_manager.update_subscriptions(websocket, add=set(new_ids))
            elif message_type == "unsubscribe":
                remove_ids = data.get("intent_ids") or []
                await websocket_manager.update_subscriptions(websocket, remove=set(remove_ids))
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception:  # pragma: no cover - log unexpected failures
        logger.exception("Unexpected error in WebSocket handler")
        await websocket_manager.disconnect(websocket)
