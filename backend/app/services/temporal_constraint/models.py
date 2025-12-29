from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class ConstraintLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CheckResult(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"

class FileVerification(BaseModel):
    """ファイル検証情報"""
    id: Optional[UUID] = None
    user_id: str
    file_path: str
    file_hash: Optional[str] = None
    verification_type: str
    verification_description: Optional[str] = None
    test_hours_invested: float = 0.0
    constraint_level: ConstraintLevel = ConstraintLevel.LOW
    verified_at: Optional[datetime] = None
    stable_since: Optional[datetime] = None
    verified_by: Optional[str] = None

class TemporalConstraintCheck(BaseModel):
    """制約チェック結果"""
    file_path: str
    constraint_level: ConstraintLevel
    check_result: CheckResult
    verification_info: Optional[FileVerification] = None
    warning_message: Optional[str] = None
    required_actions: List[str] = []
    questions: List[str] = []

class ModificationRequest(BaseModel):
    """変更リクエスト"""
    user_id: str
    file_path: str
    modification_type: str  # 'edit', 'delete', 'rename'
    modification_reason: str
    requested_by: str  # 'user', 'ai_agent', 'system'

class ModificationApproval(BaseModel):
    """変更承認"""
    approved: bool
    approval_note: str = Field(min_length=10)
    approved_by: str
