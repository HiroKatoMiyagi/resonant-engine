"""PostgreSQL implementation of the DataBridge."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional

import asyncpg

from bridge.core.data_bridge import DataBridge


class PostgreSQLBridge(DataBridge):
    """`asyncpg`ベースのDataBridge実装。"""

    def __init__(
        self,
        dsn: Optional[str] = None,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        super().__init__()
        self.dsn = dsn or os.getenv("DATABASE_URL")
        if not self.dsn:
            raise ValueError("DATABASE_URLが指定されていません。")
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:  # type: ignore[override]
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
            )
        await super().connect()

    async def disconnect(self) -> None:  # type: ignore[override]
        if self.pool:
            await self.pool.close()
            self.pool = None
        await super().disconnect()

    async def _require_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            await self.connect()
        assert self.pool is not None
        return self.pool

    # ---- Intent CRUD -------------------------------------------------

    async def save_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        status: str = "pending",
        source: str = "auto_generated",
        user_id: Optional[str] = None,
    ) -> str:
        pool = await self._require_pool()
        intent_id = str(uuid.uuid4())
        payload = json.dumps(data)

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO intents (
                    id, type, status, data, source, user_id,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4::jsonb, $5, $6,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """,
                intent_id,
                intent_type,
                status,
                payload,
                source,
                user_id,
            )
        return intent_id

    async def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, type, status, data, source, user_id,
                       feedback, reevaluation,
                       created_at, updated_at, completed_at
                FROM intents
                WHERE id = $1
                """,
                intent_id,
            )
        return dict(row) if row else None

    async def get_pending_intents(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, type, status, data, source, user_id,
                       feedback, reevaluation,
                       created_at, updated_at, completed_at
                FROM intents
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        return [dict(row) for row in rows]

    async def update_intent_status(
        self,
        intent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            if result is not None:
                updated = await conn.execute(
                    """
                    UPDATE intents
                    SET status = $1,
                        data = data || $2::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                    """,
                    status,
                    json.dumps({"result": result}),
                    intent_id,
                )
            else:
                updated = await conn.execute(
                    """
                    UPDATE intents
                    SET status = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                    """,
                    status,
                    intent_id,
                )
        return updated.endswith(" 1")

    # ---- Feedback / Reevaluation ------------------------------------

    async def save_feedback(
        self,
        intent_id: str,
        feedback_data: Dict[str, Any],
    ) -> bool:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            updated = await conn.execute(
                """
                UPDATE intents
                SET feedback = $1::jsonb,
                    status = 'waiting_reevaluation',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                json.dumps(feedback_data),
                intent_id,
            )
        return updated.endswith(" 1")

    async def get_pending_reevaluations(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, type, status, data, source, user_id,
                       feedback, reevaluation,
                       created_at, updated_at, completed_at
                FROM intents
                WHERE status = 'waiting_reevaluation'
                ORDER BY updated_at ASC
                LIMIT $1
                """,
                limit,
            )
        return [dict(row) for row in rows]

    async def save_reevaluation(
        self,
        intent_id: str,
        reevaluation_data: Dict[str, Any],
    ) -> bool:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            updated = await conn.execute(
                """
                UPDATE intents
                SET reevaluation = $1::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                json.dumps(reevaluation_data),
                intent_id,
            )
        return updated.endswith(" 1")

    async def update_reevaluation_status(
        self,
        intent_id: str,
        status: str,
        judgment: str,
        reason: str,
    ) -> bool:
        pool = await self._require_pool()
        complete_clause = (
            "completed_at = CURRENT_TIMESTAMP" if status == "approved" else "completed_at = NULL"
        )
        async with pool.acquire() as conn:
            updated = await conn.execute(
                f"""
                UPDATE intents
                SET status = $1,
                    {complete_clause},
                    updated_at = CURRENT_TIMESTAMP,
                    reevaluation = jsonb_set(
                        COALESCE(reevaluation, '{{}}'::jsonb),
                        '{{yuno_judgment}}', to_jsonb($2::text)
                    ) || jsonb_build_object('reason', $3::text)
                WHERE id = $4
                """,
                status,
                judgment,
                reason,
                intent_id,
            )
        return updated.endswith(" 1")

    # ---- Messages ----------------------------------------------------

    async def save_message(
        self,
        content: str,
        sender: str,
        intent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        pool = await self._require_pool()
        message_id = str(uuid.uuid4())
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (
                    id, content, sender, intent_id, thread_id,
                    created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, CURRENT_TIMESTAMP
                )
                """,
                message_id,
                content,
                sender,
                intent_id,
                thread_id,
            )
        return message_id

    async def get_messages(
        self,
        limit: int = 50,
        thread_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pool = await self._require_pool()
        async with pool.acquire() as conn:
            if thread_id:
                rows = await conn.fetch(
                    """
                    SELECT id, content, sender, intent_id, thread_id, created_at
                    FROM messages
                    WHERE thread_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    thread_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, content, sender, intent_id, thread_id, created_at
                    FROM messages
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit,
                )
        return [dict(row) for row in rows]
