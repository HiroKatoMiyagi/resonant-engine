"""
Memory Repository - Database Access Layer

Provides abstract interface and in-memory implementation for testing.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .embedding import cosine_similarity
from .models import MemoryRecord, MemoryResult, MemoryType, SourceType


class MemoryRepository(ABC):
    """Abstract base class for memory repository"""

    @abstractmethod
    async def insert_memory(
        self,
        content: str,
        embedding: List[float],
        memory_type: str,
        source_type: Optional[str],
        metadata: Dict[str, Any],
        expires_at: Optional[datetime],
    ) -> int:
        """Insert a new memory record"""
        pass

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: List[float],
        memory_type: Optional[str],
        limit: int,
        similarity_threshold: float,
        include_archived: bool,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using vector similarity"""
        pass

    @abstractmethod
    async def search_hybrid(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search with vector similarity and metadata filters"""
        pass

    @abstractmethod
    async def get_by_id(self, memory_id: int) -> Optional[MemoryRecord]:
        """Get memory by ID"""
        pass

    @abstractmethod
    async def archive_expired(self) -> int:
        """Archive expired working memories"""
        pass

    @abstractmethod
    async def count_by_type(self, memory_type: str) -> int:
        """Count memories by type"""
        pass


class InMemoryRepository(MemoryRepository):
    """In-memory implementation for testing"""

    def __init__(self) -> None:
        """Initialize empty storage"""
        self._storage: Dict[int, MemoryRecord] = {}
        self._next_id = 1

    async def insert_memory(
        self,
        content: str,
        embedding: List[float],
        memory_type: str,
        source_type: Optional[str],
        metadata: Dict[str, Any],
        expires_at: Optional[datetime],
    ) -> int:
        """Insert a new memory record"""
        memory_id = self._next_id
        self._next_id += 1

        now = datetime.now(timezone.utc)
        record = MemoryRecord(
            id=memory_id,
            content=content,
            embedding=embedding,
            memory_type=MemoryType(memory_type),
            source_type=SourceType(source_type) if source_type else None,
            metadata=metadata,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            is_archived=False,
        )

        self._storage[memory_id] = record
        return memory_id

    async def search_similar(
        self,
        query_embedding: List[float],
        memory_type: Optional[str],
        limit: int,
        similarity_threshold: float,
        include_archived: bool,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using vector similarity"""
        results = []
        now = datetime.now(timezone.utc)

        for record in self._storage.values():
            # Filter by memory type
            if memory_type and record.memory_type.value != memory_type:
                continue

            # Filter expired
            if record.expires_at and record.expires_at <= now:
                continue

            # Filter archived
            if not include_archived and record.is_archived:
                continue

            # Calculate similarity
            similarity = cosine_similarity(query_embedding, record.embedding)

            # Filter by threshold
            if similarity < similarity_threshold:
                continue

            results.append({
                "id": record.id,
                "content": record.content,
                "memory_type": record.memory_type.value,
                "source_type": record.source_type.value if record.source_type else None,
                "metadata": record.metadata,
                "created_at": record.created_at,
                "similarity": similarity,
            })

        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)

        # Return top N
        return results[:limit]

    async def search_hybrid(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search with vector similarity and metadata filters"""
        results = []
        now = datetime.now(timezone.utc)

        for record in self._storage.values():
            # Filter expired
            if record.expires_at and record.expires_at <= now:
                continue

            # Filter archived
            if record.is_archived:
                continue

            # Apply filters
            if not self._matches_filters(record, filters):
                continue

            # Calculate similarity
            similarity = cosine_similarity(query_embedding, record.embedding)

            results.append({
                "id": record.id,
                "content": record.content,
                "memory_type": record.memory_type.value,
                "source_type": record.source_type.value if record.source_type else None,
                "metadata": record.metadata,
                "created_at": record.created_at,
                "similarity": similarity,
            })

        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)

        # Return top N
        return results[:limit]

    def _matches_filters(self, record: MemoryRecord, filters: Dict[str, Any]) -> bool:
        """Check if record matches all filters"""
        # Source type filter
        if "source_type" in filters:
            if record.source_type is None:
                return False
            if record.source_type.value != filters["source_type"]:
                return False

        # Memory type filter
        if "memory_type" in filters:
            if record.memory_type.value != filters["memory_type"]:
                return False

        # Tags filter (metadata.tags)
        if "tags" in filters:
            record_tags = record.metadata.get("tags", [])
            if not any(tag in record_tags for tag in filters["tags"]):
                return False

        # Importance filter
        if "importance_min" in filters:
            importance = record.metadata.get("importance", 0.0)
            if importance < filters["importance_min"]:
                return False

        if "importance_max" in filters:
            importance = record.metadata.get("importance", 0.0)
            if importance > filters["importance_max"]:
                return False

        # Date filters
        if "created_after" in filters:
            if record.created_at < filters["created_after"]:
                return False

        if "created_before" in filters:
            if record.created_at > filters["created_before"]:
                return False

        return True

    async def get_by_id(self, memory_id: int) -> Optional[MemoryRecord]:
        """Get memory by ID"""
        return self._storage.get(memory_id)

    async def archive_expired(self) -> int:
        """Archive expired working memories"""
        count = 0
        now = datetime.now(timezone.utc)

        for record in self._storage.values():
            if (
                record.memory_type == MemoryType.WORKING
                and record.expires_at
                and record.expires_at <= now
                and not record.is_archived
            ):
                record.is_archived = True
                record.updated_at = now
                count += 1

        return count

    async def count_by_type(self, memory_type: str) -> int:
        """Count memories by type"""
        count = 0
        for record in self._storage.values():
            if record.memory_type.value == memory_type and not record.is_archived:
                count += 1
        return count

    def clear(self) -> None:
        """Clear all stored memories"""
        self._storage.clear()
        self._next_id = 1

    def get_all(self) -> List[MemoryRecord]:
        """Get all stored memories"""
        return list(self._storage.values())
