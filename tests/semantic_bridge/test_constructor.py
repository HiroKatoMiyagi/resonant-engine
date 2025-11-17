"""
Unit tests for MemoryUnitConstructor
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from bridge.semantic_bridge.constructor import MemoryUnitConstructor
from bridge.semantic_bridge.models import (
    EmotionState,
    InferenceResult,
    MemoryType,
)


class TestMemoryUnitConstructor:
    """Tests for MemoryUnitConstructor"""

    @pytest.fixture
    def constructor(self):
        """Create a MemoryUnitConstructor instance"""
        return MemoryUnitConstructor()

    @pytest.fixture
    def extracted_data(self):
        """Create sample extracted data"""
        return {
            "title": "Test memory unit",
            "content": "This is the content of the memory unit",
            "content_raw": "Original intent text",
            "ci_level": 35,
            "emotion_state": EmotionState.FOCUSED,
            "started_at": datetime.now(timezone.utc),
            "metadata": {"intent_id": str(uuid4()), "intent_type": "feature_request"},
        }

    @pytest.fixture
    def inference_result(self):
        """Create sample inference result"""
        return InferenceResult(
            memory_type=MemoryType.DESIGN_NOTE,
            confidence=0.85,
            reasoning="Design keywords detected",
            project_id="test_project",
            project_confidence=0.9,
            tags=["design_note", "focused", "test"],
            emotion_state=EmotionState.FOCUSED,
        )

    @pytest.mark.asyncio
    async def test_construct_memory_unit(self, constructor, extracted_data, inference_result):
        """Test basic memory unit construction"""
        unit = await constructor.construct(extracted_data, inference_result)
        assert unit.title == "Test memory unit"
        assert unit.content == "This is the content of the memory unit"
        assert unit.type == MemoryType.DESIGN_NOTE
        assert unit.project_id == "test_project"
        assert unit.ci_level == 35

    @pytest.mark.asyncio
    async def test_construct_includes_inference_metadata(
        self, constructor, extracted_data, inference_result
    ):
        """Test that inference metadata is included"""
        unit = await constructor.construct(extracted_data, inference_result)
        assert "inference_confidence" in unit.metadata
        assert "inference_reasoning" in unit.metadata
        assert "project_confidence" in unit.metadata
        assert unit.metadata["inference_confidence"] == 0.85

    def test_validate_success(self, constructor):
        """Test validation passes for valid unit"""
        from bridge.semantic_bridge.models import MemoryUnit

        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Valid title",
            content="Valid content",
            ci_level=50,
        )
        # Should not raise
        constructor._validate(unit)

    def test_validate_title_required(self, constructor):
        """Test validation fails for empty title"""
        from bridge.semantic_bridge.models import MemoryUnit

        # Pydantic already validates min_length at creation time
        with pytest.raises(ValueError):
            unit = MemoryUnit(
                type=MemoryType.SESSION_SUMMARY,
                title="",
                content="Content",
            )

    def test_validate_title_too_long(self, constructor):
        """Test validation fails for title > 200 chars"""
        from bridge.semantic_bridge.models import MemoryUnit

        # Pydantic already validates max_length at creation time
        with pytest.raises(ValueError):
            unit = MemoryUnit(
                type=MemoryType.SESSION_SUMMARY,
                title="x" * 201,
                content="Content",
            )

    def test_validate_content_required(self, constructor):
        """Test validation fails for empty content"""
        from bridge.semantic_bridge.models import MemoryUnit

        # Pydantic already validates min_length at creation time
        with pytest.raises(ValueError):
            unit = MemoryUnit(
                type=MemoryType.SESSION_SUMMARY,
                title="Title",
                content="",
            )

    def test_validate_ci_level_range(self, constructor):
        """Test CI level range validation"""
        from bridge.semantic_bridge.models import MemoryUnit

        # Valid
        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Title",
            content="Content",
            ci_level=50,
        )
        constructor._validate(unit)  # Should pass

    def test_validate_too_many_tags(self, constructor):
        """Test validation fails for too many tags"""
        from bridge.semantic_bridge.models import MemoryUnit

        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Title",
            content="Content",
            tags=[f"tag{i}" for i in range(25)],  # Too many
        )
        with pytest.raises(ValueError, match="Too many tags"):
            constructor._validate(unit)

    def test_construct_sync(self, constructor, extracted_data, inference_result):
        """Test synchronous construction"""
        unit = constructor.construct_sync(extracted_data, inference_result)
        assert unit.title == "Test memory unit"
        assert unit.type == MemoryType.DESIGN_NOTE

    @pytest.mark.asyncio
    async def test_construct_with_none_optional_fields(self, constructor, inference_result):
        """Test construction with None optional fields"""
        extracted = {
            "title": "Minimal unit",
            "content": "Minimal content",
            "ci_level": None,
            "emotion_state": None,
            "metadata": {},
        }
        unit = await constructor.construct(extracted, inference_result)
        assert unit.title == "Minimal unit"
        assert unit.ci_level is None
