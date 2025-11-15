"""Utilities for intent correction handling."""

from .diff import apply_diff, serialize_diff, validate_diff
from .idempotency import generate_correction_id, is_correction_applied

__all__ = [
    "apply_diff",
    "validate_diff",
    "serialize_diff",
    "generate_correction_id",
    "is_correction_applied",
]
