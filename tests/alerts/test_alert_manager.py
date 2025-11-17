from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Any, Deque, List
from unittest.mock import AsyncMock

import pytest

from bridge.alerts.config import AlertChannel, AlertRule, AlertSeverity
from bridge.alerts.manager import AlertManager


class _FakeAcquire:
    def __init__(self, connection: "_FakeConnection") -> None:
        self._connection = connection

    async def __aenter__(self) -> "_FakeConnection":
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - no errors expected
        return None


class _FakePool:
    def __init__(self, connection: "_FakeConnection") -> None:
        self._connection = connection

    def acquire(self) -> _FakeAcquire:
        return _FakeAcquire(self._connection)


class _FakeConnection:
    def __init__(self, values: List[float]) -> None:
        self._values: Deque[float] = deque(values)

    async def fetchval(self, query: str) -> float:
        if not self._values:
            raise AssertionError("no more values for query")
        return self._values.popleft()


class _FakeSession:
    def __init__(self, store: list[Any]) -> None:
        self._store = store

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, url: str, json: Any, timeout: int) -> None:
        self._store.append((url, json, timeout))


@pytest.mark.asyncio
async def test_alert_manager_triggers_when_threshold_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    rule = AlertRule(
        name="high_error_rate",
        description="",
        severity=AlertSeverity.ERROR,
        condition="SELECT 0.0",
        threshold=0.1,
        channels=[AlertChannel.LOG],
    )

    connection = _FakeConnection([0.2])
    pool = _FakePool(connection)

    async def _pool_factory():
        return pool

    manager = AlertManager(
        "postgres://example",
        rules=[rule],
        pool_factory=_pool_factory,
        clock=lambda: datetime(2025, 1, 1, 0, 0, 0),
    )

    send_alert = AsyncMock()
    monkeypatch.setattr(manager, "_send_alert", send_alert)

    await manager._evaluate_rule(rule, pool)

    send_alert.assert_awaited_once()


@pytest.mark.asyncio
async def test_alert_manager_respects_cooldown_and_no_activity_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2025, 1, 1, 12, 0, 0)

    high_rule = AlertRule(
        name="high_error_rate",
        description="",
        severity=AlertSeverity.ERROR,
        condition="SELECT 0.0",
        threshold=0.1,
        channels=[AlertChannel.LOG],
    )

    no_activity_rule = AlertRule(
        name="no_activity",
        description="",
        severity=AlertSeverity.INFO,
        condition="SELECT 0.0",
        threshold=1.0,
        channels=[AlertChannel.LOG],
    )

    connection = _FakeConnection([0.5, 0.0])
    pool = _FakePool(connection)

    async def _pool_factory():
        return pool

    manager = AlertManager(
        "postgres://example",
        rules=[high_rule, no_activity_rule],
        pool_factory=_pool_factory,
        clock=lambda: now,
    )

    manager.last_alerts[high_rule.name] = now

    send_alert = AsyncMock()
    monkeypatch.setattr(manager, "_send_alert", send_alert)

    await manager._evaluate_rule(high_rule, pool)
    send_alert.assert_not_called()

    # Advance cooldown beyond window
    later = now + timedelta(minutes=high_rule.cooldown_minutes + 1)
    monkeypatch.setattr(manager, "_clock", lambda: later)

    await manager._evaluate_rule(no_activity_rule, pool)
    send_alert.assert_awaited_once()


@pytest.mark.asyncio
async def test_slack_notification_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    rule = AlertRule(
        name="high_correction_rate",
        description="",
        severity=AlertSeverity.WARNING,
        condition="SELECT 0.0",
        threshold=0.2,
        channels=[AlertChannel.SLACK],
    )

    store: list[Any] = []

    def _session_factory() -> _FakeSession:
        return _FakeSession(store)

    manager = AlertManager(
        "postgres://example",
        rules=[rule],
        pool_factory=lambda: None,  # type: ignore[arg-type]
        session_factory=_session_factory,
        clock=lambda: datetime(2025, 1, 1, 0, 0, 0),
    )

    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://slack.invalid/webhook")

    await manager._send_slack(rule, "message", 0.5)

    assert len(store) == 1
    url, payload, timeout = store[0]
    assert url == "https://slack.invalid/webhook"
    assert timeout == 5
    attachment = payload["attachments"][0]
    assert "high_correction_rate" in attachment["title"]
    assert attachment["color"] == "#ff9800"

    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)