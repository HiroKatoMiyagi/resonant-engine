"""FileModificationService API Router

Phase 3: 統一ファイル操作API
"""

from fastapi import APIRouter, Depends, Query, Body
from typing import Optional

from app.services.file_modification.service import FileModificationService
from app.services.file_modification.models import (
    FileModificationRequest, FileModificationResult,
    FileReadRequest, FileReadResult, ConstraintLevel,
    ConstraintCheckResult, VerificationRegistrationRequest,
    VerificationRegistrationResult, OperationLogsResult
)
from app.dependencies import get_file_modification_service

router = APIRouter(prefix="/api/v1/files", tags=["file-modification"])


@router.post("/write", response_model=FileModificationResult)
async def write_file(
    request: FileModificationRequest,
    service: FileModificationService = Depends(get_file_modification_service)
):
    """
    ファイル書き込み（制約チェック付き）

    - CRITICAL: ブロック（手動承認必須）
    - HIGH: 50文字以上の理由が必要
    - MEDIUM: 20文字以上の理由が必要
    - LOW: 制約なし
    """
    request.operation = "write"
    return await service.write_file(request)


@router.post("/delete", response_model=FileModificationResult)
async def delete_file(
    request: FileModificationRequest,
    service: FileModificationService = Depends(get_file_modification_service)
):
    """ファイル削除（制約チェック付き）"""
    request.operation = "delete"
    return await service.delete_file(request)


@router.post("/rename", response_model=FileModificationResult)
async def rename_file(
    request: FileModificationRequest,
    service: FileModificationService = Depends(get_file_modification_service)
):
    """ファイル名変更（制約チェック付き）"""
    request.operation = "rename"
    return await service.rename_file(request)


@router.get("/read", response_model=FileReadResult)
async def read_file(
    user_id: str = Query(...),
    file_path: str = Query(...),
    requested_by: str = Query("ai_agent"),
    service: FileModificationService = Depends(get_file_modification_service)
):
    """ファイル読み込み（制約チェックなし）"""
    request = FileReadRequest(
        user_id=user_id,
        file_path=file_path,
        requested_by=requested_by
    )
    return await service.read_file(request)


@router.post("/check", response_model=ConstraintCheckResult)
async def check_constraint(
    request: FileModificationRequest,
    service: FileModificationService = Depends(get_file_modification_service)
):
    """制約チェックのみ実行（ファイル操作なし）"""
    return await service.check_constraint(request)


@router.get("/logs", response_model=OperationLogsResult)
async def get_logs(
    user_id: str = Query(...),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    operation: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    service: FileModificationService = Depends(get_file_modification_service)
):
    """操作ログ取得"""
    return await service.get_operation_logs(
        user_id=user_id,
        limit=limit,
        offset=offset,
        operation=operation,
        result=result
    )


@router.post("/register-verification", response_model=VerificationRegistrationResult)
async def register_verification(
    request: VerificationRegistrationRequest,
    service: FileModificationService = Depends(get_file_modification_service)
):
    """ファイル検証を登録"""
    verification_id = await service.register_verification(
        user_id=request.user_id,
        file_path=request.file_path,
        verification_type=request.verification_type,
        test_hours=request.test_hours,
        constraint_level=request.constraint_level,
        description=request.description,
        verified_by=request.verified_by
    )

    return VerificationRegistrationResult(
        status="registered",
        verification_id=str(verification_id),
        file_path=request.file_path,
        constraint_level=request.constraint_level.value
    )
