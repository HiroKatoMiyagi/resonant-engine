"""Choice Preservation API"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import json

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


# ==================== Endpoints ====================

@router.get("/pending")
async def get_pending_choice_points(
    user_id: str = Query(...)
):
    """未決定の選択肢を取得"""
    try:
        rows = await db.fetch("""
            SELECT 
                id::text,
                user_id,
                question,
                choices,
                tags,
                context_type,
                created_at
            FROM choice_points
            WHERE user_id = $1
              AND selected_choice_id IS NULL
            ORDER BY created_at DESC
        """, user_id)
        
        choice_points = [dict(row) for row in rows]
        return {"choice_points": choice_points, "count": len(choice_points)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending choice points: {str(e)}")


@router.post("/")
async def create_choice_point(
    request: CreateChoicePointRequest
):
    """新しい選択肢を作成"""
    try:
        # session_idとintent_idはダミー値を使用（外部キー制約があるため）
        # 実際の実装では、現在のセッションとIntentから取得する
        row = await db.fetchrow("""
            INSERT INTO choice_points (
                id,
                user_id,
                session_id,
                intent_id,
                question,
                choices,
                tags,
                context_type,
                created_at
            )
            VALUES (
                gen_random_uuid(),
                $1,
                (SELECT id FROM sessions LIMIT 1),
                (SELECT id FROM intents LIMIT 1),
                $2,
                $3::jsonb,
                $4,
                $5,
                NOW()
            )
            RETURNING id::text, user_id, question, choices, tags, context_type, created_at
        """, 
            request.user_id,
            request.question,
            json.dumps([c.dict() for c in request.choices]),
            request.tags,
            request.context_type
        )
        
        choice_point = dict(row)
        return {"choice_point": choice_point}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create choice point: {str(e)}")


@router.put("/{choice_point_id}/decide")
async def decide_choice(
    choice_point_id: UUID,
    request: DecideChoiceRequest
):
    """選択を決定"""
    try:
        # 既存のChoice Pointを取得
        cp_row = await db.fetchrow("""
            SELECT * FROM choice_points WHERE id = $1
        """, choice_point_id)
        
        if not cp_row:
            raise HTTPException(status_code=404, detail=f"Choice Point not found: {choice_point_id}")
        
        # choicesを更新（selected, rejection_reason追加）
        choices = cp_row['choices']
        if isinstance(choices, str):
            choices = json.loads(choices)
        
        updated_choices = []
        for choice in choices:
            choice_dict = dict(choice) if isinstance(choice, dict) else choice
            choice_dict['selected'] = (choice_dict['choice_id'] == request.selected_choice_id)
            
            if choice_dict['selected']:
                choice_dict['rejection_reason'] = None
            else:
                choice_dict['rejection_reason'] = request.rejection_reasons.get(choice_dict['choice_id'], "")
            
            choice_dict['evaluated_at'] = datetime.now(timezone.utc).isoformat()
            updated_choices.append(choice_dict)
        
        # DB更新
        row = await db.fetchrow("""
            UPDATE choice_points
            SET 
                selected_choice_id = $1,
                decision_rationale = $2,
                choices = $3::jsonb,
                decided_at = NOW()
            WHERE id = $4
            RETURNING id::text, user_id, question, choices, selected_choice_id, 
                      decision_rationale, tags, context_type, created_at, decided_at
        """, request.selected_choice_id, request.decision_rationale, 
             json.dumps(updated_choices), choice_point_id)
        
        choice_point = dict(row)
        return {"choice_point": choice_point}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decide choice: {str(e)}")


@router.get("/search")
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
        
        # タグフィルタ
        if tags:
            tag_list = tags.split(",")
            conditions.append(f"tags && ${param_idx}::text[]")
            params.append(tag_list)
            param_idx += 1
        
        # 時間範囲フィルタ
        if from_date:
            conditions.append(f"decided_at >= ${param_idx}")
            params.append(datetime.fromisoformat(from_date))
            param_idx += 1
        
        if to_date:
            conditions.append(f"decided_at <= ${param_idx}")
            params.append(datetime.fromisoformat(to_date))
            param_idx += 1
        
        # フルテキスト検索
        if search_text:
            conditions.append(f"question ILIKE ${param_idx}")
            params.append(f"%{search_text}%")
            param_idx += 1
        
        params.append(limit)
        
        query = f"""
            SELECT 
                id::text,
                user_id,
                question,
                choices,
                selected_choice_id,
                decision_rationale,
                tags,
                context_type,
                created_at,
                decided_at
            FROM choice_points
            WHERE {' AND '.join(conditions)}
            ORDER BY decided_at DESC
            LIMIT ${param_idx}
        """
        
        rows = await db.fetch(query, *params)
        results = [dict(row) for row in rows]
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search choice points: {str(e)}")
