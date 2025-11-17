"""Audit log ETL pipeline definitions for Bridge Lite Sprint 3."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping, MutableMapping, Optional, Sequence

import asyncpg

from bridge.realtime import Event, EventChannel, get_event_distributor

logger = logging.getLogger(__name__)

INSERT_AUDIT_LOG_TS = """
INSERT INTO audit_logs_ts (
    time,
    log_id,
    event_type,
    intent_id,
    actor,
    bridge_type,
    status_from,
    status_to,
    payload,
    duration_ms,
    success
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
"""

SELECT_AUDIT_LOG_SQL = """
SELECT id, event_type, intent_id, actor, payload, created_at
FROM audit_logs
WHERE id = $1
"""

AuditLogPoolFactory = Callable[[], Awaitable[asyncpg.Pool]]


@dataclass(slots=True)
class AuditLogETLConfig:
    """Configuration required to run the audit log ETL."""

    source_db_url: str
    target_db_url: str
    batch_size: int = 100
    interval_seconds: float = 5.0


class AuditLogETL:
    """Polling-based ETL that moves audit logs into TimescaleDB."""

    def __init__(
        self,
        config: AuditLogETLConfig,
        *,
        source_pool_factory: AuditLogPoolFactory | None = None,
        target_pool_factory: AuditLogPoolFactory | None = None,
    ) -> None:
        self.config = config
        self.last_processed_id: Optional[int] = None
        self._source_pool_factory = source_pool_factory or (lambda: asyncpg.create_pool(config.source_db_url))
        self._target_pool_factory = target_pool_factory or (lambda: asyncpg.create_pool(config.target_db_url))
        self._source_pool: asyncpg.Pool | None = None
        self._target_pool: asyncpg.Pool | None = None
        self._running = False

    async def start(self, *, stop_event: asyncio.Event | None = None) -> None:
        """Begin the continuous ETL loop.

        The optional ``stop_event`` allows graceful termination in tests.
        """

        if self._running:
            logger.debug("AuditLogETL already running; ignoring start request")
            return

        self._running = True
        try:
            while True:
                processed = await self.process_once()
                if processed:
                    logger.info("AuditLogETL processed %s audit logs", processed)

                if stop_event is not None:
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=self.config.interval_seconds)
                        break
                    except asyncio.TimeoutError:
                        continue

                await asyncio.sleep(self.config.interval_seconds)
        finally:
            await self.close()
            self._running = False

    async def process_once(self) -> int:
        """Process a single ETL batch and return the number of rows handled."""

        if self._source_pool is None:
            self._source_pool = await self._source_pool_factory()
        if self._target_pool is None:
            self._target_pool = await self._target_pool_factory()

        return await self._process_batch(self._source_pool, self._target_pool)

    async def close(self) -> None:
        """Close any open connection pools."""

        if self._source_pool is not None:
            await self._source_pool.close()
            self._source_pool = None
        if self._target_pool is not None:
            await self._target_pool.close()
            self._target_pool = None

    async def _process_batch(self, source_pool: asyncpg.Pool, target_pool: asyncpg.Pool) -> int:
        logs = await self._extract(source_pool)
        if not logs:
            return 0
        await self._transform_and_load(logs, target_pool)
        return len(logs)

    async def _extract(self, pool: asyncpg.Pool) -> Sequence[MutableMapping[str, Any]]:
        last_id = self.last_processed_id or 0
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, event_type, intent_id, actor, payload, created_at
                FROM audit_logs
                WHERE id > $1
                ORDER BY id
                LIMIT $2
                """,
                last_id,
                self.config.batch_size,
            )

        if rows:
            self.last_processed_id = rows[-1]["id"]

        return [dict(row) for row in rows]

    async def _transform_and_load(self, logs: Sequence[Mapping[str, Any]], pool: asyncpg.Pool) -> None:
        async with pool.acquire() as conn:
            for log in logs:
                await conn.execute(INSERT_AUDIT_LOG_TS, *_prepare_timeseries_row(log))


class EventDrivenAuditLogETL:
    """Event-driven ETL triggered by audit log notifications."""

    def __init__(
        self,
        config: AuditLogETLConfig,
        *,
        source_pool_factory: AuditLogPoolFactory | None = None,
        target_pool_factory: AuditLogPoolFactory | None = None,
    ) -> None:
        self.config = config
        self._source_pool_factory = source_pool_factory or (lambda: asyncpg.create_pool(config.source_db_url))
        self._target_pool_factory = target_pool_factory or (lambda: asyncpg.create_pool(config.target_db_url))
        self._source_pool: asyncpg.Pool | None = None
        self._target_pool: asyncpg.Pool | None = None
        self._distributor = None
        self._subscribed = False

    async def start(self) -> None:
        """Subscribe to audit log events and prepare pools."""

        if self._subscribed:
            return

        self._source_pool = await self._source_pool_factory()
        self._target_pool = await self._target_pool_factory()
        self._distributor = await get_event_distributor()
        self._distributor.subscribe(EventChannel.AUDIT_LOG_CREATED, self._handle_event)
        self._subscribed = True
        logger.info("Event-driven AuditLogETL subscribed to audit log events")

    async def stop(self) -> None:
        """Unsubscribe from distributor and close pools."""

        if self._distributor and self._subscribed:
            self._distributor.unsubscribe(EventChannel.AUDIT_LOG_CREATED, self._handle_event)
        self._subscribed = False
        await self._close_pools()

    async def _close_pools(self) -> None:
        if self._source_pool is not None:
            await self._source_pool.close()
            self._source_pool = None
        if self._target_pool is not None:
            await self._target_pool.close()
            self._target_pool = None

    async def _handle_event(self, event: Event) -> None:
        log_id = event.payload.get("log_id")
        if not log_id:
            logger.debug("Received audit log event without log_id; ignoring")
            return

        if self._source_pool is None or self._target_pool is None:
            logger.warning("Event-driven ETL has not been started; dropping event")
            return

        async with self._source_pool.acquire() as conn:
            row = await conn.fetchrow(SELECT_AUDIT_LOG_SQL, log_id)

        if not row:
            logger.warning("Audit log %s not found during ETL", log_id)
            return

        async with self._target_pool.acquire() as conn:
            await conn.execute(INSERT_AUDIT_LOG_TS, *_prepare_timeseries_row(dict(row)))


def _prepare_timeseries_row(log: Mapping[str, Any]) -> tuple[Any, ...]:
    payload = _ensure_payload_dict(log.get("payload"))
    return (
        log.get("created_at"),
        log.get("id"),
        log.get("event_type"),
        log.get("intent_id"),
        log.get("actor"),
        payload.get("bridge_type"),
        payload.get("old_status"),
        payload.get("new_status"),
        log.get("payload"),
        payload.get("duration_ms"),
        payload.get("success", True),
    )


def _ensure_payload_dict(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Failed to decode payload JSON; returning empty dict")
            return {}
    return dict(payload)
