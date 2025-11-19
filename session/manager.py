"""SessionManager - セッション管理とトリガー制御

Sprint 7で追加されたセッション要約機能のトリガー管理層。
"""

from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional
import logging

from memory_store.session_summary_repository import SessionSummaryRepository
from memory_store.models import SessionStats
from summarization.service import SummarizationService
from session.config import SessionConfig, get_default_session_config

logger = logging.getLogger(__name__)


class SessionManager:
    """セッション管理とトリガー制御"""

    def __init__(
        self,
        summary_repo: SessionSummaryRepository,
        summarization_service: SummarizationService,
        config: Optional[SessionConfig] = None,
    ):
        self.summary_repo = summary_repo
        self.summarization = summarization_service
        self.config = config or get_default_session_config()

    async def check_and_create_summary(
        self,
        user_id: str,
        session_id: UUID,
        messages: list,
    ) -> Optional[object]:
        """
        要約生成の必要性を判定し、必要なら生成

        Args:
            user_id: ユーザーID
            session_id: セッションID
            messages: 現在のメッセージリスト

        Returns:
            SessionSummaryResponse or None
        """
        should_create = await self._should_create_summary(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
        )

        if not should_create:
            return None

        try:
            logger.info(f"Creating session summary for session {session_id}")
            summary = await self.summarization.create_summary(
                user_id=user_id,
                session_id=session_id,
                messages=messages,
            )
            logger.info(f"Session summary created: {summary.id}")
            return summary
        except Exception as e:
            logger.error(f"Failed to create session summary: {e}")
            return None

    async def _should_create_summary(
        self,
        user_id: str,
        session_id: UUID,
        messages: list,
    ) -> bool:
        """
        要約生成が必要か判定

        トリガー条件:
        1. メッセージ数が閾値に達した（デフォルト20件）
        2. 前回要約から一定時間経過（デフォルト1時間）

        Args:
            user_id: ユーザーID
            session_id: セッションID
            messages: 現在のメッセージリスト

        Returns:
            bool: 要約生成が必要ならTrue
        """
        message_count = len(messages)

        # 条件1: メッセージ数閾値チェック
        if message_count >= self.config.summary_trigger_message_count:
            # 20件ごとにトリガー
            if message_count % self.config.summary_trigger_message_count == 0:
                logger.info(f"Trigger: message count reached {message_count}")
                return True

        # 条件2: 時間経過チェック
        last_summary = await self.summary_repo.get_latest(user_id, session_id)
        if last_summary:
            time_since_last = datetime.now() - last_summary.updated_at
            threshold = timedelta(seconds=self.config.summary_trigger_interval_seconds)

            if time_since_last >= threshold:
                logger.info(f"Trigger: time elapsed since last summary ({time_since_last})")
                return True

        return False

    async def get_session_stats(
        self,
        user_id: str,
        session_id: UUID,
        messages: list,
    ) -> SessionStats:
        """
        セッション統計を取得

        Args:
            user_id: ユーザーID
            session_id: セッションID
            messages: 現在のメッセージリスト

        Returns:
            SessionStats: セッション統計情報
        """
        message_count = len(messages)

        # 時刻情報を計算
        first_message_time = None
        last_message_time = None
        duration_seconds = None

        if messages:
            if 'created_at' in messages[0]:
                first_message_time = messages[0]['created_at']
            if 'created_at' in messages[-1]:
                last_message_time = messages[-1]['created_at']

            if first_message_time and last_message_time:
                duration = last_message_time - first_message_time
                duration_seconds = int(duration.total_seconds())

        # 要約の有無を確認
        last_summary = await self.summary_repo.get_latest(user_id, session_id)
        has_summary = last_summary is not None
        last_summary_time = last_summary.updated_at if last_summary else None

        return SessionStats(
            session_id=session_id,
            message_count=message_count,
            first_message_time=first_message_time,
            last_message_time=last_message_time,
            duration_seconds=duration_seconds,
            has_summary=has_summary,
            last_summary_time=last_summary_time,
        )
