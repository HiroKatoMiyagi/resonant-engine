from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class SpecificationStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"


class SpecificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    status: SpecificationStatus = SpecificationStatus.DRAFT
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SpecificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    status: Optional[SpecificationStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SpecificationResponse(BaseModel):
    id: UUID
    title: str
    content: str
    version: int
    status: SpecificationStatus
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpecificationListResponse(BaseModel):
    items: List[SpecificationResponse]
    total: int
    limit: int
    offset: int
