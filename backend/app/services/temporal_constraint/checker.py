import asyncpg
import logging
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from uuid import UUID

from .models import (
    FileVerification, TemporalConstraintCheck, ModificationRequest,
    ConstraintLevel, CheckResult
)

logger = logging.getLogger(__name__)

class TemporalConstraintChecker:
    """時間軸制約チェッカー"""
    
    # 制約レベルごとの設定
    CONSTRAINT_CONFIG = {
        ConstraintLevel.CRITICAL: {
            "require_approval": True,
            "require_reason": True,
            "min_reason_length": 50,
            "questions": [
                "本当にこのファイルを変更する必要がありますか？",
                "変更後の再テスト時間を確保できますか？",
                "この変更のロールバック計画はありますか？"
            ]
        },
        ConstraintLevel.HIGH: {
            "require_approval": False,
            "require_reason": True,
            "min_reason_length": 20,
            "questions": [
                "この変更の目的を記録してください"
            ]
        },
        ConstraintLevel.MEDIUM: {
            "require_approval": False,
            "require_reason": False,
            "questions": []
        },
        ConstraintLevel.LOW: {
            "require_approval": False,
            "require_reason": False,
            "questions": []
        }
    }
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def check_modification(
        self,
        request: ModificationRequest
    ) -> TemporalConstraintCheck:
        """
        ファイル変更の制約チェック
        
        Args:
            request: 変更リクエスト
            
        Returns:
            TemporalConstraintCheck: チェック結果
        """
        async with self.pool.acquire() as conn:
            # ファイル検証情報を取得
            verification = await conn.fetchrow("""
                SELECT * FROM file_verifications
                WHERE user_id = $1 AND file_path = $2
            """, request.user_id, request.file_path)
            
            if not verification:
                # 未登録ファイル = LOW制約
                return TemporalConstraintCheck(
                    file_path=request.file_path,
                    constraint_level=ConstraintLevel.LOW,
                    check_result=CheckResult.APPROVED,
                    warning_message=None,
                    required_actions=[],
                    questions=[]
                )
            
            verification_info = FileVerification(**dict(verification))
            constraint_level = ConstraintLevel(verification['constraint_level'])
            config = self.CONSTRAINT_CONFIG[constraint_level]
            
            # 警告メッセージ生成
            warning = self._generate_warning(verification_info)
            
            # 必要なアクション
            required_actions = []
            if config["require_approval"]:
                required_actions.append("approval_required")
            if config["require_reason"]:
                required_actions.append("reason_required")
            
            # 結果判定
            if constraint_level == ConstraintLevel.CRITICAL:
                check_result = CheckResult.PENDING  # 承認待ち
            elif constraint_level == ConstraintLevel.HIGH:
                if request.modification_reason and len(request.modification_reason) >= config["min_reason_length"]:
                    check_result = CheckResult.APPROVED
                else:
                    check_result = CheckResult.PENDING
            else:
                check_result = CheckResult.APPROVED
            
            # ログ記録
            await conn.execute("""
                INSERT INTO temporal_constraint_logs
                    (user_id, file_path, file_verification_id, modification_type,
                     modification_reason, requested_by, constraint_level_at_check,
                     check_result, approval_required)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, request.user_id, request.file_path, verification['id'],
                request.modification_type, request.modification_reason,
                request.requested_by, constraint_level.value,
                check_result.value, config["require_approval"])
            
            return TemporalConstraintCheck(
                file_path=request.file_path,
                constraint_level=constraint_level,
                check_result=check_result,
                verification_info=verification_info,
                warning_message=warning,
                required_actions=required_actions,
                questions=config["questions"]
            )
    
    def _generate_warning(self, verification: FileVerification) -> str:
        """警告メッセージ生成"""
        # Ensure verification.verified_at is aware
        verified_at = verification.verified_at
        if verified_at and verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        
        days_since_verified = (now - verified_at).days if verified_at else 0
        
        warning_parts = [
            f"⚠️ Temporal Constraint Warning!",
            f"",
            f"File: {verification.file_path}",
            f"Status: VERIFIED (検証済み)",
            f"Constraint Level: {verification.constraint_level.value.upper()}",
            f"",
            f"Verification History:",
            f"  - Type: {verification.verification_type}",
            f"  - Verified: {days_since_verified} days ago",
            f"  - Test Hours Invested: {verification.test_hours_invested}h",
        ]
        
        if verification.stable_since:
            stable_since = verification.stable_since
            if stable_since.tzinfo is None:
                stable_since = stable_since.replace(tzinfo=timezone.utc)
            
            stable_days = (now - stable_since).days
            warning_parts.append(f"  - Stable for: {stable_days} days")
        
        return "\n".join(warning_parts)
    
    async def register_verification(
        self,
        user_id: str,
        file_path: str,
        verification_type: str,
        test_hours: float = 0,
        constraint_level: ConstraintLevel = ConstraintLevel.MEDIUM,
        description: Optional[str] = None,
        verified_by: Optional[str] = None
    ) -> UUID:
        """ファイル検証を登録"""
        async with self.pool.acquire() as conn:
            # 既存レコードがあればUPSERT
            verification_id = await conn.fetchval("""
                INSERT INTO file_verifications
                    (user_id, file_path, verification_type, test_hours_invested,
                     constraint_level, verification_description, verified_by,
                     verified_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                ON CONFLICT (user_id, file_path) DO UPDATE
                SET verification_type = EXCLUDED.verification_type,
                    test_hours_invested = file_verifications.test_hours_invested + EXCLUDED.test_hours_invested,
                    constraint_level = EXCLUDED.constraint_level,
                    verification_description = EXCLUDED.verification_description,
                    verified_by = EXCLUDED.verified_by,
                    verified_at = NOW()
                RETURNING id
            """, user_id, file_path, verification_type, test_hours,
                constraint_level.value, description, verified_by)
            
            logger.info(
                f"Registered verification for {file_path}: "
                f"level={constraint_level.value}, hours={test_hours}"
            )
            
            return verification_id
    
    async def mark_stable(
        self,
        user_id: str,
        file_path: str
    ) -> bool:
        """ファイルを安定稼働としてマーク"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE file_verifications
                SET stable_since = NOW(),
                    constraint_level = 'high'
                WHERE user_id = $1 AND file_path = $2
            """, user_id, file_path)
            
            return result == "UPDATE 1"
    
    async def upgrade_to_critical(
        self,
        user_id: str,
        file_path: str,
        reason: str
    ) -> bool:
        """ファイルをCRITICALレベルに昇格"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE file_verifications
                SET constraint_level = 'critical',
                    metadata = COALESCE(metadata, '{}'::jsonb) || 
                               jsonb_build_object('critical_reason', $3)
                WHERE user_id = $1 AND file_path = $2
            """, user_id, file_path, reason)
            
            return result == "UPDATE 1"
