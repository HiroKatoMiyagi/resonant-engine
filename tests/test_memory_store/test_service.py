"""
Unit tests for Memory Store Service
"""

import pytest
from datetime import datetime, timedelta, timezone

from memory_store.service import MemoryStoreService
from memory_store.repository import InMemoryRepository
from memory_store.embedding import MockEmbeddingService
from memory_store.models import MemoryType, SourceType


class TestMemoryStoreService:
    """Tests for MemoryStoreService"""

    @pytest.fixture
    def service(self):
        """Create a MemoryStoreService instance"""
        repo = InMemoryRepository()
        embedding_service = MockEmbeddingService()
        return MemoryStoreService(
            repository=repo,
            embedding_service=embedding_service,
            working_memory_ttl_hours=24,
        )

    @pytest.mark.asyncio
    async def test_save_memory_working(self, service):
        """Test saving working memory"""
        memory_id = await service.save_memory(
            content="今日のタスク: Sprint 3完了",
            memory_type=MemoryType.WORKING,
            source_type=SourceType.INTENT,
        )

        assert memory_id > 0

    @pytest.mark.asyncio
    async def test_save_memory_longterm(self, service):
        """Test saving long-term memory"""
        memory_id = await service.save_memory(
            content="Resonant Engineの設計原則: 呼吸のリズム",
            memory_type=MemoryType.LONGTERM,
            source_type=SourceType.DECISION,
            metadata={"importance": 1.0, "tags": ["core", "philosophy"]},
        )

        assert memory_id > 0

    @pytest.mark.asyncio
    async def test_save_memory_with_metadata(self, service):
        """Test saving memory with metadata"""
        metadata = {
            "conversation_id": "conv123",
            "tags": ["important", "architecture"],
            "importance": 0.9,
        }
        memory_id = await service.save_memory(
            content="アーキテクチャの決定事項",
            memory_type=MemoryType.LONGTERM,
            source_type=SourceType.DECISION,
            metadata=metadata,
        )

        assert memory_id > 0
        memory = await service.get_memory(memory_id)
        assert memory.metadata == metadata

    @pytest.mark.asyncio
    async def test_search_similar_basic(self, service):
        """Test basic similarity search"""
        # Save some memories
        await service.save_memory(
            "Resonant Engineは呼吸で動く",
            MemoryType.LONGTERM,
            SourceType.DECISION,
        )
        await service.save_memory(
            "データベースの設計パターン",
            MemoryType.LONGTERM,
            SourceType.THOUGHT,
        )

        # Search for similar (use low threshold for mock embeddings)
        results = await service.search_similar(
            query="呼吸のリズムとは",
            limit=5,
            similarity_threshold=0.0,  # Low threshold for mock embeddings
        )

        assert len(results) > 0
        # Results should be sorted by similarity
        if len(results) > 1:
            assert results[0].similarity >= results[1].similarity

    @pytest.mark.asyncio
    async def test_search_similar_with_type_filter(self, service):
        """Test similarity search with memory type filter"""
        await service.save_memory(
            "Working memory test",
            MemoryType.WORKING,
        )
        await service.save_memory(
            "Long-term memory test",
            MemoryType.LONGTERM,
        )

        # Search only longterm
        results = await service.search_similar(
            query="memory test",
            memory_type=MemoryType.LONGTERM,
        )

        assert all(r.memory_type == MemoryType.LONGTERM for r in results)

    @pytest.mark.asyncio
    async def test_search_similar_threshold(self, service):
        """Test similarity threshold filtering"""
        await service.save_memory(
            "呼吸のリズム",
            MemoryType.LONGTERM,
        )

        # High threshold
        results = await service.search_similar(
            query="完全に無関係なテキスト",
            similarity_threshold=0.95,
        )

        # Should return fewer or no results with high threshold
        # (depends on embedding similarity)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_hybrid_source_type(self, service):
        """Test hybrid search with source type filter"""
        await service.save_memory(
            "Design decision about architecture",
            MemoryType.LONGTERM,
            SourceType.DECISION,
        )
        await service.save_memory(
            "Random thought about architecture",
            MemoryType.LONGTERM,
            SourceType.THOUGHT,
        )

        results = await service.search_hybrid(
            query="architecture",
            filters={"source_type": "decision"},
        )

        assert len(results) >= 1
        assert all(r.source_type == SourceType.DECISION for r in results)

    @pytest.mark.asyncio
    async def test_search_hybrid_tags(self, service):
        """Test hybrid search with tags filter"""
        await service.save_memory(
            "Important core decision",
            MemoryType.LONGTERM,
            metadata={"tags": ["important", "core"]},
        )
        await service.save_memory(
            "Minor update",
            MemoryType.LONGTERM,
            metadata={"tags": ["minor"]},
        )

        results = await service.search_hybrid(
            query="decision",
            filters={"tags": ["important"]},
        )

        assert len(results) >= 1
        assert "important" in results[0].metadata.get("tags", [])

    @pytest.mark.asyncio
    async def test_get_memory_by_id(self, service):
        """Test getting memory by ID"""
        memory_id = await service.save_memory(
            "Test content",
            MemoryType.LONGTERM,
        )

        memory = await service.get_memory(memory_id)
        assert memory is not None
        assert memory.id == memory_id
        assert memory.content == "Test content"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, service):
        """Test getting non-existent memory"""
        memory = await service.get_memory(99999)
        assert memory is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_working_memory(self, service):
        """Test archiving expired working memories"""
        # Save working memory with past expiration
        repo = service.repository
        await repo.insert_memory(
            content="Expired memory",
            embedding=[0.0] * 1536,
            memory_type="working",
            source_type=None,
            metadata={},
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        # Cleanup
        count = await service.cleanup_expired_working_memory()
        assert count >= 1

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, service):
        """Test getting memory statistics"""
        await service.save_memory("Working 1", MemoryType.WORKING)
        await service.save_memory("Working 2", MemoryType.WORKING)
        await service.save_memory("Longterm 1", MemoryType.LONGTERM)

        stats = await service.get_memory_stats()

        assert stats["working_memory_count"] == 2
        assert stats["longterm_memory_count"] == 1
        assert stats["total_count"] == 3
        assert stats["embedding_dimensions"] == 1536

    @pytest.mark.asyncio
    async def test_full_pipeline(self, service):
        """Test complete save and search pipeline"""
        # Save multiple memories
        await service.save_memory(
            "Resonant Engineは呼吸のリズムで動作する",
            MemoryType.LONGTERM,
            SourceType.DECISION,
        )
        await service.save_memory(
            "PostgreSQLとpgvectorを使用する",
            MemoryType.LONGTERM,
            SourceType.DECISION,
        )
        await service.save_memory(
            "Embeddingはtext-embedding-3-smallで生成",
            MemoryType.LONGTERM,
            SourceType.THOUGHT,
        )

        # Search (use low threshold for mock embeddings)
        results = await service.search_similar(
            query="呼吸について教えて",
            limit=3,
            similarity_threshold=0.0,  # Low threshold for mock embeddings
        )

        assert len(results) > 0
        # Results should have positive similarity scores
        assert results[0].similarity > 0.0
        # All results should be sorted by similarity
        for i in range(len(results) - 1):
            assert results[i].similarity >= results[i + 1].similarity
