"""WebSocket endpoints for real-time updates."""

import asyncio
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)


class SimpleWebSocketManager:
    """Simple WebSocket connection manager."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_pong(self, websocket: WebSocket):
        await websocket.send_json({"type": "pong"})


manager = SimpleWebSocketManager()


@router.websocket("/ws/intents")
async def websocket_intents(
    websocket: WebSocket,
    intent_ids: Optional[List[str]] = Query(default=None),
):
    """WebSocket endpoint for real-time intent updates."""
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await manager.send_pong(websocket)
            elif message_type == "subscribe":
                # Handle subscription (placeholder)
                logger.debug(f"Subscribe request: {data.get('intent_ids')}")
            elif message_type == "unsubscribe":
                # Handle unsubscription (placeholder)
                logger.debug(f"Unsubscribe request: {data.get('intent_ids')}")
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
