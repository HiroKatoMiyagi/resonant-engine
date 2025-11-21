# Sprint 11: Contradiction Detection Layer - 作業開始指示書

**作成日**: 2025-11-21
**作成者**: Kana (Claude Sonnet 4.5)
**想定期間**: 5日間
**難易度**: ★★★★☆ (高)

---

## 0. Overview

### 目的
Intent処理パイプラインに**矛盾検出層（Contradiction Detection Layer）**を実装し、過去の決定との整合性をチェックし、方針転換や技術スタック矛盾を検出する。

### 哲学的基盤
```yaml
contradiction_detection_philosophy:
    essence: "矛盾 = 呼吸の乱れ（認知的不協和の検出）"
    purpose:
        - 技術スタックの矛盾検出
        - 方針の急転換検出
        - 重複作業の防止
        - ドグマ（未検証の前提）の排除
    principles:
        - "矛盾は否定ではなく確認"
        - "方針転換は明示的に承認"
        - "同じ議論を二度しない"
        - "過去の知識を尊重する"
```

### Done Definition (Tier 1)
- [x] ContradictionDetectorサービスクラス実装
- [x] 技術スタック矛盾検出（例: PostgreSQL → SQLite）
- [x] 方針急転換検出（短期間での180度変更）
- [x] 重複作業検出（同じIntentの繰り返し）
- [x] 矛盾解決ワークフロー実装
- [x] 10件以上の単体/統合テスト作成

---

## Day 1: データモデル & PostgreSQLマイグレーション

### 目標
矛盾検出に必要なデータベーススキーマとPydanticモデルを実装。

### ステップ

#### 1.1 Pydanticモデル作成

**ファイル**: `bridge/contradiction/models.py`（新規）

```python
"""Contradiction Detection - Data Models"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class Contradiction(BaseModel):
    """矛盾検出レコード"""

    id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: str

    # Intent情報
    new_intent_id: UUID
    new_intent_content: str
    conflicting_intent_id: Optional[UUID] = None
    conflicting_intent_content: Optional[str] = None

    # 矛盾情報
    contradiction_type: str  # 'tech_stack', 'policy_shift', 'duplicate', 'dogma'
    confidence_score: float = Field(ge=0.0, le=1.0)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 詳細情報
    details: Dict[str, Any] = Field(default_factory=dict)

    # 解決情報
    resolution_status: str = "pending"  # 'pending', 'approved', 'rejected', 'modified'
    resolution_action: Optional[str] = None  # 'policy_change', 'mistake', 'coexist'
    resolution_rationale: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("contradiction_type")
    @classmethod
    def validate_contradiction_type(cls, v: str) -> str:
        allowed = ["tech_stack", "policy_shift", "duplicate", "dogma"]
        if v not in allowed:
            raise ValueError(f"contradiction_type must be one of {allowed}")
        return v

    @field_validator("resolution_status")
    @classmethod
    def validate_resolution_status(cls, v: str) -> str:
        allowed = ["pending", "approved", "rejected", "modified"]
        if v not in allowed:
            raise ValueError(f"resolution_status must be one of {allowed}")
        return v


class IntentRelation(BaseModel):
    """Intent関係"""

    id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: str

    # Intent関係
    source_intent_id: UUID
    target_intent_id: UUID
    relation_type: str  # 'contradicts', 'duplicates', 'extends', 'replaces'

    # 関係強度
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("relation_type")
    @classmethod
    def validate_relation_type(cls, v: str) -> str:
        allowed = ["contradicts", "duplicates", "extends", "replaces"]
        if v not in allowed:
            raise ValueError(f"relation_type must be one of {allowed}")
        return v
```

#### 1.2 PostgreSQLマイグレーション

**ファイル**: `docker/postgres/008_contradiction_detection.sql`（新規）

```sql
-- Sprint 11: Contradiction Detection Layer

-- contradictions テーブル
CREATE TABLE IF NOT EXISTS contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 新規Intent
    new_intent_id UUID NOT NULL,
    new_intent_content TEXT NOT NULL,

    -- 矛盾するIntent
    conflicting_intent_id UUID,
    conflicting_intent_content TEXT,

    -- 矛盾情報
    contradiction_type VARCHAR(50) NOT NULL,  -- 'tech_stack', 'policy_shift', 'duplicate', 'dogma'
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 詳細情報
    details JSONB DEFAULT '{}',

    -- 解決情報
    resolution_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'modified'
    resolution_action VARCHAR(50),  -- 'policy_change', 'mistake', 'coexist'
    resolution_rationale TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    CHECK (contradiction_type IN ('tech_stack', 'policy_shift', 'duplicate', 'dogma')),
    CHECK (resolution_status IN ('pending', 'approved', 'rejected', 'modified'))
);

-- intent_relations テーブル
CREATE TABLE IF NOT EXISTS intent_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- Intent関係
    source_intent_id UUID NOT NULL,
    target_intent_id UUID NOT NULL,
    relation_type VARCHAR(50) NOT NULL,  -- 'contradicts', 'duplicates', 'extends', 'replaces'

    -- 関係強度
    similarity_score FLOAT CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    CHECK (relation_type IN ('contradicts', 'duplicates', 'extends', 'replaces')),
    UNIQUE(source_intent_id, target_intent_id, relation_type)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_contradictions_user_id ON contradictions(user_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_new_intent ON contradictions(new_intent_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_conflicting_intent ON contradictions(conflicting_intent_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON contradictions(contradiction_type);
CREATE INDEX IF NOT EXISTS idx_contradictions_status ON contradictions(resolution_status);
CREATE INDEX IF NOT EXISTS idx_contradictions_detected_at ON contradictions(detected_at);

CREATE INDEX IF NOT EXISTS idx_intent_relations_source ON intent_relations(source_intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_relations_target ON intent_relations(target_intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_relations_type ON intent_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_intent_relations_user_id ON intent_relations(user_id);

-- コメント追加
COMMENT ON TABLE contradictions IS 'Sprint 11: Detected contradictions between intents';
COMMENT ON COLUMN contradictions.contradiction_type IS 'Type: tech_stack, policy_shift, duplicate, dogma';
COMMENT ON COLUMN contradictions.confidence_score IS 'Detection confidence (0.0 - 1.0)';
COMMENT ON COLUMN contradictions.resolution_status IS 'Status: pending, approved, rejected, modified';

COMMENT ON TABLE intent_relations IS 'Sprint 11: Relationships between intents';
COMMENT ON COLUMN intent_relations.relation_type IS 'Type: contradicts, duplicates, extends, replaces';
```

**実行**:
```bash
docker exec -i resonant-postgres psql -U resonant_user -d resonant_db < docker/postgres/008_contradiction_detection.sql
```

#### 1.3 モデルテスト

**ファイル**: `tests/contradiction/test_models.py`（新規）

```python
"""Tests for Contradiction models"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from bridge.contradiction.models import Contradiction, IntentRelation


class TestContradictionModel:
    """Test Contradiction model"""

    def test_contradiction_with_all_fields(self):
        """Test creating Contradiction with all fields"""
        contradiction = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Use SQLite",
            conflicting_intent_id=uuid4(),
            conflicting_intent_content="Use PostgreSQL",
            contradiction_type="tech_stack",
            confidence_score=0.9,
            details={"old_tech": "postgresql", "new_tech": "sqlite"},
            resolution_status="pending",
        )

        assert contradiction.user_id == "hiroki"
        assert contradiction.contradiction_type == "tech_stack"
        assert contradiction.confidence_score == 0.9
        assert contradiction.resolution_status == "pending"

    def test_contradiction_type_validation(self):
        """Test contradiction_type validation"""
        with pytest.raises(ValueError):
            Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="invalid_type",  # Invalid
                confidence_score=0.9,
            )

    def test_confidence_score_validation(self):
        """Test confidence_score must be 0.0-1.0"""
        with pytest.raises(ValueError):
            Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="tech_stack",
                confidence_score=1.5,  # Invalid
            )

    def test_resolution_status_validation(self):
        """Test resolution_status validation"""
        with pytest.raises(ValueError):
            Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="tech_stack",
                confidence_score=0.9,
                resolution_status="invalid_status",  # Invalid
            )


class TestIntentRelationModel:
    """Test IntentRelation model"""

    def test_intent_relation_with_all_fields(self):
        """Test creating IntentRelation with all fields"""
        relation = IntentRelation(
            user_id="hiroki",
            source_intent_id=uuid4(),
            target_intent_id=uuid4(),
            relation_type="contradicts",
            similarity_score=0.85,
        )

        assert relation.user_id == "hiroki"
        assert relation.relation_type == "contradicts"
        assert relation.similarity_score == 0.85

    def test_relation_type_validation(self):
        """Test relation_type validation"""
        with pytest.raises(ValueError):
            IntentRelation(
                user_id="hiroki",
                source_intent_id=uuid4(),
                target_intent_id=uuid4(),
                relation_type="invalid_type",  # Invalid
            )
```

### Day 1 成功基準
- [ ] Contradictionモデル実装完了
- [ ] IntentRelationモデル実装完了
- [ ] PostgreSQLマイグレーション作成完了
- [ ] 6件以上のモデルテスト作成

### Git Commit
```bash
git add bridge/contradiction/models.py docker/postgres/008_contradiction_detection.sql tests/contradiction/test_models.py
git commit -m "feat: Sprint 11 Day 1 - Contradiction Detection data models & PostgreSQL migration"
```

---

## Day 2: ContradictionDetector実装（4つの検出メソッド）

### 目標
矛盾検出の核となる`ContradictionDetector`サービスを実装。

### ステップ

#### 2.1 ContradictionDetector実装

**ファイル**: `bridge/contradiction/detector.py`（新規）

```python
"""Contradiction Detector Service"""

import asyncpg
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID

from .models import Contradiction, IntentRelation

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """矛盾検出サービス"""

    # 閾値設定
    TECH_STACK_KEYWORDS = {
        "database": ["postgresql", "mysql", "sqlite", "mongodb", "redis"],
        "framework": ["fastapi", "django", "flask", "express", "react", "vue", "nextjs"],
        "language": ["python", "javascript", "typescript", "go", "rust", "java"],
    }

    POLICY_SHIFT_WINDOW_DAYS = 14  # 2週間以内の方針転換を検出
    DUPLICATE_SIMILARITY_THRESHOLD = 0.85  # 類似度85%以上で重複判定

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def check_new_intent(
        self,
        user_id: str,
        new_intent_id: UUID,
        new_intent_content: str,
    ) -> List[Contradiction]:
        """
        新規Intent矛盾チェック

        Args:
            user_id: ユーザーID
            new_intent_id: 新規IntentID
            new_intent_content: Intent内容

        Returns:
            List[Contradiction]: 検出された矛盾リスト
        """
        contradictions = []

        # 1. 技術スタック矛盾チェック
        tech_contradictions = await self._check_tech_stack_contradiction(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(tech_contradictions)

        # 2. 方針転換チェック
        policy_contradictions = await self._check_policy_shift(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(policy_contradictions)

        # 3. 重複作業チェック
        duplicate_contradictions = await self._check_duplicate_work(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(duplicate_contradictions)

        # 4. ドグマチェック
        dogma_contradictions = await self._check_dogma(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(dogma_contradictions)

        # 矛盾をDBに保存
        for contradiction in contradictions:
            await self._save_contradiction(contradiction)

        logger.info(
            f"Contradiction check for intent {new_intent_id}: "
            f"found {len(contradictions)} contradictions"
        )

        return contradictions

    async def _check_tech_stack_contradiction(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """技術スタック矛盾チェック"""
        contradictions = []

        # 新Intentから技術スタック抽出
        new_tech_stack = self._extract_tech_stack(new_intent_content)

        if not new_tech_stack:
            return contradictions

        # 過去のIntentを取得（技術スタック関連）
        async with self.pool.acquire() as conn:
            # Note: Assume 'intents' table exists from previous sprints
            past_intents = await conn.fetch(
                """
                SELECT id, content, created_at
                FROM intents
                WHERE user_id = $1
                  AND id != $2
                  AND (status IS NULL OR status != 'deprecated')
                ORDER BY created_at DESC
                LIMIT 50
            """,
                user_id,
                new_intent_id,
            )

        # 各過去Intentと比較
        for past_intent in past_intents:
            past_tech_stack = self._extract_tech_stack(past_intent["content"])

            # カテゴリごとに矛盾チェック
            for category, new_tech in new_tech_stack.items():
                if category in past_tech_stack:
                    past_tech = past_tech_stack[category]
                    if new_tech != past_tech:
                        # 矛盾検出！
                        contradictions.append(
                            Contradiction(
                                user_id=user_id,
                                new_intent_id=new_intent_id,
                                new_intent_content=new_intent_content,
                                conflicting_intent_id=past_intent["id"],
                                conflicting_intent_content=past_intent["content"],
                                contradiction_type="tech_stack",
                                confidence_score=0.9,
                                details={
                                    "category": category,
                                    "old_tech": past_tech,
                                    "new_tech": new_tech,
                                    "past_intent_date": past_intent[
                                        "created_at"
                                    ].isoformat(),
                                },
                            )
                        )

        return contradictions

    def _extract_tech_stack(self, content: str) -> Dict[str, str]:
        """技術スタック抽出（単純なキーワードマッチ）"""
        content_lower = content.lower()
        tech_stack = {}

        for category, keywords in self.TECH_STACK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    tech_stack[category] = keyword
                    break

        return tech_stack

    async def _check_policy_shift(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """方針転換チェック（簡易版）"""
        contradictions = []

        # 方針キーワード（対立するペア）
        policy_keywords = [
            ("microservice", "monolith"),
            ("async", "sync"),
            ("nosql", "sql"),
            ("serverless", "traditional"),
        ]

        # 新Intentから方針抽出
        content_lower = new_intent_content.lower()
        new_policy = None
        opposite_policy = None

        for keyword_a, keyword_b in policy_keywords:
            if keyword_a in content_lower:
                new_policy = keyword_a
                opposite_policy = keyword_b
                break
            elif keyword_b in content_lower:
                new_policy = keyword_b
                opposite_policy = keyword_a
                break

        if not new_policy:
            return contradictions

        # 過去2週間のIntentを検索
        async with self.pool.acquire() as conn:
            cutoff_date = datetime.now(timezone.utc) - timedelta(
                days=self.POLICY_SHIFT_WINDOW_DAYS
            )
            past_intents = await conn.fetch(
                """
                SELECT id, content, created_at
                FROM intents
                WHERE user_id = $1
                  AND id != $2
                  AND created_at > $3
                  AND (status IS NULL OR status != 'deprecated')
                ORDER BY created_at DESC
            """,
                user_id,
                new_intent_id,
                cutoff_date,
            )

        # 方針転換チェック
        for past_intent in past_intents:
            past_content_lower = past_intent["content"].lower()
            if opposite_policy in past_content_lower:
                # 方針転換検出！
                days_elapsed = (
                    datetime.now(timezone.utc) - past_intent["created_at"]
                ).days
                contradictions.append(
                    Contradiction(
                        user_id=user_id,
                        new_intent_id=new_intent_id,
                        new_intent_content=new_intent_content,
                        conflicting_intent_id=past_intent["id"],
                        conflicting_intent_content=past_intent["content"],
                        contradiction_type="policy_shift",
                        confidence_score=0.85,
                        details={
                            "old_policy": opposite_policy,
                            "new_policy": new_policy,
                            "days_elapsed": days_elapsed,
                        },
                    )
                )

        return contradictions

    async def _check_duplicate_work(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """重複作業チェック（Jaccard係数による類似度計算）"""
        contradictions = []

        # 過去の完了/進行中Intentを取得
        async with self.pool.acquire() as conn:
            past_intents = await conn.fetch(
                """
                SELECT id, content, created_at, status
                FROM intents
                WHERE user_id = $1
                  AND id != $2
                  AND (status = 'completed' OR status = 'in_progress')
                ORDER BY created_at DESC
                LIMIT 30
            """,
                user_id,
                new_intent_id,
            )

        # 類似度計算（Jaccard係数）
        new_tokens = set(new_intent_content.lower().split())

        for past_intent in past_intents:
            past_tokens = set(past_intent["content"].lower().split())
            similarity = self._jaccard_similarity(new_tokens, past_tokens)

            if similarity >= self.DUPLICATE_SIMILARITY_THRESHOLD:
                # 重複検出！
                contradictions.append(
                    Contradiction(
                        user_id=user_id,
                        new_intent_id=new_intent_id,
                        new_intent_content=new_intent_content,
                        conflicting_intent_id=past_intent["id"],
                        conflicting_intent_content=past_intent["content"],
                        contradiction_type="duplicate",
                        confidence_score=similarity,
                        details={
                            "similarity": similarity,
                            "past_intent_status": past_intent["status"],
                            "past_intent_date": past_intent["created_at"].isoformat(),
                        },
                    )
                )

        return contradictions

    def _jaccard_similarity(self, set_a: set, set_b: set) -> float:
        """Jaccard係数計算"""
        if not set_a or not set_b:
            return 0.0

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    async def _check_dogma(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """ドグマ（未検証前提）チェック（簡易版）"""
        contradictions = []

        # ドグマキーワード
        dogma_keywords = [
            "always",
            "never",
            "every",
            "all users",
            "常に",
            "必ず",
            "絶対",
        ]

        content_lower = new_intent_content.lower()
        detected_dogmas = [kw for kw in dogma_keywords if kw in content_lower]

        if detected_dogmas:
            contradictions.append(
                Contradiction(
                    user_id=user_id,
                    new_intent_id=new_intent_id,
                    new_intent_content=new_intent_content,
                    contradiction_type="dogma",
                    confidence_score=0.7,
                    details={
                        "detected_keywords": detected_dogmas,
                        "warning": "未検証の前提が含まれている可能性があります",
                    },
                )
            )

        return contradictions

    async def _save_contradiction(self, contradiction: Contradiction):
        """矛盾をDBに保存"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO contradictions
                    (user_id, new_intent_id, new_intent_content, conflicting_intent_id,
                     conflicting_intent_content, contradiction_type, confidence_score,
                     details, resolution_status, detected_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11)
            """,
                contradiction.user_id,
                contradiction.new_intent_id,
                contradiction.new_intent_content,
                contradiction.conflicting_intent_id,
                contradiction.conflicting_intent_content,
                contradiction.contradiction_type,
                contradiction.confidence_score,
                json.dumps(contradiction.details),
                contradiction.resolution_status,
                contradiction.detected_at,
                contradiction.created_at,
            )

    async def resolve_contradiction(
        self,
        contradiction_id: UUID,
        resolution_action: str,
        resolution_rationale: str,
        resolved_by: str,
    ):
        """矛盾を解決"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE contradictions
                SET resolution_status = 'approved',
                    resolution_action = $1,
                    resolution_rationale = $2,
                    resolved_at = NOW(),
                    resolved_by = $3
                WHERE id = $4
            """,
                resolution_action,
                resolution_rationale,
                resolved_by,
                contradiction_id,
            )

            logger.info(
                f"Contradiction {contradiction_id} resolved as {resolution_action}"
            )

    async def get_pending_contradictions(self, user_id: str) -> List[Contradiction]:
        """未解決矛盾を取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM contradictions
                WHERE user_id = $1
                  AND resolution_status = 'pending'
                ORDER BY detected_at DESC
                LIMIT 20
            """,
                user_id,
            )

        contradictions = []
        for row in rows:
            row_dict = dict(row)
            if isinstance(row_dict["details"], str):
                row_dict["details"] = json.loads(row_dict["details"])
            contradictions.append(Contradiction(**row_dict))

        return contradictions
```

### Day 2 成功基準
- [ ] ContradictionDetector実装完了（4検出メソッド）
- [ ] 矛盾保存・解決メソッド実装
- [ ] 単体テスト6件以上作成

### Git Commit
```bash
git add bridge/contradiction/detector.py
git commit -m "feat: Sprint 11 Day 2 - ContradictionDetector service with 4 detection methods"
```

---

## Day 3: Confirmation Workflow & API

### 目標
矛盾検出時の確認ワークフローとAPIエンドポイントを実装。

### ステップ

#### 3.1 API Schemas

**ファイル**: `bridge/contradiction/api_schemas.py`（新規）

```python
"""API Schemas for Contradiction Detection"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class ContradictionSchema(BaseModel):
    """Contradiction response schema"""

    id: UUID
    user_id: str
    new_intent_id: UUID
    new_intent_content: str
    conflicting_intent_id: Optional[UUID]
    conflicting_intent_content: Optional[str]
    contradiction_type: str
    confidence_score: float
    detected_at: datetime
    details: Dict[str, Any]
    resolution_status: str
    resolution_action: Optional[str]
    resolution_rationale: Optional[str]
    resolved_at: Optional[datetime]


class CheckIntentRequest(BaseModel):
    """Request to check intent for contradictions"""

    user_id: str
    intent_id: UUID
    intent_content: str


class ResolveContradictionRequest(BaseModel):
    """Request to resolve a contradiction"""

    resolution_action: str = Field(
        ..., description="'policy_change', 'mistake', or 'coexist'"
    )
    resolution_rationale: str = Field(..., min_length=10)
    resolved_by: str


class ContradictionListResponse(BaseModel):
    """Response with list of contradictions"""

    contradictions: List[ContradictionSchema]
    count: int
```

#### 3.2 API Router

**ファイル**: `bridge/contradiction/api_router.py`（新規）

```python
"""API Router for Contradiction Detection"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID

from .detector import ContradictionDetector
from .api_schemas import (
    ContradictionSchema,
    CheckIntentRequest,
    ResolveContradictionRequest,
    ContradictionListResponse,
)

router = APIRouter(prefix="/api/v1/contradiction", tags=["contradiction"])


def get_contradiction_detector() -> ContradictionDetector:
    """Dependency: Get ContradictionDetector instance"""
    # TODO: Implement proper dependency injection with DB pool
    raise NotImplementedError("Implement DB pool injection")


@router.post("/check", response_model=ContradictionListResponse)
async def check_intent_for_contradictions(
    request: CheckIntentRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector),
):
    """
    Check an intent for contradictions with past intents

    This endpoint should be called before processing a new intent
    to detect potential contradictions with existing decisions.
    """
    contradictions = await detector.check_new_intent(
        user_id=request.user_id,
        new_intent_id=request.intent_id,
        new_intent_content=request.intent_content,
    )

    return ContradictionListResponse(
        contradictions=[
            ContradictionSchema(**c.model_dump()) for c in contradictions
        ],
        count=len(contradictions),
    )


@router.get("/pending", response_model=ContradictionListResponse)
async def get_pending_contradictions(
    user_id: str = Query(...),
    detector: ContradictionDetector = Depends(get_contradiction_detector),
):
    """
    Get all pending (unresolved) contradictions for a user
    """
    contradictions = await detector.get_pending_contradictions(user_id)

    return ContradictionListResponse(
        contradictions=[
            ContradictionSchema(**c.model_dump()) for c in contradictions
        ],
        count=len(contradictions),
    )


@router.put("/{contradiction_id}/resolve", response_model=dict)
async def resolve_contradiction(
    contradiction_id: UUID,
    request: ResolveContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector),
):
    """
    Resolve a detected contradiction

    Resolution actions:
    - 'policy_change': Accept the new direction, mark old intent as deprecated
    - 'mistake': Reject new intent as an error
    - 'coexist': Both intents are valid in different contexts
    """
    # Validate resolution_action
    valid_actions = ["policy_change", "mistake", "coexist"]
    if request.resolution_action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"resolution_action must be one of {valid_actions}",
        )

    await detector.resolve_contradiction(
        contradiction_id=contradiction_id,
        resolution_action=request.resolution_action,
        resolution_rationale=request.resolution_rationale,
        resolved_by=request.resolved_by,
    )

    return {
        "status": "resolved",
        "contradiction_id": str(contradiction_id),
        "action": request.resolution_action,
    }
```

### Day 3 成功基準
- [ ] APIスキーマ実装完了
- [ ] 3つのAPIエンドポイント実装完了
- [ ] API統合テスト3件以上作成

### Git Commit
```bash
git add bridge/contradiction/api_schemas.py bridge/contradiction/api_router.py
git commit -m "feat: Sprint 11 Day 3 - Contradiction Detection API endpoints & confirmation workflow"
```

---

## Day 4: Intent Bridge統合 & Re-evaluation Phase連携

### 目標
Intent処理パイプラインに矛盾検出を統合し、Re-evaluation Phaseと連携。

### ステップ

#### 4.1 Intent Bridge統合

**ファイル**: `intent_bridge/intent_bridge/processor.py`（変更）

```python
# 既存コードに追加

# Sprint 11: Contradiction Detection support
try:
    from bridge.contradiction.detector import ContradictionDetector
    HAS_CONTRADICTION_DETECTOR = True
except ImportError:
    HAS_CONTRADICTION_DETECTOR = False


class IntentProcessor:
    def __init__(
        self,
        ...,
        contradiction_detector: Optional[ContradictionDetector] = None,
    ):
        ...
        self.contradiction_detector = contradiction_detector

    async def process_intent(self, intent: Intent) -> IntentResult:
        """
        Process intent with contradiction detection
        """
        # Sprint 11: Pre-processing contradiction check
        contradictions = []
        if self.contradiction_detector:
            try:
                contradictions = await self.contradiction_detector.check_new_intent(
                    user_id=intent.user_id,
                    new_intent_id=intent.id,
                    new_intent_content=intent.content,
                )

                if contradictions:
                    # Log contradictions found
                    logger.warning(
                        f"Intent {intent.id}: {len(contradictions)} contradictions detected"
                    )

                    # Check if any are high-confidence
                    high_confidence = [
                        c for c in contradictions if c.confidence_score > 0.85
                    ]

                    if high_confidence:
                        # Pause intent processing, wait for user confirmation
                        return IntentResult(
                            status="paused_for_confirmation",
                            intent_id=intent.id,
                            contradictions=contradictions,
                            message=f"Found {len(high_confidence)} high-confidence contradictions. Please review.",
                        )
            except Exception as e:
                logger.error(f"Contradiction detection failed: {e}")
                # Continue processing even if contradiction detection fails

        # Continue with normal intent processing
        ...
```

#### 4.2 Context Assembler統合（オプション）

**ファイル**: `context_assembler/service.py`（変更）

Context Assemblerに過去の矛盾解決履歴を含める：

```python
# Sprint 11: Contradiction History support
async def _fetch_contradiction_history(
    self, user_id: str, current_question: str, limit: int = 3
) -> List:
    """過去の矛盾解決履歴を取得"""
    if not self.contradiction_detector:
        return []

    try:
        # Get resolved contradictions related to current question
        async with self.contradiction_detector.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM contradictions
                WHERE user_id = $1
                  AND resolution_status = 'approved'
                  AND (new_intent_content ILIKE $2 OR conflicting_intent_content ILIKE $2)
                ORDER BY resolved_at DESC
                LIMIT $3
            """, user_id, f"%{current_question}%", limit)

        return [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"Failed to fetch contradiction history: {e}")
        return []
```

### Day 4 成功基準
- [ ] Intent Bridge統合完了
- [ ] 矛盾検出時のIntent pause機能実装
- [ ] 統合テスト3件以上作成

### Git Commit
```bash
git add intent_bridge/intent_bridge/processor.py
git commit -m "feat: Sprint 11 Day 4 - Intent Bridge integration with Contradiction Detection"
```

---

## Day 5: テスト & ドキュメント

### 目標
包括的なテストスイートとAPIドキュメント作成。

### ステップ

#### 5.1 E2Eテスト

**ファイル**: `tests/integration/test_contradiction_detection_e2e.py`（新規）

```python
"""E2E tests for Contradiction Detection"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from bridge.contradiction.detector import ContradictionDetector
from bridge.contradiction.models import Contradiction


class TestContradictionDetectionE2E:
    """End-to-end tests for contradiction detection flow"""

    @pytest.fixture
    def mock_pool(self):
        """Mock asyncpg pool"""
        # TODO: Implement mock pool
        pass

    @pytest.mark.asyncio
    async def test_tech_stack_contradiction_full_flow(self, mock_pool):
        """
        Test full flow: detect tech stack contradiction → resolve
        """
        detector = ContradictionDetector(mock_pool)
        user_id = "hiroki"

        # Setup: Create past intent with PostgreSQL
        # ... (mock database setup)

        # Act: Check new intent with SQLite
        new_intent_id = uuid4()
        contradictions = await detector.check_new_intent(
            user_id=user_id,
            new_intent_id=new_intent_id,
            new_intent_content="Use SQLite for database",
        )

        # Assert: Contradiction detected
        assert len(contradictions) == 1
        assert contradictions[0].contradiction_type == "tech_stack"
        assert "postgresql" in contradictions[0].details["old_tech"]
        assert "sqlite" in contradictions[0].details["new_tech"]

        # Resolve
        await detector.resolve_contradiction(
            contradiction_id=contradictions[0].id,
            resolution_action="policy_change",
            resolution_rationale="Switching to SQLite for development simplicity",
            resolved_by=user_id,
        )

        # Verify resolution
        # ... (mock database verification)

    @pytest.mark.asyncio
    async def test_duplicate_work_detection(self, mock_pool):
        """Test detecting duplicate work"""
        # Test implementation
        pass

    @pytest.mark.asyncio
    async def test_policy_shift_detection(self, mock_pool):
        """Test detecting policy shift within 2 weeks"""
        # Test implementation
        pass
```

#### 5.2 APIドキュメント

**ファイル**: `docs/02_components/memory_system/api/sprint11_contradiction_detection_api.md`（新規）

```markdown
# Sprint 11: Contradiction Detection API Documentation

## Overview
矛盾検出APIは、新規Intentと過去のIntentとの整合性をチェックし、
技術スタック矛盾、方針転換、重複作業、ドグマを検出します。

## Endpoints

### 1. POST /api/v1/contradiction/check
Intent矛盾チェック

### 2. GET /api/v1/contradiction/pending
未解決矛盾一覧

### 3. PUT /api/v1/contradiction/{id}/resolve
矛盾解決

... (詳細は実装時に追加)
```

### Day 5 成功基準
- [ ] E2Eテスト5件以上作成
- [ ] APIドキュメント完成
- [ ] パフォーマンステスト実施

### Git Commit
```bash
git add tests/integration/test_contradiction_detection_e2e.py docs/02_components/memory_system/api/sprint11_contradiction_detection_api.md
git commit -m "feat: Sprint 11 Day 5 - E2E tests & API documentation"
```

---

## 完了後チェックリスト

### 機能実装
- [ ] ContradictionDetectorサービス実装
- [ ] 4種類の矛盾検出（tech_stack, policy_shift, duplicate, dogma）
- [ ] 矛盾解決ワークフロー実装
- [ ] Intent Bridge統合
- [ ] APIエンドポイント3件実装

### テスト
- [ ] 単体テスト10件以上
- [ ] 統合テスト5件以上
- [ ] E2Eテスト5件以上
- [ ] パフォーマンステスト実施

### ドキュメント
- [ ] APIドキュメント完成
- [ ] ユーザーガイド作成
- [ ] 完了レポート作成

---

## トラブルシューティング

### False Positive（誤検知）が多い
**対策**:
- confidence_scoreの閾値を上げる
- キーワードマッチング精度を上げる
- ユーザーフィードバックを記録して改善

### パフォーマンスが遅い
**対策**:
- 過去Intent検索のLIMITを調整
- インデックスを追加
- キャッシュを導入

---

## 次のステップ（Sprint 12候補）

- AI判定による高度な矛盾検出
- セマンティック矛盾検出（意味レベル）
- プロジェクト横断矛盾検出
- 矛盾パターン学習機能

---

**作成日**: 2025-11-21
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総行数**: 1,200+
