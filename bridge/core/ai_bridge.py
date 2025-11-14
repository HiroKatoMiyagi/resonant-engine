"""Abstract AI bridge for Bridge Lite."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIBridge(ABC):
    """AI API呼び出しを抽象化するBridge。"""

    @abstractmethod
    async def call_ai(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """AI APIを呼び出して応答テキストを返す。"""

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """現在使用中のモデル情報を返す。"""
