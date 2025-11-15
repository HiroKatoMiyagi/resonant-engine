"""Idempotency helpers for intent correction handling."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any
from uuid import UUID, uuid5

from bridge.core.correction.diff import serialize_diff

_CORRECTION_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, set):
        normalized_items = [_normalize(item) for item in value]
        return sorted(normalized_items, key=lambda item: repr(item))
    return value


def generate_correction_id(intent_id: UUID, diff: Mapping[str, Any]) -> UUID:
    """Generate deterministic correction identifier from intent and diff."""

    normalized = _normalize(diff)
    if not isinstance(normalized, dict):
        normalized = {"value": normalized}
    serialized = serialize_diff(normalized)
    payload = f"{intent_id}:{serialized}"
    return uuid5(_CORRECTION_NAMESPACE, payload)


def is_correction_applied(history: Iterable[object], correction_id: UUID) -> bool:
    """Check if a correction with the same ID already exists in history."""

    for record in history:
        if isinstance(record, Mapping):
            value = record.get("correction_id")
        else:
            value = getattr(record, "correction_id", None)
        if value is None:
            continue
        if isinstance(value, UUID) and value == correction_id:
            return True
        if isinstance(value, str) and value.lower() == str(correction_id).lower():
            return True
    return False


__all__ = ["generate_correction_id", "is_correction_applied"]
