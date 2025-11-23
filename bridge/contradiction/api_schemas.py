"""API Schemas for Contradiction Detection - Sprint 11"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class ContradictionSchema(BaseModel):
    """Contradiction response schema"""

    id: UUID
    user_id: str
    new_intent_id: UUID
    new_intent_content: str
    conflicting_intent_id: Optional[UUID] = None
    conflicting_intent_content: Optional[str] = None
    contradiction_type: str
    confidence_score: float
    detected_at: datetime
    details: Dict[str, Any]
    resolution_status: str
    resolution_action: Optional[str] = None
    resolution_rationale: Optional[str] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CheckIntentRequest(BaseModel):
    """Request to check intent for contradictions"""

    user_id: str
    intent_id: UUID
    intent_content: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": "hiroki",
            "intent_id": "12345678-1234-5678-1234-567812345678",
            "intent_content": "Use SQLite for database"
        }
    })


class ResolveContradictionRequest(BaseModel):
    """Request to resolve a contradiction"""

    resolution_action: str = Field(
        ..., description="'policy_change', 'mistake', or 'coexist'"
    )
    resolution_rationale: str = Field(..., min_length=10)
    resolved_by: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "resolution_action": "policy_change",
            "resolution_rationale": "Switching to SQLite for development simplicity",
            "resolved_by": "hiroki"
        }
    })


class ContradictionListResponse(BaseModel):
    """Response with list of contradictions"""

    contradictions: List[ContradictionSchema]
    count: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "contradictions": [
                {
                    "id": "12345678-1234-5678-1234-567812345678",
                    "user_id": "hiroki",
                    "new_intent_id": "87654321-4321-8765-4321-876543218765",
                    "new_intent_content": "Use SQLite database",
                    "conflicting_intent_id": "11111111-1111-1111-1111-111111111111",
                    "conflicting_intent_content": "Use PostgreSQL database",
                    "contradiction_type": "tech_stack",
                    "confidence_score": 0.9,
                    "detected_at": "2025-11-21T10:00:00Z",
                    "details": {
                        "category": "database",
                        "old_tech": "postgresql",
                        "new_tech": "sqlite"
                    },
                    "resolution_status": "pending",
                    "resolution_action": None,
                    "resolution_rationale": None,
                    "resolved_at": None
                }
            ],
            "count": 1
        }
    })
