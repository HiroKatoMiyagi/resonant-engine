# FileModificationService 設計仕様書

**作成日**: 2025-12-30
**作成者**: Kana (Claude Opus 4.5)
**バージョン**: 1.0.0
**Phase**: 3 - 統一ファイル操作API

---

## 1. 背景と目的

### 1.1 現状の問題

現在のResonant Engineには、AIエージェントが検証済みファイルを誤って変更することを防ぐための「時間軸制約層（Temporal Constraint Layer）」があります。しかし、ファイルシステムへの直接アクセスを防ぐ手段がないため、「利用規約ベース」（自主的なAPIチェック）で運用しています。

```
┌──────────────────────────────────────────────────────────────┐
│                    現状のファイルアクセス                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    直接アクセス    ┌──────────────────┐    │
│  │ AIエージェント │ ─────────────────→ │   ファイルシステム   │    │
│  └─────────────┘                    └──────────────────┘    │
│                                           ↑                 │
│  ┌─────────────┐    直接アクセス          │                 │
│  │    IDE      │ ─────────────────────────┘                 │
│  └─────────────┘                                            │
│                                           ↑                 │
│  ┌─────────────┐    直接アクセス          │                 │
│  │    CLI      │ ─────────────────────────┘                 │
│  └─────────────┘                                            │
│                                                              │
│  ⚠️ 制約チェックを強制できない                                │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Phase 3の目標

1. **統一的なFileModificationServiceを導入**
2. **すべてのファイル操作をこのサービス経由に集約**
3. **コードレベルでの制約チェックを実現**

### 1.3 移行フェーズ

| フェーズ | 対応 | 強制力 |
|---------|------|--------|
| Phase 1（完了） | 利用規約ベース + CLIラッパー | なし（自主的） |
| Phase 2（完了） | Git Hooks / CI統合 | 中（コミット/マージ時） |
| **Phase 3（本仕様）** | FileModificationService | 高（コードレベル） |

---

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────────────┐
│                    FileModificationService                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌──────────────────────┐                │
│  │  AIエージェント   │───→│ FileModificationAPI  │                │
│  └─────────────────┘    └──────────┬───────────┘                │
│                                    │                            │
│  ┌─────────────────┐    ┌──────────▼───────────┐                │
│  │      IDE        │───→│ FileModificationSvc  │                │
│  └─────────────────┘    └──────────┬───────────┘                │
│                                    │                            │
│  ┌─────────────────┐               │                            │
│  │      CLI        │───→           │                            │
│  └─────────────────┘               │                            │
│                      ┌─────────────▼─────────────┐              │
│                      │   TemporalConstraint      │              │
│                      │       Checker             │              │
│                      └─────────────┬─────────────┘              │
│                                    │                            │
│                      ┌─────────────▼─────────────┐              │
│                      │     ファイルシステム        │              │
│                      │   (制御されたアクセス)      │              │
│                      └───────────────────────────┘              │
│                                                                  │
│  🔒 直接アクセスは禁止（サービス経由のみ）                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 コンポーネント説明

| コンポーネント | 説明 | 責務 |
|---------------|------|------|
| FileModificationAPI | FastAPI ルーター | HTTP エンドポイント提供 |
| FileModificationService | ビジネスロジック | ファイル操作の統合制御 |
| TemporalConstraintChecker | 制約チェック | 検証済みファイルの保護 |
| FileOperationLog | 監査ログ | 全操作の記録 |

### 2.3 データフロー

```
[ファイル変更リクエスト]
    ↓
1. FileModificationService.write_file()
   ├─ パス検証（セキュリティチェック）
   ├─ 権限確認
   └─ user_id, file_path, reason 抽出
    ↓
2. TemporalConstraintChecker.check_modification()
   ├─ file_verifications テーブル参照
   ├─ constraint_level 取得
   └─ チェック結果返却
    ↓
3. 制約レベルに応じた処理
   ├─ CRITICAL → ブロック（人間承認必須）
   ├─ HIGH → 理由長チェック（50文字以上）
   ├─ MEDIUM → 理由長チェック（20文字以上）
   └─ LOW → 通過
    ↓
4. ファイル操作実行
   ├─ バックアップ作成
   ├─ ファイル書き込み
   └─ ハッシュ計算
    ↓
5. 操作ログ記録
   ├─ file_operation_logs テーブルに挿入
   └─ 結果返却
```

---

## 3. データモデル

### 3.1 制約レベル

```python
class ConstraintLevel(str, Enum):
    """制約レベル"""
    CRITICAL = "critical"  # 変更不可（人間承認必須）
    HIGH = "high"          # 長い理由必須（50文字以上）
    MEDIUM = "medium"      # 短い理由必須（20文字以上）
    LOW = "low"            # 制約なし
```

### 3.2 Pydanticモデル

**ファイル**: `backend/app/services/file_modification/models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum

class ConstraintLevel(str, Enum):
    """制約レベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

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
    operation: Literal["write", "delete", "rename"]
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
```

### 3.3 PostgreSQLスキーマ追加

**ファイル**: `docker/postgres/010_file_modification_service.sql`

```sql
-- ========================================
-- Phase 3: FileModificationService Tables
-- ========================================

-- file_operation_logs（操作ログ）
CREATE TABLE IF NOT EXISTS file_operation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    operation VARCHAR(50) NOT NULL,  -- write, delete, rename, read
    reason TEXT,
    requested_by VARCHAR(100),  -- user, ai_agent, system
    constraint_level VARCHAR(50),
    result VARCHAR(50) NOT NULL,  -- approved, rejected, blocked
    old_content_hash VARCHAR(64),
    new_content_hash VARCHAR(64),
    backup_path VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_file_op_logs_user
    ON file_operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_file
    ON file_operation_logs(file_path);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_time
    ON file_operation_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_operation
    ON file_operation_logs(operation);
CREATE INDEX IF NOT EXISTS idx_file_op_logs_result
    ON file_operation_logs(result);

-- file_backups（バックアップ管理）
CREATE TABLE IF NOT EXISTS file_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    original_path VARCHAR(500) NOT NULL,
    backup_path VARCHAR(500) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    operation_log_id UUID REFERENCES file_operation_logs(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE  -- 自動削除用
);

CREATE INDEX IF NOT EXISTS idx_file_backups_user
    ON file_backups(user_id);
CREATE INDEX IF NOT EXISTS idx_file_backups_original
    ON file_backups(original_path);
CREATE INDEX IF NOT EXISTS idx_file_backups_expires
    ON file_backups(expires_at);

-- 操作統計ビュー
CREATE OR REPLACE VIEW file_operation_stats AS
SELECT
    user_id,
    operation,
    result,
    constraint_level,
    COUNT(*) as count,
    DATE_TRUNC('day', created_at) as day
FROM file_operation_logs
GROUP BY user_id, operation, result, constraint_level, DATE_TRUNC('day', created_at);

-- ユーザー別の最近の操作を取得する関数
CREATE OR REPLACE FUNCTION get_recent_file_operations(
    p_user_id VARCHAR,
    p_limit INT DEFAULT 50
) RETURNS TABLE (
    id UUID,
    file_path VARCHAR,
    operation VARCHAR,
    result VARCHAR,
    constraint_level VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fol.id,
        fol.file_path,
        fol.operation,
        fol.result,
        fol.constraint_level,
        fol.created_at
    FROM file_operation_logs fol
    WHERE fol.user_id = p_user_id
    ORDER BY fol.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

---

## 4. API設計

### 4.1 エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/v1/files/write` | ファイル書き込み |
| POST | `/api/v1/files/delete` | ファイル削除 |
| POST | `/api/v1/files/rename` | ファイル名変更 |
| GET | `/api/v1/files/read` | ファイル読み込み |
| POST | `/api/v1/files/check` | 制約チェックのみ |
| GET | `/api/v1/files/logs` | 操作ログ取得 |
| POST | `/api/v1/files/register-verification` | 検証登録 |

### 4.2 リクエスト/レスポンス例

#### ファイル書き込み

**リクエスト**:
```http
POST /api/v1/files/write
Content-Type: application/json

{
    "user_id": "user123",
    "file_path": "/app/src/api/main.py",
    "operation": "write",
    "content": "# Updated content\nimport fastapi...",
    "reason": "バグ修正: ユーザー認証のエラーハンドリングを改善（Issue #456）",
    "requested_by": "ai_agent"
}
```

**レスポンス（成功）**:
```json
{
    "success": true,
    "operation": "write",
    "file_path": "/app/src/api/main.py",
    "message": "ファイルを書き込みました",
    "constraint_level": "medium",
    "check_result": "approved",
    "backup_path": "/app/backups/main.py.1735500000.bak",
    "file_hash": "sha256:abc123...",
    "timestamp": "2025-12-30T10:00:00Z"
}
```

**レスポンス（ブロック）**:
```json
{
    "success": false,
    "operation": "write",
    "file_path": "/app/src/core/auth.py",
    "message": "CRITICAL制約: このファイルは変更できません。手動承認が必要です。",
    "constraint_level": "critical",
    "check_result": "blocked",
    "backup_path": null,
    "file_hash": null,
    "timestamp": "2025-12-30T10:00:00Z"
}
```

#### 制約チェック

**リクエスト**:
```http
POST /api/v1/files/check
Content-Type: application/json

{
    "user_id": "user123",
    "file_path": "/app/src/api/main.py",
    "operation": "write",
    "reason": "機能追加"
}
```

**レスポンス**:
```json
{
    "file_path": "/app/src/api/main.py",
    "constraint_level": "high",
    "check_result": "pending",
    "can_proceed": false,
    "warning_message": "⚠️ Temporal Constraint Warning!\n\nFile: /app/src/api/main.py\nStatus: VERIFIED (検証済み)\nConstraint Level: HIGH\n...",
    "required_actions": ["reason_required"],
    "questions": ["この変更の目的を記録してください"],
    "min_reason_length": 50
}
```

#### 操作ログ取得

**リクエスト**:
```http
GET /api/v1/files/logs?user_id=user123&limit=20
```

**レスポンス**:
```json
{
    "total": 156,
    "logs": [
        {
            "id": "uuid-001",
            "file_path": "/app/src/api/main.py",
            "operation": "write",
            "result": "approved",
            "constraint_level": "medium",
            "reason": "バグ修正...",
            "created_at": "2025-12-30T10:00:00Z"
        }
    ]
}
```

---

## 5. FileModificationService実装

### 5.1 クラス設計

**ファイル**: `backend/app/services/file_modification/service.py`

```python
import asyncpg
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from .models import (
    FileModificationRequest, FileModificationResult,
    FileReadRequest, FileReadResult, FileOperationLog,
    ConstraintLevel, CheckResult
)
from ..temporal_constraint.checker import TemporalConstraintChecker
from ..temporal_constraint.models import ModificationRequest

logger = logging.getLogger(__name__)


class FileModificationService:
    """統一ファイル操作サービス"""

    # 制約レベルごとの最小理由文字数
    MIN_REASON_LENGTH = {
        ConstraintLevel.CRITICAL: 100,  # 承認必須のため参考値
        ConstraintLevel.HIGH: 50,
        ConstraintLevel.MEDIUM: 20,
        ConstraintLevel.LOW: 0,
    }

    # バックアップディレクトリ
    BACKUP_DIR = Path("/app/backups")

    # 許可されるパスのプレフィックス（セキュリティ）
    ALLOWED_PATHS = [
        "/app/",
        "/home/user/",
        "/tmp/resonant/",
    ]

    # 禁止パターン（セキュリティ）
    FORBIDDEN_PATTERNS = [
        "..",
        "~",
        "/etc/",
        "/root/",
        "/var/",
        ".env",
        "credentials",
        "secret",
    ]

    def __init__(
        self,
        pool: asyncpg.Pool,
        constraint_checker: TemporalConstraintChecker
    ):
        self.pool = pool
        self.constraint_checker = constraint_checker
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # コア操作メソッド
    # ==========================================

    async def read_file(
        self,
        request: FileReadRequest
    ) -> FileReadResult:
        """
        ファイル読み込み（制約チェックなし）

        Args:
            request: 読み込みリクエスト

        Returns:
            FileReadResult: 読み込み結果
        """
        # パス検証
        validation_error = self._validate_path(request.file_path)
        if validation_error:
            return FileReadResult(
                success=False,
                file_path=request.file_path,
                content=None,
                file_hash=None,
                message=validation_error
            )

        path = Path(request.file_path)

        if not path.exists():
            return FileReadResult(
                success=False,
                file_path=request.file_path,
                content=None,
                file_hash=None,
                message=f"ファイルが存在しません: {request.file_path}"
            )

        try:
            content = path.read_text(encoding="utf-8")
            file_hash = self._calculate_hash(content)

            # ログ記録（読み込みも記録）
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="read",
                reason="file read",
                requested_by=request.requested_by,
                constraint_level="low",
                result="approved",
                new_content_hash=file_hash
            )

            return FileReadResult(
                success=True,
                file_path=request.file_path,
                content=content,
                file_hash=file_hash,
                message="ファイルを読み込みました"
            )

        except Exception as e:
            logger.error(f"File read error: {e}")
            return FileReadResult(
                success=False,
                file_path=request.file_path,
                content=None,
                file_hash=None,
                message=f"読み込みエラー: {str(e)}"
            )

    async def write_file(
        self,
        request: FileModificationRequest
    ) -> FileModificationResult:
        """
        ファイル書き込み（制約チェック必須）

        Args:
            request: 書き込みリクエスト

        Returns:
            FileModificationResult: 書き込み結果
        """
        # パス検証
        validation_error = self._validate_path(request.file_path)
        if validation_error:
            return self._create_error_result(
                request, CheckResult.REJECTED, validation_error
            )

        # 制約チェック
        check_result = await self._check_constraint(request)

        if check_result.check_result == CheckResult.BLOCKED:
            return self._create_error_result(
                request, CheckResult.BLOCKED,
                f"CRITICAL制約: このファイルは変更できません。手動承認が必要です。",
                constraint_level=check_result.constraint_level
            )

        if check_result.check_result == CheckResult.PENDING:
            # 理由が不十分
            min_length = self.MIN_REASON_LENGTH.get(
                check_result.constraint_level, 0
            )
            return self._create_error_result(
                request, CheckResult.PENDING,
                f"理由が不十分です（最低{min_length}文字必要、現在{len(request.reason)}文字）",
                constraint_level=check_result.constraint_level
            )

        # ファイル操作実行
        return await self._execute_write(request, check_result.constraint_level)

    async def delete_file(
        self,
        request: FileModificationRequest
    ) -> FileModificationResult:
        """
        ファイル削除（制約チェック必須）
        """
        # パス検証
        validation_error = self._validate_path(request.file_path)
        if validation_error:
            return self._create_error_result(
                request, CheckResult.REJECTED, validation_error
            )

        # 制約チェック
        check_result = await self._check_constraint(request)

        if check_result.check_result in [CheckResult.BLOCKED, CheckResult.PENDING]:
            return self._create_error_result(
                request, check_result.check_result,
                f"ファイル削除がブロックされました: {check_result.constraint_level.value}制約",
                constraint_level=check_result.constraint_level
            )

        # 削除実行
        return await self._execute_delete(request, check_result.constraint_level)

    async def rename_file(
        self,
        request: FileModificationRequest
    ) -> FileModificationResult:
        """
        ファイル名変更（制約チェック必須）
        """
        if not request.new_path:
            return self._create_error_result(
                request, CheckResult.REJECTED,
                "new_path が指定されていません"
            )

        # 両方のパス検証
        for path in [request.file_path, request.new_path]:
            validation_error = self._validate_path(path)
            if validation_error:
                return self._create_error_result(
                    request, CheckResult.REJECTED, validation_error
                )

        # 制約チェック
        check_result = await self._check_constraint(request)

        if check_result.check_result in [CheckResult.BLOCKED, CheckResult.PENDING]:
            return self._create_error_result(
                request, check_result.check_result,
                f"ファイル名変更がブロックされました: {check_result.constraint_level.value}制約",
                constraint_level=check_result.constraint_level
            )

        # リネーム実行
        return await self._execute_rename(request, check_result.constraint_level)

    async def check_constraint(
        self,
        request: FileModificationRequest
    ) -> dict:
        """
        制約チェックのみ実行（ファイル操作なし）
        """
        check_result = await self._check_constraint(request)

        min_length = self.MIN_REASON_LENGTH.get(
            check_result.constraint_level, 0
        )

        return {
            "file_path": request.file_path,
            "constraint_level": check_result.constraint_level.value,
            "check_result": check_result.check_result.value,
            "can_proceed": check_result.check_result == CheckResult.APPROVED,
            "warning_message": check_result.warning_message,
            "required_actions": check_result.required_actions,
            "questions": check_result.questions,
            "min_reason_length": min_length,
            "current_reason_length": len(request.reason)
        }

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
        """
        ファイル検証を登録
        """
        return await self.constraint_checker.register_verification(
            user_id=user_id,
            file_path=file_path,
            verification_type=verification_type,
            test_hours=test_hours,
            constraint_level=constraint_level,
            description=description,
            verified_by=verified_by
        )

    async def get_operation_logs(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        operation: Optional[str] = None,
        result: Optional[str] = None
    ) -> dict:
        """
        操作ログ取得
        """
        async with self.pool.acquire() as conn:
            # 総件数取得
            count_query = """
                SELECT COUNT(*) FROM file_operation_logs
                WHERE user_id = $1
            """
            params = [user_id]

            if operation:
                count_query += " AND operation = $2"
                params.append(operation)
            if result:
                count_query += f" AND result = ${len(params) + 1}"
                params.append(result)

            total = await conn.fetchval(count_query, *params)

            # ログ取得
            query = """
                SELECT id, file_path, operation, reason, requested_by,
                       constraint_level, result, created_at
                FROM file_operation_logs
                WHERE user_id = $1
            """
            params = [user_id]

            if operation:
                query += " AND operation = $2"
                params.append(operation)
            if result:
                query += f" AND result = ${len(params) + 1}"
                params.append(result)

            query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            return {
                "total": total,
                "logs": [dict(row) for row in rows]
            }

    # ==========================================
    # プライベートメソッド
    # ==========================================

    def _validate_path(self, file_path: str) -> Optional[str]:
        """パス検証（セキュリティ）"""
        # 禁止パターンチェック
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in file_path.lower():
                return f"禁止されたパスパターンが含まれています: {pattern}"

        # 許可パスチェック
        allowed = any(
            file_path.startswith(prefix)
            for prefix in self.ALLOWED_PATHS
        )
        if not allowed:
            return f"許可されていないパスです: {file_path}"

        return None

    async def _check_constraint(
        self,
        request: FileModificationRequest
    ):
        """制約チェック実行"""
        mod_request = ModificationRequest(
            user_id=request.user_id,
            file_path=request.file_path,
            modification_type=request.operation,
            modification_reason=request.reason,
            requested_by=request.requested_by
        )

        result = await self.constraint_checker.check_modification(mod_request)

        # CRITICAL は常にブロック
        if result.constraint_level == ConstraintLevel.CRITICAL:
            result.check_result = CheckResult.BLOCKED

        # HIGH/MEDIUM で理由が不十分な場合
        elif result.constraint_level in [ConstraintLevel.HIGH, ConstraintLevel.MEDIUM]:
            min_length = self.MIN_REASON_LENGTH[result.constraint_level]
            if len(request.reason) < min_length and not request.force:
                result.check_result = CheckResult.PENDING

        return result

    async def _execute_write(
        self,
        request: FileModificationRequest,
        constraint_level: ConstraintLevel
    ) -> FileModificationResult:
        """書き込み実行"""
        path = Path(request.file_path)
        backup_path = None
        old_hash = None

        try:
            # バックアップ作成（既存ファイルの場合）
            if path.exists():
                old_content = path.read_text(encoding="utf-8")
                old_hash = self._calculate_hash(old_content)
                backup_path = self._create_backup(path, old_content)

            # 親ディレクトリ作成
            path.parent.mkdir(parents=True, exist_ok=True)

            # 書き込み
            path.write_text(request.content, encoding="utf-8")
            new_hash = self._calculate_hash(request.content)

            # ログ記録
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="write",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="approved",
                old_content_hash=old_hash,
                new_content_hash=new_hash,
                backup_path=str(backup_path) if backup_path else None
            )

            return FileModificationResult(
                success=True,
                operation="write",
                file_path=request.file_path,
                message="ファイルを書き込みました",
                constraint_level=constraint_level,
                check_result=CheckResult.APPROVED,
                backup_path=str(backup_path) if backup_path else None,
                file_hash=new_hash,
                timestamp=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Write error: {e}")

            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="write",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="rejected",
                metadata={"error": str(e)}
            )

            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"書き込みエラー: {str(e)}",
                constraint_level=constraint_level
            )

    async def _execute_delete(
        self,
        request: FileModificationRequest,
        constraint_level: ConstraintLevel
    ) -> FileModificationResult:
        """削除実行"""
        path = Path(request.file_path)

        if not path.exists():
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"ファイルが存在しません: {request.file_path}",
                constraint_level=constraint_level
            )

        try:
            # バックアップ作成
            old_content = path.read_text(encoding="utf-8")
            old_hash = self._calculate_hash(old_content)
            backup_path = self._create_backup(path, old_content)

            # 削除
            path.unlink()

            # ログ記録
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="delete",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="approved",
                old_content_hash=old_hash,
                backup_path=str(backup_path)
            )

            return FileModificationResult(
                success=True,
                operation="delete",
                file_path=request.file_path,
                message="ファイルを削除しました",
                constraint_level=constraint_level,
                check_result=CheckResult.APPROVED,
                backup_path=str(backup_path),
                file_hash=None,
                timestamp=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Delete error: {e}")
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"削除エラー: {str(e)}",
                constraint_level=constraint_level
            )

    async def _execute_rename(
        self,
        request: FileModificationRequest,
        constraint_level: ConstraintLevel
    ) -> FileModificationResult:
        """リネーム実行"""
        old_path = Path(request.file_path)
        new_path = Path(request.new_path)

        if not old_path.exists():
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"ファイルが存在しません: {request.file_path}",
                constraint_level=constraint_level
            )

        if new_path.exists():
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"移動先にファイルが既に存在します: {request.new_path}",
                constraint_level=constraint_level
            )

        try:
            # バックアップ作成
            old_content = old_path.read_text(encoding="utf-8")
            old_hash = self._calculate_hash(old_content)
            backup_path = self._create_backup(old_path, old_content)

            # 親ディレクトリ作成
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # リネーム
            shutil.move(str(old_path), str(new_path))

            # ログ記録
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="rename",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="approved",
                old_content_hash=old_hash,
                new_content_hash=old_hash,
                backup_path=str(backup_path),
                metadata={"new_path": request.new_path}
            )

            return FileModificationResult(
                success=True,
                operation="rename",
                file_path=request.new_path,
                message=f"ファイルを移動しました: {request.file_path} → {request.new_path}",
                constraint_level=constraint_level,
                check_result=CheckResult.APPROVED,
                backup_path=str(backup_path),
                file_hash=old_hash,
                timestamp=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Rename error: {e}")
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"リネームエラー: {str(e)}",
                constraint_level=constraint_level
            )

    def _calculate_hash(self, content: str) -> str:
        """SHA-256ハッシュ計算"""
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

    def _create_backup(self, path: Path, content: str) -> Path:
        """バックアップ作成"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        backup_name = f"{path.name}.{timestamp}.bak"
        backup_path = self.BACKUP_DIR / path.parent.name / backup_name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(content, encoding="utf-8")
        return backup_path

    async def _log_operation(
        self,
        user_id: str,
        file_path: str,
        operation: str,
        reason: str,
        requested_by: str,
        constraint_level: str,
        result: str,
        old_content_hash: Optional[str] = None,
        new_content_hash: Optional[str] = None,
        backup_path: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """操作ログを記録"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO file_operation_logs
                    (user_id, file_path, operation, reason, requested_by,
                     constraint_level, result, old_content_hash,
                     new_content_hash, backup_path, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, user_id, file_path, operation, reason, requested_by,
                constraint_level, result, old_content_hash,
                new_content_hash, backup_path,
                metadata if metadata else None)

    def _create_error_result(
        self,
        request: FileModificationRequest,
        check_result: CheckResult,
        message: str,
        constraint_level: ConstraintLevel = ConstraintLevel.LOW
    ) -> FileModificationResult:
        """エラー結果を作成"""
        return FileModificationResult(
            success=False,
            operation=request.operation,
            file_path=request.file_path,
            message=message,
            constraint_level=constraint_level,
            check_result=check_result,
            backup_path=None,
            file_hash=None,
            timestamp=datetime.now(timezone.utc)
        )
```

---

## 6. APIルーター実装

**ファイル**: `backend/app/routers/file_modification.py`

```python
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.services.file_modification.service import FileModificationService
from app.services.file_modification.models import (
    FileModificationRequest, FileModificationResult,
    FileReadRequest, FileReadResult, ConstraintLevel
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


@router.post("/check")
async def check_constraint(
    request: FileModificationRequest,
    service: FileModificationService = Depends(get_file_modification_service)
):
    """制約チェックのみ実行（ファイル操作なし）"""
    return await service.check_constraint(request)


@router.get("/logs")
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


@router.post("/register-verification")
async def register_verification(
    user_id: str,
    file_path: str,
    verification_type: str,
    test_hours: float = 0,
    constraint_level: ConstraintLevel = ConstraintLevel.MEDIUM,
    description: Optional[str] = None,
    verified_by: Optional[str] = None,
    service: FileModificationService = Depends(get_file_modification_service)
):
    """ファイル検証を登録"""
    verification_id = await service.register_verification(
        user_id=user_id,
        file_path=file_path,
        verification_type=verification_type,
        test_hours=test_hours,
        constraint_level=constraint_level,
        description=description,
        verified_by=verified_by
    )

    return {
        "status": "registered",
        "verification_id": str(verification_id),
        "file_path": file_path,
        "constraint_level": constraint_level.value
    }
```

---

## 7. AIエージェント統合

### 7.1 使用パターン

**推奨される使用方法**:

```python
# AIエージェントがファイルを変更する場合

# 1. まず制約チェック
check_result = await file_service.check_constraint(
    FileModificationRequest(
        user_id="user123",
        file_path="/app/src/main.py",
        operation="write",
        reason="バグ修正"
    )
)

if not check_result["can_proceed"]:
    # ユーザーに確認を求める
    print(check_result["warning_message"])
    print(f"最低{check_result['min_reason_length']}文字の理由が必要です")
    return

# 2. 十分な理由で書き込み
result = await file_service.write_file(
    FileModificationRequest(
        user_id="user123",
        file_path="/app/src/main.py",
        operation="write",
        content=new_content,
        reason="バグ修正: ユーザー認証のエラーハンドリングを改善。既存のtry-catchが不十分でエラーが握りつぶされていた問題を修正（Issue #456）",
        requested_by="ai_agent"
    )
)

if result.success:
    print(f"✅ 書き込み完了: {result.file_path}")
    print(f"   バックアップ: {result.backup_path}")
else:
    print(f"❌ エラー: {result.message}")
```

### 7.2 MCP Server設計（将来）

```json
{
    "name": "resonant-file-server",
    "version": "1.0.0",
    "description": "Resonant Engine File Modification Service MCP Server",
    "tools": [
        {
            "name": "write_file",
            "description": "Write file with temporal constraint check. Requires reason of sufficient length based on constraint level.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    },
                    "reason": {
                        "type": "string",
                        "minLength": 20,
                        "description": "Reason for modification (min 20 chars, 50 for HIGH constraint)"
                    }
                },
                "required": ["file_path", "content", "reason"]
            }
        },
        {
            "name": "read_file",
            "description": "Read file content",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "check_constraint",
            "description": "Check if file can be modified without actually modifying it",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["write", "delete", "rename"]
                    }
                },
                "required": ["file_path", "operation"]
            }
        }
    ]
}
```

---

## 8. セキュリティ考慮事項

### 8.1 パス検証

```python
# 許可されるパス
ALLOWED_PATHS = [
    "/app/",
    "/home/user/",
    "/tmp/resonant/",
]

# 禁止パターン
FORBIDDEN_PATTERNS = [
    "..",           # ディレクトリトラバーサル
    "~",            # ホームディレクトリ展開
    "/etc/",        # システム設定
    "/root/",       # rootディレクトリ
    "/var/",        # システムディレクトリ
    ".env",         # 環境変数ファイル
    "credentials",  # 認証情報
    "secret",       # シークレット
]
```

### 8.2 権限管理

- `user_id` による操作の紐付け
- 操作ログによる監査証跡
- バックアップによる復元可能性

### 8.3 入力検証

- パスの正規化と検証
- コンテンツサイズ制限（将来実装）
- ファイルタイプ制限（将来実装）

---

## 9. 移行計画

### 9.1 Phase 2（Git Hooks）からの移行

```yaml
# 現在: .pre-commit-config.yaml
- repo: local
  hooks:
    - id: temporal-constraint-check
      name: Temporal Constraint Check
      entry: python utils/temporal_constraint_cli.py check --file
      language: system

# Phase 3: APIベースに移行
# Git Hooks は補助的な役割に
```

### 9.2 既存CLIとの並行運用

```bash
# CLIは引き続き利用可能
python utils/temporal_constraint_cli.py check --file path/to/file.py

# 新しいAPIも利用可能
curl -X POST http://localhost:8000/api/v1/files/check \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "file_path": "/app/src/main.py", "operation": "write", "reason": "test"}'
```

---

## 10. 実装フェーズ

### Day 1: データモデル・スキーマ

**目標**:
- PostgreSQLスキーマ作成
- Pydanticモデル定義

**タスク**:
1. `docker/postgres/010_file_modification_service.sql` 作成
2. `backend/app/services/file_modification/models.py` 作成
3. `backend/app/services/file_modification/__init__.py` 作成
4. データベース適用

**成功基準**:
- [ ] テーブルがPostgreSQLに作成済み
- [ ] Pydanticモデルがインポート可能

### Day 2: サービス実装

**目標**:
- FileModificationService 実装
- コア機能の動作確認

**タスク**:
1. `backend/app/services/file_modification/service.py` 作成
2. 単体テスト作成

**成功基準**:
- [ ] read_file, write_file, delete_file, rename_file が動作
- [ ] 制約チェックが動作
- [ ] 単体テスト5件以上作成

### Day 3: API実装

**目標**:
- FastAPIルーター作成
- dependencies.py統合

**タスク**:
1. `backend/app/routers/file_modification.py` 作成
2. `backend/app/dependencies.py` 更新
3. `backend/app/main.py` 登録

**成功基準**:
- [ ] 全APIエンドポイントが動作
- [ ] Swagger UIで確認可能

### Day 4: AIエージェント統合

**目標**:
- 既存システムとの統合
- 使用例ドキュメント

**タスク**:
1. 既存のtemporal_constraint_cli.py との連携確認
2. AIエージェント向け使用ガイド作成

**成功基準**:
- [ ] CLIからAPI呼び出し可能
- [ ] 使用ガイドが完成

### Day 5: テスト・ドキュメント

**目標**:
- 統合テスト作成
- 最終ドキュメント整備

**タスク**:
1. E2Eテスト作成
2. 運用ドキュメント完成
3. MCP Server設計書作成（将来用）

**成功基準**:
- [ ] 統合テスト成功
- [ ] ドキュメント完成

---

## 11. 非機能要件

### 11.1 パフォーマンス目標

| 操作 | 目標 |
|------|------|
| read_file | < 100ms |
| write_file | < 500ms |
| delete_file | < 300ms |
| rename_file | < 300ms |
| check_constraint | < 100ms |

### 11.2 Observability

```python
# Prometheus メトリクス
file_operations_total: Counter  # 操作総数
file_operations_blocked: Counter  # ブロック数
file_operations_duration: Histogram  # 操作時間
constraint_check_duration: Histogram  # チェック時間
```

### 11.3 ログ

```python
# 構造化ログ
{
    "level": "info",
    "event": "file_operation",
    "user_id": "user123",
    "file_path": "/app/src/main.py",
    "operation": "write",
    "constraint_level": "medium",
    "result": "approved",
    "duration_ms": 150
}
```

---

## 12. 参考資料

- [Sprint 12: Term Drift & Temporal Constraint仕様書](../02-01_sprint12/sprint12_term_drift_temporal_constraint_spec.md)
- [Bridge統合移行設計書](../migrations/bridge_integration_migration_spec.md)
- [既存 temporal_constraint_cli.py](../../utils/temporal_constraint_cli.py)

---

**作成日**: 2025-12-30
**作成者**: Kana (Claude Opus 4.5)
**バージョン**: 1.0.0
**推定工数**: 5日間
