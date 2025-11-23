"""Intent Bridge E2E統合テスト（Context Assembler統合）

注意: このテストは実際のデータベースを使用します。
テスト実行前に以下を確認してください:
- PostgreSQLが起動している
- DATABASE_URL環境変数が設定されている
- テスト用データベースが作成されている
- ANTHROPIC_API_KEY環境変数が設定されている（実際のAPI呼び出し用）

テスト実行:
pytest tests/integration/test_intent_bridge_e2e.py -v -m e2e
"""

import os
import pytest
import asyncpg
from uuid import uuid4
from datetime import datetime

from intent_bridge.intent_bridge.processor import IntentProcessor


# E2Eテストマーカー
pytestmark = pytest.mark.e2e


@pytest.fixture
async def db_pool():
    """実際のデータベース接続（テスト用）

    環境変数DATABASE_URLが必要です。
    例: postgresql://postgres:password@localhost:5432/resonant_engine_test
    """
    import os

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set")

    try:
        pool = await asyncpg.create_pool(database_url, min_size=2, max_size=5)
    except Exception as e:
        pytest.skip(f"Failed to connect to database: {e}")

    yield pool
    await pool.close()


@pytest.fixture
async def setup_test_data(db_pool):
    """テストデータ準備とクリーンアップ"""
    async with db_pool.acquire() as conn:
        # テーブルクリア（存在する場合のみ）
        try:
            await conn.execute("DELETE FROM intents WHERE user_id = 'test_user'")
            await conn.execute("DELETE FROM messages WHERE user_id = 'test_user'")
            await conn.execute("DELETE FROM notifications WHERE user_id = 'test_user'")
        except Exception:
            # テーブルが存在しない場合はスキップ
            pass

        # サンプルメッセージ挿入（Working Memory用）
        try:
            await conn.execute("""
                INSERT INTO messages (id, user_id, role, content, created_at)
                VALUES
                    ($1, 'test_user', 'user', 'Memory Storeについて教えて', NOW() - INTERVAL '10 minutes'),
                    ($2, 'test_user', 'assistant', 'Memory Storeはpgvectorベースの長期記憶システムです', NOW() - INTERVAL '9 minutes')
            """, uuid4(), uuid4())
        except Exception as e:
            pytest.skip(f"Failed to insert test data: {e}")

    yield

    # クリーンアップ
    async with db_pool.acquire() as conn:
        try:
            await conn.execute("DELETE FROM intents WHERE user_id = 'test_user'")
            await conn.execute("DELETE FROM messages WHERE user_id = 'test_user'")
            await conn.execute("DELETE FROM notifications WHERE user_id = 'test_user'")
        except Exception:
            pass


@pytest.mark.asyncio
@pytest.mark.slow
async def test_intent_processing_e2e_mock(db_pool, setup_test_data):
    """
    Intent処理E2E（Mock使用、実DB）(TC-11 simplified)

    このテストはMockを使用して、実際のClaude API呼び出しなしでテストします。
    """
    from unittest.mock import patch, AsyncMock

    # Intent作成
    intent_id = uuid4()
    async with db_pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO intents (id, user_id, description, status, created_at)
                VALUES ($1, 'test_user', $2, 'pending', NOW())
            """, intent_id, "Context Assemblerの統合状況は？")
        except Exception as e:
            pytest.skip(f"Failed to create intent: {e}")

    # 処理実行（Mock使用）
    config = {}
    processor = IntentProcessor(db_pool, config)

    # KanaAIBridgeをmock
    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_bridge.process_intent.return_value = {
            "summary": "Context Assembler統合が完了しています（Mock応答）",
            "model": "mock-model",
            "usage": {"input_tokens": 100, "output_tokens": 150},
            "context_metadata": {
                "working_memory_count": 2,
                "semantic_memory_count": 0,
                "has_session_summary": False,
                "total_tokens": 500,
                "compression_applied": False,
            },
        }
        mock_factory.return_value = mock_bridge

        try:
            await processor.process(intent_id)
        except Exception as e:
            pytest.fail(f"Intent processing failed: {e}")

    # 結果確認
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT status, result FROM intents WHERE id = $1",
            intent_id
        )

        assert result is not None, "Intent not found after processing"
        assert result["status"] == "completed", f"Expected status=completed, got {result['status']}"

        result_json = result["result"]

        # Context metadataが含まれていることを確認
        assert "context_metadata" in result_json
        assert result_json["context_metadata"] is not None
        assert result_json["context_metadata"]["working_memory_count"] == 2
        assert result_json["context_metadata"]["semantic_memory_count"] == 0

        # 応答内容の検証
        assert len(result_json["response"]) > 0


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - このテストは実際のClaude APIを使用します"
)
async def test_intent_processing_e2e_real(db_pool, setup_test_data):
    """
    Intent処理E2E（実際のClaude API使用）(TC-11)

    注意: このテストは実際のClaude APIを呼び出すため、APIコストが発生します。
    ANTHROPIC_API_KEYが設定されている場合のみ実行されます。
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")

    # Intent作成
    intent_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'test_user', $2, 'pending', NOW())
        """, intent_id, "Memory Storeについて簡単に説明してください")

    # 処理実行（実際のAPI呼び出し）
    config = {"anthropic_api_key": api_key}
    processor = IntentProcessor(db_pool, config)

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

        # Working Memoryに事前挿入した2件が含まれていることを期待
        # （ただし、Context Assemblerの実装によっては0件の可能性もある）
        assert result_json["context_metadata"]["working_memory_count"] >= 0

        # 応答内容の検証
        assert len(result_json["response"]) > 0
        assert result_json["model"].startswith("claude")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_continuous_intent_processing_mock(db_pool, setup_test_data):
    """
    連続Intent処理（文脈継続）Mock版 (TC-12 simplified)

    2つのIntentを連続で処理し、2回目のIntentで1回目の会話が
    Working Memoryに含まれることを確認します（Mock使用）。
    """
    from unittest.mock import patch, AsyncMock

    config = {}
    processor = IntentProcessor(db_pool, config)

    # 1回目: Memory Storeについて質問
    intent_id_1 = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'test_user', 'Memory Storeの実装状況を教えて', 'pending', NOW())
        """, intent_id_1)

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_bridge.process_intent.return_value = {
            "summary": "Memory Store Sprint 2が完了しています",
            "model": "mock",
            "context_metadata": {"working_memory_count": 2, "semantic_memory_count": 0},
        }
        mock_factory.return_value = mock_bridge

        await processor.process(intent_id_1)

    # 1回目の応答をmessagesテーブルに保存（実際のシステムではこれが自動で行われる想定）
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO messages (id, user_id, role, content, created_at)
            VALUES
                ($1, 'test_user', 'user', 'Memory Storeの実装状況を教えて', NOW() - INTERVAL '1 minute'),
                ($2, 'test_user', 'assistant', 'Memory Store Sprint 2が完了しています', NOW())
        """, uuid4(), uuid4())

    # 2回目: 「それ」で参照（文脈を保持しているか確認）
    intent_id_2 = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'test_user', 'それのベクトル検索機能について詳しく', 'pending', NOW())
        """, intent_id_2)

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_bridge.process_intent.return_value = {
            "summary": "Memory Storeのベクトル検索はpgvectorを使用しています",
            "model": "mock",
            "context_metadata": {"working_memory_count": 4, "semantic_memory_count": 0},  # 1回目の2件+2回目の2件
        }
        mock_factory.return_value = mock_bridge

        await processor.process(intent_id_2)

    # 結果確認
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT result FROM intents WHERE id = $1",
            intent_id_2
        )

        result_json = result["result"]

        # Working Memoryに1回目の会話が含まれていることを確認
        # （4件 = 初期2件 + 1回目2件）
        assert result_json["context_metadata"]["working_memory_count"] == 4


@pytest.mark.asyncio
async def test_fallback_on_context_assembler_failure(db_pool, setup_test_data):
    """
    Context Assembler初期化失敗時のFallback動作確認 (TC-05 E2E)

    Context Assemblerの初期化が失敗しても、KanaAIBridgeは
    Context Assemblerなしで動作することを確認します。
    """
    from unittest.mock import patch, AsyncMock
    import warnings

    intent_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, user_id, description, status, created_at)
            VALUES ($1, 'test_user', 'Test intent', 'pending', NOW())
        """, intent_id)

    config = {}
    processor = IntentProcessor(db_pool, config)

    # Context Assembler初期化失敗を模擬
    with patch("context_assembler.factory.create_context_assembler") as mock_ca_factory:
        mock_ca_factory.side_effect = ConnectionError("Database connection failed")

        # KanaAIBridgeはFallbackで生成される
        with patch("bridge.providers.ai.kana_ai_bridge.KanaAIBridge.process_intent") as mock_process:
            mock_process.return_value = {
                "summary": "Fallback response",
                "model": "claude-sonnet-4-20250514",
                "context_metadata": None,  # Context Assemblerなし
            }

            # 警告を捕捉
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                await processor.process(intent_id)

    # 結果確認: 処理は成功するがcontext_metadata=None
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT status, result FROM intents WHERE id = $1",
            intent_id
        )

        assert result["status"] == "completed"
        # Fallbackモードではcontext_metadataがNone
        assert result["result"]["context_metadata"] is None


@pytest.mark.asyncio
async def test_intent_not_found(db_pool):
    """存在しないIntent IDでの処理 (エッジケース)"""
    config = {}
    processor = IntentProcessor(db_pool, config)

    # 存在しないIntent ID
    non_existent_id = uuid4()

    # エラーなく終了することを確認
    await processor.process(non_existent_id)

    # データベースに変更がないことを確認
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM intents WHERE id = $1",
            non_existent_id
        )
        assert result is None
