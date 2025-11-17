"""Business logic for dashboard endpoints."""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .repository import DashboardRepository, TimelineBucket

WebsocketProbe = Callable[[], Awaitable[int] | int]


class DashboardService:
    """Aggregate repository data into API response payloads."""

    def __init__(
        self,
        repository: DashboardRepository,
        *,
        websocket_probe: Optional[WebsocketProbe] = None,
    ) -> None:
        self._repository = repository
        self._websocket_probe = websocket_probe

    async def close(self) -> None:
        await self._repository.close()

    async def get_overview(self) -> Dict[str, Any]:
        total = await self._repository.fetch_total_intents()
        status_counts = await self._repository.fetch_status_counts()
        last_hour = await self._repository.fetch_recent_activity(1)
        last_day = await self._repository.fetch_recent_activity(24)
        last_week = await self._repository.fetch_recent_activity(168)
        intents_with_corrections = await self._repository.fetch_intents_with_corrections()
        correction_rate = (intents_with_corrections / total) if total else 0.0
        avg_processing_ms = await self._repository.fetch_avg_processing_time_ms()
        websocket_connections = await self._probe_websocket_connections()

        return {
            "total_intents": total,
            "status_distribution": status_counts,
            "recent_activity": {
                "last_hour": last_hour,
                "last_24h": last_day,
                "last_7d": last_week,
            },
            "correction_rate": round(correction_rate, 3),
            "avg_processing_time_ms": int(avg_processing_ms or 0),
            "active_websockets": websocket_connections,
        }

    async def get_timeline(self, start: datetime, end: datetime, granularity: str) -> List[Dict[str, Any]]:
        buckets = await self._repository.fetch_timeline(start, end, granularity)
        return [
            {
                "time": bucket.timestamp.isoformat(),
                "count": bucket.count,
            }
            for bucket in buckets
        ]

    async def get_corrections_summary(self, limit: int) -> List[Dict[str, Any]]:
        rows = await self._repository.fetch_corrections_summary(limit)
        return rows

    async def _probe_websocket_connections(self) -> int:
        if self._websocket_probe is None:
            return 0
        result = self._websocket_probe()
        if inspect.isawaitable(result):
            result = await result
        try:
            return max(int(result), 0)
        except (TypeError, ValueError):
            return 0
