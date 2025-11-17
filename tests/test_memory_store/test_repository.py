"""
Unit tests for Memory Repository
"""

import pytest
from datetime import datetime, timedelta, timezone

from memory_store.repository import InMemoryRepository
from memory_store.embedding import MockEmbeddingService


class TestInMemoryRepository:
    """Tests for InMemoryRepository"""

    @pytest.fixture
    def repo(self):
        """Create an InMemoryRepository instance"""
        return InMemoryRepository()

    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding"""
        return [0.1] * 1536

    @pytest.mark.asyncio
    async def test_insert_memory(self, repo, sample_embedding):
        """Test inserting a memory"""
        memory_id = await repo.insert_memory(
            content="Test content",
            embedding=sample_embedding,
            memory_type="working",
            source_type="intent",
            metadata={"key": "value"},
            expires_at=None,
        )

        assert memory_id == 1

    @pytest.mark.asyncio
    async def test_insert_multiple_memories(self, repo, sample_embedding):
        """Test inserting multiple memories"""
        id1 = await repo.insert_memory(
            "Memory 1", sample_embedding, "working", None, {}, None
        )
        id2 = await repo.insert_memory(
            "Memory 2", sample_embedding, "longterm", None, {}, None
        )

        assert id1 == 1
        assert id2 == 2

    @pytest.mark.asyncio
    async def test_get_by_id(self, repo, sample_embedding):
        """Test getting memory by ID"""
        memory_id = await repo.insert_memory(
            "Test", sample_embedding, "longterm", "decision", {"tag": "test"}, None
        )

        record = await repo.get_by_id(memory_id)
        assert record is not None
        assert record.content == "Test"
        assert record.metadata["tag"] == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        """Test getting non-existent memory"""
        record = await repo.get_by_id(999)
        assert record is None

    @pytest.mark.asyncio
    async def test_search_similar_basic(self, repo):
        """Test basic similarity search"""
        emb_service = MockEmbeddingService()

        # Insert memories with different embeddings
        emb1 = await emb_service.generate_embedding("呼吸のリズム")
        emb2 = await emb_service.generate_embedding("データベース設計")

        await repo.insert_memory("呼吸のリズム", emb1, "longterm", None, {}, None)
        await repo.insert_memory("データベース設計", emb2, "longterm", None, {}, None)

        # Search (use negative threshold to include all results)
        query_emb = await emb_service.generate_embedding("呼吸について")
        results = await repo.search_similar(query_emb, None, 10, -1.0, False)

        assert len(results) == 2
        # Results should be sorted by similarity
        assert results[0]["similarity"] >= results[1]["similarity"]

    @pytest.mark.asyncio
    async def test_search_similar_with_type_filter(self, repo, sample_embedding):
        """Test similarity search with type filter"""
        await repo.insert_memory("Working", sample_embedding, "working", None, {}, None)
        await repo.insert_memory("Longterm", sample_embedding, "longterm", None, {}, None)

        results = await repo.search_similar(
            sample_embedding, "longterm", 10, 0.0, False
        )

        assert len(results) == 1
        assert results[0]["memory_type"] == "longterm"

    @pytest.mark.asyncio
    async def test_search_excludes_expired(self, repo, sample_embedding):
        """Test that expired memories are excluded"""
        # Insert expired memory
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await repo.insert_memory("Expired", sample_embedding, "working", None, {}, past)

        # Insert non-expired memory
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        await repo.insert_memory("Valid", sample_embedding, "working", None, {}, future)

        results = await repo.search_similar(sample_embedding, None, 10, 0.0, False)

        assert len(results) == 1
        assert results[0]["content"] == "Valid"

    @pytest.mark.asyncio
    async def test_search_excludes_archived(self, repo, sample_embedding):
        """Test that archived memories are excluded by default"""
        id1 = await repo.insert_memory(
            "Active", sample_embedding, "longterm", None, {}, None
        )
        id2 = await repo.insert_memory(
            "To Archive", sample_embedding, "longterm", None, {}, None
        )

        # Archive one
        record = await repo.get_by_id(id2)
        record.is_archived = True

        results = await repo.search_similar(sample_embedding, None, 10, 0.0, False)
        assert len(results) == 1

        # Include archived
        results_with_archived = await repo.search_similar(
            sample_embedding, None, 10, 0.0, True
        )
        assert len(results_with_archived) == 2

    @pytest.mark.asyncio
    async def test_archive_expired(self, repo, sample_embedding):
        """Test archiving expired working memories"""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        await repo.insert_memory("Expired", sample_embedding, "working", None, {}, past)
        await repo.insert_memory("Valid", sample_embedding, "working", None, {}, future)
        await repo.insert_memory("Longterm", sample_embedding, "longterm", None, {}, None)

        count = await repo.archive_expired()
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_by_type(self, repo, sample_embedding):
        """Test counting memories by type"""
        await repo.insert_memory("W1", sample_embedding, "working", None, {}, None)
        await repo.insert_memory("W2", sample_embedding, "working", None, {}, None)
        await repo.insert_memory("L1", sample_embedding, "longterm", None, {}, None)

        working_count = await repo.count_by_type("working")
        longterm_count = await repo.count_by_type("longterm")

        assert working_count == 2
        assert longterm_count == 1

    @pytest.mark.asyncio
    async def test_search_hybrid_with_filters(self, repo, sample_embedding):
        """Test hybrid search with metadata filters"""
        await repo.insert_memory(
            "Important decision",
            sample_embedding,
            "longterm",
            "decision",
            {"tags": ["important"], "importance": 0.9},
            None,
        )
        await repo.insert_memory(
            "Random thought",
            sample_embedding,
            "longterm",
            "thought",
            {"tags": ["minor"]},
            None,
        )

        # Filter by source_type
        results = await repo.search_hybrid(
            sample_embedding, {"source_type": "decision"}, 10
        )
        assert len(results) == 1

        # Filter by tags
        results = await repo.search_hybrid(
            sample_embedding, {"tags": ["important"]}, 10
        )
        assert len(results) == 1
