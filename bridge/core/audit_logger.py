"""Audit logger abstraction for Bridge Lite."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from bridge.core.constants import AuditEventType, BridgeTypeEnum, LogSeverity


class AuditLogger(ABC):
    """Bridge Lite の監査ログ API を提供する抽象クラス。"""

    @abstractmethod
    async def log(
        self,
        bridge_type: BridgeTypeEnum,
        operation: str,
        details: Dict[str, Any],
        intent_id: Optional[str],
        correlation_id: Optional[str] = None,
        event: Optional[AuditEventType] = None,
        severity: LogSeverity = LogSeverity.INFO,
    ) -> None:
        """監査ログを記録する。"""

    @abstractmethod
    async def cleanup(self) -> None:
        """ログのローテーションや削除などのメンテナンスを行う。"""
