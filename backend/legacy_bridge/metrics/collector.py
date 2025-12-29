"""Prometheus-style metrics collector for Bridge Lite."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Dict, Optional, Set

import asyncpg
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger(__name__)

WebsocketProbe = Callable[[], Awaitable[int] | int]
PoolFactory = Callable[[], Awaitable[asyncpg.Pool]]


class IntentMetrics:
    """Container for Prometheus metrics used across Bridge Lite."""

    def __init__(self, registry: Optional[CollectorRegistry] = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.total_intents = Counter(
            "bridge_intents_total",
            "Total number of intents ingested",
            labelnames=("status",),
            registry=self.registry,
        )
        self.processing_duration = Histogram(
            "bridge_processing_duration_seconds",
            "Intent processing duration in seconds",
            labelnames=("bridge_type",),
            registry=self.registry,
        )
        self.active_intents = Gauge(
            "bridge_active_intents",
            "Number of active intents by status",
            labelnames=("status",),
            registry=self.registry,
        )
        self.correction_count = Counter(
            "bridge_corrections_total",
            "Number of corrections applied",
            labelnames=("source",),
            registry=self.registry,
        )
        self.websocket_connections = Gauge(
            "bridge_websocket_connections",
            "Number of active WebSocket connections",
            registry=self.registry,
        )

    def render(self) -> bytes:
        return generate_latest(self.registry)


class MetricsCollector:
    """Query PostgreSQL to refresh Prometheus metrics."""

    def __init__(
        self,
        database_url: str,
        *,
        pool_factory: Optional[PoolFactory] = None,
        registry: Optional[CollectorRegistry] = None,
        websocket_probe: Optional[WebsocketProbe] = None,
    ) -> None:
        if not database_url and pool_factory is None:
            raise ValueError("database_url is required when pool_factory is not provided")
        self._database_url = database_url
        self._pool_factory = pool_factory or (lambda: asyncpg.create_pool(self._database_url))
        self._pool: asyncpg.Pool | None = None
        self.metrics = IntentMetrics(registry)
        self._last_status_totals: Dict[str, int] = defaultdict(int)
        self._last_correction_totals: Dict[str, int] = defaultdict(int)
        self._known_status_labels: Set[str] = set()
        self._websocket_probe = websocket_probe

    async def start(self) -> None:
        if self._pool is None:
            self._pool = await self._pool_factory()

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def ensure_pool(self) -> asyncpg.Pool:
        await self.start()
        assert self._pool is not None
        return self._pool

    async def update_metrics(self) -> None:
        pool = await self.ensure_pool()
        async with pool.acquire() as conn:
            await self._update_status_metrics(conn)
            await self._update_correction_metrics(conn)
        await self._update_websocket_metric()

    async def start_periodic_update(
        self,
        *,
        interval_seconds: float = 30.0,
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        logger.info("Starting metrics collector loop (interval=%ss)", interval_seconds)
        try:
            while True:
                try:
                    await self.update_metrics()
                except Exception:  # pragma: no cover - defensive logging
                    logger.exception("Failed to update metrics")
                if stop_event is not None:
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
                        break
                    except asyncio.TimeoutError:
                        continue
                await asyncio.sleep(interval_seconds)
        finally:
            if stop_event is not None and stop_event.is_set():
                logger.info("Metrics collector loop stopped via event")

    async def _update_status_metrics(self, conn: asyncpg.Connection) -> None:
        rows = await conn.fetch(
            """
            SELECT status, COUNT(*) AS count
            FROM intents
            GROUP BY status
            """
        )
        current_statuses: Set[str] = set()
        for row in rows:
            status = (row.get("status") or "unknown").lower()
            count = int(row.get("count") or 0)
            current_statuses.add(status)
            self.metrics.active_intents.labels(status=status).set(count)
            self._increment_counter(self.metrics.total_intents, self._last_status_totals, "status", status, count)
        for stale in self._known_status_labels - current_statuses:
            self.metrics.active_intents.labels(status=stale).set(0)
        self._known_status_labels = current_statuses

    async def _update_correction_metrics(self, conn: asyncpg.Connection) -> None:
        rows = await conn.fetch(
            """
            SELECT COALESCE(correction->>'source', 'unknown') AS source, COUNT(*) AS count
            FROM intent_corrections
            GROUP BY source
            """
        )
        for row in rows:
            source = (row.get("source") or "unknown").lower()
            count = int(row.get("count") or 0)
            self._increment_counter(
                self.metrics.correction_count,
                self._last_correction_totals,
                "source",
                source,
                count,
            )

    async def _update_websocket_metric(self) -> None:
        if self._websocket_probe is None:
            return
        result = self._websocket_probe()
        if inspect.isawaitable(result):
            result = await result
        try:
            value = int(result)
        except (TypeError, ValueError):  # pragma: no cover - guardrail
            logger.warning("Invalid websocket probe value: %s", result)
            return
        self.metrics.websocket_connections.set(max(value, 0))

    def observe_processing_duration(self, duration_seconds: float, *, bridge_type: str = "default") -> None:
        self.metrics.processing_duration.labels(bridge_type=bridge_type).observe(max(duration_seconds, 0.0))

    def export(self) -> bytes:
        return self.metrics.render()

    def _increment_counter(
        self,
        counter: Counter,
        cache: Dict[str, int],
        label_name: str,
        label_value: str,
        absolute_total: int,
    ) -> None:
        previous = cache.get(label_value, 0)
        delta = absolute_total - previous
        if delta > 0:
            counter.labels(**{label_name: label_value}).inc(delta)
            cache[label_value] = absolute_total
        elif label_value not in cache:
            cache[label_value] = absolute_total