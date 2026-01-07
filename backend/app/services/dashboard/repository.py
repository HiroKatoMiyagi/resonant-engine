"""Database access helpers for dashboard metrics."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

import asyncpg


@dataclass
class TimelineBucket:
    timestamp: datetime
    count: int


class DashboardRepository:
    """Protocol-like base class for dashboard data access."""

    async def fetch_total_intents(self) -> int:  # pragma: no cover - interface
        raise NotImplementedError

    async def fetch_status_counts(self) -> Dict[str, int]:  # pragma: no cover - interface
        raise NotImplementedError

    async def fetch_recent_activity(self, hours: int) -> int:  # pragma: no cover - interface
        raise NotImplementedError

    async def fetch_intents_with_corrections(self) -> int:  # pragma: no cover - interface
        raise NotImplementedError

    async def fetch_avg_processing_time_ms(self, lookback_hours: int = 24) -> Optional[float]:  # pragma: no cover
        raise NotImplementedError

    async def fetch_timeline(
        self,
        start: datetime,
        end: datetime,
        granularity: str,
    ) -> List[TimelineBucket]:  # pragma: no cover - interface
        raise NotImplementedError

    async def fetch_corrections_summary(self, limit: int) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError

    async def close(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError


PoolFactory = Callable[[], Awaitable[asyncpg.Pool]]


class PostgresDashboardRepository(DashboardRepository):
    """Asyncpg-backed repository used by production dashboard endpoints."""

    def __init__(
        self,
        database_url: Optional[str] = None,
        *,
        pool_factory: Optional[PoolFactory] = None,
    ) -> None:
        self._database_url = database_url or os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
        if not self._database_url and pool_factory is None:
            raise ValueError("POSTGRES_DSN or DATABASE_URL must be configured for dashboard repository")
        self._pool_factory = pool_factory or (lambda: asyncpg.create_pool(self._database_url))
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await self._pool_factory()
        return self._pool

    async def fetch_total_intents(self) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            value = await conn.fetchval("SELECT COUNT(*) FROM intents")
        return int(value or 0)

    async def fetch_status_counts(self) -> Dict[str, int]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT COALESCE(status, 'unknown') AS status, COUNT(*) AS count
                FROM intents
                GROUP BY status
                """
            )
        return {str(row["status"]).lower(): int(row["count"] or 0) for row in rows}

    async def fetch_recent_activity(self, hours: int) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            value = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM intents
                WHERE created_at > NOW() - ($1 || ' hours')::interval
                """,
                str(hours),
            )
        return int(value or 0)

    async def fetch_intents_with_corrections(self) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            value = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT intent_id)
                FROM corrections
                """
            )
        return int(value or 0)

    async def fetch_avg_processing_time_ms(self, lookback_hours: int = 24) -> Optional[float]:
        pool = await self._ensure_pool()
        try:
            async with pool.acquire() as conn:
                value = await conn.fetchval(
                    """
                    WITH started AS (
                        SELECT intent_id, MIN(created_at) AS started_at
                        FROM audit_logs
                        WHERE event_type = 'BRIDGE_STARTED'
                          AND created_at > NOW() - ($1 || ' hours')::interval
                        GROUP BY intent_id
                    ),
                    completed AS (
                        SELECT intent_id, MIN(created_at) AS completed_at
                        FROM audit_logs
                        WHERE event_type = 'BRIDGE_COMPLETED'
                          AND created_at > NOW() - ($1 || ' hours')::interval
                        GROUP BY intent_id
                    )
                    SELECT AVG(EXTRACT(epoch FROM (completed.completed_at - started.started_at)) * 1000)
                    FROM started
                    JOIN completed ON completed.intent_id = started.intent_id
                    """,
                    str(lookback_hours),
                )
            return float(value) if value is not None else None
        except Exception:
            # audit_logs table may not exist
            return None

    async def fetch_timeline(
        self,
        start: datetime,
        end: datetime,
        granularity: str,
    ) -> List[TimelineBucket]:
        if granularity not in {"minute", "hour", "day"}:
            raise ValueError("granularity must be minute, hour, or day")
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT date_trunc($1, created_at) AS bucket, COUNT(*) AS count
                FROM intents
                WHERE created_at BETWEEN $2 AND $3
                GROUP BY bucket
                ORDER BY bucket
                """,
                granularity,
                start,
                end,
            )
        return [TimelineBucket(timestamp=row["bucket"], count=int(row["count"] or 0)) for row in rows]

    async def fetch_corrections_summary(self, limit: int) -> List[Dict[str, Any]]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT intent_id,
                       COUNT(*) AS correction_count,
                       (ARRAY_AGG(reason ORDER BY created_at DESC))[1] AS last_correction,
                       MAX(created_at) AS last_updated
                FROM corrections
                GROUP BY intent_id
                ORDER BY last_updated DESC
                LIMIT $1
                """,
                limit,
            )
        results: List[Dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "intent_id": str(row["intent_id"]),
                    "correction_count": int(row["correction_count"] or 0),
                    "last_correction": row["last_correction"],
                }
            )
        return results

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
