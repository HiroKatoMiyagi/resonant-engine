"""PostgreSQL-backed DataBridge following Bridge Lite spec v2.0."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import asyncpg
from asyncpg import Connection, Record

from bridge.core.data_bridge import DataBridge
from bridge.core.enums import IntentStatus
from bridge.core.constants import PhilosophicalActor
from bridge.core.models.intent_model import CorrectionRecord, IntentModel


class PostgresDataBridge(DataBridge):
    """Persist intents and corrections in PostgreSQL."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        pool: Optional[asyncpg.Pool] = None,
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

    async def _require_pool(self) -> asyncpg.Pool:
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
                INSERT INTO intents (id, source, type, payload, status, correlation_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6, COALESCE($7, NOW()), COALESCE($8, NOW()))
                RETURNING id, source, type, payload, status, correlation_id, created_at, updated_at
                """,
                base.intent_id,
                source,
                base.type,
                base.payload,
                base.status.value,
                correlation_id,
                created_at,
                updated_at,
            )
        assert row is not None
        return self._format_intent(row)

    async def get_intent(self, intent_id: str) -> IntentModel:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, source, type, payload, status, correlation_id, created_at, updated_at
                FROM intents
                WHERE id = $1
                """,
                intent_id,
            )
            if row is None:
                raise KeyError(f"intent not found: {intent_id}")
            corrections = await self._fetch_corrections(conn, intent_id)
        return self._format_intent(row, corrections)

    async def save_correction(self, intent_id: str, correction: Dict[str, Any]) -> IntentModel:
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
                if status is not None:
                    await conn.execute(
                        """
                        UPDATE intents
                        SET status = $2, updated_at = NOW()
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
            SELECT id, source, type, payload, status, correlation_id, created_at, updated_at
            FROM intents
            ORDER BY created_at ASC
            """
        )
        args: List[Any] = []
        if status is not None:
            query = (
                """
                SELECT id, source, type, payload, status, correlation_id, created_at, updated_at
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
                SET payload = $2::jsonb,
                    status = $3,
                    source = $4,
                    type = $5,
                    correlation_id = $6,
                    updated_at = COALESCE($7, NOW())
                WHERE id = $1
                """,
                intent.intent_id,
                intent.payload,
                intent.status.value,
                intent.source.value,
                intent.type,
                intent.correlation_id,
                intent.updated_at,
            )
        return await self.get_intent(intent.intent_id)

    async def update_intent_status(self, intent_id: str, status: Union[IntentStatus, str]) -> IntentModel:
        pool = await self._require_pool()
        status_value = IntentModel._coerce_status(status).value
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE intents
                SET status = $2, updated_at = NOW()
                WHERE id = $1
                """,
                intent_id,
                status_value,
            )
        return await self.get_intent(intent_id)

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

    @staticmethod
    def _format_intent(row: Record, corrections: Optional[List[Dict[str, Any]]] = None) -> IntentModel:
        return IntentModel(
            intent_id=row["id"],
            type=row["type"],
            payload=row["payload"],
            status=row["status"],
            source=row["source"],
            correlation_id=row["correlation_id"],
            corrections=corrections or [],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
