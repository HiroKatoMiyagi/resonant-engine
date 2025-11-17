"""
Unit tests for TypeProjectInferencer
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from bridge.semantic_bridge.inferencer import TypeProjectInferencer
from bridge.semantic_bridge.models import (
    EmotionState,
    EventContext,
    MemoryType,
)


class TestTypeProjectInferencer:
    """Tests for TypeProjectInferencer"""

    @pytest.fixture
    def inferencer(self):
        """Create a TypeProjectInferencer instance"""
        return TypeProjectInferencer()

    def test_infer_type_regulation(self, inferencer):
        """Test inference for regulation type"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="新しい規範を定義する必要がある",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 20, "emotion_state": EmotionState.CALM}
        result = inferencer.infer(event, extracted)
        assert result.memory_type == MemoryType.RESONANT_REGULATION

    def test_infer_type_milestone(self, inferencer):
        """Test inference for milestone type"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="プロジェクトの重要なマイルストーンを達成した",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 10, "emotion_state": EmotionState.EXCITED}
        result = inferencer.infer(event, extracted)
        assert result.memory_type == MemoryType.PROJECT_MILESTONE

    def test_infer_type_design_note(self, inferencer):
        """Test inference for design note type"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="システムアーキテクチャの設計を検討",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 25, "emotion_state": EmotionState.FOCUSED}
        result = inferencer.infer(event, extracted)
        assert result.memory_type == MemoryType.DESIGN_NOTE

    def test_infer_type_daily_reflection(self, inferencer):
        """Test inference for daily reflection type"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="今日の振り返りを行う",
            intent_type="exploration",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 15, "emotion_state": EmotionState.CALM}
        result = inferencer.infer(event, extracted)
        assert result.memory_type == MemoryType.DAILY_REFLECTION

    def test_infer_type_crisis_log_by_ci_level(self, inferencer):
        """Test inference for crisis log by high CI level"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Regular task description",
            intent_type="bug_fix",
            crisis_index=65,
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 65, "emotion_state": EmotionState.CRISIS}
        result = inferencer.infer(event, extracted)
        assert result.memory_type == MemoryType.CRISIS_LOG

    def test_infer_type_crisis_log_by_keyword(self, inferencer):
        """Test inference for crisis log by keyword"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="緊急の問題が発生している",
            intent_type="bug_fix",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 40, "emotion_state": EmotionState.STRESSED}
        result = inferencer.infer(event, extracted)
        assert result.memory_type == MemoryType.CRISIS_LOG

    def test_infer_project_resonant_engine(self, inferencer):
        """Test project inference for resonant engine"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Resonant Engineのブリッジ機能を実装",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 20}
        result = inferencer.infer(event, extracted)
        assert result.project_id == "resonant_engine"
        assert result.project_confidence > 0.5

    def test_infer_project_postgres(self, inferencer):
        """Test project inference for PostgreSQL"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="PostgreSQLのスキーマをマイグレーション",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 20}
        result = inferencer.infer(event, extracted)
        assert result.project_id == "postgres_implementation"

    def test_infer_project_memory_system(self, inferencer):
        """Test project inference for memory system"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="メモリの記憶システムを実装",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 20}
        result = inferencer.infer(event, extracted)
        assert result.project_id == "memory_system"

    def test_infer_project_from_metadata(self, inferencer):
        """Test project inference from metadata"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Some generic task",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            metadata={"project_id": "custom_project"},
        )
        extracted = {"ci_level": 20}
        result = inferencer.infer(event, extracted)
        assert result.project_id == "custom_project"
        assert result.project_confidence == 1.0

    def test_generate_tags(self, inferencer):
        """Test tag generation"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Design PostgreSQL schema for memory system",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"emotion_state": EmotionState.FOCUSED}
        tags = inferencer._generate_tags(
            event, extracted, MemoryType.DESIGN_NOTE
        )
        assert "design_note" in tags
        assert "focused" in tags
        assert "feature-request" in tags

    def test_keyword_extraction(self, inferencer):
        """Test keyword extraction"""
        text = "Implement PostgreSQL schema design with Pydantic models"
        keywords = inferencer._extract_keywords(text)
        assert "postgresql" in keywords
        assert "schema" in keywords
        assert "pydantic" in keywords

    def test_keyword_extraction_japanese(self, inferencer):
        """Test Japanese keyword extraction"""
        text = "メモリ管理システムのアーキテクチャを設計"
        keywords = inferencer._extract_keywords(text)
        assert "メモリ" in keywords or "アーキテクチャ" in keywords

    def test_pattern_matching(self, inferencer):
        """Test regex pattern matching"""
        assert inferencer._match_pattern("test design pattern", r"design|architecture")
        assert inferencer._match_pattern("システム設計", r"設計|design")
        assert not inferencer._match_pattern("simple test", r"design|architecture")

    def test_inference_confidence(self, inferencer):
        """Test that inference includes confidence scores"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Design new feature",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 20}
        result = inferencer.infer(event, extracted)
        assert 0.0 <= result.confidence <= 1.0
        assert 0.0 <= result.project_confidence <= 1.0

    def test_inference_reasoning(self, inferencer):
        """Test that inference includes reasoning"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="規範を定義する",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        extracted = {"ci_level": 20}
        result = inferencer.infer(event, extracted)
        assert result.reasoning != ""
        assert isinstance(result.reasoning, str)
