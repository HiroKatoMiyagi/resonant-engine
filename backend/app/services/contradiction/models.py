"""Contradiction Detection - Data Models

Sprint 11: Models for detecting and tracking contradictions between intents.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4


class Contradiction(BaseModel):
    """矛盾検出レコード / Contradiction Detection Record"""

    id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: str

    # Intent情報 / Intent Information
    new_intent_id: UUID
    new_intent_content: str
    conflicting_intent_id: Optional[UUID] = None
    conflicting_intent_content: Optional[str] = None

    # 矛盾情報 / Contradiction Information
    contradiction_type: str  # 'tech_stack', 'policy_shift', 'duplicate', 'dogma'
    confidence_score: float = Field(ge=0.0, le=1.0)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 詳細情報 / Details
    details: Dict[str, Any] = Field(default_factory=dict)

    # 解決情報 / Resolution Information
    resolution_status: str = "pending"  # 'pending', 'approved', 'rejected', 'modified'
    resolution_action: Optional[str] = None  # 'policy_change', 'mistake', 'coexist'
    resolution_rationale: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("contradiction_type")
    @classmethod
    def validate_contradiction_type(cls, v: str) -> str:
        """Validate contradiction_type is one of allowed values"""
        allowed = ["tech_stack", "policy_shift", "duplicate", "dogma"]
        if v not in allowed:
            raise ValueError(f"contradiction_type must be one of {allowed}")
        return v

    @field_validator("resolution_status")
    @classmethod
    def validate_resolution_status(cls, v: str) -> str:
        """Validate resolution_status is one of allowed values"""
        allowed = ["pending", "approved", "rejected", "modified"]
        if v not in allowed:
            raise ValueError(f"resolution_status must be one of {allowed}")
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": "hiroki",
            "new_intent_id": "12345678-1234-5678-1234-567812345678",
            "new_intent_content": "Use SQLite for database",
            "conflicting_intent_id": "87654321-4321-8765-4321-876543218765",
            "conflicting_intent_content": "Use PostgreSQL for database",
            "contradiction_type": "tech_stack",
            "confidence_score": 0.9,
            "details": {
                "category": "database",
                "old_tech": "postgresql",
                "new_tech": "sqlite"
            },
            "resolution_status": "pending"
        }
    })


class IntentRelation(BaseModel):
    """Intent関係 / Intent Relationship"""

    id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: str

    # Intent関係 / Intent Relationship
    source_intent_id: UUID
    target_intent_id: UUID
    relation_type: str  # 'contradicts', 'duplicates', 'extends', 'replaces'

    # 関係強度 / Relationship Strength
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("relation_type")
    @classmethod
    def validate_relation_type(cls, v: str) -> str:
        """Validate relation_type is one of allowed values"""
        allowed = ["contradicts", "duplicates", "extends", "replaces"]
        if v not in allowed:
            raise ValueError(f"relation_type must be one of {allowed}")
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": "hiroki",
            "source_intent_id": "12345678-1234-5678-1234-567812345678",
            "target_intent_id": "87654321-4321-8765-4321-876543218765",
            "relation_type": "contradicts",
            "similarity_score": 0.85
        }
    })
