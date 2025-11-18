"""E2E Tests for Context Assembler + KanaAIBridge Integration"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from context_assembler.service import ContextAssemblerService
from context_assembler.models import ContextConfig
from bridge.providers.ai.kana_ai_bridge import KanaAIBridge
from memory_store.models import MemoryResult, MemoryType
from backend.app.models.message import MessageResponse, MessageType


@pytest.fixture
def context_config():
    """テスト用設定"""
    return ContextConfig(
        system_prompt="Test system prompt",
        working_memory_limit=10,
        semantic_memory_limit=5,
        max_tokens=100000,
        token_safety_margin=0.8,
    )


@pytest.fixture
def mock_retrieval_orchestrator():
    """モックRetrieval Orchestrator"""
    mock = AsyncMock()
    mock_response = MagicMock()
    mock_response.results = [
        MemoryResult(
            id=1,
            content="Resonant Engineは呼吸のリズムで動作する",
            memory_type=MemoryType.LONGTERM,
            source_type=None,
            metadata={},
            similarity=0.9,
            created_at=datetime.now(),
        )
    ]
    mock.retrieve = AsyncMock(return_value=mock_response)
    return mock


@pytest.fixture
def mock_message_repository():
    """モックMessage Repository"""
    mock = AsyncMock()

    # 過去の会話を返すモック
    past_messages = [
        MessageResponse(
            id=uuid4(),
            user_id="test_user",
            content="Resonant Engineとは何ですか？",
            message_type=MessageType.USER,
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        MessageResponse(
            id=uuid4(),
            user_id="test_user",
            content="Resonant Engineは呼吸のリズムで動作するAIシステムです。",
            message_type=MessageType.KANA,
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    mock.list = AsyncMock(return_value=(past_messages, 2))
    return mock


@pytest.fixture
def mock_session_repository():
    """モックSession Repository"""
    mock = AsyncMock()
    mock.get_by_id = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def context_assembler(
    context_config,
    mock_retrieval_orchestrator,
    mock_message_repository,
    mock_session_repository,
):
    """Context Assembler Service"""
    return ContextAssemblerService(
        retrieval_orchestrator=mock_retrieval_orchestrator,
        message_repository=mock_message_repository,
        session_repository=mock_session_repository,
        config=context_config,
    )


@pytest.mark.asyncio
async def test_context_assembler_integration(context_assembler):
    """Context Assemblerの統合テスト"""
    # コンテキスト組み立て
    assembled = await context_assembler.assemble_context(
        user_message="Memory Storeについて詳しく教えて",
        user_id="test_user",
    )

    # 検証
    assert len(assembled.messages) >= 3
    assert assembled.messages[0]["role"] == "system"
    assert assembled.messages[-1]["role"] == "user"
    assert assembled.messages[-1]["content"] == "Memory Storeについて詳しく教えて"

    # メタデータ検証
    assert assembled.metadata.working_memory_count == 2
    assert assembled.metadata.semantic_memory_count == 1
    assert assembled.metadata.total_tokens > 0
    assert assembled.metadata.assembly_latency_ms < 1000  # 1秒以内


@pytest.mark.asyncio
async def test_kana_bridge_with_context_assembler(context_assembler):
    """KanaAIBridge + Context Assembler統合テスト"""
    # モックClaude APIレスポンス
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "Memory Storeは、pgvectorを使った長期記憶システムです。"
    mock_response.content = [mock_content]

    # モッククライアント
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    # KanaAIBridge初期化（Context Assembler付き）
    bridge = KanaAIBridge(
        api_key="test-key", client=mock_client, context_assembler=context_assembler
    )

    # Intent作成
    intent = {
        "content": "Memory Storeについて詳しく教えて",
        "user_id": "test_user",
    }

    # 処理
    response = await bridge.process_intent(intent)

    # 検証
    assert response["status"] == "ok"
    assert "summary" in response
    assert "Memory Store" in response["summary"]

    # Context metadataの検証
    assert "context_metadata" in response
    assert response["context_metadata"]["working_memory_count"] == 2
    assert response["context_metadata"]["semantic_memory_count"] == 1
    assert response["context_metadata"]["total_tokens"] > 0

    # Claude APIが正しいメッセージで呼ばれたか確認
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    messages = call_kwargs["messages"]

    # 過去の会話が含まれていることを確認
    message_contents = " ".join(m["content"] for m in messages)
    assert "Resonant Engine" in message_contents


@pytest.mark.asyncio
async def test_kana_bridge_without_context_assembler():
    """Context Assembler未設定時のfallbackテスト"""
    # モックClaude APIレスポンス
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "こんにちは！"
    mock_response.content = [mock_content]

    # モッククライアント
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    # KanaAIBridge初期化（Context Assembler未設定）
    bridge = KanaAIBridge(api_key="test-key", client=mock_client)

    # Intent作成
    intent = {"content": "Hello, Kana!"}

    # 処理
    response = await bridge.process_intent(intent)

    # 検証
    assert response["status"] == "ok"
    assert "summary" in response
    assert "context_metadata" not in response  # Context Assembler未使用

    # シンプルなメッセージで呼ばれたか確認
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    messages = call_kwargs["messages"]

    assert len(messages) == 2  # System + User のみ
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello, Kana!"


@pytest.mark.asyncio
async def test_kana_bridge_context_assembly_failure(context_assembler):
    """Context組み立て失敗時のfallbackテスト"""
    # Context Assemblerが例外を投げるようにモック
    context_assembler.assemble_context = AsyncMock(
        side_effect=Exception("Test error")
    )

    # モックClaude APIレスポンス
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "OK"
    mock_response.content = [mock_content]

    # モッククライアント
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    # KanaAIBridge初期化
    bridge = KanaAIBridge(
        api_key="test-key", client=mock_client, context_assembler=context_assembler
    )

    # Intent作成
    intent = {"content": "Test"}

    # 処理（例外が発生してもfallbackで動作）
    with pytest.warns(UserWarning, match="Context assembly failed"):
        response = await bridge.process_intent(intent)

    # Fallbackで動作したことを確認
    assert response["status"] == "ok"
    assert "context_metadata" not in response


@pytest.mark.asyncio
async def test_kana_bridge_backward_compatibility():
    """従来の形式のintentとの後方互換性テスト"""
    # モックClaude APIレスポンス
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "OK"
    mock_response.content = [mock_content]

    # モッククライアント
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    # KanaAIBridge初期化
    bridge = KanaAIBridge(api_key="test-key", client=mock_client)

    # 従来の形式のintent（type/payload形式）
    old_format_intent = {"type": "task", "payload": {"action": "test"}}

    # 処理
    response = await bridge.process_intent(old_format_intent)

    # 正常に処理されることを確認
    assert response["status"] == "ok"

    # _build_promptが使われたことを確認
    call_kwargs = mock_client.messages.create.call_args[1]
    messages = call_kwargs["messages"]
    assert "Intent Summary" in messages[1]["content"]
