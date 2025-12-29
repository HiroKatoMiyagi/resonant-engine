"""Abstract AI bridge aligned with Bridge Lite spec v2.0."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class AIBridge(ABC):
    """Kana などの AI プロバイダ呼び出しを抽象化する。"""

    @abstractmethod
    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Intent を受け取り、AI による一次解析結果を返す。"""
