"""Context Assembler Service Tests"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from context_assembler.service import ContextAssemblerService
from context_assembler.models import ContextConfig, AssemblyOptions
from memory_store.models import MemoryResult, MemoryType
from backend.app.models.message import MessageResponse, MessageType


@pytest.fixture
def context_config():
    """テスト用設定"""
    return ContextConfig(
        system_prompt="Test system prompt",
        working_memory_limit=5,
        semantic_memory_limit=3,
        max_tokens=1000,
        token_safety_margin=0.8,
    )


@pytest.fixture
def mock_retrieval_orchestrator():
    """モックRetrieval Orchestrator"""
    mock = AsyncMock()
    mock.retrieve = AsyncMock()
    return mock


@pytest.fixture
def mock_message_repository():
    """モックMessage Repository"""
    mock = AsyncMock()
    mock.list = AsyncMock()
    return mock


@pytest.fixture
def mock_session_repository():
    """モックSession Repository"""
    mock = AsyncMock()
    mock.get_by_id = AsyncMock()
    return mock


@pytest.fixture
def context_assembler_service(
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


def test_map_message_type_to_role(context_assembler_service):
    """MessageTypeのマッピングテスト"""
    service = context_assembler_service

    assert service._map_message_type_to_role("user") == "user"
    assert service._map_message_type_to_role("kana") == "assistant"
    assert service._map_message_type_to_role("yuno") == "assistant"
    assert service._map_message_type_to_role("system") is None


def test_get_token_limit(context_assembler_service):
    """トークン上限計算テスト"""
    service = context_assembler_service
    limit = service._get_token_limit()

    # 1000 * 0.8 = 800
    assert limit == 800


def test_build_messages_with_working_memory_only(context_assembler_service):
    """Working Memoryのみでメッセージ構築"""
    service = context_assembler_service

    memory_layers = {
        "working": [
            MessageResponse(
                id=uuid4(),
                user_id="test",
                content="こんにちは",
                message_type=MessageType.USER,
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            MessageResponse(
                id=uuid4(),
                user_id="test",
                content="こんにちは！",
                message_type=MessageType.KANA,
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ],
        "semantic": [],
        "session_summary": None,
    }

    messages = service._build_messages(memory_layers, "Memory Storeについて教えて")

    # System + Working Memory 2件 + User Message
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "こんにちは"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "こんにちは！"
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "Memory Storeについて教えて"


def test_build_messages_with_semantic_memory(context_assembler_service):
    """Semantic Memoryを含むメッセージ構築"""
    service = context_assembler_service

    memory_layers = {
        "working": [],
        "semantic": [
            MemoryResult(
                id=1,
                content="Resonant Engineは呼吸で動く",
                memory_type=MemoryType.LONGTERM,
                source_type=None,
                metadata={},
                similarity=0.9,
                created_at=datetime.now(),
            ),
        ],
        "session_summary": None,
    }

    messages = service._build_messages(memory_layers, "Resonant Engineについて")

    # System + Semantic Memory + User Message
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "assistant"
    assert "関連する過去の記憶" in messages[1]["content"]
    assert "Resonant Engineは呼吸で動く" in messages[1]["content"]
    assert messages[2]["role"] == "user"


def test_build_messages_with_session_summary(context_assembler_service):
    """Session Summaryを含むメッセージ構築"""
    service = context_assembler_service

    memory_layers = {
        "working": [],
        "semantic": [],
        "session_summary": "Previous discussion about Resonant Engine",
    }

    messages = service._build_messages(memory_layers, "続きを教えて")

    # System Prompt にSession Summaryが含まれる
    assert "Previous discussion about Resonant Engine" in messages[0]["content"]


def test_validate_context_success(context_assembler_service):
    """コンテキスト検証成功"""
    service = context_assembler_service

    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User message"},
    ]

    # 例外が発生しないことを確認
    service._validate_context(messages, 100)


def test_validate_context_empty_messages(context_assembler_service):
    """空メッセージでバリデーションエラー"""
    service = context_assembler_service

    with pytest.raises(ValueError, match="Messages cannot be empty"):
        service._validate_context([], 100)


def test_validate_context_no_system_prompt(context_assembler_service):
    """System Prompt不在でエラー"""
    service = context_assembler_service

    messages = [{"role": "user", "content": "Test"}]

    with pytest.raises(ValueError, match="First message must be system"):
        service._validate_context(messages, 100)


def test_validate_context_no_user_message(context_assembler_service):
    """User Message不在でエラー"""
    service = context_assembler_service

    messages = [
        {"role": "system", "content": "System"},
        {"role": "assistant", "content": "Assistant"},
    ]

    with pytest.raises(ValueError, match="Last message must be user"):
        service._validate_context(messages, 100)


def test_validate_context_missing_content(context_assembler_service):
    """content欠落でエラー"""
    service = context_assembler_service

    messages = [
        {"role": "system", "content": "System"},
        {"role": "user"},  # contentが無い
    ]

    with pytest.raises(ValueError, match="missing role or content"):
        service._validate_context(messages, 100)


def test_compress_context_removes_session_summary(context_assembler_service):
    """トークン圧縮：Session Summary削除"""
    service = context_assembler_service
    service.config.max_tokens = 100  # 小さい上限

    memory_layers = {
        "working": [],
        "semantic": [],
        "session_summary": "A" * 1000,  # 大きいサマリー
    }

    messages = service._build_messages(memory_layers, "Test")
    original_tokens = service.token_estimator.estimate(messages)

    # 圧縮
    compressed_messages, compressed_tokens = service._compress_context(
        messages, memory_layers, "Test"
    )

    # Session Summaryが削除されている
    assert compressed_tokens < original_tokens
    assert "A" * 1000 not in compressed_messages[0]["content"]
