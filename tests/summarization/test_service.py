"""SummarizationService単体テスト"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from summarization.service import SummarizationService
from memory_store.models import SessionSummaryResponse
from session.config import SessionConfig


@pytest.fixture
def mock_summary_repo():
    """Mock SessionSummaryRepository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_claude_client():
    """Mock Claude API client"""
    client = AsyncMock()
    response = MagicMock()
    response.content = [MagicMock(text="Test summary: Memory Store implementation session")]
    client.messages.create.return_value = response
    return client


@pytest.fixture
def sample_messages():
    """Sample messages for testing"""
    return [
        {
            'role': 'user',
            'content': 'Memory Storeの実装を始めたい',
            'created_at': datetime(2025, 11, 18, 10, 0, 0),
        },
        {
            'role': 'assistant',
            'content': 'Memory Storeの設計から始めましょう',
            'created_at': datetime(2025, 11, 18, 10, 5, 0),
        },
        {
            'role': 'user',
            'content': 'pgvectorの設定方法は？',
            'created_at': datetime(2025, 11, 18, 11, 0, 0),
        },
        {
            'role': 'assistant',
            'content': 'pgvectorのインストールは...',
            'created_at': datetime(2025, 11, 18, 11, 5, 0),
        },
    ]


@pytest.mark.asyncio
async def test_create_summary(mock_summary_repo, mock_claude_client, sample_messages):
    """要約生成の基本動作テスト"""
    # Setup
    service = SummarizationService(
        summary_repo=mock_summary_repo,
        claude_client=mock_claude_client,
    )

    user_id = "hiroki"
    session_id = uuid4()

    # Mock saved summary
    mock_summary_repo.save.return_value = uuid4()
    mock_summary_repo.get_by_session.return_value = SessionSummaryResponse(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        summary="Test summary: Memory Store implementation session",
        message_count=4,
        start_time=datetime(2025, 11, 18, 10, 0, 0),
        end_time=datetime(2025, 11, 18, 11, 5, 0),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Execute
    result = await service.create_summary(
        user_id=user_id,
        session_id=session_id,
        messages=sample_messages,
    )

    # Verify
    assert result is not None
    assert result.message_count == 4
    assert "Memory Store" in result.summary
    mock_claude_client.messages.create.assert_called_once()
    mock_summary_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_summary_empty_messages(mock_summary_repo, mock_claude_client):
    """空のメッセージリストでエラーを出すテスト"""
    service = SummarizationService(
        summary_repo=mock_summary_repo,
        claude_client=mock_claude_client,
    )

    with pytest.raises(ValueError, match="No messages found"):
        await service.create_summary(
            user_id="hiroki",
            session_id=uuid4(),
            messages=[],
        )


@pytest.mark.asyncio
async def test_build_summarization_prompt(mock_summary_repo, mock_claude_client, sample_messages):
    """プロンプト構築のテスト"""
    service = SummarizationService(
        summary_repo=mock_summary_repo,
        claude_client=mock_claude_client,
    )

    prompt = service._build_summarization_prompt(sample_messages)

    # Verify prompt contains key elements
    assert "要約" in prompt
    assert "Memory Store" in prompt
    assert "2025-11-18" in prompt
    assert str(len(sample_messages)) in prompt


@pytest.mark.asyncio
async def test_extract_time_from_messages(mock_summary_repo, mock_claude_client, sample_messages):
    """メッセージから時刻を抽出するテスト"""
    service = SummarizationService(
        summary_repo=mock_summary_repo,
        claude_client=mock_claude_client,
    )

    start_time = service._extract_start_time(sample_messages)
    end_time = service._extract_end_time(sample_messages)

    assert start_time == datetime(2025, 11, 18, 10, 0, 0)
    assert end_time == datetime(2025, 11, 18, 11, 5, 0)


@pytest.mark.asyncio
async def test_custom_config(mock_summary_repo, mock_claude_client, sample_messages):
    """カスタム設定でのサービス初期化テスト"""
    config = SessionConfig(
        summary_trigger_message_count=15,
        claude_model="claude-3-5-haiku-20241022",
        claude_max_tokens=300,
    )

    service = SummarizationService(
        summary_repo=mock_summary_repo,
        claude_client=mock_claude_client,
        config=config,
    )

    assert service.config.summary_trigger_message_count == 15
    assert service.config.claude_max_tokens == 300


@pytest.mark.asyncio
async def test_claude_api_call_parameters(mock_summary_repo, mock_claude_client, sample_messages):
    """Claude API呼び出しパラメータの確認"""
    service = SummarizationService(
        summary_repo=mock_summary_repo,
        claude_client=mock_claude_client,
    )

    user_id = "hiroki"
    session_id = uuid4()

    mock_summary_repo.save.return_value = uuid4()
    mock_summary_repo.get_by_session.return_value = SessionSummaryResponse(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        summary="Test summary",
        message_count=4,
        start_time=datetime.now(),
        end_time=datetime.now(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    await service.create_summary(
        user_id=user_id,
        session_id=session_id,
        messages=sample_messages,
    )

    # Verify Claude API was called with correct parameters
    call_args = mock_claude_client.messages.create.call_args
    assert call_args.kwargs['model'] == 'claude-3-5-haiku-20241022'
    assert call_args.kwargs['max_tokens'] == 500
    assert len(call_args.kwargs['messages']) == 1
    assert call_args.kwargs['messages'][0]['role'] == 'user'
