"""Concurrency-related error definitions for Bridge Lite."""

from __future__ import annotations

from typing import Any, Dict, Optional

import asyncpg

from bridge.core.exceptions import BridgeLiteError


class ConcurrencyError(BridgeLiteError):
    """Base class for concurrency-specific failures."""


class LockTimeoutError(ConcurrencyError):
    """Raised when an intent lock cannot be acquired within the deadline."""


class DeadlockError(ConcurrencyError):
    """Raised when Postgres reports a deadlock."""

    def __init__(self, message: str, deadlock_info: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, context=deadlock_info)
        self.deadlock_info = deadlock_info or {}


class ConcurrencyConflictError(ConcurrencyError):
    """Raised when optimistic concurrency control detects a version mismatch."""


def is_deadlock_error(error: Exception) -> bool:
    """Return True when the provided exception represents a deadlock."""

    if isinstance(error, DeadlockError):
        return True
    if isinstance(error, asyncpg.exceptions.DeadlockDetectedError):
        return True
    if isinstance(error, asyncpg.PostgresError):
        message = str(error).lower()
        return "deadlock detected" in message or "40p01" in message
    return False
