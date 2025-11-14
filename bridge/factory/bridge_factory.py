"""Factory utilities for Bridge Lite components."""

from __future__ import annotations

import os
from typing import Optional

from bridge.core.audit_logger import AuditLogger
from bridge.core.ai_bridge import AIBridge
from bridge.core.data_bridge import DataBridge
from bridge.core.feedback_bridge import FeedbackBridge
from bridge.providers.claude_bridge import ClaudeBridge
from bridge.providers.mock_bridge import (
    MockAIBridge,
    MockDataBridge,
    MockFeedbackBridge,
)
from bridge.providers.postgresql_bridge import PostgreSQLBridge
from bridge.providers.yuno_feedback_bridge import YunoFeedbackBridge


class BridgeFactory:
    """Bridge実装を環境変数ベースで生成するファクトリ。"""

    @staticmethod
    def create_data_bridge(
        bridge_type: Optional[str] = None,
    ) -> DataBridge:
        bridge_key = (bridge_type or os.getenv("DATA_BRIDGE_TYPE", "mock")).lower()
        if bridge_key == "postgresql":
            return PostgreSQLBridge()
        if bridge_key == "mock":
            return MockDataBridge()
        raise ValueError(f"Unsupported DATA_BRIDGE_TYPE: {bridge_key}")

    @staticmethod
    def create_ai_bridge(
        bridge_type: Optional[str] = None,
    ) -> AIBridge:
        bridge_key = (bridge_type or os.getenv("AI_BRIDGE_TYPE", "mock")).lower()
        if bridge_key == "claude":
            return ClaudeBridge()
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
    def create_audit_logger() -> AuditLogger:
        return AuditLogger()
