"""Concurrency control primitives for Bridge Lite Sprint 2."""

from __future__ import annotations

import asyncio
import functools
import random
from typing import Any, Callable, TypeVar
from enum import Enum
from asyncpg import DeadlockDetectedError


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


def retry_on_deadlock(max_retries: int = ConcurrencyConfig.MAX_RETRIES):
    """Decorator to retry operation on database deadlock."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except DeadlockDetectedError:
                    if retries >= max_retries:
                        raise
                    retries += 1
                    # Exponential backoff with jitter
                    base_delay = ConcurrencyConfig.RETRY_BACKOFF_BASE * (2 ** (retries - 1))
                    jitter = random.uniform(0, ConcurrencyConfig.RETRY_JITTER)
                    await asyncio.sleep(base_delay + jitter)
        return wrapper
    return decorator
