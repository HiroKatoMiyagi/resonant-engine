from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID

from app.services.term_drift.detector import TermDriftDetector
from app.services.term_drift.models import (
    TermDefinition, TermDrift, TermDriftResolution, AnalyzeRequest
)
from app.dependencies import get_term_drift_detector

router = APIRouter(prefix="/api/v1/term-drift", tags=["term-drift"])

@router.get("/pending", response_model=List[TermDrift])
async def get_pending_drifts(
    user_id: str = Query(...),
    limit: int = Query(50, le=100),
    detector: TermDriftDetector = Depends(get_term_drift_detector)
):
    """未解決のドリフト一覧を取得"""
    return await detector.get_pending_drifts(user_id, limit)

@router.post("/analyze")
async def analyze_text(
    request: AnalyzeRequest,
    detector: TermDriftDetector = Depends(get_term_drift_detector)
):
    """テキストを分析して用語を抽出・ドリフトチェック"""
    terms = await detector.extract_terms_from_text(request.text, request.source)
    
    results = []
    for term in terms:
        definition_id, drift_detected = await detector.register_term_definition(
            request.user_id, term
        )
        results.append({
            "term_name": term["term_name"],
            "definition_id": str(definition_id),
            "drift_detected": drift_detected
        })
    
    return {
        "analyzed_terms": len(results),
        "drifts_detected": sum(1 for r in results if r["drift_detected"]),
        "results": results
    }

@router.put("/{drift_id}/resolve")
async def resolve_drift(
    drift_id: UUID,
    resolution: TermDriftResolution,
    detector: TermDriftDetector = Depends(get_term_drift_detector)
):
    """ドリフトを解決"""
    success = await detector.resolve_drift(
        drift_id,
        resolution.resolution_action,
        resolution.resolution_note,
        resolution.resolved_by
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Drift not found or already resolved")
    
    return {"status": "resolved", "drift_id": str(drift_id)}
