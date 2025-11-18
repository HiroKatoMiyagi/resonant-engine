# Sprint 7: Session Summary自動生成仕様書

## 1. 概要

### 1.1 目的
セッション単位で会話を自動的に要約し、長期的な文脈保持を強化する。Claude APIを使用して要約を生成し、PostgreSQLに保存することで、Context Assemblerが長いセッションの概要を効率的に参照できるようにする。

### 1.2 背景

**Sprint 6の成果:**
- ✅ Intent Bridge - Context Assembler統合完了
- ✅ Working Memory: 直近10件の会話を参照
- ✅ Semantic Memory: 関連する長期記憶を検索
- ⚠️ Session Summary: 未実装（常にNone）

**現状の問題:**
```python
# Context Assembler内部
memory_layers = {
    "working_memory": [最新10件],  # ✅ 動作中
    "semantic_memory": [関連5件],   # ✅ 動作中
    "session_summary": None,        # ❌ 常にNone
}
```

- 長いセッション（50+メッセージ）では、Working Memoryだけでは文脈を把握しきれない
- Semantic Memoryは関連性で選ぶため、時系列の流れが失われる
- セッション全体の流れや結論を要約する機能が不足

**Sprint 7の目標:**
- セッション単位で会話を自動要約
- 要約をPostgreSQLに保存
- Context Assemblerが自動的に要約を取得
- 長期的な文脈保持の強化

---

## 2. ユースケース

### ケース1: 長時間の開発セッション

```
# セッション開始（10:00）
User: "Memory Storeの実装を始めたい"
Assistant: "Memory Storeの設計から始めましょう..."

... 20メッセージの会話 ...

User: "pgvectorの設定方法は？"
Assistant: "pgvectorのインストールは..."

... さらに30メッセージ ...

# セッション中断（12:00、合計50メッセージ）
→ Session Summaryが自動生成される:
  "2025-11-18 10:00-12:00: Memory Store実装セッション。
   pgvectorベースの長期記憶システムを設計・実装。
   主な成果: repository.py完成、テスト10件作成、
   pgvector設定完了。次のステップ: Retrieval Orchestrator統合。"

# 翌日再開（2025-11-19 09:00）
User: "昨日の続きから始めたい"
→ Context Assembler:
   - Working Memory: 直近10件（昨日の最後の会話）
   - Semantic Memory: 関連記憶5件
   - Session Summary: 昨日のセッション要約 ← NEW!
→ Assistant: "昨日はMemory Storeの実装を完了しましたね。
              次はRetrieval Orchestrator統合ですね。"
```

### ケース2: 複数セッションにまたがるプロジェクト

```
# Sprint 1セッション（11/10）
→ Summary: "Sprint 1: Bridge Lite基盤実装"

# Sprint 2セッション（11/12）
→ Summary: "Sprint 2: Memory Store実装"

# Sprint 3セッション（11/14）
→ Summary: "Sprint 3: Retrieval Orchestrator実装"

# 2週間後（11/28）
User: "Memory Storeの実装、どうなってたっけ？"
→ Context Assembler:
   - Session Summary: Sprint 2の要約を参照
→ Assistant: "11/12のSprint 2でMemory Storeを実装しました。
              pgvectorベースで、MessageRepositoryと
              MemoryRepositoryが完成しています。"
```

---

## 3. アーキテクチャ

### 3.1 システム構成

```
┌─────────────────────────────────────────────────────────────┐
│                     Intent Bridge                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ IntentProcessor.process()                            │  │
│  │  ├─ KanaAIBridge.process_intent()                    │  │
│  │  │   └─ Context Assembler.assemble_context()        │  │
│  │  │       ├─ Working Memory (10件)                    │  │
│  │  │       ├─ Semantic Memory (5件)                    │  │
│  │  │       └─ Session Summary (NEW!)                   │  │
│  │  │           └─ SessionSummaryRepository.get()       │  │
│  │  │                                                    │  │
│  │  └─ Session Manager (NEW!)                           │  │
│  │      └─ 要約トリガー判定                              │  │
│  │          └─ Summarization Service                    │  │
│  │              ├─ 会話履歴取得                          │  │
│  │              ├─ Claude API（要約生成）                │  │
│  │              └─ SessionSummaryRepository.save()      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ messages     │  │ memories     │  │ session_summaries│ │
│  │              │  │              │  │   (NEW!)         │ │
│  │ - id         │  │ - id         │  │ - id             │ │
│  │ - user_id    │  │ - user_id    │  │ - user_id        │ │
│  │ - session_id │  │ - content    │  │ - session_id     │ │
│  │ - role       │  │ - embedding  │  │ - summary        │ │
│  │ - content    │  │              │  │ - message_count  │ │
│  │ - created_at │  │              │  │ - start_time     │ │
│  └──────────────┘  └──────────────┘  │ - end_time       │ │
│                                       │ - created_at     │ │
│                                       └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 データフロー

#### フロー1: Session Summary生成（自動）

```
[Intent処理完了]
  ↓
SessionManager.check_summary_trigger()
  ├─ 条件1: メッセージ数 >= 20
  ├─ 条件2: 最終要約から1時間経過
  └─ 条件3: セッション終了通知
  ↓
  YES → SummarizationService.create_summary()
         ├─ 1. MessagesRepository.list(session_id)
         │     → 当該セッションの全メッセージ取得
         │
         ├─ 2. Claude API呼び出し（要約生成）
         │     Prompt: "以下の会話を3-5文で要約してください"
         │     → 要約テキスト生成
         │
         └─ 3. SessionSummaryRepository.save()
               → PostgreSQLに保存
```

#### フロー2: Session Summary取得（Context Assembler）

```
[Context Assembler.assemble_context()]
  ↓
_fetch_session_summary(user_id, session_id)
  ↓
SessionSummaryRepository.get_latest(user_id, session_id)
  ↓
  session_summary exists?
    YES → 要約テキストを返す
    NO  → None
  ↓
messages構築:
  - System Prompt
  - Session Summary（あれば）← NEW!
  - Semantic Memory
  - Working Memory
  - Current Message
```

---

## 4. コンポーネント設計

### 4.1 SessionSummaryRepository

**ファイル**: `memory_store/session_summary_repository.py`

**責務**:
- Session SummaryのCRUD操作
- セッション単位での取得
- ユーザー単位での取得

**インターフェース**:

```python
class SessionSummaryRepository:
    """Session Summary永続化層"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save(
        self,
        user_id: str,
        session_id: UUID,
        summary: str,
        message_count: int,
        start_time: datetime,
        end_time: datetime,
    ) -> UUID:
        """Session Summaryを保存"""

    async def get_latest(
        self,
        user_id: str,
        session_id: Optional[UUID] = None,
    ) -> Optional[SessionSummaryResponse]:
        """最新のSession Summaryを取得"""

    async def get_by_session(
        self,
        session_id: UUID,
    ) -> Optional[SessionSummaryResponse]:
        """特定セッションのSummaryを取得"""

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[SessionSummaryResponse]:
        """ユーザーのSession Summary一覧を取得"""

    async def delete(self, summary_id: UUID) -> bool:
        """Session Summaryを削除"""
```

### 4.2 SummarizationService

**ファイル**: `summarization/service.py`

**責務**:
- 会話履歴の取得
- Claude APIを使用した要約生成
- 要約の保存

**インターフェース**:

```python
class SummarizationService:
    """会話要約生成サービス"""

    def __init__(
        self,
        message_repo: MessageRepository,
        summary_repo: SessionSummaryRepository,
        claude_client: Optional[AsyncAnthropic] = None,
    ):
        self.message_repo = message_repo
        self.summary_repo = summary_repo
        self.claude_client = claude_client or self._create_claude_client()

    async def create_summary(
        self,
        user_id: str,
        session_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> SessionSummaryResponse:
        """セッションの要約を生成"""

    async def _fetch_session_messages(
        self,
        user_id: str,
        session_id: UUID,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> List[MessageResponse]:
        """セッションのメッセージを取得"""

    async def _generate_summary_with_claude(
        self,
        messages: List[MessageResponse],
    ) -> str:
        """Claude APIで要約生成"""

    def _build_summarization_prompt(
        self,
        messages: List[MessageResponse],
    ) -> str:
        """要約生成用プロンプトを構築"""
```

### 4.3 SessionManager

**ファイル**: `session/manager.py`

**責務**:
- セッション状態の管理
- 要約生成トリガーの判定
- セッションメタデータの管理

**インターフェース**:

```python
class SessionManager:
    """セッション管理とトリガー制御"""

    def __init__(
        self,
        message_repo: MessageRepository,
        summary_repo: SessionSummaryRepository,
        summarization_service: SummarizationService,
        config: Optional[SessionConfig] = None,
    ):
        self.message_repo = message_repo
        self.summary_repo = summary_repo
        self.summarization = summarization_service
        self.config = config or get_default_session_config()

    async def check_and_create_summary(
        self,
        user_id: str,
        session_id: UUID,
    ) -> Optional[SessionSummaryResponse]:
        """要約生成の必要性を判定し、必要なら生成"""

    async def _should_create_summary(
        self,
        user_id: str,
        session_id: UUID,
    ) -> bool:
        """要約生成が必要か判定"""

    async def get_session_stats(
        self,
        user_id: str,
        session_id: UUID,
    ) -> SessionStats:
        """セッション統計を取得"""
```

### 4.4 Context Assembler拡張

**ファイル**: `context_assembler/service.py` (既存ファイル修正)

**変更内容**:

```python
class ContextAssemblerService:
    # ... 既存コード ...

    async def _fetch_session_summary(
        self,
        user_id: str,
        session_id: Optional[UUID],
    ) -> Optional[str]:
        """Session Summaryを取得（修正）"""
        if not session_id:
            return None

        # SessionSummaryRepositoryから取得
        from memory_store.session_summary_repository import SessionSummaryRepository

        summary_repo = SessionSummaryRepository(self.message_repo.pool)
        summary = await summary_repo.get_latest(user_id, session_id)

        if summary:
            return summary.summary  # 要約テキストを返す

        return None
```

---

## 5. データモデル

### 5.1 PostgreSQLスキーマ

**テーブル**: `session_summaries`

```sql
CREATE TABLE IF NOT EXISTS session_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id UUID NOT NULL,
    summary TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- インデックス
    CONSTRAINT unique_session_summary UNIQUE (user_id, session_id)
);

CREATE INDEX idx_session_summaries_user_id ON session_summaries(user_id);
CREATE INDEX idx_session_summaries_session_id ON session_summaries(session_id);
CREATE INDEX idx_session_summaries_created_at ON session_summaries(created_at DESC);
```

### 5.2 Pythonモデル

**ファイル**: `memory_store/models.py` (既存ファイル拡張)

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class SessionSummaryResponse(BaseModel):
    """Session Summary応答モデル"""
    id: UUID
    user_id: str
    session_id: UUID
    summary: str
    message_count: int = Field(ge=0)
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SessionStats(BaseModel):
    """セッション統計モデル"""
    session_id: UUID
    message_count: int
    first_message_time: Optional[datetime]
    last_message_time: Optional[datetime]
    duration_seconds: Optional[int]
    has_summary: bool
    last_summary_time: Optional[datetime]
```

### 5.3 設定モデル

**ファイル**: `session/config.py`

```python
from pydantic import BaseModel, Field

class SessionConfig(BaseModel):
    """セッション管理設定"""

    # 要約生成トリガー条件
    summary_trigger_message_count: int = Field(
        default=20,
        ge=10,
        description="この数のメッセージ後に要約生成"
    )

    summary_trigger_interval_seconds: int = Field(
        default=3600,  # 1時間
        ge=300,  # 最低5分
        description="前回要約からこの秒数経過後に要約生成"
    )

    # 要約設定
    summary_max_messages: int = Field(
        default=100,
        ge=10,
        description="要約に含める最大メッセージ数"
    )

    summary_max_tokens: int = Field(
        default=4000,
        ge=500,
        description="要約生成時の最大トークン数"
    )

    # Claude API設定
    claude_model: str = Field(
        default="claude-3-5-haiku-20241022",  # 要約には高速なHaikuを使用
        description="要約生成に使用するClaudeモデル"
    )

    claude_max_tokens: int = Field(
        default=500,
        ge=100,
        le=1000,
        description="要約の最大トークン数"
    )

def get_default_session_config() -> SessionConfig:
    """デフォルト設定を取得"""
    return SessionConfig()
```

---

## 6. 要約生成ロジック

### 6.1 トリガー条件

Session Summaryは以下のいずれかの条件で自動生成：

#### 条件1: メッセージ数閾値
```python
# 20メッセージごとに要約生成
if session_message_count >= 20 and session_message_count % 20 == 0:
    create_summary()
```

#### 条件2: 時間経過
```python
# 前回要約から1時間経過
if last_summary_time and (now - last_summary_time) >= 3600:
    create_summary()
```

#### 条件3: セッション終了（将来実装）
```python
# ユーザーがセッション終了を明示的に通知
if session_end_event:
    create_summary()
```

### 6.2 要約生成プロンプト

```python
def _build_summarization_prompt(messages: List[MessageResponse]) -> str:
    """要約生成用プロンプト"""

    # メッセージを整形
    conversation = "\n".join([
        f"{msg.role}: {msg.content}"
        for msg in messages
    ])

    return f"""以下の会話セッションを要約してください。

要約の要件:
1. 3-5文の簡潔な要約
2. 主要なトピック、決定事項、成果を含める
3. 次のステップや未解決の課題があれば記載
4. 日時情報（開始時刻）を含める
5. 技術的な詳細は省略し、高レベルな概要を提供

会話:
{conversation}

要約（3-5文）:"""
```

### 6.3 要約例

**入力（50メッセージの会話）**:
```
user: "Memory Storeの実装を始めたい"
assistant: "Memory Storeの設計から始めましょう..."
... 48メッセージ ...
user: "テストも完了した"
assistant: "素晴らしいです。次はRetrieval Orchestratorです"
```

**出力（要約）**:
```
2025-11-18 10:00-12:00: Memory Store実装セッション。
pgvectorベースの長期記憶システムを設計・実装し、
MessageRepositoryとMemoryRepositoryを完成させた。
テスト10件を作成し、全て成功。
次のステップはRetrieval Orchestratorの統合。
```

---

## 7. Intent Bridge統合

### 7.1 IntentProcessor修正

**ファイル**: `intent_bridge/intent_bridge/processor.py` (既存ファイル修正)

**追加機能**:

```python
class IntentProcessor:
    def __init__(self, pool, config):
        self.pool = pool
        self.config = config
        self.ai_bridge = None
        self.session_manager = None  # NEW

    async def initialize(self):
        """非同期初期化"""
        from bridge.factory.bridge_factory import BridgeFactory
        from session.manager import SessionManager
        from session.config import get_default_session_config

        # KanaAIBridge初期化（既存）
        self.ai_bridge = await BridgeFactory.create_ai_bridge_with_memory(
            bridge_type="kana",
            pool=self.pool,
        )

        # SessionManager初期化（NEW）
        self.session_manager = await self._create_session_manager()

        logger.info("✅ KanaAIBridge and SessionManager initialized")

    async def _create_session_manager(self) -> SessionManager:
        """SessionManagerを生成"""
        from memory_store.repository import MessageRepository
        from memory_store.session_summary_repository import SessionSummaryRepository
        from summarization.service import SummarizationService
        from session.manager import SessionManager

        message_repo = MessageRepository(self.pool)
        summary_repo = SessionSummaryRepository(self.pool)
        summarization = SummarizationService(message_repo, summary_repo)

        return SessionManager(
            message_repo=message_repo,
            summary_repo=summary_repo,
            summarization_service=summarization,
        )

    async def process(self, intent_id):
        # 初回呼び出し時のみ初期化
        if self.ai_bridge is None:
            await self.initialize()

        async with self.pool.acquire() as conn:
            # ... 既存のIntent処理 ...

            try:
                # Claude API呼び出し（既存）
                response = await self.call_claude(...)

                # 結果保存（既存）
                await conn.execute(...)

                # Session Summary自動生成チェック（NEW）
                if response.get("context_metadata"):
                    await self._check_session_summary(
                        user_id=intent.get('user_id', 'hiroki'),
                        session_id=intent.get('session_id'),
                    )

                # 通知作成（既存）
                await self.create_notification(...)

    async def _check_session_summary(
        self,
        user_id: str,
        session_id: Optional[UUID],
    ) -> None:
        """Session Summary生成チェック"""
        if not session_id or not self.session_manager:
            return

        try:
            summary = await self.session_manager.check_and_create_summary(
                user_id=user_id,
                session_id=session_id,
            )

            if summary:
                logger.info(
                    f"📝 Session Summary created for session {session_id}: "
                    f"{summary.summary[:50]}..."
                )
        except Exception as e:
            logger.warning(f"Failed to create session summary: {e}")
            # エラーでも処理は継続（非クリティカル）
```

---

## 8. パフォーマンス考慮事項

### 8.1 要約生成の非同期化

```python
# ❌ 同期的（Intent処理をブロック）
summary = await summarization.create_summary(...)  # Claude API待ち

# ✅ 非同期的（バックグラウンド処理）
asyncio.create_task(
    summarization.create_summary(...)
)
# Intent処理は即座に完了
```

### 8.2 キャッシング

```python
# Session Summaryのメモリキャッシュ（将来実装）
class SessionSummaryCache:
    def __init__(self, ttl: int = 300):  # 5分TTL
        self._cache = {}
        self._ttl = ttl

    async def get(self, session_id: UUID) -> Optional[str]:
        """キャッシュから取得"""
        ...

    async def set(self, session_id: UUID, summary: str):
        """キャッシュに保存"""
        ...
```

### 8.3 コスト最適化

```python
# Haikuモデル使用（要約には十分、コスト1/5）
claude_model = "claude-3-5-haiku-20241022"

# トークン数制限
max_tokens = 500  # 要約は短く

# バッチ処理（将来実装）
# 複数セッションをまとめて要約
```

---

## 9. Done Definition（完了条件）

### Tier 1: 必須（Must Have）

- [ ] session_summariesテーブル作成（PostgreSQL）
- [ ] SessionSummaryRepository実装
  - save(), get_latest(), get_by_session(), list_by_user()
  - 単体テスト5件

- [ ] SummarizationService実装
  - create_summary(), _generate_summary_with_claude()
  - プロンプトテンプレート
  - 単体テスト8件

- [ ] SessionManager実装
  - check_and_create_summary(), _should_create_summary()
  - トリガー条件判定（メッセージ数、時間経過）
  - 単体テスト6件

- [ ] Context Assembler統合
  - _fetch_session_summary()修正
  - 単体テスト3件

- [ ] Intent Bridge統合
  - SessionManager初期化
  - 要約生成チェック
  - 単体テスト4件

- [ ] E2Eテスト実装
  - 要約生成フロー確認
  - Context Assemblerで要約取得確認
  - 3テストケース

- [ ] 受け入れテスト全件PASS
  - 12テストケース全て成功

### Tier 2: 推奨（Should Have）

- [ ] バックグラウンド処理（非同期化）
- [ ] エラーハンドリング強化
- [ ] ログ出力充実
- [ ] パフォーマンス測定
- [ ] ドキュメント更新

---

## 10. スコープ外（Out of Scope）

このSprintでは以下を実装**しない**：

- ❌ Session Summaryキャッシング（Sprint 8予定）
- ❌ ユーザー別要約設定
- ❌ 手動要約トリガーAPI
- ❌ 要約の編集機能
- ❌ 複数セッションの統合要約
- ❌ 要約の多言語対応

---

## 11. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Claude API呼び出し失敗 | 中 | リトライ機構、Fallback（要約なし） |
| 要約生成が遅い | 中 | バックグラウンド処理、Haiku使用 |
| 要約品質が低い | 低 | プロンプト改善、手動修正機能（将来） |
| トリガー条件が不適切 | 低 | 設定可能化、ユーザーフィードバック |

---

## 12. 実装スケジュール

### Day 1: データモデルとRepository
- session_summariesテーブル作成
- SessionSummaryRepository実装
- 単体テスト

### Day 2: Summarization Service
- SummarizationService実装
- Claude API統合
- プロンプト設計
- 単体テスト

### Day 3: SessionManager
- SessionManager実装
- トリガー条件実装
- 単体テスト

### Day 4: Context Assembler統合
- _fetch_session_summary()修正
- Intent Bridge統合
- 単体テスト

### Day 5: E2Eテストと受け入れテスト
- E2Eテスト実装
- 受け入れテスト実行
- バグ修正

---

## 13. 成功指標（Success Metrics）

### 定量指標
- ✅ 受け入れテスト成功率: 100%（12/12）
- ✅ 要約生成成功率: 95%以上
- ✅ 要約生成時間: 平均5秒以内
- ✅ Context Assemblerでの要約取得率: 90%以上（session_id指定時）

### 定性指標
- ✅ 要約が会話の内容を適切に反映
- ✅ 長いセッションでも文脈を保持
- ✅ ユーザーが過去のセッションを思い出せる
- ✅ コードの可読性・保守性が維持される

---

## 14. 参考資料

- [Sprint 6: Intent Bridge - Context Assembler統合](./sprint6_intent_bridge_integration_spec.md)
- [Sprint 5: Context Assembler実装](./sprint5_context_assembler_spec.md)
- [Context Assembler Service](../../../context_assembler/service.py)
- [Claude API Documentation](https://docs.anthropic.com/en/api)
