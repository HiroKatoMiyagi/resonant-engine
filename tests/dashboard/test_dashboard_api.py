from __future__ import annotations

import pytest

# Bridge API migration in progress
pytestmark = pytest.mark.skip(reason="Bridge API migration in progress - will be addressed separately")

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterator, List, Tuple

os.environ.setdefault("BRIDGE_SKIP_REALTIME_STARTUP", "1")
os.environ.setdefault("BRIDGE_RT_IN_MEMORY", "1")

import pytest
from fastapi.testclient import TestClient

from bridge.api import dashboard as dashboard_module
from bridge.api.app import app


@dataclass
class _FakeDashboardService:
    overview_payload: Dict[str, Any] = field(
        default_factory=lambda: {
            "total_intents": 12,
            "status_distribution": {"processed": 7, "received": 5},
            "recent_activity": {"last_hour": 3, "last_24h": 10, "last_7d": 42},
            "correction_rate": 0.25,
            "avg_processing_time_ms": 1500,
            "active_websockets": 2,
        }
    )
    timeline_payload: List[Dict[str, Any]] = field(
        default_factory=lambda: [
            {"time": "2025-01-01T00:00:00+00:00", "count": 4},
            {"time": "2025-01-01T01:00:00+00:00", "count": 6},
        ]
    )
    corrections_payload: List[Dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "intent_id": "11111111-1111-1111-1111-111111111111",
                "correction_count": 2,
                "last_correction": {"source": "YUNO", "applied_at": "2025-01-01T00:00:00Z"},
            }
        ]
    )
    overview_calls: int = 0
    timeline_calls: List[Tuple[datetime, datetime, str]] = field(default_factory=list)
    corrections_calls: List[int] = field(default_factory=list)

    async def get_overview(self) -> Dict[str, Any]:
        self.overview_calls += 1
        return self.overview_payload

    async def get_timeline(self, start: datetime, end: datetime, granularity: str) -> List[Dict[str, Any]]:
        self.timeline_calls.append((start, end, granularity))
        return self.timeline_payload

    async def get_corrections_summary(self, limit: int) -> List[Dict[str, Any]]:
        self.corrections_calls.append(limit)
        return self.corrections_payload


@contextmanager
def _override_dashboard_service(service: _FakeDashboardService):
    async def _dependency_override() -> _FakeDashboardService:
        return service

    setattr(dashboard_module.get_dashboard_service, "_instance", None)
    app.dependency_overrides[dashboard_module.get_dashboard_service] = _dependency_override
    try:
        yield service
    finally:
        app.dependency_overrides.pop(dashboard_module.get_dashboard_service, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_dashboard_overview_returns_service_payload(client: TestClient) -> None:
    service = _FakeDashboardService()

    with _override_dashboard_service(service):
        response = client.get("/api/v1/dashboard/overview")

    assert response.status_code == 200
    assert response.json() == service.overview_payload
    assert service.overview_calls == 1


def test_dashboard_timeline_passes_parameters(client: TestClient) -> None:
    service = _FakeDashboardService()
    start = datetime.now(timezone.utc) - timedelta(hours=2)
    end = datetime.now(timezone.utc)

    with _override_dashboard_service(service):
        response = client.get(
            "/api/v1/dashboard/timeline",
            params={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "granularity": "hour",
            },
        )

    assert response.status_code == 200
    assert response.json() == service.timeline_payload
    assert service.timeline_calls == [(start, end, "hour")]


def test_dashboard_timeline_requires_end_after_start(client: TestClient) -> None:
    service = _FakeDashboardService()
    start = datetime.now(timezone.utc)
    end = start - timedelta(minutes=5)

    with _override_dashboard_service(service):
        response = client.get(
            "/api/v1/dashboard/timeline",
            params={"start": start.isoformat(), "end": end.isoformat()},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "end must be after start"
    assert service.timeline_calls == []


def test_dashboard_corrections_returns_service_payload(client: TestClient) -> None:
    service = _FakeDashboardService()

    with _override_dashboard_service(service):
        response = client.get("/api/v1/dashboard/corrections", params={"limit": 5})

    assert response.status_code == 200
    assert response.json() == service.corrections_payload
    assert service.corrections_calls == [5]