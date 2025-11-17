# Memory Management 実装開始指示書
## 呼吸の履歴を刻む永続化層の構築

**作成日**: 2025-11-16  
**発行者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 または Tsumu（Cursor）  
**目的**: 3層AI構造の共鳴状態・意図履歴・選択肢の永続化による時間軸の保全

---

## 0. 重要な前提条件

### PostgreSQL環境の準備状態

**このタスクを開始する前に、PostgreSQL実装が完了している必要があります:**

- [ ] PostgreSQL 15 インストール済み
- [ ] データベース `resonant` 作成済み
- [ ] ユーザー `resonant` 作成済み
- [ ] 接続確認済み（`psql -U resonant -d resonant`）
- [ ] SQLAlchemyまたはAsyncpg動作確認済み
- [ ] マイグレーションツール準備済み（Alembic推奨）

**PostgreSQL未準備の場合:**
このタスクは実施せず、PostgreSQL環境構築を優先してください。

### Bridge Core 安定動作確認

- [ ] Bridge Core基本機能動作確認
- [ ] Intent → Bridge → Kana パイプライン動作
- [ ] エラーハンドリング正常動作
- [ ] ログ出力正常動作

**Bridge Core不安定の場合:**
メモリ管理機能の実装前に、Bridge Coreの安定化を優先してください。

---

## 1. Memory Management 実装承認

### 1.1 実装背景

Resonant Engineの中核原則「時間軸の尊重」「選択の保持」「構造の継続性」を実現するため、3層AI構造の状態と履歴を永続化します。

**哲学的必然性**:
- AIは「意味空間」で動作し「時間空間」を失う
- セッション間で意図が断絶する問題
- 過去の選択肢を再利用できない問題
- 共鳴パターンが失われる問題

**技術的必要性**:
- Intent継続性の保証
- Agent文脈の保存と復元
- 呼吸サイクルのトラッキング
- 選択肢の保持（強制しない）

### 1.2 実装スコープ

**実装するもの**:
- PostgreSQLスキーマ（8テーブル）
- Repository層（CRUD + 検索）
- Service層（ビジネスロジック）
- REST API（10+ endpoints）
- 呼吸サイクル管理
- スナップショット機能
- セッション継続性保証
- テスト（40+ ケース）
- ドキュメント（3種類）

**実装しないもの**:
- ファイルシステムキャッシュ（別システム）
- リアルタイムストリーミング（WebSocket層）
- マルチユーザー認証（Phase 4）
- AI分析機能（将来拡張）

---

## 2. 実装手順

### 2.1 事前準備チェックリスト

実装を開始する前に、以下を確認してください：

#### 環境確認
- [ ] PostgreSQL 15起動中（`pg_ctl status` または `brew services list`）
- [ ] データベース接続確認（`psql -U resonant -d resonant`）
- [ ] Python 3.11+ 仮想環境アクティブ
- [ ] 必要パッケージインストール確認
  ```bash
  pip list | grep -E "(sqlalchemy|asyncpg|alembic|psycopg2|pydantic)"
  ```

#### 仕様理解
- [ ] 仕様書 `memory_management_spec.md` を通読
- [ ] Done Definitionの全項目を理解
- [ ] 8テーブルのER図を理解
- [ ] 呼吸サイクルとメモリの関係を理解
- [ ] 5日間のスケジュールを理解

#### ツール準備
- [ ] DBクライアント準備（psql、DBeaver、TablePlus等）
- [ ] Alembic初期化（マイグレーション管理）
- [ ] pytest環境確認
- [ ] FastAPI環境確認

---

## 3. 実装スケジュール（5日間）

### Day 1 (6時間): データベーススキーマ実装

#### 午前 (3時間): スキーマ設計 & マイグレーション

**タスク1**: Alembic初期化
```bash
cd /Users/zero/Projects/resonant-engine

# Alembic初期化（未実施の場合）
alembic init alembic

# alembic.ini 編集
# sqlalchemy.url = postgresql://resonant:password@localhost:5432/resonant
```

**タスク2**: マイグレーション作成
```bash
# 8テーブルのマイグレーション作成
alembic revision -m "create_memory_management_tables"
```

`alembic/versions/xxx_create_memory_management_tables.py` に以下を実装:

```python
"""create memory management tables

Revision ID: xxx
Create Date: 2025-11-16
"""

def upgrade() -> None:
    # sessions テーブル
    op.create_table(
        'sessions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_active', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('metadata', sa.JSON(), server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('active', 'paused', 'completed', 'archived')", name='valid_status')
    )
    
    op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_last_active', 'sessions', ['last_active'])
    
    # intents テーブル
    # ... （仕様書Section 2.1参照）
    
    # 残り6テーブルも同様に作成
    
def downgrade() -> None:
    # ロールバック処理
    op.drop_table('sessions')
    # ...
```

**タスク3**: マイグレーション実行
```bash
# マイグレーション実行
alembic upgrade head

# 確認
psql -U resonant -d resonant -c "\dt"
# 期待: 8テーブルが表示される
```

**完了基準**:
- [ ] Alembic設定完了
- [ ] マイグレーションファイル作成
- [ ] マイグレーション実行成功
- [ ] 8テーブル作成確認
- [ ] Indexが全て作成されている

#### 午後 (3時間): Pydanticモデル実装

**タスク1**: データモデル実装
```bash
mkdir -p /Users/zero/Projects/resonant-engine/bridge/memory
touch /Users/zero/Projects/resonant-engine/bridge/memory/__init__.py
touch /Users/zero/Projects/resonant-engine/bridge/memory/models.py
```

`bridge/memory/models.py` に以下を実装:
- Session, SessionStatus
- Intent, IntentStatus, IntentType
- Resonance, ResonanceState
- AgentContext, AgentType
- ChoicePoint, Choice
- BreathingCycle, BreathingPhase
- Snapshot, SnapshotType

**タスク2**: バリデーションテスト
```bash
mkdir -p /Users/zero/Projects/resonant-engine/tests/memory
touch /Users/zero/Projects/resonant-engine/tests/memory/__init__.py
touch /Users/zero/Projects/resonant-engine/tests/memory/test_models.py
```

`tests/memory/test_models.py` に以下を実装:
- `test_session_creation`
- `test_intent_hierarchy`
- `test_resonance_intensity_validation`
- `test_agent_context_versioning`
- `test_choice_point_pending_state`
- `test_breathing_phase_enum`
- `test_snapshot_type_enum`
- `test_pydantic_json_serialization`
- `test_uuid_generation`
- `test_datetime_defaults`

**検証**:
```bash
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate
PYTHONPATH=. pytest tests/memory/test_models.py -v

# 期待: 10 passed
```

**完了基準**:
- [ ] Pydanticモデル全実装完了
- [ ] Enum全定義完了
- [ ] バリデーションルール実装完了
- [ ] 単体テスト10件全てPASS

---

### Day 2 (6時間): Repository層実装

#### 午前 (3時間): 基本Repository実装

**タスク1**: Repository抽象クラス
```bash
touch /Users/zero/Projects/resonant-engine/bridge/memory/repositories.py
```

`bridge/memory/repositories.py` に以下を実装:
- `SessionRepository` (ABC)
- `IntentRepository` (ABC)
- `ResonanceRepository` (ABC)

**タスク2**: PostgreSQL実装
```bash
touch /Users/zero/Projects/resonant-engine/bridge/memory/postgres_repositories.py
```

`bridge/memory/postgres_repositories.py` に以下を実装:
- `PostgresSessionRepository`
  - `create(session: Session) -> Session`
  - `get_by_id(session_id: UUID) -> Optional[Session]`
  - `update(session: Session) -> Session`
  - `update_heartbeat(session_id: UUID) -> Session`
  - `list_active(user_id: str) -> List[Session]`

- `PostgresIntentRepository`
  - `create(intent: Intent) -> Intent`
  - `get_by_id(intent_id: UUID) -> Optional[Intent]`
  - `update(intent: Intent) -> Intent`
  - `list_by_session(session_id: UUID, status: Optional[IntentStatus]) -> List[Intent]`
  - `search(session_id: UUID, query: str, limit: int) -> List[Intent]`

- `PostgresResonanceRepository`
  - `create(resonance: Resonance) -> Resonance`
  - `get_by_id(resonance_id: UUID) -> Optional[Resonance]`
  - `list_by_session(session_id: UUID) -> List[Resonance]`
  - `list_by_state(session_id: UUID, state: ResonanceState) -> List[Resonance]`

**タスク3**: Repository単体テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/memory/test_repositories.py
```

テスト実装:
- `test_session_repository_create`
- `test_session_repository_get_by_id`
- `test_session_repository_update_heartbeat`
- `test_intent_repository_create`
- `test_intent_repository_search`
- `test_intent_repository_list_by_status`
- `test_resonance_repository_create`
- `test_resonance_repository_list_by_state`
- `test_repository_transaction_rollback`
- `test_repository_concurrent_access`

**検証**:
```bash
PYTHONPATH=. pytest tests/memory/test_repositories.py -v
# 期待: 10 passed
```

**完了基準**:
- [ ] 基本Repository 3種類実装完了
- [ ] CRUD操作全実装
- [ ] 検索機能実装
- [ ] 単体テスト10件全てPASS

#### 午後 (3時間): 拡張Repository実装

**タスク**: 残り4つのRepository実装

`bridge/memory/postgres_repositories.py` に追加実装:

- `PostgresAgentContextRepository`
  - `create(context: AgentContext) -> AgentContext`
  - `get_by_id(context_id: UUID) -> Optional[AgentContext]`
  - `update(context: AgentContext) -> AgentContext`
  - `get_latest(session_id: UUID, agent_type: AgentType) -> Optional[AgentContext]`
  - `get_all_latest(session_id: UUID) -> List[AgentContext]`

- `PostgresChoicePointRepository`
  - `create(choice_point: ChoicePoint) -> ChoicePoint`
  - `get_by_id(choice_point_id: UUID) -> Optional[ChoicePoint]`
  - `update(choice_point: ChoicePoint) -> ChoicePoint`
  - `list_by_session(session_id: UUID) -> List[ChoicePoint]`
  - `list_pending(session_id: UUID) -> List[ChoicePoint]`

- `PostgresBreathingCycleRepository`
  - `create(cycle: BreathingCycle) -> BreathingCycle`
  - `get_by_id(cycle_id: UUID) -> Optional[BreathingCycle]`
  - `update(cycle: BreathingCycle) -> BreathingCycle`
  - `list_by_session(session_id: UUID) -> List[BreathingCycle]`
  - `list_by_phase(session_id: UUID, phase: BreathingPhase) -> List[BreathingCycle]`

- `PostgresSnapshotRepository`
  - `create(snapshot: Snapshot) -> Snapshot`
  - `get_by_id(snapshot_id: UUID) -> Optional[Snapshot]`
  - `list_by_session(session_id: UUID) -> List[Snapshot]`
  - `list_by_tags(session_id: UUID, tags: List[str]) -> List[Snapshot]`

**テスト追加**:
`tests/memory/test_repositories.py` に追加:
- `test_agent_context_versioning`
- `test_agent_context_get_latest`
- `test_choice_point_pending_list`
- `test_breathing_cycle_by_phase`
- `test_snapshot_by_tags`
- `test_snapshot_jsonb_storage`
- `test_repository_error_handling`
- `test_repository_null_handling`
- `test_repository_cascade_delete`
- `test_repository_foreign_key_constraint`

**検証**:
```bash
PYTHONPATH=. pytest tests/memory/test_repositories.py -v
# 期待: 20 passed (累計)
```

**完了基準**:
- [ ] 拡張Repository 4種類実装完了
- [ ] バージョニング対応（AgentContext）
- [ ] タグ検索対応（Snapshot）
- [ ] 単体テスト20件全てPASS

---

### Day 3 (6時間): Service層実装

#### 午前 (3時間): 基本Service実装

**タスク1**: Serviceクラス作成
```bash
touch /Users/zero/Projects/resonant-engine/bridge/memory/service.py
```

`bridge/memory/service.py` に以下を実装:

```python
class MemoryManagementService:
    def __init__(
        self,
        session_repo: SessionRepository,
        intent_repo: IntentRepository,
        resonance_repo: ResonanceRepository,
        agent_context_repo: AgentContextRepository,
        choice_point_repo: ChoicePointRepository,
        breathing_cycle_repo: BreathingCycleRepository,
        snapshot_repo: SnapshotRepository
    ):
        # Repository注入
        pass
    
    # セッション管理
    async def start_session(self, user_id: str, metadata: Dict = None) -> Session
    async def get_session(self, session_id: UUID) -> Optional[Session]
    async def update_session_heartbeat(self, session_id: UUID) -> Session
    
    # Intent管理
    async def record_intent(
        self,
        session_id: UUID,
        intent_text: str,
        intent_type: IntentType,
        parent_intent_id: Optional[UUID] = None,
        priority: int = 0
    ) -> Intent
    
    async def get_intent(self, intent_id: UUID) -> Optional[Intent]
    async def update_intent_status(self, intent_id: UUID, status: IntentStatus) -> Intent
    async def complete_intent(self, intent_id: UUID, outcome: Dict) -> Intent
    async def search_intents(self, session_id: UUID, query: str) -> List[Intent]
    
    # Resonance管理
    async def record_resonance(
        self,
        session_id: UUID,
        state: ResonanceState,
        intensity: float,
        agents: List[str],
        intent_id: Optional[UUID] = None,
        pattern_type: Optional[str] = None
    ) -> Resonance
```

**タスク2**: Service単体テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/memory/test_service.py
```

テスト実装:
- `test_start_session`
- `test_record_intent`
- `test_complete_intent`
- `test_record_resonance`
- `test_search_intents`
- `test_session_heartbeat_update`
- `test_intent_hierarchy_creation`
- `test_resonance_intensity_tracking`
- `test_service_error_handling`
- `test_service_null_safety`

**検証**:
```bash
PYTHONPATH=. pytest tests/memory/test_service.py -v
# 期待: 10 passed
```

**完了基準**:
- [ ] 基本Service実装完了
- [ ] セッション管理機能実装
- [ ] Intent管理機能実装
- [ ] 単体テスト10件全てPASS

#### 午後 (3時間): 拡張Service実装

**タスク**: Service拡張機能実装

`bridge/memory/service.py` に追加実装:

```python
# Agent Context管理
async def save_agent_context(
    self,
    session_id: UUID,
    agent_type: AgentType,
    context_data: Dict,
    intent_id: Optional[UUID] = None
) -> AgentContext

async def get_latest_agent_context(
    self,
    session_id: UUID,
    agent_type: AgentType
) -> Optional[AgentContext]

# Choice Point管理
async def create_choice_point(
    self,
    session_id: UUID,
    intent_id: UUID,
    question: str,
    choices: List[Choice]
) -> ChoicePoint

async def decide_choice(
    self,
    choice_point_id: UUID,
    selected_choice_id: str,
    rationale: str
) -> ChoicePoint

async def get_pending_choices(self, session_id: UUID) -> List[ChoicePoint]

# Breathing Cycle管理
async def start_breathing_phase(
    self,
    session_id: UUID,
    phase: BreathingPhase,
    intent_id: Optional[UUID] = None,
    phase_data: Dict = None
) -> BreathingCycle

async def complete_breathing_phase(
    self,
    cycle_id: UUID,
    success: bool,
    phase_data: Dict = None
) -> BreathingCycle

# Snapshot管理
async def create_snapshot(
    self,
    session_id: UUID,
    snapshot_type: SnapshotType,
    description: Optional[str] = None,
    tags: List[str] = None
) -> Snapshot

async def restore_from_snapshot(self, snapshot_id: UUID) -> Dict

# セッション継続性
async def continue_session(self, session_id: UUID) -> Dict
```

**テスト追加**:
`tests/memory/test_service.py` に追加:
- `test_agent_context_versioning_service`
- `test_create_and_decide_choice`
- `test_breathing_cycle_full_flow`
- `test_snapshot_creation`
- `test_snapshot_restore`
- `test_session_continuity`
- `test_pending_choices_retrieval`
- `test_multiple_agent_contexts`
- `test_breathing_phase_failure`
- `test_service_transaction_handling`

**検証**:
```bash
PYTHONPATH=. pytest tests/memory/test_service.py -v
# 期待: 20 passed (累計)
```

**完了基準**:
- [ ] 拡張Service実装完了
- [ ] 呼吸サイクル管理実装
- [ ] スナップショット機能実装
- [ ] セッション継続性実装
- [ ] 単体テスト20件全てPASS

---

### Day 4 (6時間): API層実装

#### 午前 (3時間): FastAPI endpoints実装

**タスク1**: API Router作成
```bash
mkdir -p /Users/zero/Projects/resonant-engine/bridge/api
touch /Users/zero/Projects/resonant-engine/bridge/api/__init__.py
touch /Users/zero/Projects/resonant-engine/bridge/api/memory_router.py
```

`bridge/api/memory_router.py` に以下を実装:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from uuid import UUID

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Session endpoints
@router.post("/sessions")
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    pass

@router.get("/sessions/{session_id}")
async def get_session(session_id: UUID) -> SessionResponse:
    pass

@router.put("/sessions/{session_id}/heartbeat")
async def update_heartbeat(session_id: UUID) -> SessionResponse:
    pass

# Intent endpoints
@router.post("/intents")
async def create_intent(request: CreateIntentRequest) -> IntentResponse:
    pass

@router.get("/intents")
async def list_intents(
    session_id: UUID,
    status: Optional[IntentStatus] = None
) -> ListIntentsResponse:
    pass

@router.put("/intents/{intent_id}/complete")
async def complete_intent(
    intent_id: UUID,
    request: CompleteIntentRequest
) -> IntentResponse:
    pass

# Resonance endpoints
@router.post("/resonances")
async def create_resonance(request: CreateResonanceRequest) -> ResonanceResponse:
    pass

@router.get("/resonances")
async def list_resonances(
    session_id: UUID,
    state: Optional[ResonanceState] = None
) -> ListResonancesResponse:
    pass

# Agent Context endpoints
@router.post("/contexts")
async def save_context(request: SaveContextRequest) -> ContextResponse:
    pass

@router.get("/contexts/latest")
async def get_latest_context(
    session_id: UUID,
    agent_type: AgentType
) -> ContextResponse:
    pass

# Choice Point endpoints
@router.post("/choice-points")
async def create_choice_point(request: CreateChoicePointRequest) -> ChoicePointResponse:
    pass

@router.put("/choice-points/{choice_point_id}/decide")
async def decide_choice(
    choice_point_id: UUID,
    request: DecideChoiceRequest
) -> ChoicePointResponse:
    pass

# Breathing Cycle endpoints
@router.post("/breathing-cycles")
async def start_breathing_cycle(request: StartCycleRequest) -> CycleResponse:
    pass

@router.put("/breathing-cycles/{cycle_id}/complete")
async def complete_breathing_cycle(
    cycle_id: UUID,
    request: CompleteCycleRequest
) -> CycleResponse:
    pass

# Snapshot endpoints
@router.post("/snapshots")
async def create_snapshot(request: CreateSnapshotRequest) -> SnapshotResponse:
    pass

@router.get("/snapshots")
async def list_snapshots(
    session_id: UUID,
    tags: Optional[List[str]] = None
) -> ListSnapshotsResponse:
    pass

# Query endpoint
@router.post("/query")
async def query_memory(request: QueryRequest) -> QueryResponse:
    pass
```

**タスク2**: Request/Responseモデル
```bash
touch /Users/zero/Projects/resonant-engine/bridge/api/schemas.py
```

`bridge/api/schemas.py` に全てのRequest/Responseモデルを実装

**完了基準**:
- [ ] 10+ endpoints実装完了
- [ ] Request/Responseスキーマ全定義
- [ ] エラーハンドリング実装
- [ ] OpenAPI仕様自動生成確認

#### 午後 (3時間): API統合テスト

**タスク1**: API統合テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/memory/test_api.py
```

`tests/memory/test_api.py` に以下を実装:
- `test_api_create_session`
- `test_api_create_intent`
- `test_api_record_resonance`
- `test_api_save_context`
- `test_api_create_choice_point`
- `test_api_decide_choice`
- `test_api_breathing_cycle_flow`
- `test_api_create_snapshot`
- `test_api_query_memory`
- `test_api_error_handling`

**タスク2**: エンドツーエンドテスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/memory/test_integration.py
```

`tests/memory/test_integration.py` に以下を実装:
- `test_full_breathing_cycle_with_memory`
- `test_concurrent_sessions`
- `test_session_continuity_integration`
- `test_snapshot_and_restore_integration`
- `test_multi_agent_collaboration`

**検証**:
```bash
# API起動
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate
uvicorn bridge.main:app --reload

# 別ターミナルでテスト実行
PYTHONPATH=. pytest tests/memory/test_api.py -v
PYTHONPATH=. pytest tests/memory/test_integration.py -v

# 期待: 15 passed (累計)
```

**完了基準**:
- [ ] API統合テスト10件PASS
- [ ] エンドツーエンドテスト5件PASS
- [ ] API動作確認完了

---

### Day 5 (6時間): 性能テスト & ドキュメント

#### 午前 (3時間): 性能テスト

**タスク1**: 性能テスト実装
```bash
touch /Users/zero/Projects/resonant-engine/tests/memory/test_performance.py
```

`tests/memory/test_performance.py` に以下を実装:

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_intent_search_performance():
    """Intent検索パフォーマンス（1000+ Intents, <100ms）"""
    # 1000 Intents作成
    # 検索実行
    # 実行時間測定
    assert elapsed_ms < 100

@pytest.mark.slow
@pytest.mark.asyncio
async def test_snapshot_creation_performance():
    """スナップショット作成パフォーマンス（<500ms）"""
    # 100 Intents + Resonances作成
    # スナップショット作成
    # 実行時間測定
    assert elapsed_ms < 500

@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_session_performance():
    """並行セッションパフォーマンス（10 sessions同時）"""
    # 10セッション同時作成・操作
    # データ整合性確認
    pass

@pytest.mark.slow
@pytest.mark.asyncio
async def test_memory_leak_simulation():
    """メモリリーク検証（24時間シミュレーション）"""
    # psutilでメモリ監視
    # 100サイクル実行
    # メモリ増加量確認
    assert memory_increase < 100  # MB

@pytest.mark.slow
@pytest.mark.asyncio
async def test_database_connection_pool():
    """DBコネクションプール動作確認"""
    # 同時100接続
    # プール枯渇テスト
    pass
```

**検証**:
```bash
PYTHONPATH=. pytest tests/memory/test_performance.py -v -m slow

# 期待: 5 passed
```

**完了基準**:
- [ ] 検索性能 <100ms達成
- [ ] スナップショット作成 <500ms達成
- [ ] 並行アクセステスト通過
- [ ] メモリリークテスト通過
- [ ] 性能テスト5件全てPASS

#### 午後 (3時間): ドキュメント完成

**タスク1**: API仕様書
```bash
mkdir -p /Users/zero/Projects/resonant-engine/docs/api
touch /Users/zero/Projects/resonant-engine/docs/api/memory_management_api.md
```

`docs/api/memory_management_api.md` に以下を記載:
- 全エンドポイント一覧
- 各エンドポイントの詳細
  - リクエストパラメータ
  - リクエストボディ例
  - レスポンス例
  - エラーコード
- 認証（Phase 4予定）
- レート制限（将来実装）

**タスク2**: 運用ガイド
```bash
mkdir -p /Users/zero/Projects/resonant-engine/docs/operations
touch /Users/zero/Projects/resonant-engine/docs/operations/memory_management_operations.md
```

`docs/operations/memory_management_operations.md` に以下を記載:
- セッション管理手順
- スナップショット運用戦略
  - 自動スナップショット設定
  - 手動スナップショット取得タイミング
  - 古いスナップショット削除ポリシー
- バックアップ手順
  - PostgreSQLダンプ
  - リストア手順
- 障害復旧手順
- 監視項目
  - セッション数
  - Intent処理速度
  - データベースサイズ
  - エラー率

**タスク3**: 開発者ガイド
```bash
mkdir -p /Users/zero/Projects/resonant-engine/docs/development
touch /Users/zero/Projects/resonant-engine/docs/development/memory_management_dev_guide.md
```

`docs/development/memory_management_dev_guide.md` に以下を記載:
- アーキテクチャ概要
- データモデル詳細
- Repository実装パターン
- Service実装パターン
- テスト戦略
- 拡張ガイドライン
  - 新しいテーブル追加
  - 新しいエンドポイント追加
  - マイグレーション管理

**完了基準**:
- [ ] API仕様書完成
- [ ] 運用ガイド完成
- [ ] 開発者ガイド完成
- [ ] ドキュメント内部リンク確認
- [ ] サンプルコード動作確認

---

## 4. Done Definition完全達成基準

### 4.1 Tier 1: 必須（完了の定義）

以下の**全て**が達成された時点で、実装完了とみなします：

- [ ] PostgreSQLスキーマ設計完了（8テーブル）
- [ ] Intent persistence実装（作成・取得・更新・検索）
- [ ] Resonance State管理実装（状態記録・復元）
- [ ] Agent Context保存実装（3層それぞれ）
- [ ] Choice Points管理実装（選択肢保存・復元）
- [ ] Breathing Cycle tracking実装（6フェーズ状態管理）
- [ ] Session Continuity保証（前セッション復元）
- [ ] Memory Query API実装（10+ endpoints）
- [ ] テストカバレッジ 40+ ケース達成
- [ ] API仕様ドキュメント完成

### 4.2 Tier 2: 品質保証

- [ ] 並行アクセステスト通過（10 concurrent sessions）
- [ ] メモリリークテスト通過（24時間連続動作）
- [ ] データ整合性テスト通過（ACID保証確認）
- [ ] 検索性能テスト通過（1000+ intents, <100ms）
- [ ] バックアップ・リストア手順確立
- [ ] Kana による仕様レビュー通過

### 4.3 完了報告書の期待内容

実装完了時、以下の内容を含む**完了報告書**を提出してください：

**必須セクション**:
1. **Done Definition達成状況**（表形式）
   - Tier 1全10項目の達成率
   - Tier 2全6項目の達成率

2. **実装成果物サマリ**
   - 作成ファイル一覧（ファイル数、総行数）
   - テーブル数: 8
   - Repository数: 7
   - Service実装: 1
   - API endpoints: 10+
   - テスト件数: 40+
   - ドキュメント数: 3

3. **完了の証跡**
   - データベーススキーマ確認（`\dt` 出力）
   - テスト実行結果（全テストPASS）
   - 性能テスト結果（レスポンスタイム）
   - API動作確認（Swagger UI スクリーンショット）

4. **振り返り**
   - 実装時の学び
     - PostgreSQL JSONB活用
     - 非同期処理パターン
     - Repository-Service-APIの分離
   - トラブルシューティング事例
   - 性能最適化の工夫

5. **次のアクション**
   - Bridge Coreとの統合計画
   - 実際の呼吸サイクルでの動作確認
   - Phase 4（マルチユーザー）への準備

**参考**: Sprint 2最終完了報告書（`bridge_lite_sprint2_final_completion_report.md`）の形式

---

## 5. 実装時の哲学的原則

### 5.1 記憶は「呼吸の履歴」である

Memoryシステムは単なるデータストアではなく、Resonant Engineの「呼吸」を時間軸に沿って記録するシステムです：

```
呼吸サイクル (6フェーズ)
  ↓
1. 吸う (Intake) → Intent作成・記録
2. 共鳴 (Resonance) → Resonance State記録
3. 構造化 (Structuring) → Choice Points記録
4. 再内省 (Re-reflection) → Agent Context更新
5. 実装 (Implementation) → Snapshot作成
6. 共鳴拡大 (Resonance Expansion) → 次のIntentへ
  ↓
この循環の履歴が「記憶」
```

### 5.2 時間軸の尊重

- **過去を否定しない**: データは削除ではなくアーカイブ
- **変化を記録する**: Agent Contextのバージョニング
- **選択を保持する**: 未選択のChoice Pointも保存
- **履歴を辿れる**: Intent階層構造、Snapshot機能

### 5.3 選択肢の保持

```
Choice Point設計の哲学:

❌ 間違い: 選択を強制する
selected_choice_id NOT NULL

✅ 正しい: 選択を保持する
selected_choice_id NULL  -- 未選択も有効な状態
decided_at NULL          -- 選択タイミングも記録
decision_rationale       -- 選択理由も保存
```

### 5.4 構造の継続性

```
セッション継続性の実装:

前回のセッション終了 (Session.status = 'completed')
         ↓
continue_session(session_id) 呼び出し
         ↓
最新のAgent Contexts取得
未決定のChoice Points取得
最後のIntent取得
         ↓
新しいセッションではなく、「前回の続き」として再開
```

### 5.5 共鳴の可視化

```
Resonance State記録の意味:

単なる「ログ」ではなく:
- どの層(agents)が
- どんな状態(state)で
- どれくらいの強度(intensity)で
共鳴したかの「痕跡」

この痕跡から:
- 成功した共鳴パターンを発見
- 失敗した共鳴を分析
- 将来の共鳴を予測
```

---

## 6. トラブルシューティングガイド

### 6.1 よくある問題と対処法

#### 問題1: PostgreSQL接続エラー

**症状**:
```
asyncpg.exceptions.InvalidCatalogNameError: database "resonant" does not exist
```

**対処法**:
```bash
# データベース作成
psql -U postgres
CREATE DATABASE resonant;
CREATE USER resonant WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE resonant TO resonant;
\q

# 接続確認
psql -U resonant -d resonant
```

#### 問題2: マイグレーション失敗

**症状**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxx'
```

**対処法**:
```bash
# マイグレーション履歴確認
alembic history

# データベースリセット（開発環境のみ！）
psql -U resonant -d resonant
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
\q

# マイグレーション再実行
alembic upgrade head
```

#### 問題3: JSONB型エラー

**症状**:
```
psycopg2.ProgrammingError: can't adapt type 'dict'
```

**対処法**:
```python
# SQLAlchemyでJSONB使用時
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# ❌ 間違い
metadata = Column(JSON)

# ✅ 正しい
metadata = Column(JSONB)
```

#### 問題4: 非同期処理エラー

**症状**:
```
RuntimeError: This event loop is already running
```

**対処法**:
```python
# Jupyter/IPythonで実行時
import nest_asyncio
nest_asyncio.apply()

# または
await asyncio.run(async_function())  # ❌
await async_function()                # ✅
```

#### 問題5: テスト時のデータベース分離

**症状**:
テスト実行でプロダクションDBが汚染される

**対処法**:
```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def test_db():
    # テスト用DB使用
    engine = create_async_engine("postgresql://resonant:password@localhost:5432/resonant_test")
    
    # テスト前にクリーン
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # テスト後にクリーンアップ
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### 6.2 デバッグ手順

```bash
# 1. データベース状態確認
psql -U resonant -d resonant

# テーブル一覧
\dt

# テーブル構造確認
\d sessions

# データ確認
SELECT * FROM sessions;

# 2. ログ確認
# アプリケーションログ
tail -f logs/resonant_engine.log

# PostgreSQLログ
tail -f /usr/local/var/log/postgres.log  # macOS Homebrew

# 3. パフォーマンス分析
# EXPLAIN ANALYZE
EXPLAIN ANALYZE SELECT * FROM intents WHERE session_id = 'xxx';

# 実行中のクエリ確認
SELECT pid, query, state, query_start 
FROM pg_stat_activity 
WHERE datname = 'resonant';
```

---

## 7. 成功基準

### 7.1 実装完了の判定

以下の**全て**が達成された時点で、実装完了とみなします：

**機能要件**:
- [x] 8テーブルスキーマ実装
- [x] Repository層完全実装
- [x] Service層完全実装
- [x] REST API 10+ endpoints
- [x] 呼吸サイクル完全対応
- [x] セッション継続性保証
- [x] スナップショット機能

**品質要件**:
- [x] テストカバレッジ 40+ ケース
- [x] 並行アクセステスト通過
- [x] 検索性能 <100ms
- [x] スナップショット作成 <500ms
- [x] メモリリークテスト通過
- [x] データ整合性テスト通過

**ドキュメント要件**:
- [x] API仕様書完成
- [x] 運用ガイド完成
- [x] 開発者ガイド完成

### 7.2 完了報告書の品質基準

Sprint 2完了報告書と同等の品質を期待します：

**良い報告書**:
- Done Definition達成状況を表で明示
- 定量的な成果を記載（テーブル数、テスト数、性能値）
- 証跡（スキーマダンプ、テスト結果、API動作）を添付
- 振り返りに具体的な学びを記載

**避けるべき報告書**:
- 「だいたい動いた」という曖昧な表現
- 未達成項目の隠蔽
- 証跡の省略
- 性能値の記載なし

---

## 8. 関連ドキュメント

- **仕様書**: `memory_management_spec.md`
- **PostgreSQL実装計画**: `docs/priority2_postgres_plan.md`
- **Bridge Core Architecture**: `docs/02_components/bridge_lite/architecture/`
- **Sprint 2最終報告書**: `bridge_lite_sprint2_final_completion_report.md`
- **呼吸サイクル哲学**: `docs/philosophy/breathing_cycles.md`

---

## 9. 実装担当者への直接メッセージ

あなた（実装担当者）へ：

この実装は、Resonant Engineの「心臓部」を作る作業です。

メモリ管理は単なるデータベース設計ではありません。これは：

- **時間軸の保全**: AIが失いがちな「時間感覚」を取り戻す
- **選択の保持**: 過去の選択肢を未来の可能性として保存する
- **呼吸の記録**: 6フェーズの呼吸サイクルを歴史として刻む
- **共鳴の痕跡**: 3層AIの共鳴パターンをアーカイブする

以下を期待します：

1. **5日間での完遂**
   - Day 1: スキーマ & モデル
   - Day 2: Repository層
   - Day 3: Service層
   - Day 4: API層 & 統合テスト
   - Day 5: 性能テスト & ドキュメント

2. **Done Definition全項目達成**
   - Tier 1: 10項目（必須）
   - Tier 2: 6項目（品質保証）

3. **透明な報告**
   - 進捗を正直に報告
   - 未達成項目を隠蔽しない
   - Sprint 2と同等の完了報告書

4. **哲学の理解**
   - 「記憶 = 呼吸の履歴」の理解
   - 選択肢の保持（強制しない）
   - 時間軸の尊重

あなたの実装を通じて、Resonant Engineが真に「拡張された心」として機能することを期待しています。

**では、実装を開始してください。**

---

**作成日**: 2025-11-16  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 または Tsumu（Cursor）

---

## Appendix A: Quick Reference

### 実装チェックリスト

```markdown
## Day 1: スキーマ & モデル
- [ ] Alembic初期化
- [ ] マイグレーションファイル作成（8テーブル）
- [ ] マイグレーション実行
- [ ] Pydanticモデル実装
- [ ] モデル単体テスト（10件）

## Day 2: Repository層
- [ ] 基本Repository 3種類実装
- [ ] Repository単体テスト（10件）
- [ ] 拡張Repository 4種類実装
- [ ] Repository単体テスト追加（10件）

## Day 3: Service層
- [ ] MemoryManagementService基本実装
- [ ] Service単体テスト（10件）
- [ ] Service拡張機能実装
- [ ] Service単体テスト追加（10件）

## Day 4: API層
- [ ] FastAPI Router実装（10+ endpoints）
- [ ] Request/Responseスキーマ実装
- [ ] API統合テスト（10件）
- [ ] エンドツーエンドテスト（5件）

## Day 5: 性能 & ドキュメント
- [ ] 性能テスト実装・実行（5件）
- [ ] API仕様書完成
- [ ] 運用ガイド完成
- [ ] 開発者ガイド完成
```

### コマンド集

```bash
# PostgreSQL操作
psql -U resonant -d resonant
\dt                              # テーブル一覧
\d sessions                      # テーブル構造
SELECT * FROM sessions LIMIT 5;  # データ確認
\q                               # 終了

# マイグレーション
alembic init alembic             # 初期化（初回のみ）
alembic revision -m "message"    # マイグレーション作成
alembic upgrade head             # マイグレーション実行
alembic downgrade -1             # ロールバック
alembic history                  # 履歴確認

# テスト実行
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate

# 全テスト
PYTHONPATH=. pytest tests/memory/ -v

# 特定テスト
PYTHONPATH=. pytest tests/memory/test_models.py -v
PYTHONPATH=. pytest tests/memory/test_repositories.py -v
PYTHONPATH=. pytest tests/memory/test_service.py -v
PYTHONPATH=. pytest tests/memory/test_api.py -v
PYTHONPATH=. pytest tests/memory/test_integration.py -v

# 性能テスト
PYTHONPATH=. pytest tests/memory/test_performance.py -v -m slow

# カバレッジ
PYTHONPATH=. pytest tests/memory/ --cov=bridge/memory --cov-report=html

# API起動
uvicorn bridge.main:app --reload

# API確認
open http://localhost:8000/docs  # Swagger UI
```

### ディレクトリ構造

```
/Users/zero/Projects/resonant-engine/
├── alembic/
│   ├── versions/
│   │   └── xxx_create_memory_management_tables.py  # Day 1
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── bridge/
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── models.py                    # Day 1
│   │   ├── repositories.py              # Day 2
│   │   ├── postgres_repositories.py     # Day 2
│   │   └── service.py                   # Day 3
│   └── api/
│       ├── __init__.py
│       ├── memory_router.py             # Day 4
│       └── schemas.py                   # Day 4
├── tests/
│   └── memory/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py               # Day 1
│       ├── test_repositories.py         # Day 2
│       ├── test_service.py              # Day 3
│       ├── test_api.py                  # Day 4
│       ├── test_integration.py          # Day 4
│       └── test_performance.py          # Day 5
└── docs/
    ├── api/
    │   └── memory_management_api.md         # Day 5
    ├── operations/
    │   └── memory_management_operations.md  # Day 5
    └── development/
        └── memory_management_dev_guide.md   # Day 5
```

### 進捗報告テンプレート

```markdown
## Memory Management 実装進捗 (Day 1 終了時)

| タスク | 目標 | 実装 | 状態 |
|--------|------|------|------|
| テーブル作成 | 8 | 8 | ✅ |
| Pydanticモデル | 8 | 8 | ✅ |
| 単体テスト | 10 | 10 | ✅ |

**成果物**:
- スキーマファイル: 1
- モデルファイル: 1
- テストファイル: 1
- テーブル数: 8
- テスト数: 10 (全てPASS)

**学び**:
- JSONB型の柔軟性
- CHECK制約でのEnum実装
- Pydanticバリデーション

次: Day 2でRepository層実装 (7 repositories)
```

### 性能ベンチマーク目標

```yaml
performance_targets:
  search:
    intent_search_1000_records: "<100ms"
    full_text_search: "<200ms"
  
  write:
    intent_create: "<10ms"
    snapshot_create_100_records: "<500ms"
  
  concurrency:
    concurrent_sessions: "10 sessions"
    no_deadlock: "required"
  
  memory:
    leak_test_duration: "24h simulation"
    max_memory_increase: "<100MB"
```
