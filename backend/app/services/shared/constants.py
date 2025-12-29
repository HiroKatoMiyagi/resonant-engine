"""Unified enumeration and constant definitions for Bridge Lite v2.1."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional


def _normalize(value: object) -> Optional[str]:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, str):
        return value.strip()
    return None


class PhilosophicalActor(str, Enum):
    """Resonant Engine consciousness layers."""

    YUNO = "yuno"
    KANA = "kana"
    TSUMU = "tsumu"

    @classmethod
    def _missing_(cls, value: object) -> "PhilosophicalActor":
        normalized = _normalize(value)
        if normalized is None:
            raise ValueError(f"Unknown PhilosophicalActor value: {value!r}")
        try:
            return cls(normalized.lower())
        except ValueError as exc:
            raise ValueError(f"Unknown PhilosophicalActor value: {value!r}") from exc


class TechnicalActor(str, Enum):
    """Technical execution actors that manipulate intents."""

    USER = "user"
    ENGINE = "engine"
    DAEMON = "daemon"
    SYSTEM = "system"
    DASHBOARD = "dashboard"
    API = "api"
    TEST_SUITE = "test_suite"

    @classmethod
    def _missing_(cls, value: object) -> "TechnicalActor":
        normalized = _normalize(value)
        if normalized is None:
            raise ValueError(f"Unknown TechnicalActor value: {value!r}")
        candidate = normalized.lower()
        if candidate in {"yuno", "kana", "tsumu"}:
            candidate = {
                "yuno": cls.SYSTEM.value,
                "kana": cls.ENGINE.value,
                "tsumu": cls.DAEMON.value,
            }[candidate]
        try:
            return cls(candidate)
        except ValueError as exc:
            raise ValueError(f"Unknown TechnicalActor value: {value!r}") from exc


class IntentTypeEnum(str, Enum):
    """Semantic intent categories."""

    EXECUTE = "execute"
    QUERY = "query"
    UPDATE = "update"

    @classmethod
    def _missing_(cls, value: object) -> "IntentTypeEnum":
        normalized = _normalize(value)
        if normalized is None:
            raise ValueError(f"Unknown IntentTypeEnum value: {value!r}")
        try:
            return cls(normalized.lower())
        except ValueError as exc:
            raise ValueError(f"Unknown IntentTypeEnum value: {value!r}") from exc


class BridgeTypeEnum(str, Enum):
    """Bridge pipeline stage identifiers."""

    INPUT = "input"
    NORMALIZE = "normalize"
    FEEDBACK = "feedback"
    OUTPUT = "output"

    @classmethod
    def _missing_(cls, value: object) -> "BridgeTypeEnum":
        normalized = _normalize(value)
        if normalized is None:
            raise ValueError(f"Unknown BridgeTypeEnum value: {value!r}")
        candidate = normalized.lower()
        legacy_map = {
            "data": cls.INPUT.value,
            "ai": cls.NORMALIZE.value,
            "feedback": cls.FEEDBACK.value,
            "audit": cls.OUTPUT.value,
        }
        candidate = legacy_map.get(candidate, candidate)
        try:
            return cls(candidate)
        except ValueError as exc:
            raise ValueError(f"Unknown BridgeTypeEnum value: {value!r}") from exc


class IntentStatusEnum(str, Enum):
    """Intent lifecycle states."""

    RECEIVED = "received"
    NORMALIZED = "normalized"
    PROCESSED = "processed"
    CORRECTED = "corrected"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def _missing_(cls, value: object) -> "IntentStatusEnum":
        normalized = _normalize(value)
        if normalized is None:
            raise ValueError(f"Unknown IntentStatusEnum value: {value!r}")
        candidate = normalized.lower()
        legacy_map = {
            "recorded": cls.RECEIVED.value,
            "ai_processed": cls.PROCESSED.value,
            "feedback_collected": cls.CORRECTED.value,
            "reevaluated": cls.CORRECTED.value,
            "closed": cls.COMPLETED.value,
        }
        candidate = legacy_map.get(candidate, candidate)
        try:
            return cls(candidate)
        except ValueError as exc:
            raise ValueError(f"Unknown IntentStatusEnum value: {value!r}") from exc


class ExecutionMode(str, Enum):
    """Bridge pipeline execution strategies."""

    FAILFAST = "failfast"
    CONTINUE = "continue"
    SELECTIVE = "selective"


class LogSeverity(str, Enum):
    """Audit log severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEventType(str, Enum):
    """Audit event categories tracked in Bridge Lite."""

    INTENT_RECEIVED = "intent_received"
    INTENT_COMPLETED = "intent_completed"
    INTENT_FAILED = "intent_failed"
    BRIDGE_STARTED = "bridge_started"
    BRIDGE_COMPLETED = "bridge_completed"
    BRIDGE_FAILED = "bridge_failed"
    REEVALUATED = "reevaluated"
    STATUS_CHANGED = "status_changed"
    ERROR_RECOVERY_STARTED = "error_recovery_started"
    ERROR_RECOVERY_COMPLETED = "error_recovery_completed"


# ---------------------------------------------------------------------------
# Backward-compatible aliases (v2.0 callers)
# ---------------------------------------------------------------------------


class ActorEnum(str, Enum):  # type: ignore[misc]
    """Legacy upper-case actor aliases preserved for v2.0 callers."""

    YUNO = TechnicalActor.SYSTEM.value.upper()
    KANA = TechnicalActor.ENGINE.value.upper()
    DAEMON = TechnicalActor.DAEMON.value.upper()
    BRIDGE = TechnicalActor.ENGINE.value.upper()
    SYSTEM = TechnicalActor.SYSTEM.value.upper()
    DASHBOARD = TechnicalActor.DASHBOARD.value.upper()
    API = TechnicalActor.API.value.upper()
    TEST_SUITE = TechnicalActor.TEST_SUITE.value.upper()

    @classmethod
    def _missing_(cls, value: object) -> "ActorEnum":
        normalized = _normalize(value)
        if normalized is None:
            raise ValueError(f"Unknown ActorEnum value: {value!r}")
        candidate = normalized.upper()
        if candidate in cls._value2member_map_:
            return cls(candidate)
        try:
            tech = TechnicalActor._missing_(normalized)
        except ValueError as exc:
            raise ValueError(f"Unknown ActorEnum value: {value!r}") from exc
        return cls(tech.value.upper())


class LegacyBridgeRole(str, Enum):
    """Legacy bridge role names preserved for compatibility."""

    DATA = "DATA"
    AI = "AI"
    FEEDBACK = "FEEDBACK"
    AUDIT = "AUDIT"

    @classmethod
    def _missing_(cls, value: object) -> "LegacyBridgeRole":
        normalized = _normalize(value)
        if normalized is None:
            raise ValueError(f"Unknown LegacyBridgeRole value: {value!r}")
        candidate = normalized.upper()
        if candidate in cls._value2member_map_:
            return cls(candidate)
        try:
            stage = BridgeTypeEnum._missing_(normalized)
        except ValueError as exc:
            raise ValueError(f"Unknown LegacyBridgeRole value: {value!r}") from exc
        reverse_map = {
            BridgeTypeEnum.INPUT.value: cls.DATA.value,
            BridgeTypeEnum.NORMALIZE.value: cls.AI.value,
            BridgeTypeEnum.FEEDBACK.value: cls.FEEDBACK.value,
            BridgeTypeEnum.OUTPUT.value: cls.AUDIT.value,
        }
        return cls(reverse_map[stage])


BridgeRoleEnum = LegacyBridgeRole

