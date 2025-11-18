# Sprint 6: Intent Bridge - Context Assembler統合 作業開始指示書

## 📋 作業概要

**Sprint**: Sprint 6
**目的**: Intent BridgeにContext Assemblerを統合し、Claude APIとの対話に文脈（過去の会話履歴・関連記憶）を自動的に含める
**期間**: 4日間
**担当**: Tsumu (Cursor) + Kana (Claude Sonnet 4.5)

---

## 🎯 ゴール

### ビフォー（現状）
```python
# Intent Bridge → Claude API（直接）
messages = [{"role": "user", "content": "今のメッセージだけ"}]
→ Claudeは毎回ゼロリセット（金魚の記憶）
```

### アフター（統合後）
```python
# Intent Bridge → KanaAIBridge → Context Assembler → Claude API
messages = [
    {"role": "user", "content": "過去のメッセージ1"},
    {"role": "assistant", "content": "過去の応答1"},
    {"role": "user", "content": "今のメッセージ"}  # 文脈を保持
]
→ Claudeが過去を記憶して応答
```

---

## 📊 前提確認

### 実装済みコンポーネント（Sprint 5）
- ✅ Context Assembler Service (`context_assembler/service.py`)
- ✅ KanaAIBridge統合 (`bridge/providers/ai/kana_ai_bridge.py`)
- ✅ Token Estimator (`context_assembler/token_estimator.py`)
- ✅ Models (`context_assembler/models.py`)

### 確認すべき依存関係
```bash
# Memory Store実装確認
ls -la memory_store/repository.py
ls -la memory_store/models.py

# Retrieval Orchestrator実装確認
ls -la retrieval/orchestrator.py

# PostgreSQLテーブル確認
psql -U postgres -d resonant_engine -c "\dt messages"
psql -U postgres -d resonant_engine -c "\dt memories"
```

**⚠️ 重要:** Memory StoreまたはRetrieval Orchestratorが未実装の場合、Mockを使用して進める。

---

## 🗓️ 実装スケジュール

### Day 1: Factory層実装
**所要時間**: 3-4時間

1. Context Assembler Factory実装
2. BridgeFactory拡張
3. 単体テスト（Factory層）

### Day 2: Intent Bridge修正
**所要時間**: 3-4時間

1. processor.py修正
2. 単体テスト（Intent Bridge）

### Day 3: 統合テスト
**所要時間**: 4-5時間

1. E2Eテスト実装
2. 受け入れテスト実行

### Day 4: レビューと修正
**所要時間**: 2-3時間

1. コードレビュー
2. バグ修正
3. ドキュメント更新

---

## 📝 Day 1: Factory層実装

### タスク1-1: Context Assembler Factory実装

**ファイル**: `context_assembler/factory.py` (新規作成)

**実装内容**:

```python
"""Context Assembler Factory - 依存関係注入層"""

import asyncpg
import os
from typing import Optional

from context_assembler.service import ContextAssemblerService
from context_assembler.config import get_default_config, ContextConfig


def get_database_url() -> str:
    """環境変数からデータベースURLを取得"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Example: postgresql://user:password@localhost:5432/resonant_engine"
        )
    return url


async def create_context_assembler(
    pool: Optional[asyncpg.Pool] = None,
    config: Optional[ContextConfig] = None,
) -> ContextAssemblerService:
    """
    Context Assemblerインスタンスを生成

    Args:
        pool: PostgreSQL接続プール（Noneの場合は新規作成）
        config: Context設定（Noneの場合はデフォルト）

    Returns:
        ContextAssemblerService: 初期化済みインスタンス

    Raises:
        ConnectionError: データベース接続失敗
        ValueError: 依存関係の初期化失敗
        ImportError: 必須モジュール未インストール
    """
    # 1. データベース接続プール
    if pool is None:
        database_url = get_database_url()
        try:
            pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                timeout=30,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create database pool: {e}") from e

    # 2. リポジトリ初期化
    try:
        from memory_store.repository import MessageRepository, MemoryRepository
    except ImportError as e:
        raise ImportError(
            "Memory Store repositories not found. "
            "Please implement memory_store/repository.py or use Mock."
        ) from e

    message_repo = MessageRepository(pool)
    memory_repo = MemoryRepository(pool)

    # 3. Retrieval Orchestrator初期化
    try:
        from retrieval.orchestrator import RetrievalOrchestrator
    except ImportError as e:
        raise ImportError(
            "Retrieval Orchestrator not found. "
            "Please implement retrieval/orchestrator.py or use Mock."
        ) from e

    retrieval = RetrievalOrchestrator(memory_repo=memory_repo)

    # 4. Context Assembler初期化
    return ContextAssemblerService(
        message_repo=message_repo,
        retrieval=retrieval,
        config=config or get_default_config(),
    )
```

**検証**:
```bash
# Pythonインタラクティブで確認
cd /home/user/resonant-engine
source venv/bin/activate
python3 -c "
import asyncio
from context_assembler.factory import create_context_assembler

async def test():
    ca = await create_context_assembler()
    print(f'✅ Context Assembler created: {ca}')

asyncio.run(test())
"
```

### タスク1-2: BridgeFactory拡張

**ファイル**: `bridge/factory/bridge_factory.py` (既存ファイル修正)

**変更内容**:

```python
# 既存のインポートに追加
from typing import Optional
import asyncpg

# ... 既存コード ...

class BridgeFactory:
    """Bridge実装を環境変数ベースで生成するファクトリ。"""

    # ... 既存メソッド（create_data_bridge, create_ai_bridge等）...

    @staticmethod
    async def create_ai_bridge_with_memory(
        bridge_type: Optional[str] = None,
        pool: Optional[asyncpg.Pool] = None,
    ) -> AIBridge:
        """
        Context Assembler統合版のAI Bridgeを生成

        Args:
            bridge_type: "kana", "claude", "mock"（デフォルト: 環境変数AI_BRIDGE_TYPE）
            pool: PostgreSQL接続プール（Noneの場合はFactoryが新規作成）

        Returns:
            AIBridge: Context Assembler統合済みのAI Bridge

        Raises:
            ValueError: 未対応のbridge_type
            ConnectionError: Context Assembler初期化失敗
        """
        from context_assembler.factory import create_context_assembler

        bridge_key = (bridge_type or os.getenv("AI_BRIDGE_TYPE", "kana")).lower()

        if bridge_key in {"kana", "claude"}:
            # Context Assembler初期化
            try:
                context_assembler = await create_context_assembler(pool=pool)
            except (ConnectionError, ValueError, ImportError) as e:
                # Context Assembler初期化失敗 → Fallback（Context Assemblerなし）
                import warnings
                warnings.warn(
                    f"Context Assembler initialization failed: {e}. "
                    f"Falling back to KanaAIBridge without context memory."
                )
                return KanaAIBridge()  # context_assembler=None

            return KanaAIBridge(context_assembler=context_assembler)

        if bridge_key == "mock":
            # Mockは従来通り（Context Assemblerなし）
            return MockAIBridge()

        raise ValueError(f"Unsupported AI_BRIDGE_TYPE: {bridge_key}")
```

**検証**:
```python
# tests/bridge/test_factory_integration.py (新規)
import pytest
from bridge.factory.bridge_factory import BridgeFactory


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory():
    """Context Assembler統合版AI Bridgeの生成"""
    bridge = await BridgeFactory.create_ai_bridge_with_memory("kana")
    assert bridge is not None
    assert hasattr(bridge, "process_intent")


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_mock():
    """Mock Bridge生成（Context Assemblerなし）"""
    bridge = await BridgeFactory.create_ai_bridge_with_memory("mock")
    assert bridge is not None
```

### タスク1-3: 単体テスト（Factory層）

**ファイル**: `tests/context_assembler/test_factory.py` (新規作成)

**実装内容**:

```python
"""Context Assembler Factory単体テスト"""

import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock, patch

from context_assembler.factory import (
    create_context_assembler,
    get_database_url,
)
from context_assembler.service import ContextAssemblerService


def test_get_database_url_success(monkeypatch):
    """環境変数からURL取得成功"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    url = get_database_url()
    assert url == "postgresql://localhost/test"


def test_get_database_url_missing(monkeypatch):
    """環境変数未設定時にエラー"""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        get_database_url()


@pytest.mark.asyncio
async def test_create_context_assembler_with_pool():
    """既存プールでContext Assembler生成"""
    # Mock pool
    mock_pool = AsyncMock(spec=asyncpg.Pool)

    # Mock repositories
    with patch("context_assembler.factory.MessageRepository") as mock_msg_repo, \
         patch("context_assembler.factory.MemoryRepository") as mock_mem_repo, \
         patch("context_assembler.factory.RetrievalOrchestrator") as mock_retrieval:

        ca = await create_context_assembler(pool=mock_pool)

        assert isinstance(ca, ContextAssemblerService)
        mock_msg_repo.assert_called_once_with(mock_pool)
        mock_mem_repo.assert_called_once_with(mock_pool)


@pytest.mark.asyncio
async def test_create_context_assembler_import_error():
    """依存関係インポート失敗時にエラー"""
    mock_pool = AsyncMock(spec=asyncpg.Pool)

    with patch("context_assembler.factory.MessageRepository", side_effect=ImportError):
        with pytest.raises(ImportError, match="Memory Store"):
            await create_context_assembler(pool=mock_pool)


@pytest.mark.asyncio
async def test_create_context_assembler_connection_error(monkeypatch):
    """DB接続失敗時にエラー"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid")

    with patch("asyncpg.create_pool", side_effect=Exception("Connection failed")):
        with pytest.raises(ConnectionError, match="Failed to create database pool"):
            await create_context_assembler()
```

**実行**:
```bash
cd /home/user/resonant-engine
source venv/bin/activate
pytest tests/context_assembler/test_factory.py -v
```

---

## 📝 Day 2: Intent Bridge修正

### タスク2-1: processor.py修正

**ファイル**: `intent_bridge/intent_bridge/processor.py` (既存ファイル修正)

**変更手順**:

#### ステップ1: インポート追加

```python
# ファイル冒頭に追加
from typing import Optional
```

#### ステップ2: `__init__` 修正

```python
# Before
def __init__(self, pool, config):
    self.pool = pool
    self.config = config
    self.claude = None  # ❌ 削除

    # Initialize Claude client if API key is available
    if config.get('anthropic_api_key'):
        try:
            import anthropic
            self.claude = anthropic.Anthropic(
                api_key=config['anthropic_api_key']
            )
        except ImportError:
            logger.warning("Anthropic package not installed, using mock response")

# After
def __init__(self, pool, config):
    self.pool = pool
    self.config = config
    self.ai_bridge = None  # ✅ KanaAIBridgeを格納
```

#### ステップ3: `initialize` メソッド追加

```python
async def initialize(self):
    """非同期初期化: KanaAIBridge（Context Assembler統合）を生成"""
    from bridge.factory.bridge_factory import BridgeFactory

    try:
        self.ai_bridge = await BridgeFactory.create_ai_bridge_with_memory(
            bridge_type="kana",
            pool=self.pool,
        )
        logger.info("✅ KanaAIBridge initialized with Context Assembler")
    except Exception as e:
        logger.error(f"❌ Failed to initialize KanaAIBridge: {e}")
        raise
```

#### ステップ4: `process` メソッド修正

```python
async def process(self, intent_id):
    # 初回呼び出し時のみ初期化
    if self.ai_bridge is None:
        await self.initialize()

    async with self.pool.acquire() as conn:
        # 1. Intent取得
        intent = await conn.fetchrow(
            "SELECT * FROM intents WHERE id = $1",
            intent_id
        )

        if not intent:
            logger.warning(f"⚠️ Intent {intent_id} not found")
            return

        # 2. ステータス更新: processing
        await conn.execute("""
            UPDATE intents
            SET status = 'processing', updated_at = NOW()
            WHERE id = $1
        """, intent_id)

        try:
            # 3. KanaAIBridge経由でClaude API呼び出し
            logger.info(f"🤖 Processing intent via KanaAIBridge...")
            response = await self.call_claude(
                description=intent['description'],
                user_id=intent.get('user_id', 'hiroki'),
                session_id=intent.get('session_id'),
            )

            # 4. 結果保存（metadata含む）
            result_data = {
                "response": response["response"],
                "model": response["model"],
                "usage": response.get("usage", {}),
                "context_metadata": response.get("context_metadata"),  # NEW
                "processed_at": response["processed_at"],
            }

            await conn.execute("""
                UPDATE intents
                SET status = 'completed',
                    result = $1::jsonb,
                    processed_at = NOW(),
                    updated_at = NOW()
                WHERE id = $2
            """, json.dumps(result_data), intent_id)

            # 5. 通知作成
            await self.create_notification(conn, intent_id, 'success')

            logger.info(f"✅ Intent {intent_id} processed successfully")
            if response.get("context_metadata"):
                logger.info(
                    f"📊 Context: WM={response['context_metadata']['working_memory_count']}, "
                    f"SM={response['context_metadata']['semantic_memory_count']}"
                )

        except Exception as e:
            logger.error(f"Error processing intent: {e}")
            await conn.execute("""
                UPDATE intents
                SET status = 'failed',
                    result = $1::jsonb,
                    updated_at = NOW()
                WHERE id = $2
            """, json.dumps({"error": str(e)}), intent_id)

            await self.create_notification(conn, intent_id, 'error')
            logger.error(f"❌ Intent {intent_id} failed: {e}")
```

#### ステップ5: `call_claude` メソッド完全書き換え

```python
# 完全に置き換え
async def call_claude(
    self,
    description: str,
    user_id: str = "hiroki",
    session_id: Optional[str] = None,
):
    """
    KanaAIBridge経由でClaude APIを呼び出し（Context Assembler統合）

    Args:
        description: Intent内容
        user_id: ユーザーID
        session_id: セッションID（オプション）

    Returns:
        dict: {
            "response": str,
            "model": str,
            "usage": dict,
            "context_metadata": dict,  # Context Assemblerメタデータ
            "processed_at": str,
        }
    """
    if self.ai_bridge:
        try:
            # KanaAIBridge.process_intent()を呼び出し
            result = await self.ai_bridge.process_intent({
                "content": description,
                "user_id": user_id,
                "session_id": session_id,
            })

            # レスポンス整形
            return {
                "response": result.get("summary", ""),
                "model": result.get("model", "unknown"),
                "usage": result.get("usage", {}),
                "context_metadata": result.get("context_metadata"),
                "processed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"KanaAIBridge error: {e}")
            raise

    # Fallback: Mock応答（ai_bridgeが初期化失敗した場合のみ）
    logger.warning("⚠️ Using mock response (KanaAIBridge not initialized)")
    return {
        "response": f"[Mock Response] Intent processed: {description[:100]}",
        "model": "mock",
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "context_metadata": None,
        "processed_at": datetime.utcnow().isoformat(),
    }
```

### タスク2-2: 単体テスト（Intent Bridge）

**ファイル**: `tests/intent_bridge/test_processor_integration.py` (新規作成)

```python
"""Intent Bridge - Context Assembler統合テスト"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from intent_bridge.intent_bridge.processor import IntentProcessor


@pytest.fixture
def mock_pool():
    """Mock PostgreSQL pool"""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool, conn


@pytest.fixture
def mock_config():
    """Mock config"""
    return {
        "anthropic_api_key": "sk-ant-test",
    }


@pytest.mark.asyncio
async def test_initialize_success(mock_pool, mock_config):
    """KanaAIBridge初期化成功"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_factory.return_value = mock_bridge

        await processor.initialize()

        assert processor.ai_bridge is not None
        mock_factory.assert_called_once_with(bridge_type="kana", pool=pool)


@pytest.mark.asyncio
async def test_call_claude_with_context(mock_pool, mock_config):
    """Context Assembler経由でClaude呼び出し"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)

    # Mock KanaAIBridge
    mock_bridge = AsyncMock()
    mock_bridge.process_intent.return_value = {
        "summary": "Memory Store Sprint 2が完了しています",
        "model": "claude-sonnet-4-20250514",
        "usage": {"input_tokens": 100, "output_tokens": 150},
        "context_metadata": {
            "working_memory_count": 10,
            "semantic_memory_count": 5,
            "total_tokens": 3240,
        },
    }
    processor.ai_bridge = mock_bridge

    # 実行
    result = await processor.call_claude(
        description="Memory Storeの実装状況は？",
        user_id="hiroki",
    )

    # 検証
    assert result["response"] == "Memory Store Sprint 2が完了しています"
    assert result["model"] == "claude-sonnet-4-20250514"
    assert result["context_metadata"]["working_memory_count"] == 10
    assert result["context_metadata"]["semantic_memory_count"] == 5

    mock_bridge.process_intent.assert_called_once_with({
        "content": "Memory Storeの実装状況は？",
        "user_id": "hiroki",
        "session_id": None,
    })


@pytest.mark.asyncio
async def test_call_claude_fallback(mock_pool, mock_config):
    """ai_bridgeが未初期化時にMock応答"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)
    processor.ai_bridge = None  # 未初期化

    result = await processor.call_claude("Test intent")

    assert result["response"].startswith("[Mock Response]")
    assert result["model"] == "mock"
    assert result["context_metadata"] is None


@pytest.mark.asyncio
async def test_process_intent_with_context(mock_pool, mock_config):
    """Intent処理全体（Context Assembler統合）"""
    pool, conn = mock_pool
    processor = IntentProcessor(pool, mock_config)

    # Mock intent
    intent_id = uuid4()
    conn.fetchrow.return_value = {
        "id": intent_id,
        "description": "Context Assemblerについて教えて",
        "user_id": "hiroki",
        "session_id": None,
    }

    # Mock KanaAIBridge
    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_bridge.process_intent.return_value = {
            "summary": "Context Assemblerは3層記憶統合サービスです",
            "model": "claude-sonnet-4-20250514",
            "context_metadata": {"working_memory_count": 5, "semantic_memory_count": 3},
        }
        mock_factory.return_value = mock_bridge

        # 実行
        await processor.process(intent_id)

        # 検証: context_metadataが保存されていることを確認
        update_call = [c for c in conn.execute.call_args_list if "completed" in str(c)]
        assert len(update_call) > 0
```

**実行**:
```bash
pytest tests/intent_bridge/test_processor_integration.py -v
```

---

## 📝 Day 3: 統合テスト

### タスク3-1: E2Eテスト実装

**ファイル**: `tests/integration/test_intent_bridge_e2e.py` (新規作成)

```python
"""Intent Bridge E2E統合テスト（Context Assembler統合）"""

import pytest
import asyncpg
from uuid import uuid4
from datetime import datetime

from intent_bridge.intent_bridge.processor import IntentProcessor


@pytest.fixture
async def db_pool():
    """実際のデータベース接続（テスト用）"""
    pool = await asyncpg.create_pool(
        "postgresql://postgres:password@localhost:5432/resonant_engine_test"
    )
    yield pool
    await pool.close()


@pytest.fixture
async def setup_test_data(db_pool):
    """テストデータ準備"""
    async with db_pool.acquire() as conn:
        # テーブルクリア
        await conn.execute("DELETE FROM intents")
        await conn.execute("DELETE FROM messages")
        await conn.execute("DELETE FROM notifications")

        # サンプルメッセージ挿入（Working Memory用）
        await conn.execute("""
            INSERT INTO messages (id, user_id, role, content, created_at)
            VALUES
                ($1, 'hiroki', 'user', 'Memory Storeについて教えて', NOW() - INTERVAL '10 minutes'),
                ($2, 'hiroki', 'assistant', 'Memory Storeはpgvectorベースの...', NOW() - INTERVAL '9 minutes')
        """, uuid4(), uuid4())

    yield
    # クリーンアップ
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM intents")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_intent_processing_with_context(db_pool, setup_test_data):
    """Intent処理でContext Assemblerが使われることを確認"""

    config = {"anthropic_api_key": "sk-ant-test"}  # 実際のキーを使用
    processor = IntentProcessor(db_pool, config)

    # Intent作成
    intent_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'hiroki', $2, 'pending', NOW())
        """, intent_id, "Context Assemblerの統合状況は？")

    # 処理実行
    await processor.process(intent_id)

    # 結果確認
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT status, result FROM intents WHERE id = $1",
            intent_id
        )

        assert result["status"] == "completed"
        result_json = result["result"]

        # Context metadataが含まれていることを確認
        assert "context_metadata" in result_json
        assert result_json["context_metadata"] is not None
        assert result_json["context_metadata"]["working_memory_count"] >= 0
        assert result_json["context_metadata"]["semantic_memory_count"] >= 0

        # 応答内容の検証
        assert len(result_json["response"]) > 0
        assert result_json["model"].startswith("claude")
```

### タスク3-2: 受け入れテスト実行

**ファイル**: `tests/acceptance/test_sprint6_acceptance.py` (Day 3で作成)

詳細は次のドキュメント（受け入れテスト仕様書）で定義。

---

## 📝 Day 4: レビューと修正

### チェックリスト

#### コード品質
- [ ] 型ヒント（Type Hints）を全関数に追加
- [ ] Docstringを全関数に記載
- [ ] ログ出力が適切（INFO, WARNING, ERROR）
- [ ] エラーハンドリングが適切

#### テスト
- [ ] 単体テスト全件PASS
- [ ] E2Eテスト全件PASS
- [ ] 受け入れテスト全件PASS
- [ ] カバレッジ80%以上

#### ドキュメント
- [ ] README更新（統合手順追加）
- [ ] 環境変数一覧更新
- [ ] コメント追加（複雑なロジック）

---

## 🔧 環境設定

### 必須環境変数

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
DATABASE_URL=postgresql://postgres:password@localhost:5432/resonant_engine
AI_BRIDGE_TYPE=kana
```

### Python依存関係

```bash
# 既存
pip install asyncpg anthropic pydantic

# 追加確認
pip list | grep -E "asyncpg|anthropic|pydantic"
```

---

## 🐛 トラブルシューティング

### 問題1: Memory Store/Retrieval未実装

**エラー**:
```
ImportError: Memory Store repositories not found
```

**対策**:
1. Mock実装を使用
2. または Sprint 1-4のMemory Store実装を確認

### 問題2: データベース接続失敗

**エラー**:
```
ConnectionError: Failed to create database pool
```

**対策**:
```bash
# PostgreSQL起動確認
pg_ctl status

# データベース存在確認
psql -U postgres -l | grep resonant_engine

# 接続テスト
psql -U postgres -d resonant_engine -c "SELECT 1"
```

### 問題3: Context組み立て失敗

**エラー**:
```
Context assembly failed: ...
```

**対策**:
KanaAIBridgeが自動的にFallbackするため、警告ログを確認:
```python
warnings.warn(f"Context assembly failed: {e}, falling back to simple mode")
```

---

## 📊 成功指標

### 実装完了判定
- [ ] Context Assembler Factory実装完了
- [ ] BridgeFactory拡張完了
- [ ] Intent Bridge修正完了
- [ ] 単体テスト16件全てPASS
- [ ] E2Eテスト3件全てPASS
- [ ] 受け入れテスト14件全てPASS

### 動作確認
```bash
# Intent作成
curl -X POST http://localhost:8000/api/intents \
  -H "Content-Type: application/json" \
  -d '{"description": "Memory Storeについて教えて", "user_id": "hiroki"}'

# 結果確認（context_metadataが含まれること）
curl http://localhost:8000/api/intents/{intent_id}
```

---

## 📚 参考資料

- [Sprint 6仕様書](../architecture/sprint6_intent_bridge_integration_spec.md)
- [Sprint 5 Context Assembler](../architecture/sprint5_context_assembler_spec.md)
- [KanaAIBridge実装](../../../bridge/providers/ai/kana_ai_bridge.py)
- [Context Assemblerデモ](../../../examples/context_assembler_demo.py)

---

## ✅ 作業開始前の最終確認

```bash
# 1. ブランチ確認
git branch
# → claude/add-conversation-memory-017fnuDD9kLAQh58XR9AKmwB

# 2. 依存関係確認
ls -la memory_store/repository.py
ls -la retrieval/orchestrator.py

# 3. 環境変数確認
echo $DATABASE_URL
echo $ANTHROPIC_API_KEY

# 4. データベース確認
psql -U postgres -d resonant_engine -c "\dt"
```

**全て確認できたら Day 1 開始！**
