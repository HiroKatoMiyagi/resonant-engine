"""Summarization Service - 会話要約生成サービス"""

import os
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from anthropic import AsyncAnthropic

from memory_store.session_summary_repository import SessionSummaryRepository
from memory_store.models import SessionSummaryResponse
from session.config import SessionConfig, get_default_session_config


class SummarizationService:
    """会話要約生成サービス"""

    def __init__(
        self,
        summary_repo: SessionSummaryRepository,
        config: Optional[SessionConfig] = None,
        claude_client: Optional[AsyncAnthropic] = None,
    ):
        self.summary_repo = summary_repo
        self.config = config or get_default_session_config()
        self.claude_client = claude_client or self._create_claude_client()

    def _create_claude_client(self) -> AsyncAnthropic:
        """Claude APIクライアントを作成"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        return AsyncAnthropic(api_key=api_key)

    async def create_summary(
        self,
        user_id: str,
        session_id: UUID,
        messages: List[dict],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> SessionSummaryResponse:
        """
        セッションの要約を生成

        Args:
            user_id: ユーザーID
            session_id: セッションID
            messages: メッセージリスト（辞書形式）
            start_time: セッション開始時刻（Noneの場合は自動計算）
            end_time: セッション終了時刻（Noneの場合は現在時刻）

        Returns:
            SessionSummaryResponse: 生成された要約

        Raises:
            ValueError: メッセージが存在しない場合
        """
        if not messages:
            raise ValueError(f"No messages found for session {session_id}")

        # 時刻情報を計算
        actual_start_time = start_time or self._extract_start_time(messages)
        actual_end_time = end_time or self._extract_end_time(messages)

        # Claude APIで要約生成
        summary_text = await self._generate_summary_with_claude(messages)

        # 要約を保存
        summary_id = await self.summary_repo.save(
            user_id=user_id,
            session_id=session_id,
            summary=summary_text,
            message_count=len(messages),
            start_time=actual_start_time,
            end_time=actual_end_time,
        )

        # 保存された要約を返す
        return await self.summary_repo.get_by_session(session_id)

    def _extract_start_time(self, messages: List[dict]) -> datetime:
        """メッセージリストから開始時刻を抽出"""
        if messages and 'created_at' in messages[0]:
            return messages[0]['created_at']
        return datetime.now()

    def _extract_end_time(self, messages: List[dict]) -> datetime:
        """メッセージリストから終了時刻を抽出"""
        if messages and 'created_at' in messages[-1]:
            return messages[-1]['created_at']
        return datetime.now()

    async def _generate_summary_with_claude(
        self,
        messages: List[dict],
    ) -> str:
        """Claude APIで要約生成"""
        prompt = self._build_summarization_prompt(messages)

        response = await self.claude_client.messages.create(
            model=self.config.claude_model,
            max_tokens=self.config.claude_max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.content[0].text

    def _build_summarization_prompt(
        self,
        messages: List[dict],
    ) -> str:
        """要約生成用プロンプトを構築"""
        # メッセージを整形
        conversation = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])

        # 時刻情報
        start_time = self._extract_start_time(messages).strftime("%Y-%m-%d %H:%M")
        end_time = self._extract_end_time(messages).strftime("%Y-%m-%d %H:%M")

        return f"""以下の会話セッションを要約してください。

要約の要件:
1. 3-5文の簡潔な要約
2. 主要なトピック、決定事項、成果を含める
3. 次のステップや未解決の課題があれば記載
4. 日時情報を含める（{start_time} - {end_time}）
5. 技術的な詳細は省略し、高レベルな概要を提供

会話（{len(messages)}メッセージ）:
{conversation}

要約（3-5文、日本語）:"""
