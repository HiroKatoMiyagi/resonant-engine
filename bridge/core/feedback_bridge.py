"""Abstract feedback bridge for Bridge Lite."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class FeedbackBridge(ABC):
    """Yuno再評価などのフィードバック処理を抽象化する。"""

    @abstractmethod
    async def request_reevaluation(
        self,
        intent_id: str,
        intent_data: Dict[str, Any],
        feedback_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Yunoへ再評価リクエストを送信し結果を返す。"""

    @abstractmethod
    async def get_reevaluation_status(self, intent_id: str) -> Optional[str]:
        """再評価ステータスを取得する。"""
