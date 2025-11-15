"""Diff validation and application utilities for intent corrections."""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Dict

from bridge.core.exceptions import DiffApplicationError, DiffValidationError


_RELATIVE_PREFIXES = {"+", "-", "*", "/"}
_FUNCTION_CALL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*\s*\(")
_FORBIDDEN_SEQUENCE = "__import__"


def validate_diff(diff: Dict[str, Any]) -> None:
    """Validate diff payload according to Bridge Lite rules."""

    if not isinstance(diff, dict):
        raise DiffValidationError("Diff payload must be a dictionary", context=diff)

    for key, value in diff.items():
        if not isinstance(key, str) or not key:
            raise DiffValidationError("Diff keys must be non-empty strings", context=key)
        if key.startswith('.') or key.endswith('.') or '..' in key:
            raise DiffValidationError(f"Diff key '{key}' contains invalid dot notation", context=key)
        if isinstance(value, dict):
            validate_diff(value)
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                continue
            if stripped[0] in _RELATIVE_PREFIXES and stripped[1:].lstrip().isdigit():
                raise DiffValidationError(
                    f"Relative operations forbidden in diff: {key}={value}",
                    context={"key": key, "value": value},
                )
            if _FUNCTION_CALL_RE.match(stripped):
                raise DiffValidationError(
                    f"Function-style expressions forbidden in diff: {key}={value}",
                    context={"key": key, "value": value},
                )
            if _FORBIDDEN_SEQUENCE in stripped:
                raise DiffValidationError(
                    "Python code patterns forbidden in diff values",
                    context={"key": key, "value": value},
                )
        elif isinstance(value, (list, set, tuple)):
            # Ensure nested string validation in sequences
            for item in value:
                if isinstance(item, str):
                    validate_diff({key: item})
        # Other primitive types considered safe


def apply_diff(target: Dict[str, Any], diff: Dict[str, Any]) -> Dict[str, Any]:
    """Apply absolute-value diff entries to a target dict."""

    validate_diff(diff)
    base = copy.deepcopy(target) if target is not None else {}

    for raw_key, value in diff.items():
        if raw_key == "":
            raise DiffValidationError("Diff key cannot be empty", context=raw_key)

        path = raw_key.split('.')
        cursor = base
        for segment in path[:-1]:
            existing = cursor.get(segment)
            if existing is None:
                cursor[segment] = {}
                cursor = cursor[segment]
                continue
            if not isinstance(existing, dict):
                raise DiffApplicationError(
                    f"Cannot traverse into non-dict segment '{segment}' for key '{raw_key}'",
                    context={"segment": segment, "existing_type": type(existing).__name__},
                )
            cursor = existing
        cursor[path[-1]] = copy.deepcopy(value)

    return base


def serialize_diff(diff: Dict[str, Any]) -> str:
    """Serialize diff to deterministic JSON for hashing/idempotency."""

    return json.dumps(diff, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


__all__ = ["validate_diff", "apply_diff", "serialize_diff"]
