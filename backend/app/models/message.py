from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MessageType(str, Enum):
    USER = "user"
    YUNO = "yuno"
    KANA = "kana"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = MessageType.USER
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: UUID
    user_id: str
    content: str
    message_type: MessageType
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    items: List[MessageResponse]
    total: int
    limit: int
    offset: int
