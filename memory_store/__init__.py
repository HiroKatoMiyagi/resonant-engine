"""
Memory Store System - pgvector-based Semantic Memory Storage

Provides vector-based memory storage and semantic similarity search
for the Resonant Engine memory system.
"""

from .models import (
    MemoryType,
    SourceType,
    MemoryCreate,
    MemoryRecord,
    MemoryResult,
    MemorySearchQuery,
)
from .embedding import EmbeddingService, MockEmbeddingService, EmbeddingError
from .repository import MemoryRepository, InMemoryRepository
from .service import MemoryStoreService

__all__ = [
    # Models
    "MemoryType",
    "SourceType",
    "MemoryCreate",
    "MemoryRecord",
    "MemoryResult",
    "MemorySearchQuery",
    # Services
    "EmbeddingService",
    "MockEmbeddingService",
    "EmbeddingError",
    # Repository
    "MemoryRepository",
    "InMemoryRepository",
    # Main Service
    "MemoryStoreService",
]
