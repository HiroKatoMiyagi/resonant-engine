"""Correction utilities for intent processing."""

from .diff import apply_diff
from .idempotency import generate_correction_id, is_correction_applied

__all__ = ["apply_diff", "generate_correction_id", "is_correction_applied"]
