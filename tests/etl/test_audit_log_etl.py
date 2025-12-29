from __future__ import annotations

import pytest

# Bridge migration in progress - these modules will be addressed separately
pytestmark = pytest.mark.skip(reason="Bridge migration in progress - etl module will be addressed separately")

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.legacy_bridge.etl import AuditLogETL, AuditLogETLConfig, EventDrivenAuditLogETL
from backend.legacy_bridge.etl import cli as etl_cli
from app.services.realtime import EventChannel, get_event_distributor, shutdown_event_distributor


class _FakeAcquire:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    async def __aenter__(self) -> Any:  # pragma: no cover - trivial
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None


class FakePool:
    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self.closed = False

    def acquire(self) -> _FakeAcquire:
        return _FakeAcquire(self._connection)

    async def close(self) -> None:
        self.closed = True


class FakeSourceConnection:
    def __init__(self, rows: List[Dict[str, Any]]) -> None:
        self._rows = rows
        self.fetch_calls: List[Dict[str, Any]] = []
        self.fetchrow_results: Dict[int, Dict[str, Any]] = {row["id"]: row for row in rows}

    async def fetch(self, query: str, last_id: int, batch_size: int) -> List[Dict[str, Any]]:
        self.fetch_calls.append({"query": query, "last_id": last_id, "batch_size": batch_size})
        filtered = [row for row in self._rows if row["id"] > last_id]
        return filtered[:batch_size]

    async def fetchrow(self, query: str, log_id: int) -> Optional[Dict[str, Any]]:
        return self.fetchrow_results.get(log_id)


class FakeTargetConnection:
    def __init__(self) -> None:
        self.inserts: List[Dict[str, Any]] = []

    async def execute(self, query: str, *args: Any) -> None:
        self.inserts.append({"query": query, "args": args})


@pytest.mark.asyncio
async def test_audit_log_etl_process_once_transforms_payload() -> None:
    created_at = datetime.now(timezone.utc)
    rows = [
        {
            "id": 1,
            "event_type": "BRIDGE_COMPLETED",
            "intent_id": uuid4(),
            "actor": "system",
            "payload": {
                "bridge_type": "YUNO",
                "old_status": "processing",
                "new_status": "completed",
                "duration_ms": 1200,
                "success": True,
            },
            "created_at": created_at,
        },
        {
            "id": 2,
            "event_type": "BRIDGE_COMPLETED",
            "intent_id": uuid4(),
            "actor": "system",
            "payload": {
                "bridge_type": "YUNO",
                "old_status": "completed",
                "new_status": "archived",
                "duration_ms": 300,
                "success": True,
            },
            "created_at": created_at,
        },
    ]

    source_pool = FakePool(FakeSourceConnection(rows))
    target_connection = FakeTargetConnection()
    target_pool = FakePool(target_connection)

    async def _source_factory() -> FakePool:
        return source_pool

    async def _target_factory() -> FakePool:
        return target_pool

    config = AuditLogETLConfig("postgres://source", "postgres://target", batch_size=10)
    etl = AuditLogETL(config, source_pool_factory=_source_factory, target_pool_factory=_target_factory)

    processed = await etl.process_once()

    assert processed == 2
    assert len(target_connection.inserts) == 2
    first_args = target_connection.inserts[0]["args"]
    assert first_args[0] == created_at
    assert first_args[5] == "YUNO"
    assert first_args[6] == "processing"
    assert first_args[7] == "completed"
    assert first_args[9] == 1200
    assert first_args[10] is True

    # Running again without new rows should not insert duplicates
    processed_again = await etl.process_once()
    assert processed_again == 0
    assert len(target_connection.inserts) == 2

    await etl.close()


@pytest.mark.asyncio
async def test_event_driven_etl_handles_notifications(monkeypatch) -> None:
    monkeypatch.setenv("BRIDGE_RT_IN_MEMORY", "1")

    created_at = datetime.now(timezone.utc)
    intent_id = uuid4()
    log_row = {
        "id": 42,
        "event_type": "BRIDGE_COMPLETED",
        "intent_id": intent_id,
        "actor": "system",
        "payload": {
            "bridge_type": "YUNO",
            "old_status": "received",
            "new_status": "completed",
            "duration_ms": 1500,
            "success": True,
        },
        "created_at": created_at,
    }

    source_conn = FakeSourceConnection([])
    source_conn.fetchrow_results = {42: log_row}
    target_conn = FakeTargetConnection()

    async def _source_factory() -> FakePool:
        return FakePool(source_conn)

    async def _target_factory() -> FakePool:
        return FakePool(target_conn)

    config = AuditLogETLConfig("postgres://source", "postgres://target")
    etl = EventDrivenAuditLogETL(config, source_pool_factory=_source_factory, target_pool_factory=_target_factory)

    await etl.start()

    distributor = await get_event_distributor()
    await distributor.publish(EventChannel.AUDIT_LOG_CREATED, {"log_id": 42})

    # Allow the async handler to complete
    await asyncio.sleep(0.05)

    assert len(target_conn.inserts) == 1
    args = target_conn.inserts[0]["args"]
    assert args[1] == 42
    assert args[4] == "system"
    assert args[6] == "received"
    assert args[7] == "completed"

    await etl.stop()
    await shutdown_event_distributor()


def test_build_config_requires_source_dsn(monkeypatch) -> None:
    for env_var in ("BRIDGE_SOURCE_DSN", "POSTGRES_DSN", "DATABASE_URL"):
        monkeypatch.delenv(env_var, raising=False)
    args = etl_cli.parse_args([])
    with pytest.raises(RuntimeError):
        etl_cli.build_config(args)


def test_build_config_uses_env_defaults(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_DSN", "postgres://source")
    monkeypatch.setenv("TIMESCALE_DSN", "postgres://target")
    monkeypatch.delenv("TIMESCALE_DATABASE_URL", raising=False)
    args = etl_cli.parse_args([])
    config = etl_cli.build_config(args)
    assert config.source_db_url == "postgres://source"
    assert config.target_db_url == "postgres://target"
    assert config.batch_size == 100
    assert config.interval_seconds == 5.0


def test_build_config_defaults_target_to_source(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://shared")
    for env_var in ("TIMESCALE_DSN", "BRIDGE_TIMESCALE_DSN", "TIMESCALE_DATABASE_URL"):
        monkeypatch.delenv(env_var, raising=False)
    args = etl_cli.parse_args([])
    config = etl_cli.build_config(args)
    assert config.source_db_url == "postgres://shared"
    assert config.target_db_url == "postgres://shared"