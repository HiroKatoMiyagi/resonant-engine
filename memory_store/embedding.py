"""
Embedding Service - Text to Vector Conversion

Provides embedding generation with caching and retry logic.
Includes mock implementation for testing without OpenAI API.
"""

import asyncio
import hashlib
import math
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class EmbeddingError(Exception):
    """Embedding関連のエラー"""
    pass


class EmbeddingService(ABC):
    """Abstract base class for embedding services"""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get the number of dimensions in the embedding"""
        pass


class MockEmbeddingService(EmbeddingService):
    """
    Mock Embedding Service for testing without OpenAI API.

    Generates deterministic pseudo-embeddings based on text content.
    Uses hashing to ensure same text always produces same embedding.
    """

    def __init__(
        self,
        dimensions: int = 1536,
        cache_enabled: bool = True,
        simulate_latency: bool = False,
        latency_ms: int = 50,
    ):
        """
        Initialize mock embedding service.

        Args:
            dimensions: Number of dimensions for embeddings
            cache_enabled: Whether to cache embeddings
            simulate_latency: Whether to simulate API latency
            latency_ms: Simulated latency in milliseconds
        """
        self.dimensions = dimensions
        self.cache_enabled = cache_enabled
        self.simulate_latency = simulate_latency
        self.latency_ms = latency_ms
        self._cache: Dict[str, List[float]] = {}
        self._call_count = 0

    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.md5(text.encode()).hexdigest()

    def _text_to_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic embedding from text.

        Uses character frequencies and text features to create
        a reproducible embedding vector.
        """
        # Create a seed from the text hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)

        # Use seeded random for reproducibility
        rng = random.Random(seed)

        # Generate base embedding
        embedding = [rng.gauss(0, 1) for _ in range(self.dimensions)]

        # Normalize to unit vector
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        # Add semantic features based on text
        self._add_semantic_features(text, embedding)

        # Re-normalize after adding features
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def _add_semantic_features(self, text: str, embedding: List[float]) -> None:
        """
        Add semantic features to embedding based on text content.

        This creates meaningful relationships between similar texts.
        """
        text_lower = text.lower()

        # Feature mapping: keywords -> embedding indices to adjust
        feature_map = {
            "呼吸": [0, 1, 2],
            "breathing": [0, 1, 2],
            "resonant": [3, 4, 5],
            "engine": [6, 7, 8],
            "memory": [9, 10, 11],
            "メモリ": [9, 10, 11],
            "記憶": [12, 13, 14],
            "vector": [15, 16, 17],
            "embedding": [18, 19, 20],
            "postgresql": [21, 22, 23],
            "database": [24, 25, 26],
            "intent": [27, 28, 29],
            "decision": [30, 31, 32],
            "working": [33, 34, 35],
            "longterm": [36, 37, 38],
            "design": [39, 40, 41],
            "設計": [39, 40, 41],
            "test": [42, 43, 44],
            "テスト": [42, 43, 44],
        }

        # Apply feature adjustments
        for keyword, indices in feature_map.items():
            if keyword in text_lower:
                for idx in indices:
                    if idx < len(embedding):
                        embedding[idx] += 0.5

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not text:
            raise EmbeddingError("Text cannot be empty")

        # Simulate latency if enabled
        if self.simulate_latency:
            await asyncio.sleep(self.latency_ms / 1000)

        # Check cache
        if self.cache_enabled:
            cache_key = self._generate_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Generate embedding
        self._call_count += 1
        embedding = self._text_to_embedding(text)

        # Store in cache
        if self.cache_enabled:
            self._cache[cache_key] = embedding

        return embedding

    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.dimensions

    def get_call_count(self) -> int:
        """Get number of API calls (for testing)"""
        return self._call_count

    def clear_cache(self) -> None:
        """Clear the embedding cache"""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


class OpenAIEmbeddingService(EmbeddingService):
    """
    OpenAI Embedding Service for production use.

    Requires openai package and valid API key.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        cache_enabled: bool = True,
        retry_count: int = 3,
    ):
        """
        Initialize OpenAI embedding service.

        Args:
            api_key: OpenAI API key
            model: Model name
            cache_enabled: Whether to cache embeddings
            retry_count: Number of retries on failure
        """
        self.api_key = api_key
        self.model = model
        self.cache_enabled = cache_enabled
        self.retry_count = retry_count
        self._cache: Dict[str, List[float]] = {}
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create OpenAI client"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise EmbeddingError("openai package not installed")
        return self._client

    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key"""
        return hashlib.md5(f"{self.model}:{text}".encode()).hexdigest()

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API.

        Args:
            text: Text to embed

        Returns:
            List[float]: 1536-dimensional embedding vector

        Raises:
            EmbeddingError: If embedding generation fails after retries
        """
        if not text:
            raise EmbeddingError("Text cannot be empty")

        # Check cache
        if self.cache_enabled:
            cache_key = self._generate_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Retry logic
        last_error = None
        client = self._get_client()

        for attempt in range(self.retry_count):
            try:
                response = await client.embeddings.create(
                    model=self.model,
                    input=text
                )
                embedding = response.data[0].embedding

                # Cache the result
                if self.cache_enabled:
                    self._cache[cache_key] = embedding

                return embedding

            except Exception as e:
                last_error = e
                if attempt < self.retry_count - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                continue

        raise EmbeddingError(f"Embedding generation failed: {last_error}")

    def get_dimensions(self) -> int:
        """Get embedding dimensions (1536 for text-embedding-3-small)"""
        return 1536

    def clear_cache(self) -> None:
        """Clear the embedding cache"""
        self._cache.clear()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity (0.0 to 1.0)
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same length")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)
