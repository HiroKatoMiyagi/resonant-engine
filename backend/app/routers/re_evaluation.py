"""Re-evaluation API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID

from app.dependencies import get_bridge_set

router = APIRouter(prefix="/api/v1/intent", tags=["re-evaluation"])


class ReEvalRequest(BaseModel):
    """再評価リクエスト"""
    intent_id: UUID
    diff: Dict[str, Any]
    source: str
    reason: str


@router.post("/reeval")
async def re_evaluate_intent(
    request: ReEvalRequest,
    bridge_set = Depends(get_bridge_set)
):
    """
    Intent再評価
    
    Args:
        request: 再評価リクエスト
        bridge_set: BridgeSet（DI）
    
    Returns:
        再評価結果
    """
    try:
        result = await bridge_set.feedback.evaluate_intent(
            intent_id=str(request.intent_id),
            diff=request.diff,
            source=request.source,
            reason=request.reason
        )
        
        return {
            "intent_id": str(request.intent_id),
            "status": "re-evaluated",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to re-evaluate intent: {str(e)}")
