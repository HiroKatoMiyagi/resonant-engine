"""
Unit tests for SemanticExtractor
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.services.semantic.extractor import SemanticExtractor
from app.services.semantic.models import EmotionState, EventContext


class TestSemanticExtractor:
    """Tests for SemanticExtractor"""

    @pytest.fixture
    def extractor(self):
        """Create a SemanticExtractor instance"""
        return SemanticExtractor()

    @pytest.fixture
    def basic_event(self):
        """Create a basic event context"""
        return EventContext(
            intent_id=uuid4(),
            intent_text="Design memory management system",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            crisis_index=25,
        )

    def test_extract_meaning(self, extractor, basic_event):
        """Test basic meaning extraction"""
        result = extractor.extract_meaning(basic_event)
        assert "title" in result
        assert "content" in result
        assert "content_raw" in result
        assert "ci_level" in result
        assert "emotion_state" in result
        assert "started_at" in result
        assert "metadata" in result

    def test_generate_title_short_text(self, extractor):
        """Test title generation for short text"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Short title",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        result = extractor._generate_title(event)
        assert result == "Short title"

    def test_generate_title_long_text(self, extractor):
        """Test title generation for long text"""
        long_text = "This is a very long intent text that should be truncated to fit within the 50 character limit for titles"
        event = EventContext(
            intent_id=uuid4(),
            intent_text=long_text,
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        result = extractor._generate_title(event)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_generate_title_with_japanese_sentence(self, extractor):
        """Test title generation with Japanese text"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="メモリ管理システムの設計。これは非常に重要なタスクです。",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        result = extractor._generate_title(event)
        assert "。" in result or len(result) <= 50

    def test_extract_content_basic(self, extractor, basic_event):
        """Test content extraction without response"""
        result = extractor._extract_content(basic_event)
        assert basic_event.intent_text in result

    def test_extract_content_with_kana_response(self, extractor):
        """Test content extraction with Kana response"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Test intent",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            kana_response="This is Kana's response",
        )
        result = extractor._extract_content(event)
        assert "Test intent" in result
        assert "【応答】" in result
        assert "This is Kana's response" in result

    def test_extract_content_with_bridge_result(self, extractor):
        """Test content extraction with bridge result"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Test intent",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            bridge_result={"status": "success", "processing_time_ms": 100},
        )
        result = extractor._extract_content(event)
        assert "Test intent" in result
        assert "【処理結果】" in result

    def test_infer_emotion_crisis(self, extractor):
        """Test emotion inference for crisis state"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Critical error",
            intent_type="bug_fix",
            timestamp=datetime.now(timezone.utc),
            crisis_index=75,
        )
        result = extractor._infer_emotion(event)
        assert result == EmotionState.CRISIS

    def test_infer_emotion_stressed(self, extractor):
        """Test emotion inference for stressed state"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Some issue",
            intent_type="bug_fix",
            timestamp=datetime.now(timezone.utc),
            crisis_index=55,
        )
        result = extractor._infer_emotion(event)
        assert result == EmotionState.STRESSED

    def test_infer_emotion_focused(self, extractor):
        """Test emotion inference for focused state"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Working on task",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            crisis_index=35,
        )
        result = extractor._infer_emotion(event)
        assert result == EmotionState.FOCUSED

    def test_infer_emotion_calm(self, extractor):
        """Test emotion inference for calm state"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Regular task",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            crisis_index=15,
        )
        result = extractor._infer_emotion(event)
        assert result == EmotionState.CALM

    def test_infer_emotion_neutral(self, extractor):
        """Test emotion inference for neutral state"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Simple task",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            crisis_index=5,
        )
        result = extractor._infer_emotion(event)
        assert result == EmotionState.NEUTRAL

    def test_extract_metadata(self, extractor, basic_event):
        """Test metadata extraction"""
        result = extractor._extract_metadata(basic_event)
        assert "intent_id" in result
        assert "intent_type" in result
        assert result["intent_type"] == "feature_request"

    def test_extract_metadata_with_session(self, extractor):
        """Test metadata extraction with session ID"""
        session_id = uuid4()
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Test",
            intent_type="feature_request",
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
        )
        result = extractor._extract_metadata(event)
        assert result["session_id"] == str(session_id)
