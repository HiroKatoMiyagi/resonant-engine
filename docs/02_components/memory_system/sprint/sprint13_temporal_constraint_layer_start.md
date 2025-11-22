# Sprint 13: Temporal Constraint Layer - 作業開始指示書

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**想定期間**: 8-10週間（7日間の集中開発）
**難易度**: ★★★★☆ (高)

---

## 0. Overview

### 目的
ファイルの検証ステータスとテスト工数を追跡し、検証済みコードの変更に対して適切な警告・承認フローを提供するシステムを構築する。

### Done Definition (Tier 1)
- [ ] FileVerificationRegistryサービスクラス実装
- [ ] ChangeGuardサービスクラス実装
- [ ] DependencyAnalyzerサービスクラス実装
- [ ] 変更前警告システム実装
- [ ] Re-evaluation Phase統合
- [ ] 10件以上の単体/統合テスト作成

---

## Day 1: データモデル & PostgreSQLマイグレーション

### 目標
時間軸制約層に必要なデータベーススキーマとPydanticモデルを実装。

### ステップ

#### 1.1 ディレクトリ構造作成

```bash
mkdir -p bridge/temporal_constraint
touch bridge/temporal_constraint/__init__.py
touch bridge/temporal_constraint/models.py
touch bridge/temporal_constraint/registry.py
touch bridge/temporal_constraint/guard.py
touch bridge/temporal_constraint/analyzer.py
touch bridge/temporal_constraint/api_schemas.py
touch bridge/temporal_constraint/api_router.py
```

#### 1.2 Pydanticモデル作成

**ファイル**: `bridge/temporal_constraint/models.py`（新規）

```python
"""Temporal Constraint Layer - Data Models"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timezone
from uuid import UUID, uuid4


class FileVerification(BaseModel):
    """ファイル検証ステータス"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    file_path: str
    file_hash: Optional[str] = None  # SHA256
    verification_status: Literal[
        "pending", "in_progress", "verified", "needs_reverification", "failed"
    ] = "pending"
    test_hours: float = Field(default=0.0, ge=0.0)
    test_cases_count: int = Field(default=0, ge=0)
    coverage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    validity_days: int = Field(default=90, ge=1, le=365)
    verified_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationHistory(BaseModel):
    """検証履歴"""
    id: UUID = Field(default_factory=uuid4)
    verification_id: UUID
    action: Literal["created", "verified", "invalidated", "expired", "reverified"]
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    reason: Optional[str] = None
    test_hours_at_change: Optional[float] = None
    test_cases_at_change: Optional[int] = None
    changed_by: str
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = ["created", "verified", "invalidated", "expired", "reverified"]
        if v not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v


class FileDependency(BaseModel):
    """ファイル依存関係"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    source_file: str
    dependent_file: str
    dependency_type: Literal["import", "test", "config", "api"] = "import"
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

    @field_validator("dependency_type")
    @classmethod
    def validate_dependency_type(cls, v: str) -> str:
        allowed = ["import", "test", "config", "api"]
        if v not in allowed:
            raise ValueError(f"dependency_type must be one of {allowed}")
        return v


class ChangeApproval(BaseModel):
    """変更承認"""
    id: UUID = Field(default_factory=uuid4)
    verification_id: UUID
    user_id: str
    approval_status: Literal["pending", "approved", "rejected", "bypassed"] = "pending"
    approval_type: Literal["normal", "emergency", "exception"] = "normal"
    requested_change: Optional[str] = None
    impact_summary: Optional[Dict[str, Any]] = None
    approval_reason: Optional[str] = None
    requested_by: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None

    @field_validator("approval_status")
    @classmethod
    def validate_approval_status(cls, v: str) -> str:
        allowed = ["pending", "approved", "rejected", "bypassed"]
        if v not in allowed:
            raise ValueError(f"approval_status must be one of {allowed}")
        return v


class ChangeWarning(BaseModel):
    """変更警告"""
    file_path: str
    verification_status: str
    test_hours: float
    test_cases_count: int
    coverage_percent: Optional[float]
    verified_at: Optional[datetime]
    expires_at: Optional[datetime]
    warning_level: Literal["info", "warning", "critical"]
    message: str
    affected_dependents: List[Dict[str, Any]] = Field(default_factory=list)
    total_affected_test_hours: float = 0.0
    recommendations: List[str] = Field(default_factory=list)


class ImpactReport(BaseModel):
    """影響分析レポート"""
    file_path: str
    verification_status: str
    test_hours: float
    direct_dependents: List[Dict[str, Any]] = Field(default_factory=list)
    indirect_dependents: List[Dict[str, Any]] = Field(default_factory=list)
    total_affected_files: int = 0
    total_affected_test_hours: float = 0.0
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    recommendations: List[str] = Field(default_factory=list)
```

#### 1.3 PostgreSQLマイグレーション

**ファイル**: `docker/postgres/010_temporal_constraint_layer.sql`（新規）

```sql
-- Sprint 13: Temporal Constraint Layer
-- 時間軸制約層用テーブル

-- 1. file_verifications: ファイル検証ステータステーブル
CREATE TABLE IF NOT EXISTS file_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- ファイル情報
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),

    -- 検証ステータス
    verification_status VARCHAR(50) DEFAULT 'pending',

    -- テスト工数
    test_hours FLOAT DEFAULT 0,
    test_cases_count INT DEFAULT 0,
    coverage_percent FLOAT CHECK (coverage_percent >= 0 AND coverage_percent <= 100),

    -- 有効期限
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    validity_days INT DEFAULT 90,

    -- メタデータ
    verified_by VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    UNIQUE(user_id, file_path),
    CHECK (verification_status IN ('pending', 'in_progress', 'verified', 'needs_reverification', 'failed'))
);

-- 2. verification_history: 検証履歴テーブル
CREATE TABLE IF NOT EXISTS verification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES file_verifications(id) ON DELETE CASCADE,

    -- 変更情報
    action VARCHAR(50) NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    reason TEXT,

    -- テスト情報スナップショット
    test_hours_at_change FLOAT,
    test_cases_at_change INT,

    -- メタデータ
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    CHECK (action IN ('created', 'verified', 'invalidated', 'expired', 'reverified'))
);

-- 3. file_dependencies: ファイル依存関係テーブル
CREATE TABLE IF NOT EXISTS file_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 依存関係
    source_file TEXT NOT NULL,
    dependent_file TEXT NOT NULL,
    dependency_type VARCHAR(50) DEFAULT 'import',

    -- メタデータ
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- 制約
    UNIQUE(user_id, source_file, dependent_file),
    CHECK (dependency_type IN ('import', 'test', 'config', 'api'))
);

-- 4. change_approvals: 変更承認テーブル
CREATE TABLE IF NOT EXISTS change_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES file_verifications(id),
    user_id VARCHAR(255) NOT NULL,

    -- 承認情報
    approval_status VARCHAR(50) DEFAULT 'pending',
    approval_type VARCHAR(50) NOT NULL,

    -- 詳細
    requested_change TEXT,
    impact_summary JSONB,
    approval_reason TEXT,

    -- メタデータ
    requested_by VARCHAR(255) NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decided_by VARCHAR(255),
    decided_at TIMESTAMP WITH TIME ZONE,

    -- 制約
    CHECK (approval_status IN ('pending', 'approved', 'rejected', 'bypassed')),
    CHECK (approval_type IN ('normal', 'emergency', 'exception'))
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_file_verifications_user_path ON file_verifications(user_id, file_path);
CREATE INDEX IF NOT EXISTS idx_file_verifications_status ON file_verifications(verification_status);
CREATE INDEX IF NOT EXISTS idx_file_verifications_expires ON file_verifications(expires_at);
CREATE INDEX IF NOT EXISTS idx_file_verifications_verified_status ON file_verifications(verification_status)
    WHERE verification_status = 'verified';

CREATE INDEX IF NOT EXISTS idx_verification_history_verification ON verification_history(verification_id);
CREATE INDEX IF NOT EXISTS idx_verification_history_changed_at ON verification_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_verification_history_action ON verification_history(action);

CREATE INDEX IF NOT EXISTS idx_file_dependencies_source ON file_dependencies(source_file);
CREATE INDEX IF NOT EXISTS idx_file_dependencies_dependent ON file_dependencies(dependent_file);
CREATE INDEX IF NOT EXISTS idx_file_dependencies_user ON file_dependencies(user_id);
CREATE INDEX IF NOT EXISTS idx_file_dependencies_active ON file_dependencies(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_change_approvals_status ON change_approvals(approval_status);
CREATE INDEX IF NOT EXISTS idx_change_approvals_verification ON change_approvals(verification_id);
CREATE INDEX IF NOT EXISTS idx_change_approvals_pending ON change_approvals(approval_status)
    WHERE approval_status = 'pending';

-- コメント追加
COMMENT ON TABLE file_verifications IS 'Sprint 13: ファイル検証ステータス管理';
COMMENT ON TABLE verification_history IS 'Sprint 13: 検証ステータスの変更履歴';
COMMENT ON TABLE file_dependencies IS 'Sprint 13: ファイル間の依存関係';
COMMENT ON TABLE change_approvals IS 'Sprint 13: ファイル変更の承認フロー';
```

#### 1.4 モデルテスト

**ファイル**: `tests/temporal_constraint/test_models.py`（新規）

```python
"""Tests for Temporal Constraint Layer models"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from bridge.temporal_constraint.models import (
    FileVerification,
    VerificationHistory,
    FileDependency,
    ChangeApproval,
    ChangeWarning,
    ImpactReport,
)


class TestFileVerificationModel:
    """Test FileVerification model"""

    def test_file_verification_with_all_fields(self):
        """Test creating FileVerification with all fields"""
        verification = FileVerification(
            user_id="hiroki",
            file_path="bridge/memory/service.py",
            file_hash="abc123def456",
            verification_status="verified",
            test_hours=12.5,
            test_cases_count=45,
            coverage_percent=92.5,
            verified_by="hiroki",
        )

        assert verification.user_id == "hiroki"
        assert verification.file_path == "bridge/memory/service.py"
        assert verification.verification_status == "verified"
        assert verification.test_hours == 12.5
        assert verification.test_cases_count == 45
        assert verification.coverage_percent == 92.5

    def test_file_verification_defaults(self):
        """Test default values"""
        verification = FileVerification(
            user_id="hiroki",
            file_path="test.py",
        )

        assert verification.verification_status == "pending"
        assert verification.test_hours == 0.0
        assert verification.test_cases_count == 0
        assert verification.validity_days == 90

    def test_coverage_percent_validation(self):
        """Test coverage_percent must be 0-100"""
        with pytest.raises(ValueError):
            FileVerification(
                user_id="hiroki",
                file_path="test.py",
                coverage_percent=150.0,
            )


class TestVerificationHistoryModel:
    """Test VerificationHistory model"""

    def test_verification_history_with_all_fields(self):
        """Test creating VerificationHistory"""
        history = VerificationHistory(
            verification_id=uuid4(),
            action="verified",
            old_status="pending",
            new_status="verified",
            reason="All tests passed",
            test_hours_at_change=12.5,
            test_cases_at_change=45,
            changed_by="hiroki",
        )

        assert history.action == "verified"
        assert history.old_status == "pending"
        assert history.new_status == "verified"

    def test_invalid_action(self):
        """Test invalid action raises error"""
        with pytest.raises(ValueError):
            VerificationHistory(
                verification_id=uuid4(),
                action="invalid_action",
                changed_by="hiroki",
            )


class TestFileDependencyModel:
    """Test FileDependency model"""

    def test_file_dependency_valid(self):
        """Test valid FileDependency"""
        for dep_type in ["import", "test", "config", "api"]:
            dep = FileDependency(
                user_id="hiroki",
                source_file="service.py",
                dependent_file="models.py",
                dependency_type=dep_type,
            )
            assert dep.dependency_type == dep_type

    def test_invalid_dependency_type(self):
        """Test invalid dependency_type raises error"""
        with pytest.raises(ValueError):
            FileDependency(
                user_id="hiroki",
                source_file="service.py",
                dependent_file="models.py",
                dependency_type="invalid",
            )


class TestChangeApprovalModel:
    """Test ChangeApproval model"""

    def test_change_approval_valid(self):
        """Test valid ChangeApproval"""
        approval = ChangeApproval(
            verification_id=uuid4(),
            user_id="hiroki",
            approval_status="pending",
            approval_type="normal",
            requested_change="Add new method",
            requested_by="hiroki",
        )

        assert approval.approval_status == "pending"
        assert approval.approval_type == "normal"

    def test_invalid_approval_status(self):
        """Test invalid approval_status raises error"""
        with pytest.raises(ValueError):
            ChangeApproval(
                verification_id=uuid4(),
                user_id="hiroki",
                approval_type="normal",
                approval_status="invalid",
                requested_by="hiroki",
            )


class TestChangeWarningModel:
    """Test ChangeWarning model"""

    def test_change_warning_complete(self):
        """Test complete ChangeWarning"""
        warning = ChangeWarning(
            file_path="service.py",
            verification_status="verified",
            test_hours=12.5,
            test_cases_count=45,
            coverage_percent=92.5,
            verified_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
            warning_level="warning",
            message="Protected file modification",
            affected_dependents=[{"file": "router.py", "test_hours": 5.0}],
            total_affected_test_hours=17.5,
            recommendations=["Run tests after modification"],
        )

        assert warning.warning_level == "warning"
        assert warning.total_affected_test_hours == 17.5


class TestImpactReportModel:
    """Test ImpactReport model"""

    def test_impact_report_complete(self):
        """Test complete ImpactReport"""
        report = ImpactReport(
            file_path="models.py",
            verification_status="verified",
            test_hours=25.0,
            direct_dependents=[{"file": "service.py", "test_hours": 12.5}],
            indirect_dependents=[{"file": "router.py", "test_hours": 5.0}],
            total_affected_files=3,
            total_affected_test_hours=42.5,
            risk_level="high",
            recommendations=["Incremental changes recommended"],
        )

        assert report.risk_level == "high"
        assert report.total_affected_files == 3
```

### Day 1 成功基準
- [ ] ディレクトリ構造作成完了
- [ ] 6つのPydanticモデル実装完了
- [ ] PostgreSQLマイグレーション（4テーブル）作成完了
- [ ] 10件以上のモデルテスト作成

### Git Commit
```bash
git add bridge/temporal_constraint/ docker/postgres/010_temporal_constraint_layer.sql tests/temporal_constraint/
git commit -m "feat: Sprint 13 Day 1 - Temporal Constraint Layer data models & PostgreSQL migration"
```

---

## Day 2: FileVerificationRegistry実装

### 目標
ファイル検証ステータスの登録・更新・検索を行うFileVerificationRegistryサービスを実装。

### ステップ

#### 2.1 FileVerificationRegistry実装

**ファイル**: `bridge/temporal_constraint/registry.py`（新規）

```python
"""File Verification Registry Service"""

import asyncpg
import hashlib
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID

from .models import FileVerification, VerificationHistory

logger = logging.getLogger(__name__)


class FileVerificationRegistry:
    """ファイル検証レジストリサービス"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def register_verification(
        self,
        user_id: str,
        file_path: str,
        verification_status: str = "pending",
        test_hours: float = 0,
        test_cases_count: int = 0,
        coverage_percent: Optional[float] = None,
        validity_days: int = 90,
        verified_by: Optional[str] = None,
        notes: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> FileVerification:
        """
        ファイル検証を登録

        Args:
            user_id: ユーザーID
            file_path: ファイルパス
            verification_status: 検証ステータス
            test_hours: テスト工数（時間）
            test_cases_count: テストケース数
            coverage_percent: カバレッジ（%）
            validity_days: 有効日数（デフォルト90日）
            verified_by: 検証者
            notes: 備考
            file_hash: ファイルハッシュ

        Returns:
            FileVerification: 登録された検証情報
        """
        verified_by = verified_by or user_id

        # 有効期限の計算
        verified_at = None
        expires_at = None
        if verification_status == "verified":
            verified_at = datetime.now(timezone.utc)
            expires_at = verified_at + timedelta(days=validity_days)

        async with self.pool.acquire() as conn:
            # 既存チェック
            existing = await conn.fetchrow("""
                SELECT id FROM file_verifications
                WHERE user_id = $1 AND file_path = $2
            """, user_id, file_path)

            if existing:
                raise ValueError(f"Verification for '{file_path}' already exists")

            # 検証登録
            row = await conn.fetchrow("""
                INSERT INTO file_verifications
                    (user_id, file_path, file_hash, verification_status,
                     test_hours, test_cases_count, coverage_percent,
                     verified_at, expires_at, validity_days,
                     verified_by, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
            """, user_id, file_path, file_hash, verification_status,
                test_hours, test_cases_count, coverage_percent,
                verified_at, expires_at, validity_days,
                verified_by, notes)

            verification = FileVerification(**dict(row))

            # 履歴を記録
            await conn.execute("""
                INSERT INTO verification_history
                    (verification_id, action, new_status, changed_by)
                VALUES ($1, 'created', $2, $3)
            """, verification.id, verification_status, verified_by)

            logger.info(f"Verification registered: {file_path} (status: {verification_status})")

            return verification

    async def update_verification(
        self,
        verification_id: UUID,
        verification_status: str,
        test_hours: Optional[float] = None,
        test_cases_count: Optional[int] = None,
        coverage_percent: Optional[float] = None,
        changed_by: str,
        reason: str,
    ) -> FileVerification:
        """
        検証ステータスを更新

        Args:
            verification_id: 検証ID
            verification_status: 新しいステータス
            test_hours: テスト工数
            test_cases_count: テストケース数
            coverage_percent: カバレッジ
            changed_by: 変更者
            reason: 変更理由

        Returns:
            FileVerification: 更新された検証情報
        """
        async with self.pool.acquire() as conn:
            # 現在の検証情報を取得
            current = await conn.fetchrow("""
                SELECT * FROM file_verifications WHERE id = $1
            """, verification_id)

            if not current:
                raise ValueError(f"Verification {verification_id} not found")

            old_status = current["verification_status"]

            # 有効期限の更新
            verified_at = current["verified_at"]
            expires_at = current["expires_at"]
            if verification_status == "verified" and old_status != "verified":
                verified_at = datetime.now(timezone.utc)
                expires_at = verified_at + timedelta(days=current["validity_days"])

            # 更新値の決定
            new_test_hours = test_hours if test_hours is not None else current["test_hours"]
            new_test_cases = test_cases_count if test_cases_count is not None else current["test_cases_count"]
            new_coverage = coverage_percent if coverage_percent is not None else current["coverage_percent"]

            # 検証情報を更新
            row = await conn.fetchrow("""
                UPDATE file_verifications
                SET verification_status = $1,
                    test_hours = $2,
                    test_cases_count = $3,
                    coverage_percent = $4,
                    verified_at = $5,
                    expires_at = $6,
                    updated_at = NOW()
                WHERE id = $7
                RETURNING *
            """, verification_status, new_test_hours, new_test_cases,
                new_coverage, verified_at, expires_at, verification_id)

            verification = FileVerification(**dict(row))

            # 履歴を記録
            action = "reverified" if verification_status == "verified" else "verified"
            if verification_status == "needs_reverification":
                action = "invalidated"

            await conn.execute("""
                INSERT INTO verification_history
                    (verification_id, action, old_status, new_status, reason,
                     test_hours_at_change, test_cases_at_change, changed_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, verification_id, action, old_status, verification_status,
                reason, new_test_hours, new_test_cases, changed_by)

            logger.info(f"Verification updated: {verification.file_path} ({old_status} -> {verification_status})")

            return verification

    async def get_verification(
        self,
        user_id: str,
        file_path: str,
    ) -> Optional[FileVerification]:
        """ファイルの検証情報を取得"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM file_verifications
                WHERE user_id = $1 AND file_path = $2
            """, user_id, file_path)

            if row:
                return FileVerification(**dict(row))
            return None

    async def get_verification_by_id(
        self,
        verification_id: UUID,
    ) -> Optional[FileVerification]:
        """IDで検証情報を取得"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM file_verifications WHERE id = $1
            """, verification_id)

            if row:
                return FileVerification(**dict(row))
            return None

    async def get_expiring_verifications(
        self,
        user_id: str,
        days_until_expiry: int = 14,
    ) -> List[FileVerification]:
        """期限切れ間近の検証を取得"""
        expiry_threshold = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM file_verifications
                WHERE user_id = $1
                  AND verification_status = 'verified'
                  AND expires_at <= $2
                  AND expires_at > NOW()
                ORDER BY expires_at ASC
            """, user_id, expiry_threshold)

            return [FileVerification(**dict(row)) for row in rows]

    async def invalidate_verification(
        self,
        verification_id: UUID,
        reason: str,
        invalidated_by: str,
    ) -> VerificationHistory:
        """検証を失効"""
        async with self.pool.acquire() as conn:
            # 現在の検証情報を取得
            current = await conn.fetchrow("""
                SELECT * FROM file_verifications WHERE id = $1
            """, verification_id)

            if not current:
                raise ValueError(f"Verification {verification_id} not found")

            old_status = current["verification_status"]

            # ステータスを更新
            await conn.execute("""
                UPDATE file_verifications
                SET verification_status = 'needs_reverification',
                    updated_at = NOW()
                WHERE id = $1
            """, verification_id)

            # 履歴を記録
            history_row = await conn.fetchrow("""
                INSERT INTO verification_history
                    (verification_id, action, old_status, new_status, reason,
                     test_hours_at_change, test_cases_at_change, changed_by)
                VALUES ($1, 'invalidated', $2, 'needs_reverification', $3, $4, $5, $6)
                RETURNING *
            """, verification_id, old_status, reason,
                current["test_hours"], current["test_cases_count"], invalidated_by)

            logger.info(f"Verification invalidated: {current['file_path']} (reason: {reason})")

            return VerificationHistory(**dict(history_row))

    async def get_all_verifications(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
    ) -> List[FileVerification]:
        """全検証情報を取得"""
        async with self.pool.acquire() as conn:
            if status_filter:
                rows = await conn.fetch("""
                    SELECT * FROM file_verifications
                    WHERE user_id = $1 AND verification_status = $2
                    ORDER BY file_path
                """, user_id, status_filter)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM file_verifications
                    WHERE user_id = $1
                    ORDER BY file_path
                """, user_id)

            return [FileVerification(**dict(row)) for row in rows]

    async def get_verification_history(
        self,
        verification_id: UUID,
    ) -> List[VerificationHistory]:
        """検証履歴を取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM verification_history
                WHERE verification_id = $1
                ORDER BY changed_at DESC
            """, verification_id)

            return [VerificationHistory(**dict(row)) for row in rows]
```

### Day 2 成功基準
- [ ] FileVerificationRegistry実装完了（8メソッド）
- [ ] 検証有効期限計算実装
- [ ] 単体テスト6件以上作成

### Git Commit
```bash
git add bridge/temporal_constraint/registry.py tests/temporal_constraint/test_registry.py
git commit -m "feat: Sprint 13 Day 2 - FileVerificationRegistry service implementation"
```

---

## Day 3: ChangeGuard実装

### 目標
変更前チェックと警告生成を行うChangeGuardサービスを実装。

### ステップ

#### 3.1 ChangeGuard実装

**ファイル**: `bridge/temporal_constraint/guard.py`（新規）

```python
"""Change Guard Service"""

import asyncpg
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from .models import FileVerification, ChangeApproval, ChangeWarning
from .registry import FileVerificationRegistry

logger = logging.getLogger(__name__)


class ChangeGuard:
    """変更ガードサービス"""

    # 警告レベルの閾値（テスト工数時間）
    WARNING_THRESHOLDS = {
        "info": 2.0,      # 2時間未満 -> info
        "warning": 10.0,  # 2-10時間 -> warning
        "critical": 10.0, # 10時間以上 -> critical
    }

    def __init__(self, pool: asyncpg.Pool, registry: FileVerificationRegistry):
        self.pool = pool
        self.registry = registry

    async def check_file_modification(
        self,
        user_id: str,
        file_path: str,
    ) -> Optional[ChangeWarning]:
        """
        ファイル変更の可否をチェック

        Args:
            user_id: ユーザーID
            file_path: ファイルパス

        Returns:
            ChangeWarning: 警告情報（警告が必要な場合）
            None: 警告不要な場合
        """
        verification = await self.registry.get_verification(user_id, file_path)

        if not verification:
            # 未検証ファイル -> 警告なし
            return None

        if verification.verification_status != "verified":
            # 検証済みでない -> 警告なし
            return None

        # 警告レベルを決定
        warning_level = self._determine_warning_level(verification.test_hours)

        # 影響を受ける依存ファイルを取得
        affected_dependents = await self._get_affected_dependents(user_id, file_path)
        total_affected_hours = verification.test_hours + sum(
            d.get("test_hours", 0) for d in affected_dependents
        )

        # 推奨アクションを生成
        recommendations = self._generate_recommendations(
            verification, affected_dependents
        )

        # 警告メッセージを生成
        message = self._generate_warning_message(verification, warning_level)

        return ChangeWarning(
            file_path=file_path,
            verification_status=verification.verification_status,
            test_hours=verification.test_hours,
            test_cases_count=verification.test_cases_count,
            coverage_percent=verification.coverage_percent,
            verified_at=verification.verified_at,
            expires_at=verification.expires_at,
            warning_level=warning_level,
            message=message,
            affected_dependents=affected_dependents,
            total_affected_test_hours=total_affected_hours,
            recommendations=recommendations,
        )

    def _determine_warning_level(self, test_hours: float) -> str:
        """警告レベルを決定"""
        if test_hours >= self.WARNING_THRESHOLDS["critical"]:
            return "critical"
        elif test_hours >= self.WARNING_THRESHOLDS["info"]:
            return "warning"
        return "info"

    async def _get_affected_dependents(
        self,
        user_id: str,
        file_path: str,
    ) -> List[Dict[str, Any]]:
        """影響を受ける依存ファイルを取得"""
        affected = []

        async with self.pool.acquire() as conn:
            # 依存ファイルを取得
            deps = await conn.fetch("""
                SELECT fd.dependent_file, fv.test_hours, fv.verification_status
                FROM file_dependencies fd
                LEFT JOIN file_verifications fv
                    ON fd.user_id = fv.user_id AND fd.dependent_file = fv.file_path
                WHERE fd.user_id = $1 AND fd.source_file = $2 AND fd.is_active = TRUE
            """, user_id, file_path)

            for dep in deps:
                affected.append({
                    "file": dep["dependent_file"],
                    "test_hours": dep["test_hours"] or 0,
                    "status": dep["verification_status"] or "unknown",
                })

        return affected

    def _generate_recommendations(
        self,
        verification: FileVerification,
        affected_dependents: List[Dict[str, Any]],
    ) -> List[str]:
        """推奨アクションを生成"""
        recommendations = []

        if verification.test_hours > 20:
            recommendations.append(
                "高テスト工数のファイルです。変更前にテスト計画を立ててください。"
            )

        if len(affected_dependents) > 5:
            recommendations.append(
                f"{len(affected_dependents)}個のファイルに影響があります。段階的な変更を推奨します。"
            )

        if verification.coverage_percent and verification.coverage_percent > 80:
            recommendations.append(
                "高カバレッジのファイルです。変更後は全テストの実行を推奨します。"
            )

        if not recommendations:
            recommendations.append("変更後にテストを実行してください。")

        return recommendations

    def _generate_warning_message(
        self,
        verification: FileVerification,
        warning_level: str,
    ) -> str:
        """警告メッセージを生成"""
        if warning_level == "critical":
            return f"⚠️ CRITICAL: このファイルは{verification.test_hours:.1f}時間のテスト工数で検証済みです。変更には承認が必要です。"
        elif warning_level == "warning":
            return f"⚠️ WARNING: このファイルは検証済みです（テスト工数: {verification.test_hours:.1f}時間）。変更後の再検証を推奨します。"
        return f"ℹ️ INFO: このファイルは検証済みです（テスト工数: {verification.test_hours:.1f}時間）。"

    async def request_approval(
        self,
        verification_id: UUID,
        requested_change: str,
        requested_by: str,
        approval_type: str = "normal",
        impact_summary: Optional[Dict[str, Any]] = None,
    ) -> ChangeApproval:
        """変更承認をリクエスト"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO change_approvals
                    (verification_id, user_id, approval_type, requested_change,
                     impact_summary, requested_by)
                SELECT id, user_id, $2, $3, $4, $5
                FROM file_verifications WHERE id = $1
                RETURNING *
            """, verification_id, approval_type, requested_change,
                impact_summary, requested_by)

            logger.info(f"Approval requested for verification {verification_id}")

            return ChangeApproval(**dict(row))

    async def approve_change(
        self,
        approval_id: UUID,
        decided_by: str,
        approval_reason: str,
    ) -> ChangeApproval:
        """変更を承認"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE change_approvals
                SET approval_status = 'approved',
                    decided_by = $1,
                    approval_reason = $2,
                    decided_at = NOW()
                WHERE id = $3
                RETURNING *
            """, decided_by, approval_reason, approval_id)

            if not row:
                raise ValueError(f"Approval {approval_id} not found")

            logger.info(f"Change approved: {approval_id}")

            return ChangeApproval(**dict(row))

    async def bypass_change(
        self,
        approval_id: UUID,
        bypassed_by: str,
        bypass_reason: str,
    ) -> ChangeApproval:
        """変更をバイパス（緊急時）"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE change_approvals
                SET approval_status = 'bypassed',
                    decided_by = $1,
                    approval_reason = $2,
                    decided_at = NOW()
                WHERE id = $3
                RETURNING *
            """, bypassed_by, bypass_reason, approval_id)

            if not row:
                raise ValueError(f"Approval {approval_id} not found")

            logger.warning(f"Change bypassed: {approval_id} (reason: {bypass_reason})")

            return ChangeApproval(**dict(row))

    async def get_pending_approvals(
        self,
        user_id: str,
    ) -> List[ChangeApproval]:
        """未処理の承認リクエストを取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM change_approvals
                WHERE user_id = $1 AND approval_status = 'pending'
                ORDER BY requested_at DESC
            """, user_id)

            return [ChangeApproval(**dict(row)) for row in rows]
```

### Day 3 成功基準
- [ ] ChangeGuard実装完了（8メソッド）
- [ ] 警告レベル判定ロジック実装
- [ ] 単体テスト6件以上作成

### Git Commit
```bash
git add bridge/temporal_constraint/guard.py tests/temporal_constraint/test_guard.py
git commit -m "feat: Sprint 13 Day 3 - ChangeGuard service implementation"
```

---

## Day 4: DependencyAnalyzer実装

### 目標
ファイル依存関係の分析と影響範囲の計算を行うDependencyAnalyzerサービスを実装。

### ステップ

#### 4.1 DependencyAnalyzer実装

**ファイル**: `bridge/temporal_constraint/analyzer.py`（新規）

```python
"""Dependency Analyzer Service"""

import asyncpg
import logging
import re
from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from pathlib import Path

from .models import FileDependency, ImpactReport
from .registry import FileVerificationRegistry

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """依存関係分析サービス"""

    # リスクレベルの閾値
    RISK_THRESHOLDS = {
        "low": 10.0,      # 10時間未満
        "medium": 30.0,   # 30時間未満
        "high": 50.0,     # 50時間未満
        "critical": 50.0, # 50時間以上
    }

    def __init__(self, pool: asyncpg.Pool, registry: FileVerificationRegistry):
        self.pool = pool
        self.registry = registry

    async def register_dependency(
        self,
        user_id: str,
        source_file: str,
        dependent_file: str,
        dependency_type: str = "import",
    ) -> FileDependency:
        """依存関係を登録"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO file_dependencies
                    (user_id, source_file, dependent_file, dependency_type)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, source_file, dependent_file)
                DO UPDATE SET is_active = TRUE, detected_at = NOW()
                RETURNING *
            """, user_id, source_file, dependent_file, dependency_type)

            return FileDependency(**dict(row))

    async def get_dependents(
        self,
        user_id: str,
        file_path: str,
        include_indirect: bool = True,
    ) -> List[FileDependency]:
        """依存先ファイルを取得"""
        async with self.pool.acquire() as conn:
            # 直接依存
            direct = await conn.fetch("""
                SELECT * FROM file_dependencies
                WHERE user_id = $1 AND source_file = $2 AND is_active = TRUE
            """, user_id, file_path)

            direct_deps = [FileDependency(**dict(row)) for row in direct]

            if not include_indirect:
                return direct_deps

            # 間接依存を再帰的に取得
            all_deps = list(direct_deps)
            visited: Set[str] = {file_path}

            for dep in direct_deps:
                if dep.dependent_file not in visited:
                    visited.add(dep.dependent_file)
                    indirect = await self.get_dependents(
                        user_id, dep.dependent_file, include_indirect=True
                    )
                    for ind in indirect:
                        if ind.dependent_file not in visited:
                            all_deps.append(ind)
                            visited.add(ind.dependent_file)

            return all_deps

    async def analyze_change_impact(
        self,
        user_id: str,
        file_path: str,
    ) -> ImpactReport:
        """変更影響を分析"""
        verification = await self.registry.get_verification(user_id, file_path)

        test_hours = verification.test_hours if verification else 0.0
        status = verification.verification_status if verification else "unknown"

        # 直接依存を取得
        direct_deps = await self.get_dependents(user_id, file_path, include_indirect=False)

        direct_info = []
        direct_hours = 0.0

        for dep in direct_deps:
            dep_verification = await self.registry.get_verification(
                user_id, dep.dependent_file
            )
            dep_hours = dep_verification.test_hours if dep_verification else 0.0
            dep_status = dep_verification.verification_status if dep_verification else "unknown"

            direct_info.append({
                "file": dep.dependent_file,
                "test_hours": dep_hours,
                "status": dep_status,
                "dependency_type": dep.dependency_type,
            })
            direct_hours += dep_hours

        # 間接依存を取得
        all_deps = await self.get_dependents(user_id, file_path, include_indirect=True)
        indirect_deps = [d for d in all_deps if d not in direct_deps]

        indirect_info = []
        indirect_hours = 0.0

        for dep in indirect_deps:
            dep_verification = await self.registry.get_verification(
                user_id, dep.dependent_file
            )
            dep_hours = dep_verification.test_hours if dep_verification else 0.0
            dep_status = dep_verification.verification_status if dep_verification else "unknown"

            indirect_info.append({
                "file": dep.dependent_file,
                "test_hours": dep_hours,
                "status": dep_status,
            })
            indirect_hours += dep_hours

        total_hours = test_hours + direct_hours + indirect_hours
        total_files = 1 + len(direct_info) + len(indirect_info)

        # リスクレベルを決定
        risk_level = self._determine_risk_level(total_hours)

        # 推奨アクションを生成
        recommendations = self._generate_impact_recommendations(
            total_hours, total_files, status
        )

        return ImpactReport(
            file_path=file_path,
            verification_status=status,
            test_hours=test_hours,
            direct_dependents=direct_info,
            indirect_dependents=indirect_info,
            total_affected_files=total_files,
            total_affected_test_hours=total_hours,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    def _determine_risk_level(self, total_hours: float) -> str:
        """リスクレベルを決定"""
        if total_hours >= self.RISK_THRESHOLDS["critical"]:
            return "critical"
        elif total_hours >= self.RISK_THRESHOLDS["high"]:
            return "high"
        elif total_hours >= self.RISK_THRESHOLDS["medium"]:
            return "medium"
        return "low"

    def _generate_impact_recommendations(
        self,
        total_hours: float,
        total_files: int,
        status: str,
    ) -> List[str]:
        """影響分析の推奨アクションを生成"""
        recommendations = []

        if total_hours >= 50:
            recommendations.append(
                "非常に高い影響度です。変更は段階的に行い、各段階でテストを実施してください。"
            )

        if total_files >= 10:
            recommendations.append(
                f"{total_files}個のファイルに影響があります。変更計画を立てることを推奨します。"
            )

        if status == "verified":
            recommendations.append(
                "検証済みファイルです。変更後は再検証が必要です。"
            )

        if not recommendations:
            recommendations.append("影響範囲は限定的です。通常の変更プロセスで問題ありません。")

        return recommendations

    async def remove_dependency(
        self,
        user_id: str,
        source_file: str,
        dependent_file: str,
    ) -> bool:
        """依存関係を削除（非アクティブ化）"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE file_dependencies
                SET is_active = FALSE
                WHERE user_id = $1 AND source_file = $2 AND dependent_file = $3
            """, user_id, source_file, dependent_file)

            return result == "UPDATE 1"

    async def get_dependencies_for_file(
        self,
        user_id: str,
        file_path: str,
    ) -> List[FileDependency]:
        """ファイルが依存しているファイルを取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM file_dependencies
                WHERE user_id = $1 AND dependent_file = $2 AND is_active = TRUE
            """, user_id, file_path)

            return [FileDependency(**dict(row)) for row in rows]
```

### Day 4 成功基準
- [ ] DependencyAnalyzer実装完了（6メソッド）
- [ ] リスクレベル判定ロジック実装
- [ ] 単体テスト6件以上作成

### Git Commit
```bash
git add bridge/temporal_constraint/analyzer.py tests/temporal_constraint/test_analyzer.py
git commit -m "feat: Sprint 13 Day 4 - DependencyAnalyzer service implementation"
```

---

## Day 5: API Router実装

### 目標
APIスキーマとエンドポイントを実装。

### Day 5 成功基準
- [ ] APIスキーマ実装完了
- [ ] API Router実装完了（12エンドポイント）
- [ ] API統合テスト3件以上作成

### Git Commit
```bash
git add bridge/temporal_constraint/api_schemas.py bridge/temporal_constraint/api_router.py
git commit -m "feat: Sprint 13 Day 5 - API Router implementation"
```

---

## Day 6: Re-evaluation Phase統合

### 目標
Re-evaluation Phaseとの統合を実装。

### Day 6 成功基準
- [ ] Re-evaluation Phase統合完了
- [ ] ファイル変更時の自動失効機能
- [ ] 統合テスト3件以上作成

### Git Commit
```bash
git add bridge/temporal_constraint/integration.py tests/integration/
git commit -m "feat: Sprint 13 Day 6 - Re-evaluation Phase integration"
```

---

## Day 7: テスト & ドキュメント

### 目標
包括的なテストスイートとAPIドキュメント作成。

### Day 7 成功基準
- [ ] E2Eテスト5件以上作成
- [ ] APIドキュメント完成
- [ ] パフォーマンステスト実施
- [ ] 完了レポート作成

### Git Commit
```bash
git add tests/ docs/
git commit -m "feat: Sprint 13 Day 7 - E2E tests & API documentation"
```

---

## 完了後チェックリスト

### 機能実装
- [ ] FileVerificationRegistryサービス実装
- [ ] ChangeGuardサービス実装
- [ ] DependencyAnalyzerサービス実装
- [ ] APIエンドポイント12件実装
- [ ] Re-evaluation Phase統合

### テスト
- [ ] 単体テスト15件以上
- [ ] 統合テスト5件以上
- [ ] E2Eテスト5件以上
- [ ] パフォーマンステスト実施

### ドキュメント
- [ ] APIドキュメント完成
- [ ] 完了レポート作成

---

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
