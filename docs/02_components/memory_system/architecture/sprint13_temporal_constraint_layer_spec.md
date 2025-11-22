# Sprint 13: Temporal Constraint Layer（時間軸制約層）仕様書

## 0. CRITICAL: Temporal Constraint as Stability Guardian

**⚠️ IMPORTANT: 「時間軸制約 = 検証済みコードの保護」**

Temporal Constraint Layerは、テスト・検証に費やされた工数（時間）に基づいてコードの変更を制御し、**意図しない破壊を防ぐ**システムです。これは単なるファイルロックではなく、**「検証の価値を時間軸で保護」**し、安定性と開発速度のバランスを取ります。

```yaml
temporal_constraint_philosophy:
    essence: "検証工数 = 価値の蓄積、その価値を保護する"
    problem:
        - 50時間テストしたファイルを軽率に変更
        - 変更後、全テストが壊れる
        - 再検証に50時間必要
        - → 開発サイクルの破壊
    purpose:
        - 検証済みファイルの変更前警告
        - テスト工数の可視化
        - 変更影響の事前評価
        - 段階的な変更承認
    principles:
        - "検証時間は資産である"
        - "変更は計画的に"
        - "影響を理解してから編集"
        - "呼吸を乱さない変更"
```

### 呼吸サイクルとの関係

```
Temporal Constraint (時間軸制約の呼吸)
    ↓
Inhale: ファイル変更のリクエスト
    ↓
Check: 検証ステータスを確認
    ↓
Evaluate: テスト工数・影響範囲を評価
    ↓
Decide: 変更を許可/警告/ブロック
    ↓
Log: 変更履歴を記録
    ↓
Re-evaluate: 検証ステータスを更新
    ↓
Expand: 学習に活かす
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] FileVerificationサービスクラス実装
- [ ] ファイル検証ステータスの登録・更新・履歴管理
- [ ] テスト工数トラッキング機能
- [ ] 変更前警告システム実装
- [ ] Re-evaluation Phase統合
- [ ] 10件以上の単体/統合テストが作成され、CI で緑

#### Tier 2: 品質要件
- [ ] 警告レイテンシ < 200ms
- [ ] False Positive Rate < 10%（不要な警告率）
- [ ] Git Hook統合
- [ ] Observability: `verification_bypass_count`, `protected_file_changes`

---

## 1. 概要

### 1.1 目的
ファイルの検証ステータスとテスト工数を追跡し、検証済みコードの変更に対して適切な警告・承認フローを提供するシステムを構築する。

### 1.2 背景

**既存インフラ:**
- Sprint 10: Choice Preservation System実装済み
- Sprint 11: Contradiction Detection Layer実装済み
- Sprint 12: Term Drift Detection実装済み
- **Hypothesis Trace System実装済み**（`daemon/hypothesis_trace.py`）
- **Re-evaluation Phase実装済み**（`bridge/api/reeval.py`）

**現状の問題:**

1. **検証工数の可視化不足**
   ```
   ファイルA: 50時間のテスト・検証完了
   開発者: 「ちょっとリファクタリング」
   結果: 全テスト失敗、50時間が無駄に

   → 検証に費やした時間が見えないため軽率な変更が発生
   ```

2. **変更影響の事前評価なし**
   ```
   コアモジュール変更 → 依存モジュール20個が壊れる
   気づいたのはCI後

   → 事前に影響範囲を把握する仕組みがない
   ```

3. **検証ステータスの形骸化**
   ```
   "検証済み"マークされたファイル
   実際は6ヶ月前のテスト
   コードは既に大きく変更済み

   → 検証の有効期限管理がない
   ```

### 1.3 目標
- FileVerificationサービス実装
- テスト工数トラッキング
- 変更前警告システム
- 検証ステータス管理
- Re-evaluation Phase統合

### 1.4 スコープ

**含む:**
- ファイル検証ステータスの登録・更新
- テスト工数（時間、テストケース数）の記録
- 変更前警告・承認フロー
- 検証有効期限管理
- 依存関係に基づく影響分析

**含まない（将来拡張）:**
- IDE統合（VSCode Extension等）
- CI/CDパイプライン統合
- 自動テスト実行連携

---

## 2. ユースケース

### 2.1 ファイル検証の登録

**シナリオ:**
テスト完了後、ファイルの検証ステータスを登録。

**フロー:**
```python
TemporalConstraintService.register_verification(
    file_path="bridge/memory/service.py",
    verification_status="verified",
    test_hours=12.5,
    test_cases_count=45,
    coverage_percent=92.5,
    verified_by="hiroki"
)
```

**結果:**
```yaml
verification_registered:
    file_path: "bridge/memory/service.py"
    status: "verified"
    test_hours: 12.5
    test_cases_count: 45
    coverage_percent: 92.5
    verified_at: "2025-11-22T10:00:00Z"
    expires_at: "2025-02-22T10:00:00Z"  # 3ヶ月後
```

---

### 2.2 変更前警告

**シナリオ:**
検証済みファイルを変更しようとした時の警告。

**フロー:**
```python
warning = TemporalConstraintService.check_file_modification(
    file_path="bridge/memory/service.py",
    user_id="hiroki"
)
```

**結果:**
```
⚠️ Protected File Warning!

ファイル: bridge/memory/service.py
検証ステータス: verified
テスト工数: 12.5時間
テストケース: 45件
カバレッジ: 92.5%
検証日: 2025-11-22

このファイルを変更すると、12.5時間のテスト工数が影響を受ける可能性があります。

変更の影響:
- 依存ファイル: 8件
- 影響を受けるテスト: 45件
- 推定再検証時間: 8-10時間

選択肢:
1. 変更をキャンセル
2. 変更を続行（再検証必要として記録）
3. 例外として変更（理由入力必須）
```

---

### 2.3 検証ステータスの失効

**シナリオ:**
ファイル変更により検証ステータスが失効。

**フロー:**
```python
TemporalConstraintService.invalidate_verification(
    file_path="bridge/memory/service.py",
    reason="Code modification by hiroki",
    modified_by="hiroki"
)
```

**結果:**
```yaml
verification_invalidated:
    file_path: "bridge/memory/service.py"
    old_status: "verified"
    new_status: "needs_reverification"
    invalidated_at: "2025-11-23T14:00:00Z"
    reason: "Code modification by hiroki"
    previous_test_hours: 12.5
```

---

### 2.4 依存関係に基づく影響分析

**シナリオ:**
コアファイル変更時の影響範囲を事前評価。

**フロー:**
```python
impact = TemporalConstraintService.analyze_change_impact(
    file_path="bridge/memory/models.py"
)
```

**結果:**
```yaml
impact_analysis:
    file: "bridge/memory/models.py"
    verification_status: "verified"
    test_hours: 25.0
    direct_dependents:
        - path: "bridge/memory/service.py"
          test_hours: 12.5
          status: "verified"
        - path: "bridge/memory/api_router.py"
          test_hours: 8.0
          status: "verified"
    indirect_dependents:
        - path: "tests/memory/test_models.py"
          test_hours: 5.0
          status: "verified"
    total_affected_test_hours: 50.5
    recommendation: "高影響度の変更です。段階的な変更と再検証を推奨します。"
```

---

### 2.5 検証有効期限の管理

**シナリオ:**
検証の有効期限が切れそうなファイルを検出。

**フロー:**
```python
expiring = TemporalConstraintService.get_expiring_verifications(
    user_id="hiroki",
    days_until_expiry=14
)
```

**結果:**
```yaml
expiring_verifications:
    - file_path: "bridge/memory/service.py"
      status: "verified"
      expires_at: "2025-12-05T10:00:00Z"
      days_remaining: 13
      test_hours: 12.5
      recommendation: "再検証を推奨"
```

---

## 3. アーキテクチャ

### 3.1 全体構成

```
┌──────────────────────────────────────────────────────────┐
│              Temporal Constraint Layer                    │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  File Verification Registry                         │ │
│  │  - ファイル検証ステータス管理                       │ │
│  │  - テスト工数トラッキング                           │ │
│  │  - 有効期限管理                                     │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Change Guard                                       │ │
│  │  - 変更前チェック                                   │ │
│  │  - 警告生成                                         │ │
│  │  - 承認フロー管理                                   │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Dependency Analyzer                                │ │
│  │  - ファイル依存関係の追跡                           │ │
│  │  - 影響範囲の計算                                   │ │
│  │  - 推奨アクションの生成                             │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Verification History                               │ │
│  │  - 検証履歴の記録                                   │ │
│  │  - 失効履歴の追跡                                   │ │
│  │  - 統計・分析                                       │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
          ↓                    ↑
    [PostgreSQL]        [Re-evaluation Phase]
    - file_verifications
    - verification_history
    - file_dependencies
    - change_approvals
```

### 3.2 データフロー

```
[File Modification Request]
    ↓
1. Change Request Received
    ↓
2. Verification Check
   ├─ 未検証ファイル → 変更許可（ログのみ）
   └─ 検証済みファイル → 警告フロー
    ↓
3. Impact Analysis
   ├─ 依存ファイルの検出
   ├─ 影響テスト工数の計算
   └─ 推奨アクションの生成
    ↓
4. User Decision
   ├─ キャンセル → 変更中止
   ├─ 続行 → 検証ステータス失効
   └─ 例外許可 → 理由記録して続行
    ↓
5. Change Execution
   ├─ 検証ステータス更新
   ├─ 依存ファイル通知
   └─ 履歴記録
    ↓
6. Re-evaluation Trigger
   ├─ 再検証タスク生成
   └─ テスト再実行スケジュール
```

---

## 4. データモデル

### 4.1 file_verifications テーブル（新規）

```sql
CREATE TABLE file_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- ファイル情報
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),  -- SHA256 of file content

    -- 検証ステータス
    verification_status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'in_progress', 'verified', 'needs_reverification', 'failed'

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
```

### 4.2 verification_history テーブル（新規）

```sql
CREATE TABLE verification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES file_verifications(id) ON DELETE CASCADE,

    -- 変更情報
    action VARCHAR(50) NOT NULL,  -- 'created', 'verified', 'invalidated', 'expired', 'reverified'
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    reason TEXT,

    -- テスト情報スナップショット
    test_hours_at_change FLOAT,
    test_cases_at_change INT,

    -- メタデータ
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4.3 file_dependencies テーブル（新規）

```sql
CREATE TABLE file_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,

    -- 依存関係
    source_file TEXT NOT NULL,  -- 依存元ファイル
    dependent_file TEXT NOT NULL,  -- 依存先ファイル
    dependency_type VARCHAR(50) DEFAULT 'import',
    -- 'import', 'test', 'config', 'api'

    -- メタデータ
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- 制約
    UNIQUE(user_id, source_file, dependent_file)
);
```

### 4.4 change_approvals テーブル（新規）

```sql
CREATE TABLE change_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID NOT NULL REFERENCES file_verifications(id),
    user_id VARCHAR(255) NOT NULL,

    -- 承認情報
    approval_status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'approved', 'rejected', 'bypassed'
    approval_type VARCHAR(50) NOT NULL,
    -- 'normal', 'emergency', 'exception'

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
```

### 4.5 Pydanticモデル

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timezone
from uuid import UUID, uuid4


class FileVerification(BaseModel):
    """ファイル検証ステータス"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    file_path: str
    file_hash: Optional[str] = None
    verification_status: Literal["pending", "in_progress", "verified", "needs_reverification", "failed"] = "pending"
    test_hours: float = 0.0
    test_cases_count: int = 0
    coverage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    validity_days: int = 90
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


class FileDependency(BaseModel):
    """ファイル依存関係"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    source_file: str
    dependent_file: str
    dependency_type: Literal["import", "test", "config", "api"] = "import"
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


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
    affected_dependents: List[Dict[str, Any]]
    total_affected_test_hours: float
    recommendations: List[str]


class ImpactReport(BaseModel):
    """影響分析レポート"""
    file_path: str
    verification_status: str
    test_hours: float
    direct_dependents: List[Dict[str, Any]]
    indirect_dependents: List[Dict[str, Any]]
    total_affected_files: int
    total_affected_test_hours: float
    risk_level: Literal["low", "medium", "high", "critical"]
    recommendations: List[str]
```

---

## 5. コンポーネント設計

### 5.1 FileVerificationRegistry サービス

**ファイル:** `bridge/temporal_constraint/registry.py`（新規）

```python
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
    ) -> FileVerification:
        """ファイル検証を登録"""

    async def update_verification(
        self,
        verification_id: UUID,
        verification_status: str,
        test_hours: Optional[float] = None,
        test_cases_count: Optional[int] = None,
        changed_by: str,
        reason: str,
    ) -> FileVerification:
        """検証ステータスを更新"""

    async def get_verification(
        self,
        user_id: str,
        file_path: str,
    ) -> Optional[FileVerification]:
        """ファイルの検証情報を取得"""

    async def get_expiring_verifications(
        self,
        user_id: str,
        days_until_expiry: int = 14,
    ) -> List[FileVerification]:
        """期限切れ間近の検証を取得"""

    async def invalidate_verification(
        self,
        verification_id: UUID,
        reason: str,
        invalidated_by: str,
    ) -> VerificationHistory:
        """検証を失効"""
```

### 5.2 ChangeGuard サービス

**ファイル:** `bridge/temporal_constraint/guard.py`（新規）

```python
class ChangeGuard:
    """変更ガードサービス"""

    # 警告レベルの閾値
    WARNING_THRESHOLDS = {
        "info": 2.0,      # 2時間未満
        "warning": 10.0,  # 10時間未満
        "critical": 10.0, # 10時間以上
    }

    def __init__(self, pool: asyncpg.Pool, registry: FileVerificationRegistry):
        self.pool = pool
        self.registry = registry

    async def check_file_modification(
        self,
        user_id: str,
        file_path: str,
    ) -> Optional[ChangeWarning]:
        """ファイル変更の可否をチェック"""

    async def request_approval(
        self,
        verification_id: UUID,
        requested_change: str,
        requested_by: str,
        approval_type: str = "normal",
    ) -> ChangeApproval:
        """変更承認をリクエスト"""

    async def approve_change(
        self,
        approval_id: UUID,
        decided_by: str,
        approval_reason: str,
    ) -> ChangeApproval:
        """変更を承認"""

    async def bypass_change(
        self,
        approval_id: UUID,
        bypassed_by: str,
        bypass_reason: str,
    ) -> ChangeApproval:
        """変更をバイパス（緊急時）"""
```

### 5.3 DependencyAnalyzer サービス

**ファイル:** `bridge/temporal_constraint/analyzer.py`（新規）

```python
class DependencyAnalyzer:
    """依存関係分析サービス"""

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

    async def get_dependents(
        self,
        user_id: str,
        file_path: str,
        include_indirect: bool = True,
    ) -> List[FileDependency]:
        """依存先ファイルを取得"""

    async def analyze_change_impact(
        self,
        user_id: str,
        file_path: str,
    ) -> ImpactReport:
        """変更影響を分析"""

    async def scan_dependencies(
        self,
        user_id: str,
        root_path: str,
    ) -> int:
        """プロジェクト内の依存関係をスキャン"""
```

---

## 6. API設計

### 6.1 エンドポイント一覧

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/verifications` | 検証登録 |
| GET | `/api/v1/verifications` | 検証一覧取得 |
| GET | `/api/v1/verifications/{file_path}` | 検証詳細取得 |
| PUT | `/api/v1/verifications/{id}` | 検証更新 |
| DELETE | `/api/v1/verifications/{id}` | 検証削除 |
| POST | `/api/v1/verifications/check` | 変更前チェック |
| GET | `/api/v1/verifications/expiring` | 期限切れ間近リスト |
| POST | `/api/v1/approvals` | 承認リクエスト |
| PUT | `/api/v1/approvals/{id}/approve` | 承認実行 |
| PUT | `/api/v1/approvals/{id}/bypass` | バイパス実行 |
| GET | `/api/v1/dependencies/{file_path}/impact` | 影響分析 |
| POST | `/api/v1/dependencies/scan` | 依存関係スキャン |

---

## 7. パフォーマンス

### 7.1 レイテンシ目標

| 操作 | 目標 |
|------|------|
| 検証登録 | < 100ms |
| 変更前チェック | < 200ms |
| 影響分析 | < 500ms |
| 依存関係スキャン | < 5s（100ファイル） |

### 7.2 インデックス設計

```sql
-- 高速検索用インデックス
CREATE INDEX idx_file_verifications_user_path ON file_verifications(user_id, file_path);
CREATE INDEX idx_file_verifications_status ON file_verifications(verification_status);
CREATE INDEX idx_file_verifications_expires ON file_verifications(expires_at);

-- 履歴検索
CREATE INDEX idx_verification_history_verification ON verification_history(verification_id);
CREATE INDEX idx_verification_history_changed_at ON verification_history(changed_at);

-- 依存関係検索
CREATE INDEX idx_file_dependencies_source ON file_dependencies(source_file);
CREATE INDEX idx_file_dependencies_dependent ON file_dependencies(dependent_file);
CREATE INDEX idx_file_dependencies_user ON file_dependencies(user_id);

-- 承認検索
CREATE INDEX idx_change_approvals_status ON change_approvals(approval_status);
CREATE INDEX idx_change_approvals_verification ON change_approvals(verification_id);
```

---

## 8. Re-evaluation Phase統合

### 8.1 統合ポイント

```python
class ReEvaluationIntegration:
    """Re-evaluation Phaseとの統合"""

    def __init__(
        self,
        reeval_service: ReEvaluationService,
        temporal_service: TemporalConstraintService,
    ):
        self.reeval_service = reeval_service
        self.temporal_service = temporal_service

    async def on_file_modified(
        self,
        user_id: str,
        file_path: str,
        modification_type: str,
        modified_by: str,
    ):
        """ファイル変更時の処理"""
        # 1. 検証ステータスを確認
        verification = await self.temporal_service.registry.get_verification(
            user_id, file_path
        )

        if verification and verification.verification_status == "verified":
            # 2. 検証を失効
            await self.temporal_service.registry.invalidate_verification(
                verification.id,
                reason=f"File modified: {modification_type}",
                invalidated_by=modified_by,
            )

            # 3. Re-evaluation Phaseをトリガー
            await self.reeval_service.trigger_reevaluation(
                user_id=user_id,
                target_type="file_verification",
                target_id=str(verification.id),
                reason=f"Verification invalidated due to file modification",
            )

            # 4. 依存ファイルに通知
            dependents = await self.temporal_service.analyzer.get_dependents(
                user_id, file_path
            )

            for dep in dependents:
                await self.notify_dependent_change(
                    user_id=user_id,
                    dependent_file=dep.dependent_file,
                    source_file=file_path,
                )
```

---

## 9. Git Hook統合（オプション）

### 9.1 Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 変更されたファイルを取得
changed_files=$(git diff --cached --name-only)

for file in $changed_files; do
    # Temporal Constraint APIをチェック
    response=$(curl -s -X POST "http://localhost:8000/api/v1/verifications/check" \
        -H "Content-Type: application/json" \
        -d "{\"file_path\": \"$file\", \"user_id\": \"$USER\"}")

    warning_level=$(echo $response | jq -r '.warning_level')

    if [ "$warning_level" == "critical" ]; then
        echo "⚠️  CRITICAL: Protected file modification detected!"
        echo "File: $file"
        echo $(echo $response | jq -r '.message')
        echo ""
        echo "To bypass, use: git commit --no-verify"
        exit 1
    elif [ "$warning_level" == "warning" ]; then
        echo "⚠️  WARNING: Verified file modification detected!"
        echo "File: $file"
        echo $(echo $response | jq -r '.message')
    fi
done

exit 0
```

---

## 10. 制約と前提

### 10.1 制約
- ファイルレベルの検証（関数レベルは将来拡張）
- 手動での検証登録（自動テスト連携は将来拡張）
- 単一プロジェクトスコープ（マルチプロジェクトは将来拡張）

### 10.2 前提
- Re-evaluation Phase実装済み
- PostgreSQL接続可能
- ファイルハッシュ計算可能（SHA256）

---

## 11. 今後の拡張

### 11.1 Sprint 14以降候補
- IDE統合（VSCode Extension）
- CI/CDパイプライン統合
- 自動テスト結果連携
- 関数レベルの検証トラッキング
- マルチプロジェクト対応

---

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総行数**: 700+
