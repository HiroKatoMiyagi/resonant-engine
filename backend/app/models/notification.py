from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    message: Optional[str] = None
    notification_type: NotificationType = NotificationType.INFO
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    id: UUID
    user_id: str
    title: str
    message: Optional[str]
    notification_type: NotificationType
    is_read: bool
    metadata: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    limit: int
    offset: int


class NotificationMarkReadRequest(BaseModel):
    notification_ids: List[UUID]
