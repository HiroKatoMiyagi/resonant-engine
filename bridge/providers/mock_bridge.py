"""Mock bridge implementations for testing."""

from __future__ import annotations

import asyncio
import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bridge.core.ai_bridge import AIBridge
from bridge.core.data_bridge import DataBridge
from bridge.core.feedback_bridge import FeedbackBridge


class MockDataBridge(DataBridge):
    """インメモリでIntent/Messageを扱うDataBridge。"""

    def __init__(self) -> None:
        super().__init__()
        self._intents: Dict[str, Dict[str, Any]] = {}
        self._messages: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def connect(self) -> None:  # type: ignore[override]
        await super().connect()

    async def disconnect(self) -> None:  # type: ignore[override]
        async with self._lock:
            self._intents.clear()
            self._messages.clear()
        await super().disconnect()

    async def save_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        status: str = "pending",
        source: str = "auto_generated",
        user_id: Optional[str] = None,
    ) -> str:
        intent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "id": intent_id,
            "type": intent_type,
            "status": status,
            "data": copy.deepcopy(data),
            "source": source,
            "user_id": user_id,
            "feedback": None,
            "reevaluation": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }
        async with self._lock:
            self._intents[intent_id] = payload
        return intent_id

    async def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            intent = self._intents.get(intent_id)
            return copy.deepcopy(intent) if intent else None

    async def get_pending_intents(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        async with self._lock:
            pending = [i for i in self._intents.values() if i["status"] == "pending"]
        pending.sort(key=lambda item: item["created_at"])
        slice_items = pending[offset : offset + limit]
        return [copy.deepcopy(item) for item in slice_items]

    async def update_intent_status(
        self,
        intent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        async with self._lock:
            intent = self._intents.get(intent_id)
            if not intent:
                return False
            intent["status"] = status
            intent["updated_at"] = datetime.now(timezone.utc).isoformat()
            if result is not None:
                intent.setdefault("result", copy.deepcopy(result))
        return True

    async def save_feedback(
        self,
        intent_id: str,
        feedback_data: Dict[str, Any],
    ) -> bool:
        async with self._lock:
            intent = self._intents.get(intent_id)
            if not intent:
                return False
            intent["feedback"] = copy.deepcopy(feedback_data)
            intent["status"] = "waiting_reevaluation"
            intent["updated_at"] = datetime.now(timezone.utc).isoformat()
        return True

    async def get_pending_reevaluations(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        async with self._lock:
            reevaluations = [
                i for i in self._intents.values() if i["status"] == "waiting_reevaluation"
            ]
        reevaluations.sort(key=lambda item: item["updated_at"])
        slice_items = reevaluations[:limit]
        return [copy.deepcopy(item) for item in slice_items]

    async def save_reevaluation(
        self,
        intent_id: str,
        reevaluation_data: Dict[str, Any],
    ) -> bool:
        async with self._lock:
            intent = self._intents.get(intent_id)
            if not intent:
                return False
            intent["reevaluation"] = copy.deepcopy(reevaluation_data)
            intent["updated_at"] = datetime.now(timezone.utc).isoformat()
        return True

    async def update_reevaluation_status(
        self,
        intent_id: str,
        status: str,
        judgment: str,
        reason: str,
    ) -> bool:
        async with self._lock:
            intent = self._intents.get(intent_id)
            if not intent:
                return False
            intent["status"] = status
            intent["updated_at"] = datetime.now(timezone.utc).isoformat()
            if status == "approved":
                intent["completed_at"] = datetime.now(timezone.utc).isoformat()
            if intent.get("reevaluation") is None:
                intent["reevaluation"] = {}
            intent["reevaluation"]["yuno_judgment"] = judgment
            intent["reevaluation"]["reason"] = reason
        return True

    async def save_message(
        self,
        content: str,
        sender: str,
        intent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        message_id = str(uuid.uuid4())
        entry = {
            "id": message_id,
            "content": content,
            "sender": sender,
            "intent_id": intent_id,
            "thread_id": thread_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        async with self._lock:
            self._messages.append(entry)
        return message_id

    async def get_messages(
        self,
        limit: int = 50,
        thread_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        async with self._lock:
            if thread_id:
                filtered = [m for m in self._messages if m["thread_id"] == thread_id]
            else:
                filtered = list(self._messages)
        filtered.sort(key=lambda item: item["created_at"], reverse=True)
        slice_items = filtered[:limit]
        return [copy.deepcopy(item) for item in slice_items]


class MockAIBridge(AIBridge):
    """ダミーのAIBridge。"""

    def __init__(self, static_response: str = "Mock response") -> None:
        self.static_response = static_response

    async def call_ai(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        return f"{self.static_response}: {prompt}"

    async def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "model": "mock-model",
        }


class MockFeedbackBridge(FeedbackBridge):
    """YunoレスポンスをモックするFeedbackBridge。"""

    def __init__(self, judgment: str = "approved") -> None:
        self.judgment = judgment

    async def request_reevaluation(
        self,
        intent_id: str,
        intent_data: Dict[str, Any],
        feedback_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        return {
            "yuno_judgment": self.judgment,
            "yuno_response": "mock-response",
            "yuno_model": "mock-yuno",
            "evaluation_score": 0.9,
            "evaluation_criteria": {
                "intent_alignment": 0.9,
                "code_quality": 0.9,
                "test_coverage": 0.9,
                "documentation": 0.9,
            },
            "improvement_suggestions": ["Add more tests"],
            "reason": "Mock evaluation",
            "reevaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_reevaluation_status(self, intent_id: str) -> Optional[str]:
        return self.judgment
