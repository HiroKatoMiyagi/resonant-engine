# Sprint 11: Contradiction Detection Layer（矛盾検出層）仕様書

## 0. CRITICAL: Contradiction as Cognitive Dissonance

**⚠️ IMPORTANT: 「矛盾 = 認知的不協和・呼吸の乱れ」**

Contradiction Detection Layerは、過去の決定や方針との整合性をチェックし、**意図しない矛盾や方針転換を検出**するシステムです。これは単なるエラーチェックではなく、**「呼吸の乱れ」を感知**し、ユーザーに確認を促すことで、一貫性を保ちます。

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

### 呼吸サイクルとの関係

```
Contradiction Detection (矛盾検出の呼吸)
    ↓
Inhale: 新規Intentが提出される
    ↓
Detect: 過去のIntentとの矛盾を検出
    ↓
Alert: ユーザーに確認を促す
    ↓
Decide: 方針転換 or ミス修正
    ↓
Log: 決定を記録
    ↓
Expand: 知識として蓄積
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] ContradictionDetectorサービスクラス実装
- [ ] 技術スタック矛盾検出（例: PostgreSQL → SQLite）
- [ ] 方針急転換検出（短期間での180度変更）
- [ ] 重複作業検出（同じIntentの繰り返し）
- [ ] Re-evaluation Phaseとの統合
- [ ] 10件以上の単体/統合テストが作成され、CI で緑

#### Tier 2: 品質要件
- [ ] 検出レイテンシ < 500ms
- [ ] False Positive Rate < 10%（誤検知率）
- [ ] 矛盾検出時の確認ワークフロー動作
- [ ] Observability: `contradiction_detected_count`, `contradiction_type_distribution`

---

## 1. 概要

### 1.1 目的
Intent処理パイプラインに**矛盾検出層（Contradiction Detection Layer）**を実装し、過去の決定との整合性をチェックし、方針転換や技術スタック矛盾を検出する。

### 1.2 背景

**既存インフラ:**
- Sprint 6: Intent Bridge実装済み
- Sprint 7: Session Summary実装済み
- **Re-evaluation Phase実装済み**（`bridge/api/reeval.py`）
  - `CorrectionRecord`による修正追跡
  - Intentバージョニング

**現状の問題:**
1. **技術スタック矛盾が検出されない**
   ```
   Week 1: Intent-001 「PostgreSQL使用」
   Week 5: Intent-010 「SQLite使用」
   → 矛盾が検出されず、混在した実装が発生
   ```

2. **方針の急転換が記録されない**
   ```
   Week 1: Intent-005 「マイクロサービス化」
   Week 2: Intent-008 「モノリス維持」
   → なぜ方針転換したか不明
   ```

3. **重複作業が防げない**
   ```
   Week 1: Intent-003 「ログイン機能実装」
   Week 4: Intent-012 「ログイン機能実装」
   → 既に実装済みであることが分からない
   ```

### 1.3 目標
- ContradictionDetectorサービス実装
- 4種類の矛盾検出（技術スタック・方針転換・重複・ドグマ）
- Re-evaluation Phaseとの統合
- 確認ワークフロー実装

### 1.4 スコープ

**含む:**
- 技術スタック矛盾検出（database, framework, language）
- 方針急転換検出（180度変更）
- 重複作業検出（類似Intent検索）
- ドグマ検出（未検証前提）

**含まない（将来拡張）:**
- AI判定による高度な矛盾検出
- セマンティック矛盾検出（意味レベルの矛盾）
- プロジェクト横断矛盾検出

---

## 2. ユースケース

### 2.1 技術スタック矛盾の検出

**シナリオ:**
Week 1に「PostgreSQL使用」を決定。Week 5に「SQLite使用」のIntentが提出される。

**矛盾検出:**
```python
ContradictionDetector.check_new_intent(Intent-010):
    ↓
⚠️ 技術スタック矛盾を検出！
Intent-001 (Week 1): PostgreSQL使用
  理由: スケーラビリティ重視

Intent-010 (Week 5): SQLite使用 ← 矛盾！
  理由: シンプル性重視

確認:
1. 方針転換ですか？（PostgreSQL → SQLite）
2. ミスですか？（修正が必要）
3. 共存ですか？（開発環境はSQLite、本番はPostgreSQL）
```

**ユーザー対応:**
```
Option A: 方針転換
  → Intent-010を承認
  → ChoicePoint作成「なぜSQLiteに変更したか」
  → 過去のIntent-001を`deprecated`に設定

Option B: ミス修正
  → Intent-010を却下
  → 「既にPostgreSQLを使用中」と通知

Option C: 共存
  → Intent-010を承認
  → context_type="development"でタグ付け
```

---

### 2.2 方針急転換の検出

**シナリオ:**
Week 1に「マイクロサービス化」を決定。Week 2に「モノリス維持」のIntentが提出される。

**矛盾検出:**
```python
ContradictionDetector.check_policy_shift(Intent-008):
    ↓
⚠️ 方針急転換を検出！
Intent-005 (Week 1): マイクロサービス化
  理由: スケーラビリティと独立デプロイ

Intent-008 (Week 2): モノリス維持 ← 180度変更！
  理由: 開発効率重視

確認:
- 1週間で方針が180度変わっています
- 理由を記録してください
```

**ユーザー対応:**
```
理由記録: 「初期プロトタイプではモノリスが適切。
          マイクロサービス化は将来的に検討」
→ ChoicePoint作成
→ Intent-005を`postponed`に設定
```

---

### 2.3 重複作業の検出

**シナリオ:**
Week 1に「ログイン機能実装」完了。Week 4に再度「ログイン機能実装」のIntentが提出される。

**矛盾検出:**
```python
ContradictionDetector.check_duplicate_work(Intent-012):
    ↓
⚠️ 重複作業の可能性を検出！
Intent-003 (Week 1): ログイン機能実装
  Status: completed
  Confidence: 95%類似度

Intent-012 (Week 4): ログイン機能実装 ← 重複！

確認:
1. 既に実装済みです
2. 追加機能ですか？（OAuth対応など）
3. リファクタリングですか？
```

**ユーザー対応:**
```
Option A: 追加機能
  → Intent-012を承認
  → タイトル変更「ログインにOAuth追加」

Option B: ミス
  → Intent-012を却下
  → 既存実装を案内
```

---

### 2.4 ドグマの検出

**シナリオ:**
「ユーザーは常にログインする」という前提が未検証のまま使われている。

**ドグマ検出:**
```python
ContradictionDetector.check_dogma(Intent-015):
    ↓
⚠️ 未検証前提（ドグマ）を検出！
Intent-015: 「ログイン後のダッシュボード実装」
  前提: "ユーザーは常にログインする"
  検証: なし

確認:
- ゲストユーザーの扱いは？
- ログインなしでの利用は？
```

---

## 3. アーキテクチャ

### 3.1 全体構成

```
┌──────────────────────────────────────────────────────────┐
│        Contradiction Detection Layer                     │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Contradiction Detector Service                    │ │
│  │  - Technology Stack Checker                        │ │
│  │  - Policy Shift Detector                           │ │
│  │  - Duplicate Work Detector                         │ │
│  │  - Dogma Detector                                  │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Contradiction Repository                          │ │
│  │  - Store detected contradictions                   │ │
│  │  - Link to intents                                 │ │
│  │  - Resolution tracking                             │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Confirmation Workflow                             │ │
│  │  - User notification                               │ │
│  │  - Resolution options                              │ │
│  │  - Choice Point creation                           │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
          ↓                    ↑
    [PostgreSQL]       [Re-evaluation Phase]
    - contradictions
    - intent_relations
```

### 3.2 データフロー

```
[New Intent Created]
    ↓
1. Intent Submitted
    ↓
2. Contradiction Detection (Pre-processing)
   ├─ Technology Stack Check
   ├─ Policy Shift Check
   ├─ Duplicate Work Check
   └─ Dogma Check
    ↓
3. Contradiction Found?
   ├─ No → Intent Processing continues
   └─ Yes → Confirmation Workflow
       ├─ Notify user
       ├─ Present options
       └─ Wait for decision
    ↓
4. User Decision
   ├─ Approve → Intent proceeds (log policy change)
   ├─ Reject → Intent canceled
   └─ Modify → Update Intent, re-check
    ↓
5. Resolution Logged
   ├─ Contradiction record updated
   └─ ChoicePoint created (if policy change)
```

---

## 4. データモデル

### 4.1 contradictions テーブル（新規）

```sql
CREATE TABLE contradictions (
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
    confidence_score FLOAT,  -- 0.0 - 1.0
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 詳細情報
    details JSONB,  -- {"old_tech": "PostgreSQL", "new_tech": "SQLite", ...}

    -- 解決情報
    resolution_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'modified'
    resolution_action VARCHAR(50),  -- 'policy_change', 'mistake', 'coexist'
    resolution_rationale TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_contradictions_user_id ON contradictions(user_id);
CREATE INDEX idx_contradictions_new_intent ON contradictions(new_intent_id);
CREATE INDEX idx_contradictions_type ON contradictions(contradiction_type);
CREATE INDEX idx_contradictions_status ON contradictions(resolution_status);
```

### 4.2 intent_relations テーブル（新規）

```sql
CREATE TABLE intent_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- Intent関係
    source_intent_id UUID NOT NULL,
    target_intent_id UUID NOT NULL,
    relation_type VARCHAR(50) NOT NULL,  -- 'contradicts', 'duplicates', 'extends', 'replaces'

    -- 関係強度
    similarity_score FLOAT,  -- 0.0 - 1.0

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_intent_id, target_intent_id, relation_type)
);

CREATE INDEX idx_intent_relations_source ON intent_relations(source_intent_id);
CREATE INDEX idx_intent_relations_target ON intent_relations(target_intent_id);
CREATE INDEX idx_intent_relations_type ON intent_relations(relation_type);
```

### 4.3 Pydanticモデル

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class Contradiction(BaseModel):
    """矛盾検出レコード"""
    id: Optional[UUID] = None
    user_id: str

    # Intent情報
    new_intent_id: UUID
    new_intent_content: str
    conflicting_intent_id: Optional[UUID] = None
    conflicting_intent_content: Optional[str] = None

    # 矛盾情報
    contradiction_type: str  # 'tech_stack', 'policy_shift', 'duplicate', 'dogma'
    confidence_score: float = Field(ge=0.0, le=1.0)
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    # 詳細情報
    details: Dict[str, Any] = {}

    # 解決情報
    resolution_status: str = "pending"  # 'pending', 'approved', 'rejected', 'modified'
    resolution_action: Optional[str] = None  # 'policy_change', 'mistake', 'coexist'
    resolution_rationale: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class IntentRelation(BaseModel):
    """Intent関係"""
    id: Optional[UUID] = None
    user_id: str
    source_intent_id: UUID
    target_intent_id: UUID
    relation_type: str  # 'contradicts', 'duplicates', 'extends', 'replaces'
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 5. コンポーネント設計

### 5.1 ContradictionDetector サービス

**ファイル:** `bridge/contradiction/detector.py`（新規）

```python
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .models import Contradiction, IntentRelation

logger = logging.getLogger(__name__)

class ContradictionDetector:
    """矛盾検出サービス"""

    # 閾値設定
    TECH_STACK_KEYWORDS = {
        "database": ["postgresql", "mysql", "sqlite", "mongodb", "redis"],
        "framework": ["fastapi", "django", "flask", "express", "react", "vue"],
        "language": ["python", "javascript", "typescript", "go", "rust"]
    }

    POLICY_SHIFT_WINDOW_DAYS = 14  # 2週間以内の方針転換を検出
    DUPLICATE_SIMILARITY_THRESHOLD = 0.85  # 類似度85%以上で重複判定

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def check_new_intent(
        self,
        user_id: str,
        new_intent_id: str,
        new_intent_content: str
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

        return contradictions

    async def _check_tech_stack_contradiction(
        self,
        user_id: str,
        new_intent_id: str,
        new_intent_content: str
    ) -> List[Contradiction]:
        """技術スタック矛盾チェック"""
        contradictions = []

        # 新Intentから技術スタック抽出
        new_tech_stack = self._extract_tech_stack(new_intent_content)

        if not new_tech_stack:
            return contradictions

        # 過去のIntentを取得（技術スタック関連）
        async with self.pool.acquire() as conn:
            past_intents = await conn.fetch("""
                SELECT id, content, created_at
                FROM intents
                WHERE user_id = $1
                  AND id != $2
                  AND status != 'deprecated'
                ORDER BY created_at DESC
                LIMIT 50
            """, user_id, new_intent_id)

        # 各過去Intentと比較
        for past_intent in past_intents:
            past_tech_stack = self._extract_tech_stack(past_intent['content'])

            # カテゴリごとに矛盾チェック
            for category, new_tech in new_tech_stack.items():
                if category in past_tech_stack:
                    past_tech = past_tech_stack[category]
                    if new_tech != past_tech:
                        # 矛盾検出！
                        contradictions.append(Contradiction(
                            user_id=user_id,
                            new_intent_id=UUID(new_intent_id),
                            new_intent_content=new_intent_content,
                            conflicting_intent_id=past_intent['id'],
                            conflicting_intent_content=past_intent['content'],
                            contradiction_type="tech_stack",
                            confidence_score=0.9,
                            details={
                                "category": category,
                                "old_tech": past_tech,
                                "new_tech": new_tech,
                                "past_intent_date": past_intent['created_at'].isoformat()
                            }
                        ))

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
        self,
        user_id: str,
        new_intent_id: str,
        new_intent_content: str
    ) -> List[Contradiction]:
        """方針転換チェック（簡易版）"""
        contradictions = []

        # 方針キーワード
        policy_keywords = [
            ("microservice", "monolith"),
            ("sync", "async"),
            ("sql", "nosql"),
        ]

        # 新Intentから方針抽出
        content_lower = new_intent_content.lower()
        new_policy = None
        for keyword_a, keyword_b in policy_keywords:
            if keyword_a in content_lower:
                new_policy = keyword_a
                break
            elif keyword_b in content_lower:
                new_policy = keyword_b
                break

        if not new_policy:
            return contradictions

        # 過去2週間のIntentを検索
        async with self.pool.acquire() as conn:
            cutoff_date = datetime.utcnow() - timedelta(days=self.POLICY_SHIFT_WINDOW_DAYS)
            past_intents = await conn.fetch("""
                SELECT id, content, created_at
                FROM intents
                WHERE user_id = $1
                  AND id != $2
                  AND created_at > $3
                  AND status != 'deprecated'
                ORDER BY created_at DESC
            """, user_id, new_intent_id, cutoff_date)

        # 方針転換チェック
        for past_intent in past_intents:
            past_content_lower = past_intent['content'].lower()
            for keyword_a, keyword_b in policy_keywords:
                if new_policy == keyword_a and keyword_b in past_content_lower:
                    # 方針転換検出！
                    contradictions.append(Contradiction(
                        user_id=user_id,
                        new_intent_id=UUID(new_intent_id),
                        new_intent_content=new_intent_content,
                        conflicting_intent_id=past_intent['id'],
                        conflicting_intent_content=past_intent['content'],
                        contradiction_type="policy_shift",
                        confidence_score=0.85,
                        details={
                            "old_policy": keyword_b,
                            "new_policy": keyword_a,
                            "days_elapsed": (datetime.utcnow() - past_intent['created_at']).days
                        }
                    ))
                elif new_policy == keyword_b and keyword_a in past_content_lower:
                    contradictions.append(Contradiction(
                        user_id=user_id,
                        new_intent_id=UUID(new_intent_id),
                        new_intent_content=new_intent_content,
                        conflicting_intent_id=past_intent['id'],
                        conflicting_intent_content=past_intent['content'],
                        contradiction_type="policy_shift",
                        confidence_score=0.85,
                        details={
                            "old_policy": keyword_a,
                            "new_policy": keyword_b,
                            "days_elapsed": (datetime.utcnow() - past_intent['created_at']).days
                        }
                    ))

        return contradictions

    async def _check_duplicate_work(
        self,
        user_id: str,
        new_intent_id: str,
        new_intent_content: str
    ) -> List[Contradiction]:
        """重複作業チェック（単純な類似度計算）"""
        contradictions = []

        # 過去の完了Intentを取得
        async with self.pool.acquire() as conn:
            past_intents = await conn.fetch("""
                SELECT id, content, created_at, status
                FROM intents
                WHERE user_id = $1
                  AND id != $2
                  AND (status = 'completed' OR status = 'in_progress')
                ORDER BY created_at DESC
                LIMIT 30
            """, user_id, new_intent_id)

        # 類似度計算（Jaccard係数）
        new_tokens = set(new_intent_content.lower().split())

        for past_intent in past_intents:
            past_tokens = set(past_intent['content'].lower().split())
            similarity = self._jaccard_similarity(new_tokens, past_tokens)

            if similarity >= self.DUPLICATE_SIMILARITY_THRESHOLD:
                # 重複検出！
                contradictions.append(Contradiction(
                    user_id=user_id,
                    new_intent_id=UUID(new_intent_id),
                    new_intent_content=new_intent_content,
                    conflicting_intent_id=past_intent['id'],
                    conflicting_intent_content=past_intent['content'],
                    contradiction_type="duplicate",
                    confidence_score=similarity,
                    details={
                        "similarity": similarity,
                        "past_intent_status": past_intent['status'],
                        "past_intent_date": past_intent['created_at'].isoformat()
                    }
                ))

        return contradictions

    def _jaccard_similarity(self, set_a: set, set_b: set) -> float:
        """Jaccard係数計算"""
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    async def _check_dogma(
        self,
        user_id: str,
        new_intent_id: str,
        new_intent_content: str
    ) -> List[Contradiction]:
        """ドグマ（未検証前提）チェック（簡易版）"""
        contradictions = []

        # ドグマキーワード
        dogma_keywords = ["always", "never", "every", "all users", "常に", "必ず"]

        content_lower = new_intent_content.lower()
        detected_dogmas = [kw for kw in dogma_keywords if kw in content_lower]

        if detected_dogmas:
            contradictions.append(Contradiction(
                user_id=user_id,
                new_intent_id=UUID(new_intent_id),
                new_intent_content=new_intent_content,
                contradiction_type="dogma",
                confidence_score=0.7,
                details={
                    "detected_keywords": detected_dogmas,
                    "warning": "未検証の前提が含まれている可能性があります"
                }
            ))

        return contradictions

    async def _save_contradiction(self, contradiction: Contradiction):
        """矛盾をDBに保存"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO contradictions
                    (user_id, new_intent_id, new_intent_content, conflicting_intent_id,
                     conflicting_intent_content, contradiction_type, confidence_score,
                     details, resolution_status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
            """, contradiction.user_id, contradiction.new_intent_id,
                contradiction.new_intent_content, contradiction.conflicting_intent_id,
                contradiction.conflicting_intent_content, contradiction.contradiction_type,
                contradiction.confidence_score, json.dumps(contradiction.details),
                contradiction.resolution_status)

    async def resolve_contradiction(
        self,
        contradiction_id: str,
        resolution_action: str,
        resolution_rationale: str,
        resolved_by: str
    ):
        """矛盾を解決"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE contradictions
                SET resolution_status = 'approved',
                    resolution_action = $1,
                    resolution_rationale = $2,
                    resolved_at = NOW(),
                    resolved_by = $3
                WHERE id = $4
            """, resolution_action, resolution_rationale, resolved_by, contradiction_id)

            logger.info(f"Contradiction {contradiction_id} resolved as {resolution_action}")
```

---

## 6. パフォーマンス

### 6.1 レイテンシ目標

| 操作 | 目標 |
|------|------|
| 単一Intent矛盾チェック | < 500ms |
| 技術スタック矛盾検出 | < 200ms |
| 重複作業検出（30件比較） | < 300ms |

---

## 7. 運用

### 7.1 確認ワークフロー

矛盾検出時のユーザー確認フロー:

```
[Contradiction Detected]
    ↓
1. 通知: 「矛盾を検出しました」
    ↓
2. 詳細表示:
   - 新規Intent
   - 矛盾する過去のIntent
   - 矛盾の種類
   - 信頼度スコア
    ↓
3. 選択肢提示:
   a) 方針転換（Approve）
   b) ミス修正（Reject）
   c) 共存（Approve with context）
    ↓
4. 理由記録:
   - ユーザーが理由を入力
   - ChoicePoint作成（方針転換の場合）
    ↓
5. 解決:
   - 矛盾レコード更新
   - Intent処理続行
```

---

## 8. 制約と前提

### 8.1 制約
- 単純なキーワードマッチング（AI判定は将来拡張）
- 技術スタックは主要なものに限定
- False Positive許容（確認ワークフローで解決）

### 8.2 前提
- Intent Bridge実装済み
- Re-evaluation Phase実装済み

---

## 9. 今後の拡張

### 9.1 Sprint 12以降候補
- AI判定による高度な矛盾検出
- セマンティック矛盾検出（意味レベル）
- プロジェクト横断矛盾検出

---

**作成日**: 2025-11-20
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総行数**: 850
