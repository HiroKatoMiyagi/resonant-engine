"""SessionManager単体テスト"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from session.manager import SessionManager
from session.config import SessionConfig
from memory_store.models import SessionSummaryResponse, SessionStats


@pytest.fixture
def mock_summary_repo():
    """Mock SessionSummaryRepository"""
    return AsyncMock()


@pytest.fixture
def mock_summarization_service():
    """Mock SummarizationService"""
    return AsyncMock()


@pytest.fixture
def sample_messages():
    """Sample messages for testing"""
    base_time = datetime(2025, 11, 18, 10, 0, 0)
    return [
        {
            'role': 'user' if i % 2 == 0 else 'assistant',
            'content': f'Message {i}',
            'created_at': base_time + timedelta(minutes=i * 5),
        }
        for i in range(20)
    ]


@pytest.mark.asyncio
async def test_should_create_summary_message_count_trigger(
    mock_summary_repo,
    mock_summarization_service,
    sample_messages,
):
    """メッセージ数が20件でトリガー"""
    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
    )

    # 前回の要約なし
    mock_summary_repo.get_latest.return_value = None

    should_create = await manager._should_create_summary(
        user_id="hiroki",
        session_id=uuid4(),
        messages=sample_messages,  # 20件
    )

    assert should_create is True


@pytest.mark.asyncio
async def test_should_not_create_summary_insufficient_messages(
    mock_summary_repo,
    mock_summarization_service,
    sample_messages,
):
    """メッセージ数が19件では生成しない"""
    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
    )

    mock_summary_repo.get_latest.return_value = None

    should_create = await manager._should_create_summary(
        user_id="hiroki",
        session_id=uuid4(),
        messages=sample_messages[:19],  # 19件
    )

    assert should_create is False


@pytest.mark.asyncio
async def test_should_create_summary_time_trigger(
    mock_summary_repo,
    mock_summarization_service,
):
    """前回要約から1時間経過でトリガー"""
    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
    )

    session_id = uuid4()

    # 1時間前の要約を返す
    old_summary = SessionSummaryResponse(
        id=uuid4(),
        user_id="hiroki",
        session_id=session_id,
        summary="Old summary",
        message_count=20,
        start_time=datetime.now() - timedelta(hours=2),
        end_time=datetime.now() - timedelta(hours=1, minutes=5),
        created_at=datetime.now() - timedelta(hours=2),
        updated_at=datetime.now() - timedelta(hours=1, minutes=5),  # 1時間5分前
    )
    mock_summary_repo.get_latest.return_value = old_summary

    # 15件のメッセージ（メッセージ数では不足）
    messages = [
        {'role': 'user', 'content': f'Message {i}', 'created_at': datetime.now()}
        for i in range(15)
    ]

    should_create = await manager._should_create_summary(
        user_id="hiroki",
        session_id=session_id,
        messages=messages,
    )

    assert should_create is True


@pytest.mark.asyncio
async def test_check_and_create_summary_success(
    mock_summary_repo,
    mock_summarization_service,
    sample_messages,
):
    """要約生成成功のテスト"""
    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
    )

    user_id = "hiroki"
    session_id = uuid4()

    # 要約が必要（20件）
    mock_summary_repo.get_latest.return_value = None

    # 要約生成が成功
    created_summary = SessionSummaryResponse(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        summary="Test summary",
        message_count=20,
        start_time=datetime.now(),
        end_time=datetime.now(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_summarization_service.create_summary.return_value = created_summary

    result = await manager.check_and_create_summary(
        user_id=user_id,
        session_id=session_id,
        messages=sample_messages,
    )

    assert result is not None
    assert result.message_count == 20
    mock_summarization_service.create_summary.assert_called_once()


@pytest.mark.asyncio
async def test_check_and_create_summary_not_needed(
    mock_summary_repo,
    mock_summarization_service,
):
    """要約生成不要のテスト"""
    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
    )

    # 10件のメッセージ（不足）
    messages = [
        {'role': 'user', 'content': f'Message {i}', 'created_at': datetime.now()}
        for i in range(10)
    ]

    mock_summary_repo.get_latest.return_value = None

    result = await manager.check_and_create_summary(
        user_id="hiroki",
        session_id=uuid4(),
        messages=messages,
    )

    assert result is None
    mock_summarization_service.create_summary.assert_not_called()


@pytest.mark.asyncio
async def test_get_session_stats(
    mock_summary_repo,
    mock_summarization_service,
    sample_messages,
):
    """セッション統計取得のテスト"""
    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
    )

    session_id = uuid4()
    mock_summary_repo.get_latest.return_value = None

    stats = await manager.get_session_stats(
        user_id="hiroki",
        session_id=session_id,
        messages=sample_messages,
    )

    assert isinstance(stats, SessionStats)
    assert stats.message_count == 20
    assert stats.session_id == session_id
    assert stats.first_message_time is not None
    assert stats.last_message_time is not None
    assert stats.duration_seconds is not None
    assert stats.has_summary is False


@pytest.mark.asyncio
async def test_custom_config(
    mock_summary_repo,
    mock_summarization_service,
):
    """カスタム設定でのマネージャー初期化"""
    config = SessionConfig(
        summary_trigger_message_count=15,
        summary_trigger_interval_seconds=1800,  # 30分
    )

    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
        config=config,
    )

    assert manager.config.summary_trigger_message_count == 15
    assert manager.config.summary_trigger_interval_seconds == 1800


@pytest.mark.asyncio
async def test_check_and_create_summary_error_handling(
    mock_summary_repo,
    mock_summarization_service,
    sample_messages,
):
    """要約生成エラー時のハンドリング"""
    manager = SessionManager(
        summary_repo=mock_summary_repo,
        summarization_service=mock_summarization_service,
    )

    mock_summary_repo.get_latest.return_value = None
    mock_summarization_service.create_summary.side_effect = Exception("API Error")

    result = await manager.check_and_create_summary(
        user_id="hiroki",
        session_id=uuid4(),
        messages=sample_messages,
    )

    # エラーでもNoneを返す（非クリティカル）
    assert result is None
