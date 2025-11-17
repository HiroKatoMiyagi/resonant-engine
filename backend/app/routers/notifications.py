from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.notification import NotificationCreate, NotificationResponse, NotificationListResponse, NotificationMarkReadRequest
from app.repositories.notification_repo import NotificationRepository

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
repo = NotificationRepository()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    user_id: Optional[str] = None,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of notifications with optional filtering"""
    items, total = await repo.list(user_id, is_read, notification_type, limit, offset)
    return NotificationListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=NotificationResponse)
async def get_notification(id: UUID):
    """Get a specific notification by ID"""
    notification = await repo.get_by_id(id)
    if not notification:
        raise HTTPException(status_code=404, detail=f"Notification {id} not found")
    return notification


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(data: NotificationCreate):
    """Create a new notification"""
    return await repo.create(data)


@router.post("/mark-read")
async def mark_notifications_read(data: NotificationMarkReadRequest):
    """Mark notifications as read"""
    count = await repo.mark_read(data.notification_ids)
    return {"marked_read": count}


@router.delete("/{id}", status_code=204)
async def delete_notification(id: UUID):
    """Delete a notification"""
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Notification {id} not found")
