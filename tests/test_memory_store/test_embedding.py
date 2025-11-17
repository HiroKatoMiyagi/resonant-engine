"""
Unit tests for Embedding Service
"""

import pytest
from memory_store.embedding import (
    MockEmbeddingService,
    EmbeddingError,
    cosine_similarity,
)


class TestMockEmbeddingService:
    """Tests for MockEmbeddingService"""

    @pytest.fixture
    def embedding_service(self):
        """Create a MockEmbeddingService instance"""
        return MockEmbeddingService(dimensions=1536, cache_enabled=True)

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_service):
        """Test successful embedding generation"""
        text = "Resonant Engineは呼吸のリズムで動作する"
        embedding = await embedding_service.generate_embedding(text)

        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)

    @pytest.mark.asyncio
    async def test_generate_embedding_deterministic(self, embedding_service):
        """Test that same text produces same embedding"""
        text = "テストテキスト"
        embedding1 = await embedding_service.generate_embedding(text)
        embedding_service.clear_cache()
        embedding2 = await embedding_service.generate_embedding(text)

        assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_generate_embedding_cache(self, embedding_service):
        """Test cache mechanism"""
        text = "キャッシュテスト"

        # First call
        await embedding_service.generate_embedding(text)
        call_count1 = embedding_service.get_call_count()

        # Second call (should use cache)
        await embedding_service.generate_embedding(text)
        call_count2 = embedding_service.get_call_count()

        # Call count should not increase
        assert call_count2 == call_count1

    @pytest.mark.asyncio
    async def test_generate_embedding_different_texts(self, embedding_service):
        """Test that different texts produce different embeddings"""
        text1 = "呼吸のリズム"
        text2 = "データベース設計"

        embedding1 = await embedding_service.generate_embedding(text1)
        embedding2 = await embedding_service.generate_embedding(text2)

        # Embeddings should be different
        assert embedding1 != embedding2

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text_error(self, embedding_service):
        """Test error on empty text"""
        with pytest.raises(EmbeddingError, match="Text cannot be empty"):
            await embedding_service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_semantic_similarity(self, embedding_service):
        """Test that semantically similar texts have higher similarity"""
        text1 = "呼吸のリズムで動作する"
        text2 = "breathing rhythm operation"
        text3 = "データベース設計パターン"

        emb1 = await embedding_service.generate_embedding(text1)
        emb2 = await embedding_service.generate_embedding(text2)
        emb3 = await embedding_service.generate_embedding(text3)

        # Similar topics should have higher similarity
        sim_1_2 = cosine_similarity(emb1, emb2)
        sim_1_3 = cosine_similarity(emb1, emb3)

        # Breathing-related texts should be more similar
        assert sim_1_2 > sim_1_3

    def test_get_dimensions(self, embedding_service):
        """Test getting dimensions"""
        assert embedding_service.get_dimensions() == 1536

    def test_cache_size(self, embedding_service):
        """Test cache size tracking"""
        assert embedding_service.get_cache_size() == 0


class TestCosineSimilarity:
    """Tests for cosine_similarity function"""

    def test_identical_vectors(self):
        """Test similarity of identical vectors"""
        vec = [1.0, 2.0, 3.0]
        similarity = cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.0001

    def test_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.0001

    def test_opposite_vectors(self):
        """Test similarity of opposite vectors"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        similarity = cosine_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 0.0001

    def test_different_length_error(self):
        """Test error on different length vectors"""
        vec1 = [1.0, 2.0]
        vec2 = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="same length"):
            cosine_similarity(vec1, vec2)
