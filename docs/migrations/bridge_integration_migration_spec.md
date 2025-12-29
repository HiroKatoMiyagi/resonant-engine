# Bridge統合移行設計書

**作成日**: 2025-12-29  
**作成者**: Kana (Claude Opus 4.5)  
**実行者**: Kiro (Claude Sonnet 4.5)  
**目的**: `bridge/`ディレクトリを`backend/app/`に統合し、標準的なFastAPI構成に変更する

---

## 1. 背景と目的

### 1.1 現状の問題

- `bridge/`と`backend/app/`に機能が分散している
- `bridge/`内で命名規則が混在（層の名前と機能の名前）
- `bridge`という抽象的な名前が分かりにくい
- 2つのAPIレイヤーが存在していた（`bridge/api/`は削除済み）

### 1.2 目的

- 全ての機能を`backend/app/`に統合
- 標準的なFastAPI構成にする
- コードの可読性と保守性を向上

---

## 2. 現状の構造

```
resonant-engine/
├── backend/
│   └── app/
│       ├── main.py              # FastAPIアプリ
│       ├── config.py            # 設定
│       ├── database.py          # DB接続
│       ├── dependencies.py      # DI
│       ├── models/              # Pydanticモデル
│       ├── repositories/        # DBリポジトリ
│       ├── routers/             # APIルーター
│       └── services/            # （空）
│
├── bridge/
│   ├── core/                    # 抽象クラス、共通ロジック
│   │   ├── ai_bridge.py
│   │   ├── audit_logger.py
│   │   ├── bridge_set.py
│   │   ├── concurrency.py
│   │   ├── constants.py
│   │   ├── data_bridge.py
│   │   ├── errors.py
│   │   ├── exceptions.py
│   │   ├── feedback_bridge.py
│   │   ├── reeval_client.py
│   │   ├── clients/
│   │   ├── correction/
│   │   └── models/
│   │
│   ├── providers/               # 具象実装
│   │   ├── ai/                  # Claude/Mock AI
│   │   ├── audit/               # 監査ログ
│   │   ├── data/                # PostgreSQL/Mock Data
│   │   └── feedback/            # Yuno/Mock Feedback
│   │
│   ├── memory/                  # メモリ管理
│   ├── contradiction/           # 矛盾検出
│   ├── semantic_bridge/         # セマンティック抽出
│   ├── realtime/                # WebSocket/SSE
│   ├── dashboard/               # ダッシュボードサービス
│   ├── factory/                 # BridgeFactory
│   ├── alerts/                  # アラート管理
│   ├── metrics/                 # メトリクス収集
│   └── etl/                     # ETL処理
│
├── memory_store/                # メモリストア（独立パッケージ）
├── memory_lifecycle/            # メモリライフサイクル（独立パッケージ）
├── context_assembler/           # コンテキスト組立（独立パッケージ）
├── retrieval/                   # 検索（独立パッケージ）
└── ...
```

---

## 3. 目標の構造

```
resonant-engine/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── dependencies.py      # DI設定（Factory置き換え）
│       │
│       ├── models/              # ドメインモデル
│       │   ├── intent.py
│       │   ├── message.py
│       │   ├── correction.py    # ← bridge/core/models/から移動
│       │   └── ...
│       │
│       ├── repositories/        # DBリポジトリ
│       │   ├── intent_repo.py
│       │   ├── message_repo.py
│       │   └── ...
│       │
│       ├── routers/             # APIエンドポイント（変更なし）
│       │   ├── intents.py
│       │   ├── messages.py
│       │   └── ...
│       │
│       ├── services/            # ビジネスロジック
│       │   ├── __init__.py
│       │   ├── intent/          # Intent処理
│       │   │   ├── __init__.py
│       │   │   ├── service.py   # IntentService
│       │   │   ├── bridge_set.py
│       │   │   └── reeval.py
│       │   │
│       │   ├── memory/          # メモリ管理
│       │   │   ├── __init__.py
│       │   │   ├── service.py
│       │   │   ├── repositories.py
│       │   │   ├── choice_engine.py
│       │   │   └── database.py
│       │   │
│       │   ├── contradiction/   # 矛盾検出
│       │   │   ├── __init__.py
│       │   │   ├── detector.py
│       │   │   └── models.py
│       │   │
│       │   ├── semantic/        # セマンティック抽出
│       │   │   ├── __init__.py
│       │   │   ├── extractor.py
│       │   │   ├── inferencer.py
│       │   │   └── constructor.py
│       │   │
│       │   ├── realtime/        # リアルタイム通信
│       │   │   ├── __init__.py
│       │   │   ├── event_distributor.py
│       │   │   └── websocket_manager.py
│       │   │
│       │   ├── dashboard/       # ダッシュボード
│       │   │   ├── __init__.py
│       │   │   ├── service.py
│       │   │   └── repository.py
│       │   │
│       │   └── shared/          # 共通
│       │       ├── __init__.py
│       │       ├── constants.py
│       │       ├── exceptions.py
│       │       └── errors.py
│       │
│       └── integrations/        # 外部連携
│           ├── __init__.py
│           ├── claude.py        # Claude API
│           ├── openai.py        # OpenAI API
│           ├── audit_logger.py  # 監査ログ
│           └── feedback.py      # Yunoフィードバック
│
├── (bridge/ は削除)
├── memory_store/                # 独立パッケージは維持
├── memory_lifecycle/
├── context_assembler/
└── retrieval/
```

---

## 4. 移行フェーズ

### フェーズ1: 準備（現状維持で構造作成）

**目的**: 新しいディレクトリ構造を作成し、インポートを更新

#### タスク1.1: ディレクトリ作成
```bash
mkdir -p backend/app/services/intent
mkdir -p backend/app/services/memory
mkdir -p backend/app/services/contradiction
mkdir -p backend/app/services/semantic
mkdir -p backend/app/services/realtime
mkdir -p backend/app/services/dashboard
mkdir -p backend/app/services/shared
mkdir -p backend/app/integrations
```

#### タスク1.2: 各ディレクトリに`__init__.py`作成
```python
# backend/app/services/__init__.py
"""Business logic services."""

# backend/app/services/shared/__init__.py
"""Shared utilities and constants."""

# backend/app/integrations/__init__.py
"""External service integrations."""
```

---

### フェーズ2: 共通モジュール移行（shared, integrations）

**目的**: 他のモジュールが依存する共通部分を先に移行

#### タスク2.1: shared移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/core/constants.py` | `backend/app/services/shared/constants.py` |
| `bridge/core/exceptions.py` | `backend/app/services/shared/exceptions.py` |
| `bridge/core/errors.py` | `backend/app/services/shared/errors.py` |

**手順**:
1. ファイルをコピー
2. インポートパスを更新: `from bridge.core.constants` → `from app.services.shared.constants`
3. `__init__.py`でエクスポート

#### タスク2.2: integrations移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/providers/ai/kana_ai_bridge.py` | `backend/app/integrations/claude.py` |
| `bridge/providers/ai/mock_ai_bridge.py` | `backend/app/integrations/mock_claude.py` |
| `bridge/providers/feedback/yuno_feedback_bridge.py` | `backend/app/integrations/openai.py` |
| `bridge/providers/feedback/mock_feedback_bridge.py` | `backend/app/integrations/mock_openai.py` |
| `bridge/core/audit_logger.py` + `bridge/providers/audit/` | `backend/app/integrations/audit_logger.py` |

**手順**:
1. ファイルをコピー
2. クラス名を明確化（例: `KanaAIBridge` → `ClaudeClient`）
3. インポートパスを更新

---

### フェーズ3: サービス移行（機能別）

#### タスク3.1: contradiction移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/contradiction/detector.py` | `backend/app/services/contradiction/detector.py` |
| `bridge/contradiction/models.py` | `backend/app/services/contradiction/models.py` |
| `bridge/contradiction/api_schemas.py` | `backend/app/models/contradiction.py`に統合 |
| `bridge/contradiction/api_router.py` | 削除（既にrouters/contradictions.pyがある）|

**手順**:
1. ファイルをコピー
2. インポートパスを更新
3. `backend/app/routers/contradictions.py`のインポートを更新:
   ```python
   # Before
   from bridge.contradiction.detector import ContradictionDetector
   # After
   from app.services.contradiction.detector import ContradictionDetector
   ```

#### タスク3.2: memory移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/memory/database.py` | `backend/app/services/memory/database.py` |
| `bridge/memory/models.py` | `backend/app/services/memory/models.py` |
| `bridge/memory/repositories.py` | `backend/app/services/memory/repositories.py` |
| `bridge/memory/postgres_repositories.py` | `backend/app/services/memory/postgres_repositories.py` |
| `bridge/memory/in_memory_repositories.py` | `backend/app/services/memory/in_memory_repositories.py` |
| `bridge/memory/choice_query_engine.py` | `backend/app/services/memory/choice_engine.py` |
| `bridge/memory/service.py` | `backend/app/services/memory/service.py` |
| `bridge/memory/api_schemas.py` | `backend/app/models/memory.py`に統合 |
| `bridge/memory/api_router.py` | 削除（機能はrouters/に分散済み）|

#### タスク3.3: semantic移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/semantic_bridge/extractor.py` | `backend/app/services/semantic/extractor.py` |
| `bridge/semantic_bridge/inferencer.py` | `backend/app/services/semantic/inferencer.py` |
| `bridge/semantic_bridge/constructor.py` | `backend/app/services/semantic/constructor.py` |
| `bridge/semantic_bridge/api_schemas.py` | `backend/app/models/semantic.py` |

#### タスク3.4: realtime移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/realtime/event_distributor.py` | `backend/app/services/realtime/event_distributor.py` |
| `bridge/realtime/websocket_manager.py` | `backend/app/services/realtime/websocket_manager.py` |
| `bridge/realtime/triggers.py` | `backend/app/services/realtime/triggers.py` |

#### タスク3.5: dashboard移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/dashboard/service.py` | `backend/app/services/dashboard/service.py` |
| `bridge/dashboard/repository.py` | `backend/app/services/dashboard/repository.py` |

#### タスク3.6: intent移行

| 移行元 | 移行先 |
|--------|--------|
| `bridge/core/bridge_set.py` | `backend/app/services/intent/bridge_set.py` |
| `bridge/core/reeval_client.py` | `backend/app/services/intent/reeval.py` |
| `bridge/core/ai_bridge.py` | `backend/app/services/intent/ai_bridge.py`（抽象クラス）|
| `bridge/core/data_bridge.py` | `backend/app/services/intent/data_bridge.py`（抽象クラス）|
| `bridge/core/feedback_bridge.py` | `backend/app/services/intent/feedback_bridge.py`（抽象クラス）|
| `bridge/core/concurrency.py` | `backend/app/services/intent/concurrency.py` |
| `bridge/core/models/` | `backend/app/models/`に統合 |
| `bridge/core/correction/` | `backend/app/services/intent/correction/` |
| `bridge/core/clients/` | 削除（reeval_clientに統合済み）|

---

### フェーズ4: Factory削除とDI移行

**目的**: `bridge/factory/`を削除し、`dependencies.py`でDI管理

#### タスク4.1: dependencies.py更新

```python
# backend/app/dependencies.py
from functools import lru_cache
from app.services.contradiction.detector import ContradictionDetector
from app.services.dashboard.service import DashboardService
from app.services.dashboard.repository import PostgresDashboardRepository
from app.integrations.claude import ClaudeClient
from app.integrations.openai import OpenAIClient
from app.integrations.audit_logger import AuditLogger

@lru_cache
def get_contradiction_detector() -> ContradictionDetector:
    return ContradictionDetector()

@lru_cache
def get_dashboard_service() -> DashboardService:
    repo = PostgresDashboardRepository()
    return DashboardService(repo)

@lru_cache
def get_claude_client() -> ClaudeClient:
    return ClaudeClient()

@lru_cache
def get_openai_client() -> OpenAIClient:
    return OpenAIClient()

@lru_cache
def get_audit_logger() -> AuditLogger:
    return AuditLogger()
```

#### タスク4.2: BridgeFactory削除

`bridge/factory/`を削除し、全ての参照を`dependencies.py`経由に変更

---

### フェーズ5: 不要ファイル削除

#### タスク5.1: bridge/内の不要ファイル削除

- `bridge/alerts/` → 使用状況を確認して削除または移行
- `bridge/metrics/` → 使用状況を確認して削除または移行
- `bridge/etl/` → 使用状況を確認して削除または移行
- `bridge/data/` → `migrations/`に移動
- `bridge/daemon_config.json` → 必要なら`config/`に移動
- `bridge/intent_protocol.json` → 必要なら`config/`に移動
- `bridge/setup.py` → 削除

#### タスク5.2: bridge/ディレクトリ削除

全ての移行完了後:
```bash
rm -rf bridge/
```

---

### フェーズ6: Dockerfile更新

#### タスク6.1: backend/Dockerfile更新

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 独立パッケージをコピー（bridgeは不要になる）
COPY memory_store/ ./memory_store/
COPY memory_lifecycle/ ./memory_lifecycle/
COPY context_assembler/ ./context_assembler/
COPY retrieval/ ./retrieval/

# 依存関係インストール
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 独立パッケージインストール
RUN pip install -e ./memory_store && \
    pip install -e ./memory_lifecycle

# アプリケーションコピー
COPY backend/app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### フェーズ7: テスト更新

#### タスク7.1: テストのインポート更新

`tests/`内の全ファイルで:
```python
# Before
from bridge.xxx import YYY
# After
from app.services.xxx import YYY
# or
from app.integrations.xxx import YYY
```

#### タスク7.2: テスト実行

```bash
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate
pytest tests/ -v --tb=short
```

---

## 5. 各フェーズの完了条件

| フェーズ | 完了条件 |
|---------|---------|
| フェーズ1 | ディレクトリ構造が作成されている |
| フェーズ2 | `shared/`, `integrations/`が動作する |
| フェーズ3 | 全サービスが移行され、APIが動作する |
| フェーズ4 | `bridge/factory/`が削除されている |
| フェーズ5 | `bridge/`ディレクトリが削除されている |
| フェーズ6 | Dockerビルドが成功する |
| フェーズ7 | テストが80%以上パスする |

---

## 6. 動作確認手順

### 6.1 各フェーズ後の確認

```bash
# API動作確認
curl http://localhost:8000/health
curl http://localhost:8000/api/messages
curl http://localhost:8000/api/intents

# フロントエンド確認
# http://localhost:3000 でメッセージが表示されること
```

### 6.2 最終確認

```bash
# Dockerビルド
cd docker
docker compose up -d --build backend

# テスト
docker exec resonant_backend pytest tests/system/ -v

# 全エンドポイント確認
curl http://localhost:8000/api/messages
curl http://localhost:8000/api/intents
curl http://localhost:8000/api/specifications
curl http://localhost:8000/api/notifications
curl http://localhost:8000/api/v1/contradiction/pending?user_id=test
```

---

## 7. ロールバック手順

問題が発生した場合:

```bash
# Gitで元に戻す
git checkout -- .
git clean -fd

# Dockerリビルド
cd docker
docker compose up -d --build
```

---

## 8. 注意事項

### 8.1 独立パッケージは維持

以下のパッケージは`backend/app/`に統合しない:
- `memory_store/`
- `memory_lifecycle/`
- `context_assembler/`
- `retrieval/`
- `summarization/`
- `session/`
- `user_profile/`

これらは独立したPythonパッケージとして維持し、`pip install -e`でインストールする。

### 8.2 循環インポートに注意

移行時に循環インポートが発生しやすい。発生した場合:
1. 遅延インポート（関数内import）を使用
2. インターフェース（Protocol）を使用して依存を逆転

### 8.3 段階的に進める

一度に全てを移行せず、フェーズごとに動作確認を行う。

---

## 9. 推定工数

| フェーズ | 推定時間 |
|---------|---------|
| フェーズ1 | 30分 |
| フェーズ2 | 2時間 |
| フェーズ3 | 4時間 |
| フェーズ4 | 1時間 |
| フェーズ5 | 30分 |
| フェーズ6 | 1時間 |
| フェーズ7 | 2時間 |
| **合計** | **約11時間** |

---

## 10. 実行指示（Kiro向け）

### 実行順序

1. **フェーズ1から順番に実行**
2. **各フェーズ完了後に動作確認**
3. **問題があれば報告して停止**

### コンテキスト制限対策

- 1フェーズずつ実行
- 大量のファイル変更は分割
- 不要なファイル内容は出力しない

### 報告形式

各フェーズ完了時:
```
## フェーズX完了

### 実行内容
- ファイルA: 移動
- ファイルB: インポート更新

### 動作確認
- curl http://localhost:8000/health → OK
- curl http://localhost:8000/api/messages → OK

### 次のアクション
フェーズX+1に進みます
```

---

**設計書作成完了**

この設計書に従ってKiroが移行を実行してください。
