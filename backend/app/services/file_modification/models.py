"""FileModificationService Models

Phase 3: 統一ファイル操作API用のPydanticモデル定義
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


class ConstraintLevel(str, Enum):
    """制約レベル"""
    CRITICAL = "critical"  # 変更不可（人間承認必須）
    HIGH = "high"          # 長い理由必須（50文字以上）
    MEDIUM = "medium"      # 短い理由必須（20文字以上）
    LOW = "low"            # 制約なし


class CheckResult(str, Enum):
    """チェック結果"""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    BLOCKED = "blocked"


class FileModificationRequest(BaseModel):
    """ファイル変更リクエスト"""
    user_id: str
    file_path: str
    operation: Literal["write", "delete", "rename"] = "write"
    content: Optional[str] = None  # write時のみ
    new_path: Optional[str] = None  # rename時のみ
    reason: str = Field(..., min_length=1)
    requested_by: str = "ai_agent"  # user, ai_agent, system
    force: bool = False  # MEDIUM以下を警告なしで通過


class FileModificationResult(BaseModel):
    """ファイル変更結果"""
    success: bool
    operation: str
    file_path: str
    message: str
    constraint_level: ConstraintLevel
    check_result: CheckResult
    backup_path: Optional[str] = None
    file_hash: Optional[str] = None
    timestamp: datetime


class FileOperationLog(BaseModel):
    """操作ログ（監査用）"""
    id: Optional[UUID] = None
    user_id: str
    file_path: str
    operation: str
    reason: str
    requested_by: str
    constraint_level: str
    result: str  # approved, rejected, blocked
    old_content_hash: Optional[str] = None
    new_content_hash: Optional[str] = None
    backup_path: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


class FileReadRequest(BaseModel):
    """ファイル読み込みリクエスト"""
    user_id: str
    file_path: str
    requested_by: str = "ai_agent"


class FileReadResult(BaseModel):
    """ファイル読み込み結果"""
    success: bool
    file_path: str
    content: Optional[str] = None
    file_hash: Optional[str] = None
    message: str


class ConstraintCheckRequest(BaseModel):
    """制約チェックリクエスト"""
    user_id: str
    file_path: str
    operation: Literal["write", "delete", "rename"] = "write"
    reason: str = Field(..., min_length=1)
    requested_by: str = "ai_agent"


class ConstraintCheckResult(BaseModel):
    """制約チェック結果"""
    file_path: str
    constraint_level: str
    check_result: str
    can_proceed: bool
    warning_message: Optional[str] = None
    required_actions: list[str] = []
    questions: list[str] = []
    min_reason_length: int = 0
    current_reason_length: int = 0


class VerificationRegistrationRequest(BaseModel):
    """検証登録リクエスト"""
    user_id: str
    file_path: str
    verification_type: str
    test_hours: float = 0
    constraint_level: ConstraintLevel = ConstraintLevel.MEDIUM
    description: Optional[str] = None
    verified_by: Optional[str] = None


class VerificationRegistrationResult(BaseModel):
    """検証登録結果"""
    status: str
    verification_id: str
    file_path: str
    constraint_level: str


class OperationLogsResult(BaseModel):
    """操作ログ結果"""
    total: int
    logs: list[dict]
