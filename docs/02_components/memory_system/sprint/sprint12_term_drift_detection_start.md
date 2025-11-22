# Sprint 12: Term Drift Detection - 作業開始指示書

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**想定期間**: 6-8週間（6日間の集中開発）
**難易度**: ★★★☆☆ (中〜高)

---

## 0. Overview

### 目的
プロジェクト内の用語定義を一元管理し、**用語の意味が時間とともに変化（ドリフト）**することを検出・追跡・警告するシステムを構築する。

### Done Definition (Tier 1)
- [ ] TermRegistryサービスクラス実装
- [ ] 用語定義の登録・更新・履歴管理
- [ ] 用語使用箇所のスキャン機能
- [ ] ドリフト検出アルゴリズム実装
- [ ] Intent Bridge統合
- [ ] 10件以上の単体/統合テスト作成

---

## Day 1: データモデル & PostgreSQLマイグレーション

### 目標
用語ドリフト検出に必要なデータベーススキーマとPydanticモデルを実装。

### ステップ

#### 1.1 ディレクトリ構造作成

```bash
mkdir -p bridge/term_drift
touch bridge/term_drift/__init__.py
touch bridge/term_drift/models.py
touch bridge/term_drift/registry.py
touch bridge/term_drift/scanner.py
touch bridge/term_drift/detector.py
touch bridge/term_drift/impact.py
touch bridge/term_drift/api_schemas.py
touch bridge/term_drift/api_router.py
```

#### 1.2 Pydanticモデル作成

**ファイル**: `bridge/term_drift/models.py`（新規）

```python
"""Term Drift Detection - Data Models"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4


class TermDefinition(BaseModel):
    """用語定義"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    term: str = Field(min_length=1, max_length=255)
    definition: str = Field(min_length=1)
    scope: str = "global"  # 'global', 'authentication', 'analytics', etc.
    version: int = 1
    is_active: bool = True
    superseded_by: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("scope must be <= 100 characters")
        return v.lower()


class TermAlias(BaseModel):
    """用語エイリアス"""
    id: UUID = Field(default_factory=uuid4)
    term_id: UUID
    alias: str = Field(min_length=1, max_length=255)
    context: Optional[str] = None  # NULL = 全コンテキスト
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TermVersion(BaseModel):
    """用語バージョン履歴"""
    id: UUID = Field(default_factory=uuid4)
    term_id: UUID
    old_definition: str
    new_definition: str
    change_reason: Optional[str] = None
    semantic_diff_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    changed_by: str


class TermUsage(BaseModel):
    """用語使用箇所"""
    id: UUID = Field(default_factory=uuid4)
    term_id: UUID
    user_id: str
    source_type: str
    source_id: Optional[UUID] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    context: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    drift_detected: bool = False
    drift_type: Optional[str] = None
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        allowed = ["intent", "code_comment", "documentation", "choice_point"]
        if v not in allowed:
            raise ValueError(f"source_type must be one of {allowed}")
        return v


class TermDriftAlert(BaseModel):
    """用語ドリフトアラート"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    term_id: UUID
    usage_id: Optional[UUID] = None
    alert_type: str
    severity: str = "warning"
    message: str
    detected_context: Optional[str] = None
    expected_definition: Optional[str] = None
    resolution_status: str = "pending"
    resolution_action: Optional[str] = None
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        allowed = ["definition_drift", "context_mismatch", "alias_conflict"]
        if v not in allowed:
            raise ValueError(f"alert_type must be one of {allowed}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = ["info", "warning", "critical"]
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v

    @field_validator("resolution_status")
    @classmethod
    def validate_resolution_status(cls, v: str) -> str:
        allowed = ["pending", "resolved", "dismissed"]
        if v not in allowed:
            raise ValueError(f"resolution_status must be one of {allowed}")
        return v
```

#### 1.3 PostgreSQLマイグレーション

**ファイル**: `docker/postgres/009_term_drift_detection.sql`（新規）

```sql
-- Sprint 12: Term Drift Detection Layer
-- 用語ドリフト検出用テーブル

-- 1. term_definitions: 用語定義テーブル
CREATE TABLE IF NOT EXISTS term_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 用語情報
    term VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    scope VARCHAR(100) DEFAULT 'global',

    -- バージョン管理
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES term_definitions(id),

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    UNIQUE(user_id, term, scope, version)
);

-- 2. term_aliases: エイリアステーブル
CREATE TABLE IF NOT EXISTS term_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_id UUID NOT NULL REFERENCES term_definitions(id) ON DELETE CASCADE,

    -- エイリアス情報
    alias VARCHAR(255) NOT NULL,
    context VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    UNIQUE(term_id, alias, context)
);

-- 3. term_versions: バージョン履歴テーブル
CREATE TABLE IF NOT EXISTS term_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_id UUID NOT NULL REFERENCES term_definitions(id) ON DELETE CASCADE,

    -- 変更情報
    old_definition TEXT NOT NULL,
    new_definition TEXT NOT NULL,
    change_reason TEXT,
    semantic_diff_score FLOAT CHECK (semantic_diff_score >= 0 AND semantic_diff_score <= 1),

    -- メタデータ
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changed_by VARCHAR(255) NOT NULL
);

-- 4. term_usages: 使用箇所テーブル
CREATE TABLE IF NOT EXISTS term_usages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_id UUID NOT NULL REFERENCES term_definitions(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,

    -- 使用箇所情報
    source_type VARCHAR(50) NOT NULL,
    source_id UUID,
    file_path TEXT,
    line_number INT,
    context TEXT,

    -- 検出情報
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    drift_detected BOOLEAN DEFAULT FALSE,
    drift_type VARCHAR(50),

    -- メタデータ
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    CHECK (source_type IN ('intent', 'code_comment', 'documentation', 'choice_point'))
);

-- 5. term_drift_alerts: ドリフトアラートテーブル
CREATE TABLE IF NOT EXISTS term_drift_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    term_id UUID NOT NULL REFERENCES term_definitions(id),
    usage_id UUID REFERENCES term_usages(id),

    -- アラート情報
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',
    message TEXT NOT NULL,
    detected_context TEXT,
    expected_definition TEXT,

    -- 解決情報
    resolution_status VARCHAR(50) DEFAULT 'pending',
    resolution_action VARCHAR(50),
    resolution_note TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    CHECK (alert_type IN ('definition_drift', 'context_mismatch', 'alias_conflict')),
    CHECK (severity IN ('info', 'warning', 'critical')),
    CHECK (resolution_status IN ('pending', 'resolved', 'dismissed'))
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_term_definitions_term ON term_definitions(term);
CREATE INDEX IF NOT EXISTS idx_term_definitions_user_scope ON term_definitions(user_id, scope);
CREATE INDEX IF NOT EXISTS idx_term_definitions_active ON term_definitions(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_term_aliases_alias ON term_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_term_aliases_term ON term_aliases(term_id);

CREATE INDEX IF NOT EXISTS idx_term_versions_term ON term_versions(term_id);
CREATE INDEX IF NOT EXISTS idx_term_versions_changed_at ON term_versions(changed_at);

CREATE INDEX IF NOT EXISTS idx_term_usages_term ON term_usages(term_id);
CREATE INDEX IF NOT EXISTS idx_term_usages_source ON term_usages(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_term_usages_user ON term_usages(user_id);
CREATE INDEX IF NOT EXISTS idx_term_usages_drift ON term_usages(drift_detected) WHERE drift_detected = TRUE;

CREATE INDEX IF NOT EXISTS idx_term_drift_alerts_status ON term_drift_alerts(resolution_status);
CREATE INDEX IF NOT EXISTS idx_term_drift_alerts_user ON term_drift_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_term_drift_alerts_term ON term_drift_alerts(term_id);

-- フルテキスト検索用インデックス
CREATE INDEX IF NOT EXISTS idx_term_definitions_term_fulltext
    ON term_definitions USING GIN(to_tsvector('simple', term));
CREATE INDEX IF NOT EXISTS idx_term_definitions_definition_fulltext
    ON term_definitions USING GIN(to_tsvector('simple', definition));

-- コメント追加
COMMENT ON TABLE term_definitions IS 'Sprint 12: 用語定義レジストリ';
COMMENT ON TABLE term_aliases IS 'Sprint 12: 用語エイリアス（同義語）';
COMMENT ON TABLE term_versions IS 'Sprint 12: 用語定義の変更履歴';
COMMENT ON TABLE term_usages IS 'Sprint 12: 用語使用箇所の記録';
COMMENT ON TABLE term_drift_alerts IS 'Sprint 12: 用語ドリフト検出アラート';
```

#### 1.4 モデルテスト

**ファイル**: `tests/term_drift/test_models.py`（新規）

```python
"""Tests for Term Drift Detection models"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from bridge.term_drift.models import (
    TermDefinition,
    TermAlias,
    TermVersion,
    TermUsage,
    TermDriftAlert,
)


class TestTermDefinitionModel:
    """Test TermDefinition model"""

    def test_term_definition_with_all_fields(self):
        """Test creating TermDefinition with all fields"""
        term = TermDefinition(
            user_id="hiroki",
            term="ユーザー",
            definition="システムに登録済みのアカウントを持つ人物",
            scope="authentication",
            created_by="hiroki",
        )

        assert term.user_id == "hiroki"
        assert term.term == "ユーザー"
        assert term.scope == "authentication"
        assert term.version == 1
        assert term.is_active is True

    def test_term_definition_default_scope(self):
        """Test default scope is 'global'"""
        term = TermDefinition(
            user_id="hiroki",
            term="テスト",
            definition="テスト定義",
            created_by="hiroki",
        )
        assert term.scope == "global"

    def test_term_definition_scope_lowercase(self):
        """Test scope is converted to lowercase"""
        term = TermDefinition(
            user_id="hiroki",
            term="テスト",
            definition="テスト定義",
            scope="Authentication",
            created_by="hiroki",
        )
        assert term.scope == "authentication"


class TestTermAliasModel:
    """Test TermAlias model"""

    def test_term_alias_with_context(self):
        """Test TermAlias with specific context"""
        alias = TermAlias(
            term_id=uuid4(),
            alias="訪問者",
            context="analytics",
        )

        assert alias.alias == "訪問者"
        assert alias.context == "analytics"
        assert alias.is_active is True

    def test_term_alias_without_context(self):
        """Test TermAlias without context (global)"""
        alias = TermAlias(
            term_id=uuid4(),
            alias="アカウント",
        )

        assert alias.alias == "アカウント"
        assert alias.context is None


class TestTermUsageModel:
    """Test TermUsage model"""

    def test_term_usage_valid_source_type(self):
        """Test valid source_type values"""
        for source_type in ["intent", "code_comment", "documentation", "choice_point"]:
            usage = TermUsage(
                term_id=uuid4(),
                user_id="hiroki",
                source_type=source_type,
            )
            assert usage.source_type == source_type

    def test_term_usage_invalid_source_type(self):
        """Test invalid source_type raises error"""
        with pytest.raises(ValueError):
            TermUsage(
                term_id=uuid4(),
                user_id="hiroki",
                source_type="invalid_type",
            )


class TestTermDriftAlertModel:
    """Test TermDriftAlert model"""

    def test_drift_alert_with_all_fields(self):
        """Test creating TermDriftAlert with all fields"""
        alert = TermDriftAlert(
            user_id="hiroki",
            term_id=uuid4(),
            alert_type="definition_drift",
            severity="warning",
            message="用語「ユーザー」の定義ドリフトを検出",
            detected_context="ゲストを含む全ユーザー",
            expected_definition="登録済みアカウント",
        )

        assert alert.alert_type == "definition_drift"
        assert alert.severity == "warning"
        assert alert.resolution_status == "pending"

    def test_drift_alert_invalid_alert_type(self):
        """Test invalid alert_type raises error"""
        with pytest.raises(ValueError):
            TermDriftAlert(
                user_id="hiroki",
                term_id=uuid4(),
                alert_type="invalid_type",
                message="Test",
            )

    def test_drift_alert_invalid_severity(self):
        """Test invalid severity raises error"""
        with pytest.raises(ValueError):
            TermDriftAlert(
                user_id="hiroki",
                term_id=uuid4(),
                alert_type="definition_drift",
                severity="invalid_severity",
                message="Test",
            )
```

### Day 1 成功基準
- [ ] ディレクトリ構造作成完了
- [ ] 5つのPydanticモデル実装完了
- [ ] PostgreSQLマイグレーション（5テーブル）作成完了
- [ ] 10件以上のモデルテスト作成

### Git Commit
```bash
git add bridge/term_drift/ docker/postgres/009_term_drift_detection.sql tests/term_drift/
git commit -m "feat: Sprint 12 Day 1 - Term Drift Detection data models & PostgreSQL migration"
```

---

## Day 2: TermRegistry実装

### 目標
用語定義の登録・更新・検索を行うTermRegistryサービスを実装。

### ステップ

#### 2.1 TermRegistry実装

**ファイル**: `bridge/term_drift/registry.py`（新規）

```python
"""Term Registry Service"""

import asyncpg
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from .models import TermDefinition, TermAlias, TermVersion

logger = logging.getLogger(__name__)


class TermRegistry:
    """用語レジストリサービス"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def register_term(
        self,
        user_id: str,
        term: str,
        definition: str,
        scope: str = "global",
        aliases: List[str] = None,
        created_by: str = None,
    ) -> TermDefinition:
        """
        新しい用語を登録

        Args:
            user_id: ユーザーID
            term: 用語
            definition: 定義
            scope: スコープ（デフォルト: global）
            aliases: エイリアスリスト
            created_by: 作成者（デフォルト: user_id）

        Returns:
            TermDefinition: 登録された用語定義
        """
        aliases = aliases or []
        created_by = created_by or user_id

        async with self.pool.acquire() as conn:
            # 既存チェック
            existing = await conn.fetchrow("""
                SELECT id FROM term_definitions
                WHERE user_id = $1 AND term = $2 AND scope = $3 AND is_active = TRUE
            """, user_id, term, scope.lower())

            if existing:
                raise ValueError(f"Term '{term}' already exists in scope '{scope}'")

            # 用語登録
            row = await conn.fetchrow("""
                INSERT INTO term_definitions
                    (user_id, term, definition, scope, created_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """, user_id, term, definition, scope.lower(), created_by)

            term_def = TermDefinition(**dict(row))

            # エイリアス登録
            for alias in aliases:
                await conn.execute("""
                    INSERT INTO term_aliases (term_id, alias)
                    VALUES ($1, $2)
                    ON CONFLICT (term_id, alias, context) DO NOTHING
                """, term_def.id, alias)

            logger.info(f"Term registered: {term} (scope: {scope})")

            return term_def

    async def update_definition(
        self,
        term_id: UUID,
        new_definition: str,
        change_reason: str,
        changed_by: str,
    ) -> TermVersion:
        """
        用語定義を更新（バージョン履歴作成）

        Args:
            term_id: 用語ID
            new_definition: 新しい定義
            change_reason: 変更理由
            changed_by: 変更者

        Returns:
            TermVersion: バージョン履歴
        """
        async with self.pool.acquire() as conn:
            # 現在の定義を取得
            current = await conn.fetchrow("""
                SELECT * FROM term_definitions WHERE id = $1 AND is_active = TRUE
            """, term_id)

            if not current:
                raise ValueError(f"Term {term_id} not found")

            old_definition = current["definition"]

            # 意味的差分スコアを計算（簡易版）
            semantic_diff = self._calculate_semantic_diff(old_definition, new_definition)

            # バージョン履歴を作成
            version_row = await conn.fetchrow("""
                INSERT INTO term_versions
                    (term_id, old_definition, new_definition, change_reason, semantic_diff_score, changed_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """, term_id, old_definition, new_definition, change_reason, semantic_diff, changed_by)

            # 定義を更新
            await conn.execute("""
                UPDATE term_definitions
                SET definition = $1, version = version + 1, updated_at = NOW()
                WHERE id = $2
            """, new_definition, term_id)

            logger.info(f"Term definition updated: {term_id} (diff: {semantic_diff:.2f})")

            return TermVersion(**dict(version_row))

    def _calculate_semantic_diff(self, old_def: str, new_def: str) -> float:
        """意味的差分スコアを計算（簡易版: Jaccard距離）"""
        old_tokens = set(old_def.lower().split())
        new_tokens = set(new_def.lower().split())

        if not old_tokens or not new_tokens:
            return 1.0

        intersection = len(old_tokens & new_tokens)
        union = len(old_tokens | new_tokens)

        similarity = intersection / union if union > 0 else 0.0
        return 1.0 - similarity  # 差分スコア（0=同じ、1=完全に異なる）

    async def add_alias(
        self,
        term_id: UUID,
        alias: str,
        context: Optional[str] = None,
    ) -> TermAlias:
        """エイリアスを追加"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO term_aliases (term_id, alias, context)
                VALUES ($1, $2, $3)
                ON CONFLICT (term_id, alias, context) DO UPDATE SET is_active = TRUE
                RETURNING *
            """, term_id, alias, context)

            logger.info(f"Alias added: {alias} -> term {term_id}")

            return TermAlias(**dict(row))

    async def get_term(
        self,
        user_id: str,
        term: str,
        scope: Optional[str] = None,
    ) -> Optional[TermDefinition]:
        """
        用語を取得（エイリアス含む）

        Args:
            user_id: ユーザーID
            term: 用語またはエイリアス
            scope: スコープ（Noneの場合は全スコープから検索）

        Returns:
            TermDefinition: 用語定義（見つからない場合はNone）
        """
        async with self.pool.acquire() as conn:
            # 直接マッチを試行
            if scope:
                row = await conn.fetchrow("""
                    SELECT * FROM term_definitions
                    WHERE user_id = $1 AND term = $2 AND scope = $3 AND is_active = TRUE
                """, user_id, term, scope.lower())
            else:
                row = await conn.fetchrow("""
                    SELECT * FROM term_definitions
                    WHERE user_id = $1 AND term = $2 AND is_active = TRUE
                    ORDER BY CASE WHEN scope = 'global' THEN 0 ELSE 1 END
                    LIMIT 1
                """, user_id, term)

            if row:
                return TermDefinition(**dict(row))

            # エイリアスから検索
            alias_row = await conn.fetchrow("""
                SELECT td.* FROM term_definitions td
                JOIN term_aliases ta ON td.id = ta.term_id
                WHERE td.user_id = $1 AND ta.alias = $2 AND td.is_active = TRUE AND ta.is_active = TRUE
                LIMIT 1
            """, user_id, term)

            if alias_row:
                return TermDefinition(**dict(alias_row))

            return None

    async def search_terms(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
    ) -> List[TermDefinition]:
        """用語を検索"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM term_definitions
                WHERE user_id = $1 AND is_active = TRUE
                  AND (term ILIKE $2 OR definition ILIKE $2)
                ORDER BY
                    CASE WHEN term ILIKE $3 THEN 0 ELSE 1 END,
                    term
                LIMIT $4
            """, user_id, f"%{query}%", f"{query}%", limit)

            return [TermDefinition(**dict(row)) for row in rows]

    async def get_term_history(
        self,
        term_id: UUID,
    ) -> List[TermVersion]:
        """用語の履歴を取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM term_versions
                WHERE term_id = $1
                ORDER BY changed_at DESC
            """, term_id)

            return [TermVersion(**dict(row)) for row in rows]

    async def get_all_terms(
        self,
        user_id: str,
        scope: Optional[str] = None,
    ) -> List[TermDefinition]:
        """全用語を取得"""
        async with self.pool.acquire() as conn:
            if scope:
                rows = await conn.fetch("""
                    SELECT * FROM term_definitions
                    WHERE user_id = $1 AND scope = $2 AND is_active = TRUE
                    ORDER BY term
                """, user_id, scope.lower())
            else:
                rows = await conn.fetch("""
                    SELECT * FROM term_definitions
                    WHERE user_id = $1 AND is_active = TRUE
                    ORDER BY scope, term
                """, user_id)

            return [TermDefinition(**dict(row)) for row in rows]

    async def deactivate_term(
        self,
        term_id: UUID,
    ) -> bool:
        """用語を非アクティブ化"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE term_definitions
                SET is_active = FALSE, updated_at = NOW()
                WHERE id = $1
            """, term_id)

            logger.info(f"Term deactivated: {term_id}")
            return result == "UPDATE 1"
```

### Day 2 成功基準
- [ ] TermRegistry実装完了（8メソッド）
- [ ] 意味的差分スコア計算実装
- [ ] 単体テスト6件以上作成

### Git Commit
```bash
git add bridge/term_drift/registry.py tests/term_drift/test_registry.py
git commit -m "feat: Sprint 12 Day 2 - TermRegistry service implementation"
```

---

## Day 3: TermScanner & DriftDetector実装

### 目標
コンテンツ内の用語をスキャンし、ドリフトを検出する機能を実装。

### ステップ

#### 3.1 TermScanner実装

**ファイル**: `bridge/term_drift/scanner.py`（新規）

```python
"""Term Scanner Service"""

import asyncpg
import re
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from .models import TermDefinition, TermUsage
from .registry import TermRegistry

logger = logging.getLogger(__name__)


class TermScanner:
    """用語スキャナー"""

    def __init__(self, pool: asyncpg.Pool, registry: TermRegistry):
        self.pool = pool
        self.registry = registry

    async def scan_content(
        self,
        user_id: str,
        content: str,
        source_type: str,
        source_id: Optional[UUID] = None,
        file_path: Optional[str] = None,
    ) -> List[TermUsage]:
        """
        コンテンツ内の用語をスキャン

        Args:
            user_id: ユーザーID
            content: スキャン対象のコンテンツ
            source_type: ソースタイプ（intent, code_comment, etc.）
            source_id: ソースID
            file_path: ファイルパス

        Returns:
            List[TermUsage]: 検出された用語使用箇所
        """
        usages = []

        # 登録済み用語を取得
        terms = await self.registry.get_all_terms(user_id)

        for term_def in terms:
            # 用語とエイリアスをパターンとして構築
            patterns = [term_def.term]

            # エイリアスを取得
            async with self.pool.acquire() as conn:
                alias_rows = await conn.fetch("""
                    SELECT alias FROM term_aliases
                    WHERE term_id = $1 AND is_active = TRUE
                """, term_def.id)
                patterns.extend([row["alias"] for row in alias_rows])

            # 各パターンでマッチを検索
            for pattern in patterns:
                matches = self._find_matches(content, pattern)

                for match in matches:
                    context = self._extract_context(content, match["start"], match["end"])

                    usage = TermUsage(
                        term_id=term_def.id,
                        user_id=user_id,
                        source_type=source_type,
                        source_id=source_id,
                        file_path=file_path,
                        context=context,
                        confidence_score=self._calculate_confidence(pattern, context),
                    )
                    usages.append(usage)

                    # DBに記録
                    await self._save_usage(usage)

        logger.info(f"Scanned content: found {len(usages)} term usages")
        return usages

    def _find_matches(self, content: str, pattern: str) -> List[Dict[str, int]]:
        """パターンマッチを検索"""
        matches = []
        # 単語境界を考慮したマッチング
        regex = re.compile(rf'\b{re.escape(pattern)}\b', re.IGNORECASE)

        for match in regex.finditer(content):
            matches.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
            })

        return matches

    def _extract_context(
        self,
        content: str,
        start: int,
        end: int,
        window_size: int = 50,
    ) -> str:
        """用語の周辺コンテキストを抽出"""
        context_start = max(0, start - window_size)
        context_end = min(len(content), end + window_size)

        context = content[context_start:context_end]

        # 前後に省略があることを示す
        if context_start > 0:
            context = "..." + context
        if context_end < len(content):
            context = context + "..."

        return context

    def _calculate_confidence(self, pattern: str, context: str) -> float:
        """マッチ信頼度を計算"""
        # 完全一致なら高信頼度
        if pattern.lower() in context.lower():
            return 1.0

        # 部分一致は中程度
        return 0.7

    async def _save_usage(self, usage: TermUsage):
        """使用箇所をDBに保存"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO term_usages
                    (term_id, user_id, source_type, source_id, file_path, context, confidence_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, usage.term_id, usage.user_id, usage.source_type,
                usage.source_id, usage.file_path, usage.context, usage.confidence_score)
```

#### 3.2 DriftDetector実装

**ファイル**: `bridge/term_drift/detector.py`（新規）

```python
"""Drift Detector Service"""

import asyncpg
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from .models import TermDefinition, TermUsage, TermDriftAlert
from .scanner import TermScanner
from .registry import TermRegistry

logger = logging.getLogger(__name__)


class DriftDetector:
    """ドリフト検出サービス"""

    # ドリフト検出キーワード
    DRIFT_INDICATORS = {
        "expansion": ["含む", "including", "also", "および", "かつ", "加えて"],
        "restriction": ["のみ", "only", "限定", "excluding", "除く", "だけ"],
        "change": ["変更", "更新", "新しい", "different", "変わった", "異なる"],
    }

    CONTRADICTION_INDICATORS = ["ではない", "not", "ない", "except", "但し"]

    def __init__(self, pool: asyncpg.Pool, scanner: TermScanner, registry: TermRegistry):
        self.pool = pool
        self.scanner = scanner
        self.registry = registry

    async def detect_drift(
        self,
        user_id: str,
        content: str,
        source_type: str = "intent",
        source_id: Optional[UUID] = None,
    ) -> List[TermDriftAlert]:
        """
        コンテンツ内のドリフトを検出

        Args:
            user_id: ユーザーID
            content: チェック対象コンテンツ
            source_type: ソースタイプ
            source_id: ソースID

        Returns:
            List[TermDriftAlert]: 検出されたドリフトアラート
        """
        alerts = []

        # コンテンツをスキャン
        usages = await self.scanner.scan_content(
            user_id=user_id,
            content=content,
            source_type=source_type,
            source_id=source_id,
        )

        for usage in usages:
            # 用語定義を取得
            async with self.pool.acquire() as conn:
                term_row = await conn.fetchrow("""
                    SELECT * FROM term_definitions WHERE id = $1
                """, usage.term_id)

            if not term_row:
                continue

            term_def = TermDefinition(**dict(term_row))

            # コンテキスト不一致チェック
            mismatch_alert = await self._check_context_mismatch(
                term_def, usage.context, usage
            )
            if mismatch_alert:
                alerts.append(mismatch_alert)
                await self._save_alert(mismatch_alert)

            # 定義ドリフトチェック
            drift_alert = await self._check_definition_drift(
                term_def, usage.context, usage
            )
            if drift_alert:
                alerts.append(drift_alert)
                await self._save_alert(drift_alert)

        logger.info(f"Drift detection: found {len(alerts)} alerts")
        return alerts

    async def _check_context_mismatch(
        self,
        term: TermDefinition,
        usage_context: str,
        usage: TermUsage,
    ) -> Optional[TermDriftAlert]:
        """コンテキスト不一致をチェック"""
        context_lower = usage_context.lower()
        definition_lower = term.definition.lower()

        # 矛盾インジケーターをチェック
        for indicator in self.CONTRADICTION_INDICATORS:
            if indicator in context_lower:
                # コンテキスト内で用語の否定が使われている
                return TermDriftAlert(
                    user_id=usage.user_id,
                    term_id=term.id,
                    usage_id=usage.id,
                    alert_type="context_mismatch",
                    severity="warning",
                    message=f"用語「{term.term}」が否定的なコンテキストで使用されています",
                    detected_context=usage_context,
                    expected_definition=term.definition,
                )

        return None

    async def _check_definition_drift(
        self,
        term: TermDefinition,
        usage_context: str,
        usage: TermUsage,
    ) -> Optional[TermDriftAlert]:
        """定義ドリフトをチェック"""
        context_lower = usage_context.lower()

        # 拡張インジケーターをチェック
        for indicator in self.DRIFT_INDICATORS["expansion"]:
            if indicator in context_lower:
                # 定義の拡張が示唆されている
                return TermDriftAlert(
                    user_id=usage.user_id,
                    term_id=term.id,
                    usage_id=usage.id,
                    alert_type="definition_drift",
                    severity="info",
                    message=f"用語「{term.term}」の定義が拡張されている可能性があります",
                    detected_context=usage_context,
                    expected_definition=term.definition,
                )

        # 制限インジケーターをチェック
        for indicator in self.DRIFT_INDICATORS["restriction"]:
            if indicator in context_lower:
                return TermDriftAlert(
                    user_id=usage.user_id,
                    term_id=term.id,
                    usage_id=usage.id,
                    alert_type="definition_drift",
                    severity="info",
                    message=f"用語「{term.term}」の定義が制限されている可能性があります",
                    detected_context=usage_context,
                    expected_definition=term.definition,
                )

        return None

    async def _save_alert(self, alert: TermDriftAlert):
        """アラートをDBに保存"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO term_drift_alerts
                    (user_id, term_id, usage_id, alert_type, severity, message,
                     detected_context, expected_definition)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, alert.user_id, alert.term_id, alert.usage_id, alert.alert_type,
                alert.severity, alert.message, alert.detected_context, alert.expected_definition)

    async def resolve_alert(
        self,
        alert_id: UUID,
        resolution_action: str,
        resolution_note: str,
        resolved_by: str,
    ):
        """アラートを解決"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE term_drift_alerts
                SET resolution_status = 'resolved',
                    resolution_action = $1,
                    resolution_note = $2,
                    resolved_at = NOW(),
                    resolved_by = $3
                WHERE id = $4
            """, resolution_action, resolution_note, resolved_by, alert_id)

            logger.info(f"Alert {alert_id} resolved: {resolution_action}")

    async def get_pending_alerts(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[TermDriftAlert]:
        """未解決アラートを取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM term_drift_alerts
                WHERE user_id = $1 AND resolution_status = 'pending'
                ORDER BY
                    CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
                    created_at DESC
                LIMIT $2
            """, user_id, limit)

            return [TermDriftAlert(**dict(row)) for row in rows]
```

### Day 3 成功基準
- [ ] TermScanner実装完了（4メソッド）
- [ ] DriftDetector実装完了（5メソッド）
- [ ] 単体テスト8件以上作成

### Git Commit
```bash
git add bridge/term_drift/scanner.py bridge/term_drift/detector.py tests/term_drift/
git commit -m "feat: Sprint 12 Day 3 - TermScanner & DriftDetector implementation"
```

---

## Day 4: ImpactAnalyzer & API Router実装

### 目標
影響分析機能とAPIエンドポイントを実装。

### ステップ

#### 4.1 ImpactAnalyzer実装

**ファイル**: `bridge/term_drift/impact.py`（新規）

```python
"""Impact Analyzer Service"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TermImpactReport(BaseModel):
    """影響分析レポート"""
    term_id: UUID
    term: str
    definition: str
    usage_count: int
    affected_files: List[Dict[str, Any]]
    affected_intents: int
    affected_choice_points: int
    recommendations: List[str]


class ImpactAnalyzer:
    """影響分析サービス"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def analyze_impact(
        self,
        term_id: UUID,
    ) -> TermImpactReport:
        """用語変更の影響を分析"""
        async with self.pool.acquire() as conn:
            # 用語情報を取得
            term_row = await conn.fetchrow("""
                SELECT * FROM term_definitions WHERE id = $1
            """, term_id)

            if not term_row:
                raise ValueError(f"Term {term_id} not found")

            # 使用箇所を集計
            usage_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_count,
                    COUNT(DISTINCT file_path) FILTER (WHERE file_path IS NOT NULL) as file_count,
                    COUNT(*) FILTER (WHERE source_type = 'intent') as intent_count,
                    COUNT(*) FILTER (WHERE source_type = 'choice_point') as choice_count
                FROM term_usages
                WHERE term_id = $1
            """, term_id)

            # ファイル別集計
            file_usages = await conn.fetch("""
                SELECT file_path, source_type, COUNT(*) as count
                FROM term_usages
                WHERE term_id = $1 AND file_path IS NOT NULL
                GROUP BY file_path, source_type
                ORDER BY count DESC
                LIMIT 20
            """, term_id)

            affected_files = [
                {
                    "path": row["file_path"],
                    "source_type": row["source_type"],
                    "usages": row["count"],
                }
                for row in file_usages
            ]

            # 推奨事項を生成
            recommendations = self._generate_recommendations(
                usage_count=usage_stats["total_count"],
                file_count=usage_stats["file_count"],
                intent_count=usage_stats["intent_count"],
            )

            return TermImpactReport(
                term_id=term_id,
                term=term_row["term"],
                definition=term_row["definition"],
                usage_count=usage_stats["total_count"],
                affected_files=affected_files,
                affected_intents=usage_stats["intent_count"],
                affected_choice_points=usage_stats["choice_count"],
                recommendations=recommendations,
            )

    def _generate_recommendations(
        self,
        usage_count: int,
        file_count: int,
        intent_count: int,
    ) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        if usage_count > 50:
            recommendations.append(
                "この用語は広く使用されています。定義変更は慎重に行ってください。"
            )

        if file_count > 10:
            recommendations.append(
                f"{file_count}個のファイルに影響があります。段階的な更新を推奨します。"
            )

        if intent_count > 10:
            recommendations.append(
                "多くのIntentで使用されています。過去のIntentとの整合性を確認してください。"
            )

        if not recommendations:
            recommendations.append("影響範囲は限定的です。安全に更新できます。")

        return recommendations
```

#### 4.2 API Schemas & Router実装

**ファイル**: `bridge/term_drift/api_schemas.py`（新規）

```python
"""API Schemas for Term Drift Detection"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class RegisterTermRequest(BaseModel):
    """用語登録リクエスト"""
    term: str = Field(min_length=1, max_length=255)
    definition: str = Field(min_length=1)
    scope: str = "global"
    aliases: List[str] = Field(default_factory=list)


class UpdateDefinitionRequest(BaseModel):
    """定義更新リクエスト"""
    new_definition: str = Field(min_length=1)
    change_reason: str = Field(min_length=10)


class AddAliasRequest(BaseModel):
    """エイリアス追加リクエスト"""
    alias: str = Field(min_length=1, max_length=255)
    context: Optional[str] = None


class ScanContentRequest(BaseModel):
    """コンテンツスキャンリクエスト"""
    content: str = Field(min_length=1)
    source_type: str = "intent"
    source_id: Optional[UUID] = None
    file_path: Optional[str] = None


class ResolveAlertRequest(BaseModel):
    """アラート解決リクエスト"""
    resolution_action: str = Field(..., description="'definition_updated', 'term_changed', 'exception_allowed'")
    resolution_note: str = Field(min_length=10)


class TermResponse(BaseModel):
    """用語レスポンス"""
    id: UUID
    term: str
    definition: str
    scope: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DriftAlertResponse(BaseModel):
    """ドリフトアラートレスポンス"""
    id: UUID
    term_id: UUID
    alert_type: str
    severity: str
    message: str
    detected_context: Optional[str]
    expected_definition: Optional[str]
    resolution_status: str
    created_at: datetime
```

**ファイル**: `bridge/term_drift/api_router.py`（新規）

```python
"""API Router for Term Drift Detection"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from .registry import TermRegistry
from .scanner import TermScanner
from .detector import DriftDetector
from .impact import ImpactAnalyzer
from .api_schemas import *

router = APIRouter(prefix="/api/v1/terms", tags=["term-drift"])


# Dependency injection placeholders
def get_registry() -> TermRegistry:
    raise NotImplementedError("Implement dependency injection")

def get_detector() -> DriftDetector:
    raise NotImplementedError("Implement dependency injection")

def get_impact_analyzer() -> ImpactAnalyzer:
    raise NotImplementedError("Implement dependency injection")


@router.post("", response_model=TermResponse)
async def register_term(
    request: RegisterTermRequest,
    user_id: str = Query(...),
    registry: TermRegistry = Depends(get_registry),
):
    """新しい用語を登録"""
    term = await registry.register_term(
        user_id=user_id,
        term=request.term,
        definition=request.definition,
        scope=request.scope,
        aliases=request.aliases,
        created_by=user_id,
    )
    return TermResponse(**term.model_dump())


@router.get("", response_model=List[TermResponse])
async def list_terms(
    user_id: str = Query(...),
    scope: Optional[str] = Query(None),
    registry: TermRegistry = Depends(get_registry),
):
    """用語一覧を取得"""
    terms = await registry.get_all_terms(user_id, scope)
    return [TermResponse(**t.model_dump()) for t in terms]


@router.get("/{term_id}", response_model=TermResponse)
async def get_term(
    term_id: UUID,
    registry: TermRegistry = Depends(get_registry),
):
    """用語詳細を取得"""
    # Implementation
    pass


@router.put("/{term_id}", response_model=dict)
async def update_definition(
    term_id: UUID,
    request: UpdateDefinitionRequest,
    user_id: str = Query(...),
    registry: TermRegistry = Depends(get_registry),
):
    """用語定義を更新"""
    version = await registry.update_definition(
        term_id=term_id,
        new_definition=request.new_definition,
        change_reason=request.change_reason,
        changed_by=user_id,
    )
    return {"status": "updated", "version": version.model_dump()}


@router.post("/{term_id}/aliases", response_model=dict)
async def add_alias(
    term_id: UUID,
    request: AddAliasRequest,
    registry: TermRegistry = Depends(get_registry),
):
    """エイリアスを追加"""
    alias = await registry.add_alias(
        term_id=term_id,
        alias=request.alias,
        context=request.context,
    )
    return {"status": "added", "alias": alias.model_dump()}


@router.get("/{term_id}/impact")
async def get_impact(
    term_id: UUID,
    analyzer: ImpactAnalyzer = Depends(get_impact_analyzer),
):
    """影響分析を取得"""
    report = await analyzer.analyze_impact(term_id)
    return report.model_dump()


@router.post("/scan", response_model=dict)
async def scan_content(
    request: ScanContentRequest,
    user_id: str = Query(...),
    detector: DriftDetector = Depends(get_detector),
):
    """コンテンツをスキャンしてドリフトを検出"""
    alerts = await detector.detect_drift(
        user_id=user_id,
        content=request.content,
        source_type=request.source_type,
        source_id=request.source_id,
    )
    return {
        "alerts": [a.model_dump() for a in alerts],
        "count": len(alerts),
    }


@router.get("/drift-alerts", response_model=List[DriftAlertResponse])
async def list_drift_alerts(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    detector: DriftDetector = Depends(get_detector),
):
    """未解決ドリフトアラート一覧を取得"""
    alerts = await detector.get_pending_alerts(user_id, limit)
    return [DriftAlertResponse(**a.model_dump()) for a in alerts]


@router.put("/drift-alerts/{alert_id}/resolve", response_model=dict)
async def resolve_alert(
    alert_id: UUID,
    request: ResolveAlertRequest,
    user_id: str = Query(...),
    detector: DriftDetector = Depends(get_detector),
):
    """ドリフトアラートを解決"""
    await detector.resolve_alert(
        alert_id=alert_id,
        resolution_action=request.resolution_action,
        resolution_note=request.resolution_note,
        resolved_by=user_id,
    )
    return {"status": "resolved", "alert_id": str(alert_id)}
```

### Day 4 成功基準
- [ ] ImpactAnalyzer実装完了
- [ ] APIスキーマ実装完了
- [ ] API Router実装完了（10エンドポイント）
- [ ] API統合テスト3件以上作成

### Git Commit
```bash
git add bridge/term_drift/impact.py bridge/term_drift/api_schemas.py bridge/term_drift/api_router.py
git commit -m "feat: Sprint 12 Day 4 - ImpactAnalyzer & API Router implementation"
```

---

## Day 5: Intent Bridge統合

### 目標
Intent処理パイプラインにTerm Drift Detectionを統合。

### ステップ

#### 5.1 Intent Bridge統合

**ファイル**: `intent_bridge/intent_bridge/processor.py`（変更）

```python
# 既存コードに追加

# Sprint 12: Term Drift Detection support
try:
    from bridge.term_drift.detector import DriftDetector
    HAS_DRIFT_DETECTOR = True
except ImportError:
    HAS_DRIFT_DETECTOR = False


class IntentProcessor:
    def __init__(
        self,
        ...,
        drift_detector: Optional[DriftDetector] = None,
    ):
        ...
        self.drift_detector = drift_detector

    async def process_intent(self, intent: Intent) -> IntentResult:
        # Sprint 12: Term Drift Detection
        drift_alerts = []
        if self.drift_detector:
            try:
                drift_alerts = await self.drift_detector.detect_drift(
                    user_id=intent.user_id,
                    content=intent.content,
                    source_type="intent",
                    source_id=intent.id,
                )

                if drift_alerts:
                    logger.info(f"Intent {intent.id}: {len(drift_alerts)} term drift alerts")

                    # 重大なドリフトがある場合は確認を求める
                    critical_alerts = [a for a in drift_alerts if a.severity == "critical"]
                    if critical_alerts:
                        return IntentResult(
                            status="paused_for_term_confirmation",
                            intent_id=intent.id,
                            drift_alerts=drift_alerts,
                            message=f"用語の定義ドリフトを検出しました: {len(drift_alerts)}件",
                        )
            except Exception as e:
                logger.error(f"Term drift detection failed: {e}")
                # Continue processing even if drift detection fails

        # Continue with normal processing
        ...
```

### Day 5 成功基準
- [ ] Intent Bridge統合完了
- [ ] ドリフト検出時のIntent pause機能実装
- [ ] 統合テスト3件以上作成

### Git Commit
```bash
git add intent_bridge/intent_bridge/processor.py tests/integration/
git commit -m "feat: Sprint 12 Day 5 - Intent Bridge integration with Term Drift Detection"
```

---

## Day 6: テスト & ドキュメント

### 目標
包括的なテストスイートとAPIドキュメント作成。

### ステップ

- E2Eテスト5件以上作成
- APIドキュメント作成
- パフォーマンステスト実施
- 完了レポート作成

### Day 6 成功基準
- [ ] E2Eテスト5件以上作成
- [ ] APIドキュメント完成
- [ ] パフォーマンステスト実施
- [ ] 完了レポート作成

### Git Commit
```bash
git add tests/ docs/
git commit -m "feat: Sprint 12 Day 6 - E2E tests & API documentation"
```

---

## 完了後チェックリスト

### 機能実装
- [ ] TermRegistryサービス実装
- [ ] TermScannerサービス実装
- [ ] DriftDetectorサービス実装
- [ ] ImpactAnalyzerサービス実装
- [ ] APIエンドポイント10件実装
- [ ] Intent Bridge統合

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
