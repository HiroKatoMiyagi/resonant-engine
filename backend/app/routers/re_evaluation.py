"""Re-evaluation API（修正版）"""

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
    
    Note: 現在はMockFeedbackBridgeを使用しているため、
          実際の再評価は行われず、モックレスポンスを返します。
    """
    try:
        # Intentデータを構築
        intent_data = {
            "id": str(request.intent_id),
            "type": "re_evaluation",
            "source": request.source,
            "reason": request.reason,
            "diff": request.diff
        }
        
        # ✅ 修正: evaluate_intent → request_reevaluation
        result = await bridge_set.feedback.request_reevaluation(intent_data)
        
        return {
            "intent_id": str(request.intent_id),
            "status": "re-evaluated",
            "judgment": result.get("judgment", "approved"),
            "evaluated_at": result.get("evaluated_at"),
            "notes": result.get("notes"),
            "diff": request.diff,
            "source": request.source,
            "reason": request.reason
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to re-evaluate intent: {str(e)}")
