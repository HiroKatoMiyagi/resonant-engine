from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from app.models.intent import IntentCreate, IntentUpdate, IntentStatusUpdate, IntentResponse, IntentListResponse
from app.repositories.intent_repo import IntentRepository
from app.dependencies import get_term_drift_detector
from app.services.term_drift.detector import TermDriftDetector

router = APIRouter(prefix="/api/intents", tags=["intents"])
repo = IntentRepository()


async def analyze_intent_terms_task(
    user_id: str,
    text: str,
    source_id: str,
    detector: TermDriftDetector
):
    """Background task to analyze terms in new intent"""
    try:
        terms = await detector.extract_terms_from_text(text, f"Intent:{source_id}")
        for term in terms:
            await detector.register_term_definition(user_id, term)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error analyzing intent terms: {e}")


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
async def create_intent(
    data: IntentCreate,
    background_tasks: BackgroundTasks,
    detector: TermDriftDetector = Depends(get_term_drift_detector)
):
    """Create a new intent"""
    intent = await repo.create(data)
    
    # ユーザーIDがIntenCreateに含まれていない場合（System等の場合）はデフォルト値を使用するか、
    # IntentResponseから取得する（今のIntentResponseにはsession_idはあるがuser_idはないかも？）
    # Repositoryのcreate実装を見ると、System Default Sessionを使っている。
    # 簡易的に "system_user" または data内の情報を使う。
    # ここでは仮に "system" とする。実際のUser Contextが必要だが、現状のAPIにはUser情報がない。
    user_id = "system" 
    
    background_tasks.add_task(
        analyze_intent_terms_task,
        user_id,
        data.intent_text,
        str(intent.id),
        detector
    )
    
    return intent


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
