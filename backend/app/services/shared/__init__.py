"""Shared utilities and constants."""

from app.services.shared.constants import (
    IntentStatusEnum,
    PhilosophicalActor,
    TechnicalActor,
    IntentTypeEnum,
    BridgeTypeEnum,
    ExecutionMode,
    LogSeverity,
    AuditEventType,
)
from app.services.shared.exceptions import (
    BridgeLiteError,
    DiffError,
    DiffValidationError,
    DiffApplicationError,
    InvalidStatusError,
)
from app.services.shared.errors import (
    ConcurrencyError,
    LockTimeoutError,
    DeadlockError,
    ConcurrencyConflictError,
    is_deadlock_error,
)

__all__ = [
    # Constants
    "IntentStatusEnum",
    "PhilosophicalActor",
    "TechnicalActor",
    "IntentTypeEnum",
    "BridgeTypeEnum",
    "ExecutionMode",
    "LogSeverity",
    "AuditEventType",
    # Exceptions
    "BridgeLiteError",
    "DiffError",
    "DiffValidationError",
    "DiffApplicationError",
    "InvalidStatusError",
    # Errors
    "ConcurrencyError",
    "LockTimeoutError",
    "DeadlockError",
    "ConcurrencyConflictError",
    "is_deadlock_error",
]
