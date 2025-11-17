"""
Semantic Bridge API Router

FastAPI router for Semantic Bridge REST API endpoints.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .api_schemas import (
    ErrorResponse,
    HealthResponse,
    InferenceInfo,
    MemoryUnitResponse,
    ProcessEventRequest,
    ProcessEventResponse,
    ProjectInfo,
    ProjectsResponse,
    SearchResponse,
    TagInfo,
    TagsResponse,
)
from .models import (
    EmotionState,
    EventContext,
    MemorySearchQuery,
    MemoryType,
    MemoryUnit,
)
from .repositories import InMemoryUnitRepository
from .service import SemanticBridgeService

# Create router
router = APIRouter(prefix="/api/semantic-bridge", tags=["semantic-bridge"])

# Global service instance (will be replaced with proper DI)
_service: Optional[SemanticBridgeService] = None
_repository: Optional[InMemoryUnitRepository] = None


def get_semantic_bridge_service() -> SemanticBridgeService:
    """Dependency injection for Semantic Bridge Service"""
    global _service, _repository

    if _service is None:
        _repository = InMemoryUnitRepository()
        _service = SemanticBridgeService(memory_repo=_repository)

    return _service


def get_repository() -> InMemoryUnitRepository:
    """Dependency injection for Repository"""
    global _repository

    if _repository is None:
        get_semantic_bridge_service()  # Initialize service and repository

    return _repository


def memory_unit_to_response(unit: MemoryUnit) -> MemoryUnitResponse:
    """Convert MemoryUnit to API response"""
    return MemoryUnitResponse(
        id=unit.id,
        user_id=unit.user_id,
        project_id=unit.project_id,
        type=unit.type,
        title=unit.title,
        content=unit.content,
        content_raw=unit.content_raw,
        tags=unit.tags,
        ci_level=unit.ci_level,
        emotion_state=unit.emotion_state,
        started_at=unit.started_at,
        ended_at=unit.ended_at,
        created_at=unit.created_at,
        updated_at=unit.updated_at,
        metadata=unit.metadata,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check service health status"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="semantic_bridge",
    )


@router.post("/process", response_model=ProcessEventResponse)
async def process_event(
    request: ProcessEventRequest,
    service: SemanticBridgeService = Depends(get_semantic_bridge_service),
) -> ProcessEventResponse:
    """
    Process an event and convert it to a memory unit.

    This endpoint:
    1. Extracts semantic meaning from the event
    2. Infers memory type and project
    3. Constructs and saves the memory unit
    """
    try:
        # Create EventContext from request
        event_context = EventContext(
            intent_id=request.intent_id,
            intent_text=request.intent_text,
            intent_type=request.intent_type,
            session_id=request.session_id,
            crisis_index=request.crisis_index,
            timestamp=request.timestamp,
            bridge_result=request.bridge_result,
            kana_response=request.kana_response,
            metadata=request.metadata,
        )

        # Process event
        memory_unit = await service.process_event(event_context)

        # Get inference info from metadata
        inference_info = InferenceInfo(
            confidence=memory_unit.metadata.get("inference_confidence", 0.0),
            reasoning=memory_unit.metadata.get("inference_reasoning", ""),
            project_confidence=memory_unit.metadata.get("project_confidence", 0.0),
        )

        return ProcessEventResponse(
            memory_unit=memory_unit_to_response(memory_unit),
            inference=inference_info,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_memories(
    query: MemorySearchQuery,
    repo: InMemoryUnitRepository = Depends(get_repository),
) -> SearchResponse:
    """
    Search for memory units with various filters.

    Supports filtering by:
    - Project ID(s)
    - Memory type(s)
    - Tags (any or all mode)
    - Date range
    - CI Level range
    - Emotion states
    - Text search (title and content)
    """
    try:
        results = await repo.search(query)
        total = await repo.count(query)

        return SearchResponse(
            results=[memory_unit_to_response(u) for u in results],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/memory/{memory_id}", response_model=MemoryUnitResponse)
async def get_memory(
    memory_id: UUID,
    repo: InMemoryUnitRepository = Depends(get_repository),
) -> MemoryUnitResponse:
    """Get a specific memory unit by ID"""
    memory_unit = await repo.get_by_id(memory_id)

    if not memory_unit:
        raise HTTPException(status_code=404, detail=f"Memory unit not found: {memory_id}")

    return memory_unit_to_response(memory_unit)


@router.get("/projects", response_model=ProjectsResponse)
async def get_projects(
    repo: InMemoryUnitRepository = Depends(get_repository),
) -> ProjectsResponse:
    """Get project statistics"""
    projects = await repo.get_projects()

    return ProjectsResponse(
        projects=[
            ProjectInfo(
                project_id=p["project_id"],
                memory_count=p["memory_count"],
                latest_memory_at=p["latest_memory_at"],
            )
            for p in projects
        ]
    )


@router.get("/tags", response_model=TagsResponse)
async def get_tags(
    repo: InMemoryUnitRepository = Depends(get_repository),
) -> TagsResponse:
    """Get tag statistics"""
    tags = await repo.get_tags()

    return TagsResponse(tags=[TagInfo(tag=t["tag"], count=t["count"]) for t in tags])


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    repo: InMemoryUnitRepository = Depends(get_repository),
) -> dict:
    """Delete a memory unit by ID"""
    success = await repo.delete(memory_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Memory unit not found: {memory_id}")

    return {"status": "deleted", "memory_id": str(memory_id)}


# Reset function for testing
def reset_service() -> None:
    """Reset the global service and repository"""
    global _service, _repository
    _service = None
    _repository = None
