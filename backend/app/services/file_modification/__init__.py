"""FileModificationService - Phase 3 統一ファイル操作API

このモジュールは、AIエージェントがファイルを操作する際の
時間軸制約チェックを強制するための統一APIを提供します。

主要コンポーネント:
- FileModificationService: ファイル操作のコアサービス
- FileModificationRequest/Result: 変更リクエスト/結果モデル
- ConstraintLevel: 制約レベル (CRITICAL, HIGH, MEDIUM, LOW)
- CheckResult: チェック結果 (APPROVED, REJECTED, PENDING, BLOCKED)
"""

from .service import FileModificationService
from .models import (
    ConstraintLevel,
    CheckResult,
    FileModificationRequest,
    FileModificationResult,
    FileReadRequest,
    FileReadResult,
    FileOperationLog,
    ConstraintCheckResult,
    VerificationRegistrationRequest,
    VerificationRegistrationResult,
    OperationLogsResult,
)

__all__ = [
    "FileModificationService",
    "ConstraintLevel",
    "CheckResult",
    "FileModificationRequest",
    "FileModificationResult",
    "FileReadRequest",
    "FileReadResult",
    "FileOperationLog",
    "ConstraintCheckResult",
    "VerificationRegistrationRequest",
    "VerificationRegistrationResult",
    "OperationLogsResult",
]
