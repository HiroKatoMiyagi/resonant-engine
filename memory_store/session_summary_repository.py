"""Session Summary Repository - Session要約の永続化層

Sprint 7で追加されたセッション要約機能のリポジトリ層。
"""

import asyncpg
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from memory_store.models import SessionSummaryResponse


class SessionSummaryRepository:
    """Session Summary永続化層"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save(
        self,
        user_id: str,
        session_id: UUID,
        summary: str,
        message_count: int,
        start_time: datetime,
        end_time: datetime,
    ) -> UUID:
        """
        Session Summaryを保存

        Args:
            user_id: ユーザーID
            session_id: セッションID
            summary: 要約テキスト
            message_count: メッセージ数
            start_time: セッション開始時刻
            end_time: セッション終了時刻

        Returns:
            UUID: 保存されたSession SummaryのID

        Note:
            同じuser_id + session_idの組み合わせの場合、UPSERTで更新
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO session_summaries (
                    user_id, session_id, summary, message_count,
                    start_time, end_time, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                ON CONFLICT (user_id, session_id)
                DO UPDATE SET
                    summary = EXCLUDED.summary,
                    message_count = EXCLUDED.message_count,
                    end_time = EXCLUDED.end_time,
                    updated_at = NOW()
                RETURNING id
            """, user_id, session_id, summary, message_count, start_time, end_time)

            return result['id']

    async def get_latest(
        self,
        user_id: str,
        session_id: Optional[UUID] = None,
    ) -> Optional[SessionSummaryResponse]:
        """
        最新のSession Summaryを取得

        Args:
            user_id: ユーザーID
            session_id: セッションID（Noneの場合は最新）

        Returns:
            SessionSummaryResponse or None
        """
        async with self.pool.acquire() as conn:
            if session_id:
                # 特定セッションの要約
                row = await conn.fetchrow("""
                    SELECT * FROM session_summaries
                    WHERE user_id = $1 AND session_id = $2
                    ORDER BY created_at DESC
                    LIMIT 1
                """, user_id, session_id)
            else:
                # ユーザーの最新要約
                row = await conn.fetchrow("""
                    SELECT * FROM session_summaries
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, user_id)

            if row:
                return SessionSummaryResponse(**dict(row))
            return None

    async def get_by_session(
        self,
        session_id: UUID,
    ) -> Optional[SessionSummaryResponse]:
        """
        特定セッションのSummaryを取得

        Args:
            session_id: セッションID

        Returns:
            SessionSummaryResponse or None
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM session_summaries
                WHERE session_id = $1
            """, session_id)

            if row:
                return SessionSummaryResponse(**dict(row))
            return None

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[SessionSummaryResponse]:
        """
        ユーザーのSession Summary一覧を取得

        Args:
            user_id: ユーザーID
            limit: 取得件数

        Returns:
            List[SessionSummaryResponse]
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM session_summaries
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)

            return [SessionSummaryResponse(**dict(row)) for row in rows]

    async def delete(self, summary_id: UUID) -> bool:
        """
        Session Summaryを削除

        Args:
            summary_id: Summary ID

        Returns:
            bool: 削除成功したらTrue
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM session_summaries
                WHERE id = $1
            """, summary_id)

            return result == "DELETE 1"
