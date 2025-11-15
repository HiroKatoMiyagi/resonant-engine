"""Factory utilities for Bridge Lite components."""

from __future__ import annotations

import os
from typing import Optional

from bridge.core.ai_bridge import AIBridge
from bridge.core.audit_logger import AuditLogger
from bridge.core.bridge_set import BridgeSet
from bridge.core.data_bridge import DataBridge
from bridge.core.feedback_bridge import FeedbackBridge
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
    def create_feedback_bridge(
        bridge_type: Optional[str] = None,
    ) -> FeedbackBridge:
        bridge_key = (bridge_type or os.getenv("FEEDBACK_BRIDGE_TYPE", "mock")).lower()
        if bridge_key == "yuno":
            return YunoFeedbackBridge()
        if bridge_key == "mock":
            return MockFeedbackBridge()
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
        feedback = BridgeFactory.create_feedback_bridge(feedback_bridge)
        audit = BridgeFactory.create_audit_logger(audit_logger)
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
