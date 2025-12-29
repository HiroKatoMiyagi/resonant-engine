"""Bridge Lite data-access abstraction matching v2.0 specification."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Union, TYPE_CHECKING

from app.services.shared.constants import IntentStatusEnum
from .locks import LockedIntentSession

if TYPE_CHECKING:
    from app.models.intent import IntentModel


class DataBridge(ABC):
    """Intentと再評価情報を扱うストレージ層の抽象クラス。"""

    def __init__(self) -> None:
        self._connected = False

    async def connect(self) -> None:
        """必要なら接続を初期化する。"""

        self._connected = True

    async def disconnect(self) -> None:
        """接続を解放する。"""

        self._connected = False

    async def __aenter__(self) -> "DataBridge":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.disconnect()

    # ---- Required API (v2.0 spec) ----------------------------------

    @abstractmethod
    async def save_intent(self, intent: "IntentModel") -> "IntentModel":
        """Intent を保存し、永続化されたモデルを返す。"""

    @abstractmethod
    async def get_intent(self, intent_id: str) -> "IntentModel":
        """intent_id に対応する Intent モデルを取得する。"""

    @abstractmethod
    async def save_correction(self, intent_id: str, correction: Dict[str, Any]) -> "IntentModel":
        """再評価から生成された Correction Plan を保存し、Intent を更新して返す。"""

    @abstractmethod
    async def list_intents(self, status: Optional[IntentStatusEnum] = None) -> List["IntentModel"]:
        """Intent を状態などでフィルタして列挙する。"""

    @abstractmethod
    async def update_intent(self, intent: "IntentModel") -> "IntentModel":
        """Persist updates to an existing intent."""

    async def update_intent_status(
        self,
        intent_id: str,
        status: Union[IntentStatusEnum, str],
    ) -> "IntentModel":
        """Optionally update an intent status. Bridges should override when supported."""

        raise NotImplementedError("update_intent_status is not implemented for this data bridge")

    @abstractmethod
    async def update_intent_if_version_matches(
        self,
        intent_id: str,
        intent: "IntentModel",
        *,
        expected_version: int,
    ) -> bool:
        """Attempt to persist changes only when the intent version matches the expectation."""

    @abstractmethod
    def lock_intent_for_update(
        self,
        intent_id: str,
        *,
        timeout: float = 5.0,
    ) -> AsyncIterator["LockedIntentSession"]:
        """Acquire a pessimistic lock for exclusive operations."""
