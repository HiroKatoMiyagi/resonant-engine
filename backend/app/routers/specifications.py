from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from app.models.specification import SpecificationCreate, SpecificationUpdate, SpecificationResponse, SpecificationListResponse
from app.repositories.specification_repo import SpecificationRepository

router = APIRouter(prefix="/api/specifications", tags=["specifications"])
repo = SpecificationRepository()


@router.get("", response_model=SpecificationListResponse)
async def list_specifications(
    status: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of specifications with optional filtering"""
    tags_list = tags.split(",") if tags else None
    items, total = await repo.list(status, tags_list, search, limit, offset)
    return SpecificationListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=SpecificationResponse)
async def get_specification(id: UUID):
    """Get a specific specification by ID"""
    spec = await repo.get_by_id(id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Specification {id} not found")
    return spec


@router.post("", response_model=SpecificationResponse, status_code=201)
async def create_specification(data: SpecificationCreate):
    """Create a new specification"""
    return await repo.create(data)


@router.put("/{id}", response_model=SpecificationResponse)
async def update_specification(id: UUID, data: SpecificationUpdate):
    """Update an existing specification"""
    spec = await repo.update(id, data)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Specification {id} not found")
    return spec


@router.delete("/{id}", status_code=204)
async def delete_specification(id: UUID):
    """Delete a specification"""
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Specification {id} not found")
