"""PostgreSQL-backed DataBridge following Bridge Lite Sprint 2 spec."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import asyncpg
from asyncpg import Connection, Pool, Record

from bridge.core.concurrency import ConcurrencyConfig
from bridge.core.constants import PhilosophicalActor
from bridge.core.data_bridge import DataBridge
from bridge.core.enums import IntentStatus
from bridge.core.errors import DeadlockError, LockTimeoutError, is_deadlock_error
from bridge.core.locks import LockedIntentSession
from bridge.core.models.intent_model import CorrectionRecord, IntentModel


class PostgresDataBridge(DataBridge):
    """Persist intents and corrections in PostgreSQL."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        pool: Optional[Pool] = None,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        super().__init__()
        self._dsn = dsn or os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
        self._pool = pool
        self._min_size = min_size
        self._max_size = max_size

    async def connect(self) -> None:  # type: ignore[override]
        if self._pool is None:
            if not self._dsn:
                raise ValueError("POSTGRES_DSN or DATABASE_URL must be provided")
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
            )
        await super().connect()

    async def disconnect(self) -> None:  # type: ignore[override]
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
        await super().disconnect()

    async def _require_pool(self) -> Pool:
        if self._pool is None:
            await self.connect()
        assert self._pool is not None
        return self._pool

    async def save_intent(self, intent: IntentModel) -> IntentModel:
        pool = await self._require_pool()
        base = intent.model_copy(deep=True)
        now = datetime.now(timezone.utc)
        created_at = base.created_at or now
        updated_at = base.updated_at or now
        source = base.source.value
        correlation_id = base.correlation_id
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO intents (id, source, type, data, status, correlation_id, created_at, updated_at, version)
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4::jsonb,
                    $5,
                    $6,
                    COALESCE($7, NOW()),
                    COALESCE($8, NOW()),
                    COALESCE($9, 0)
                )
                RETURNING id, source, type, data, status, correlation_id, created_at, updated_at, version
                """,
                base.intent_id,
                source,
                base.type,
                base.payload,
                base.status.value,
                correlation_id,
                created_at,
                updated_at,
                base.version,
            )
        assert row is not None
        return self._format_intent(row)

    async def get_intent(self, intent_id: str) -> IntentModel:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, source, type, data, status, correlation_id, created_at, updated_at, version
                FROM intents
                WHERE id = $1
                """,
                intent_id,
            )
            if row is None:
                raise KeyError(f"intent not found: {intent_id}")
            corrections = await self._fetch_corrections(conn, intent_id)
        return self._format_intent(row, corrections)

    async def save_correction(
        self,
        intent_id: str,
        correction: Dict[str, Any],
        *,
        persist_status: bool = True,
    ) -> IntentModel:
        pool = await self._require_pool()
        status_raw = correction.get("status")
        status = IntentModel._coerce_status(status_raw) if status_raw is not None else None
        correction_payload = dict(correction)
        correction_payload.setdefault("source", correction_payload.get("source") or PhilosophicalActor.KANA.value)
        correction_payload.setdefault(
            "diff",
            correction_payload.get("diff") or correction_payload.get("payload") or {},
        )
        correction_payload.setdefault("applied_at", correction_payload.get("applied_at") or datetime.now(timezone.utc))
        record = CorrectionRecord.model_validate(correction_payload)
        record_dump = record.model_dump(mode="json", exclude_none=True)
        async with pool.acquire() as conn:
            async with conn.transaction():
                exists = await conn.fetchval(
                    """
                    SELECT 1
                    FROM intent_corrections
                    WHERE intent_id = $1 AND correction->>'correction_id' = $2
                    LIMIT 1
                    """,
                    intent_id,
                    str(record.correction_id),
                )
                if not exists:
                    await conn.execute(
                        """
                        INSERT INTO intent_corrections (intent_id, correction)
                        VALUES ($1, $2::jsonb)
                        """,
                        intent_id,
                        record_dump,
                    )
                if status is not None and persist_status:
                    await conn.execute(
                        """
                        UPDATE intents
                        SET status = $2, updated_at = NOW(), version = version + 1
                        WHERE id = $1
                        """,
                        intent_id,
                        status.value,
                    )
        return await self.get_intent(intent_id)

    async def list_intents(self, status: Optional[IntentStatus] = None) -> List[IntentModel]:
        pool = await self._require_pool()
        query = (
            """
            SELECT id, source, type, data, status, correlation_id, created_at, updated_at, version
            FROM intents
            ORDER BY created_at ASC
            """
        )
        args: List[Any] = []
        if status is not None:
            query = (
                """
                SELECT id, source, type, data, status, correlation_id, created_at, updated_at, version
                FROM intents
                WHERE status = $1
                ORDER BY created_at ASC
                """
            )
            args.append(status.value)

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
        return [self._format_intent(row) for row in rows]

    async def update_intent(self, intent: IntentModel) -> IntentModel:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE intents
                SET data = $2::jsonb,
                    status = $3,
                    source = $4,
                    type = $5,
                    correlation_id = $6,
                    updated_at = COALESCE($7, NOW()),
                    version = COALESCE($8, version)
                WHERE id = $1
                """,
                intent.intent_id,
                intent.payload,
                intent.status.value,
                intent.source.value,
                intent.type,
                intent.correlation_id,
                intent.updated_at,
                intent.version,
            )
        return await self.get_intent(intent.intent_id)

    async def update_intent_status(self, intent_id: str, status: Union[IntentStatus, str]) -> IntentModel:
        new_status = IntentModel._coerce_status(status)

        async with self.lock_intent_for_update(intent_id) as locked:
            IntentModel.validate_status_transition(locked.intent.status, new_status)
            intent = locked.intent.with_updates(
                status=new_status,
                updated_at=datetime.now(timezone.utc),
            )
            intent.increment_version()
            locked.replace(intent)
            return intent

    async def update_intent_if_version_matches(
        self,
        intent_id: str,
        intent: IntentModel,
        *,
        expected_version: int,
    ) -> bool:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE intents
                SET data = $3::jsonb,
                    status = $4,
                    source = $5,
                    type = $6,
                    correlation_id = $7,
                    updated_at = COALESCE($8, NOW()),
                    version = $9
                WHERE id = $1 AND version = $2
                RETURNING id
                """,
                intent_id,
                expected_version,
                intent.payload,
                intent.status.value,
                intent.source.value,
                intent.type,
                intent.correlation_id,
                intent.updated_at,
                intent.version,
            )
            if row:
                return True
        return False

    @asynccontextmanager
    async def lock_intent_for_update(
        self,
        intent_id: str,
        *,
        timeout: float | None = None,
    ) -> AsyncIterator[LockedIntentSession]:
        pool = await self._require_pool()
        timeout = timeout or ConcurrencyConfig.LOCK_TIMEOUT

        async with pool.acquire() as conn:
            tx = conn.transaction()
            await tx.start()
            try:
                await self._configure_timeouts(conn, timeout)
                row = await conn.fetchrow(
                    """
                    SELECT id, source, type, data, status, correlation_id, created_at, updated_at, version
                    FROM intents
                    WHERE id = $1
                    FOR UPDATE NOWAIT
                    """,
                    intent_id,
                )
                if row is None:
                    raise KeyError(f"intent not found: {intent_id}")
                corrections = await self._fetch_corrections(conn, intent_id)
                session = LockedIntentSession(self._format_intent(row, corrections))
                try:
                    yield session
                finally:
                    await self._persist_locked_intent(conn, session.intent)
                await tx.commit()
            except asyncpg.exceptions.LockNotAvailableError as exc:
                await tx.rollback()
                raise LockTimeoutError(f"Could not acquire lock on intent {intent_id}") from exc
            except asyncpg.PostgresError as exc:
                await tx.rollback()
                if is_deadlock_error(exc):
                    raise DeadlockError(
                        f"Deadlock detected while locking intent {intent_id}",
                        deadlock_info={"intent_id": intent_id},
                    ) from exc
                raise
            except Exception:
                await tx.rollback()
                raise

    async def _fetch_corrections(self, conn: Connection, intent_id: str) -> List[Dict[str, Any]]:
        rows = await conn.fetch(
            """
            SELECT correction, created_at
            FROM intent_corrections
            WHERE intent_id = $1
            ORDER BY created_at ASC
            """,
            intent_id,
        )
        corrections: List[Dict[str, Any]] = []
        for row in rows:
            correction = dict(row["correction"])
            correction.setdefault("applied_at", row.get("created_at"))
            record = CorrectionRecord.model_validate(correction)
            corrections.append(record.model_dump(mode="json", exclude_none=True))
        return corrections

    async def _persist_locked_intent(self, conn: Connection, intent: IntentModel) -> None:
        await conn.execute(
            """
            UPDATE intents
            SET data = $2::jsonb,
                status = $3,
                source = $4,
                type = $5,
                correlation_id = $6,
                updated_at = COALESCE($7, NOW()),
                version = $8
            WHERE id = $1
            """,
            intent.intent_id,
            intent.payload,
            intent.status.value,
            intent.source.value,
            intent.type,
            intent.correlation_id,
            intent.updated_at,
            intent.version,
        )

    async def _configure_timeouts(self, conn: Connection, timeout: float) -> None:
        timeout_ms = int(timeout * 1000)
        await conn.execute(f"SET LOCAL statement_timeout = '{timeout_ms}ms'")
        await conn.execute(f"SET LOCAL lock_timeout = '{timeout_ms}ms'")

    @staticmethod
    def _format_intent(row: Record, corrections: Optional[List[Dict[str, Any]]] = None) -> IntentModel:
        return IntentModel(
            intent_id=row["id"],
            type=row["type"],
            payload=row["data"],
            status=row["status"],
            source=row["source"],
            correlation_id=row["correlation_id"],
            corrections=corrections or [],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            version=row.get("version") or 0,
        )
