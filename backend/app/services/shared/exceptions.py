"""Common exception types for Bridge Lite core modules."""
 
from __future__ import annotations
 
from typing import Any
 
 
class BridgeLiteError(Exception):
    """Base class for Bridge Lite specific errors."""
 
    def __init__(self, message: str, *, context: Any | None = None) -> None:
        super().__init__(message)
        self.context = context
 
 
class DiffError(BridgeLiteError):
    """Base error raised when applying diffs to intent payloads."""
 
 
class DiffValidationError(DiffError):
    """Raised when a diff payload fails validation."""
 
 
class DiffApplicationError(DiffError):
    """Raised when a diff cannot be applied to the target payload."""
 
 
class InvalidStatusError(BridgeLiteError):
    """Raised when an operation is attempted in an invalid intent status."""
 
 
__all__ = [
    "BridgeLiteError",
    "DiffError",
    "DiffValidationError",
    "DiffApplicationError",
    "InvalidStatusError",
]
