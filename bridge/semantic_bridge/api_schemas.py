"""
API Schemas for Semantic Bridge

Pydantic models for API request and response schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .models import EmotionState, MemorySearchQuery, MemoryType


class ProcessEventRequest(BaseModel):
    """Request for processing an event"""

    intent_id: UUID
    intent_text: str = Field(..., min_length=1)
    intent_type: str
    session_id: Optional[UUID] = None
    crisis_index: Optional[int] = Field(default=None, ge=0, le=100)
    timestamp: datetime
    bridge_result: Optional[Dict[str, Any]] = None
    kana_response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InferenceInfo(BaseModel):
    """Information about the inference result"""

    confidence: float
    reasoning: str
    project_confidence: float


class MemoryUnitResponse(BaseModel):
    """Response containing a memory unit"""

    id: UUID
    user_id: str
    project_id: Optional[str]
    type: MemoryType
    title: str
    content: str
    content_raw: Optional[str]
    tags: List[str]
    ci_level: Optional[int]
    emotion_state: Optional[EmotionState]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    # Pydantic V2 handles UUID and datetime serialization automatically
    model_config = ConfigDict(use_enum_values=False)


class ProcessEventResponse(BaseModel):
    """Response from processing an event"""

    memory_unit: MemoryUnitResponse
    inference: InferenceInfo


class SearchResponse(BaseModel):
    """Response from search query"""

    results: List[MemoryUnitResponse]
    total: int
    limit: int
    offset: int


class ProjectInfo(BaseModel):
    """Project statistics"""

    project_id: str
    memory_count: int
    latest_memory_at: datetime


class ProjectsResponse(BaseModel):
    """Response containing project statistics"""

    projects: List[ProjectInfo]


class TagInfo(BaseModel):
    """Tag statistics"""

    tag: str
    count: int


class TagsResponse(BaseModel):
    """Response containing tag statistics"""

    tags: List[TagInfo]


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    service: str


class ErrorResponse(BaseModel):
    """Error response"""

    detail: str
