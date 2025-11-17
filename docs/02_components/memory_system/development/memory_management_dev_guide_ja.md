# Memory Management System - 開発者ガイド

**バージョン**: 1.0.0
**作成日**: 2025-11-17
**作成者**: Sonnet 4.5 (Claude Code Implementation)

## 概要

本ガイドは、Memory Management System を開発する開発者向けの技術詳細を提供します。アーキテクチャ、実装パターン、拡張ガイドラインをカバーします。

## アーキテクチャ

### システム層

```
┌─────────────────────────────────────┐
│          REST API 層                │
│  (FastAPI Router + Schemas)         │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         サービス層                  │
│  (MemoryManagementService)          │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│       リポジトリ層                  │
│  (抽象 + 実装)                      │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         データ層                    │
│  (Pydantic Models + SQLAlchemy)     │
└─────────────────────────────────────┘
```

## ファイル構造

```
bridge/memory/
├── __init__.py                    # パッケージエクスポート
├── models.py                      # Pydantic データモデル
├── database.py                    # SQLAlchemy ORM モデル
├── repositories.py                # 抽象リポジトリインターフェース
├── in_memory_repositories.py      # インメモリ実装
├── service.py                     # ビジネスロジックサービス
├── api_schemas.py                 # API リクエスト/レスポンススキーマ
└── api_router.py                  # FastAPI エンドポイント

tests/memory/
├── __init__.py
├── test_models.py                 # モデルユニットテスト
└── test_service.py                # サービスユニットテスト
```

## データモデル

### コアモデル

すべてのモデルは Pydantic BaseModel を継承し、以下を提供:
- UUID 自動生成
- タイムゾーン対応タイムスタンプ
- JSON シリアライズ
- フィールドバリデーション

例:
```python
from bridge.memory.models import Intent, IntentType

intent = Intent(
    session_id=session_id,
    intent_text="メモリシステム設計",
    intent_type=IntentType.FEATURE_REQUEST,
    priority=8,
)
```

### モデル階層

- **Session**: 呼吸ユニットコンテナ
  - **Intent**: ユーザー意図（階層構造）
    - **ChoicePoint**: 決定ポイント
    - **Resonance**: 状態記録
    - **BreathingCycle**: フェーズ追跡
  - **AgentContext**: エージェントごとの状態（バージョン管理）
  - **Snapshot**: 時間的保存

## リポジトリパターン

### 抽象インターフェース

```python
from bridge.memory.repositories import IntentRepository

class CustomIntentRepository(IntentRepository):
    async def create(self, intent: Intent) -> Intent:
        # 実装
        pass

    async def get_by_id(self, intent_id: UUID) -> Optional[Intent]:
        # 実装
        pass
```

### 利用可能なリポジトリ

1. **SessionRepository** - セッションライフサイクル
2. **IntentRepository** - Intent CRUD + 検索
3. **ResonanceRepository** - 共鳴パターン
4. **AgentContextRepository** - バージョン管理されたコンテキスト
5. **ChoicePointRepository** - 決定管理
6. **BreathingCycleRepository** - フェーズ追跡
7. **SnapshotRepository** - 時間的保存

### インメモリ実装

テストと開発用:
```python
from bridge.memory.in_memory_repositories import (
    InMemorySessionRepository,
    InMemoryIntentRepository,
)

repo = InMemorySessionRepository()
session = await repo.create(Session(user_id="test"))
```

## サービス層

### MemoryManagementService

すべてのリポジトリを調整する中央サービス:

```python
from bridge.memory.service import MemoryManagementService
from bridge.memory.in_memory_repositories import *

service = MemoryManagementService(
    session_repo=InMemorySessionRepository(),
    intent_repo=InMemoryIntentRepository(),
    resonance_repo=InMemoryResonanceRepository(),
    agent_context_repo=InMemoryAgentContextRepository(),
    choice_point_repo=InMemoryChoicePointRepository(),
    breathing_cycle_repo=InMemoryBreathingCycleRepository(),
    snapshot_repo=InMemorySnapshotRepository(),
)
```

### 主要操作

#### セッション管理
```python
# セッション開始
session = await service.start_session("user_id", {"client": "web"})

# ハートビート更新
await service.update_session_heartbeat(session.id)

# 前回セッション継続
data = await service.continue_session(session.id)
```

#### Intent ライフサイクル
```python
# Intent 記録（呼吸フェーズ1）
intent = await service.record_intent(
    session.id,
    "スキーマ設計",
    IntentType.FEATURE_REQUEST,
    priority=8
)

# ステータス更新
await service.update_intent_status(intent.id, IntentStatus.IN_PROGRESS)

# 結果付きで完了
await service.complete_intent(intent.id, {"result": "success"})
```

#### 共鳴記録
```python
# 共鳴記録（呼吸フェーズ2）
resonance = await service.record_resonance(
    session.id,
    ResonanceState.ALIGNED,
    intensity=0.85,
    agents=["yuno", "kana"],
    pattern_type="philosophical_alignment"
)
```

#### 選択管理
```python
# 選択ポイント作成（呼吸フェーズ3）
choice_point = await service.create_choice_point(
    session.id,
    intent.id,
    "PostgreSQL か SQLite か？",
    [
        Choice(id="pg", description="PostgreSQL", implications={}),
        Choice(id="sqlite", description="SQLite", implications={}),
    ]
)

# 決定
await service.decide_choice(choice_point.id, "pg", "スケーラビリティ向上")

# 保留決定の取得
pending = await service.get_pending_choices(session.id)
```

#### エージェントコンテキストバージョニング
```python
# コンテキスト保存（呼吸フェーズ4）
context = await service.save_agent_context(
    session.id,
    AgentType.KANA,
    {"focus": "memory design", "version": 1}
)

# 最新取得
latest = await service.get_latest_agent_context(session.id, AgentType.KANA)

# 全エージェント取得
all_contexts = await service.get_all_agent_contexts(session.id)
```

#### 呼吸サイクル
```python
# フェーズ開始
cycle = await service.start_breathing_phase(
    session.id,
    BreathingPhase.STRUCTURING,
    phase_data={"action": "schema_design"}
)

# フェーズ完了
await service.complete_breathing_phase(
    cycle.id,
    success=True,
    phase_data={"outcome": "completed"}
)
```

#### スナップショット
```python
# スナップショット作成（時間軸保存）
snapshot = await service.create_snapshot(
    session.id,
    SnapshotType.MILESTONE,
    description="スキーマ完成",
    tags=["milestone", "schema"]
)

# データ復元
data = await service.restore_from_snapshot(snapshot.id)
```

## API 層

### 新しいエンドポイントの追加

1. `api_schemas.py` でリクエスト/レスポンススキーマを定義:
```python
class NewFeatureRequest(BaseModel):
    session_id: UUID
    data: Dict[str, Any]

class NewFeatureResponse(BaseModel):
    id: UUID
    status: str
```

2. `api_router.py` でエンドポイントを追加:
```python
@router.post("/new-feature", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    # 実装
    pass
```

## テスト

### テスト実行

```bash
# すべてのメモリテスト
python -m pytest tests/memory/ -v

# 特定のテストファイル
python -m pytest tests/memory/test_models.py -v

# カバレッジ付き
python -m pytest tests/memory/ --cov=bridge/memory --cov-report=html
```

### テスト記述

```python
import pytest
from bridge.memory.service import MemoryManagementService
from bridge.memory.in_memory_repositories import *

@pytest.fixture
def memory_service():
    return MemoryManagementService(
        session_repo=InMemorySessionRepository(),
        intent_repo=InMemoryIntentRepository(),
        # ... 他のリポジトリ
    )

@pytest.mark.asyncio
async def test_new_feature(memory_service):
    session = await memory_service.start_session("test")
    assert session.id is not None
```

## 拡張ガイドライン

### 新しいモデルの追加

1. `models.py` で Pydantic モデルを定義
2. `database.py` で SQLAlchemy モデルを追加
3. 抽象リポジトリインターフェースを作成
4. リポジトリを実装（まずインメモリ）
5. サービスメソッドを追加
6. API エンドポイントを作成
7. テストを書く

### 哲学への準拠

システムを拡張する際、以下の原則を維持してください:

- **時間軸保存**: 削除せず、アーカイブのみ
- **選択の保持**: 未決定の選択肢は利用可能のまま
- **バージョニング**: 変更を追跡し、上書きしない
- **呼吸リズム**: 操作を6フェーズにマッピング

### パフォーマンス考慮事項

- 頻繁なクエリには JSONB インデックスを使用
- リストエンドポイントにページネーションを実装
- 頻繁にアクセスされるデータをキャッシュ
- クエリ実行時間を監視

## デプロイ

### 環境変数

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

### データベースセットアップ

Docker Compose を使用:
```bash
docker-compose up -d db
```

提供されたスクリプトを使用:
```bash
python scripts/setup_docker_db.py
```

### API 実行

```bash
uvicorn bridge.api.app:app --reload --port 8000
```

## 将来の開発

### フェーズ4 - マルチユーザーサポート
- 認証/承認
- ユーザー固有のデータ分離
- 共有セッション機能

### 高度な機能
- PostgreSQL FTS による全文検索
- 埋め込みによるセマンティック検索
- パターン分析と予測
- リアルタイム通知

## 共通パターン

### 階層的 Intent
```python
parent = await service.record_intent(...)
child = await service.record_intent(
    ...,
    parent_intent_id=parent.id
)
```

### セッション継続性
```python
# 一日の終わり
await service.update_session_status(session.id, SessionStatus.PAUSED)

# 翌日
data = await service.continue_session(session.id)
# data にはコンテキスト、保留中の選択、最後の Intent が含まれる
```

### 完全な呼吸サイクル
```python
# 1. 吸う
intake = await service.start_breathing_phase(session_id, BreathingPhase.INTAKE)
intent = await service.record_intent(...)
await service.complete_breathing_phase(intake.id, True)

# 2. 共鳴
resonance_cycle = await service.start_breathing_phase(session_id, BreathingPhase.RESONANCE)
await service.record_resonance(...)
await service.complete_breathing_phase(resonance_cycle.id, True)

# 全6フェーズを継続...
```

## トラブルシューティング

### よくある問題

1. **インポートエラー**: pydantic と他の依存関係がインストールされていることを確認
2. **非同期の問題**: 非同期テストには `@pytest.mark.asyncio` を使用
3. **UUID バリデーション**: 文字列ではなく適切な UUID 型を使用
4. **日時タイムゾーン**: 常にタイムゾーン対応の日時を使用

### デバッグツール

```python
# 検査用 JSON ダンプ
print(model.model_dump(mode="json"))

# モデルバリデーションチェック
from pydantic import ValidationError
try:
    Model(**data)
except ValidationError as e:
    print(e.errors())
```

## リソース

- Pydantic ドキュメント: https://docs.pydantic.dev/
- FastAPI ドキュメント: https://fastapi.tiangolo.com/
- SQLAlchemy ドキュメント: https://docs.sqlalchemy.org/
- Resonant Engine 哲学: `docs/philosophy/breathing_cycles.md`

## よく使うコマンド

```bash
# 開発サーバー起動
uvicorn bridge.api.app:app --reload

# テスト実行
pytest tests/memory/ -v

# カバレッジレポート生成
pytest tests/memory/ --cov=bridge/memory --cov-report=html

# データベースマイグレーション（将来）
alembic upgrade head

# Linting
ruff check bridge/memory/
black bridge/memory/
```

## ベストプラクティス

### コーディング規約

1. **型ヒント**: すべての関数に型ヒントを付ける
2. **Docstrings**: 公開 API には docstring を記述
3. **エラーハンドリング**: 適切な例外を定義して使用
4. **非同期**: I/O バウンド操作は async/await を使用

### テスト規約

1. **AAA パターン**: Arrange-Act-Assert
2. **フィクスチャ**: 共通セットアップは fixture で
3. **モック**: 外部依存はモック化
4. **命名**: `test_<機能>_<条件>_<期待結果>`

### Git コミット

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント変更
test: テスト追加/修正
refactor: リファクタリング
```

---

**更新日**: 2025-11-17
**メンテナー**: Resonant Engine Team
