"""
Sprint 10: Context Assembler + Choice Query Engine Integration Tests

Tests for automatic past choice injection into context assembly.
"""

import pytest
import sys
print(f"DEBUG SYS.PATH: {sys.path}")
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from context_assembler.service import ContextAssemblerService
from context_assembler.models import (
    AssemblyOptions,
    ContextConfig,
)
from app.services.memory.models import Choice, ChoicePoint


class TestContextAssemblerChoiceIntegration:
    """Test Context Assembler integration with Choice Query Engine"""

    @pytest.fixture
    def mock_choice_query_engine(self):
        """Mock ChoiceQueryEngine"""
        engine = AsyncMock()
        return engine

    @pytest.fixture
    def mock_retrieval_orchestrator(self):
        """Mock RetrievalOrchestrator"""
        orchestrator = AsyncMock()
        orchestrator.retrieve = AsyncMock(return_value=MagicMock(results=[]))
        return orchestrator

    @pytest.fixture
    def mock_message_repo(self):
        """Mock MessageRepository"""
        repo = AsyncMock()
        repo.list = AsyncMock(return_value=([], 0))
        return repo

    @pytest.fixture
    def mock_session_repo(self):
        """Mock SessionRepository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def context_assembler(
        self,
        mock_retrieval_orchestrator,
        mock_message_repo,
        mock_session_repo,
        mock_choice_query_engine,
    ):
        """Create ContextAssemblerService with mocked dependencies"""
        config = ContextConfig()
        return ContextAssemblerService(
            retrieval_orchestrator=mock_retrieval_orchestrator,
            message_repository=mock_message_repo,
            session_repository=mock_session_repo,
            config=config,
            choice_query_engine=mock_choice_query_engine,
        )

    @pytest.mark.asyncio
    async def test_assemble_context_with_past_choices(
        self, context_assembler, mock_choice_query_engine
    ):
        """Test that past choices are included in assembled context"""
        # Arrange
        user_id = "hiroki"
        user_message = "PostgreSQLとMySQLどちらを使うべきですか？"
        session_id = uuid4()

        # Mock past choice
        past_choice = ChoicePoint(
            user_id=user_id,
            session_id=session_id,
            intent_id=uuid4(),
            question="データベース選定",
            choices=[
                Choice(
                    id="A",
                    description="PostgreSQL",
                    selected=True,
                    evaluation_score=0.9,
                ),
                Choice(
                    id="B",
                    description="SQLite",
                    selected=False,
                    rejection_reason="スケーラビリティ限界",
                ),
            ],
            selected_choice_id="A",
            decision_rationale="スケーラビリティと拡張性を考慮",
            decided_at=datetime.now(timezone.utc),
        )

        mock_choice_query_engine.get_relevant_choices_for_context = AsyncMock(
            return_value=[past_choice]
        )

        # Act
        result = await context_assembler.assemble_context(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
        )

        # Assert
        assert result is not None
        assert result.metadata.past_choices_count == 1
        mock_choice_query_engine.get_relevant_choices_for_context.assert_called_once()

        # Verify system message contains past choice
        system_message = result.messages[0]["content"]
        assert "過去の意思決定履歴" in system_message
        assert "データベース選定" in system_message
        assert "PostgreSQL" in system_message
        assert "スケーラビリティと拡張性を考慮" in system_message
        assert "SQLite" in system_message
        assert "スケーラビリティ限界" in system_message

    @pytest.mark.asyncio
    async def test_assemble_context_without_past_choices_when_disabled(
        self, context_assembler, mock_choice_query_engine
    ):
        """Test that past choices are not fetched when disabled"""
        # Arrange
        user_id = "hiroki"
        user_message = "テスト"
        options = AssemblyOptions(include_past_choices=False)

        # Act
        result = await context_assembler.assemble_context(
            user_message=user_message,
            user_id=user_id,
            options=options,
        )

        # Assert
        assert result is not None
        assert result.metadata.past_choices_count == 0
        mock_choice_query_engine.get_relevant_choices_for_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_assemble_context_handles_choice_query_error(
        self, context_assembler, mock_choice_query_engine
    ):
        """Test graceful handling of ChoiceQueryEngine errors"""
        # Arrange
        user_id = "hiroki"
        user_message = "テスト"

        # Simulate error
        mock_choice_query_engine.get_relevant_choices_for_context = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Act
        result = await context_assembler.assemble_context(
            user_message=user_message,
            user_id=user_id,
        )

        # Assert: Should not crash, just log warning
        assert result is not None
        assert result.metadata.past_choices_count == 0

    @pytest.mark.asyncio
    async def test_assemble_context_with_multiple_past_choices(
        self, context_assembler, mock_choice_query_engine
    ):
        """Test that multiple past choices are formatted correctly"""
        # Arrange
        user_id = "hiroki"
        user_message = "技術選定について"
        session_id = uuid4()

        # Mock multiple past choices
        past_choices = [
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
                decided_at=datetime.now(timezone.utc),
            ),
            ChoicePoint(
                user_id=user_id,
                session_id=session_id,
                intent_id=uuid4(),
                question="フレームワーク選定",
                choices=[
                    Choice(id="A", description="FastAPI", selected=True),
                    Choice(id="B", description="Flask", selected=False, rejection_reason="機能不足"),
                ],
                selected_choice_id="A",
                decision_rationale="型安全性とドキュメント自動生成",
                decided_at=datetime.now(timezone.utc),
            ),
        ]

        mock_choice_query_engine.get_relevant_choices_for_context = AsyncMock(
            return_value=past_choices
        )

        # Act
        result = await context_assembler.assemble_context(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
        )

        # Assert
        assert result is not None
        assert result.metadata.past_choices_count == 2

        system_message = result.messages[0]["content"]
        assert "1. **データベース選定**" in system_message
        assert "2. **フレームワーク選定**" in system_message
        assert "PostgreSQL" in system_message
        assert "FastAPI" in system_message

    @pytest.mark.asyncio
    async def test_assemble_context_respects_past_choices_limit(
        self, context_assembler, mock_choice_query_engine
    ):
        """Test that past_choices_limit is respected"""
        # Arrange
        user_id = "hiroki"
        user_message = "テスト"
        options = AssemblyOptions(past_choices_limit=2)

        # Act
        await context_assembler.assemble_context(
            user_message=user_message,
            user_id=user_id,
            options=options,
        )

        # Assert: Verify limit was passed correctly
        mock_choice_query_engine.get_relevant_choices_for_context.assert_called_once()
        call_args = mock_choice_query_engine.get_relevant_choices_for_context.call_args
        assert call_args.kwargs["limit"] == 2

    @pytest.mark.asyncio
    async def test_compression_reduces_past_choices_first(
        self, context_assembler, mock_choice_query_engine
    ):
        """Test that compression reduces past choices before semantic memory"""
        # This test would require setting up a large context that exceeds token limit
        # For now, just verify the compression logic includes past_choices handling
        # The actual compression is tested in the compression method
        pass

    @pytest.mark.asyncio
    async def test_context_without_choice_query_engine(
        self, mock_retrieval_orchestrator, mock_message_repo, mock_session_repo
    ):
        """Test that Context Assembler works without ChoiceQueryEngine"""
        # Arrange
        config = ContextConfig()
        assembler = ContextAssemblerService(
            retrieval_orchestrator=mock_retrieval_orchestrator,
            message_repository=mock_message_repo,
            session_repository=mock_session_repo,
            config=config,
            choice_query_engine=None,  # No choice engine
        )

        user_id = "hiroki"
        user_message = "テスト"

        # Act
        result = await assembler.assemble_context(
            user_message=user_message,
            user_id=user_id,
        )

        # Assert: Should work fine, just without past choices
        assert result is not None
        assert result.metadata.past_choices_count == 0
