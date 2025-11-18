# Sprint 6: Intent Bridge - Context Assembler統合 受け入れテスト仕様書

## 📋 概要

**Sprint**: Sprint 6
**テスト対象**: Intent Bridge - Context Assembler統合
**テスト件数**: 14件
**実行環境**: PostgreSQL + Intent Bridge + KanaAIBridge + Context Assembler

---

## 🎯 テスト方針

### 検証レベル
1. **Unit（単体）**: Factory, BridgeFactory, Intent Bridgeの個別機能
2. **Integration（統合）**: コンポーネント間連携
3. **E2E（End-to-End）**: Intent作成 → 処理 → 結果確認（実DB）
4. **Acceptance（受け入れ）**: ユーザー要求の充足確認

### 合格基準
- 全14テストケース PASS
- カバレッジ 80%以上
- 重大な既知のバグなし

---

## 📝 テストケース一覧

| ID | カテゴリ | テスト名 | 優先度 |
|----|---------|---------|--------|
| TC-01 | Unit | Context Assembler Factory: 正常系 | P1 |
| TC-02 | Unit | Context Assembler Factory: DB接続失敗 | P1 |
| TC-03 | Unit | Context Assembler Factory: 依存関係エラー | P2 |
| TC-04 | Unit | BridgeFactory: Context Assembler統合版生成 | P1 |
| TC-05 | Unit | BridgeFactory: Fallback（Context Assembler失敗） | P1 |
| TC-06 | Unit | Intent Bridge: KanaAIBridge初期化 | P1 |
| TC-07 | Unit | Intent Bridge: call_claude（Context付き） | P1 |
| TC-08 | Unit | Intent Bridge: call_claude（Fallback） | P2 |
| TC-09 | Integration | Intent処理全体（Context Assembler統合） | P1 |
| TC-10 | Integration | Context metadata保存確認 | P1 |
| TC-11 | E2E | Intent処理E2E（実DB、文脈あり） | P1 |
| TC-12 | E2E | 連続Intent処理（文脈継続） | P1 |
| TC-13 | Acceptance | ユーザー体験改善確認 | P1 |
| TC-14 | Acceptance | PostgreSQLデータ活用率確認 | P1 |

---

## 🧪 テストケース詳細

### TC-01: Context Assembler Factory - 正常系

**目的**: Context Assembler Factoryが正常にインスタンスを生成できることを確認

**前提条件**:
- PostgreSQL起動中
- DATABASE_URL環境変数設定済み
- Memory Store, Retrieval Orchestrator実装済み

**テスト手順**:
```python
import asyncio
import asyncpg
from context_assembler.factory import create_context_assembler

async def test():
    # 1. 接続プール作成
    pool = await asyncpg.create_pool(
        "postgresql://postgres:password@localhost:5432/resonant_engine"
    )

    # 2. Context Assembler生成
    ca = await create_context_assembler(pool=pool)

    # 3. 検証
    assert ca is not None
    assert hasattr(ca, "assemble_context")
    assert hasattr(ca, "message_repo")
    assert hasattr(ca, "retrieval")

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ Context Assemblerインスタンス生成成功
- ✅ message_repo, retrieval属性が存在
- ✅ エラーなし

**テストコード**: `tests/context_assembler/test_factory.py::test_create_context_assembler_with_pool`

---

### TC-02: Context Assembler Factory - DB接続失敗

**目的**: データベース接続失敗時に適切なエラーが発生することを確認

**前提条件**:
- PostgreSQL停止中 または 無効なDATABASE_URL

**テスト手順**:
```python
import pytest
from context_assembler.factory import create_context_assembler

@pytest.mark.asyncio
async def test_db_connection_error(monkeypatch):
    # 無効なURL設定
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid:5432/test")

    # 実行
    with pytest.raises(ConnectionError, match="Failed to create database pool"):
        await create_context_assembler()
```

**期待結果**:
- ✅ `ConnectionError` 例外発生
- ✅ エラーメッセージに "Failed to create database pool" 含む

**テストコード**: `tests/context_assembler/test_factory.py::test_create_context_assembler_connection_error`

---

### TC-03: Context Assembler Factory - 依存関係エラー

**目的**: Memory Store等の依存関係が未実装時に適切なエラーが発生することを確認

**前提条件**:
- Memory Store未実装（ImportError発生状態）

**テスト手順**:
```python
import pytest
from unittest.mock import patch
from context_assembler.factory import create_context_assembler

@pytest.mark.asyncio
async def test_import_error():
    # MessageRepositoryのインポート失敗を模擬
    with patch("context_assembler.factory.MessageRepository", side_effect=ImportError):
        with pytest.raises(ImportError, match="Memory Store"):
            await create_context_assembler(pool=mock_pool)
```

**期待結果**:
- ✅ `ImportError` 例外発生
- ✅ エラーメッセージに "Memory Store" 含む

**テストコード**: `tests/context_assembler/test_factory.py::test_create_context_assembler_import_error`

---

### TC-04: BridgeFactory - Context Assembler統合版生成

**目的**: BridgeFactoryがContext Assembler統合版KanaAIBridgeを生成できることを確認

**前提条件**:
- PostgreSQL起動中
- AI_BRIDGE_TYPE=kana

**テスト手順**:
```python
import pytest
from bridge.factory.bridge_factory import BridgeFactory

@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory():
    # 実行
    bridge = await BridgeFactory.create_ai_bridge_with_memory("kana")

    # 検証
    assert bridge is not None
    assert hasattr(bridge, "process_intent")
    assert hasattr(bridge, "_context_assembler")
    assert bridge._context_assembler is not None
```

**期待結果**:
- ✅ KanaAIBridgeインスタンス生成成功
- ✅ `_context_assembler` 属性が存在
- ✅ `_context_assembler` がNoneでない

**テストコード**: `tests/bridge/test_factory_integration.py::test_create_ai_bridge_with_memory`

---

### TC-05: BridgeFactory - Fallback（Context Assembler失敗）

**目的**: Context Assembler初期化失敗時にFallbackすることを確認

**前提条件**:
- PostgreSQL停止中（Context Assembler初期化失敗状態）

**テスト手順**:
```python
import pytest
import warnings
from bridge.factory.bridge_factory import BridgeFactory

@pytest.mark.asyncio
async def test_fallback_on_context_assembler_failure(monkeypatch):
    # 無効なDATABASE_URL
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid:5432/test")

    # 実行（警告を捕捉）
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        bridge = await BridgeFactory.create_ai_bridge_with_memory("kana")

        # 検証
        assert bridge is not None  # Fallback成功
        assert len(w) > 0  # 警告発生
        assert "Context Assembler initialization failed" in str(w[0].message)
        assert bridge._context_assembler is None  # Context Assemblerなし
```

**期待結果**:
- ✅ KanaAIBridgeインスタンス生成成功（Fallback）
- ✅ 警告発生
- ✅ `_context_assembler` がNone

**テストコード**: `tests/bridge/test_factory_integration.py::test_create_ai_bridge_fallback`

---

### TC-06: Intent Bridge - KanaAIBridge初期化

**目的**: Intent BridgeがKanaAIBridgeを正しく初期化できることを確認

**前提条件**:
- PostgreSQL起動中
- ANTHROPIC_API_KEY設定済み

**テスト手順**:
```python
import pytest
from unittest.mock import AsyncMock, patch
from intent_bridge.intent_bridge.processor import IntentProcessor

@pytest.mark.asyncio
async def test_initialize_success():
    mock_pool = AsyncMock()
    config = {"anthropic_api_key": "sk-ant-test"}
    processor = IntentProcessor(mock_pool, config)

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_factory.return_value = mock_bridge

        # 実行
        await processor.initialize()

        # 検証
        assert processor.ai_bridge is not None
        assert processor.ai_bridge == mock_bridge
        mock_factory.assert_called_once_with(bridge_type="kana", pool=mock_pool)
```

**期待結果**:
- ✅ `processor.ai_bridge` がセットされる
- ✅ `BridgeFactory.create_ai_bridge_with_memory()` が呼ばれる

**テストコード**: `tests/intent_bridge/test_processor_integration.py::test_initialize_success`

---

### TC-07: Intent Bridge - call_claude（Context付き）

**目的**: `call_claude()` がKanaAIBridge経由で正しく動作することを確認

**前提条件**:
- Intent Bridge初期化済み（ai_bridgeセット）

**テスト手順**:
```python
import pytest
from unittest.mock import AsyncMock
from intent_bridge.intent_bridge.processor import IntentProcessor

@pytest.mark.asyncio
async def test_call_claude_with_context():
    mock_pool = AsyncMock()
    config = {}
    processor = IntentProcessor(mock_pool, config)

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

    # process_intent呼び出し確認
    mock_bridge.process_intent.assert_called_once_with({
        "content": "Memory Storeの実装状況は？",
        "user_id": "hiroki",
        "session_id": None,
    })
```

**期待結果**:
- ✅ KanaAIBridge.process_intent() が呼ばれる
- ✅ context_metadataが返される
- ✅ 応答内容が正しい

**テストコード**: `tests/intent_bridge/test_processor_integration.py::test_call_claude_with_context`

---

### TC-08: Intent Bridge - call_claude（Fallback）

**目的**: ai_bridge未初期化時にMock応答を返すことを確認

**前提条件**:
- Intent Bridge未初期化（ai_bridge=None）

**テスト手順**:
```python
import pytest
from intent_bridge.intent_bridge.processor import IntentProcessor

@pytest.mark.asyncio
async def test_call_claude_fallback():
    mock_pool = AsyncMock()
    config = {}
    processor = IntentProcessor(mock_pool, config)
    processor.ai_bridge = None  # 未初期化

    # 実行
    result = await processor.call_claude("Test intent")

    # 検証
    assert result["response"].startswith("[Mock Response]")
    assert result["model"] == "mock"
    assert result["context_metadata"] is None
```

**期待結果**:
- ✅ Mock応答が返される
- ✅ model="mock"
- ✅ context_metadata=None

**テストコード**: `tests/intent_bridge/test_processor_integration.py::test_call_claude_fallback`

---

### TC-09: Integration - Intent処理全体（Context Assembler統合）

**目的**: Intent処理の全フロー（取得→処理→保存）が動作することを確認

**前提条件**:
- PostgreSQL起動中
- テストIntent挿入済み

**テスト手順**:
```python
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from intent_bridge.intent_bridge.processor import IntentProcessor

@pytest.mark.asyncio
async def test_process_intent_with_context():
    mock_pool = AsyncMock()
    conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = conn

    config = {}
    processor = IntentProcessor(mock_pool, config)

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
            "context_metadata": {
                "working_memory_count": 5,
                "semantic_memory_count": 3,
                "total_tokens": 2500,
            },
        }
        mock_factory.return_value = mock_bridge

        # 実行
        await processor.process(intent_id)

        # 検証: status='completed' で更新されること
        update_calls = [
            call for call in conn.execute.call_args_list
            if "completed" in str(call)
        ]
        assert len(update_calls) > 0

        # 検証: context_metadataが保存されること
        result_json_arg = update_calls[0][0][1]
        import json
        result_data = json.loads(result_json_arg)
        assert "context_metadata" in result_data
        assert result_data["context_metadata"]["working_memory_count"] == 5
```

**期待結果**:
- ✅ Intent status="completed"
- ✅ result.context_metadataが保存される
- ✅ 通知作成される

**テストコード**: `tests/intent_bridge/test_processor_integration.py::test_process_intent_with_context`

---

### TC-10: Integration - Context metadata保存確認

**目的**: IntentのresultにContext metadataが正しく保存されることを確認

**前提条件**:
- TC-09実行済み

**テスト手順**:
```python
# TC-09の延長
# result JSONの構造を詳細検証

result_data = {
    "response": "...",
    "model": "claude-sonnet-4-20250514",
    "usage": {...},
    "context_metadata": {
        "working_memory_count": 5,
        "semantic_memory_count": 3,
        "has_session_summary": False,
        "total_tokens": 2500,
        "compression_applied": False,
    },
    "processed_at": "2025-11-18T10:00:00Z",
}

assert "context_metadata" in result_data
assert isinstance(result_data["context_metadata"], dict)
assert "working_memory_count" in result_data["context_metadata"]
assert "semantic_memory_count" in result_data["context_metadata"]
assert "total_tokens" in result_data["context_metadata"]
```

**期待結果**:
- ✅ result.context_metadataが存在
- ✅ 必須フィールド全て存在
- ✅ 型が正しい（dict）

**テストコード**: `tests/intent_bridge/test_processor_integration.py::test_context_metadata_save`

---

### TC-11: E2E - Intent処理E2E（実DB、文脈あり）

**目的**: 実際のデータベースを使用した完全なIntent処理フローを確認

**前提条件**:
- PostgreSQL起動中（テストDB）
- テーブル作成済み（intents, messages, memories, notifications）
- ANTHROPIC_API_KEY設定済み（実際のAPIキー）

**テスト手順**:
```python
import pytest
import asyncpg
from uuid import uuid4
from intent_bridge.intent_bridge.processor import IntentProcessor

@pytest.fixture
async def db_pool():
    pool = await asyncpg.create_pool(
        "postgresql://postgres:password@localhost:5432/resonant_engine_test"
    )
    yield pool
    await pool.close()

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_intent_processing_e2e(db_pool):
    # 1. テストデータ準備
    async with db_pool.acquire() as conn:
        # メッセージ挿入（Working Memory用）
        await conn.execute("""
            INSERT INTO messages (id, user_id, role, content, created_at)
            VALUES
                ($1, 'hiroki', 'user', 'Memory Storeについて教えて', NOW() - INTERVAL '10 minutes'),
                ($2, 'hiroki', 'assistant', 'Memory Storeはpgvectorベースの...', NOW() - INTERVAL '9 minutes')
        """, uuid4(), uuid4())

    # 2. Intent作成
    intent_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'hiroki', $2, 'pending', NOW())
        """, intent_id, "Context Assemblerの統合状況は？")

    # 3. 処理実行
    config = {"anthropic_api_key": "sk-ant-..."}  # 実際のキー
    processor = IntentProcessor(db_pool, config)
    await processor.process(intent_id)

    # 4. 結果確認
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
        assert result_json["context_metadata"]["working_memory_count"] >= 2  # 2件以上
        assert result_json["context_metadata"]["semantic_memory_count"] >= 0

        # 応答内容の検証
        assert len(result_json["response"]) > 0
        assert result_json["model"].startswith("claude")
```

**期待結果**:
- ✅ Intent status="completed"
- ✅ result.context_metadataが含まれる
- ✅ working_memory_count >= 2（事前に挿入した2件以上）
- ✅ Claudeからの応答が返る

**テストコード**: `tests/integration/test_intent_bridge_e2e.py::test_intent_processing_e2e`

---

### TC-12: E2E - 連続Intent処理（文脈継続）

**目的**: 連続するIntentで文脈が継続されることを確認

**前提条件**:
- TC-11実行済み

**テスト手順**:
```python
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_continuous_intent_processing(db_pool):
    config = {"anthropic_api_key": "sk-ant-..."}
    processor = IntentProcessor(db_pool, config)

    # 1回目: Memory Storeについて質問
    intent_id_1 = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'hiroki', 'Memory Storeの実装状況を教えて', 'pending', NOW())
        """, intent_id_1)

    await processor.process(intent_id_1)

    # 2回目: 「それ」で参照（文脈を保持しているか確認）
    intent_id_2 = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'hiroki', 'それのベクトル検索機能について詳しく', 'pending', NOW())
        """, intent_id_2)

    await processor.process(intent_id_2)

    # 結果確認
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT result FROM intents WHERE id = $1",
            intent_id_2
        )

        result_json = result["result"]

        # Working Memoryに1回目の会話が含まれていることを確認
        assert result_json["context_metadata"]["working_memory_count"] >= 2

        # 応答内容に「Memory Store」または「pgvector」が含まれることを期待
        # （文脈を理解して応答している証拠）
        response_text = result_json["response"].lower()
        assert "memory" in response_text or "vector" in response_text or "pgvector" in response_text
```

**期待結果**:
- ✅ 2回目のIntent処理時、1回目の会話がWorking Memoryに含まれる
- ✅ Claudeが「それ」を正しく解釈して応答（Memory Storeに言及）

**テストコード**: `tests/integration/test_intent_bridge_e2e.py::test_continuous_intent_processing`

---

### TC-13: Acceptance - ユーザー体験改善確認

**目的**: 統合によるユーザー体験改善を定性的に確認

**前提条件**:
- TC-12実行済み
- 統合前後の応答を比較可能

**テスト手順**:

**統合前（模擬）**:
```python
# 統合前: 直接Claude API呼び出し
messages = [{"role": "user", "content": "それのベクトル検索機能について"}]
response_before = await claude.messages.create(messages=messages)
# → Claudeは「それ」が何か理解できない
```

**統合後（実際）**:
```python
# 統合後: Context Assembler経由
# TC-12で確認済み
# → Claudeは「それ = Memory Store」を理解して応答
```

**評価基準**:
| 指標 | 統合前 | 統合後 | 改善 |
|------|--------|--------|------|
| 文脈理解率 | 0% | 90%+ | ✅ |
| 説明の繰り返し | 毎回 | 不要 | ✅ |
| 応答品質 | 低 | 高 | ✅ |

**期待結果**:
- ✅ 「それ」「昨日話した」等の代名詞・参照表現を理解
- ✅ ユーザーが前提を説明し直す必要がない
- ✅ 応答の一貫性が向上

**テストコード**: Manual（手動確認）

---

### TC-14: Acceptance - PostgreSQLデータ活用率確認

**目的**: PostgreSQLに保存されたデータが実際に活用されていることを定量的に確認

**前提条件**:
- PostgreSQLにテストデータ挿入済み
  - messages: 50件
  - memories: 100件

**テスト手順**:
```python
@pytest.mark.asyncio
@pytest.mark.acceptance
async def test_postgresql_data_utilization(db_pool):
    # 1. テストデータ準備
    async with db_pool.acquire() as conn:
        # 50件のメッセージ挿入
        for i in range(50):
            await conn.execute("""
                INSERT INTO messages (id, user_id, role, content, created_at)
                VALUES ($1, 'hiroki', 'user', $2, NOW() - INTERVAL '1 hour' * $3)
            """, uuid4(), f"Test message {i}", i)

        # 100件のメモリ挿入
        for i in range(100):
            await conn.execute("""
                INSERT INTO memories (id, user_id, content, embedding, created_at)
                VALUES ($1, 'hiroki', $2, $3, NOW())
            """, uuid4(), f"Test memory {i}", [0.1] * 1536)  # ダミーベクトル

    # 2. Intent処理
    intent_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'hiroki', 'テストIntent', 'pending', NOW())
        """, intent_id)

    config = {"anthropic_api_key": "sk-ant-..."}
    processor = IntentProcessor(db_pool, config)
    await processor.process(intent_id)

    # 3. データ活用率確認
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT result FROM intents WHERE id = $1",
            intent_id
        )

        metadata = result["result"]["context_metadata"]

        # Working Memory: 10件取得（50件中）
        assert metadata["working_memory_count"] == 10
        working_memory_rate = 10 / 50 * 100  # 20%（最新10件のみ）

        # Semantic Memory: 5件取得（100件中）
        assert metadata["semantic_memory_count"] == 5
        semantic_memory_rate = 5 / 100 * 100  # 5%（関連5件のみ）

        # 総削減率
        total_data = 50 + 100  # 150件
        used_data = 10 + 5  # 15件
        reduction_rate = (1 - used_data / total_data) * 100

        assert reduction_rate == 90  # 90%削減（150件 → 15件）

        print(f"✅ Working Memory: {working_memory_rate}% (10/50)")
        print(f"✅ Semantic Memory: {semantic_memory_rate}% (5/100)")
        print(f"✅ Total reduction: {reduction_rate}% (150 → 15)")
```

**期待結果**:
- ✅ Working Memory取得: 10件（50件中）= 20%
- ✅ Semantic Memory取得: 5件（100件中）= 5%
- ✅ 総削減率: 90%（150件 → 15件）
- ✅ PostgreSQLデータが選別的に活用される（死蔵ではない）

**テストコード**: `tests/acceptance/test_sprint6_acceptance.py::test_postgresql_data_utilization`

---

## 🔧 テスト実行方法

### 環境準備

```bash
# 1. テスト用データベース作成
createdb resonant_engine_test

# 2. テーブル作成
psql -U postgres -d resonant_engine_test < schema.sql

# 3. 環境変数設定
export DATABASE_URL="postgresql://postgres:password@localhost:5432/resonant_engine_test"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### テスト実行

```bash
# 全テスト実行
cd /home/user/resonant-engine
source venv/bin/activate
pytest tests/ -v

# カテゴリ別実行
pytest tests/context_assembler/test_factory.py -v  # Unit
pytest tests/bridge/test_factory_integration.py -v  # Unit
pytest tests/intent_bridge/test_processor_integration.py -v  # Integration
pytest tests/integration/test_intent_bridge_e2e.py -v -m e2e  # E2E
pytest tests/acceptance/test_sprint6_acceptance.py -v -m acceptance  # Acceptance

# カバレッジ測定
pytest --cov=context_assembler --cov=bridge --cov=intent_bridge --cov-report=html
```

### 受け入れテスト実行

```bash
# 受け入れテスト専用スクリプト
python tests/acceptance/run_sprint6_acceptance.py

# 出力例:
# ======= Sprint 6 Acceptance Test Report =======
# TC-01: ✅ PASS
# TC-02: ✅ PASS
# TC-03: ✅ PASS
# ...
# TC-14: ✅ PASS
# ===============================================
# Total: 14/14 PASS (100%)
# Status: ✅ ACCEPTED
```

---

## 📊 合格判定

### Tier 1: 必須（Must Pass）

- [ ] TC-01~TC-14 全てPASS
- [ ] E2Eテスト（TC-11, TC-12）で実際にClaude APIが応答
- [ ] Context metadataが正しく保存される（TC-10）
- [ ] PostgreSQLデータ活用率90%削減（TC-14）

### Tier 2: 推奨（Should Pass）

- [ ] カバレッジ80%以上
- [ ] パフォーマンス: Intent処理3秒以内
- [ ] ログ出力が適切

---

## 🐛 既知の問題・制限事項

### 制限事項
1. **Memory Store/Retrieval未実装時**: MockまたはImportError
2. **Session Summary**: 本Sprintでは未実装（Sprint 7予定）
3. **キャッシング**: 本Sprintでは未実装

### トラブルシューティング

#### 問題: TC-11, TC-12でAPIエラー
```
anthropic.APIStatusError: 401 Unauthorized
```

**対策**: ANTHROPIC_API_KEY確認
```bash
echo $ANTHROPIC_API_KEY
# 有効なキーをセット
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### 問題: TC-14でembeddingエラー
```
ValueError: embedding dimension mismatch
```

**対策**: pgvector拡張確認
```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE memories ADD COLUMN embedding vector(1536);
```

---

## 📚 参考資料

- [Sprint 6仕様書](../architecture/sprint6_intent_bridge_integration_spec.md)
- [Sprint 6作業開始指示書](../sprint/sprint6_intent_bridge_integration_start.md)
- [Sprint 5受け入れテスト](./sprint5_acceptance_test_spec.md)

---

## ✅ 受け入れ完了条件

**Sprint 6を受け入れるための最終チェックリスト:**

- [ ] 全14テストケース PASS
- [ ] E2Eテストで実際のClaude API応答確認
- [ ] Context metadata保存確認
- [ ] PostgreSQLデータ活用率90%削減確認
- [ ] カバレッジ80%以上
- [ ] ドキュメント更新完了
- [ ] コードレビュー完了
- [ ] 重大なバグなし

**全て✅の場合: Sprint 6 ACCEPTED**
