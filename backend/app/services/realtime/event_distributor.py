"""Event distribution layer backed by PostgreSQL LISTEN/NOTIFY."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Awaitable, Callable, Dict, Optional, Set

import asyncpg

from .triggers import ensure_realtime_triggers

logger = logging.getLogger(__name__)


class EventChannel(str, Enum):  # type: ignore[misc]
    """Canonical real-time channels shared across Bridge Lite."""

    INTENT_CHANGED = "intent_changed"
    AUDIT_LOG_CREATED = "audit_log_created"
    METRICS_UPDATED = "metrics_updated"


@dataclass(slots=True)
class Event:
    """Lightweight event payload propagated to subscribers."""

    channel: EventChannel
    payload: Dict[str, object]
    timestamp: datetime


Subscriber = Callable[[Event], Awaitable[None] | None]


class EventDistributor:
    """Listen to PostgreSQL notifications and fan them out to subscribers."""

    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._in_memory_only = bool(os.getenv("BRIDGE_RT_IN_MEMORY") == "1")
        if not self._database_url and not self._in_memory_only:
            raise ValueError("database_url is required for EventDistributor")
        self._subscribers: Dict[EventChannel, Set[Subscriber]] = {
            channel: set() for channel in EventChannel
        }
        self._connection: Optional[asyncpg.Connection] = None
        self._running = False
        self._start_lock: Optional[asyncio.Lock] = None

    @property
    def running(self) -> bool:
        return self._running

    async def start(self) -> None:
        if self._start_lock is None:
            self._start_lock = asyncio.Lock()
        async with self._start_lock:
            if self._running:
                return
            if self._in_memory_only:
                self._running = True
                logger.info("Event distributor running in in-memory mode (no PostgreSQL connection)")
                return
            await ensure_realtime_triggers(self._database_url)
            self._connection = await asyncpg.connect(self._database_url)
            for channel in EventChannel:
                await self._connection.add_listener(channel.value, self._handle_notification)
            self._running = True
            logger.info("Event distributor started and listening on %s", list(EventChannel))

    async def stop(self) -> None:
        if not self._running:
            return
        if self._in_memory_only:
            self._running = False
            return
        if self._connection is None:
            self._running = False
            return
        try:
            for channel in EventChannel:
                await self._connection.remove_listener(channel.value, self._handle_notification)
            await self._connection.close()
        finally:
            self._connection = None
            self._running = False
            logger.info("Event distributor stopped")

    def subscribe(self, channel: EventChannel, handler: Subscriber) -> None:
        self._subscribers.setdefault(channel, set()).add(handler)

    def unsubscribe(self, channel: EventChannel, handler: Subscriber) -> None:
        self._subscribers.get(channel, set()).discard(handler)

    async def publish(self, channel: EventChannel, payload: Dict[str, object]) -> None:
        event = Event(channel=channel, payload=payload, timestamp=datetime.now(timezone.utc))
        await self._distribute(event)

    async def _handle_notification(self, connection, pid, channel: str, payload: str) -> None:
        try:
            event_channel = EventChannel(channel)
        except ValueError:
            logger.warning("Received notification for unknown channel: %s", channel)
            return
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON payload on channel %s: %s", channel, exc)
            return
        event = Event(
            channel=event_channel,
            payload=data,
            timestamp=datetime.now(timezone.utc),
        )
        await self._distribute(event)

    async def _distribute(self, event: Event) -> None:
        handlers = list(self._subscribers.get(event.channel, set()))
        if not handlers:
            return
        tasks: list[Awaitable[None]] = []
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    tasks.append(result)
            except Exception:  # pragma: no cover - logged for observability
                logger.exception("Subscriber %s failed for channel %s", handler, event.channel)
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):  # pragma: no cover - defensive logging
                    logger.exception("Async subscriber failed: %s", result)


_event_distributor: Optional[EventDistributor] = None
_event_distributor_lock: Optional[asyncio.Lock] = None


async def get_event_distributor() -> EventDistributor:
    global _event_distributor, _event_distributor_lock
    if _event_distributor and _event_distributor.running:
        return _event_distributor
    if _event_distributor_lock is None:
        _event_distributor_lock = asyncio.Lock()
    async with _event_distributor_lock:
        if _event_distributor and _event_distributor.running:
            return _event_distributor
        database_url = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
        _event_distributor = EventDistributor(database_url)
        await _event_distributor.start()
        return _event_distributor


async def shutdown_event_distributor() -> None:
    global _event_distributor
    if _event_distributor is None:
        return
    await _event_distributor.stop()
    _event_distributor = None
