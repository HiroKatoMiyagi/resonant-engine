"""API Router for Contradiction Detection - Sprint 11"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID

from .detector import ContradictionDetector
from .api_schemas import (
    ContradictionSchema,
    CheckIntentRequest,
    ResolveContradictionRequest,
    ContradictionListResponse,
)

router = APIRouter(prefix="/api/v1/contradiction", tags=["contradiction"])


def get_contradiction_detector() -> ContradictionDetector:
    """Dependency: Get ContradictionDetector instance"""
    # TODO: Implement proper dependency injection with DB pool
    raise NotImplementedError("Implement DB pool injection")


@router.post("/check", response_model=ContradictionListResponse)
async def check_intent_for_contradictions(
    request: CheckIntentRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector),
):
    """
    Check an intent for contradictions with past intents

    This endpoint should be called before processing a new intent
    to detect potential contradictions with existing decisions.

    **Contradiction Types:**
    - `tech_stack`: Technology stack contradictions (e.g., PostgreSQL → SQLite)
    - `policy_shift`: Policy shifts within 2 weeks (e.g., microservice → monolith)
    - `duplicate`: Duplicate work (similar intents with high similarity)
    - `dogma`: Unverified assumptions (keywords like "always", "never")
    """
    contradictions = await detector.check_new_intent(
        user_id=request.user_id,
        new_intent_id=request.intent_id,
        new_intent_content=request.intent_content,
    )

    return ContradictionListResponse(
        contradictions=[
            ContradictionSchema(**c.model_dump()) for c in contradictions
        ],
        count=len(contradictions),
    )


@router.get("/pending", response_model=ContradictionListResponse)
async def get_pending_contradictions(
    user_id: str = Query(..., description="User ID to get pending contradictions for"),
    detector: ContradictionDetector = Depends(get_contradiction_detector),
):
    """
    Get all pending (unresolved) contradictions for a user

    Returns up to 20 most recent pending contradictions, ordered by detection time.
    """
    contradictions = await detector.get_pending_contradictions(user_id)

    return ContradictionListResponse(
        contradictions=[
            ContradictionSchema(**c.model_dump()) for c in contradictions
        ],
        count=len(contradictions),
    )


@router.put("/{contradiction_id}/resolve", response_model=dict)
async def resolve_contradiction(
    contradiction_id: UUID,
    request: ResolveContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector),
):
    """
    Resolve a detected contradiction

    **Resolution Actions:**
    - `policy_change`: Accept the new direction, mark old intent as deprecated
    - `mistake`: Reject new intent as an error
    - `coexist`: Both intents are valid in different contexts

    **Example:**
    ```json
    {
        "resolution_action": "policy_change",
        "resolution_rationale": "Switching to SQLite for development simplicity",
        "resolved_by": "hiroki"
    }
    ```
    """
    # Validate resolution_action
    valid_actions = ["policy_change", "mistake", "coexist"]
    if request.resolution_action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"resolution_action must be one of {valid_actions}",
        )

    await detector.resolve_contradiction(
        contradiction_id=contradiction_id,
        resolution_action=request.resolution_action,
        resolution_rationale=request.resolution_rationale,
        resolved_by=request.resolved_by,
    )

    return {
        "status": "resolved",
        "contradiction_id": str(contradiction_id),
        "action": request.resolution_action,
    }
