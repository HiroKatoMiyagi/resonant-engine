from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.services.temporal_constraint.checker import TemporalConstraintChecker
from app.services.temporal_constraint.models import (
    FileVerification, TemporalConstraintCheck, ModificationRequest,
    ConstraintLevel
)
from app.dependencies import get_temporal_constraint_checker

router = APIRouter(prefix="/api/v1/temporal-constraint", tags=["temporal-constraint"])

@router.post("/check", response_model=TemporalConstraintCheck)
async def check_modification(
    request: ModificationRequest,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイル変更の制約チェック"""
    return await checker.check_modification(request)

@router.post("/verify")
async def register_verification(
    user_id: str,
    file_path: str,
    verification_type: str,
    test_hours: float = 0,
    constraint_level: ConstraintLevel = ConstraintLevel.MEDIUM,
    description: Optional[str] = None,
    verified_by: Optional[str] = None,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイル検証を登録"""
    verification_id = await checker.register_verification(
        user_id, file_path, verification_type, test_hours,
        constraint_level, description, verified_by
    )
    
    return {
        "status": "registered",
        "verification_id": str(verification_id),
        "file_path": file_path,
        "constraint_level": constraint_level.value
    }

@router.post("/mark-stable")
async def mark_file_stable(
    user_id: str,
    file_path: str,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイルを安定稼働としてマーク"""
    success = await checker.mark_stable(user_id, file_path)
    
    if not success:
        raise HTTPException(status_code=404, detail="File verification not found")
    
    return {"status": "marked_stable", "file_path": file_path}

@router.post("/upgrade-critical")
async def upgrade_to_critical(
    user_id: str,
    file_path: str,
    reason: str,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイルをCRITICALレベルに昇格"""
    success = await checker.upgrade_to_critical(user_id, file_path, reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="File verification not found")
    
    return {"status": "upgraded_to_critical", "file_path": file_path}
