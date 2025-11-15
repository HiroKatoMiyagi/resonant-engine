"""Pydantic models for the Bridge Lite re-evaluation API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bridge.core.constants import IntentStatusEnum, PhilosophicalActor


class ReEvaluationRequest(BaseModel):
    """Incoming payload for the re-evaluation endpoint."""

    model_config = ConfigDict(populate_by_name=True, json_schema_extra={"example": {
        "intent_id": "550e8400-e29b-41d4-a716-446655440000",
        "diff": {"payload": {"status": "corrected"}},
        "source": "yuno",
        "reason": "Status normalization",
    }})

    intent_id: UUID = Field(..., description="Target intent ID to re-evaluate")
    diff: Dict[str, Any] = Field(..., description="Absolute diff to apply to the intent payload")
    source: PhilosophicalActor = Field(..., description="Source philosophical actor (YUNO/KANA)")
    reason: str = Field(..., min_length=1, max_length=1000, description="Human-readable correction reason")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional correction metadata")


class ReEvaluationResponse(BaseModel):
    """Successful re-evaluation response payload."""

    intent_id: UUID
    status: IntentStatusEnum
    already_applied: bool
    correction_id: UUID
    applied_at: datetime
    correction_count: int


class ReEvaluationError(BaseModel):
    """Standardized error body for re-evaluation failures."""

    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


__all__ = [
    "ReEvaluationRequest",
    "ReEvaluationResponse",
    "ReEvaluationError",
]
