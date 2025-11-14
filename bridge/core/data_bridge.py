"""Abstract data access bridge for Bridge Lite."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DataBridge(ABC):
    """抽象データアクセスレイヤー。

    Intent/Messageストレージに対する操作を統一インターフェースで提供する。
    具体的な実装（PostgreSQL、Mockなど）はこの抽象クラスを継承する。
    """

    def __init__(self) -> None:
        self._connected: bool = False

    @property
    def is_connected(self) -> bool:
        """現在の接続状態を返す。"""

        return self._connected

    async def connect(self) -> None:
        """接続を初期化する。

        具体実装側で接続処理（プールの初期化など）を行う。
        デフォルトでは状態フラグのみを更新する。
        """

        self._connected = True

    async def disconnect(self) -> None:
        """接続を終了する。"""

        self._connected = False

    async def __aenter__(self) -> "DataBridge":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.disconnect()

    # ---- Intent CRUD -------------------------------------------------

    @abstractmethod
    async def save_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        status: str = "pending",
        source: str = "auto_generated",
        user_id: Optional[str] = None,
    ) -> str:
        """Intentを保存しIDを返す。"""

    @abstractmethod
    async def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        """IntentをIDで取得する。"""

    @abstractmethod
    async def get_pending_intents(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """処理待ちIntentの一覧を取得する。"""

    @abstractmethod
    async def update_intent_status(
        self,
        intent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Intentのステータスを更新する。"""

    # ---- Feedback / Reevaluation ------------------------------------

    @abstractmethod
    async def save_feedback(
        self,
        intent_id: str,
        feedback_data: Dict[str, Any],
    ) -> bool:
        """Kana処理後のフィードバックを保存する。"""

    @abstractmethod
    async def get_pending_reevaluations(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """再評価待ちIntentを取得する。"""

    @abstractmethod
    async def save_reevaluation(
        self,
        intent_id: str,
        reevaluation_data: Dict[str, Any],
    ) -> bool:
        """Yuno再評価データを保存する。"""

    @abstractmethod
    async def update_reevaluation_status(
        self,
        intent_id: str,
        status: str,
        judgment: str,
        reason: str,
    ) -> bool:
        """再評価後の最終ステータスを更新する。"""

    # ---- Message operations -----------------------------------------

    @abstractmethod
    async def save_message(
        self,
        content: str,
        sender: str,
        intent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        """メッセージを保存しIDを返す。"""

    @abstractmethod
    async def get_messages(
        self,
        limit: int = 50,
        thread_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """メッセージ一覧を取得する。"""
