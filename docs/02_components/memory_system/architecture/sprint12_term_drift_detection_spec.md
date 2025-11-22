# Sprint 12: Term Drift Detection（用語ドリフト検出）仕様書

## 0. CRITICAL: Term Drift as Cognitive Dissonance

**⚠️ IMPORTANT: 「用語ドリフト = 認知的不協和・呼吸の乱れ」**

Term Drift Detection Layerは、プロジェクト内で使用される用語の定義が時間とともに変化（ドリフト）することを検出し、**意図しない認識の不一致を防ぐ**システムです。これは単なる辞書管理ではなく、**「言葉の意味の揺らぎ」を感知**し、明確な定義の共有を促します。

```yaml
term_drift_philosophy:
    essence: "用語の意味の揺らぎ = 呼吸の乱れ（認知的不協和の検出）"
    problem:
        - Week 1: "ユーザー" = 登録済みアカウント
        - Week 8: "ユーザー" = ゲスト含む全訪問者
        - → 混乱と矛盾の原因
    purpose:
        - 用語定義の変化を追跡
        - 影響範囲を可視化
        - 明示的な定義更新を促進
        - コード・ドキュメント間の一貫性維持
    principles:
        - "用語は共通言語"
        - "定義の変更は明示的に"
        - "影響範囲を把握してから変更"
        - "履歴を残し、学習に活かす"
```

### 呼吸サイクルとの関係

```
Term Drift Detection (用語ドリフト検出の呼吸)
    ↓
Inhale: 新規Intent/コードが提出される
    ↓
Scan: 用語使用をスキャン
    ↓
Compare: 登録済み定義と比較
    ↓
Detect: ドリフト（意味の揺らぎ）を検出
    ↓
Alert: 確認を促す
    ↓
Decide: 定義更新 or 用語変更
    ↓
Log: 履歴を記録
    ↓
Expand: 用語辞書に反映
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] TermRegistryサービスクラス実装
- [ ] 用語定義の登録・更新・履歴管理
- [ ] 用語使用箇所のスキャン機能
- [ ] ドリフト検出アルゴリズム実装
- [ ] Intent Bridge統合（新規Intent時の自動チェック）
- [ ] 10件以上の単体/統合テストが作成され、CI で緑

#### Tier 2: 品質要件
- [ ] 検出レイテンシ < 300ms
- [ ] False Positive Rate < 15%（誤検知率）
- [ ] 用語辞書UI/API動作
- [ ] Observability: `term_drift_detected_count`, `term_definition_updates`

---

## 1. 概要

### 1.1 目的
プロジェクト内の用語定義を一元管理し、**用語の意味が時間とともに変化（ドリフト）**することを検出・追跡・警告するシステムを構築する。

### 1.2 背景

**既存インフラ:**
- Sprint 10: Choice Preservation実装済み
- Sprint 11: Contradiction Detection実装予定
- **Agent Context Versioning実装済み**（`bridge/memory/models.py`）
  - バージョン追跡機構
  - `superseded_by`による継承リンク

**現状の問題:**

1. **用語定義の暗黙的変化**
   ```
   Week 1: Intent-001「ユーザーはログイン後にダッシュボードを見る」
           暗黙の定義: "ユーザー" = 登録済みアカウント

   Week 8: Intent-050「ユーザーの行動をアナリティクスで追跡」
           暗黙の定義: "ユーザー" = ゲスト含む全訪問者

   → 同じ「ユーザー」という言葉が異なる意味で使用され、混乱を招く
   ```

2. **コードとドキュメントの用語不一致**
   ```
   コード: class Customer: ...  # 顧客
   ドキュメント: "ユーザーは..."  # 同じ概念？

   → 用語の不一致がコミュニケーションエラーの原因に
   ```

3. **プロジェクト固有用語の共有不足**
   ```
   開発者A: "エージェント" = AIアシスタント
   開発者B: "エージェント" = 人間のサポート担当

   → 用語辞書がないため、認識のズレが発生
   ```

### 1.3 目標
- TermRegistryサービス実装
- 用語定義のバージョン管理
- ドリフト検出と影響分析
- Intent Bridge統合

### 1.4 スコープ

**含む:**
- 用語定義の登録・更新・削除
- 定義履歴（バージョン管理）
- 使用箇所スキャン（Intent、コメント）
- ドリフト検出（キーワードベース）
- 影響分析（使用箇所リスト）

**含まない（将来拡張）:**
- AI判定による意味的ドリフト検出
- コード内の変数名・クラス名の自動スキャン
- 多言語対応（日本語・英語混在）

---

## 2. ユースケース

### 2.1 用語定義の登録

**シナリオ:**
プロジェクト開始時に主要な用語を定義。

**フロー:**
```python
TermRegistry.register_term(
    term="ユーザー",
    definition="システムに登録済みのアカウントを持つ人物",
    scope="authentication",
    aliases=["アカウント", "メンバー", "User"]
)
```

**結果:**
```yaml
term_registered:
    term: "ユーザー"
    definition: "システムに登録済みのアカウントを持つ人物"
    scope: "authentication"
    aliases: ["アカウント", "メンバー", "User"]
    version: 1
    created_at: "2025-08-01T10:00:00Z"
```

---

### 2.2 用語ドリフトの検出

**シナリオ:**
Week 8に新しいIntentが提出され、用語の使い方が変化。

**検出フロー:**
```python
TermDriftDetector.check_content(
    content="ユーザーの行動をアナリティクスで追跡（ゲスト含む）",
    user_id="hiroki"
)
```

**結果:**
```
⚠️ Term Drift Detected!

用語: "ユーザー"
登録済み定義: "システムに登録済みのアカウントを持つ人物"
検出された使用: "ゲスト含む" ← 定義と矛盾！

コンテキスト:
「ユーザーの行動をアナリティクスで追跡（ゲスト含む）」

確認:
1. 定義を更新しますか？
   新定義: "システムを利用する全ての人物（ゲスト含む）"
2. 別の用語を使用しますか？
   提案: "訪問者" または "Visitor"
3. このコンテキストのみの例外として許可しますか？
```

---

### 2.3 定義の更新と履歴記録

**シナリオ:**
用語定義を更新し、変更理由を記録。

**フロー:**
```python
TermRegistry.update_definition(
    term_id="term-001",
    new_definition="システムを利用する全ての人物（登録済み・ゲスト含む）",
    change_reason="アナリティクス機能追加に伴い、ゲストユーザーも含める必要が発生",
    changed_by="hiroki"
)
```

**結果:**
```yaml
term_updated:
    term: "ユーザー"
    old_definition: "システムに登録済みのアカウントを持つ人物"
    new_definition: "システムを利用する全ての人物（登録済み・ゲスト含む）"
    version: 2
    change_reason: "アナリティクス機能追加に伴い..."
    semantic_diff_score: 0.65  # 意味的変化の度合い
    updated_at: "2025-10-15T14:30:00Z"
```

---

### 2.4 影響分析

**シナリオ:**
用語定義を変更する前に、影響範囲を確認。

**フロー:**
```python
impact = TermRegistry.analyze_impact(term_id="term-001")
```

**結果:**
```yaml
impact_analysis:
    term: "ユーザー"
    usage_count: 47
    affected_files:
        - path: "auth/login_handler.py"
          usages: 12
          context_type: "code_comment"
        - path: "docs/user_guide.md"
          usages: 23
          context_type: "documentation"
        - path: "intents/intent_001.json"
          usages: 5
          context_type: "intent"
    recommendation:
        - "認証モジュールでの使用は「登録ユーザー」に変更推奨"
        - "アナリティクスモジュールは新定義で問題なし"
```

---

### 2.5 用語の別名（エイリアス）管理

**シナリオ:**
同じ概念を指す異なる用語を紐付け。

**フロー:**
```python
TermRegistry.add_alias(
    term_id="term-001",
    alias="訪問者",
    context="analytics"  # このコンテキストでのみ有効
)
```

**結果:**
```yaml
alias_added:
    term: "ユーザー"
    alias: "訪問者"
    context: "analytics"
    note: "アナリティクスコンテキストでは「訪問者」を「ユーザー」の別名として認識"
```

---

## 3. アーキテクチャ

### 3.1 全体構成

```
┌──────────────────────────────────────────────────────────┐
│              Term Drift Detection Layer                  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Term Registry Service                             │ │
│  │  - 用語定義の登録・管理                            │ │
│  │  - バージョン履歴                                  │ │
│  │  - スコープ管理（global/module/file）              │ │
│  │  - エイリアス管理                                  │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Term Scanner                                      │ │
│  │  - コンテンツ内の用語検出                          │ │
│  │  - コンテキスト抽出                                │ │
│  │  - 使用パターン分析                                │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Drift Detector                                    │ │
│  │  - 定義との不一致検出                              │ │
│  │  - 意味的変化スコア計算                            │ │
│  │  - ドリフトアラート生成                            │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Impact Analyzer                                   │ │
│  │  - 影響ファイル特定                                │ │
│  │  - 使用箇所マッピング                              │ │
│  │  - 更新推奨生成                                    │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
          ↓                    ↑
    [PostgreSQL]        [Intent Bridge]
    - term_definitions
    - term_versions
    - term_usages
    - term_aliases
```

### 3.2 データフロー

```
[New Intent/Content Created]
    ↓
1. Content Submitted
    ↓
2. Term Scanning
   ├─ 登録済み用語の検出
   ├─ エイリアスの検出
   └─ コンテキスト抽出
    ↓
3. Drift Detection
   ├─ 定義との整合性チェック
   ├─ コンテキスト依存チェック
   └─ 意味的変化スコア計算
    ↓
4. Drift Found?
   ├─ No → Content Processing continues
   └─ Yes → Alert Workflow
       ├─ Notify user
       ├─ Present options
       └─ Wait for decision
    ↓
5. User Decision
   ├─ Update Definition → Term version created
   ├─ Use Different Term → Content updated
   └─ Allow Exception → Exception logged
    ↓
6. Resolution Logged
   ├─ Usage recorded
   └─ Impact analysis updated
```

---

## 4. データモデル

### 4.1 term_definitions テーブル（新規）

```sql
CREATE TABLE term_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 用語情報
    term VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    scope VARCHAR(100) DEFAULT 'global',  -- 'global', 'module_name', 'file_path'

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
```

### 4.2 term_aliases テーブル（新規）

```sql
CREATE TABLE term_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_id UUID NOT NULL REFERENCES term_definitions(id) ON DELETE CASCADE,

    -- エイリアス情報
    alias VARCHAR(255) NOT NULL,
    context VARCHAR(100),  -- NULL = 全コンテキスト、または特定コンテキスト
    is_active BOOLEAN DEFAULT TRUE,

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    UNIQUE(term_id, alias, context)
);
```

### 4.3 term_versions テーブル（新規）

```sql
CREATE TABLE term_versions (
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
```

### 4.4 term_usages テーブル（新規）

```sql
CREATE TABLE term_usages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_id UUID NOT NULL REFERENCES term_definitions(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,

    -- 使用箇所情報
    source_type VARCHAR(50) NOT NULL,  -- 'intent', 'code_comment', 'documentation', 'choice_point'
    source_id UUID,  -- Intent ID, Choice Point ID, etc.
    file_path TEXT,
    line_number INT,
    context TEXT,  -- 周辺テキスト

    -- 検出情報
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    drift_detected BOOLEAN DEFAULT FALSE,
    drift_type VARCHAR(50),  -- 'context_mismatch', 'definition_conflict', 'alias_confusion'

    -- メタデータ
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4.5 term_drift_alerts テーブル（新規）

```sql
CREATE TABLE term_drift_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    term_id UUID NOT NULL REFERENCES term_definitions(id),
    usage_id UUID REFERENCES term_usages(id),

    -- アラート情報
    alert_type VARCHAR(50) NOT NULL,  -- 'definition_drift', 'context_mismatch', 'alias_conflict'
    severity VARCHAR(20) DEFAULT 'warning',  -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    detected_context TEXT,
    expected_definition TEXT,

    -- 解決情報
    resolution_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'resolved', 'dismissed'
    resolution_action VARCHAR(50),  -- 'definition_updated', 'term_changed', 'exception_allowed'
    resolution_note TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4.6 Pydanticモデル

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


class TermDefinition(BaseModel):
    """用語定義"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    term: str = Field(min_length=1, max_length=255)
    definition: str = Field(min_length=1)
    scope: str = "global"
    version: int = 1
    is_active: bool = True
    superseded_by: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TermAlias(BaseModel):
    """用語エイリアス"""
    id: UUID = Field(default_factory=uuid4)
    term_id: UUID
    alias: str = Field(min_length=1, max_length=255)
    context: Optional[str] = None
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
    source_type: str  # 'intent', 'code_comment', 'documentation', 'choice_point'
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
    alert_type: str  # 'definition_drift', 'context_mismatch', 'alias_conflict'
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
```

---

## 5. コンポーネント設計

### 5.1 TermRegistry サービス

**ファイル:** `bridge/term_drift/registry.py`（新規）

```python
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
        aliases: List[str] = [],
        created_by: str = None,
    ) -> TermDefinition:
        """新しい用語を登録"""

    async def update_definition(
        self,
        term_id: UUID,
        new_definition: str,
        change_reason: str,
        changed_by: str,
    ) -> TermVersion:
        """用語定義を更新（バージョン履歴作成）"""

    async def add_alias(
        self,
        term_id: UUID,
        alias: str,
        context: Optional[str] = None,
    ) -> TermAlias:
        """エイリアスを追加"""

    async def get_term(
        self,
        user_id: str,
        term: str,
        scope: Optional[str] = None,
    ) -> Optional[TermDefinition]:
        """用語を取得（エイリアス含む）"""

    async def search_terms(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
    ) -> List[TermDefinition]:
        """用語を検索"""

    async def get_term_history(
        self,
        term_id: UUID,
    ) -> List[TermVersion]:
        """用語の履歴を取得"""
```

### 5.2 TermScanner サービス

**ファイル:** `bridge/term_drift/scanner.py`（新規）

```python
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
    ) -> List[TermUsage]:
        """コンテンツ内の用語をスキャン"""

    async def extract_context(
        self,
        content: str,
        term: str,
        window_size: int = 50,
    ) -> str:
        """用語の周辺コンテキストを抽出"""

    async def calculate_confidence(
        self,
        term: str,
        context: str,
        definition: str,
    ) -> float:
        """マッチ信頼度を計算"""
```

### 5.3 DriftDetector サービス

**ファイル:** `bridge/term_drift/detector.py`（新規）

```python
class DriftDetector:
    """ドリフト検出サービス"""

    # ドリフト検出キーワード
    DRIFT_INDICATORS = {
        "expansion": ["含む", "including", "also", "および"],
        "restriction": ["のみ", "only", "限定", "excluding"],
        "change": ["変更", "更新", "新しい", "different"],
    }

    def __init__(self, pool: asyncpg.Pool, scanner: TermScanner):
        self.pool = pool
        self.scanner = scanner

    async def detect_drift(
        self,
        user_id: str,
        content: str,
        source_type: str = "intent",
    ) -> List[TermDriftAlert]:
        """コンテンツ内のドリフトを検出"""

    async def calculate_semantic_diff(
        self,
        old_definition: str,
        new_context: str,
    ) -> float:
        """意味的差分スコアを計算（0.0-1.0）"""

    async def check_context_mismatch(
        self,
        term: TermDefinition,
        usage_context: str,
    ) -> Optional[TermDriftAlert]:
        """コンテキスト不一致をチェック"""
```

### 5.4 ImpactAnalyzer サービス

**ファイル:** `bridge/term_drift/impact.py`（新規）

```python
class ImpactAnalyzer:
    """影響分析サービス"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def analyze_impact(
        self,
        term_id: UUID,
    ) -> TermImpactReport:
        """用語変更の影響を分析"""

    async def get_usage_summary(
        self,
        term_id: UUID,
    ) -> Dict[str, Any]:
        """使用状況サマリーを取得"""

    async def suggest_updates(
        self,
        term_id: UUID,
        new_definition: str,
    ) -> List[UpdateSuggestion]:
        """更新提案を生成"""
```

---

## 6. API設計

### 6.1 エンドポイント一覧

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/terms` | 用語登録 |
| GET | `/api/v1/terms` | 用語一覧取得 |
| GET | `/api/v1/terms/{term_id}` | 用語詳細取得 |
| PUT | `/api/v1/terms/{term_id}` | 用語定義更新 |
| DELETE | `/api/v1/terms/{term_id}` | 用語削除（非アクティブ化） |
| POST | `/api/v1/terms/{term_id}/aliases` | エイリアス追加 |
| GET | `/api/v1/terms/{term_id}/history` | 履歴取得 |
| GET | `/api/v1/terms/{term_id}/impact` | 影響分析 |
| POST | `/api/v1/terms/scan` | コンテンツスキャン |
| GET | `/api/v1/terms/drift-alerts` | ドリフトアラート一覧 |
| PUT | `/api/v1/terms/drift-alerts/{alert_id}/resolve` | アラート解決 |

---

## 7. パフォーマンス

### 7.1 レイテンシ目標

| 操作 | 目標 |
|------|------|
| 用語登録 | < 100ms |
| 用語検索 | < 50ms |
| コンテンツスキャン | < 300ms |
| ドリフト検出 | < 200ms |
| 影響分析 | < 500ms |

### 7.2 インデックス設計

```sql
-- 高速検索用インデックス
CREATE INDEX idx_term_definitions_term ON term_definitions(term);
CREATE INDEX idx_term_definitions_user_scope ON term_definitions(user_id, scope);
CREATE INDEX idx_term_definitions_active ON term_definitions(is_active) WHERE is_active = TRUE;

-- エイリアス検索
CREATE INDEX idx_term_aliases_alias ON term_aliases(alias);
CREATE INDEX idx_term_aliases_term ON term_aliases(term_id);

-- 使用箇所検索
CREATE INDEX idx_term_usages_term ON term_usages(term_id);
CREATE INDEX idx_term_usages_source ON term_usages(source_type, source_id);

-- アラート検索
CREATE INDEX idx_term_drift_alerts_status ON term_drift_alerts(resolution_status);
CREATE INDEX idx_term_drift_alerts_user ON term_drift_alerts(user_id);
```

---

## 8. Intent Bridge統合

### 8.1 統合ポイント

```python
class IntentProcessor:
    def __init__(
        self,
        ...,
        drift_detector: Optional[DriftDetector] = None,
    ):
        self.drift_detector = drift_detector

    async def process_intent(self, intent: Intent) -> IntentResult:
        # Sprint 12: Term Drift Detection
        if self.drift_detector:
            drift_alerts = await self.drift_detector.detect_drift(
                user_id=intent.user_id,
                content=intent.content,
                source_type="intent",
            )

            if drift_alerts:
                # 重大なドリフトがある場合は確認を求める
                critical_alerts = [a for a in drift_alerts if a.severity == "critical"]
                if critical_alerts:
                    return IntentResult(
                        status="paused_for_term_confirmation",
                        intent_id=intent.id,
                        drift_alerts=drift_alerts,
                        message=f"用語の定義ドリフトを検出しました: {len(drift_alerts)}件",
                    )

        # Continue with normal processing
        ...
```

---

## 9. 制約と前提

### 9.1 制約
- キーワードベースのドリフト検出（AI判定は将来拡張）
- 日本語・英語の主要用語のみ対応
- コード内の変数名は対象外（コメントのみ）

### 9.2 前提
- Intent Bridge実装済み
- Contradiction Detection (Sprint 11) との連携可能

---

## 10. 今後の拡張

### 10.1 Sprint 14以降候補
- AI判定による意味的ドリフト検出
- コード内変数名・クラス名のスキャン
- 多言語対応（同義語辞書の拡充）
- 用語間の関係性グラフ

---

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総行数**: 700+
