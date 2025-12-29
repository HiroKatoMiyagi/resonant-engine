"""
Unit tests for Semantic Bridge data models
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.services.semantic.models import (
    MemoryType,
    EmotionState,
    MemoryUnit,
    EventContext,
    InferenceResult,
    TypeInferenceRule,
    MemorySearchQuery,
)


class TestMemoryType:
    """Tests for MemoryType enum"""

    def test_memory_type_values(self):
        """Test all memory type values"""
        assert MemoryType.SESSION_SUMMARY == "session_summary"
        assert MemoryType.DAILY_REFLECTION == "daily_reflection"
        assert MemoryType.PROJECT_MILESTONE == "project_milestone"
        assert MemoryType.RESONANT_REGULATION == "resonant_regulation"
        assert MemoryType.DESIGN_NOTE == "design_note"
        assert MemoryType.CRISIS_LOG == "crisis_log"

    def test_memory_type_count(self):
        """Test that we have exactly 6 memory types"""
        assert len(MemoryType) == 6


class TestEmotionState:
    """Tests for EmotionState enum"""

    def test_emotion_state_values(self):
        """Test all emotion state values"""
        assert EmotionState.CALM == "calm"
        assert EmotionState.FOCUSED == "focused"
        assert EmotionState.STRESSED == "stressed"
        assert EmotionState.CRISIS == "crisis"
        assert EmotionState.EXCITED == "excited"
        assert EmotionState.NEUTRAL == "neutral"

    def test_emotion_state_count(self):
        """Test that we have exactly 6 emotion states"""
        assert len(EmotionState) == 6


class TestMemoryUnit:
    """Tests for MemoryUnit model"""

    def test_memory_unit_creation(self):
        """Test basic memory unit creation"""
        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Test memory",
            content="Test content",
        )
        assert unit.user_id == "hiroki"
        assert unit.type == MemoryType.SESSION_SUMMARY
        assert unit.title == "Test memory"
        assert unit.content == "Test content"
        assert isinstance(unit.id, UUID)

    def test_memory_unit_with_all_fields(self):
        """Test memory unit with all optional fields"""
        now = datetime.now(timezone.utc)
        unit = MemoryUnit(
            user_id="custom_user",
            project_id="test_project",
            type=MemoryType.DESIGN_NOTE,
            title="Full test",
            content="Full content",
            content_raw="Raw content",
            tags=["tag1", "tag2"],
            ci_level=50,
            emotion_state=EmotionState.FOCUSED,
            started_at=now,
            ended_at=now,
            metadata={"key": "value"},
        )
        assert unit.user_id == "custom_user"
        assert unit.project_id == "test_project"
        assert unit.ci_level == 50
        assert unit.emotion_state == EmotionState.FOCUSED
        assert len(unit.tags) == 2

    def test_memory_unit_uuid_generation(self):
        """Test that UUID is automatically generated"""
        unit1 = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Test",
            content="Content",
        )
        unit2 = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Test",
            content="Content",
        )
        assert unit1.id != unit2.id

    def test_memory_unit_datetime_defaults(self):
        """Test datetime default values"""
        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Test",
            content="Content",
        )
        assert isinstance(unit.created_at, datetime)
        assert isinstance(unit.updated_at, datetime)

    def test_memory_unit_json_serialization(self):
        """Test JSON serialization"""
        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Test",
            content="Content",
        )
        json_data = unit.model_dump(mode="json")
        assert isinstance(json_data["id"], str)
        assert isinstance(json_data["created_at"], str)

    def test_memory_unit_title_validation_too_long(self):
        """Test title length validation"""
        with pytest.raises(ValueError):
            MemoryUnit(
                type=MemoryType.SESSION_SUMMARY,
                title="x" * 201,  # Too long
                content="Content",
            )

    def test_memory_unit_ci_level_validation(self):
        """Test CI level range validation"""
        # Valid range
        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Test",
            content="Content",
            ci_level=50,
        )
        assert unit.ci_level == 50

        # Below range
        with pytest.raises(ValueError):
            MemoryUnit(
                type=MemoryType.SESSION_SUMMARY,
                title="Test",
                content="Content",
                ci_level=-1,
            )

        # Above range
        with pytest.raises(ValueError):
            MemoryUnit(
                type=MemoryType.SESSION_SUMMARY,
                title="Test",
                content="Content",
                ci_level=101,
            )


class TestEventContext:
    """Tests for EventContext model"""

    def test_event_context_creation(self):
        """Test basic event context creation"""
        context = EventContext(
            intent_id=uuid4(),
            intent_text="Test intent",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        assert context.intent_text == "Test intent"
        assert context.intent_type == "feature_request"

    def test_event_context_with_optional_fields(self):
        """Test event context with optional fields"""
        context = EventContext(
            intent_id=uuid4(),
            intent_text="Test intent",
            intent_type="feature_request",
            session_id=uuid4(),
            crisis_index=75,
            timestamp=datetime.now(timezone.utc),
            bridge_result={"status": "success"},
            kana_response="Response text",
            metadata={"key": "value"},
        )
        assert context.crisis_index == 75
        assert context.bridge_result == {"status": "success"}
        assert context.kana_response == "Response text"

    def test_event_context_crisis_index_validation(self):
        """Test crisis index range validation"""
        with pytest.raises(ValueError):
            EventContext(
                intent_id=uuid4(),
                intent_text="Test",
                intent_type="feature_request",
                crisis_index=101,  # Too high
                timestamp=datetime.now(timezone.utc),
            )


class TestInferenceResult:
    """Tests for InferenceResult model"""

    def test_inference_result_creation(self):
        """Test inference result creation"""
        result = InferenceResult(
            memory_type=MemoryType.DESIGN_NOTE,
            confidence=0.85,
            reasoning="Test reasoning",
        )
        assert result.memory_type == MemoryType.DESIGN_NOTE
        assert result.confidence == 0.85
        assert result.reasoning == "Test reasoning"

    def test_inference_result_with_project(self):
        """Test inference result with project"""
        result = InferenceResult(
            memory_type=MemoryType.DESIGN_NOTE,
            confidence=0.9,
            reasoning="Test",
            project_id="test_project",
            project_confidence=0.8,
            tags=["tag1", "tag2"],
            emotion_state=EmotionState.FOCUSED,
        )
        assert result.project_id == "test_project"
        assert result.project_confidence == 0.8

    def test_inference_result_tag_deduplication(self):
        """Test that duplicate tags are removed"""
        result = InferenceResult(
            memory_type=MemoryType.SESSION_SUMMARY,
            confidence=0.5,
            reasoning="Test",
            tags=["tag1", "tag1", "tag2", "tag2", "tag3"],
        )
        assert len(result.tags) == 3
        assert set(result.tags) == {"tag1", "tag2", "tag3"}

    def test_inference_result_confidence_validation(self):
        """Test confidence range validation"""
        with pytest.raises(ValueError):
            InferenceResult(
                memory_type=MemoryType.SESSION_SUMMARY,
                confidence=1.5,  # Too high
                reasoning="Test",
            )


class TestTypeInferenceRule:
    """Tests for TypeInferenceRule model"""

    def test_type_inference_rule_creation(self):
        """Test inference rule creation"""
        rule = TypeInferenceRule(
            pattern=r"test",
            memory_type=MemoryType.DESIGN_NOTE,
            priority=10,
            description="Test rule",
        )
        assert rule.pattern == r"test"
        assert rule.memory_type == MemoryType.DESIGN_NOTE
        assert rule.priority == 10


class TestMemorySearchQuery:
    """Tests for MemorySearchQuery model"""

    def test_memory_search_query_defaults(self):
        """Test default values"""
        query = MemorySearchQuery()
        assert query.user_id == "hiroki"
        assert query.limit == 10
        assert query.offset == 0
        assert query.sort_by == "created_at"
        assert query.sort_order == "desc"
        assert query.tag_mode == "any"

    def test_memory_search_query_with_filters(self):
        """Test query with various filters"""
        query = MemorySearchQuery(
            project_id="test_project",
            type=MemoryType.DESIGN_NOTE,
            tags=["tag1", "tag2"],
            ci_level_min=10,
            ci_level_max=50,
            emotion_states=[EmotionState.FOCUSED, EmotionState.CALM],
            text_query="search term",
        )
        assert query.project_id == "test_project"
        assert query.type == MemoryType.DESIGN_NOTE
        assert len(query.tags) == 2

    def test_memory_search_query_ci_level_validation(self):
        """Test CI level range validation"""
        with pytest.raises(ValueError):
            MemorySearchQuery(
                ci_level_min=60,
                ci_level_max=40,  # Max < Min
            )

    def test_memory_search_query_pagination(self):
        """Test pagination parameters"""
        query = MemorySearchQuery(limit=100, offset=50)
        assert query.limit == 100
        assert query.offset == 50

    def test_memory_search_query_tag_mode(self):
        """Test tag mode validation"""
        query = MemorySearchQuery(tag_mode="all")
        assert query.tag_mode == "all"

        query = MemorySearchQuery(tag_mode="any")
        assert query.tag_mode == "any"

        # Invalid tag mode should fail
        with pytest.raises(ValueError):
            MemorySearchQuery(tag_mode="invalid")
