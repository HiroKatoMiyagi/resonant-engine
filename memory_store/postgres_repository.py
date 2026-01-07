"""
PostgreSQL Memory Repository - Database Access Layer for pgvector

Implements memory storage with PostgreSQL and pgvector extension.
"""

import asyncpg
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import MemoryRecord, MemoryType, SourceType
from .repository import MemoryRepository


class PostgresMemoryRepository(MemoryRepository):
    """PostgreSQL implementation with pgvector support"""

    def __init__(self, pool: asyncpg.Pool) -> None:
        """
        Initialize with connection pool.
        
        Args:
            pool: asyncpg connection pool
        """
        self._pool = pool

    async def insert_memory(
        self,
        content: str,
        embedding: List[float],
        memory_type: str,
        source_type: Optional[str],
        metadata: Dict[str, Any],
        expires_at: Optional[datetime],
        user_id: Optional[str] = None,
    ) -> int:
        """Insert a new memory record"""
        import json
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memories (content, embedding, memory_type, source_type, metadata, expires_at, user_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                content,
                str(embedding),  # pgvector accepts string representation
                memory_type,
                source_type,
                json.dumps(metadata),
                expires_at,
                user_id,
            )
            return row["id"]

    async def search_similar(
        self,
        query_embedding: List[float],
        memory_type: Optional[str],
        limit: int,
        similarity_threshold: float,
        include_archived: bool,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using pgvector cosine similarity"""
        import json
        
        # Build query with optional filters
        conditions = ["archived = false OR $5 = true"]
        params = [str(query_embedding), limit, similarity_threshold, memory_type, include_archived]
        
        if memory_type:
            conditions.append("memory_type = $4")
        
        if user_id:
            conditions.append(f"user_id = ${len(params) + 1}")
            params.append(user_id)
        
        where_clause = " AND ".join(conditions)
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT 
                    id, content, memory_type, source_type, metadata, created_at,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM memories
                WHERE {where_clause}
                    AND 1 - (embedding <=> $1::vector) >= $3
                ORDER BY similarity DESC
                LIMIT $2
                """,
                *params
            )
            
            results = []
            for row in rows:
                metadata = row["metadata"]
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                results.append({
                    "id": row["id"],
                    "content": row["content"],
                    "memory_type": row["memory_type"],
                    "source_type": row["source_type"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                    "similarity": float(row["similarity"]),
                })
            return results

    async def search_hybrid(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search with vector similarity and metadata filters"""
        import json
        
        conditions = ["archived = false"]
        params = [str(query_embedding), limit]
        param_idx = 3
        
        if filters.get("source_type"):
            conditions.append(f"source_type = ${param_idx}")
            params.append(filters["source_type"])
            param_idx += 1
        
        if filters.get("memory_type"):
            conditions.append(f"memory_type = ${param_idx}")
            params.append(filters["memory_type"])
            param_idx += 1
            
        if filters.get("user_id"):
            conditions.append(f"user_id = ${param_idx}")
            params.append(filters["user_id"])
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT 
                    id, content, memory_type, source_type, metadata, created_at,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM memories
                WHERE {where_clause}
                ORDER BY similarity DESC
                LIMIT $2
                """,
                *params
            )
            
            results = []
            for row in rows:
                metadata = row["metadata"]
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                results.append({
                    "id": row["id"],
                    "content": row["content"],
                    "memory_type": row["memory_type"],
                    "source_type": row["source_type"],
                    "metadata": metadata,
                    "created_at": row["created_at"],
                    "similarity": float(row["similarity"]),
                })
            return results

    async def get_by_id(self, memory_id: int) -> Optional[MemoryRecord]:
        """Get memory by ID"""
        import json
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM memories WHERE id = $1",
                memory_id
            )
            
            if not row:
                return None
            
            metadata = row["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            return MemoryRecord(
                id=row["id"],
                content=row["content"],
                embedding=[],  # Don't load full embedding for simple fetch
                memory_type=MemoryType(row["memory_type"]),
                source_type=SourceType(row["source_type"]) if row["source_type"] else None,
                metadata=metadata,
                created_at=row["created_at"],
                updated_at=row.get("updated_at", row["created_at"]),
                expires_at=row["expires_at"],
                is_archived=row["archived"],
            )

    async def archive_expired(self) -> int:
        """Archive expired working memories"""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE memories 
                SET archived = true 
                WHERE memory_type = 'WORKING' 
                    AND expires_at IS NOT NULL 
                    AND expires_at <= NOW()
                    AND archived = false
                """
            )
            # Extract count from "UPDATE N" string
            count = int(result.split()[-1]) if result else 0
            return count

    async def count_by_type(self, memory_type: str) -> int:
        """Count memories by type"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM memories WHERE memory_type = $1 AND archived = false",
                memory_type
            )
            return row["count"] if row else 0

    async def get_user_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(*) FILTER (WHERE archived = false) as active_count,
                    COUNT(*) FILTER (WHERE archived = true) as archive_count,
                    COUNT(*) FILTER (WHERE memory_type = 'WORKING') as working_count,
                    COUNT(*) FILTER (WHERE memory_type = 'LONGTERM') as longterm_count
                FROM memories
                WHERE user_id = $1 OR user_id IS NULL
                """,
                user_id
            )
            return {
                "total_count": row["total_count"],
                "active_count": row["active_count"],
                "archive_count": row["archive_count"],
                "working_count": row["working_count"],
                "longterm_count": row["longterm_count"],
            }
