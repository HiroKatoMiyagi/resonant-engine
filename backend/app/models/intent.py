from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class IntentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IntentCreate(BaseModel):
    intent_text: str = Field(..., min_length=1)
    intent_type: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentUpdate(BaseModel):
    intent_text: Optional[str] = None
    intent_type: Optional[str] = None
    status: Optional[IntentStatus] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    outcome: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class IntentStatusUpdate(BaseModel):
    status: IntentStatus
    outcome: Optional[Dict[str, Any]] = None


class IntentResponse(BaseModel):
    id: UUID
    intent_text: str
    intent_type: Optional[str]
    status: IntentStatus
    priority: int
    outcome: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class IntentListResponse(BaseModel):
    items: List[IntentResponse]
    total: int
    limit: int
    offset: int
