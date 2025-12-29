"""Context Assembler Service - コンテキスト組み立てサービス"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from memory_store.models import MemoryResult
from backend.app.models.message import MessageResponse
from backend.app.repositories.message_repo import MessageRepository
from app.services.memory.repositories import SessionRepository
from retrieval.orchestrator import RetrievalOrchestrator, RetrievalOptions

from .models import (
    AssembledContext,
    AssemblyOptions,
    ContextConfig,
    ContextMetadata,
)
from .token_estimator import TokenEstimator

# Sprint 7: Session Summary support
try:
    from memory_store.session_summary_repository import SessionSummaryRepository
    HAS_SESSION_SUMMARY = True
except ImportError:
    HAS_SESSION_SUMMARY = False

# Sprint 8: User Profile support
try:
    from user_profile.context_provider import ProfileContextProvider
    HAS_USER_PROFILE = True
except ImportError:
    HAS_USER_PROFILE = False

# Sprint 10: Choice Preservation support
try:
    from app.services.memory.choice_engine import ChoiceQueryEngine
    HAS_CHOICE_QUERY = True
except ImportError:
    HAS_CHOICE_QUERY = False


class ContextAssemblerService:
    """
    コンテキスト組み立てサービス

    Retrieval Orchestratorからの記憶と直近の会話履歴を統合し、
    Claude APIに渡す最適なコンテキストを構築します。
    """

    def __init__(
        self,
        retrieval_orchestrator: RetrievalOrchestrator,
        message_repository: MessageRepository,
        session_repository: SessionRepository,
        config: ContextConfig,
        session_summary_repository: Optional['SessionSummaryRepository'] = None,
        profile_context_provider: Optional['ProfileContextProvider'] = None,
        choice_query_engine: Optional['ChoiceQueryEngine'] = None,
    ):
        self.retrieval = retrieval_orchestrator
        self.message_repo = message_repository
        self.session_repo = session_repository
        self.config = config
        self.token_estimator = TokenEstimator()
        # Sprint 7: Session Summary Repository
        self.summary_repo = session_summary_repository
        # Sprint 8: User Profile Context Provider
        self.profile_provider = profile_context_provider
        # Sprint 10: Choice Query Engine
        self.choice_query_engine = choice_query_engine

    async def assemble_context(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[UUID] = None,
        options: Optional[AssemblyOptions] = None,
    ) -> AssembledContext:
        """
        コンテキストを組み立てる

        Args:
            user_message: 現在のユーザーメッセージ
            user_id: ユーザーID
            session_id: セッションID（オプション）
            options: 組み立てオプション

        Returns:
            AssembledContext: メッセージリスト + メタデータ + プロフィールコンテキスト
        """
        start_time = time.time()
        options = options or AssemblyOptions()

        # 0. User Profile取得（Sprint 8）
        profile_context = None
        if options.include_user_profile and self.profile_provider:
            try:
                profile_context = await self.profile_provider.get_profile_context(
                    user_id=user_id,
                    include_family=options.include_family,
                    include_goals=options.include_goals,
                )
                if profile_context:
                    import logging
                    logging.info(f"✅ Profile context loaded: {profile_context.token_count} tokens")
            except Exception as e:
                import logging
                logging.warning(f"Failed to load profile context: {e}")

        # 1. メモリ階層を取得
        memory_layers = await self._fetch_memory_layers(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            options=options,
        )

        # 2. メッセージリストを構築（Profile統合）
        messages = self._build_messages(memory_layers, user_message, profile_context)

        # 3. トークン数を推定
        total_tokens = self.token_estimator.estimate(messages)

        # 4. トークン上限チェックと圧縮
        compression_applied = False
        if total_tokens > self._get_token_limit():
            messages, total_tokens = self._compress_context(
                messages, memory_layers, user_message, profile_context
            )
            compression_applied = True

        # 5. 検証
        self._validate_context(messages, total_tokens)

        assembly_time = (time.time() - start_time) * 1000

        # 6. メタデータ構築（Sprint 8: Profile情報追加、Sprint 10: Choice追加）
        metadata = ContextMetadata(
            working_memory_count=len(memory_layers.get("working", [])),
            semantic_memory_count=len(memory_layers.get("semantic", [])),
            has_session_summary=memory_layers.get("session_summary") is not None,
            total_tokens=total_tokens,
            token_limit=self._get_token_limit(),
            compression_applied=compression_applied,
            assembly_latency_ms=assembly_time,
            # Sprint 8: User Profile metadata
            has_user_profile=profile_context is not None,
            profile_token_count=profile_context.token_count if profile_context else 0,
            # Sprint 10: Choice Preservation metadata
            past_choices_count=len(memory_layers.get("past_choices", [])),
        )

        return AssembledContext(
            messages=messages,
            metadata=metadata,
            profile_context=profile_context,
        )

    async def _fetch_memory_layers(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[UUID],
        options: AssemblyOptions,
    ) -> Dict[str, Any]:
        """メモリ階層を並行取得"""
        tasks = []

        # Working Memory（直近の会話）
        tasks.append(
            self._fetch_working_memory(
                user_id=user_id,
                limit=options.working_memory_limit
                or self.config.working_memory_limit,
            )
        )

        # Semantic Memory（関連記憶）
        if options.include_semantic_memory:
            tasks.append(
                self._fetch_semantic_memory(
                    query=user_message,
                    limit=options.semantic_memory_limit
                    or self.config.semantic_memory_limit,
                )
            )
        else:
            # ダミータスク（空リストを返す）
            async def empty_task():
                return []
            tasks.append(empty_task())

        # Session Summary
        if session_id and options.include_session_summary:
            tasks.append(self._fetch_session_summary(user_id, session_id))
        else:
            # ダミータスク（Noneを返す）
            async def empty_summary():
                return None
            tasks.append(empty_summary())

        # Sprint 10: Past Choices
        if options.include_past_choices:
            tasks.append(self._fetch_past_choices(user_id, user_message, options.past_choices_limit))
        else:
            # ダミータスク（空リストを返す）
            async def empty_choices():
                return []
            tasks.append(empty_choices())

        # 並行実行
        working, semantic, summary, past_choices = await asyncio.gather(*tasks)

        return {
            "working": working,
            "semantic": semantic,
            "session_summary": summary,
            "past_choices": past_choices,
        }

    async def _fetch_working_memory(
        self, user_id: str, limit: int
    ) -> List[MessageResponse]:
        """Working Memory: 直近N件の会話"""
        messages, _ = await self.message_repo.list(user_id=user_id, limit=limit)
        # 時系列順（古い→新しい）に並び替え
        return list(reversed(messages))

    async def _fetch_semantic_memory(
        self, query: str, limit: int
    ) -> List[MemoryResult]:
        """Semantic Memory: 関連する記憶をベクトル検索"""
        response = await self.retrieval.retrieve(
            query=query, options=RetrievalOptions(limit=limit, log_metrics=False)
        )
        return response.results

    async def _fetch_session_summary(self, user_id: str, session_id: UUID) -> Optional[str]:
        """
        Session Summary: セッションの要約を取得

        Sprint 7: SessionSummaryRepositoryから取得（優先）
        Fallback: SessionRepositoryのmetadataから取得
        """
        # Sprint 7: SessionSummaryRepositoryから取得
        if self.summary_repo:
            try:
                summary = await self.summary_repo.get_latest(user_id, session_id)
                if summary:
                    return summary.summary
            except Exception as e:
                import logging
                logging.warning(f"Failed to fetch session summary: {e}")

        # Fallback: 既存のSessionRepositoryから取得
        session = await self.session_repo.get_by_id(session_id)
        if session and session.metadata:
            return session.metadata.get("summary")
        return None

    async def _fetch_past_choices(self, user_id: str, current_question: str, limit: int) -> List:
        """
        Past Choices: 過去の選択履歴を取得（Sprint 10）

        現在の質問に関連する過去の選択を取得して、
        コンテキストに含めることで一貫した意思決定を支援します。
        """
        if not self.choice_query_engine:
            return []

        try:
            past_choices = await self.choice_query_engine.get_relevant_choices_for_context(
                user_id=user_id,
                current_question=current_question,
                limit=limit
            )
            return past_choices
        except Exception as e:
            import logging
            logging.warning(f"Failed to fetch past choices: {e}")
            return []

    def _build_messages(
        self,
        memory_layers: Dict[str, Any],
        user_message: str,
        profile_context: Optional['ProfileContext'] = None,
    ) -> List[Dict[str, str]]:
        """Claude APIに渡すメッセージリストを構築（Sprint 8: Profile統合）"""
        messages = []

        # 1. System Prompt（Sprint 8: Profile統合）
        system_parts = [self.config.system_prompt]

        # Sprint 8: User Profile調整
        if profile_context and profile_context.system_prompt_adjustment:
            system_parts.append("\n")
            system_parts.append(profile_context.system_prompt_adjustment)

        # Sprint 8: User Profile コンテキストセクション
        if profile_context and profile_context.context_section:
            system_parts.append("\n")
            system_parts.append(profile_context.context_section)

        # Session Summary
        if memory_layers.get("session_summary"):
            system_parts.append(
                f"\n\n## セッション要約\n{memory_layers['session_summary']}"
            )

        # Sprint 10: Past Decision History
        past_choices = memory_layers.get("past_choices", [])
        if past_choices:
            system_parts.append("\n\n## 過去の意思決定履歴\n")
            system_parts.append("以下は、あなたが過去に行った類似の意思決定です。一貫性を保つために参考にしてください。\n\n")
            for i, cp in enumerate(past_choices, 1):
                # 選択された選択肢
                selected_choice = next((c for c in cp.choices if c.id == cp.selected_choice_id), None)
                if selected_choice:
                    system_parts.append(f"{i}. **{cp.question}**\n")
                    system_parts.append(f"   - 選択: {selected_choice.description}\n")
                    if cp.decision_rationale:
                        system_parts.append(f"   - 理由: {cp.decision_rationale}\n")

                    # 却下された選択肢（理由がある場合）
                    rejected_choices = [c for c in cp.choices if c.id != cp.selected_choice_id and c.rejection_reason]
                    if rejected_choices:
                        system_parts.append("   - 却下した選択肢:\n")
                        for rc in rejected_choices:
                            system_parts.append(f"     • {rc.description}: {rc.rejection_reason}\n")

                    if cp.decided_at:
                        system_parts.append(f"   - 決定日: {cp.decided_at.strftime('%Y-%m-%d')}\n")
                    system_parts.append("\n")

        system_content = "".join(system_parts)
        messages.append({"role": "system", "content": system_content})

        # 2. Semantic Memory
        semantic_memories = memory_layers.get("semantic", [])
        if semantic_memories:
            memory_text = "## 関連する過去の記憶\n\n"
            for i, mem in enumerate(semantic_memories[:3], 1):
                memory_text += (
                    f"{i}. {mem.content} (関連度: {mem.similarity:.2f})\n"
                )

            messages.append({"role": "assistant", "content": memory_text})

        # 3. Working Memory
        working_messages = memory_layers.get("working", [])
        for msg in working_messages[-5:]:  # 直近5件
            role = self._map_message_type_to_role(msg.message_type)
            if role:  # systemは除外
                messages.append({"role": role, "content": msg.content})

        # 4. Current User Message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _map_message_type_to_role(self, message_type: str) -> Optional[str]:
        """MessageTypeをClaude API roleにマッピング"""
        mapping = {
            "user": "user",
            "kana": "assistant",
            "yuno": "assistant",
            "system": None,  # systemメッセージは除外
        }
        return mapping.get(message_type.lower())

    def _compress_context(
        self,
        messages: List[Dict[str, str]],
        memory_layers: Dict[str, Any],
        user_message: str,
        profile_context: Optional['ProfileContext'] = None,
    ) -> Tuple[List[Dict[str, str]], int]:
        """トークン上限を超えた場合にコンテキストを圧縮（Sprint 8: Profile考慮、Sprint 10: Choice考慮）"""
        compressed_layers = memory_layers.copy()

        # Phase 1: Session Summary削除
        if compressed_layers.get("session_summary"):
            compressed_layers["session_summary"] = None
            messages = self._build_messages(compressed_layers, user_message, profile_context)
            tokens = self.token_estimator.estimate(messages)
            if tokens <= self._get_token_limit():
                return messages, tokens

        # Phase 2: Past Choices削減（Sprint 10）
        past_choices = compressed_layers.get("past_choices", [])
        while len(past_choices) > 1:
            past_choices = past_choices[:-1]  # 最後（関連度が低い）から削除
            compressed_layers["past_choices"] = past_choices
            messages = self._build_messages(compressed_layers, user_message, profile_context)
            tokens = self.token_estimator.estimate(messages)
            if tokens <= self._get_token_limit():
                return messages, tokens

        # Phase 3: Semantic Memory削減
        semantic = compressed_layers.get("semantic", [])
        while len(semantic) > 1:
            semantic = semantic[:-1]  # 最後（類似度が低い）から削除
            compressed_layers["semantic"] = semantic
            messages = self._build_messages(compressed_layers, user_message, profile_context)
            tokens = self.token_estimator.estimate(messages)
            if tokens <= self._get_token_limit():
                return messages, tokens

        # Phase 4: Working Memory削減
        working = compressed_layers.get("working", [])
        while len(working) > 2:  # 最低2件は残す
            working = working[1:]  # 最初（古い）から削除
            compressed_layers["working"] = working
            messages = self._build_messages(compressed_layers, user_message, profile_context)
            tokens = self.token_estimator.estimate(messages)
            if tokens <= self._get_token_limit():
                return messages, tokens

        # それでも超過する場合は現状を返す
        # Note: User Profileは削除しない（認知特性への配慮は必須）
        return messages, tokens

    def _get_token_limit(self) -> int:
        """トークン上限を計算（安全マージン考慮）"""
        return int(self.config.max_tokens * self.config.token_safety_margin)

    def _validate_context(
        self, messages: List[Dict[str, str]], total_tokens: int
    ) -> None:
        """コンテキストの妥当性を検証"""
        # 1. メッセージが空でないか
        if not messages:
            raise ValueError("Messages cannot be empty")

        # 2. 最初のメッセージがsystemか
        if messages[0].get("role") != "system":
            raise ValueError("First message must be system prompt")

        # 3. 最後のメッセージがuserか
        if messages[-1].get("role") != "user":
            raise ValueError("Last message must be user message")

        # 4. role/contentが存在するか
        for i, msg in enumerate(messages):
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"Message {i} missing role or content")
            if not msg["content"]:
                raise ValueError(f"Message {i} has empty content")

        # 5. トークン数が上限を超えていないか（警告のみ）
        if total_tokens > self.config.max_tokens:
            import warnings

            warnings.warn(
                f"Total tokens {total_tokens} exceeds max {self.config.max_tokens}"
            )
