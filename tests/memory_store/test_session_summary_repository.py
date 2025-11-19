"""SessionSummaryRepository単体テスト"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from memory_store.session_summary_repository import SessionSummaryRepository
from memory_store.models import SessionSummaryResponse


@pytest.fixture
def mock_pool():
    """Mock PostgreSQL pool"""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool, conn


@pytest.mark.asyncio
async def test_save_new_summary(mock_pool):
    """新規Session Summaryの保存"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    summary_id = uuid4()
    conn.fetchrow.return_value = {'id': summary_id}

    user_id = "hiroki"
    session_id = uuid4()
    summary = "Test summary"
    start_time = datetime.now() - timedelta(hours=2)
    end_time = datetime.now()

    result_id = await repo.save(
        user_id=user_id,
        session_id=session_id,
        summary=summary,
        message_count=20,
        start_time=start_time,
        end_time=end_time,
    )

    assert result_id == summary_id
    conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_with_session_id(mock_pool):
    """特定セッションの最新要約取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    session_id = uuid4()
    conn.fetchrow.return_value = {
        'id': uuid4(),
        'user_id': 'hiroki',
        'session_id': session_id,
        'summary': 'Test summary',
        'message_count': 20,
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }

    result = await repo.get_latest(user_id="hiroki", session_id=session_id)

    assert result is not None
    assert isinstance(result, SessionSummaryResponse)
    assert result.session_id == session_id


@pytest.mark.asyncio
async def test_get_latest_without_session_id(mock_pool):
    """ユーザーの最新要約取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    conn.fetchrow.return_value = {
        'id': uuid4(),
        'user_id': 'hiroki',
        'session_id': uuid4(),
        'summary': 'Latest summary',
        'message_count': 30,
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }

    result = await repo.get_latest(user_id="hiroki")

    assert result is not None
    assert result.summary == 'Latest summary'


@pytest.mark.asyncio
async def test_get_by_session(mock_pool):
    """セッションIDで要約取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    session_id = uuid4()
    conn.fetchrow.return_value = {
        'id': uuid4(),
        'user_id': 'hiroki',
        'session_id': session_id,
        'summary': 'Session summary',
        'message_count': 25,
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }

    result = await repo.get_by_session(session_id)

    assert result is not None
    assert result.session_id == session_id


@pytest.mark.asyncio
async def test_list_by_user(mock_pool):
    """ユーザーの要約一覧取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    conn.fetch.return_value = [
        {
            'id': uuid4(),
            'user_id': 'hiroki',
            'session_id': uuid4(),
            'summary': f'Summary {i}',
            'message_count': 20 + i,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
        for i in range(5)
    ]

    results = await repo.list_by_user(user_id="hiroki", limit=10)

    assert len(results) == 5
    assert all(isinstance(r, SessionSummaryResponse) for r in results)


@pytest.mark.asyncio
async def test_delete_summary(mock_pool):
    """Session Summaryの削除"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    summary_id = uuid4()
    conn.execute.return_value = "DELETE 1"

    result = await repo.delete(summary_id)

    assert result is True
    conn.execute.assert_called_once()
