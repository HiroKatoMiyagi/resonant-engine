"""Concurrency control primitives for Bridge Lite Sprint 2."""

from __future__ import annotations

from enum import Enum


class LockStrategy(str, Enum):
    """Supported lock strategies for bridge operations."""

    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    NONE = "none"


class ConcurrencyConfig:
    """Centralized concurrency configuration knobs."""

    LOCK_STRATEGIES = {
        "update_status": LockStrategy.PESSIMISTIC,
        "re_evaluate": LockStrategy.OPTIMISTIC,
        "pipeline_execute": LockStrategy.PESSIMISTIC,
        "audit_log": LockStrategy.NONE,
    }

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 0.1  # seconds
    RETRY_JITTER = 0.05  # seconds
    DEADLOCK_TIMEOUT = 5.0  # seconds
    LOCK_TIMEOUT = 5.0  # seconds
    ISOLATION_LEVEL = "READ COMMITTED"

    @classmethod
    def get_lock_strategy(cls, operation: str) -> LockStrategy:
        return cls.LOCK_STRATEGIES.get(operation, LockStrategy.NONE)
