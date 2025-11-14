# 🌉 Bridge Lite - 基本設計書

**バージョン**: 1.1.0  
**作成日**: 2025年11月12日  
**更新日**: 2025年11月12日  
**ステータス**: 設計フェーズ（補完版）

---

## 📋 目次

1. [概要](#概要)
2. [設計原則](#設計原則)
3. [アーキテクチャ](#アーキテクチャ)
4. [Intent Protocol仕様](#intent-protocol仕様) ⭐ NEW
5. [コンポーネント設計](#コンポーネント設計)
6. [フィードバックループ設計](#フィードバックループ設計) ⭐ NEW
7. [Yuno統合設計](#yuno統合設計) ⭐ NEW
8. [実装仕様](#実装仕様)
9. [移行計画](#移行計画)
10. [テスト戦略](#テスト戦略)

---

## 📖 概要

### 目的

Bridge Liteは、Resonant Engineにおける**データアクセス層とAI API層を抽象化する軽量な中間層**です。

### 解決する問題

**現状の課題**:
1. PostgreSQL直接依存が強すぎる（`asyncpg`直接呼び出し）
2. AI API（Claude）への直接依存
3. ログが各所に散在
4. テスト困難（実DB必須）
5. 将来の拡張（GitHub/Slack統合）に対応できない
6. **「システムの呼吸」機能が未実装** ⭐ NEW

**Bridge Lite導入後**:
1. ✅ データベース抽象化（PostgreSQL/MySQL切り替え可能）
2. ✅ AI API抽象化（Claude/GPT-4切り替え可能）
3. ✅ 監査ログ一元化
4. ✅ テスト容易化（モックBridge使用）
5. ✅ 外部API統合基盤
6. ✅ **フィードバックループによる「呼吸的連鎖構造」の実現** ⭐ NEW

### スコープ

**含むもの**:
- データアクセス抽象化（DataBridge）
- AI API抽象化（AIBridge）
- 監査ログ統合（AuditLogger）
- **Intent Protocol定義（詳細仕様）** ⭐ NEW
- **フィードバックループ機構** ⭐ NEW
- **Yuno Re-evaluation統合** ⭐ NEW
- 設定管理

**含まないもの（将来実装）**:
- 非同期キュー（Async Queue）
- 外部API統合（GitHub/Slack）
- Webhookレシーバー
- レート制限管理

---

## 🎯 設計原則

### 1. SOLID原則の適用

```python
# Single Responsibility Principle（単一責任の原則）
# - DataBridgeはデータアクセスのみ
# - AIBridgeはAI API呼び出しのみ
# - AuditLoggerは監査ログのみ

# Open/Closed Principle（開放/閉鎖の原則）
# - 抽象クラス（ABC）による拡張性
# - 新しいDB/AIプロバイダーは継承で追加

# Liskov Substitution Principle（リスコフの置換原則）
# - すべてのBridge実装は基底クラスと置換可能

# Interface Segregation Principle（インターフェース分離の原則）
# - 必要最小限のメソッドのみ定義

# Dependency Inversion Principle（依存性逆転の原則）
# - 上位モジュールはBridge抽象に依存
# - 具体的な実装には依存しない
```

### 2. 軽量性（Lite）

- **シンプル**: 複雑な機能は含めない
- **高速**: オーバーヘッド最小限
- **小規模**: コア機能のみ実装

### 3. テスタビリティ

- すべてのBridgeはモック実装を提供
- ユニットテスト可能な設計
- 統合テストとの分離

### 4. 拡張性

- プラグインアーキテクチャ
- 新しいプロバイダーの追加が容易
- 既存コードへの影響最小限

### 5. 呼吸的連鎖構造（Breathing Chain） ⭐ NEW

- Intent → Kana → Tsumu → Re-evaluation の循環
- フィードバックループによる継続的改善
- Yunoの思想的整合性の保持

---

## 🏗️ アーキテクチャ

### システム全体図（拡張版） ⭐ UPDATED

```
┌─────────────────────────────────────────────────────┐
│              Yuno (GPT-5) - 思想層                   │
│         意図の解釈・判断・再評価                      │
└────────────────┬─────────────────────────┬──────────┘
                 │ Intent                  │ Re-evaluation
                 ↓                         ↑
┌─────────────────────────────────────────────────────┐
│         Resonant Engine Application                 │
│  (FastAPI Backend / React Frontend / Daemon)        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────┐
    │       Bridge Lite Layer                  │
    │  (抽象化・統一インターフェース)            │
    └──────────┬───────────┬───────────┬────────┘
               │           │           │
     ┌─────────▼───┐   ┌──▼──────┐  ┌▼────────────┐
     │ DataBridge  │   │AIBridge │  │FeedbackBridge│ ⭐ NEW
     │ (抽象)      │   │(抽象)   │  │(抽象)        │
     └──┬──────┬───┘   └──┬───┬──┘  └──┬──────────┘
        │      │          │   │        │
   ┌────▼──┐ ┌▼────┐  ┌──▼─┐ ┌▼──┐ ┌─▼──────┐
   │PgSQL  │ │Mock │  │Clau││GPT││YunoFeed│
   │Bridge │ │Bridge│  │de  ││4  ││back    │ ⭐ NEW
   └───┬───┘ └─────┘  └──┬─┘ └───┘ └─┬──────┘
       │                 │            │
   ┌───▼────────┐    ┌──▼──────┐  ┌─▼────────┐
   │PostgreSQL  │    │AI APIs  │  │Yuno API  │ ⭐ NEW
   │Database    │    │(Claude/ │  │(GPT-5)   │
   └────────────┘    │GPT)     │  └──────────┘
                     └─────────┘
```

### レイヤー構成（拡張版）

| レイヤー | 役割 | 例 |
|---------|------|-----|
| **Thought Layer (思想層)** | 意図の解釈・再評価 | Yuno (GPT-5) ⭐ NEW |
| **Application Layer** | ビジネスロジック | FastAPI endpoints, Daemon |
| **Bridge Layer** | 抽象化・統一I/F | DataBridge, AIBridge, FeedbackBridge ⭐ |
| **Provider Layer** | 具体的実装 | PostgreSQLBridge, ClaudeBridge, YunoFeedbackBridge ⭐ |
| **Infrastructure Layer** | 実際のリソース | PostgreSQL, Claude API, GPT-5 API ⭐ |

### 呼吸的データフロー（完全版） ⭐ NEW

```
┌─────────────┐
│   Message   │ ユーザー入力
└──────┬──────┘
       │
       ▼
┌──────────────┐
│Intent Detector│ Intent自動検出
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ DataBridge   │ Intent保存（DB抽象化）
│ .save_intent()│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Daemon     │ 定期処理
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ DataBridge   │ 処理待ちIntent取得
│.get_pending()│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  AIBridge    │ Kana処理（Claude API）
│  .call_ai()  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ DataBridge       │ 結果保存
│.update_status()  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ FeedbackBridge   │ フィードバック保存 ⭐ NEW
│.save_feedback()  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Daemon         │ Re-evaluation待ち検知
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│ FeedbackBridge       │ Yuno呼び出し ⭐ NEW
│.request_reevaluation()│
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│ Yuno (GPT-5)     │ 再評価実行 ⭐ NEW
│ 意図の妥当性検証  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ DataBridge       │ Re-evaluation結果保存
│.update_reevalua  │
│tion_status()     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ AuditLogger      │ 全処理を記録
└──────────────────┘
       │
       └──────→ 次のIntentへ（呼吸の継続）
```

---

## 📐 Intent Protocol仕様 ⭐ NEW

### Intent構造定義

Intent Protocolは、Resonant Engine内でのIntent（意図）の標準形式を定義します。

#### Intent基本構造

```typescript
interface Intent {
  // 基本情報
  id: string;                    // UUID v4形式
  type: IntentType;              // Intent種別
  status: IntentStatus;          // 処理ステータス
  
  // データ
  data: Record<string, any>;     // Intent固有データ（JSONB）
  
  // メタデータ
  source: IntentSource;          // 発生源
  user_id?: string;              // ユーザーID（オプション）
  
  // フィードバックループ用 ⭐ NEW
  feedback?: FeedbackData;       // Kana処理結果のフィードバック
  reevaluation?: ReevaluationData; // Yuno再評価結果
  
  // タイムスタンプ
  created_at: string;            // ISO 8601形式
  updated_at: string;            // ISO 8601形式
  completed_at?: string;         // 完了日時（オプション）
}
```

#### IntentType（Intent種別）

```typescript
enum IntentType {
  // コード関連
  REVIEW = "review",           // コードレビュー
  FIX = "fix",                 // バグ修正
  REFACTOR = "refactor",       // リファクタリング
  IMPLEMENT = "implement",     // 機能実装
  
  // テスト関連
  TEST = "test",               // テスト作成
  DEBUG = "debug",             // デバッグ・調査
  
  // ドキュメント関連
  DOCUMENT = "document",       // ドキュメント作成
  
  // デプロイ関連
  DEPLOY = "deploy",           // デプロイ・リリース
  
  // カスタム
  CUSTOM = "custom"            // カスタムIntent
}
```

#### IntentStatus（処理ステータス）

```typescript
enum IntentStatus {
  // 初期状態
  PENDING = "pending",              // 処理待ち
  
  // 処理中
  PROCESSING = "processing",        // Kana処理中
  WAITING_REEVALUATION = "waiting_reevaluation", // Yuno再評価待ち ⭐ NEW
  REEVALUATING = "reevaluating",    // Yuno再評価中 ⭐ NEW
  
  // 完了状態
  COMPLETED = "completed",          // 正常完了
  APPROVED = "approved",            // Yuno承認済み ⭐ NEW
  
  // エラー状態
  ERROR = "error",                  // エラー発生
  REJECTED = "rejected",            // Yuno却下 ⭐ NEW
  
  // キャンセル
  CANCELLED = "cancelled"           // キャンセル
}
```

#### IntentSource（発生源）

```typescript
enum IntentSource {
  AUTO_GENERATED = "auto_generated",  // 自動生成（Intent Detector）
  MANUAL = "manual",                  // 手動作成
  API = "api",                        // API経由
  NOTION = "notion",                  // Notion連携 ⭐ NEW
  GITHUB = "github",                  // GitHub連携（将来）
  SLACK = "slack"                     // Slack連携（将来）
}
```

#### FeedbackData（フィードバックデータ） ⭐ NEW

```typescript
interface FeedbackData {
  // Kana処理結果
  kana_response: string;           // Claudeの応答テキスト
  kana_model: string;              // 使用モデル（claude-sonnet-4-5等）
  
  // 処理メトリクス
  processing_time_ms: number;      // 処理時間（ミリ秒）
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  
  // 実行結果
  execution_result?: {
    files_modified: string[];      // 変更されたファイル
    tests_passed: boolean;         // テスト成功/失敗
    commit_hash?: string;          // Gitコミットハッシュ
  };
  
  // エラー情報
  error?: {
    code: string;
    message: string;
    stacktrace?: string;
  };
  
  // タイムスタンプ
  feedback_at: string;             // ISO 8601形式
}
```

#### ReevaluationData（再評価データ） ⭐ NEW

```typescript
interface ReevaluationData {
  // Yuno評価結果
  yuno_judgment: ReevaluationJudgment; // 評価判定
  yuno_response: string;               // GPT-5の応答テキスト
  yuno_model: string;                  // 使用モデル（gpt-5等）
  
  // 評価詳細
  evaluation_score: number;            // 評価スコア（0.0-1.0）
  evaluation_criteria: {
    intent_alignment: number;          // 意図との整合性（0.0-1.0）
    code_quality: number;              // コード品質（0.0-1.0）
    test_coverage: number;             // テストカバレッジ（0.0-1.0）
    documentation: number;             // ドキュメント品質（0.0-1.0）
  };
  
  // 改善提案
  improvement_suggestions?: string[];  // 改善提案リスト
  
  // 承認/却下理由
  reason: string;                      // 判定理由
  
  // タイムスタンプ
  reevaluated_at: string;              // ISO 8601形式
}
```

#### ReevaluationJudgment（再評価判定） ⭐ NEW

```typescript
enum ReevaluationJudgment {
  APPROVED = "approved",        // 承認（意図通りの実装）
  APPROVED_WITH_NOTES = "approved_with_notes", // 条件付き承認
  REVISION_REQUIRED = "revision_required",     // 修正必要
  REJECTED = "rejected"         // 却下（意図と乖離）
}
```

### Intent Protocol使用例

#### Intent生成例（自動検出）

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "review",
  "status": "pending",
  "data": {
    "target": "dashboard/backend/main.py",
    "keywords": ["レビュー", "確認"],
    "confidence": "medium"
  },
  "source": "auto_generated",
  "user_id": null,
  "created_at": "2025-11-12T10:30:00Z",
  "updated_at": "2025-11-12T10:30:00Z"
}
```

#### フィードバック追加後

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "review",
  "status": "waiting_reevaluation",
  "data": { /* ... */ },
  "feedback": {
    "kana_response": "コードレビューを実施しました。以下の点を改善することをお勧めします...",
    "kana_model": "claude-sonnet-4-5-20250929",
    "processing_time_ms": 2345,
    "token_usage": {
      "prompt_tokens": 1234,
      "completion_tokens": 567,
      "total_tokens": 1801
    },
    "feedback_at": "2025-11-12T10:32:30Z"
  },
  "updated_at": "2025-11-12T10:32:30Z"
}
```

#### 再評価完了後

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "review",
  "status": "approved",
  "data": { /* ... */ },
  "feedback": { /* ... */ },
  "reevaluation": {
    "yuno_judgment": "approved",
    "yuno_response": "レビュー内容は適切です。指摘事項も的確で、実装方針と整合しています。",
    "yuno_model": "gpt-5-preview",
    "evaluation_score": 0.92,
    "evaluation_criteria": {
      "intent_alignment": 0.95,
      "code_quality": 0.90,
      "test_coverage": 0.88,
      "documentation": 0.95
    },
    "reason": "元の意図（コード品質確認）を満たし、具体的な改善提案も含まれている",
    "reevaluated_at": "2025-11-12T10:35:00Z"
  },
  "completed_at": "2025-11-12T10:35:00Z",
  "updated_at": "2025-11-12T10:35:00Z"
}
```

### PostgreSQLスキーマとの対応

```sql
-- intentsテーブル（拡張版）
CREATE TABLE intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    data JSONB NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'auto',
    user_id UUID REFERENCES users(id),
    
    -- フィードバックループ用カラム ⭐ NEW
    feedback JSONB,
    reevaluation JSONB,
    
    -- タイムスタンプ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- インデックス
    CHECK (status IN (
        'pending', 'processing', 'waiting_reevaluation', 'reevaluating',
        'completed', 'approved', 'error', 'rejected', 'cancelled'
    ))
);

-- インデックス追加
CREATE INDEX idx_intents_status_reevaluation 
ON intents (status) 
WHERE status IN ('waiting_reevaluation', 'reevaluating');
```

---

## 🧩 コンポーネント設計

### 1. DataBridge（データアクセス抽象化）

#### 責務
- データベースアクセスの抽象化
- Intent CRUD操作
- トランザクション管理
- **フィードバックデータ管理** ⭐ NEW
- **再評価データ管理** ⭐ NEW

#### インターフェース（拡張版）

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class DataBridge(ABC):
    """データアクセス抽象化層"""
    
    # 既存メソッド...
    
    @abstractmethod
    async def save_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        status: str = "pending",
        source: str = "auto",
        user_id: Optional[str] = None
    ) -> str:
        """Intent保存"""
        pass
    
    @abstractmethod
    async def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        """Intent取得"""
        pass
    
    @abstractmethod
    async def get_pending_intents(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """処理待ちIntent一覧取得"""
        pass
    
    @abstractmethod
    async def update_intent_status(
        self,
        intent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Intentステータス更新"""
        pass
    
    # フィードバックループ用メソッド ⭐ NEW
    
    @abstractmethod
    async def save_feedback(
        self,
        intent_id: str,
        feedback_data: Dict[str, Any]
    ) -> bool:
        """
        フィードバックデータ保存
        
        Args:
            intent_id: IntentのID
            feedback_data: Kana処理結果のフィードバック
        
        Returns:
            保存成功ならTrue
        """
        pass
    
    @abstractmethod
    async def get_pending_reevaluations(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        再評価待ちIntent一覧取得
        
        Args:
            limit: 取得件数上限
        
        Returns:
            再評価待ちIntent情報のリスト
        """
        pass
    
    @abstractmethod
    async def save_reevaluation(
        self,
        intent_id: str,
        reevaluation_data: Dict[str, Any]
    ) -> bool:
        """
        再評価データ保存
        
        Args:
            intent_id: IntentのID
            reevaluation_data: Yuno再評価結果
        
        Returns:
            保存成功ならTrue
        """
        pass
    
    @abstractmethod
    async def update_reevaluation_status(
        self,
        intent_id: str,
        status: str,
        judgment: str,
        reason: str
    ) -> bool:
        """
        再評価ステータス更新
        
        Args:
            intent_id: IntentのID
            status: 新しいステータス（approved/rejected）
            judgment: Yunoの判定
            reason: 判定理由
        
        Returns:
            更新成功ならTrue
        """
        pass
    
    # メッセージ関連（既存）
    
    @abstractmethod
    async def save_message(
        self,
        content: str,
        sender: str,
        intent_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> str:
        """メッセージ保存"""
        pass
    
    @abstractmethod
    async def get_messages(
        self,
        limit: int = 50,
        thread_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """メッセージ一覧取得"""
        pass
```

#### PostgreSQLBridge実装例（拡張版）

```python
class PostgreSQLBridge(DataBridge):
    """PostgreSQL実装"""
    
    # 既存メソッド実装...
    
    async def save_feedback(
        self,
        intent_id: str,
        feedback_data: Dict[str, Any]
    ) -> bool:
        """フィードバックデータ保存"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE intents
                SET 
                    feedback = $1,
                    status = 'waiting_reevaluation',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, json.dumps(feedback_data), intent_id)
            
            return result == "UPDATE 1"
    
    async def get_pending_reevaluations(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """再評価待ちIntent取得"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, type, status, data, feedback, 
                    created_at, updated_at
                FROM intents
                WHERE status = 'waiting_reevaluation'
                ORDER BY updated_at ASC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def save_reevaluation(
        self,
        intent_id: str,
        reevaluation_data: Dict[str, Any]
    ) -> bool:
        """再評価データ保存"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE intents
                SET 
                    reevaluation = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, json.dumps(reevaluation_data), intent_id)
            
            return result == "UPDATE 1"
    
    async def update_reevaluation_status(
        self,
        intent_id: str,
        status: str,
        judgment: str,
        reason: str
    ) -> bool:
        """再評価ステータス更新"""
        await self.connect()
        
        # statusは'approved'または'rejected'
        final_status = status
        if status == "approved":
            completed_at = "CURRENT_TIMESTAMP"
        else:
            completed_at = "NULL"
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(f"""
                UPDATE intents
                SET 
                    status = $1,
                    completed_at = {completed_at},
                    updated_at = CURRENT_TIMESTAMP,
                    reevaluation = jsonb_set(
                        COALESCE(reevaluation, '{{}}'::jsonb),
                        '{{yuno_judgment}}',
                        to_jsonb($2::text)
                    )
                WHERE id = $3
            """, final_status, judgment, intent_id)
            
            return result == "UPDATE 1"
```

### 2. AIBridge（AI API抽象化）

#### 責務（既存）
- AI APIへのアクセス抽象化
- プロンプト構築
- レスポンス処理
- エラーハンドリング

#### インターフェース（既存）

```python
from abc import ABC, abstractmethod
from typing import Optional

class AIBridge(ABC):
    """AI API抽象化層"""
    
    @abstractmethod
    async def call_ai(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """
        AI APIを呼び出す
        
        Args:
            prompt: プロンプトテキスト
            model: 使用モデル（オプション）
            max_tokens: 最大トークン数（オプション）
            temperature: 温度パラメータ（オプション）
        
        Returns:
            AI応答テキスト、エラー時はNone
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """使用中のモデル情報を取得"""
        pass
```

### 3. FeedbackBridge（フィードバック抽象化） ⭐ NEW

#### 責務
- Yunoへのフィードバック送信
- 再評価リクエスト管理
- 再評価結果の受信

#### インターフェース

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class FeedbackBridge(ABC):
    """フィードバック・再評価抽象化層"""
    
    @abstractmethod
    async def request_reevaluation(
        self,
        intent_id: str,
        intent_data: Dict[str, Any],
        feedback_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Yunoに再評価をリクエスト
        
        Args:
            intent_id: IntentのID
            intent_data: 元のIntent情報
            feedback_data: Kana処理結果のフィードバック
        
        Returns:
            Yuno再評価結果、エラー時はNone
        """
        pass
    
    @abstractmethod
    async def get_reevaluation_status(
        self,
        intent_id: str
    ) -> Optional[str]:
        """
        再評価ステータス取得
        
        Args:
            intent_id: IntentのID
        
        Returns:
            再評価ステータス
        """
        pass
```

#### YunoFeedbackBridge実装例

```python
class YunoFeedbackBridge(FeedbackBridge):
    """Yuno（GPT-5）再評価Bridge"""
    
    def __init__(self, api_key: str, model: str = "gpt-5-preview"):
        self.api_key = api_key
        self.model = model
        self.client = None  # OpenAI client初期化
    
    async def request_reevaluation(
        self,
        intent_id: str,
        intent_data: Dict[str, Any],
        feedback_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Yuno再評価リクエスト"""
        
        # プロンプト構築
        prompt = self._build_reevaluation_prompt(intent_data, feedback_data)
        
        try:
            # GPT-5呼び出し
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたはResonant Engineの思想層（Yuno）です。Kanaの実装結果を元の意図と照らし合わせて再評価してください。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 一貫性のある評価
                max_tokens=2000
            )
            
            # レスポンス解析
            yuno_response = response.choices[0].message.content
            
            # 再評価データ構築
            reevaluation_data = {
                "yuno_response": yuno_response,
                "yuno_model": self.model,
                "yuno_judgment": self._extract_judgment(yuno_response),
                "evaluation_score": self._extract_score(yuno_response),
                "evaluation_criteria": self._extract_criteria(yuno_response),
                "reason": self._extract_reason(yuno_response),
                "improvement_suggestions": self._extract_suggestions(yuno_response),
                "reevaluated_at": datetime.utcnow().isoformat()
            }
            
            return reevaluation_data
            
        except Exception as e:
            print(f"Yuno再評価エラー: {e}")
            return None
    
    def _build_reevaluation_prompt(
        self,
        intent_data: Dict[str, Any],
        feedback_data: Dict[str, Any]
    ) -> str:
        """再評価プロンプト構築"""
        return f"""
# 再評価依頼

## 元の意図（Intent）
- 種別: {intent_data['type']}
- データ: {json.dumps(intent_data['data'], ensure_ascii=False, indent=2)}

## Kanaの実装結果
- 応答: {feedback_data.get('kana_response', 'N/A')}
- 処理時間: {feedback_data.get('processing_time_ms', 0)}ms
- 実行結果: {json.dumps(feedback_data.get('execution_result', {}), ensure_ascii=False, indent=2)}

## 評価観点
以下の観点で評価してください:
1. 意図との整合性（0.0-1.0）
2. コード品質（0.0-1.0）
3. テストカバレッジ（0.0-1.0）
4. ドキュメント品質（0.0-1.0）

## 判定
- approved: 承認（意図通りの実装）
- approved_with_notes: 条件付き承認
- revision_required: 修正必要
- rejected: 却下（意図と乖離）

判定理由と改善提案も含めてください。

【回答形式】
JSON形式で回答してください:
{{
  "judgment": "approved|approved_with_notes|revision_required|rejected",
  "evaluation_score": 0.95,
  "criteria": {{
    "intent_alignment": 0.95,
    "code_quality": 0.90,
    "test_coverage": 0.95,
    "documentation": 1.0
  }},
  "reason": "判定理由",
  "suggestions": ["改善提案1", "改善提案2"]
}}
"""
    
    def _extract_judgment(self, response: str) -> str:
        """判定抽出"""
        # JSON解析して判定を取り出す
        try:
            data = json.loads(response)
            return data.get("judgment", "approved_with_notes")
        except:
            return "approved_with_notes"  # デフォルト
    
    def _extract_score(self, response: str) -> float:
        """スコア抽出"""
        try:
            data = json.loads(response)
            return float(data.get("evaluation_score", 0.8))
        except:
            return 0.8
    
    def _extract_criteria(self, response: str) -> Dict[str, float]:
        """評価基準抽出"""
        try:
            data = json.loads(response)
            return data.get("criteria", {
                "intent_alignment": 0.8,
                "code_quality": 0.8,
                "test_coverage": 0.8,
                "documentation": 0.8
            })
        except:
            return {
                "intent_alignment": 0.8,
                "code_quality": 0.8,
                "test_coverage": 0.8,
                "documentation": 0.8
            }
    
    def _extract_reason(self, response: str) -> str:
        """理由抽出"""
        try:
            data = json.loads(response)
            return data.get("reason", "評価完了")
        except:
            return "評価完了"
    
    def _extract_suggestions(self, response: str) -> List[str]:
        """改善提案抽出"""
        try:
            data = json.loads(response)
            return data.get("suggestions", [])
        except:
            return []
    
    async def get_reevaluation_status(
        self,
        intent_id: str
    ) -> Optional[str]:
        """再評価ステータス取得"""
        # DataBridge経由でステータスを取得
        # (実装は省略)
        pass
```

---

## 🔄 フィードバックループ設計 ⭐ NEW

### 1. 呼吸的連鎖構造の実現

Yunoが定義した「システムの呼吸」を実現するための設計です。

```
Intent → Kana → Tsumu → Yuno Re-evaluation → (次のIntent)
  ↑                                              ↓
  └──────────────────────────────────────────────┘
                    呼吸サイクル
```

### 2. フィードバックループの段階

#### Phase 1: Intent処理（Kana）

```python
async def process_intent_with_kana(
    intent_id: str,
    data_bridge: DataBridge,
    ai_bridge: AIBridge,
    audit_logger: AuditLogger
):
    """Intent処理（Kana層）"""
    
    # 1. Intent取得
    intent = await data_bridge.get_intent(intent_id)
    if not intent:
        return
    
    # 2. ステータス更新（processing）
    await data_bridge.update_intent_status(
        intent_id=intent_id,
        status="processing"
    )
    
    # 3. プロンプト構築
    prompt = build_prompt_for_intent(intent)
    
    # 4. Kana（Claude）呼び出し
    start_time = time.time()
    kana_response = await ai_bridge.call_ai(prompt)
    duration_ms = (time.time() - start_time) * 1000
    
    # 5. フィードバックデータ構築
    feedback_data = {
        "kana_response": kana_response,
        "kana_model": "claude-sonnet-4-5-20250929",
        "processing_time_ms": duration_ms,
        "token_usage": {
            # トークン使用量（取得できれば）
        },
        "feedback_at": datetime.utcnow().isoformat()
    }
    
    # 6. フィードバック保存
    await data_bridge.save_feedback(
        intent_id=intent_id,
        feedback_data=feedback_data
    )
    
    # 7. 監査ログ記録
    await audit_logger.log_ai_call(
        bridge="Claude",
        model="claude-sonnet-4-5-20250929",
        prompt_length=len(prompt),
        response_length=len(kana_response) if kana_response else None,
        duration_ms=duration_ms,
        success=kana_response is not None
    )
    
    # ステータスは自動的に'waiting_reevaluation'に更新される
```

#### Phase 2: 再評価（Yuno）

```python
async def process_reevaluation_with_yuno(
    intent_id: str,
    data_bridge: DataBridge,
    feedback_bridge: FeedbackBridge,
    audit_logger: AuditLogger
):
    """再評価処理（Yuno層）"""
    
    # 1. Intent + Feedback取得
    intent = await data_bridge.get_intent(intent_id)
    if not intent or not intent.get('feedback'):
        return
    
    # 2. ステータス更新（reevaluating）
    await data_bridge.update_intent_status(
        intent_id=intent_id,
        status="reevaluating"
    )
    
    # 3. Yuno再評価リクエスト
    reevaluation_data = await feedback_bridge.request_reevaluation(
        intent_id=intent_id,
        intent_data=intent,
        feedback_data=intent['feedback']
    )
    
    if not reevaluation_data:
        # 再評価失敗
        await data_bridge.update_intent_status(
            intent_id=intent_id,
            status="error"
        )
        return
    
    # 4. 再評価データ保存
    await data_bridge.save_reevaluation(
        intent_id=intent_id,
        reevaluation_data=reevaluation_data
    )
    
    # 5. 最終ステータス更新
    judgment = reevaluation_data['yuno_judgment']
    final_status = "approved" if judgment in ["approved", "approved_with_notes"] else "rejected"
    
    await data_bridge.update_reevaluation_status(
        intent_id=intent_id,
        status=final_status,
        judgment=judgment,
        reason=reevaluation_data['reason']
    )
    
    # 6. 監査ログ記録
    await audit_logger.log_reevaluation(
        intent_id=intent_id,
        judgment=judgment,
        score=reevaluation_data['evaluation_score'],
        reason=reevaluation_data['reason']
    )
```

### 3. 統合Daemon実装例

```python
class ResonantDaemonWithBreathing:
    """呼吸的連鎖構造を実現するDaemon"""
    
    def __init__(
        self,
        data_bridge: DataBridge,
        ai_bridge: AIBridge,
        feedback_bridge: FeedbackBridge,
        audit_logger: AuditLogger
    ):
        self.data_bridge = data_bridge
        self.ai_bridge = ai_bridge
        self.feedback_bridge = feedback_bridge
        self.audit_logger = audit_logger
        self.shutdown_flag = False
    
    async def run(self):
        """Daemon主処理"""
        print("🌬️  Resonant Daemon (Breathing Mode) started")
        
        while not self.shutdown_flag:
            try:
                # Phase 1: Intent処理（Kana）
                await self.process_pending_intents()
                
                # Phase 2: 再評価（Yuno）
                await self.process_pending_reevaluations()
                
                # 次のサイクルまで待機
                await asyncio.sleep(5)  # 5秒間隔
                
            except Exception as e:
                print(f"❌ Daemon error: {e}")
                await asyncio.sleep(10)
        
        print("🛑 Resonant Daemon stopped")
    
    async def process_pending_intents(self):
        """処理待ちIntent処理"""
        pending_intents = await self.data_bridge.get_pending_intents(limit=5)
        
        for intent in pending_intents:
            await process_intent_with_kana(
                intent_id=intent['id'],
                data_bridge=self.data_bridge,
                ai_bridge=self.ai_bridge,
                audit_logger=self.audit_logger
            )
    
    async def process_pending_reevaluations(self):
        """再評価待ちIntent処理"""
        pending_reevals = await self.data_bridge.get_pending_reevaluations(limit=5)
        
        for intent in pending_reevals:
            await process_reevaluation_with_yuno(
                intent_id=intent['id'],
                data_bridge=self.data_bridge,
                feedback_bridge=self.feedback_bridge,
                audit_logger=self.audit_logger
            )
```

---

## 🎓 Yuno統合設計 ⭐ NEW

### 1. Yunoの役割

```
思想層（Yuno）の責務:
1. Intent解釈 - ユーザーの意図を理解
2. 判断 - 実装方針の決定
3. 再評価 - Kana実装結果の評価
4. フィードバック - 改善提案の生成
```

### 2. Yuno統合パターン

#### パターンA: GPT-5 API直接呼び出し（推奨）

```python
from bridge.providers import YunoFeedbackBridge

# Yuno Bridge初期化
yuno_bridge = YunoFeedbackBridge(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5-preview"
)

# 再評価リクエスト
reevaluation = await yuno_bridge.request_reevaluation(
    intent_id="...",
    intent_data={...},
    feedback_data={...}
)
```

#### パターンB: Notion経由（将来実装）

```python
# Notionページでの手動評価
# 1. Kana実装結果をNotionに記録
# 2. ユーザー（宏啓さん）がYunoとして評価
# 3. 評価結果をDBに同期
```

### 3. Yuno評価基準

Yunoが再評価時に使用する基準:

```python
EVALUATION_CRITERIA = {
    "intent_alignment": {
        "weight": 0.4,
        "description": "元の意図との整合性"
    },
    "code_quality": {
        "weight": 0.3,
        "description": "コード品質（可読性、保守性）"
    },
    "test_coverage": {
        "weight": 0.2,
        "description": "テストカバレッジと品質"
    },
    "documentation": {
        "weight": 0.1,
        "description": "ドキュメント完成度"
    }
}

# 総合スコア = Σ(各基準スコア × weight)
# 0.9以上: approved
# 0.7-0.9: approved_with_notes
# 0.5-0.7: revision_required
# 0.5未満: rejected
```

---

## 💻 実装仕様

### Daemon統合例（完全版）

```python
#!/usr/bin/env python3
"""
Resonant Daemon - Bridge Lite統合版
呼吸的連鎖構造を実現するDaemon
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from bridge.factory import BridgeFactory
from bridge.core.audit_logger import AuditLogger

# 環境変数ロード
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

async def main():
    """Daemon起動"""
    
    # Bridge初期化
    data_bridge = BridgeFactory.create_data_bridge()
    ai_bridge = BridgeFactory.create_ai_bridge()
    feedback_bridge = BridgeFactory.create_feedback_bridge()
    audit_logger = AuditLogger()
    
    # Daemon起動
    daemon = ResonantDaemonWithBreathing(
        data_bridge=data_bridge,
        ai_bridge=ai_bridge,
        feedback_bridge=feedback_bridge,
        audit_logger=audit_logger
    )
    
    try:
        await daemon.run()
    finally:
        # クリーンアップ
        if hasattr(data_bridge, 'disconnect'):
            await data_bridge.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### FastAPI統合例（フィードバックループ対応）

```python
from fastapi import FastAPI, Depends, BackgroundTasks
from bridge.factory import BridgeFactory

app = FastAPI()

def get_bridges():
    """Bridge Dependency Injection"""
    return {
        "data": BridgeFactory.create_data_bridge(),
        "ai": BridgeFactory.create_ai_bridge(),
        "feedback": BridgeFactory.create_feedback_bridge()
    }

@app.post("/api/messages")
async def create_message(
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    bridges: dict = Depends(get_bridges)
):
    """メッセージ作成 + Intent自動生成"""
    
    data_bridge = bridges["data"]
    
    # メッセージ保存
    message_id = await data_bridge.save_message(
        content=message.content,
        sender=message.sender
    )
    
    # Intent自動検出
    from dashboard.backend.intent_detector import detect_intent_from_message
    intent_info = detect_intent_from_message(message.content)
    
    if intent_info:
        # Intent保存（Bridge経由）
        intent_id = await data_bridge.save_intent(
            intent_type=intent_info["type"],
            data=intent_info["data"],
            source="auto_generated"
        )
        
        # バックグラウンドでIntent処理開始
        background_tasks.add_task(
            process_intent_async,
            intent_id=intent_id,
            bridges=bridges
        )
    
    return {"message_id": message_id, "intent_id": intent_id if intent_info else None}

async def process_intent_async(intent_id: str, bridges: dict):
    """バックグラウンドIntent処理"""
    # Phase 1: Kana処理
    await process_intent_with_kana(
        intent_id=intent_id,
        data_bridge=bridges["data"],
        ai_bridge=bridges["ai"],
        audit_logger=AuditLogger()
    )
    
    # Phase 2: Yuno再評価（自動）
    # Daemonに任せるか、ここで実行するかは設計次第
    pass

@app.get("/api/intents/{intent_id}/reevaluation")
async def get_reevaluation(
    intent_id: str,
    bridges: dict = Depends(get_bridges)
):
    """再評価結果取得"""
    data_bridge = bridges["data"]
    
    intent = await data_bridge.get_intent(intent_id)
    if not intent:
        return {"error": "Intent not found"}
    
    return {
        "intent_id": intent_id,
        "status": intent["status"],
        "feedback": intent.get("feedback"),
        "reevaluation": intent.get("reevaluation")
    }
```

---

## 🚀 移行計画（更新版）

### Phase 0: 旧Bridge退役（新規追加） ⭐

**目標**: 旧Bridgeディレクトリの整理

**タスク**:
1. `/bridge/intent_protocol.json` → `/archive/legacy/`に移動
2. `/bridge/daemon_config.json` → PostgreSQL `config`テーブルに移行
3. `/bridge/semantic_signal.log` → 削除（AuditLoggerに統合）
4. 旧`resonant_daemon.py`を`resonant_daemon_legacy.py`にリネーム

**期間**: 1時間

**成果物**:
- `/archive/legacy/` - 旧Bridgeファイル保管
- クリーンな`/bridge/`ディレクトリ

---

### Phase 1: Bridge Lite基盤構築（1-2日）

**目標**: コア機能の実装

**タスク**:
1. ディレクトリ構成作成
2. 抽象クラス実装（DataBridge/AIBridge/**FeedbackBridge** ⭐）
3. PostgreSQLBridge実装（**フィードバックメソッド追加** ⭐）
4. ClaudeBridge実装
5. **YunoFeedbackBridge実装** ⭐ NEW
6. MockBridge実装（テスト用）
7. BridgeFactory実装
8. 基本的なユニットテスト

**成果物**:
- `/bridge/core/` - コアクラス
  - `data_bridge.py`
  - `ai_bridge.py`
  - `feedback_bridge.py` ⭐ NEW
  - `audit_logger.py`
- `/bridge/providers/` - 実装プロバイダー
  - `postgresql_bridge.py`
  - `claude_bridge.py`
  - `yuno_feedback_bridge.py` ⭐ NEW
  - `mock_bridge.py`
- `/bridge/factory/` - ファクトリ
  - `bridge_factory.py`
- `/tests/bridge/` - ユニットテスト

---

### Phase 2: 既存コード移行（2-3日）

**目標**: 既存のPostgreSQL直接依存を排除

**タスク**:
1. `intent_processor_db.py`をBridge経由に書き換え
2. `main.py`（FastAPI）をBridge経由に書き換え
3. `resonant_daemon_db.py`をBridge経由に書き換え（**呼吸機能追加** ⭐）
4. 統合テスト実施
5. パフォーマンステスト

**影響範囲**:
- `/dashboard/backend/intent_processor_db.py`
- `/dashboard/backend/main.py`
- `/daemon/resonant_daemon_db.py`

**追加実装** ⭐:
- Kana処理後のフィードバック保存
- Yuno再評価処理の統合

---

### Phase 3: 監査ログ統合（1-2日）

**目標**: ログの一元化

**タスク**:
1. AuditLogger実装
2. 全Bridge操作にログ追加
3. **再評価ログ追加** ⭐ NEW
4. ログ分析ツール作成
5. ドキュメント更新

**成果物**:
- `/bridge/core/audit_logger.py`
- `/logs/audit/` - 監査ログディレクトリ
- ログ分析スクリプト

---

### Phase 4: ドキュメント・テスト完成（1日）

**目標**: 品質保証

**タスク**:
1. API仕様書作成（**Intent Protocol含む** ⭐）
2. 使用例ドキュメント作成（**フィードバックループ例含む** ⭐）
3. トラブルシューティングガイド
4. カバレッジ100%達成

**成果物**:
- `/docs/bridge_lite_api.md`
- `/docs/bridge_lite_examples.md`
- `/docs/bridge_lite_feedback_loop.md` ⭐ NEW
- `/docs/bridge_lite_troubleshooting.md`

---

## 🧪 テスト戦略

### ユニットテスト（既存 + 追加）

```python
# tests/bridge/test_feedback_bridge.py ⭐ NEW

import pytest
from bridge.providers import YunoFeedbackBridge, MockBridge

@pytest.mark.asyncio
async def test_request_reevaluation():
    """Yuno再評価リクエストテスト"""
    
    # モックBridge使用
    feedback_bridge = YunoFeedbackBridge(
        api_key="test_key",
        model="gpt-5-preview"
    )
    
    intent_data = {
        "type": "review",
        "data": {"target": "test.py"}
    }
    
    feedback_data = {
        "kana_response": "レビュー完了",
        "processing_time_ms": 2000
    }
    
    # 再評価実行（モック）
    reevaluation = await feedback_bridge.request_reevaluation(
        intent_id="test-intent-id",
        intent_data=intent_data,
        feedback_data=feedback_data
    )
    
    assert reevaluation is not None
    assert "yuno_judgment" in reevaluation
    assert "evaluation_score" in reevaluation
    assert reevaluation["yuno_judgment"] in [
        "approved", "approved_with_notes", 
        "revision_required", "rejected"
    ]

@pytest.mark.asyncio
async def test_save_feedback():
    """フィードバック保存テスト"""
    data_bridge = MockBridge()
    
    # Intent作成
    intent_id = await data_bridge.save_intent(
        intent_type="review",
        data={"target": "test.py"}
    )
    
    # フィードバック保存
    feedback_data = {
        "kana_response": "テスト完了",
        "processing_time_ms": 1500
    }
    
    success = await data_bridge.save_feedback(
        intent_id=intent_id,
        feedback_data=feedback_data
    )
    
    assert success
    
    # 確認
    intent = await data_bridge.get_intent(intent_id)
    assert intent["status"] == "waiting_reevaluation"
    assert intent["feedback"] == feedback_data
```

### 統合テスト（フィードバックループ）

```python
# tests/integration/test_breathing_cycle.py ⭐ NEW

import pytest
from bridge.factory import BridgeFactory
import os

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_breathing_cycle():
    """完全な呼吸サイクルテスト"""
    
    # 実際のBridge使用
    os.environ["DATA_BRIDGE_TYPE"] = "postgresql"
    os.environ["AI_BRIDGE_TYPE"] = "claude"
    os.environ["FEEDBACK_BRIDGE_TYPE"] = "yuno"
    
    data_bridge = BridgeFactory.create_data_bridge()
    ai_bridge = BridgeFactory.create_ai_bridge()
    feedback_bridge = BridgeFactory.create_feedback_bridge()
    
    # Phase 1: Intent作成
    intent_id = await data_bridge.save_intent(
        intent_type="review",
        data={"target": "integration_test.py"},
        source="auto_generated"
    )
    
    # Phase 2: Kana処理
    intent = await data_bridge.get_intent(intent_id)
    kana_response = await ai_bridge.call_ai(f"Review: {intent['data']['target']}")
    
    feedback_data = {
        "kana_response": kana_response,
        "kana_model": "claude-sonnet-4-5-20250929",
        "processing_time_ms": 2000
    }
    
    await data_bridge.save_feedback(intent_id, feedback_data)
    
    # Phase 3: ステータス確認
    updated = await data_bridge.get_intent(intent_id)
    assert updated["status"] == "waiting_reevaluation"
    assert updated["feedback"] is not None
    
    # Phase 4: Yuno再評価
    reevaluation = await feedback_bridge.request_reevaluation(
        intent_id=intent_id,
        intent_data=updated,
        feedback_data=updated["feedback"]
    )
    
    await data_bridge.save_reevaluation(intent_id, reevaluation)
    
    # Phase 5: 最終確認
    final = await data_bridge.get_intent(intent_id)
    assert final["reevaluation"] is not None
    assert final["status"] in ["approved", "rejected"]
    
    print(f"✅ 呼吸サイクル完了: {final['status']}")
```

---

## 📈 メトリクス・監視（更新版）

### 監視指標（追加）

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| Intent保存レイテンシ | < 100ms | AuditLogger |
| AI API呼び出しレイテンシ | < 3s | AuditLogger |
| **Yuno再評価レイテンシ** ⭐ | < 5s | AuditLogger |
| **フィードバックループ完了時間** ⭐ | < 10s | AuditLogger |
| **再評価承認率** ⭐ | > 80% | データ分析 |
| データベース接続プール使用率 | < 80% | PostgreSQLBridge |
| エラー率 | < 1% | 例外ログ |
| ログファイルサイズ | < 100MB/日 | ログローテーション |

### ログ出力例（追加）

```json
// 再評価ログ ⭐ NEW
{
  "timestamp": "2025-11-12T18:35:00.123456",
  "type": "reevaluation",
  "intent_id": "a1b2c3d4-...",
  "yuno_model": "gpt-5-preview",
  "judgment": "approved",
  "evaluation_score": 0.92,
  "criteria": {
    "intent_alignment": 0.95,
    "code_quality": 0.90,
    "test_coverage": 0.88,
    "documentation": 0.95
  },
  "duration_ms": 4567.89,
  "success": true
}
```

---

## 🔒 セキュリティ考慮事項

### 1. API Key管理
- 環境変数での管理
- コードに直接記述しない
- `.env`ファイルは`.gitignore`に追加
- **Yuno（GPT-5）API Keyも同様に管理** ⭐

### 2. ログセキュリティ
- 機密情報（API Key等）をログに記録しない
- ユーザーデータは最小限に
- ログファイルのアクセス権限管理
- **再評価ログには個人情報を含めない** ⭐

### 3. データベースセキュリティ
- SQLインジェクション対策（パラメータ化クエリ）
- 接続プールの適切な管理
- トランザクション分離レベルの設定

---

## 📚 参考資料

### 設計パターン
- **Bridge Pattern**: 抽象化と実装の分離
- **Factory Pattern**: オブジェクト生成の一元化
- **Strategy Pattern**: アルゴリズムの切り替え
- **Observer Pattern**: フィードバックループの実装 ⭐ NEW

### 関連ドキュメント
- `/docs/work_log_20251112.md` - 本日の作業記録
- `/docs/technical_review_response_20251112.md` - 技術レビュー対応
- `/docs/bridge_architecture_evaluation_20251112.md` - Bridgeアーキテクチャ評価
- `/docs/complete_architecture_design.md` - Yunoの完全アーキテクチャ設計 ⭐

---

## 📝 更新履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|-----------|---------|------|
| 2025-11-12 | 1.0.0 | 初版作成 | GitHub Copilot |
| 2025-11-12 | 1.1.0 | Intent Protocol仕様、フィードバックループ設計、Yuno統合設計を追加 | Claude (Kana) |

---

## ✅ 補完内容サマリ

### 追加セクション ⭐
1. **Intent Protocol仕様** - 完全なIntent構造定義
2. **フィードバックループ設計** - 呼吸的連鎖構造の実装詳細
3. **Yuno統合設計** - 思想層との統合パターン
4. **FeedbackBridge** - 新しいBridgeコンポーネント

### 拡張内容 ⭐
- DataBridge: フィードバック・再評価メソッド追加
- アーキテクチャ図: Yuno層を含む完全版
- 移行計画: Phase 0（旧Bridge退役）追加
- テスト戦略: 呼吸サイクルテスト追加
- メトリクス: 再評価関連指標追加

### 設計思想の統合 ⭐
- Yunoの「システムの呼吸」概念を技術的に実現
- 一方向フロー → 双方向フィードバックループへ進化
- 思想層（Yuno）との明確な連携設計

---

**ドキュメント終了**
