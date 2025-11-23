"""
tests/system/test_context.py

ST-CTX: Context Assemblerテスト

このファイルは tests/conftest.py の db_pool フィクスチャを使用します。
独自のconftest.pyを作成しないでください。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from context_assembler.service import ContextAssemblerService
from context_assembler.models import ContextConfig, AssemblyOptions
from context_assembler.token_estimator import TokenEstimator


@pytest.mark.asyncio
async def test_context_assembler_initialization():
    """ST-CTX-001: ContextAssemblerService初期化確認
    
    目的: ContextAssemblerServiceが正しく初期化できることを確認
    """
    # モックの依存関係を作成
    retrieval_orchestrator = MagicMock()
    message_repository = MagicMock()
    session_repository = MagicMock()
    config = ContextConfig()
    
    service = ContextAssemblerService(
        retrieval_orchestrator=retrieval_orchestrator,
        message_repository=message_repository,
        session_repository=session_repository,
        config=config,
    )
    
    assert service is not None
    assert service.retrieval is not None
    assert service.message_repo is not None
    assert service.session_repo is not None
    assert service.config is not None
    assert service.token_estimator is not None


@pytest.mark.asyncio
async def test_token_estimator():
    """ST-CTX-002: TokenEstimator動作確認
    
    目的: TokenEstimatorが正常にトークン数を推定できることを確認
    """
    estimator = TokenEstimator()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
    ]
    
    token_count = estimator.estimate(messages)
    
    assert token_count > 0
    assert isinstance(token_count, int)


@pytest.mark.asyncio
async def test_context_config():
    """ST-CTX-003: ContextConfig設定確認
    
    目的: ContextConfigが正しく設定できることを確認
    """
    config = ContextConfig(
        max_tokens=8000,
        working_memory_limit=10,
        semantic_memory_limit=5,
        token_safety_margin=0.9,
    )
    
    assert config.max_tokens == 8000
    assert config.working_memory_limit == 10
    assert config.semantic_memory_limit == 5
    assert config.token_safety_margin == 0.9


@pytest.mark.asyncio
async def test_assembly_options():
    """ST-CTX-004: AssemblyOptions設定確認
    
    目的: AssemblyOptionsが正しく設定できることを確認
    """
    options = AssemblyOptions(
        include_semantic_memory=True,
        include_session_summary=True,
        include_user_profile=True,
        working_memory_limit=15,
        semantic_memory_limit=8,
    )
    
    assert options.include_semantic_memory is True
    assert options.include_session_summary is True
    assert options.include_user_profile is True
    assert options.working_memory_limit == 15
    assert options.semantic_memory_limit == 8


@pytest.mark.asyncio
async def test_context_assembly_basic():
    """ST-CTX-005: 基本的なコンテキスト組み立て
    
    目的: ContextAssemblerServiceが基本的なコンテキストを組み立てられることを確認
    """
    # モックの依存関係を作成
    retrieval_orchestrator = MagicMock()
    retrieval_orchestrator.retrieve = AsyncMock(return_value=MagicMock(results=[]))
    
    message_repository = MagicMock()
    message_repository.list = AsyncMock(return_value=([], 0))
    
    session_repository = MagicMock()
    session_repository.get_by_id = AsyncMock(return_value=None)
    
    config = ContextConfig()
    
    service = ContextAssemblerService(
        retrieval_orchestrator=retrieval_orchestrator,
        message_repository=message_repository,
        session_repository=session_repository,
        config=config,
    )
    
    # コンテキスト組み立て実行
    result = await service.assemble_context(
        user_message="Hello, this is a test message.",
        user_id="test_user",
        session_id=None,
        options=AssemblyOptions(
            include_semantic_memory=False,
            include_session_summary=False,
        ),
    )
    
    assert result is not None
    assert result.messages is not None
    assert len(result.messages) > 0
    assert result.metadata is not None
    assert result.metadata.total_tokens > 0
    
    # 最初のメッセージがsystemであることを確認
    assert result.messages[0]["role"] == "system"
    
    # 最後のメッセージがuserであることを確認
    assert result.messages[-1]["role"] == "user"
    assert result.messages[-1]["content"] == "Hello, this is a test message."
