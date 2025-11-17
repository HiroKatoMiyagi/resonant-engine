from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.message import MessageCreate, MessageUpdate, MessageResponse, MessageListResponse
from app.repositories.message_repo import MessageRepository

router = APIRouter(prefix="/api/messages", tags=["messages"])
repo = MessageRepository()


@router.get("", response_model=MessageListResponse)
async def list_messages(
    user_id: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of messages with optional filtering"""
    items, total = await repo.list(user_id, message_type, limit, offset)
    return MessageListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=MessageResponse)
async def get_message(id: UUID):
    """Get a specific message by ID"""
    msg = await repo.get_by_id(id)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
    return msg


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(data: MessageCreate):
    """Create a new message"""
    return await repo.create(data)


@router.put("/{id}", response_model=MessageResponse)
async def update_message(id: UUID, data: MessageUpdate):
    """Update an existing message"""
    msg = await repo.update(id, data)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
    return msg


@router.delete("/{id}", status_code=204)
async def delete_message(id: UUID):
    """Delete a message"""
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
