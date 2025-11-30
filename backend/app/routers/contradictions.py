"""Contradiction Detection API - 完全実装版"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from bridge.contradiction.detector import ContradictionDetector
from app.dependencies import get_contradiction_detector

router = APIRouter(prefix="/api/v1/contradiction", tags=["contradiction"])


# ==================== Request/Response Models ====================

class CheckContradictionRequest(BaseModel):
    """矛盾チェックリクエスト"""
    user_id: str
    intent_id: str
    intent_content: str


class ResolveContradictionRequest(BaseModel):
    """矛盾解決リクエスト"""
    resolution_action: str = Field(..., pattern="^(policy_change|mistake|coexist)$")
    resolution_rationale: str = Field(..., min_length=10)
    resolved_by: str


class ContradictionResponse(BaseModel):
    """矛盾レスポンス"""
    id: str
    user_id: str
    new_intent_id: str
    new_intent_content: str
    conflicting_intent_id: Optional[str]
    conflicting_intent_content: Optional[str]
    contradiction_type: str
    confidence_score: float
    detected_at: str
    details: Dict[str, Any]
    resolution_status: str
    resolution_action: Optional[str]
    resolution_rationale: Optional[str]
    resolved_at: Optional[str]


class ContradictionListResponse(BaseModel):
    """矛盾リストレスポンス"""
    contradictions: List[ContradictionResponse]
    count: int


# ==================== Endpoints ====================

@router.get("/pending", response_model=ContradictionListResponse)
async def get_pending_contradictions(
    user_id: str = Query(..., description="User ID to get pending contradictions for"),
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """
    未解決の矛盾一覧を取得
    
    Args:
        user_id: ユーザーID
        detector: Contradiction Detector（DI）
    
    Returns:
        ContradictionListResponse: 未解決矛盾のリスト
    """
    try:
        contradictions = await detector.get_pending_contradictions(user_id)
        
        return ContradictionListResponse(
            contradictions=[
                ContradictionResponse(**c.dict()) for c in contradictions
            ],
            count=len(contradictions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending contradictions: {str(e)}")


@router.post("/check", response_model=ContradictionListResponse)
async def check_intent_for_contradictions(
    request: CheckContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """
    Intentの矛盾をチェック
    
    Args:
        request: チェックリクエスト
        detector: Contradiction Detector（DI）
    
    Returns:
        ContradictionListResponse: 検出された矛盾のリスト
    """
    try:
        contradictions = await detector.check_new_intent(
            user_id=request.user_id,
            new_intent_id=UUID(request.intent_id) if isinstance(request.intent_id, str) else request.intent_id,
            new_intent_content=request.intent_content
        )
        
        return ContradictionListResponse(
            contradictions=[
                ContradictionResponse(**c.dict()) for c in contradictions
            ],
            count=len(contradictions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check contradictions: {str(e)}")


@router.put("/{contradiction_id}/resolve")
async def resolve_contradiction(
    contradiction_id: UUID,
    request: ResolveContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """
    矛盾を解決
    
    Args:
        contradiction_id: 矛盾ID
        request: 解決リクエスト
        detector: Contradiction Detector（DI）
    
    Returns:
        解決結果
    """
    try:
        result = await detector.resolve_contradiction(
            contradiction_id=contradiction_id,
            resolution_action=request.resolution_action,
            resolution_rationale=request.resolution_rationale,
            resolved_by=request.resolved_by
        )
        
        return {
            "status": "resolved",
            "contradiction_id": str(contradiction_id),
            "resolution_action": request.resolution_action
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve contradiction: {str(e)}")
