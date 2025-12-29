"""Choice Preservation API - Pydantic v2準拠版（asyncpg自動変換対応）"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.database import db

router = APIRouter(prefix="/api/v1/memory/choice-points", tags=["choice-preservation"])


# ==================== Request/Response Models ====================

class ChoiceRequest(BaseModel):
    """選択肢リクエスト"""
    choice_id: str
    choice_text: str


class CreateChoicePointRequest(BaseModel):
    """Choice Point作成リクエスト"""
    user_id: str
    question: str
    choices: List[ChoiceRequest]
    tags: List[str] = Field(default_factory=list)
    context_type: str = "general"


class DecideChoiceRequest(BaseModel):
    """選択決定リクエスト"""
    selected_choice_id: str
    decision_rationale: str
    rejection_reasons: Dict[str, str] = Field(default_factory=dict)


class ChoicePointResponse(BaseModel):
    """Choice Point レスポンススキーマ"""
    id: str
    user_id: str
    question: str
    choices: List[Dict[str, Any]]
    tags: List[str]
    context_type: str
    created_at: str
    selected_choice_id: Optional[str] = None
    decision_rationale: Optional[str] = None
    decided_at: Optional[str] = None


class ChoicePointListResponse(BaseModel):
    """Choice Point リストレスポンス"""
    choice_points: List[ChoicePointResponse]
    count: int


class ChoicePointSearchResponse(BaseModel):
    """Choice Point 検索レスポンス"""
    results: List[ChoicePointResponse]
    count: int


# ==================== Internal Models (DB層) ====================

class ChoicePointDB(BaseModel):
    """DB層のChoice Point（UUID/datetime型のまま）"""
    id: UUID
    user_id: str
    question: str
    choices: List[Dict[str, Any]]
    tags: List[str]
    context_type: str
    created_at: datetime
    selected_choice_id: Optional[str] = None
    decision_rationale: Optional[str] = None
    decided_at: Optional[datetime] = None


# ==================== Endpoints ====================

@router.get("/pending", response_model=ChoicePointListResponse)
async def get_pending_choice_points(
    user_id: str = Query(...)
):
    """未決定の選択肢を取得"""
    try:
        rows = await db.fetch("""
            SELECT 
                id, user_id, question, choices, tags, context_type,
                created_at, selected_choice_id, decision_rationale, decided_at
            FROM choice_points
            WHERE user_id = $1 AND selected_choice_id IS NULL
            ORDER BY created_at DESC
        """, user_id)
        
        # ✅ asyncpgが自動変換するのでそのまま使用
        choice_points = [
            ChoicePointResponse(**ChoicePointDB(**dict(row)).model_dump(mode='json'))
            for row in rows
        ]
        
        return ChoicePointListResponse(choice_points=choice_points, count=len(choice_points))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending choice points: {str(e)}")


@router.post("/", response_model=ChoicePointResponse)
async def create_choice_point(request: CreateChoicePointRequest):
    """新しいChoice Pointを作成"""
    try:
        # ✅ dict/listを直接渡す（asyncpgが自動的にJSONBに変換）
        row = await db.fetchrow("""
            INSERT INTO choice_points (user_id, question, choices, tags, context_type)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, question, choices, selected_choice_id, 
                      decision_rationale, tags, context_type, created_at, decided_at
        """, request.user_id, request.question,
            [c.model_dump() for c in request.choices],  # ✅ json.dumps()不要
            request.tags, request.context_type)
        
        return ChoicePointResponse(**ChoicePointDB(**dict(row)).model_dump(mode='json'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create choice point: {str(e)}")


@router.put("/{choice_point_id}/decide", response_model=ChoicePointResponse)
async def decide_choice(choice_point_id: UUID, request: DecideChoiceRequest):
    """選択を決定"""
    try:
        cp_row = await db.fetchrow("SELECT * FROM choice_points WHERE id = $1", choice_point_id)
        if not cp_row:
            raise HTTPException(status_code=404, detail=f"Choice Point not found: {choice_point_id}")
        
        # ✅ asyncpgが自動変換したchoicesをそのまま使用
        choices = cp_row['choices']
        
        updated_choices = []
        for choice in choices:
            choice_dict = dict(choice) if isinstance(choice, dict) else choice
            choice_dict['selected'] = (choice_dict['choice_id'] == request.selected_choice_id)
            choice_dict['rejection_reason'] = None if choice_dict['selected'] else request.rejection_reasons.get(choice_dict['choice_id'], "")
            choice_dict['evaluated_at'] = datetime.now(timezone.utc).isoformat()
            updated_choices.append(choice_dict)
        
        # ✅ dict/listを直接渡す（asyncpgが自動的にJSONBに変換）
        row = await db.fetchrow("""
            UPDATE choice_points
            SET selected_choice_id = $1, decision_rationale = $2, choices = $3, decided_at = NOW()
            WHERE id = $4
            RETURNING id, user_id, question, choices, selected_choice_id, 
                      decision_rationale, tags, context_type, created_at, decided_at
        """, request.selected_choice_id, request.decision_rationale, 
             updated_choices, choice_point_id)  # ✅ json.dumps()不要、::jsonb不要
        
        return ChoicePointResponse(**ChoicePointDB(**dict(row)).model_dump(mode='json'))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decide choice: {str(e)}")


@router.get("/search", response_model=ChoicePointSearchResponse)
async def search_choice_points(
    user_id: str = Query(...),
    tags: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100)
):
    """選択肢を検索"""
    try:
        conditions = ["user_id = $1", "selected_choice_id IS NOT NULL"]
        params = [user_id]
        param_idx = 2
        
        if tags:
            conditions.append(f"tags && ${param_idx}::text[]")
            params.append(tags.split(","))
            param_idx += 1
        
        if from_date:
            conditions.append(f"decided_at >= ${param_idx}")
            params.append(datetime.fromisoformat(from_date))
            param_idx += 1
        
        if to_date:
            conditions.append(f"decided_at <= ${param_idx}")
            params.append(datetime.fromisoformat(to_date))
            param_idx += 1
        
        if search_text:
            conditions.append(f"question ILIKE ${param_idx}")
            params.append(f"%{search_text}%")
            param_idx += 1
        
        params.append(limit)
        
        query = f"""
            SELECT id, user_id, question, choices, selected_choice_id, decision_rationale,
                   tags, context_type, created_at, decided_at
            FROM choice_points
            WHERE {' AND '.join(conditions)}
            ORDER BY decided_at DESC LIMIT ${param_idx}
        """
        
        rows = await db.fetch(query, *params)
        
        # ✅ asyncpgが自動変換するのでそのまま使用
        results = [
            ChoicePointResponse(**ChoicePointDB(**dict(row)).model_dump(mode='json'))
            for row in rows
        ]
        
        return ChoicePointSearchResponse(results=results, count=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search choice points: {str(e)}")
