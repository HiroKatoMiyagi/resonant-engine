"""Feedback bridge abstraction per Bridge Lite spec v2.0."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from bridge.core.clients.reeval_client import ReEvalClient
    from bridge.core.models.intent_model import IntentModel


class FeedbackBridge(ABC):
    """Yuno による再評価フェーズのインターフェース。"""

    def __init__(self, reeval_client: Optional["ReEvalClient"] = None) -> None:
        self._reeval_client = reeval_client

    def attach_reeval_client(self, client: "ReEvalClient") -> None:
        """Attach a re-evaluation client after construction."""

        self._reeval_client = client

    @property
    def reeval_client(self) -> Optional["ReEvalClient"]:
        """Return the configured re-evaluation client if available."""

        return self._reeval_client

    @abstractmethod
    async def request_reevaluation(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """簡易的な再評価を実行し結果を返す (Phase 1)。"""

    @abstractmethod
    async def submit_feedback(self, intent_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックを登録し、必要に応じて一次応答を返す。"""

    @abstractmethod
    async def reanalyze(self, intent: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Intent と履歴から再評価結果を生成する。"""

    @abstractmethod
    async def generate_correction(
        self,
        intent: Dict[str, Any],
        feedback_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """再評価結果をもとに Correction Plan を構築する。"""

    async def execute(self, intent: "IntentModel") -> "IntentModel":
        """Optional hook for bridges that can trigger re-evaluation directly."""

        return intent
