"""
Memory Store Service - Main Orchestration Layer

Coordinates memory storage, embedding generation, and similarity search.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .embedding import EmbeddingService
from .models import MemoryCreate, MemoryResult, MemoryType, SourceType
from .repository import MemoryRepository


class MemoryStoreService:
    """
    記憶の保存・検索サービス

    Working Memory と Long-term Memory の管理、
    ベクトル類似度検索、ハイブリッド検索を提供
    """

    def __init__(
        self,
        repository: MemoryRepository,
        embedding_service: EmbeddingService,
        working_memory_ttl_hours: int = 24,
        default_similarity_threshold: float = 0.7,
    ) -> None:
        """
        Initialize Memory Store Service.

        Args:
            repository: Database access layer
            embedding_service: Embedding generation service
            working_memory_ttl_hours: TTL for working memories (default 24h)
            default_similarity_threshold: Default threshold for similarity search
        """
        self.repository = repository
        self.embedding_service = embedding_service
        self.working_memory_ttl_hours = working_memory_ttl_hours
        self.default_similarity_threshold = default_similarity_threshold

    async def save_memory(
        self,
        content: str,
        memory_type: MemoryType,
        source_type: Optional[SourceType] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """
        記憶を保存

        Args:
            content: 記憶内容
            memory_type: 'working' or 'longterm'
            source_type: 'intent', 'thought', 'correction', 'decision'
            metadata: メタデータ（JSONB）
            expires_at: 有効期限（Working Memory用、未指定時は24時間後）
            user_id: ユーザーID

        Returns:
            memory_id: 保存された記憶のID
        """
        start_time = time.time()

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(content)

        # Set expiration for working memory
        if memory_type == MemoryType.WORKING and expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=self.working_memory_ttl_hours
            )

        # Extract user_id from metadata if not provided directly
        if user_id is None and metadata:
            user_id = metadata.get("user_id")

        # Save to repository
        memory_id = await self.repository.insert_memory(
            content=content,
            embedding=embedding,
            memory_type=memory_type.value,
            source_type=source_type.value if source_type else None,
            metadata=metadata or {},
            expires_at=expires_at,
            user_id=user_id,
        )

        # Log the save operation
        processing_time_ms = (time.time() - start_time) * 1000
        self._log_save(memory_id, memory_type, source_type, processing_time_ms)

        return memory_id

    async def search_similar(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        similarity_threshold: Optional[float] = None,
        include_archived: bool = False,
    ) -> List[MemoryResult]:
        """
        類似記憶検索（ベクトル検索）

        Args:
            query: 検索クエリ
            memory_type: フィルタ（working/longterm）
            limit: 最大返却数
            similarity_threshold: 類似度閾値（0.0-1.0）
            include_archived: アーカイブ済みも含むか

        Returns:
            List[MemoryResult]: 類似度順の記憶リスト
        """
        start_time = time.time()

        if similarity_threshold is None:
            similarity_threshold = self.default_similarity_threshold

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Search in repository
        rows = await self.repository.search_similar(
            query_embedding=query_embedding,
            memory_type=memory_type.value if memory_type else None,
            limit=limit,
            similarity_threshold=similarity_threshold,
            include_archived=include_archived,
        )

        # Convert to MemoryResult
        results = [self._row_to_memory_result(row) for row in rows]

        # Log search operation
        processing_time_ms = (time.time() - start_time) * 1000
        self._log_search("similar", query, len(results), processing_time_ms)

        return results

    async def search_hybrid(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int = 10,
    ) -> List[MemoryResult]:
        """
        ハイブリッド検索（ベクトル + メタデータフィルタ）

        Args:
            query: 検索クエリ
            filters: メタデータフィルタ条件
                例: {"tags": ["important"], "source_type": "decision"}
            limit: 最大返却数

        Returns:
            List[MemoryResult]: フィルタ適用後の類似記憶リスト
        """
        start_time = time.time()

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Search with filters
        rows = await self.repository.search_hybrid(
            query_embedding=query_embedding,
            filters=filters,
            limit=limit,
        )

        # Convert to MemoryResult
        results = [self._row_to_memory_result(row) for row in rows]

        # Log search operation
        processing_time_ms = (time.time() - start_time) * 1000
        self._log_search("hybrid", query, len(results), processing_time_ms)

        return results

    async def get_memory(self, memory_id: int) -> Optional[MemoryResult]:
        """
        IDで記憶を取得

        Args:
            memory_id: 記憶ID

        Returns:
            MemoryResult or None
        """
        record = await self.repository.get_by_id(memory_id)
        if record is None:
            return None

        return MemoryResult(
            id=record.id,
            content=record.content,
            memory_type=record.memory_type,
            source_type=record.source_type,
            metadata=record.metadata,
            similarity=1.0,  # Exact match
            created_at=record.created_at,
        )

    async def cleanup_expired_working_memory(self) -> int:
        """
        有効期限切れのWorking Memoryをアーカイブ

        Returns:
            アーカイブされた記憶の数
        """
        count = await self.repository.archive_expired()
        print(f"Archived {count} expired working memories")
        return count

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        メモリ統計情報を取得

        Returns:
            統計情報の辞書
        """
        working_count = await self.repository.count_by_type(MemoryType.WORKING.value)
        longterm_count = await self.repository.count_by_type(MemoryType.LONGTERM.value)

        return {
            "working_memory_count": working_count,
            "longterm_memory_count": longterm_count,
            "total_count": working_count + longterm_count,
            "embedding_dimensions": self.embedding_service.get_dimensions(),
            "working_memory_ttl_hours": self.working_memory_ttl_hours,
        }

    def _row_to_memory_result(self, row: Dict[str, Any]) -> MemoryResult:
        """Convert database row to MemoryResult"""
        source_type = None
        if row.get("source_type"):
            source_type = SourceType(row["source_type"])

        # Clamp similarity to [0.0, 1.0] range (negative values can occur with mock embeddings)
        similarity = max(0.0, min(1.0, row["similarity"]))

        return MemoryResult(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            source_type=source_type,
            metadata=row.get("metadata", {}),
            similarity=similarity,
            created_at=row["created_at"],
        )

    def _log_save(
        self,
        memory_id: int,
        memory_type: MemoryType,
        source_type: Optional[SourceType],
        processing_time_ms: float,
    ) -> None:
        """Log memory save operation"""
        print(
            f"""
        Memory Store Save:
          Memory ID: {memory_id}
          Type: {memory_type.value}
          Source: {source_type.value if source_type else 'None'}
          Processing Time: {processing_time_ms:.2f}ms
        """
        )

    def _log_search(
        self,
        search_type: str,
        query: str,
        result_count: int,
        processing_time_ms: float,
    ) -> None:
        """Log memory search operation"""
        query_preview = query[:50] + "..." if len(query) > 50 else query
        print(
            f"""
        Memory Store Search ({search_type}):
          Query: {query_preview}
          Results: {result_count}
          Processing Time: {processing_time_ms:.2f}ms
        """
        )
