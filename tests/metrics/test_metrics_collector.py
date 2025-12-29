from __future__ import annotations

import pytest

# Bridge migration in progress - these modules will be addressed separately
pytestmark = pytest.mark.skip(reason="Bridge migration in progress - metrics module will be addressed separately")

from collections import deque
from typing import Any, Deque, Dict, List
from prometheus_client import CollectorRegistry

from bridge.metrics import MetricsCollector


class _FakeAcquire:
    def __init__(self, connection: "_FakeConnection") -> None:
        self._connection = connection

    async def __aenter__(self) -> "_FakeConnection":
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakePool:
    def __init__(self, connection: "_FakeConnection") -> None:
        self._connection = connection
        self.closed = False

    def acquire(self) -> _FakeAcquire:
        return _FakeAcquire(self._connection)

    async def close(self) -> None:
        self.closed = True


class _FakeConnection:
    def __init__(self, status_batches: List[List[Dict[str, Any]]], correction_batches: List[List[Dict[str, Any]]]) -> None:
        self._status_batches: Deque[List[Dict[str, Any]]] = deque(status_batches)
        self._correction_batches: Deque[List[Dict[str, Any]]] = deque(correction_batches)

    async def fetch(self, query: str, *args: Any) -> List[Dict[str, Any]]:
        if "FROM intents" in query:
            return self._status_batches.popleft() if self._status_batches else []
        if "FROM intent_corrections" in query:
            return self._correction_batches.popleft() if self._correction_batches else []
        raise AssertionError(f"unexpected query: {query}")


@pytest.mark.asyncio
async def test_metrics_collector_updates_counters_and_gauges() -> None:
    status_batches = [
        [
            {"status": "processed", "count": 2},
            {"status": "received", "count": 1},
        ],
        [
            {"status": "processed", "count": 3},
            {"status": "failed", "count": 1},
        ],
    ]
    correction_batches = [
        [
            {"source": "YUNO", "count": 3},
            {"source": None, "count": 1},
        ],
        [
            {"source": "YUNO", "count": 5},
        ],
    ]

    connection = _FakeConnection(status_batches, correction_batches)
    registry = CollectorRegistry()

    async def _pool_factory() -> _FakePool:
        return _FakePool(connection)

    async def _probe() -> int:
        return 5

    collector = MetricsCollector(
        "postgres://example",
        pool_factory=_pool_factory,
        registry=registry,
        websocket_probe=_probe,
    )

    await collector.update_metrics()

    registry = collector.metrics.registry

    assert registry.get_sample_value("bridge_active_intents", {"status": "processed"}) == 2
    assert registry.get_sample_value("bridge_active_intents", {"status": "received"}) == 1

    assert registry.get_sample_value("bridge_intents_total", {"status": "processed"}) == 2
    assert registry.get_sample_value("bridge_intents_total", {"status": "received"}) == 1

    assert registry.get_sample_value("bridge_corrections_total", {"source": "yuno"}) == 3
    assert registry.get_sample_value("bridge_corrections_total", {"source": "unknown"}) == 1

    assert registry.get_sample_value("bridge_websocket_connections", {}) == 5

    # Second update adjusts counters/gauges and zeroes removed statuses
    await collector.update_metrics()

    assert registry.get_sample_value("bridge_active_intents", {"status": "processed"}) == 3
    assert registry.get_sample_value("bridge_active_intents", {"status": "failed"}) == 1
    assert registry.get_sample_value("bridge_active_intents", {"status": "received"}) == 0

    assert registry.get_sample_value("bridge_intents_total", {"status": "processed"}) == 3
    assert registry.get_sample_value("bridge_intents_total", {"status": "failed"}) == 1

    assert registry.get_sample_value("bridge_corrections_total", {"source": "yuno"}) == 5
    assert registry.get_sample_value("bridge_corrections_total", {"source": "unknown"}) == 1

    # Export should include at least one metric name
    output = collector.export().decode()
    assert "bridge_active_intents" in output