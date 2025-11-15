"""PostgreSQL backed audit logger."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import asyncpg
from asyncpg import Record

from bridge.core.audit_logger import AuditLogger
from bridge.core.constants import AuditEventType, BridgeTypeEnum, LogSeverity


class PostgresAuditLogger(AuditLogger):
    """Persist audit entries and expose simple cleanup logic."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        pool: Optional[asyncpg.Pool] = None,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        self._dsn = dsn or os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
        self._pool = pool
        self._min_size = min_size
        self._max_size = max_size

    async def _require_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            if not self._dsn:
                raise ValueError("POSTGRES_DSN or DATABASE_URL must be provided")
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
            )
        return self._pool

    async def log(
        self,
        bridge_type: BridgeTypeEnum,
        operation: str,
        details: Dict[str, Any],
        intent_id: Optional[str],
        correlation_id: Optional[str] = None,
        event: Optional[AuditEventType] = None,
        severity: LogSeverity = LogSeverity.INFO,
    ) -> None:
        pool = await self._require_pool()
        log_details = dict(details)
        if event is not None:
            log_details.setdefault("_bridge_event", event.value)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_logs (bridge_type, operation, level, details, intent_id, correlation_id)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                """,
                bridge_type.value,
                operation,
                severity.value,
                log_details,
                intent_id,
                correlation_id,
            )

    async def cleanup(self) -> None:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM audit_logs WHERE timestamp < now() - INTERVAL '30 days'"
            )

    async def fetch_recent(self, limit: int = 10) -> list[Record]:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *
                FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT $1
                """,
                limit,
            )
        return list(rows)
