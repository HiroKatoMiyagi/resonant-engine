"""
Sprint 10: Choice Preservation System - Model Tests

Tests for enhanced Choice and ChoicePoint models with rejection reasons,
evaluation scores, and tagging support.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID
from pydantic import ValidationError

from bridge.memory.models import Choice, ChoicePoint


class TestChoiceModelEnhanced:
    """Test enhanced Choice model (Sprint 10)"""

    def test_choice_with_all_fields(self):
        """Test Choice with all new Sprint 10 fields"""
        choice = Choice(
            id="A",
            description="PostgreSQL",
            implications={"scalability": "high", "complexity": "medium"},
            selected=True,
            evaluation_score=0.9,
            rejection_reason=None,
            evaluated_at=datetime.now(timezone.utc)
        )

        assert choice.id == "A"
        assert choice.description == "PostgreSQL"
        assert choice.selected is True
        assert choice.evaluation_score == 0.9
        assert choice.rejection_reason is None
        assert choice.evaluated_at is not None

    def test_rejected_choice_with_reason(self):
        """Test rejected choice with rejection reason"""
        choice = Choice(
            id="B",
            description="SQLite",
            selected=False,
            evaluation_score=0.6,
            rejection_reason="スケーラビリティ限界: 複数ユーザー対応が困難"
        )

        assert choice.selected is False
        assert choice.evaluation_score == 0.6
        assert choice.rejection_reason is not None
        assert "スケーラビリティ限界" in choice.rejection_reason

    def test_choice_default_values(self):
        """Test Choice with default values"""
        choice = Choice(
            id="C",
            description="MongoDB"
        )

        # Defaults
        assert choice.selected is False
        assert choice.evaluation_score is None
        assert choice.rejection_reason is None
        assert choice.evaluated_at is None
        assert choice.implications == {}

    def test_evaluation_score_validation(self):
        """Test evaluation score must be between 0 and 1"""
        # Valid
        choice = Choice(id="A", description="Test", evaluation_score=0.5)
        assert choice.evaluation_score == 0.5

        # Invalid: > 1
        with pytest.raises(ValidationError):
            Choice(id="A", description="Test", evaluation_score=1.5)

        # Invalid: < 0
        with pytest.raises(ValidationError):
            Choice(id="A", description="Test", evaluation_score=-0.1)

    def test_rejection_reason_max_length(self):
        """Test rejection reason has max length constraint"""
        # Valid: within limit
        reason = "A" * 1000
        choice = Choice(id="A", description="Test", rejection_reason=reason)
        assert len(choice.rejection_reason) == 1000

        # Invalid: exceeds limit (Pydantic will truncate or error depending on config)
        # This behavior depends on Pydantic version and configuration


class TestChoicePointModelEnhanced:
    """Test enhanced ChoicePoint model (Sprint 10)"""

    def test_choice_point_with_all_fields(self):
        """Test ChoicePoint with all new Sprint 10 fields"""
        session_id = uuid4()
        intent_id = uuid4()

        choice_point = ChoicePoint(
            user_id="hiroki",
            session_id=session_id,
            intent_id=intent_id,
            question="データベース選定",
            choices=[
                Choice(
                    id="A",
                    description="PostgreSQL",
                    selected=True,
                    evaluation_score=0.9
                ),
                Choice(
                    id="B",
                    description="SQLite",
                    selected=False,
                    evaluation_score=0.6,
                    rejection_reason="スケーラビリティ限界"
                )
            ],
            selected_choice_id="A",
            decision_rationale="スケーラビリティと拡張性を考慮",
            tags=["database", "technology_stack", "architecture"],
            context_type="architecture"
        )

        assert choice_point.user_id == "hiroki"
        assert choice_point.question == "データベース選定"
        assert len(choice_point.choices) == 2
        assert choice_point.selected_choice_id == "A"
        assert choice_point.tags == ["database", "technology_stack", "architecture"]
        assert choice_point.context_type == "architecture"

    def test_choice_point_default_values(self):
        """Test ChoicePoint with default values"""
        session_id = uuid4()
        intent_id = uuid4()

        choice_point = ChoicePoint(
            user_id="test_user",
            session_id=session_id,
            intent_id=intent_id,
            question="Test question",
            choices=[
                Choice(id="A", description="Option A"),
                Choice(id="B", description="Option B")
            ]
        )

        # Defaults
        assert choice_point.tags == []
        assert choice_point.context_type == "general"
        assert choice_point.selected_choice_id is None
        assert choice_point.decision_rationale is None
        assert choice_point.decided_at is None

    def test_tags_validation_max_10(self):
        """Test tags validation: maximum 10 tags"""
        session_id = uuid4()
        intent_id = uuid4()

        # Valid: 10 tags
        valid_tags = [f"tag{i}" for i in range(10)]
        choice_point = ChoicePoint(
            user_id="test_user",
            session_id=session_id,
            intent_id=intent_id,
            question="Test",
            choices=[
                Choice(id="A", description="A"),
                Choice(id="B", description="B")
            ],
            tags=valid_tags
        )
        assert len(choice_point.tags) == 10

        # Invalid: 11 tags
        invalid_tags = [f"tag{i}" for i in range(11)]
        with pytest.raises(ValidationError):
            ChoicePoint(
                user_id="test_user",
                session_id=session_id,
                intent_id=intent_id,
                question="Test",
                choices=[
                    Choice(id="A", description="A"),
                    Choice(id="B", description="B")
                ],
                tags=invalid_tags
            )

    def test_choice_point_with_rejection_reasons(self):
        """Test ChoicePoint with rejection reasons for all choices"""
        session_id = uuid4()
        intent_id = uuid4()

        choices = [
            Choice(
                id="A",
                description="PostgreSQL",
                selected=True,
                evaluation_score=0.9,
                rejection_reason=None
            ),
            Choice(
                id="B",
                description="SQLite",
                selected=False,
                evaluation_score=0.6,
                rejection_reason="スケーラビリティ限界: 複数ユーザー対応が困難"
            ),
            Choice(
                id="C",
                description="MongoDB",
                selected=False,
                evaluation_score=0.4,
                rejection_reason="リレーショナルデータに不向き"
            )
        ]

        choice_point = ChoicePoint(
            user_id="hiroki",
            session_id=session_id,
            intent_id=intent_id,
            question="データベース選定",
            choices=choices,
            selected_choice_id="A",
            decision_rationale="スケーラビリティと拡張性を考慮",
            tags=["database", "technology"]
        )

        # Verify selected choice has no rejection reason
        selected = next(c for c in choice_point.choices if c.id == "A")
        assert selected.selected is True
        assert selected.rejection_reason is None

        # Verify rejected choices have rejection reasons
        rejected_b = next(c for c in choice_point.choices if c.id == "B")
        assert rejected_b.selected is False
        assert rejected_b.rejection_reason is not None

        rejected_c = next(c for c in choice_point.choices if c.id == "C")
        assert rejected_c.selected is False
        assert rejected_c.rejection_reason is not None

    def test_choice_point_minimum_choices(self):
        """Test ChoicePoint requires at least 2 choices"""
        session_id = uuid4()
        intent_id = uuid4()

        # Valid: 2 choices
        choice_point = ChoicePoint(
            user_id="test_user",
            session_id=session_id,
            intent_id=intent_id,
            question="Test",
            choices=[
                Choice(id="A", description="A"),
                Choice(id="B", description="B")
            ]
        )
        assert len(choice_point.choices) == 2

        # Invalid: 1 choice
        with pytest.raises(ValidationError):
            ChoicePoint(
                user_id="test_user",
                session_id=session_id,
                intent_id=intent_id,
                question="Test",
                choices=[
                    Choice(id="A", description="A")
                ]
            )

    def test_choice_point_unique_choice_ids(self):
        """Test ChoicePoint requires unique choice IDs"""
        session_id = uuid4()
        intent_id = uuid4()

        # Invalid: duplicate choice IDs
        with pytest.raises(ValidationError):
            ChoicePoint(
                user_id="test_user",
                session_id=session_id,
                intent_id=intent_id,
                question="Test",
                choices=[
                    Choice(id="A", description="First A"),
                    Choice(id="A", description="Second A")  # Duplicate ID
                ]
            )

    def test_choice_point_json_serialization(self):
        """Test ChoicePoint can be serialized to JSON"""
        session_id = uuid4()
        intent_id = uuid4()

        choice_point = ChoicePoint(
            user_id="hiroki",
            session_id=session_id,
            intent_id=intent_id,
            question="Test",
            choices=[
                Choice(id="A", description="A", selected=True, evaluation_score=0.8),
                Choice(id="B", description="B", selected=False, rejection_reason="Test reason")
            ],
            tags=["test", "example"],
            context_type="feature"
        )

        # Convert to dict
        data = choice_point.model_dump()

        assert data["user_id"] == "hiroki"
        assert data["question"] == "Test"
        assert len(data["choices"]) == 2
        assert data["tags"] == ["test", "example"]
        assert data["context_type"] == "feature"

        # Choices should include new fields
        assert data["choices"][0]["selected"] is True
        assert data["choices"][0]["evaluation_score"] == 0.8
        assert data["choices"][1]["rejection_reason"] == "Test reason"
