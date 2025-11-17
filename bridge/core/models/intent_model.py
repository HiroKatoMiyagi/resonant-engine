"""Pydantic representations of Bridge Lite intent entities (v2.1)."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, Iterable, List, Mapping, Optional, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from bridge.core.constants import (
    BridgeTypeEnum,
    IntentStatusEnum,
    IntentTypeEnum,
    PhilosophicalActor,
    TechnicalActor,
)
from bridge.core.correction.diff import apply_diff
from bridge.core.correction.idempotency import generate_correction_id, is_correction_applied
from bridge.core.exceptions import DiffValidationError, InvalidStatusError


def _now() -> datetime:
    """Return an aware UTC timestamp for intent bookkeeping."""

    return datetime.now(timezone.utc)


class CorrectionRecord(BaseModel):
    """Structured representation of an applied intent correction."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True, extra="allow")

    correction_id: UUID = Field(default_factory=uuid4)
    source: PhilosophicalActor = Field(default=PhilosophicalActor.KANA)
    reason: str = Field(default="legacy-correction")
    diff: Dict[str, Any] = Field(default_factory=dict)
    applied_at: datetime = Field(default_factory=_now)
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    def _normalize_legacy_payload(cls, data: Any) -> Any:
        if isinstance(data, Mapping):
            normalized = dict(data)
            if "applied_at" not in normalized and "created_at" in normalized:
                normalized.setdefault("applied_at", normalized.pop("created_at"))
            if "diff" not in normalized and "payload" in normalized:
                normalized.setdefault("diff", {"payload": normalized["payload"]})
            return normalized
        return data

    @field_validator("source", mode="before")
    def _coerce_source(cls, value: Any) -> PhilosophicalActor:
        if isinstance(value, PhilosophicalActor):
            return value
        return PhilosophicalActor._missing_(value)

    @field_validator("diff", mode="before")
    def _ensure_diff_dict(cls, value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            return dict(value)
        raise ValueError("Correction diff must be a mapping")

    @field_validator("applied_at", mode="before")
    def _coerce_applied_at(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        if value is None:
            return _now()
        raise ValueError("Invalid applied_at value for correction history")


class IntentModel(BaseModel):
    """Strongly typed representation of an intent within Bridge Lite v2.1."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: UUID = Field(default_factory=uuid4, alias="intent_id")
    type: str
    intent_type: IntentTypeEnum = Field(default=IntentTypeEnum.EXECUTE)
    bridge_type: BridgeTypeEnum = Field(default=BridgeTypeEnum.INPUT)
    correlation_id: UUID = Field(default_factory=uuid4)
    payload: Dict[str, Any]
    status: IntentStatusEnum = Field(default=IntentStatusEnum.RECEIVED)
    philosophical_actor: PhilosophicalActor = Field(default=PhilosophicalActor.KANA)
    technical_actor: TechnicalActor = Field(default=TechnicalActor.SYSTEM, alias="source")
    correction_history: List[CorrectionRecord] = Field(default_factory=list, alias="corrections")
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    version: int = Field(default=0)
    _ALLOWED_STATUS_TRANSITIONS: ClassVar[Dict[IntentStatusEnum, set[IntentStatusEnum]]] = {
        IntentStatusEnum.RECEIVED: {
            IntentStatusEnum.RECEIVED,
            IntentStatusEnum.NORMALIZED,
            IntentStatusEnum.FAILED,
        },
        IntentStatusEnum.NORMALIZED: {
            IntentStatusEnum.NORMALIZED,
            IntentStatusEnum.PROCESSED,
            IntentStatusEnum.COMPLETED,
            IntentStatusEnum.FAILED,
        },
        IntentStatusEnum.PROCESSED: {
            IntentStatusEnum.PROCESSED,
            IntentStatusEnum.CORRECTED,
            IntentStatusEnum.COMPLETED,
            IntentStatusEnum.FAILED,
        },
        IntentStatusEnum.CORRECTED: {
            IntentStatusEnum.CORRECTED,
            IntentStatusEnum.COMPLETED,
            IntentStatusEnum.FAILED,
        },
        IntentStatusEnum.COMPLETED: {IntentStatusEnum.COMPLETED},
        IntentStatusEnum.FAILED: {IntentStatusEnum.FAILED},
    }

    @field_validator("correction_history", mode="before")
    def _coerce_corrections(cls, value: Any) -> List[CorrectionRecord]:
        if value is None:
            return []
        items: List[Any]
        if isinstance(value, list):
            items = value
        elif isinstance(value, (str, bytes)):
            raise ValueError("correction_history must be an iterable of mappings, not a string")
        elif isinstance(value, Iterable):
            items = list(value)
        else:
            raise ValueError("correction_history must be iterable")
        return [CorrectionRecord.model_validate(item) for item in items]

    @property
    def intent_id(self) -> str:
        return str(self.id)

    @property
    def source(self) -> TechnicalActor:
        return self.technical_actor

    @property
    def corrections(self) -> List[Dict[str, Any]]:
        return [record.model_dump(mode="json", exclude_none=True) for record in self.correction_history]

    @corrections.setter
    def corrections(self, value: Iterable[Dict[str, Any]]) -> None:
        self.correction_history = [CorrectionRecord.model_validate(item) for item in value]

    def model_dump_bridge(self) -> Dict[str, Any]:
        """Dump intent data using Bridge Lite alias conventions."""

        return self.model_dump(by_alias=True)

    def with_updates(self, **changes: Any) -> "IntentModel":
        """Return a deep copy of the model with selected attributes updated."""

        return self.model_copy(update=changes, deep=True)

    def increment_version(self) -> "IntentModel":
        """Increment version metadata in-place and update timestamp."""

        self.version += 1
        self.updated_at = _now()
        return self

    @staticmethod
    def validate_status_transition(current: IntentStatusEnum, new: IntentStatusEnum) -> None:
        """Ensure status transitions respect the allowed lifecycle graph."""

        if current == new:
            return
        allowed = IntentModel._ALLOWED_STATUS_TRANSITIONS.get(current, set())
        if new not in allowed:
            raise InvalidStatusError(
                f"Invalid status transition {current.value} -> {new.value}",
                context={"current": current.value, "requested": new.value},
            )

    def apply_correction(
        self,
        diff: Dict[str, Any],
        *,
        source: PhilosophicalActor,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple["IntentModel", CorrectionRecord, bool]:
        """Apply diff to the intent, returning updated model, record, and idempotency flag."""

        if not isinstance(diff, dict):
            raise DiffValidationError("Correction diff must be a dictionary", context={"diff": diff})

        if self.status in {IntentStatusEnum.COMPLETED, IntentStatusEnum.FAILED}:
            raise InvalidStatusError(
                f"Cannot correct intent in {self.status.value} status",
                context={"status": self.status.value},
            )

        correction_id = generate_correction_id(self.id, diff)
        history = list(self.correction_history)
        if is_correction_applied(history, correction_id):
            existing = next(record for record in history if record.correction_id == correction_id)
            return self, existing, True

        payload_diff_raw = diff.get("payload", {})
        if payload_diff_raw is None:
            payload_diff_raw = {}
        if not isinstance(payload_diff_raw, dict):
            raise DiffValidationError(
                "diff['payload'] must be a dictionary when provided",
                context={"payload": payload_diff_raw},
            )

        updated_payload = apply_diff(self.payload or {}, payload_diff_raw)
        applied_at = _now()
        record = CorrectionRecord(
            correction_id=correction_id,
            source=source,
            reason=reason,
            diff=copy.deepcopy(diff),
            applied_at=applied_at,
            metadata=copy.deepcopy(metadata) if metadata is not None else None,
        )
        history.append(record)

        updated_intent = self.with_updates(
            payload=updated_payload,
            correction_history=history,
            status=IntentStatusEnum.CORRECTED,
            updated_at=applied_at,
            version=self.version + 1,
        )
        return updated_intent, record, False

    @classmethod
    def new(
        cls,
        intent_type: str,
        payload: Dict[str, Any],
        *,
        intent_id: Optional[Union[str, UUID]] = None,
        correlation_id: Optional[Union[str, UUID]] = None,
        status: Optional[Union[IntentStatusEnum, str]] = None,
        technical_actor: Optional[Union[TechnicalActor, str]] = None,
        source: Optional[Union[TechnicalActor, str]] = None,
        philosophical_actor: Optional[Union[PhilosophicalActor, str]] = None,
        bridge_type: Optional[Union[BridgeTypeEnum, str]] = None,
        intent_semantic_type: Optional[Union[IntentTypeEnum, str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        corrections: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> "IntentModel":
        now = created_at or _now()
        payload_copy = copy.deepcopy(payload)
        embedded_corrections = payload_copy.pop("corrections", None)
        status_value = cls._coerce_status(status or payload_copy.get("status"))
        tech_actor = cls._coerce_technical_actor(
            technical_actor or source or payload_copy.get("technical_actor") or payload_copy.get("source")
        )
        phil_actor = cls._coerce_philosophical_actor(
            philosophical_actor or payload_copy.get("philosophical_actor") or "kana"
        )
        bridge_value = cls._coerce_bridge_type(
            bridge_type or payload_copy.get("bridge_type") or "input"
        )
        intent_class = cls._coerce_intent_type(
            intent_semantic_type or payload_copy.get("intent_type") or IntentTypeEnum.EXECUTE
        )
        if corrections is not None:
            corr_history = copy.deepcopy(list(corrections))
        elif embedded_corrections is not None:
            corr_history = copy.deepcopy(list(embedded_corrections))
        else:
            corr_history = []

        return cls(
            intent_id=cls._coerce_uuid(intent_id) or uuid4(),
            type=intent_type,
            correlation_id=cls._coerce_uuid(correlation_id) or uuid4(),
            payload=payload_copy,
            status=status_value,
            bridge_type=bridge_value,
            intent_type=intent_class,
            philosophical_actor=phil_actor,
            technical_actor=tech_actor,
            correction_history=corr_history,
            created_at=now,
            updated_at=updated_at or payload_copy.get("updated_at") or now,
        )

    # ------------------------------------------------------------------
    # Coercion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_uuid(value: Optional[Union[str, UUID]]) -> Optional[UUID]:
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _coerce_status(value: Optional[Union[IntentStatusEnum, str]]) -> IntentStatusEnum:
        if value is None:
            return IntentStatusEnum.RECEIVED
        if isinstance(value, IntentStatusEnum):
            return value
        return IntentStatusEnum._missing_(value)

    @staticmethod
    def _coerce_technical_actor(value: Optional[Union[TechnicalActor, str]]) -> TechnicalActor:
        if value is None:
            return TechnicalActor.SYSTEM
        if isinstance(value, TechnicalActor):
            return value
        return TechnicalActor._missing_(value)

    @staticmethod
    def _coerce_philosophical_actor(value: Optional[Union[PhilosophicalActor, str]]) -> PhilosophicalActor:
        if value is None:
            return PhilosophicalActor.KANA
        if isinstance(value, PhilosophicalActor):
            return value
        return PhilosophicalActor._missing_(value)

    @staticmethod
    def _coerce_bridge_type(value: Optional[Union[BridgeTypeEnum, str]]) -> BridgeTypeEnum:
        if value is None:
            return BridgeTypeEnum.INPUT
        if isinstance(value, BridgeTypeEnum):
            return value
        return BridgeTypeEnum._missing_(value)

    @staticmethod
    def _coerce_intent_type(value: Optional[Union[IntentTypeEnum, str]]) -> IntentTypeEnum:
        if value is None:
            return IntentTypeEnum.EXECUTE
        if isinstance(value, IntentTypeEnum):
            return value
        return IntentTypeEnum._missing_(value)
