"""Retry helpers for concurrency primitives."""

from __future__ import annotations

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from bridge.core.errors import DeadlockError, is_deadlock_error

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_deadlock(
    *,
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 2.0,
    jitter: float = 0.05,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Retry decorator that transparently handles Postgres deadlocks."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:  # pragma: no cover - narrow path
                    if not is_deadlock_error(exc):
                        raise
                    last_error = exc
                    if attempt >= max_retries - 1:
                        break
                    delay = min(base_delay * (2**attempt), max_delay)
                    if jitter:
                        delay += random.uniform(-jitter, jitter)
                    delay = max(delay, 0.0)
                    logger.warning(
                        "Deadlock detected during %s (attempt %s/%s). Retrying in %.3fs",
                        func.__qualname__,
                        attempt + 1,
                        max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)

            raise DeadlockError(
                f"Operation {func.__qualname__} failed after {max_retries} deadlock retries",
                deadlock_info={"max_retries": max_retries, "last_error": str(last_error)},
            ) from last_error

        return wrapper

    return decorator
