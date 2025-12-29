"""WebSocket connection management for real-time intent updates."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional, Set

from fastapi import WebSocket

from .event_distributor import Event

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Track WebSocket connections and broadcast intent events."""

    def __init__(self) -> None:
        self._intent_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._wildcard_subscribers: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, intent_ids: Optional[Set[str]]) -> None:
        await websocket.accept()
        async with self._lock:
            if intent_ids:
                for intent_id in intent_ids:
                    self._intent_subscriptions.setdefault(intent_id, set()).add(websocket)
            else:
                self._wildcard_subscribers.add(websocket)
        logger.debug("WebSocket %s connected with intents=%s", id(websocket), intent_ids or "*")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            for subscribers in self._intent_subscriptions.values():
                subscribers.discard(websocket)
            self._wildcard_subscribers.discard(websocket)
            # Clean up empty keys
            self._intent_subscriptions = {
                k: v for k, v in self._intent_subscriptions.items() if v
            }
        await websocket.close()
        logger.debug("WebSocket %s disconnected", id(websocket))

    async def update_subscriptions(
        self,
        websocket: WebSocket,
        *,
        add: Optional[Set[str]] = None,
        remove: Optional[Set[str]] = None,
    ) -> None:
        async with self._lock:
            if add:
                for intent_id in add:
                    self._intent_subscriptions.setdefault(intent_id, set()).add(websocket)
                    self._wildcard_subscribers.discard(websocket)
            if remove:
                for intent_id in remove:
                    subscribers = self._intent_subscriptions.get(intent_id)
                    if subscribers:
                        subscribers.discard(websocket)
                        if not subscribers:
                            self._intent_subscriptions.pop(intent_id, None)

    async def broadcast_intent_event(self, event: Event) -> None:
        intent_id = event.payload.get("intent_id")
        async with self._lock:
            recipients: Set[WebSocket] = set(self._wildcard_subscribers)
            if intent_id and intent_id in self._intent_subscriptions:
                recipients.update(self._intent_subscriptions[intent_id])
        if not recipients:
            return
        disconnected: Set[WebSocket] = set()
        for websocket in recipients:
            try:
                await websocket.send_json(
                    {
                        "type": "intent_update",
                        "data": event.payload,
                        "timestamp": event.timestamp.isoformat(),
                    }
                )
            except Exception:  # pragma: no cover - logged for observability
                logger.exception("Failed to send real-time update; dropping connection")
                disconnected.add(websocket)
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self._wildcard_subscribers.discard(ws)
                    for subscribers in self._intent_subscriptions.values():
                        subscribers.discard(ws)
                self._intent_subscriptions = {
                    k: v for k, v in self._intent_subscriptions.items() if v
                }

    async def send_pong(self, websocket: WebSocket) -> None:
        await websocket.send_json({"type": "pong"})

    async def reset(self) -> None:
        """Clear all connections (used by tests)."""

        async with self._lock:
            self._intent_subscriptions.clear()
            self._wildcard_subscribers.clear()

    async def active_connection_count(self) -> int:
        """Return the total number of unique active WebSocket connections."""

        async with self._lock:
            unique: Set[WebSocket] = set(self._wildcard_subscribers)
            for subscribers in self._intent_subscriptions.values():
                unique.update(subscribers)
            return len(unique)


websocket_manager = WebSocketManager()
