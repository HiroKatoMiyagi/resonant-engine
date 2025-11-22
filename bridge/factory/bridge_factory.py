"""Factory utilities for Bridge Lite components."""

from __future__ import annotations

import os
from typing import Any, Optional

import asyncpg

from bridge.core.ai_bridge import AIBridge
from bridge.core.audit_logger import AuditLogger
from bridge.core.bridge_set import BridgeSet
from bridge.core.data_bridge import DataBridge
from bridge.core.feedback_bridge import FeedbackBridge
from bridge.core.reeval_client import ReEvalClient
from bridge.providers.ai import KanaAIBridge, MockAIBridge
from bridge.providers.audit import MockAuditLogger, PostgresAuditLogger
from bridge.providers.data import MockDataBridge, PostgresDataBridge
from bridge.providers.feedback import MockFeedbackBridge, YunoFeedbackBridge


class BridgeFactory:
    """Bridge実装を環境変数ベースで生成するファクトリ。"""

    @staticmethod
    def create_data_bridge(
        bridge_type: Optional[str] = None,
    ) -> DataBridge:
        bridge_key = (bridge_type or os.getenv("DATA_BRIDGE_TYPE", "mock")).lower()
        if bridge_key in {"postgresql", "postgres", "pg"}:
            return PostgresDataBridge()
        if bridge_key == "mock":
            return MockDataBridge()
        raise ValueError(f"Unsupported DATA_BRIDGE_TYPE: {bridge_key}")

    @staticmethod
    def create_ai_bridge(
        bridge_type: Optional[str] = None,
    ) -> AIBridge:
        bridge_key = (bridge_type or os.getenv("AI_BRIDGE_TYPE", "kana")).lower()
        if bridge_key in {"kana", "claude"}:
            return KanaAIBridge()
        if bridge_key == "mock":
            return MockAIBridge()
        raise ValueError(f"Unsupported AI_BRIDGE_TYPE: {bridge_key}")

    @staticmethod
    async def create_ai_bridge_with_memory(
        bridge_type: Optional[str] = None,
        pool: Optional[asyncpg.Pool] = None,
    ) -> AIBridge:
        """
        Context Assembler統合版のAI Bridgeを生成

        Args:
            bridge_type: "kana", "claude", "mock"（デフォルト: 環境変数AI_BRIDGE_TYPE）
            pool: PostgreSQL接続プール（Noneの場合はFactoryが新規作成）

        Returns:
            AIBridge: Context Assembler統合済みのAI Bridge

        Raises:
            ValueError: 未対応のbridge_type
            ConnectionError: Context Assembler初期化失敗

        Example:
            >>> bridge = await BridgeFactory.create_ai_bridge_with_memory("kana")
            >>> result = await bridge.process_intent({
            ...     "content": "Memory Storeについて教えて",
            ...     "user_id": "hiroki"
            ... })
        """
        from context_assembler.factory import create_context_assembler

        bridge_key = (bridge_type or os.getenv("AI_BRIDGE_TYPE", "kana")).lower()

        if bridge_key in {"kana", "claude"}:
            # Context Assembler初期化
            try:
                context_assembler = await create_context_assembler(pool=pool)
            except (ConnectionError, ValueError, ImportError) as e:
                # Context Assembler初期化失敗 → Fallback（Context Assemblerなし）
                import warnings

                warnings.warn(
                    f"Context Assembler initialization failed: {e}. "
                    f"Falling back to KanaAIBridge without context memory."
                )
                return KanaAIBridge()  # context_assembler=None

            return KanaAIBridge(context_assembler=context_assembler)

        if bridge_key == "mock":
            # Mockは従来通り（Context Assemblerなし）
            return MockAIBridge()

        raise ValueError(f"Unsupported AI_BRIDGE_TYPE: {bridge_key}")

    @staticmethod
    def create_contradiction_detector(
        pool: asyncpg.Pool,
    ) -> Any:
        """
        Sprint 11: Contradiction Detector生成

        Args:
            pool: PostgreSQL接続プール

        Returns:
            ContradictionDetector: 矛盾検出サービス

        Example:
            >>> detector = BridgeFactory.create_contradiction_detector(pool)
            >>> contradictions = await detector.check_new_intent(
            ...     user_id="hiroki",
            ...     new_intent_id=intent_id,
            ...     new_intent_content="Use SQLite database"
            ... )
        """
        from bridge.contradiction.detector import ContradictionDetector

        return ContradictionDetector(pool=pool)

    @staticmethod
    def create_feedback_bridge(
        bridge_type: Optional[str] = None,
        *,
        reeval_client: Optional[ReEvalClient] = None,
    ) -> FeedbackBridge:
        bridge_key = (bridge_type or os.getenv("FEEDBACK_BRIDGE_TYPE", "mock")).lower()
        if bridge_key == "yuno":
            return YunoFeedbackBridge(reeval_client=reeval_client)
        if bridge_key == "mock":
            return MockFeedbackBridge(reeval_client=reeval_client)
        raise ValueError(f"Unsupported FEEDBACK_BRIDGE_TYPE: {bridge_key}")

    @staticmethod
    def create_audit_logger(logger_type: Optional[str] = None) -> AuditLogger:
        bridge_key = (logger_type or os.getenv("AUDIT_LOGGER_TYPE", "mock")).lower()
        if bridge_key in {"postgresql", "postgres", "pg"}:
            return PostgresAuditLogger()
        if bridge_key == "mock":
            return MockAuditLogger()
        raise ValueError(f"Unsupported AUDIT_LOGGER_TYPE: {bridge_key}")

    @staticmethod
    def create_all(
        *,
        data_bridge: Optional[str] = None,
        ai_bridge: Optional[str] = None,
        feedback_bridge: Optional[str] = None,
        audit_logger: Optional[str] = None,
    ) -> BridgeSet:
        """Construct a BridgeSet bundle using optional overrides for each component."""

        data = BridgeFactory.create_data_bridge(data_bridge)
        ai = BridgeFactory.create_ai_bridge(ai_bridge)
        audit = BridgeFactory.create_audit_logger(audit_logger)
        reeval_client = ReEvalClient(data, audit)
        feedback = BridgeFactory.create_feedback_bridge(
            feedback_bridge,
            reeval_client=reeval_client,
        )
        feedback.attach_reeval_client(reeval_client)
        return BridgeSet(data=data, ai=ai, feedback=feedback, audit=audit)

    @staticmethod
    def create_bridge_set(
        *,
        data_bridge: Optional[str] = None,
        ai_bridge: Optional[str] = None,
        feedback_bridge: Optional[str] = None,
        audit_logger: Optional[str] = None,
    ) -> BridgeSet:
        """Alias to :meth:`create_all` for callers expecting bridge set terminology."""

        return BridgeFactory.create_all(
            data_bridge=data_bridge,
            ai_bridge=ai_bridge,
            feedback_bridge=feedback_bridge,
            audit_logger=audit_logger,
        )
