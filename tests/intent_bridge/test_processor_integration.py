"""Intent Bridge - Context Assembler統合テスト"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json

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
    """KanaAIBridge初期化成功 (TC-06)"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)

    # BridgeFactory.create_ai_bridge_with_memory()をmock
    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_factory.return_value = mock_bridge

        await processor.initialize()

        # 検証
        assert processor.ai_bridge is not None
        assert processor.ai_bridge == mock_bridge
        mock_factory.assert_called_once_with(bridge_type="kana", pool=pool)


@pytest.mark.asyncio
async def test_initialize_failure(mock_pool, mock_config):
    """KanaAIBridge初期化失敗時にエラー (TC-06-2)"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_factory.side_effect = Exception("Initialization failed")

        with pytest.raises(Exception, match="Initialization failed"):
            await processor.initialize()


@pytest.mark.asyncio
async def test_call_claude_with_context(mock_pool, mock_config):
    """Context Assembler経由でClaude呼び出し (TC-07)"""
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
            "has_session_summary": False,
            "total_tokens": 3240,
            "compression_applied": False,
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
    assert result["usage"]["input_tokens"] == 100
    assert result["usage"]["output_tokens"] == 150
    assert result["context_metadata"] is not None
    assert result["context_metadata"]["working_memory_count"] == 10
    assert result["context_metadata"]["semantic_memory_count"] == 5

    # process_intent呼び出し確認
    mock_bridge.process_intent.assert_called_once_with({
        "content": "Memory Storeの実装状況は？",
        "user_id": "hiroki",
        "session_id": None,
    })


@pytest.mark.asyncio
async def test_call_claude_with_session_id(mock_pool, mock_config):
    """session_idを含めてClaude呼び出し (TC-07-2)"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)

    mock_bridge = AsyncMock()
    mock_bridge.process_intent.return_value = {
        "summary": "Test response",
        "model": "claude-sonnet-4-20250514",
        "context_metadata": {"working_memory_count": 5, "semantic_memory_count": 3},
    }
    processor.ai_bridge = mock_bridge

    session_id = str(uuid4())
    result = await processor.call_claude(
        description="Test intent",
        user_id="hiroki",
        session_id=session_id,
    )

    # session_idが渡されたことを確認
    call_args = mock_bridge.process_intent.call_args[0][0]
    assert call_args["session_id"] == session_id


@pytest.mark.asyncio
async def test_call_claude_fallback(mock_pool, mock_config):
    """ai_bridge未初期化時にMock応答 (TC-08)"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)
    processor.ai_bridge = None  # 未初期化

    result = await processor.call_claude("Test intent")

    # Mock応答確認
    assert result["response"].startswith("[Mock Response]")
    assert result["model"] == "mock"
    assert result["usage"]["input_tokens"] == 0
    assert result["usage"]["output_tokens"] == 0
    assert result["context_metadata"] is None


@pytest.mark.asyncio
async def test_call_claude_error_handling(mock_pool, mock_config):
    """KanaAIBridgeエラー時に例外伝播 (TC-07-3)"""
    pool, _ = mock_pool
    processor = IntentProcessor(pool, mock_config)

    mock_bridge = AsyncMock()
    mock_bridge.process_intent.side_effect = Exception("API error")
    processor.ai_bridge = mock_bridge

    with pytest.raises(Exception, match="API error"):
        await processor.call_claude("Test intent")


@pytest.mark.asyncio
async def test_process_intent_with_context(mock_pool, mock_config):
    """Intent処理全体（Context Assembler統合） (TC-09)"""
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
            "usage": {"input_tokens": 120, "output_tokens": 180},
            "context_metadata": {
                "working_memory_count": 5,
                "semantic_memory_count": 3,
                "total_tokens": 2500,
                "compression_applied": False,
            },
        }
        mock_factory.return_value = mock_bridge

        # 実行
        await processor.process(intent_id)

        # 検証: status='completed' で更新されること
        update_calls = [
            call for call in conn.execute.call_args_list
            if len(call[0]) > 0 and "completed" in str(call[0][0])
        ]
        assert len(update_calls) > 0

        # 検証: context_metadataが保存されること
        result_json_arg = update_calls[0][0][1]
        result_data = json.loads(result_json_arg)
        assert "context_metadata" in result_data
        assert result_data["context_metadata"]["working_memory_count"] == 5
        assert result_data["context_metadata"]["semantic_memory_count"] == 3


@pytest.mark.asyncio
async def test_process_intent_auto_initialize(mock_pool, mock_config):
    """初回呼び出し時に自動初期化 (TC-09-2)"""
    pool, conn = mock_pool
    processor = IntentProcessor(pool, mock_config)

    # ai_bridgeは初期状態でNone
    assert processor.ai_bridge is None

    intent_id = uuid4()
    conn.fetchrow.return_value = {
        "id": intent_id,
        "description": "Test intent",
        "user_id": "hiroki",
    }

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_bridge.process_intent.return_value = {
            "summary": "Test response",
            "model": "test",
            "context_metadata": {"working_memory_count": 0, "semantic_memory_count": 0},
        }
        mock_factory.return_value = mock_bridge

        await processor.process(intent_id)

        # 初期化が呼ばれたことを確認
        assert processor.ai_bridge is not None
        mock_factory.assert_called_once()


@pytest.mark.asyncio
async def test_process_intent_not_found(mock_pool, mock_config):
    """存在しないIntent IDでの処理 (TC-09-3)"""
    pool, conn = mock_pool
    processor = IntentProcessor(pool, mock_config)

    intent_id = uuid4()
    conn.fetchrow.return_value = None  # Intent not found

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory"):
        await processor.process(intent_id)

        # updateが呼ばれないことを確認
        update_calls = [
            call for call in conn.execute.call_args_list
            if "completed" in str(call)
        ]
        assert len(update_calls) == 0


@pytest.mark.asyncio
async def test_process_intent_error_handling(mock_pool, mock_config):
    """Intent処理中のエラーハンドリング (TC-09-4)"""
    pool, conn = mock_pool
    processor = IntentProcessor(pool, mock_config)

    intent_id = uuid4()
    conn.fetchrow.return_value = {
        "id": intent_id,
        "description": "Test intent",
        "user_id": "hiroki",
    }

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_bridge.process_intent.side_effect = Exception("API error")
        mock_factory.return_value = mock_bridge

        await processor.process(intent_id)

        # status='failed' で更新されること
        failed_calls = [
            call for call in conn.execute.call_args_list
            if len(call[0]) > 0 and "failed" in str(call[0][0])
        ]
        assert len(failed_calls) > 0

        # エラー通知が作成されること
        notification_calls = [
            call for call in conn.execute.call_args_list
            if "notifications" in str(call)
        ]
        assert len(notification_calls) > 0


@pytest.mark.asyncio
async def test_context_metadata_saved(mock_pool, mock_config):
    """Context metadataが正しく保存される (TC-10)"""
    pool, conn = mock_pool
    processor = IntentProcessor(pool, mock_config)

    intent_id = uuid4()
    conn.fetchrow.return_value = {
        "id": intent_id,
        "description": "Test",
        "user_id": "hiroki",
    }

    with patch("bridge.factory.bridge_factory.BridgeFactory.create_ai_bridge_with_memory") as mock_factory:
        mock_bridge = AsyncMock()
        mock_bridge.process_intent.return_value = {
            "summary": "Response",
            "model": "claude-sonnet-4-20250514",
            "usage": {"input_tokens": 50, "output_tokens": 100},
            "context_metadata": {
                "working_memory_count": 8,
                "semantic_memory_count": 4,
                "has_session_summary": False,
                "total_tokens": 2800,
                "compression_applied": False,
            },
        }
        mock_factory.return_value = mock_bridge

        await processor.process(intent_id)

        # result JSONを取得
        update_calls = [
            call for call in conn.execute.call_args_list
            if len(call[0]) > 0 and "completed" in str(call[0][0])
        ]
        result_json = json.loads(update_calls[0][0][1])

        # context_metadataの全フィールドを検証
        assert result_json["context_metadata"]["working_memory_count"] == 8
        assert result_json["context_metadata"]["semantic_memory_count"] == 4
        assert result_json["context_metadata"]["has_session_summary"] is False
        assert result_json["context_metadata"]["total_tokens"] == 2800
        assert result_json["context_metadata"]["compression_applied"] is False
