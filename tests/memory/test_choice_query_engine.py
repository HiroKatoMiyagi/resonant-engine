"""
Sprint 10: Choice Preservation System - Query Engine Tests

Tests for ChoiceQueryEngine including tag search, time-range filtering,
and full-text search capabilities.

Note: These tests require a PostgreSQL database with the choice_points table.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from bridge.memory.choice_query_engine import ChoiceQueryEngine, find_technology_decisions, find_recent_decisions
from bridge.memory.models import ChoicePoint, Choice


class TestChoiceQueryEngine:
    """Test ChoiceQueryEngine class"""

    @pytest.fixture
    def mock_pool(self):
        """Create a mock asyncpg pool"""
        pool = AsyncMock()
        return pool

    @pytest.fixture
    def engine(self, mock_pool):
        """Create ChoiceQueryEngine with mock pool"""
        return ChoiceQueryEngine(mock_pool)

    def test_engine_initialization(self, mock_pool):
        """Test engine can be initialized"""
        engine = ChoiceQueryEngine(mock_pool)
        assert engine.pool == mock_pool

    @pytest.mark.asyncio
    async def test_search_by_tags_or_logic(self, engine, mock_pool):
        """Test tag search with OR logic (match any tag)"""
        # Mock database response
        mock_conn = AsyncMock()
        mock_row = {
            'id': uuid4(),
            'user_id': 'test_user',
            'session_id': uuid4(),
            'intent_id': uuid4(),
            'question': 'Test question',
            'choices': '[{"id": "A", "description": "Test"}]',
            'selected_choice_id': 'A',
            'tags': ['database', 'technology'],
            'context_type': 'general',
            'created_at': datetime.now(timezone.utc),
            'decided_at': datetime.now(timezone.utc),
            'decision_rationale': 'Test',
            'metadata': {}
        }
        mock_conn.fetch.return_value = [mock_row]
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Execute search
        results = await engine.search_by_tags(
            user_id='test_user',
            tags=['database'],
            match_all=False,
            limit=10
        )

        # Verify
        assert len(results) == 1
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        assert 'tags &&' in call_args[0][0]  # OR logic query

    @pytest.mark.asyncio
    async def test_search_by_tags_and_logic(self, engine, mock_pool):
        """Test tag search with AND logic (match all tags)"""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Execute search
        results = await engine.search_by_tags(
            user_id='test_user',
            tags=['database', 'technology'],
            match_all=True,
            limit=10
        )

        # Verify
        assert len(results) == 0
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        assert 'tags @>' in call_args[0][0]  # AND logic query

    @pytest.mark.asyncio
    async def test_search_by_time_range_both_dates(self, engine, mock_pool):
        """Test time range search with both from_date and to_date"""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        from_date = datetime.now(timezone.utc) - timedelta(days=30)
        to_date = datetime.now(timezone.utc)

        # Execute search
        results = await engine.search_by_time_range(
            user_id='test_user',
            from_date=from_date,
            to_date=to_date,
            limit=10
        )

        # Verify
        assert len(results) == 0
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        query = call_args[0][0]
        assert 'decided_at >=' in query
        assert 'decided_at <=' in query

    @pytest.mark.asyncio
    async def test_search_by_time_range_from_only(self, engine, mock_pool):
        """Test time range search with only from_date"""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        from_date = datetime.now(timezone.utc) - timedelta(days=7)

        # Execute search
        results = await engine.search_by_time_range(
            user_id='test_user',
            from_date=from_date,
            to_date=None,
            limit=10
        )

        # Verify
        assert len(results) == 0
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        query = call_args[0][0]
        assert 'decided_at >=' in query
        assert 'decided_at <=' not in query

    @pytest.mark.asyncio
    async def test_search_fulltext(self, engine, mock_pool):
        """Test full-text search"""
        mock_conn = AsyncMock()
        mock_row = {
            'id': uuid4(),
            'user_id': 'test_user',
            'session_id': uuid4(),
            'intent_id': uuid4(),
            'question': 'Database selection for project',
            'choices': '[{"id": "A", "description": "PostgreSQL"}]',
            'selected_choice_id': 'A',
            'tags': ['database'],
            'context_type': 'architecture',
            'created_at': datetime.now(timezone.utc),
            'decided_at': datetime.now(timezone.utc),
            'decision_rationale': 'Test',
            'metadata': {},
            'rank': 0.5  # Rank field from fulltext search
        }
        mock_conn.fetch.return_value = [mock_row]
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Execute search
        results = await engine.search_fulltext(
            user_id='test_user',
            search_text='database',
            limit=10
        )

        # Verify
        assert len(results) == 1
        assert results[0].question == 'Database selection for project'
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        query = call_args[0][0]
        assert 'ts_rank' in query
        assert 'to_tsvector' in query

    @pytest.mark.asyncio
    async def test_get_relevant_choices_for_context(self, engine, mock_pool):
        """Test context relevance search"""
        mock_conn = AsyncMock()
        mock_rows = [
            {
                'id': uuid4(),
                'user_id': 'test_user',
                'session_id': uuid4(),
                'intent_id': uuid4(),
                'question': 'Which database should we use?',
                'choices': '[{"id": "A", "description": "PostgreSQL"}]',
                'selected_choice_id': 'A',
                'tags': ['database', 'technology'],
                'context_type': 'architecture',
                'created_at': datetime.now(timezone.utc),
                'decided_at': datetime.now(timezone.utc),
                'decision_rationale': 'Test',
                'metadata': {},
                'rank': 0.8
            },
            {
                'id': uuid4(),
                'user_id': 'test_user',
                'session_id': uuid4(),
                'intent_id': uuid4(),
                'question': 'Database configuration',
                'choices': '[{"id": "A", "description": "Config"}]',
                'selected_choice_id': 'A',
                'tags': ['configuration'],
                'context_type': 'feature',
                'created_at': datetime.now(timezone.utc),
                'decided_at': datetime.now(timezone.utc),
                'decision_rationale': 'Test',
                'metadata': {},
                'rank': 0.6
            }
        ]
        mock_conn.fetch.return_value = mock_rows
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Execute search with tag filter
        results = await engine.get_relevant_choices_for_context(
            user_id='test_user',
            current_question='What database are we using?',
            tags=['database'],
            limit=3
        )

        # Verify: should filter by tag
        assert len(results) == 1
        assert 'database' in results[0].tags

    @pytest.mark.asyncio
    async def test_get_relevant_choices_no_tag_filter(self, engine, mock_pool):
        """Test context relevance search without tag filter"""
        mock_conn = AsyncMock()
        mock_rows = [
            {
                'id': uuid4(),
                'user_id': 'test_user',
                'session_id': uuid4(),
                'intent_id': uuid4(),
                'question': 'Test question 1',
                'choices': '[{"id": "A", "description": "Test"}]',
                'selected_choice_id': 'A',
                'tags': ['tag1'],
                'context_type': 'general',
                'created_at': datetime.now(timezone.utc),
                'decided_at': datetime.now(timezone.utc),
                'decision_rationale': 'Test',
                'metadata': {},
                'rank': 0.9
            },
            {
                'id': uuid4(),
                'user_id': 'test_user',
                'session_id': uuid4(),
                'intent_id': uuid4(),
                'question': 'Test question 2',
                'choices': '[{"id": "A", "description": "Test"}]',
                'selected_choice_id': 'A',
                'tags': ['tag2'],
                'context_type': 'general',
                'created_at': datetime.now(timezone.utc),
                'decided_at': datetime.now(timezone.utc),
                'decision_rationale': 'Test',
                'metadata': {},
                'rank': 0.7
            }
        ]
        mock_conn.fetch.return_value = mock_rows
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Execute search without tag filter
        results = await engine.get_relevant_choices_for_context(
            user_id='test_user',
            current_question='Test',
            tags=None,
            limit=3
        )

        # Verify: should return all results (no tag filtering)
        assert len(results) == 2


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.mark.asyncio
    async def test_find_technology_decisions(self):
        """Test find_technology_decisions convenience function"""
        # Mock engine
        mock_engine = AsyncMock(spec=ChoiceQueryEngine)
        mock_engine.search_by_tags.return_value = []

        # Execute
        results = await find_technology_decisions(
            engine=mock_engine,
            user_id='test_user',
            category='database',
            limit=5
        )

        # Verify
        assert results == []
        mock_engine.search_by_tags.assert_called_once_with(
            user_id='test_user',
            tags=['database'],
            match_all=False,
            limit=5
        )

    @pytest.mark.asyncio
    async def test_find_recent_decisions(self):
        """Test find_recent_decisions convenience function"""
        # Mock engine
        mock_engine = AsyncMock(spec=ChoiceQueryEngine)
        mock_engine.search_by_time_range.return_value = []

        # Execute
        results = await find_recent_decisions(
            engine=mock_engine,
            user_id='test_user',
            days=7,
            limit=10
        )

        # Verify
        assert results == []
        mock_engine.search_by_time_range.assert_called_once()
        call_args = mock_engine.search_by_time_range.call_args
        assert call_args[1]['user_id'] == 'test_user'
        assert call_args[1]['to_date'] is None
        assert call_args[1]['limit'] == 10
