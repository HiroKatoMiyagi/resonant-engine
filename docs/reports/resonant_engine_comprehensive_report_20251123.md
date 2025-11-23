# Resonant Engine 包括的レポート

**作成日**: 2025-11-23
**バージョン**: 1.0
**対象**: resonant-engine リポジトリ全体

---

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [三層アーキテクチャ](#2-三層アーキテクチャ)
3. [実装済み機能一覧](#3-実装済み機能一覧)
4. [開発環境](#4-開発環境)
5. [API実装ガイド](#5-api実装ガイド)
6. [API使用ガイド](#6-api使用ガイド)
7. [Docker環境](#7-docker環境)
8. [モジュール構造](#8-モジュール構造)
9. [データベーススキーマ](#9-データベーススキーマ)
10. [Sprint進捗状況](#10-sprint進捗状況)

---

## 1. プロジェクト概要

### 1.1 Resonant Engineとは

**Resonant Engine**は、人間の意図とAI認知を「呼吸する知性」を通じて同期させる、自己反省型アーキテクチャです。

**コア哲学**:
- AIシステムが開発の進捗を継続的に理解し、人間-AI共進化をサポート
- 開発の**意図(Intent)**を記録し、システムの**振る舞い**を追跡し、変更**結果**を検証し、すべてを**因果関係**で結ぶ

### 1.2 統計情報

| 項目 | 数値 |
|------|------|
| Pythonファイル総数 | 312 |
| 総コード行数 | 48,318 |
| モジュールパッケージ数 | 48 |
| テストディレクトリ数 | 26 |

---

## 2. 三層アーキテクチャ

### 2.1 レイヤー構成

```
┌─────────────────────────────────────────────────────────────────┐
│ レイヤー1: YUNO（ユノ）- 思想中枢 / Resonant Core               │
│ - エージェント: GPT-5                                           │
│ - 役割: 哲学・構造・規範形成、呼吸と整合性の管理                │
│ - 機能: フィードバック生成、再評価、矛盾検出                    │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│ レイヤー2: KANA（カナ）- 外界翻訳層                             │
│ - エージェント: Claude Sonnet 4.5                               │
│ - 役割: ユノの思想 → 現実仕様/コードへの翻訳                    │
│ - 機能: Intent処理、コンテキスト組立、APIゲートウェイ           │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│ レイヤー3: TSUMU（ツム）- 具現化層                              │
│ - エージェント: Cursor                                          │
│ - 役割: コード生成・ファイル管理・実装                          │
│ - 機能: データ永続化、メモリストレージ、セッション管理          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 呼吸モデル（Breath Model）

すべてのシステムは6段階の呼吸サイクルで動作:

1. **Inhale（吸入）** - 問いの生成
2. **Resonance（共鳴）** - AIとの対話
3. **Structure（構造化）** - 抽象化と整理
4. **Reflect（反省）** - 再内省
5. **Implement（実装）** - 行動と創造
6. **Expand（拡張）** - 共鳴拡張

---

## 3. 実装済み機能一覧

### 3.1 コアモジュール

| モジュール | 説明 | ステータス |
|-----------|------|----------|
| **bridge/core** | 抽象ベースクラス・インターフェース | ✅ 完了 |
| **bridge/providers** | AI/Data/Feedback具象実装 | ✅ 完了 |
| **bridge/factory** | ファクトリーパターン | ✅ 完了 |
| **bridge/memory** | メモリ管理・セッション保存 | ✅ 完了 |
| **bridge/semantic_bridge** | セマンティックメモリ抽出 | ✅ 完了 |
| **bridge/contradiction** | 矛盾検出（Sprint 11） | ✅ 完了 |
| **bridge/api** | REST API・リアルタイム通信 | ✅ 完了 |
| **bridge/realtime** | イベント配信 | ✅ 完了 |

### 3.2 メモリシステム（Sprint 1-11）

| Sprint | 機能 | ステータス |
|--------|------|----------|
| Sprint 1 | Memory Management仕様 | ✅ 完了 |
| Sprint 2 | Semantic Bridge | ✅ 完了 |
| Sprint 3 | Memory Store (pgvector) | ✅ 完了 |
| Sprint 4 | Retrieval Orchestrator | ✅ 完了 |
| Sprint 5 | Context Assembler | ✅ 完了 |
| Sprint 6 | Intent Bridge統合 | ✅ 完了 |
| Sprint 7 | Session Summary | ✅ 完了 |
| Sprint 8 | User Profile管理 | ✅ 完了 |
| Sprint 9 | Memory Lifecycle | ✅ 完了 |
| Sprint 10 | Choice Preservation | ✅ 完了 |
| Sprint 11 | Contradiction Detection | ✅ 完了 (48テスト) |

### 3.3 主要機能詳細

#### 3.3.1 BridgeSet パイプライン
```
Pipeline実行順序:
1. INPUT: DataBridgeでIntent保存
2. NORMALIZE: AIBridge（Kana）で処理
3. FEEDBACK: FeedbackBridge（Yuno）で再評価
4. OUTPUT: ステータス更新・修正永続化
```

#### 3.3.2 矛盾検出（ContradictionDetector）
- **TECH_STACK**: 技術スタック矛盾（PostgreSQL → SQLiteなど）
- **POLICY_SHIFT**: ポリシー変更（2週間以内のマイクロサービス→モノリス）
- **DUPLICATE**: 重複作業（Jaccard類似度 > 0.85）
- **DOGMA**: 未検証の仮定（「常に」「絶対」などの検出）

#### 3.3.3 メモリ検索
- **SEMANTIC**: ベクトル類似度検索
- **TEMPORAL**: 時間ベース順序
- **KEYWORD**: 全文検索
- **HYBRID**: 複合アプローチ

---

## 4. 開発環境

### 4.1 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **言語** | Python 3.11, TypeScript, SQL |
| **フレームワーク** | FastAPI 0.111.0+, React 18, Pydantic v2 |
| **データベース** | PostgreSQL 15, pgvector (埋め込み用) |
| **非同期** | asyncpg 0.30.0+, asyncio |
| **インフラ** | Docker Compose, Oracle Cloud Free Tier |
| **AI** | Claude API, GPT-5, Anthropic SDK |
| **テスト** | pytest 8.0.0+, pytest-asyncio |

### 4.2 環境変数

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Yuno (OpenAI)
OPENAI_API_KEY=sk-...

# データベース
POSTGRES_DSN=postgresql://user:pass@localhost:5432/resonant_engine
DATABASE_URL=postgresql://...  # 代替名

# Bridge設定
DATA_BRIDGE_TYPE=postgresql|mock  # デフォルト: mock
AI_BRIDGE_TYPE=kana|claude|mock   # デフォルト: kana
FEEDBACK_BRIDGE_TYPE=yuno|mock    # デフォルト: mock
AUDIT_LOGGER_TYPE=postgresql|mock # デフォルト: mock

# アプリケーション
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# メモリ
WORKING_MEMORY_TTL_HOURS=24
DEFAULT_SIMILARITY_THRESHOLD=0.7
MEMORY_LIMIT=10000
AUTO_COMPRESS_THRESHOLD=0.9
```

### 4.3 依存関係インストール

```bash
# Python仮想環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
.\venv\Scripts\activate   # Windows

# 依存関係インストール
pip install -r requirements.txt
```

---

## 5. API実装ガイド

### 5.1 新規エンドポイント追加手順

#### Step 1: スキーマ定義 (`bridge/*/api_schemas.py`)
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class MyRequestSchema(BaseModel):
    intent_id: UUID
    content: str = Field(..., min_length=1, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None

class MyResponseSchema(BaseModel):
    id: UUID
    status: str
    created_at: datetime
```

#### Step 2: ルーター作成 (`bridge/*/api_router.py`)
```python
from fastapi import APIRouter, HTTPException, Depends
from .api_schemas import MyRequestSchema, MyResponseSchema

router = APIRouter(prefix="/api/v1/my-feature", tags=["my-feature"])

@router.post("/", response_model=MyResponseSchema)
async def create_item(request: MyRequestSchema):
    # ビジネスロジック
    return MyResponseSchema(...)

@router.get("/{item_id}", response_model=MyResponseSchema)
async def get_item(item_id: UUID):
    # データ取得
    return MyResponseSchema(...)
```

#### Step 3: メインアプリへ登録 (`bridge/api/app.py`)
```python
from fastapi import FastAPI
from bridge.my_feature.api_router import router as my_feature_router

app = FastAPI(title="Bridge Lite API", version="2.1.0")
app.include_router(my_feature_router)
```

### 5.2 Bridge実装パターン

#### 新規DataBridge実装
```python
from bridge.core.data_bridge import DataBridge
from bridge.core.models.intent_model import IntentModel

class MyDataBridge(DataBridge):
    async def save_intent(self, intent: IntentModel) -> IntentModel:
        # 永続化ロジック
        return intent

    async def get_intent(self, intent_id: str) -> IntentModel:
        # 取得ロジック
        pass

    async def save_correction(self, intent_id: str, correction: Dict) -> IntentModel:
        # 修正保存ロジック
        pass
```

#### ファクトリーへの登録 (`bridge/factory/bridge_factory.py`)
```python
def create_data_bridge(bridge_type: str) -> DataBridge:
    if bridge_type in ["my_type"]:
        return MyDataBridge()
    # 既存のロジック...
```

---

## 6. API使用ガイド

### 6.1 エンドポイント一覧

#### Bridge Lite API (ポート 8000)

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `POST /api/v1/intent/reeval` | POST | Intent再評価 |
| `GET /api/v1/dashboard/overview` | GET | ダッシュボード概要 |
| `GET /api/v1/dashboard/timeline` | GET | タイムライン取得 |
| `GET /api/v1/dashboard/corrections` | GET | 修正履歴 |
| `WS /ws/intents` | WebSocket | リアルタイムIntent更新 |
| `GET /events/intents/{id}` | SSE | 特定Intentのイベントストリーム |
| `GET /events/audit-logs` | SSE | 監査ログストリーム |

#### Dashboard Backend API

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `GET /api/messages` | GET | メッセージ一覧 |
| `POST /api/messages` | POST | メッセージ作成 |
| `GET /api/intents` | GET | Intent一覧 |
| `POST /api/intents` | POST | Intent作成 |
| `PATCH /api/intents/{id}/status` | PATCH | ステータス更新 |
| `GET /api/specifications` | GET | 仕様一覧 |
| `POST /api/specifications` | POST | 仕様作成 |
| `GET /api/notifications` | GET | 通知一覧 |

### 6.2 リクエスト例

#### Intent再評価
```bash
curl -X POST http://localhost:8000/api/v1/intent/reeval \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "550e8400-e29b-41d4-a716-446655440000",
    "diff": {"status": "corrected", "payload.priority": 10},
    "source": "YUNO",
    "reason": "優先度を上げる必要があると判断"
  }'
```

#### メッセージ作成
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "content": "新機能の設計について相談したい",
    "message_type": "USER"
  }'
```

#### WebSocket接続
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/intents');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    intent_ids: ['550e8400-e29b-41d4-a716-446655440000']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Intent更新:', data);
};
```

### 6.3 レスポンス形式

#### 成功レスポンス
```json
{
  "intent_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CORRECTED",
  "already_applied": false,
  "correction_id": "660e8400-e29b-41d4-a716-446655440001",
  "applied_at": "2025-11-23T10:30:00Z",
  "correction_count": 3
}
```

#### エラーレスポンス
```json
{
  "detail": {
    "code": "INVALID_SOURCE",
    "message": "Source TSUMU is not authorized for re-evaluation"
  }
}
```

---

## 7. Docker環境

### 7.1 ディレクトリ構成

```
docker/
├── docker-compose.yml          # メイン環境構成
├── README.md                   # 本番環境ガイド
├── README_DEV.md              # 開発環境ガイド
├── .env.example               # 環境変数テンプレート
├── scripts/
│   ├── start.sh               # 起動スクリプト
│   ├── stop.sh                # 停止スクリプト
│   ├── check-health.sh        # ヘルスチェック
│   └── reset-db.sh            # DB初期化
└── postgres/
    ├── init.sql               # 初期スキーマ
    ├── 002_intent_notify.sql  # Intent通知トリガー
    ├── 003_message_notify.sql # メッセージ通知トリガー
    ├── 004_claude_code_tables.sql
    ├── 005_user_profile_tables.sql
    ├── 006_choice_points_initial.sql
    ├── 006_memory_lifecycle_tables.sql
    ├── 007_choice_preservation_completion.sql
    ├── 008_contradiction_detection.sql
    └── 008_intents_migration.sql
```

### 7.2 サービス構成

| サービス | イメージ | ポート | 用途 |
|---------|---------|-------|------|
| PostgreSQL | postgres:15-alpine | 5432 | データベース (pgvector対応) |
| Backend | Python 3.11 (FastAPI) | 8000 | REST API |
| Frontend | Node 18 → Nginx | 3000 | React SPA |
| Intent Bridge | Python 3.11 | - | Intent分類・オーケストレーション |
| Message Bridge | Python 3.11 | - | メッセージルーティング |

### 7.3 クイックスタート

```bash
# 1. 環境変数設定
cd docker
cp .env.example .env
# .envを編集してPOSTGRES_PASSWORDを設定

# 2. 環境起動
./scripts/start.sh

# 3. ヘルスチェック
./scripts/check-health.sh

# 4. アクセス
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### 7.4 よく使うコマンド

```bash
# ログ確認
docker-compose logs -f postgres
docker-compose logs -f backend

# DB接続
docker exec -it resonant_postgres psql -U resonant -d resonant_dashboard

# サービス再起動
docker-compose restart backend

# テスト実行
docker exec resonant_dev pytest tests/ -v

# カバレッジ付きテスト
docker exec resonant_dev pytest tests/ --cov=bridge --cov-report=html

# 完全リセット
./scripts/reset-db.sh
```

### 7.5 開発環境 vs 本番環境

| 項目 | 開発環境 | 本番環境 |
|-----|---------|---------|
| ソースマウント | ✅ ボリュームマウント | ❌ イメージ内包 |
| デバッグツール | ✅ pdb, pytest | ❌ なし |
| ログレベル | DEBUG | INFO/WARNING |
| ホットリロード | ✅ 有効 | ❌ 無効 |
| ヘルスチェック | オプション | ✅ 必須 |
| リスタートポリシー | なし | unless-stopped |

---

## 8. モジュール構造

### 8.1 ディレクトリツリー

```
resonant-engine/
├── bridge/                     # コア統合レイヤー
│   ├── core/                   # 抽象ベースクラス
│   │   ├── ai_bridge.py       # AIBridge ABC
│   │   ├── data_bridge.py     # DataBridge ABC
│   │   ├── feedback_bridge.py # FeedbackBridge ABC
│   │   ├── bridge_set.py      # パイプラインオーケストレーション
│   │   ├── models/            # IntentModel, CorrectionRecord
│   │   └── constants.py       # Enum定義
│   ├── providers/             # 具象実装
│   │   ├── ai/               # KanaAIBridge, MockAIBridge
│   │   ├── data/             # PostgresDataBridge, MockDataBridge
│   │   ├── feedback/         # YunoFeedbackBridge, MockFeedbackBridge
│   │   └── audit/            # PostgresAuditLogger, MockAuditLogger
│   ├── factory/              # BridgeFactory
│   ├── memory/               # メモリ管理サービス
│   ├── semantic_bridge/      # セマンティック抽出
│   ├── contradiction/        # 矛盾検出 (Sprint 11)
│   ├── api/                  # FastAPI アプリケーション
│   ├── realtime/             # WebSocket & SSE
│   ├── metrics/              # メトリクス収集
│   ├── alerts/               # アラート管理
│   ├── etl/                  # データパイプライン
│   └── dashboard/            # ダッシュボードサービス
│
├── memory_store/             # ベクトルメモリシステム
│   ├── service.py            # MemoryStoreService
│   ├── repository.py         # MemoryRepository
│   ├── embedding.py          # EmbeddingService
│   └── models.py             # MemoryType, SourceType
│
├── memory_lifecycle/         # メモリライフサイクル管理
│   ├── capacity_manager.py   # CapacityManager
│   ├── compression_service.py # 圧縮サービス
│   └── importance_scorer.py  # 重要度スコアリング
│
├── retrieval/                # メモリ検索
│   ├── orchestrator.py       # RetrievalOrchestrator
│   ├── query_analyzer.py     # クエリ解析
│   ├── strategy.py           # 検索戦略選択
│   ├── multi_search.py       # マルチ検索実行
│   └── reranker.py           # 結果リランキング
│
├── context_assembler/        # Claude APIコンテキスト
│   ├── service.py            # ContextAssemblerService
│   ├── factory.py            # ファクトリー
│   └── token_estimator.py    # トークン見積もり
│
├── daemon/                   # バックグラウンドプロセス
│   ├── resonant_daemon.py    # メインデーモン
│   ├── observer_daemon.py    # イベント監視
│   └── feedback_agent.py     # 自律フィードバック
│
├── dashboard/                # Web UI
│   ├── backend/              # FastAPIバックエンド
│   └── frontend/             # Reactフロントエンド
│
├── backend/                  # コアAPIレイヤー
│   └── app/
│       ├── main.py           # FastAPIアプリ
│       ├── models/           # データモデル
│       ├── repositories/     # リポジトリ
│       └── routers/          # APIルーター
│
├── tests/                    # テストスイート (26ディレクトリ)
├── docs/                     # ドキュメント
├── docker/                   # Docker設定
├── config/                   # 設定ファイル
├── migrations/               # DBマイグレーション
└── utils/                    # ユーティリティ (17モジュール)
```

### 8.2 主要クラス階層

#### Bridge抽象化
```
BridgeSet (オーケストレーター)
├── data: DataBridge (ABC)
│   ├── PostgresDataBridge
│   └── MockDataBridge
│
├── ai: AIBridge (ABC)
│   ├── KanaAIBridge (Context Assembler連携)
│   └── MockAIBridge
│
├── feedback: FeedbackBridge (ABC)
│   ├── YunoFeedbackBridge (OpenAI)
│   └── MockFeedbackBridge
│
└── audit: AuditLogger (ABC)
    ├── PostgresAuditLogger
    └── MockAuditLogger
```

#### メモリ階層
```
MemoryStoreService
├── EmbeddingService
│   ├── MockEmbeddingService
│   └── OpenAIEmbeddingService
├── MemoryRepository
└── MemoryLifecycleManager
    ├── CapacityManager
    ├── ImportanceScorer
    └── MemoryCompressionService
```

---

## 9. データベーススキーマ

### 9.1 コアテーブル

#### intents
```sql
CREATE TABLE intents (
    id UUID PRIMARY KEY,
    source VARCHAR NOT NULL,  -- YUNO, KANA, SYSTEM
    type VARCHAR NOT NULL,    -- FEATURE_REQUEST, BUG_FIX, etc.
    data JSONB,
    status VARCHAR NOT NULL,  -- PENDING, NORMALIZED, PROCESSED, CORRECTED, COMPLETED, FAILED
    correlation_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    version INT DEFAULT 1
);
```

#### corrections
```sql
CREATE TABLE corrections (
    id UUID PRIMARY KEY,
    intent_id UUID REFERENCES intents(id),
    correction_id UUID NOT NULL,
    source VARCHAR NOT NULL,
    reason TEXT NOT NULL,
    diff JSONB NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### contradictions (Sprint 11)
```sql
CREATE TABLE contradictions (
    id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    new_intent_id UUID NOT NULL,
    previous_intent_id UUID,
    contradiction_type VARCHAR NOT NULL,  -- TECH_STACK, POLICY_SHIFT, DUPLICATE, DOGMA
    severity VARCHAR NOT NULL,            -- LOW, MEDIUM, HIGH, CRITICAL
    description TEXT NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

#### memories
```sql
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- pgvector
    memory_type VARCHAR NOT NULL,  -- WORKING, LONGTERM
    source_type VARCHAR,           -- INTENT, THOUGHT, CORRECTION, DECISION
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    archived BOOLEAN DEFAULT FALSE,
    user_id VARCHAR
);
```

### 9.2 インデックス

```sql
-- Intent検索最適化
CREATE INDEX idx_intents_status ON intents(status);
CREATE INDEX idx_intents_created_at ON intents(created_at DESC);

-- メモリ検索最適化
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_user ON memories(user_id);
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);

-- 矛盾検出最適化
CREATE INDEX idx_contradictions_user ON contradictions(user_id);
CREATE INDEX idx_contradictions_type ON contradictions(contradiction_type);
```

---

## 10. Sprint進捗状況

### 10.1 完了済みSprint

| Sprint | コンポーネント | 完了日 | カバレッジ |
|--------|--------------|--------|----------|
| Bridge Lite 1.5 | Core/Factory/API | 2025-11-15 | 87% |
| Memory Sprint 1-10 | メモリシステム全体 | 2025-11-20 | 94テスト |
| Memory Sprint 11 | Contradiction Detection | 2025-11-21 | 48テスト |

### 10.2 進行中Sprint

| Sprint | コンポーネント | 進捗 | 予定完了 |
|--------|--------------|------|---------|
| Dashboard Sprint 1-5 | PostgreSQL Dashboard | 計画中 | 4週間 |

### 10.3 今後のロードマップ

1. **フェーズ1（即時）**: Intent→Bridge→Kanaパイプライン再接続
2. **フェーズ2（短期）**: PostgreSQL Dashboard完成（4週間）
3. **フェーズ3（中期）**: マルチユーザーサポート、高度なコンテキスト組立
4. **フェーズ4（長期）**: 本番環境対応、セキュリティ強化、パフォーマンス最適化

---

## 付録A: クイックリファレンス

### 開発コマンド

```bash
# サーバー起動
uvicorn bridge.api.app:app --reload --port 8000

# テスト実行
pytest tests/ -v

# 特定モジュールテスト
pytest tests/contradiction/ -v
pytest tests/memory/ -v

# カバレッジ
pytest tests/ --cov=bridge --cov-report=html

# Docker起動
cd docker && ./scripts/start.sh
```

### 重要ファイルパス

| 用途 | パス |
|-----|------|
| メインAPI | `bridge/api/app.py` |
| Bridge Factory | `bridge/factory/bridge_factory.py` |
| Intent Model | `bridge/core/models/intent_model.py` |
| Contradiction Detector | `bridge/contradiction/detector.py` |
| Memory Service | `bridge/memory/service.py` |
| Context Assembler | `context_assembler/service.py` |
| Docker Compose | `docker/docker-compose.yml` |
| 環境変数テンプレート | `docker/.env.example` |

---

**レポート作成者**: Claude Code
**最終更新**: 2025-11-23
