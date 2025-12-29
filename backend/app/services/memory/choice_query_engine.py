"""
Choice Query Engine.

Provides advanced query capabilities for choice points, including:
- Tag-based search
- Time-range filtering
- Full-text search
- Contextual relevance ranking
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.services.memory.models import ChoicePoint, Choice


class ChoiceQueryEngine:
    """Advanced query engine for choice points"""

    def __init__(self, pool):
        self.pool = pool

    async def search_by_tags(
        self,
        user_id: str,
        tags: List[str],
        match_all: bool = False,
        limit: int = 10,
    ) -> List[ChoicePoint]:
        """Search choice points by tags"""
        op = "@>" if match_all else "&&"
        query = f"""
            SELECT * FROM choice_points
            WHERE user_id = $1
            AND tags {op} $2
            ORDER BY decided_at DESC NULLS LAST
            LIMIT $3
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, tags, limit)
            return [self._map_row(row) for row in rows]

    async def search_by_time_range(
        self,
        user_id: str,
        from_date: datetime,
        to_date: Optional[datetime],
        limit: int = 10,
    ) -> List[ChoicePoint]:
        """Search choice points by time range"""
        query = """
            SELECT * FROM choice_points
            WHERE user_id = $1
            AND decided_at >= $2
        """
        params = [user_id, from_date]
        
        if to_date:
            query += " AND decided_at <= $3"
            params.append(to_date)
            
        query += " ORDER BY decided_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._map_row(row) for row in rows]

    async def search_fulltext(
        self,
        user_id: str,
        search_text: str,
        limit: int = 10,
    ) -> List[ChoicePoint]:
        """Full-text search on question and rationale"""
        query = """
            SELECT *, ts_rank(to_tsvector('english', question || ' ' || coalesce(decision_rationale, '')), plainto_tsquery('english', $2)) as rank
            FROM choice_points
            WHERE user_id = $1
            AND to_tsvector('english', question || ' ' || coalesce(decision_rationale, '')) @@ plainto_tsquery('english', $2)
            ORDER BY rank DESC
            LIMIT $3
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, search_text, limit)
            return [self._map_row(row) for row in rows]

    async def get_relevant_choices_for_context(
        self,
        user_id: str,
        current_question: str,
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[ChoicePoint]:
        """Get relevant choice points for context"""
        # Note: This is a hybrid search (semantic + metadata)
        # Simplified implementation using fulltext search as proxy for semantic search in this migration step
        # Ideally would use pgvector cosine similarity if embeddings were available
        
        base_query = """
            SELECT *, ts_rank(to_tsvector('english', question || ' ' || coalesce(decision_rationale, '')), plainto_tsquery('english', $2)) as rank
            FROM choice_points
            WHERE user_id = $1
            AND to_tsvector('english', question || ' ' || coalesce(decision_rationale, '')) @@ plainto_tsquery('english', $2)
        """
        params = [user_id, current_question]
        
        if tags:
            base_query += " AND tags && $" + str(len(params) + 1)
            params.append(tags)
            
        base_query += " ORDER BY rank DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            return [self._map_row(row) for row in rows]

    def _map_row(self, row) -> ChoicePoint:
        """Map DB row to ChoicePoint model"""
        import json
        choices_data = row['choices']
        if isinstance(choices_data, str):
            choices_data = json.loads(choices_data)
        
        choices = [Choice(**c) for c in choices_data]
        
        return ChoicePoint(
            id=row['id'],
            user_id=row['user_id'],
            session_id=row['session_id'],
            intent_id=row['intent_id'],
            question=row['question'],
            choices=choices,
            selected_choice_id=row['selected_choice_id'],
            created_at=row['created_at'],
            decided_at=row['decided_at'],
            decision_rationale=row['decision_rationale'],
            tags=row['tags'] if 'tags' in row else [],
            context_type=row['context_type'] if 'context_type' in row else "general",
            metadata=row['metadata'] if 'metadata' in row else {},
        )


async def find_technology_decisions(
    engine: ChoiceQueryEngine,
    user_id: str,
    category: Optional[str] = None,
    limit: int = 5,
) -> List[ChoicePoint]:
    """Find technology related decisions"""
    tags = ['technology']
    if category:
        tags.append(category)
    return await engine.search_by_tags(user_id, tags, match_all=False, limit=limit)


async def find_recent_decisions(
    engine: ChoiceQueryEngine,
    user_id: str,
    days: int = 7,
    limit: int = 10,
) -> List[ChoicePoint]:
    """Find recent decisions"""
    from datetime import timedelta
    from_date = datetime.now() - timedelta(days=days)
    return await engine.search_by_time_range(user_id, from_date, None, limit)
