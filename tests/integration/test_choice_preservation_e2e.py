"""
Sprint 10: Choice Preservation System - E2E Tests

End-to-end tests covering the complete flow:
1. Create Choice Point
2. Decide with rejection reasons
3. Search by tags/time/fulltext
4. Context Assembler integration
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from bridge.memory.models import Choice, ChoicePoint
from bridge.memory.service import MemoryManagementService
from bridge.memory.choice_query_engine import ChoiceQueryEngine
from context_assembler.service import ContextAssemblerService
from context_assembler.models import ContextConfig, AssemblyOptions


class TestChoicePreservationE2E:
    """End-to-end tests for Choice Preservation System"""

    @pytest.fixture
    def mock_pool(self):
        """Mock asyncpg connection pool"""
        pool = AsyncMock()
        conn = AsyncMock()

        # Mock acquire context manager
        pool.acquire = AsyncMock(return_value=conn)
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock(return_value=None)

        return pool

    @pytest.fixture
    def memory_service(self, mock_pool):
        """Create MemoryManagementService with mock pool"""
        return MemoryManagementService(pool=mock_pool)

    @pytest.fixture
    def choice_query_engine(self, mock_pool):
        """Create ChoiceQueryEngine with mock pool"""
        return ChoiceQueryEngine(pool=mock_pool)

    @pytest.mark.asyncio
    async def test_full_choice_preservation_flow(self, memory_service, mock_pool):
        """
        Complete flow test: Create → Decide → Search → Verify

        This test simulates a user making a technology decision,
        then searching for it later.
        """
        # Setup
        user_id = "hiroki"
        session_id = uuid4()
        intent_id = uuid4()

        # Mock database responses
        choice_point_id = uuid4()
        conn = await mock_pool.acquire().__aenter__()

        # Mock INSERT for create_choice_point_enhanced
        conn.fetchval = AsyncMock(return_value=choice_point_id)

        # Mock SELECT for retrieval
        mock_row = {
            "id": choice_point_id,
            "user_id": user_id,
            "session_id": session_id,
            "intent_id": intent_id,
            "question": "データベース選定",
            "choices": [
                {
                    "id": "A",
                    "description": "PostgreSQL",
                    "implications": {},
                    "selected": True,
                    "evaluation_score": 0.9,
                    "rejection_reason": None,
                    "evaluated_at": None,
                },
                {
                    "id": "B",
                    "description": "SQLite",
                    "implications": {},
                    "selected": False,
                    "evaluation_score": 0.6,
                    "rejection_reason": "スケーラビリティ限界",
                    "evaluated_at": None,
                },
                {
                    "id": "C",
                    "description": "MongoDB",
                    "implications": {},
                    "selected": False,
                    "evaluation_score": 0.4,
                    "rejection_reason": "リレーショナルデータに不向き",
                    "evaluated_at": None,
                }
            ],
            "selected_choice_id": "A",
            "tags": ["database", "technology_stack"],
            "context_type": "architecture",
            "created_at": datetime.now(timezone.utc),
            "decided_at": datetime.now(timezone.utc),
            "decision_rationale": "スケーラビリティと拡張性を考慮",
            "metadata": {},
        }

        conn.fetchrow = AsyncMock(return_value=mock_row)

        # Step 1: Create Choice Point
        cp = await memory_service.create_choice_point_enhanced(
            user_id=user_id,
            session_id=session_id,
            intent_id=intent_id,
            question="データベース選定",
            choices=[
                Choice(id="A", description="PostgreSQL"),
                Choice(id="B", description="SQLite"),
                Choice(id="C", description="MongoDB"),
            ],
            tags=["database", "technology_stack"],
            context_type="architecture",
        )

        # Verify creation
        assert cp is not None
        assert cp.id == choice_point_id
        assert cp.question == "データベース選定"
        assert len(cp.choices) == 3

        # Step 2: Decide with rejection reasons
        # Mock UPDATE for decide
        conn.execute = AsyncMock(return_value="UPDATE 1")

        cp = await memory_service.decide_choice_enhanced(
            choice_point_id=choice_point_id,
            selected_choice_id="A",
            rationale="スケーラビリティと拡張性を考慮",
            rejection_reasons={
                "B": "スケーラビリティ限界",
                "C": "リレーショナルデータに不向き",
            }
        )

        # Verify decision
        assert cp.selected_choice_id == "A"
        assert cp.decision_rationale == "スケーラビリティと拡張性を考慮"

        selected = next(c for c in cp.choices if c.id == "A")
        assert selected.selected is True
        assert selected.rejection_reason is None

        rejected_b = next(c for c in cp.choices if c.id == "B")
        assert rejected_b.selected is False
        assert rejected_b.rejection_reason == "スケーラビリティ限界"

        rejected_c = next(c for c in cp.choices if c.id == "C")
        assert rejected_c.selected is False
        assert rejected_c.rejection_reason == "リレーショナルデータに不向き"

    @pytest.mark.asyncio
    async def test_search_and_context_integration(
        self, memory_service, choice_query_engine, mock_pool
    ):
        """
        Test search functionality and Context Assembler integration

        Simulates searching for past decisions and using them in context.
        """
        # Setup
        user_id = "hiroki"
        session_id = uuid4()

        # Mock database for search
        conn = await mock_pool.acquire().__aenter__()

        mock_rows = [
            {
                "id": uuid4(),
                "user_id": user_id,
                "session_id": session_id,
                "intent_id": uuid4(),
                "question": "データベース選定",
                "choices": [
                    {"id": "A", "description": "PostgreSQL", "selected": True},
                    {"id": "B", "description": "MySQL", "selected": False, "rejection_reason": "ライセンス懸念"},
                ],
                "selected_choice_id": "A",
                "tags": ["database", "technology"],
                "context_type": "architecture",
                "created_at": datetime.now(timezone.utc),
                "decided_at": datetime.now(timezone.utc),
                "decision_rationale": "拡張性重視",
                "metadata": {},
            },
            {
                "id": uuid4(),
                "user_id": user_id,
                "session_id": session_id,
                "intent_id": uuid4(),
                "question": "フレームワーク選定",
                "choices": [
                    {"id": "A", "description": "FastAPI", "selected": True},
                    {"id": "B", "description": "Flask", "selected": False, "rejection_reason": "機能不足"},
                ],
                "selected_choice_id": "A",
                "tags": ["framework", "technology"],
                "context_type": "architecture",
                "created_at": datetime.now(timezone.utc),
                "decided_at": datetime.now(timezone.utc),
                "decision_rationale": "型安全性とドキュメント自動生成",
                "metadata": {},
            }
        ]

        conn.fetch = AsyncMock(return_value=mock_rows)

        # Step 1: Search by tags
        results = await choice_query_engine.search_by_tags(
            user_id=user_id,
            tags=["technology"],
            match_all=False,
            limit=10
        )

        # Verify search results
        assert len(results) == 2
        assert results[0].question == "データベース選定"
        assert results[1].question == "フレームワーク選定"

        # Step 2: Test Context Assembler integration
        # Create minimal Context Assembler with mock dependencies
        mock_retrieval = AsyncMock()
        mock_retrieval.retrieve = AsyncMock(return_value=MagicMock(results=[]))

        mock_message_repo = AsyncMock()
        mock_message_repo.list = AsyncMock(return_value=([], 0))

        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id = AsyncMock(return_value=None)

        # Mock choice_query_engine for context assembler
        mock_choice_engine = AsyncMock()
        mock_choice_engine.get_relevant_choices_for_context = AsyncMock(
            return_value=[
                ChoicePoint(
                    user_id=user_id,
                    session_id=session_id,
                    intent_id=uuid4(),
                    question="データベース選定",
                    choices=[
                        Choice(id="A", description="PostgreSQL", selected=True),
                        Choice(id="B", description="MySQL", selected=False, rejection_reason="ライセンス懸念"),
                    ],
                    selected_choice_id="A",
                    decision_rationale="拡張性重視",
                    tags=["database", "technology"],
                    context_type="architecture",
                    decided_at=datetime.now(timezone.utc),
                )
            ]
        )

        context_assembler = ContextAssemblerService(
            retrieval_orchestrator=mock_retrieval,
            message_repository=mock_message_repo,
            session_repository=mock_session_repo,
            config=ContextConfig(),
            choice_query_engine=mock_choice_engine,
        )

        # Assemble context
        user_message = "MySQLとPostgreSQLどちらを使うべきですか？"
        result = await context_assembler.assemble_context(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
        )

        # Verify context includes past choices
        assert result is not None
        assert result.metadata.past_choices_count == 1

        system_message = result.messages[0]["content"]
        assert "過去の意思決定履歴" in system_message
        assert "データベース選定" in system_message
        assert "PostgreSQL" in system_message

    @pytest.mark.asyncio
    async def test_time_range_search(self, choice_query_engine, mock_pool):
        """Test searching choices by time range"""
        # Setup
        user_id = "hiroki"
        from_date = datetime.now(timezone.utc) - timedelta(days=7)
        to_date = datetime.now(timezone.utc)

        # Mock database
        conn = await mock_pool.acquire().__aenter__()

        mock_rows = [
            {
                "id": uuid4(),
                "user_id": user_id,
                "session_id": uuid4(),
                "intent_id": uuid4(),
                "question": "Recent decision",
                "choices": [{"id": "A", "description": "Option A", "selected": True}],
                "selected_choice_id": "A",
                "tags": ["recent"],
                "context_type": "general",
                "created_at": datetime.now(timezone.utc) - timedelta(days=3),
                "decided_at": datetime.now(timezone.utc) - timedelta(days=3),
                "decision_rationale": "Test",
                "metadata": {},
            }
        ]

        conn.fetch = AsyncMock(return_value=mock_rows)

        # Search
        results = await choice_query_engine.search_by_time_range(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            limit=10
        )

        # Verify
        assert len(results) == 1
        assert results[0].question == "Recent decision"
        assert results[0].decided_at >= from_date
        assert results[0].decided_at <= to_date

    @pytest.mark.asyncio
    async def test_fulltext_search(self, choice_query_engine, mock_pool):
        """Test full-text search functionality"""
        # Setup
        user_id = "hiroki"
        search_text = "database"

        # Mock database
        conn = await mock_pool.acquire().__aenter__()

        mock_rows = [
            {
                "id": uuid4(),
                "user_id": user_id,
                "session_id": uuid4(),
                "intent_id": uuid4(),
                "question": "What database should we use?",
                "choices": [
                    {"id": "A", "description": "PostgreSQL", "selected": True},
                    {"id": "B", "description": "MySQL", "selected": False},
                ],
                "selected_choice_id": "A",
                "tags": ["database"],
                "context_type": "architecture",
                "created_at": datetime.now(timezone.utc),
                "decided_at": datetime.now(timezone.utc),
                "decision_rationale": "Best for our use case",
                "metadata": {},
                "rank": 0.75,  # ts_rank result
            }
        ]

        conn.fetch = AsyncMock(return_value=mock_rows)

        # Search
        results = await choice_query_engine.search_fulltext(
            user_id=user_id,
            search_text=search_text,
            limit=10
        )

        # Verify
        assert len(results) == 1
        assert "database" in results[0].question.lower()

    @pytest.mark.asyncio
    async def test_context_relevance_for_similar_questions(
        self, choice_query_engine, mock_pool
    ):
        """
        Test that get_relevant_choices_for_context returns choices
        relevant to the current question
        """
        # Setup
        user_id = "hiroki"
        current_question = "Should we use PostgreSQL or MongoDB?"

        # Mock database
        conn = await mock_pool.acquire().__aenter__()

        # Mock relevant past choices
        mock_rows = [
            {
                "id": uuid4(),
                "user_id": user_id,
                "session_id": uuid4(),
                "intent_id": uuid4(),
                "question": "データベース選定: PostgreSQL vs MySQL",
                "choices": [
                    {"id": "A", "description": "PostgreSQL", "selected": True},
                    {"id": "B", "description": "MySQL", "selected": False, "rejection_reason": "ライセンス懸念"},
                ],
                "selected_choice_id": "A",
                "tags": ["database", "technology"],
                "context_type": "architecture",
                "created_at": datetime.now(timezone.utc),
                "decided_at": datetime.now(timezone.utc),
                "decision_rationale": "拡張性とパフォーマンス",
                "metadata": {},
                "rank": 0.85,
            }
        ]

        conn.fetch = AsyncMock(return_value=mock_rows)

        # Get relevant choices
        results = await choice_query_engine.get_relevant_choices_for_context(
            user_id=user_id,
            current_question=current_question,
            limit=3
        )

        # Verify
        assert len(results) == 1
        assert "PostgreSQL" in results[0].question
        assert results[0].selected_choice_id == "A"
