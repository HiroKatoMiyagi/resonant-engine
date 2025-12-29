# Sprint 12: Term Drift Detection & Temporal Constraint Layer 統合仕様書

## 0. CRITICAL: Resonant Engineの哲学的完成

**⚠️ IMPORTANT: 「時間軸 = 知性の根幹・呼吸の連続性」**

Term Drift Detection（用語ドリフト検出）とTemporal Constraint Layer（時間軸制約層）は、Resonant Engineの哲学を完全に実現するための**最後の2つのピース**です。AIが「意味空間」だけで動作し「時間空間」を無視する問題を根本的に解決します。

```yaml
philosophy:
    essence: "理解とは共鳴、複製ではない"
    problem:
        - AIは「今」だけを最適化する
        - 過去の検証済みコードを破壊する
        - 用語の意味変化に気づかない
        - 時間軸を持たない知性は不完全
    solution:
        - Term Drift Detection: 用語の意味変化を追跡
        - Temporal Constraint Layer: 検証済みコードを保護
    outcome:
        - 「時間を持つ知性」の実現
        - 呼吸の連続性を保証
        - 人間-AI共進化の基盤完成
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] Term Drift Detection: 用語定義の変化を検出・警告
- [ ] Temporal Constraint Layer: 検証済みファイルの変更前に確認要求
- [ ] PostgreSQLスキーマ: 4テーブル追加
- [ ] 20件以上の単体/統合テスト作成、CI で緑

#### Tier 2: 品質要件
- [ ] 用語ドリフト検出精度 > 85%
- [ ] 検出レイテンシ < 500ms
- [ ] False Positive率 < 10%
- [ ] Observability: `term_drift_count`, `temporal_constraint_warnings`

---

## 1. 概要

### 1.1 目的

**2つの高度機能の実装目的:**

1. **Term Drift Detection（用語ドリフト検出）**
   - 用語の意味が時間とともに変化することを検出
   - 過去のコード・決定との整合性を維持
   - 暗黙の仮定変更を可視化

2. **Temporal Constraint Layer（時間軸制約層）**
   - 歴史的に検証済みのコードを保護
   - AIによる無意識の破壊を防止
   - 変更前の明示的確認を強制

### 1.2 背景

**現状の問題（11月比較検討時の指摘）:**

```
Week 1: User Profile = {name, email, password}
Week 4: User Profile = {name, email, password, cognitive_traits}
         ↓
問題: Week 1-3のコードは新定義に対応していない
      データマイグレーション必要？
      誰も気づいていない...

Week 1-4: Amazon SP-API連携を実装（100時間テスト）
Week 10: AI「データ取得を高速化します」
         ↓
問題: 検証済みコードが破壊される
      再テストに100時間必要
      AIは「最適化」としか思っていない
```

### 1.3 スコープ

**含む:**
- 用語定義の履歴管理
- 用語変化の自動検出
- 影響範囲の分析
- 検証済みファイルの保護
- 変更前の確認フロー
- APIエンドポイント
- フロントエンドUI

**含まない（将来拡張）:**
- 自動マイグレーション生成
- セマンティックバージョニング
- 複数プロジェクト間の用語同期

---

## 2. ユースケース

### 2.1 Term Drift Detection

#### UC-TD-1: 用語定義の変化検出

**シナリオ:**
Sprint 1で定義した「Intent」の意味が、Sprint 5で拡張された。

**Before（現状）:**
```python
# Sprint 1: Intent = ユーザーの要望
class Intent:
    content: str
    user_id: str

# Sprint 5: Intent = ユーザーの要望 + AI処理結果
class Intent:
    content: str
    user_id: str
    ai_response: Optional[str]     # 追加
    processing_status: str          # 追加
    
# 問題: Sprint 1-4のコードは新フィールドを扱えない
```

**After（Sprint 12）:**
```
⚠️ Term Drift Detected!

Term: "Intent"
Original Definition (Week 1):
  - Fields: content, user_id
  - Purpose: ユーザーの要望を表現

Current Definition (Week 5):
  - Fields: content, user_id, ai_response, processing_status
  - Purpose: ユーザーの要望 + AI処理結果

Impact Analysis:
  - 影響ファイル: 12件
  - 影響関数: 23件
  - マイグレーション推奨: Yes

Actions:
  [ ] 影響範囲を確認する
  [ ] 意図的な変更として承認
  [ ] 元の定義に戻す
```

#### UC-TD-2: 技術用語の暗黙的変更検出

**シナリオ:**
「認証」という用語の意味が変わった。

```
Week 1: "認証" = Basic Auth
Week 8: "認証" = JWT Token Auth (誰も明示的に変更を宣言していない)

⚠️ Term Drift Detected!

Term: "認証"
Context Changes:
  - Week 1: "Basic Auth", "ユーザー名/パスワード"
  - Week 8: "JWT", "Bearer Token", "OAuth"

Confidence: 0.87 (High)

Question: この用語の意味変化は意図的ですか？
```

### 2.2 Temporal Constraint Layer

#### UC-TC-1: 検証済みコードの保護

**シナリオ:**
100時間かけてテストしたAmazon SP-API連携コードをAIが「最適化」しようとした。

**Before（現状）:**
```
AI: "sp_api_client.pyのデータ取得を最適化します"
→ コード変更
→ 本番でバグ発生
→ 100時間のテストが無駄に
```

**After（Sprint 12）:**
```
⚠️ Temporal Constraint Warning!

File: sp_api_client.py
Status: VERIFIED (検証済み)

Verification History:
  - 2025-10-15: 100時間の統合テスト完了
  - 2025-10-20: 本番リリース
  - 2025-11-01: 30日間安定稼働確認

Constraint Level: HIGH
Last Verified: 35 days ago
Test Hours Invested: 100h

⚠️ このファイルは検証済みです。変更には以下が必要:

Questions:
  1. 本当に変更が必要ですか？ [Yes/No]
  2. 変更後の再テスト時間を確保できますか？ [Yes/No]
  3. 変更の理由を記録してください: [_____]

Actions:
  [ ] 変更を承認して続行
  [ ] 変更をキャンセル
  [ ] 新規ファイルとして実装
```

#### UC-TC-2: 検証レベルに応じた制約

```
Constraint Levels:

CRITICAL (赤):
  - 本番稼働中のコア機能
  - 変更には2人以上の承認が必要
  - 例: sp_api_client.py, auth_service.py

HIGH (オレンジ):
  - 検証済みだが比較的新しい
  - 変更には理由の記録が必要
  - 例: memory_store.py, intent_processor.py

MEDIUM (黄):
  - テスト済みだが検証期間が短い
  - 警告表示のみ
  - 例: dashboard_service.py

LOW (緑):
  - 開発中または未検証
  - 制約なし
  - 例: experimental/*.py
```

---

## 3. アーキテクチャ

### 3.1 全体構成

```
┌──────────────────────────────────────────────────────────────────┐
│         Term Drift Detection & Temporal Constraint System        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Term Drift Detection Layer                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                │   │
│  │  │ Term Registry   │  │ Drift Detector  │                │   │
│  │  │ (用語定義履歴)   │→│ (変化検出)       │                │   │
│  │  └─────────────────┘  └────────┬────────┘                │   │
│  │                                 │                         │   │
│  │  ┌─────────────────┐  ┌────────▼────────┐                │   │
│  │  │ Impact Analyzer │←─│ Alert Generator │                │   │
│  │  │ (影響範囲分析)   │  │ (警告生成)       │                │   │
│  │  └─────────────────┘  └─────────────────┘                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Temporal Constraint Layer                                │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                │   │
│  │  │ File Registry   │  │ Constraint      │                │   │
│  │  │ (ファイル履歴)   │→│ Checker         │                │   │
│  │  └─────────────────┘  └────────┬────────┘                │   │
│  │                                 │                         │   │
│  │  ┌─────────────────┐  ┌────────▼────────┐                │   │
│  │  │ Approval Flow   │←─│ Protection Gate │                │   │
│  │  │ (承認フロー)     │  │ (保護ゲート)     │                │   │
│  │  └─────────────────┘  └─────────────────┘                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Shared Components                                        │   │
│  │  - PostgreSQL Storage                                     │   │
│  │  - Event Bus (矛盾検出との連携)                            │   │
│  │  - API Layer                                              │   │
│  │  - Frontend UI                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 データフロー

#### Term Drift Detection

```
[New Intent/Document Created]
    ↓
1. Term Extraction
   ├─ 固有名詞抽出（Intent, Memory, Bridge...）
   ├─ 技術用語抽出（認証, API, データベース...）
   └─ 定義文抽出（"XはYである"パターン）
    ↓
2. Registry Lookup
   ├─ 既存定義との比較
   ├─ 類似度計算（Jaccard, Cosine）
   └─ 変化検出
    ↓
3. Drift Analysis
   ├─ 変化タイプ分類（拡張/縮小/変更）
   ├─ 信頼度スコア計算
   └─ 影響範囲特定
    ↓
4. Alert Generation
   ├─ 警告生成
   ├─ 推奨アクション提示
   └─ 通知送信
```

#### Temporal Constraint Layer

```
[File Modification Request]
    ↓
1. File Lookup
   ├─ verification_history 確認
   ├─ constraint_level 取得
   └─ last_verified 確認
    ↓
2. Constraint Check
   ├─ CRITICAL: 承認フロー起動
   ├─ HIGH: 理由記録要求
   ├─ MEDIUM: 警告表示
   └─ LOW: 通過
    ↓
3. Approval Flow (if needed)
   ├─ 確認質問表示
   ├─ 理由入力
   └─ 承認/却下
    ↓
4. Action
   ├─ 承認: 変更許可 + ログ記録
   └─ 却下: 変更ブロック
```

---

## 4. データモデル

### 4.1 PostgreSQLスキーマ

**ファイル**: `docker/postgres/009_term_drift_temporal_constraint.sql`

```sql
-- ========================================
-- Sprint 12: Term Drift & Temporal Constraint Tables
-- ========================================

-- ========================================
-- Part 1: Term Drift Detection
-- ========================================

-- 1. term_definitions（用語定義履歴）
CREATE TABLE IF NOT EXISTS term_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- 用語情報
    term_name VARCHAR(255) NOT NULL,
    term_category VARCHAR(100),  -- 'domain_object', 'technical', 'process', 'custom'
    
    -- 定義内容
    definition_text TEXT NOT NULL,
    definition_context TEXT,  -- どこで定義されたか
    definition_source VARCHAR(255),  -- ファイル名、Intent ID等
    
    -- 構造化定義（オプション）
    structured_definition JSONB,  -- {fields: [], methods: [], relations: []}
    
    -- バージョン管理
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES term_definitions(id),
    
    -- タイムスタンプ
    defined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_term_definitions_user ON term_definitions(user_id);
CREATE INDEX idx_term_definitions_term ON term_definitions(term_name);
CREATE INDEX idx_term_definitions_current ON term_definitions(is_current) WHERE is_current = TRUE;
CREATE INDEX idx_term_definitions_category ON term_definitions(term_category);

-- 2. term_drifts（検出されたドリフト）
CREATE TABLE IF NOT EXISTS term_drifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- 用語情報
    term_name VARCHAR(255) NOT NULL,
    
    -- 変化情報
    original_definition_id UUID REFERENCES term_definitions(id),
    new_definition_id UUID REFERENCES term_definitions(id),
    drift_type VARCHAR(50) NOT NULL,  -- 'expansion', 'contraction', 'semantic_shift', 'context_change'
    
    -- 分析結果
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    change_summary TEXT,
    impact_analysis JSONB,  -- {affected_files: [], affected_intents: [], severity: 'high'}
    
    -- ステータス
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'acknowledged', 'resolved', 'dismissed'
    resolution_action VARCHAR(100),  -- 'intentional_change', 'rollback', 'migration_needed'
    resolution_note TEXT,
    resolved_by VARCHAR(255),
    
    -- タイムスタンプ
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_term_drifts_user ON term_drifts(user_id);
CREATE INDEX idx_term_drifts_term ON term_drifts(term_name);
CREATE INDEX idx_term_drifts_status ON term_drifts(status);
CREATE INDEX idx_term_drifts_detected ON term_drifts(detected_at DESC);

-- ========================================
-- Part 2: Temporal Constraint Layer
-- ========================================

-- 3. file_verifications（ファイル検証履歴）
CREATE TABLE IF NOT EXISTS file_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- ファイル情報
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64),  -- SHA-256
    
    -- 検証情報
    verification_type VARCHAR(100),  -- 'unit_test', 'integration_test', 'manual_test', 'production_stable'
    verification_description TEXT,
    test_hours_invested FLOAT DEFAULT 0,  -- テストに費やした時間
    
    -- 制約レベル
    constraint_level VARCHAR(50) DEFAULT 'low',  -- 'critical', 'high', 'medium', 'low'
    
    -- タイムスタンプ
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stable_since TIMESTAMP WITH TIME ZONE,  -- 安定稼働開始日
    
    -- メタデータ
    verified_by VARCHAR(255),
    metadata JSONB
);

CREATE UNIQUE INDEX idx_file_verifications_file ON file_verifications(user_id, file_path);
CREATE INDEX idx_file_verifications_level ON file_verifications(constraint_level);
CREATE INDEX idx_file_verifications_verified ON file_verifications(verified_at DESC);

-- 4. temporal_constraint_logs（制約ログ）
CREATE TABLE IF NOT EXISTS temporal_constraint_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- ファイル情報
    file_path VARCHAR(500) NOT NULL,
    file_verification_id UUID REFERENCES file_verifications(id),
    
    -- リクエスト情報
    modification_type VARCHAR(50),  -- 'edit', 'delete', 'rename'
    modification_reason TEXT,
    requested_by VARCHAR(255),  -- 'user', 'ai_agent', 'system'
    
    -- 制約チェック結果
    constraint_level_at_check VARCHAR(50),
    check_result VARCHAR(50),  -- 'approved', 'rejected', 'pending'
    
    -- 承認情報
    approval_required BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approval_note TEXT,
    
    -- タイムスタンプ
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decided_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_temporal_logs_user ON temporal_constraint_logs(user_id);
CREATE INDEX idx_temporal_logs_file ON temporal_constraint_logs(file_path);
CREATE INDEX idx_temporal_logs_result ON temporal_constraint_logs(check_result);
CREATE INDEX idx_temporal_logs_time ON temporal_constraint_logs(requested_at DESC);

-- ========================================
-- Functions
-- ========================================

-- 用語の最新定義を取得
CREATE OR REPLACE FUNCTION get_current_term_definition(
    p_user_id VARCHAR,
    p_term_name VARCHAR
) RETURNS TABLE (
    id UUID,
    definition_text TEXT,
    version INTEGER,
    defined_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT td.id, td.definition_text, td.version, td.defined_at
    FROM term_definitions td
    WHERE td.user_id = p_user_id
      AND td.term_name = p_term_name
      AND td.is_current = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ファイルの制約レベルを取得
CREATE OR REPLACE FUNCTION get_file_constraint_level(
    p_user_id VARCHAR,
    p_file_path VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_level VARCHAR;
BEGIN
    SELECT constraint_level INTO v_level
    FROM file_verifications
    WHERE user_id = p_user_id
      AND file_path = p_file_path;
    
    RETURN COALESCE(v_level, 'low');
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Pydanticモデル

**ファイル**: `backend/app/services/term_drift/models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

# ========================================
# Enums
# ========================================

class TermCategory(str, Enum):
    DOMAIN_OBJECT = "domain_object"  # Intent, Memory, Bridge等
    TECHNICAL = "technical"           # 認証, API, データベース等
    PROCESS = "process"               # Sprint, Deploy, Test等
    CUSTOM = "custom"                 # ユーザー定義

class DriftType(str, Enum):
    EXPANSION = "expansion"           # フィールド追加等
    CONTRACTION = "contraction"       # フィールド削除等
    SEMANTIC_SHIFT = "semantic_shift" # 意味の変化
    CONTEXT_CHANGE = "context_change" # 使用コンテキストの変化

class DriftStatus(str, Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class ConstraintLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CheckResult(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"

# ========================================
# Term Drift Models
# ========================================

class TermDefinition(BaseModel):
    """用語定義"""
    id: Optional[UUID] = None
    user_id: str
    term_name: str
    term_category: TermCategory = TermCategory.CUSTOM
    definition_text: str
    definition_context: Optional[str] = None
    definition_source: Optional[str] = None
    structured_definition: Optional[Dict[str, Any]] = None
    version: int = 1
    is_current: bool = True
    defined_at: Optional[datetime] = None

class TermDrift(BaseModel):
    """検出されたドリフト"""
    id: Optional[UUID] = None
    user_id: str
    term_name: str
    original_definition_id: Optional[UUID] = None
    new_definition_id: Optional[UUID] = None
    drift_type: DriftType
    confidence_score: float = Field(ge=0.0, le=1.0)
    change_summary: str
    impact_analysis: Optional[Dict[str, Any]] = None
    status: DriftStatus = DriftStatus.PENDING
    detected_at: Optional[datetime] = None

class TermDriftResolution(BaseModel):
    """ドリフト解決リクエスト"""
    resolution_action: str  # 'intentional_change', 'rollback', 'migration_needed'
    resolution_note: str = Field(min_length=10)
    resolved_by: str

# ========================================
# Temporal Constraint Models
# ========================================

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
```

---

## 5. コンポーネント設計

### 5.1 Term Drift Detector

**ファイル**: `backend/app/services/term_drift/detector.py`

```python
import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
import re

from .models import (
    TermDefinition, TermDrift, DriftType, DriftStatus,
    TermCategory
)

logger = logging.getLogger(__name__)

class TermDriftDetector:
    """用語ドリフト検出サービス"""
    
    # 類似度閾値
    SIMILARITY_THRESHOLD = 0.7
    
    # ドメインオブジェクトキーワード
    DOMAIN_OBJECTS = [
        "Intent", "Memory", "Bridge", "Yuno", "Kana", "Tsumu",
        "Contradiction", "Choice", "Session", "Profile"
    ]
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def extract_terms_from_text(
        self,
        text: str,
        source: str
    ) -> List[Dict[str, Any]]:
        """
        テキストから用語定義を抽出
        
        Args:
            text: 分析対象テキスト
            source: ソース識別子（ファイル名等）
            
        Returns:
            List[Dict]: 抽出された用語定義リスト
        """
        extracted_terms = []
        
        # パターン1: "XはYである" / "X is Y"
        definition_patterns = [
            r'「([^」]+)」は[、]?(.+?)(?:です|である|とする)',
            r'(\w+)\s*(?:is|means|refers to)\s*(.+?)(?:\.|$)',
            r'# (\w+)\n+(.+?)(?:\n\n|$)',  # Markdown見出し
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                term_name, definition = match
                extracted_terms.append({
                    "term_name": term_name.strip(),
                    "definition_text": definition.strip()[:500],
                    "definition_source": source,
                    "term_category": self._categorize_term(term_name)
                })
        
        # パターン2: ドメインオブジェクト検出
        for domain_obj in self.DOMAIN_OBJECTS:
            if domain_obj in text:
                # コンテキストを抽出
                context = self._extract_context(text, domain_obj)
                if context and len(context) > 20:
                    extracted_terms.append({
                        "term_name": domain_obj,
                        "definition_text": context,
                        "definition_source": source,
                        "term_category": TermCategory.DOMAIN_OBJECT.value
                    })
        
        return extracted_terms
    
    def _categorize_term(self, term_name: str) -> str:
        """用語のカテゴリを判定"""
        if term_name in self.DOMAIN_OBJECTS:
            return TermCategory.DOMAIN_OBJECT.value
        
        technical_keywords = ["API", "Auth", "Database", "Token", "Cache"]
        if any(kw.lower() in term_name.lower() for kw in technical_keywords):
            return TermCategory.TECHNICAL.value
        
        process_keywords = ["Sprint", "Deploy", "Test", "Build", "Release"]
        if any(kw.lower() in term_name.lower() for kw in process_keywords):
            return TermCategory.PROCESS.value
        
        return TermCategory.CUSTOM.value
    
    def _extract_context(self, text: str, term: str) -> Optional[str]:
        """用語の周辺コンテキストを抽出"""
        sentences = re.split(r'[。.!?]', text)
        relevant_sentences = [s for s in sentences if term in s]
        
        if relevant_sentences:
            return '. '.join(relevant_sentences[:3])[:500]
        return None
    
    async def register_term_definition(
        self,
        user_id: str,
        term: Dict[str, Any]
    ) -> Tuple[UUID, bool]:
        """
        用語定義を登録（既存との比較・ドリフト検出含む）
        
        Args:
            user_id: ユーザーID
            term: 用語定義
            
        Returns:
            Tuple[UUID, bool]: (定義ID, ドリフト検出フラグ)
        """
        async with self.pool.acquire() as conn:
            # 既存定義を取得
            existing = await conn.fetchrow("""
                SELECT id, definition_text, version, defined_at
                FROM term_definitions
                WHERE user_id = $1 AND term_name = $2 AND is_current = TRUE
            """, user_id, term["term_name"])
            
            drift_detected = False
            
            if existing:
                # 類似度計算
                similarity = self._calculate_similarity(
                    existing['definition_text'],
                    term['definition_text']
                )
                
                if similarity < self.SIMILARITY_THRESHOLD:
                    # ドリフト検出！
                    drift_detected = True
                    
                    # 既存定義を非現行に
                    await conn.execute("""
                        UPDATE term_definitions
                        SET is_current = FALSE
                        WHERE id = $1
                    """, existing['id'])
                    
                    # 新定義を登録
                    new_id = await conn.fetchval("""
                        INSERT INTO term_definitions
                            (user_id, term_name, term_category, definition_text,
                             definition_source, version, is_current)
                        VALUES ($1, $2, $3, $4, $5, $6, TRUE)
                        RETURNING id
                    """, user_id, term["term_name"], term.get("term_category"),
                        term["definition_text"], term.get("definition_source"),
                        existing['version'] + 1)
                    
                    # ドリフトを記録
                    drift_type = self._determine_drift_type(
                        existing['definition_text'],
                        term['definition_text']
                    )
                    
                    await conn.execute("""
                        INSERT INTO term_drifts
                            (user_id, term_name, original_definition_id,
                             new_definition_id, drift_type, confidence_score,
                             change_summary)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, user_id, term["term_name"], existing['id'], new_id,
                        drift_type.value, 1.0 - similarity,
                        f"定義が変化: 類似度 {similarity:.2f}")
                    
                    logger.warning(
                        f"Term drift detected: {term['term_name']} "
                        f"(similarity: {similarity:.2f})"
                    )
                    
                    return new_id, True
                else:
                    # 変化なし、既存IDを返す
                    return existing['id'], False
            else:
                # 新規登録
                new_id = await conn.fetchval("""
                    INSERT INTO term_definitions
                        (user_id, term_name, term_category, definition_text,
                         definition_source, version, is_current)
                    VALUES ($1, $2, $3, $4, $5, 1, TRUE)
                    RETURNING id
                """, user_id, term["term_name"], term.get("term_category"),
                    term["definition_text"], term.get("definition_source"))
                
                return new_id, False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Jaccard類似度計算"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _determine_drift_type(self, old_def: str, new_def: str) -> DriftType:
        """ドリフトタイプを判定"""
        old_words = set(old_def.lower().split())
        new_words = set(new_def.lower().split())
        
        added = new_words - old_words
        removed = old_words - new_words
        
        if len(added) > len(removed) * 2:
            return DriftType.EXPANSION
        elif len(removed) > len(added) * 2:
            return DriftType.CONTRACTION
        elif len(added) > 0 and len(removed) > 0:
            return DriftType.SEMANTIC_SHIFT
        else:
            return DriftType.CONTEXT_CHANGE
    
    async def get_pending_drifts(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[TermDrift]:
        """未解決のドリフト一覧を取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM term_drifts
                WHERE user_id = $1 AND status = 'pending'
                ORDER BY detected_at DESC
                LIMIT $2
            """, user_id, limit)
            
            return [TermDrift(**dict(row)) for row in rows]
    
    async def resolve_drift(
        self,
        drift_id: UUID,
        resolution_action: str,
        resolution_note: str,
        resolved_by: str
    ) -> bool:
        """ドリフトを解決"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE term_drifts
                SET status = 'resolved',
                    resolution_action = $1,
                    resolution_note = $2,
                    resolved_by = $3,
                    resolved_at = NOW()
                WHERE id = $4 AND status = 'pending'
            """, resolution_action, resolution_note, resolved_by, drift_id)
            
            return result == "UPDATE 1"
```

### 5.2 Temporal Constraint Checker

**ファイル**: `backend/app/services/temporal_constraint/checker.py`

```python
import asyncpg
import logging
from typing import Optional, List
from datetime import datetime, timedelta
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
        days_since_verified = (datetime.utcnow() - verification.verified_at).days if verification.verified_at else 0
        
        warning_parts = [
            f"⚠️ Temporal Constraint Warning!",
            f"",
            f"File: {verification.file_path}",
            f"Status: VERIFIED (検証済み)",
            f"Constraint Level: {verification.constraint_level.upper()}",
            f"",
            f"Verification History:",
            f"  - Type: {verification.verification_type}",
            f"  - Verified: {days_since_verified} days ago",
            f"  - Test Hours Invested: {verification.test_hours_invested}h",
        ]
        
        if verification.stable_since:
            stable_days = (datetime.utcnow() - verification.stable_since).days
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
```

---

## 6. API設計

### 6.1 Term Drift API

**ファイル**: `backend/app/routers/term_drift.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID

from app.services.term_drift.detector import TermDriftDetector
from app.services.term_drift.models import (
    TermDefinition, TermDrift, TermDriftResolution
)
from app.dependencies import get_term_drift_detector

router = APIRouter(prefix="/api/v1/term-drift", tags=["term-drift"])

@router.get("/pending", response_model=List[TermDrift])
async def get_pending_drifts(
    user_id: str = Query(...),
    limit: int = Query(50, le=100),
    detector: TermDriftDetector = Depends(get_term_drift_detector)
):
    """未解決のドリフト一覧を取得"""
    return await detector.get_pending_drifts(user_id, limit)

@router.post("/analyze")
async def analyze_text(
    user_id: str,
    text: str,
    source: str,
    detector: TermDriftDetector = Depends(get_term_drift_detector)
):
    """テキストを分析して用語を抽出・ドリフトチェック"""
    terms = await detector.extract_terms_from_text(text, source)
    
    results = []
    for term in terms:
        definition_id, drift_detected = await detector.register_term_definition(
            user_id, term
        )
        results.append({
            "term_name": term["term_name"],
            "definition_id": str(definition_id),
            "drift_detected": drift_detected
        })
    
    return {
        "analyzed_terms": len(results),
        "drifts_detected": sum(1 for r in results if r["drift_detected"]),
        "results": results
    }

@router.put("/{drift_id}/resolve")
async def resolve_drift(
    drift_id: UUID,
    resolution: TermDriftResolution,
    detector: TermDriftDetector = Depends(get_term_drift_detector)
):
    """ドリフトを解決"""
    success = await detector.resolve_drift(
        drift_id,
        resolution.resolution_action,
        resolution.resolution_note,
        resolution.resolved_by
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Drift not found or already resolved")
    
    return {"status": "resolved", "drift_id": str(drift_id)}
```

### 6.2 Temporal Constraint API

**ファイル**: `backend/app/routers/temporal_constraint.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.services.temporal_constraint.checker import TemporalConstraintChecker
from app.services.temporal_constraint.models import (
    FileVerification, TemporalConstraintCheck, ModificationRequest,
    ConstraintLevel
)
from app.dependencies import get_temporal_constraint_checker

router = APIRouter(prefix="/api/v1/temporal-constraint", tags=["temporal-constraint"])

@router.post("/check", response_model=TemporalConstraintCheck)
async def check_modification(
    request: ModificationRequest,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイル変更の制約チェック"""
    return await checker.check_modification(request)

@router.post("/verify")
async def register_verification(
    user_id: str,
    file_path: str,
    verification_type: str,
    test_hours: float = 0,
    constraint_level: ConstraintLevel = ConstraintLevel.MEDIUM,
    description: Optional[str] = None,
    verified_by: Optional[str] = None,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイル検証を登録"""
    verification_id = await checker.register_verification(
        user_id, file_path, verification_type, test_hours,
        constraint_level, description, verified_by
    )
    
    return {
        "status": "registered",
        "verification_id": str(verification_id),
        "file_path": file_path,
        "constraint_level": constraint_level.value
    }

@router.post("/mark-stable")
async def mark_file_stable(
    user_id: str,
    file_path: str,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイルを安定稼働としてマーク"""
    success = await checker.mark_stable(user_id, file_path)
    
    if not success:
        raise HTTPException(status_code=404, detail="File verification not found")
    
    return {"status": "marked_stable", "file_path": file_path}

@router.post("/upgrade-critical")
async def upgrade_to_critical(
    user_id: str,
    file_path: str,
    reason: str,
    checker: TemporalConstraintChecker = Depends(get_temporal_constraint_checker)
):
    """ファイルをCRITICALレベルに昇格"""
    success = await checker.upgrade_to_critical(user_id, file_path, reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="File verification not found")
    
    return {"status": "upgraded_to_critical", "file_path": file_path}
```

---

## 7. 作業開始指示

### Day 1: データベーススキーマ & 基本モデル

**目標:**
- PostgreSQLスキーマ作成（4テーブル）
- Pydanticモデル定義
- 基本リポジトリ実装

**ステップ:**

1. マイグレーションファイル作成
   - `docker/postgres/009_term_drift_temporal_constraint.sql`
   - 上記セクション4.1のSQLを実行

2. モデル作成
   - `backend/app/services/term_drift/models.py`
   - `backend/app/services/temporal_constraint/models.py`

3. データベース適用
   ```bash
   docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard < docker/postgres/009_term_drift_temporal_constraint.sql
   ```

**成功基準:**
- [ ] 4テーブルがPostgreSQLに作成済み
- [ ] Pydanticモデルが定義済み
- [ ] 単体テスト2件作成

### Day 2: Term Drift Detector実装

**目標:**
- 用語抽出機能
- ドリフト検出ロジック
- 類似度計算

**ステップ:**

1. `backend/app/services/term_drift/detector.py`
   - `extract_terms_from_text`
   - `register_term_definition`
   - `_calculate_similarity`

2. 単体テスト作成
   - `tests/services/term_drift/test_detector.py`

**成功基準:**
- [ ] 用語抽出が動作
- [ ] ドリフト検出が動作
- [ ] 単体テスト5件以上作成

### Day 3: Temporal Constraint Checker実装

**目標:**
- 制約チェックロジック
- 検証登録機能
- 警告生成

**ステップ:**

1. `backend/app/services/temporal_constraint/checker.py`
   - `check_modification`
   - `register_verification`
   - `_generate_warning`

2. 単体テスト作成
   - `tests/services/temporal_constraint/test_checker.py`

**成功基準:**
- [ ] 制約チェックが動作
- [ ] 検証登録が動作
- [ ] 単体テスト5件以上作成

### Day 4: API実装 & DI統合

**目標:**
- FastAPIルーター作成
- dependencies.py統合
- main.py登録

**ステップ:**

1. ルーター作成
   - `backend/app/routers/term_drift.py`
   - `backend/app/routers/temporal_constraint.py`

2. DI設定
   ```python
   # backend/app/dependencies.py
   @lru_cache
   def get_term_drift_detector() -> TermDriftDetector:
       return TermDriftDetector(db.pool)
   
   @lru_cache
   def get_temporal_constraint_checker() -> TemporalConstraintChecker:
       return TemporalConstraintChecker(db.pool)
   ```

3. main.py登録
   ```python
   from app.routers import term_drift, temporal_constraint
   app.include_router(term_drift.router)
   app.include_router(temporal_constraint.router)
   ```

**成功基準:**
- [ ] 全APIエンドポイントが動作
- [ ] Swagger UIで確認可能
- [ ] 統合テスト3件以上作成

### Day 5: 統合テスト & ドキュメント

**目標:**
- E2Eテスト作成
- 矛盾検出との連携
- 運用ドキュメント

**ステップ:**

1. E2Eテスト
   - `tests/integration/test_term_drift_e2e.py`
   - `tests/integration/test_temporal_constraint_e2e.py`

2. 矛盾検出連携
   - Intent作成時に用語抽出を呼び出し
   - ファイル変更前に制約チェック

3. ドキュメント
   - API使用例
   - 運用手順

**成功基準:**
- [ ] E2Eテスト成功
- [ ] 矛盾検出連携動作
- [ ] ドキュメント完成

---

## 8. 非機能要件

### 8.1 パフォーマンス

| 操作 | 目標 |
|------|------|
| 用語抽出 | < 200ms |
| ドリフト検出 | < 500ms |
| 制約チェック | < 100ms |
| 検証登録 | < 200ms |

### 8.2 Observability

```python
# メトリクス
term_drift_count: Counter  # 検出されたドリフト数
term_drift_resolution_rate: Gauge  # 解決率
temporal_constraint_warnings: Counter  # 警告数
temporal_constraint_blocks: Counter  # ブロック数
```

---

## 9. 今後の拡張

### 9.1 Phase 2候補

1. **自動マイグレーション生成**
   - ドリフト検出時にDBマイグレーションを自動生成

2. **セマンティックバージョニング**
   - 用語定義にセマンティックバージョンを付与

3. **IDE統合**
   - VSCode/Cursor拡張で制約警告を表示

4. **CI/CD統合**
   - PRマージ前に自動チェック

---

## 10. アーキテクチャ制約と利用規約ベースアプローチ

### 10.1 アーキテクチャ上の制約

**制約の背景:**

現在のResonant Engineには、ソースコードの変更を行うための統一的なAPI（例: `FileModificationService`）が存在していません。AIエージェントやユーザーがファイルシステムを直接操作したり、様々な手段でファイルを書き換える可能性があるため、「あらゆるファイル変更の前に必ずTemporal Constraint Checkを通過させる」という仕組みをコードレベルで強制することが現状のアーキテクチャでは不可能です。

```
┌──────────────────────────────────────────────────────────────┐
│                    現状のファイルアクセス                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐    直接アクセス    ┌──────────────────┐        │
│  │ AIエージェント │ ─────────────────→ │   ファイルシステム   │        │
│  └─────────┘                    └──────────────────┘        │
│                                           ↑                 │
│  ┌─────────┐    直接アクセス              │                 │
│  │   IDE    │ ─────────────────────────────┘                 │
│  └─────────┘                                                │
│                                           ↑                 │
│  ┌─────────┐    直接アクセス              │                 │
│  │   CLI   │ ─────────────────────────────┘                 │
│  └─────────┘                                                │
│                                                              │
│  ⚠️ 制約チェックを強制できない                                │
└──────────────────────────────────────────────────────────────┘
```

### 10.2 利用規約ベースアプローチ（採用方針）

**方針:**

コードレベルでの強制ではなく、ファイル変更を行うクライアント（AIエージェント、IDEプラグイン、開発者）が**自主的に**制約チェックAPIを呼び出す「利用規約ベース」のアプローチを採用します。

```
┌──────────────────────────────────────────────────────────────┐
│                 利用規約ベースアプローチ                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐  1. チェック依頼  ┌──────────────────┐          │
│  │ AIエージェント │ ────────────────→ │ Temporal Constraint │          │
│  │ (協力的)  │ ←──────────────── │       API         │          │
│  └─────────┘  2. 結果・警告    └──────────────────┘          │
│       │                                                      │
│       │ 3. 承認後のみ書き込み                                  │
│       ↓                                                      │
│  ┌──────────────────┐                                        │
│  │   ファイルシステム   │                                        │
│  └──────────────────┘                                        │
│                                                              │
│  ✅ 協力的なクライアントは制約を遵守                            │
│  ⚠️ 非協力的なクライアントは制約をバイパス可能                    │
└──────────────────────────────────────────────────────────────┘
```

### 10.3 提供するツールとAPI

#### API エンドポイント

| エンドポイント | 用途 |
|---------------|------|
| `POST /api/v1/temporal-constraint/check` | ファイル変更前の制約チェック |
| `POST /api/v1/temporal-constraint/verify` | ファイル検証の登録 |
| `POST /api/v1/temporal-constraint/mark-stable` | 安定稼働マーク |
| `POST /api/v1/temporal-constraint/upgrade-critical` | CRITICALレベルへ昇格 |

#### CLI ツール（AIエージェント向け推奨）

```bash
# ファイル変更前の制約チェック
python utils/temporal_constraint_cli.py check --file path/to/file.py

# 制約チェック付きでファイル書き込み（AIエージェント向け推奨）
python utils/temporal_constraint_cli.py write --file path/to/file.py --reason "バグ修正: #123"

# ファイルを検証済みとして登録
python utils/temporal_constraint_cli.py verify --file path/to/file.py --hours 10 --level high

# 登録済みファイル一覧
python utils/temporal_constraint_cli.py list

# チェックログ確認
python utils/temporal_constraint_cli.py logs
```

### 10.4 AIエージェント統合ガイドライン

**AIエージェント（Claude Code, Cursor等）への推奨事項:**

1. **ファイル変更前には必ず制約チェックを実行**
   ```python
   # 推奨パターン
   result = await constraint_checker.check_modification(request)
   if not result.can_proceed:
       # ユーザーに確認を求める
       show_warning(result.warning_message)
       if not user_confirmed:
           return  # 変更を中止
   ```

2. **CLIラッパーの使用を推奨**
   - 直接ファイルを書き込む代わりに `temporal_constraint_cli.py write` を使用
   - 変更理由を必ず記録

3. **検証済みファイルの識別**
   - CRITICAL/HIGH 制約のファイルは慎重に扱う
   - 可能な限り新規ファイルとして実装を検討

### 10.5 将来の強制メカニズム（Phase 2以降）

| フェーズ | 対応 | 強制力 |
|---------|------|--------|
| **現在** | 利用規約ベース + CLIラッパー | なし（自主的） |
| **Phase 2** | Git Hooks / CI統合 | 中（コミット/マージ時） |
| **Phase 3** | FileModificationService | 高（コードレベル） |

```yaml
# Phase 2: pre-commit フック例
- repo: local
  hooks:
    - id: temporal-constraint-check
      name: Temporal Constraint Check
      entry: python utils/temporal_constraint_cli.py check --file
      language: system
      types: [python]
```

---

## 11. 参考資料

- [Sprint 11: Contradiction Detection仕様書](../contradiction/sprint11_contradiction_detection_spec.md)
- [kiro_resonant_comparison_handoff.md](../../../../kiro_resonant_comparison_handoff.md)
- [Resonant Engine進捗レポート](../../../reports/resonant_engine_status_report_20251229.md)

---

**作成日**: 2025-12-29  
**作成者**: Kana (Claude Opus 4.5)  
**バージョン**: 1.1.0  
**推定工数**: 5日間
