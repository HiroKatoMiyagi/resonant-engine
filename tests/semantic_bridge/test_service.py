"""
Unit tests for SemanticBridgeService
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from bridge.semantic_bridge.service import SemanticBridgeService
from bridge.semantic_bridge.models import EventContext, MemoryType
from bridge.semantic_bridge.repositories import InMemoryUnitRepository


class TestSemanticBridgeService:
    """Tests for SemanticBridgeService"""

    @pytest.fixture
    def service(self):
        """Create a SemanticBridgeService instance"""
        repo = InMemoryUnitRepository()
        return SemanticBridgeService(memory_repo=repo)

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

    @pytest.mark.asyncio
    async def test_process_event_full_pipeline(self, service, basic_event):
        """Test complete event processing pipeline"""
        memory_unit = await service.process_event(basic_event)
        assert memory_unit.id is not None
        assert memory_unit.type == MemoryType.DESIGN_NOTE
        assert "Design memory management system" in memory_unit.title

    @pytest.mark.asyncio
    async def test_process_event_regulation_type(self, service):
        """Test processing event for regulation type"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="新しい規範を定義する",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            crisis_index=15,
        )
        memory_unit = await service.process_event(event)
        assert memory_unit.type == MemoryType.RESONANT_REGULATION

    @pytest.mark.asyncio
    async def test_process_event_milestone_type(self, service):
        """Test processing event for milestone type"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="重要なマイルストーンを達成した",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            crisis_index=10,
        )
        memory_unit = await service.process_event(event)
        assert memory_unit.type == MemoryType.PROJECT_MILESTONE

    @pytest.mark.asyncio
    async def test_process_event_crisis_log(self, service):
        """Test processing event for crisis log"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="システムエラー発生",
            intent_type="bug_fix",
            timestamp=datetime.now(timezone.utc),
            crisis_index=70,
        )
        memory_unit = await service.process_event(event)
        assert memory_unit.type == MemoryType.CRISIS_LOG

    @pytest.mark.asyncio
    async def test_process_event_project_inference(self, service):
        """Test project inference during processing"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Resonant Engineのブリッジ機能を実装",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
            crisis_index=20,
        )
        memory_unit = await service.process_event(event)
        assert memory_unit.project_id == "resonant_engine"

    @pytest.mark.asyncio
    async def test_process_event_saves_to_repository(self, service):
        """Test that processed event is saved to repository"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Test task",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        memory_unit = await service.process_event(event)

        # Verify it's saved
        repo = service.memory_repo
        saved_unit = await repo.get_by_id(memory_unit.id)
        assert saved_unit is not None
        assert saved_unit.id == memory_unit.id

    def test_process_event_sync(self, service):
        """Test synchronous event processing"""
        event = EventContext(
            intent_id=uuid4(),
            intent_text="Sync test task",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        memory_unit = service.process_event_sync(event)
        assert memory_unit.id is not None
        assert "Sync test task" in memory_unit.title

    @pytest.mark.asyncio
    async def test_process_events_batch(self, service):
        """Test batch processing of multiple events"""
        events = [
            EventContext(
                intent_id=uuid4(),
                intent_text=f"Task {i}",
                intent_type="feature_request",
                timestamp=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]
        results = await service.process_events_batch(events)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_metadata_includes_inference_info(self, service, basic_event):
        """Test that metadata includes inference information"""
        memory_unit = await service.process_event(basic_event)
        assert "inference_confidence" in memory_unit.metadata
        assert "inference_reasoning" in memory_unit.metadata
        assert "project_confidence" in memory_unit.metadata

    def test_get_extractor(self, service):
        """Test getting the extractor instance"""
        extractor = service.get_extractor()
        assert extractor is not None

    def test_get_inferencer(self, service):
        """Test getting the inferencer instance"""
        inferencer = service.get_inferencer()
        assert inferencer is not None

    def test_get_constructor(self, service):
        """Test getting the constructor instance"""
        constructor = service.get_constructor()
        assert constructor is not None

    @pytest.mark.asyncio
    async def test_tags_are_generated(self, service, basic_event):
        """Test that tags are automatically generated"""
        memory_unit = await service.process_event(basic_event)
        assert len(memory_unit.tags) > 0
        # Should include at least the type tag
        assert memory_unit.type.value in memory_unit.tags

    @pytest.mark.asyncio
    async def test_emotion_state_is_set(self, service, basic_event):
        """Test that emotion state is properly inferred"""
        memory_unit = await service.process_event(basic_event)
        assert memory_unit.emotion_state is not None
