"""In-memory DataBridge implementation for tests and local development."""

from __future__ import annotations

import asyncio
import copy
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from app.services.shared.constants import PhilosophicalActor
from app.services.intent.data_bridge import DataBridge
from app.services.shared.constants import IntentStatusEnum as IntentStatus
from app.services.shared.errors import LockTimeoutError
from app.services.intent.locks import LockedIntentSession


class MockDataBridge(DataBridge):
    """A simple in-memory store following the Bridge Lite spec."""

    def __init__(self) -> None:
        super().__init__()
        self._intents: Dict[str, Any] = {}  # IntentModel
        self._corrections: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._intent_locks: Dict[str, asyncio.Lock] = {}
        self._active_sessions: Dict[str, LockedIntentSession] = {}
        self._lock_owners: Dict[str, asyncio.Task] = {}

    async def connect(self) -> None:  # type: ignore[override]
        await super().connect()

    async def disconnect(self) -> None:  # type: ignore[override]
        async with self._lock:
            self._intents.clear()
            self._corrections.clear()
        await super().disconnect()

    async def save_intent(self, intent: Any) -> Any:
        # Import here to avoid circular dependency
        from app.models.intent import IntentModel, CorrectionRecord
        
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

    async def get_intent(self, intent_id: str) -> Any:
        async with self._lock:
            intent = self._intents.get(intent_id)
            if intent is None:
                raise KeyError(f"intent not found: {intent_id}")
            return intent.model_copy(deep=True)

    async def save_correction(
        self,
        intent_id: str,
        correction: Dict[str, Any],
        *,
        persist_status: bool = True,
    ) -> Any:
        # Import here to avoid circular dependency
        from app.models.intent import IntentModel, CorrectionRecord
        
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
            status = intent.status
            version_delta = 0
            if persist_status:
                status = IntentModel._coerce_status(
                    correction.get("status", IntentStatus.CORRECTED)
                )
                version_delta = 1
            updated = intent.with_updates(
                correction_history=corrections,
                status=status,
                updated_at=record.applied_at,
                version=intent.version + version_delta,
            )
            self._intents[intent_id] = updated
            self._corrections.append(
                {"intent_id": intent_id, **record.model_dump(exclude_none=True)}
            )
            return updated.model_copy(deep=True)

    async def update_intent(self, intent: Any) -> Any:
        async with self._lock:
            if intent.intent_id not in self._intents:
                raise KeyError(f"intent not found: {intent.intent_id}")
            stored = intent.model_copy(deep=True)
            self._intents[intent.intent_id] = stored
            return stored.model_copy(deep=True)

    async def update_intent_if_version_matches(
        self,
        intent_id: str,
        intent: Any,
        *,
        expected_version: int,
    ) -> bool:
        async with self._lock:
            current = self._intents.get(intent_id)
            if current is None or current.version != expected_version:
                return False
            self._intents[intent_id] = intent.model_copy(deep=True)
            return True

    async def list_intents(self, status: Optional[IntentStatus] = None) -> List[Any]:
        async with self._lock:
            intents = list(self._intents.values())
        if status is not None:
            intents = [item for item in intents if item.status == status]
        intents.sort(key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc))
        return [intent.model_copy(deep=True) for intent in intents]

    async def update_intent_status(self, intent_id: str, status: Union[IntentStatus, str]) -> Any:
        # Import here to avoid circular dependency
        from app.models.intent import IntentModel
        
        status_value = IntentModel._coerce_status(status)
        current_task = asyncio.current_task()
        if current_task is not None and self._lock_owners.get(intent_id) == current_task:
            session = self._active_sessions[intent_id]
            updated = self._apply_status_update(session.intent, status_value)
            return session.replace(updated).model_copy(deep=True)

        async with self.lock_intent_for_update(intent_id) as locked:
            updated = self._apply_status_update(locked.intent, status_value)
            return locked.replace(updated).model_copy(deep=True)

    @asynccontextmanager
    async def lock_intent_for_update(
        self,
        intent_id: str,
        *,
        timeout: float = 5.0,
    ) -> AsyncIterator[LockedIntentSession]:
        if intent_id not in self._intents:
            raise KeyError(f"intent not found: {intent_id}")

        per_intent = self._intent_locks.setdefault(intent_id, asyncio.Lock())
        session: LockedIntentSession | None = None
        owner = asyncio.current_task()
        if owner is None:  # pragma: no cover - event loop invariant
            raise RuntimeError("lock_intent_for_update requires an active task")
        try:
            await asyncio.wait_for(per_intent.acquire(), timeout)
        except asyncio.TimeoutError as exc:  # pragma: no cover - defensive
            raise LockTimeoutError(f"Mock lock timeout for intent {intent_id}") from exc

        try:
            async with self._lock:
                intent = self._intents[intent_id].model_copy(deep=True)
            session = LockedIntentSession(intent)
            self._active_sessions[intent_id] = session
            self._lock_owners[intent_id] = owner
            try:
                yield session
            finally:
                await self._persist_locked_intent(session.intent)
        finally:
            if session is not None:
                self._active_sessions.pop(intent_id, None)
            if self._lock_owners.get(intent_id) == owner:
                self._lock_owners.pop(intent_id, None)
            if per_intent.locked():
                per_intent.release()

    async def _persist_locked_intent(self, intent: Any) -> None:
        async with self._lock:
            self._intents[intent.intent_id] = intent.model_copy(deep=True)

    def _apply_status_update(self, intent: Any, status: IntentStatus) -> Any:
        # Import here to avoid circular dependency
        from app.models.intent import IntentModel
        
        IntentModel.validate_status_transition(intent.status, status)
        updated = intent.with_updates(
            status=status,
            updated_at=datetime.now(timezone.utc),
        )
        updated.increment_version()
        return updated
