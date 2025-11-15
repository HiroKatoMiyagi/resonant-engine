"""In-memory DataBridge implementation for tests and local development."""

from __future__ import annotations

import asyncio
import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from bridge.core.data_bridge import DataBridge
from bridge.core.enums import IntentStatus
from bridge.core.models.intent_model import CorrectionRecord, IntentModel
from bridge.core.constants import PhilosophicalActor


class MockDataBridge(DataBridge):
    """A simple in-memory store following the Bridge Lite spec."""

    def __init__(self) -> None:
        super().__init__()
        self._intents: Dict[str, IntentModel] = {}
        self._corrections: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def connect(self) -> None:  # type: ignore[override]
        await super().connect()

    async def disconnect(self) -> None:  # type: ignore[override]
        async with self._lock:
            self._intents.clear()
            self._corrections.clear()
        await super().disconnect()

    async def save_intent(self, intent: IntentModel) -> IntentModel:
        now = datetime.now(timezone.utc)
        base = intent.model_copy(deep=True)
        created_at = base.created_at or now
        updated = base.model_copy(
            update={
                "created_at": created_at,
                "updated_at": base.updated_at or now,
                "correction_history": copy.deepcopy(base.correction_history),
            },
            deep=True,
        )
        async with self._lock:
            self._intents[updated.intent_id] = updated
        return updated.model_copy(deep=True)

    async def get_intent(self, intent_id: str) -> IntentModel:
        async with self._lock:
            intent = self._intents.get(intent_id)
            if intent is None:
                raise KeyError(f"intent not found: {intent_id}")
            return intent.model_copy(deep=True)

    async def save_correction(self, intent_id: str, correction: Dict[str, Any]) -> IntentModel:
        entry = copy.deepcopy(correction)
        applied_at = entry.get("applied_at")
        if applied_at is None:
            applied_at = datetime.now(timezone.utc)
        entry.setdefault("applied_at", applied_at)
        entry.setdefault("source", entry.get("source") or PhilosophicalActor.KANA.value)
        entry.setdefault("diff", entry.get("diff") or entry.get("payload") or {})
        record = CorrectionRecord.model_validate(entry)
        async with self._lock:
            if intent_id not in self._intents:
                raise KeyError(f"intent not found: {intent_id}")
            intent = self._intents[intent_id]
            if any(item.correction_id == record.correction_id for item in intent.correction_history):
                return intent.model_copy(deep=True)

            corrections = list(intent.correction_history)
            corrections.append(record)
            status = IntentModel._coerce_status(
                correction.get("status", IntentStatus.CORRECTED)
            )
            updated = intent.with_updates(
                correction_history=corrections,
                status=status,
                updated_at=record.applied_at,
                version=intent.version + 1,
            )
            self._intents[intent_id] = updated
            self._corrections.append(
                {"intent_id": intent_id, **record.model_dump(exclude_none=True)}
            )
            return updated.model_copy(deep=True)

    async def update_intent(self, intent: IntentModel) -> IntentModel:
        async with self._lock:
            if intent.intent_id not in self._intents:
                raise KeyError(f"intent not found: {intent.intent_id}")
            stored = intent.model_copy(deep=True)
            self._intents[intent.intent_id] = stored
            return stored.model_copy(deep=True)

    async def list_intents(self, status: Optional[IntentStatus] = None) -> List[IntentModel]:
        async with self._lock:
            intents = list(self._intents.values())
        if status is not None:
            intents = [item for item in intents if item.status == status]
        intents.sort(key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc))
        return [intent.model_copy(deep=True) for intent in intents]

    async def update_intent_status(self, intent_id: str, status: Union[IntentStatus, str]) -> IntentModel:
        async with self._lock:
            if intent_id not in self._intents:
                raise KeyError(f"intent not found: {intent_id}")
            status_value = IntentModel._coerce_status(status)
            updated = self._intents[intent_id].with_updates(
                status=status_value,
                updated_at=datetime.now(timezone.utc),
            )
            self._intents[intent_id] = updated
            return updated.model_copy(deep=True)
