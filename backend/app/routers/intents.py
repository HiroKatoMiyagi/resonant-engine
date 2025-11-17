from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.intent import IntentCreate, IntentUpdate, IntentStatusUpdate, IntentResponse, IntentListResponse
from app.repositories.intent_repo import IntentRepository

router = APIRouter(prefix="/api/intents", tags=["intents"])
repo = IntentRepository()


@router.get("", response_model=IntentListResponse)
async def list_intents(
    status: Optional[str] = None,
    intent_type: Optional[str] = None,
    priority_min: Optional[int] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of intents with optional filtering"""
    items, total = await repo.list(status, intent_type, priority_min, limit, offset)
    return IntentListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=IntentResponse)
async def get_intent(id: UUID):
    """Get a specific intent by ID"""
    intent = await repo.get_by_id(id)
    if not intent:
        raise HTTPException(status_code=404, detail=f"Intent {id} not found")
    return intent


@router.post("", response_model=IntentResponse, status_code=201)
async def create_intent(data: IntentCreate):
    """Create a new intent"""
    return await repo.create(data)


@router.put("/{id}", response_model=IntentResponse)
async def update_intent(id: UUID, data: IntentUpdate):
    """Update an existing intent"""
    intent = await repo.update(id, data)
    if not intent:
        raise HTTPException(status_code=404, detail=f"Intent {id} not found")
    return intent


@router.patch("/{id}/status", response_model=IntentResponse)
async def update_intent_status(id: UUID, data: IntentStatusUpdate):
    """Update intent status"""
    intent = await repo.update_status(id, data)
    if not intent:
        raise HTTPException(status_code=404, detail=f"Intent {id} not found")
    return intent


@router.delete("/{id}", status_code=204)
async def delete_intent(id: UUID):
    """Delete an intent"""
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Intent {id} not found")
