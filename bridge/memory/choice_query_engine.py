"""
Sprint 10: Choice Preservation System - Historical Query Engine

Provides advanced querying capabilities for Choice Points:
- Tag-based search (AND/OR logic)
- Time-range filtering
- Full-text search on questions
- Context relevance scoring for assembler integration

Philosophy:
- Past choices are living knowledge, not dead records
- Historical context enriches present decisions
- Search must be fast (<500ms) and accurate
"""

import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from .models import ChoicePoint, Choice

logger = logging.getLogger(__name__)


class ChoiceQueryEngine:
    """
    Historical Query Engine for Choice Points.

    Enables searching past decisions by tags, time ranges, and full-text,
    providing the foundation for historical context injection.
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize query engine with database connection pool.

        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    async def search_by_tags(
        self,
        user_id: str,
        tags: List[str],
        match_all: bool = False,
        limit: int = 10
    ) -> List[ChoicePoint]:
        """
        Search Choice Points by tags.

        Args:
            user_id: User ID to filter by
            tags: List of tags to search for
            match_all: If True, match ALL tags (AND). If False, match ANY tag (OR)
            limit: Maximum number of results

        Returns:
            List of matching Choice Points, sorted by decided_at DESC
        """
        async with self.pool.acquire() as conn:
            if match_all:
                # AND search: choice point must have ALL specified tags
                query = """
                    SELECT * FROM choice_points
                    WHERE user_id = $1
                      AND tags @> $2::text[]
                      AND selected_choice_id IS NOT NULL
                    ORDER BY decided_at DESC NULLS LAST
                    LIMIT $3
                """
            else:
                # OR search: choice point must have ANY of the specified tags
                query = """
                    SELECT * FROM choice_points
                    WHERE user_id = $1
                      AND tags && $2::text[]
                      AND selected_choice_id IS NOT NULL
                    ORDER BY decided_at DESC NULLS LAST
                    LIMIT $3
                """

            rows = await conn.fetch(query, user_id, tags, limit)
            return [self._row_to_choice_point(row) for row in rows]

    async def search_by_time_range(
        self,
        user_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[ChoicePoint]:
        """
        Search Choice Points by time range.

        Args:
            user_id: User ID to filter by
            from_date: Start of time range (inclusive). None = no lower bound
            to_date: End of time range (inclusive). None = no upper bound
            limit: Maximum number of results

        Returns:
            List of matching Choice Points, sorted by decided_at DESC
        """
        async with self.pool.acquire() as conn:
            conditions = ["user_id = $1", "selected_choice_id IS NOT NULL"]
            params: List[Any] = [user_id]
            param_idx = 2

            if from_date:
                conditions.append(f"decided_at >= ${param_idx}")
                params.append(from_date)
                param_idx += 1

            if to_date:
                conditions.append(f"decided_at <= ${param_idx}")
                params.append(to_date)
                param_idx += 1

            params.append(limit)

            query = f"""
                SELECT * FROM choice_points
                WHERE {' AND '.join(conditions)}
                ORDER BY decided_at DESC NULLS LAST
                LIMIT ${param_idx}
            """

            rows = await conn.fetch(query, *params)
            return [self._row_to_choice_point(row) for row in rows]

    async def search_fulltext(
        self,
        user_id: str,
        search_text: str,
        limit: int = 10
    ) -> List[ChoicePoint]:
        """
        Full-text search on Choice Point questions.

        Uses PostgreSQL's built-in full-text search with relevance ranking.

        Args:
            user_id: User ID to filter by
            search_text: Text to search for
            limit: Maximum number of results

        Returns:
            List of matching Choice Points, sorted by relevance (rank) DESC
        """
        async with self.pool.acquire() as conn:
            query = """
                SELECT *,
                       ts_rank(to_tsvector('english', question), plainto_tsquery('english', $2)) AS rank
                FROM choice_points
                WHERE user_id = $1
                  AND selected_choice_id IS NOT NULL
                  AND to_tsvector('english', question) @@ plainto_tsquery('english', $2)
                ORDER BY rank DESC, decided_at DESC
                LIMIT $3
            """

            rows = await conn.fetch(query, user_id, search_text, limit)
            # Remove rank field before conversion
            return [self._row_to_choice_point(row, exclude_fields=['rank']) for row in rows]

    async def get_relevant_choices_for_context(
        self,
        user_id: str,
        current_question: str,
        tags: Optional[List[str]] = None,
        limit: int = 3
    ) -> List[ChoicePoint]:
        """
        Get relevant past choices for Context Assembler.

        This method is optimized for context injection:
        1. Uses full-text search to find semantically related questions
        2. Optionally filters by tags for more precise matching
        3. Returns a small number of highly relevant choices

        Args:
            user_id: User ID
            current_question: The current question/context
            tags: Optional tag filter for more precise matching
            limit: Maximum number of results (default 3 for context injection)

        Returns:
            List of relevant past Choice Points
        """
        # First, get candidates via full-text search
        candidates = await self.search_fulltext(
            user_id=user_id,
            search_text=current_question,
            limit=limit * 2  # Get more candidates for filtering
        )

        # If tags provided, filter candidates by tag overlap
        if tags and candidates:
            candidates = [
                cp for cp in candidates
                if any(tag in cp.tags for tag in tags)
            ]

        # Return top N most relevant
        return candidates[:limit]

    def _row_to_choice_point(
        self,
        row: asyncpg.Record,
        exclude_fields: Optional[List[str]] = None
    ) -> ChoicePoint:
        """
        Convert database row to ChoicePoint model.

        Handles JSONB deserialization for choices field.

        Args:
            row: Database row record
            exclude_fields: Fields to exclude from conversion (e.g., 'rank' from fulltext search)

        Returns:
            ChoicePoint instance
        """
        row_dict = dict(row)

        # Remove excluded fields
        if exclude_fields:
            for field in exclude_fields:
                row_dict.pop(field, None)

        # Parse choices JSONB if it's a string
        if 'choices' in row_dict and isinstance(row_dict['choices'], str):
            row_dict['choices'] = json.loads(row_dict['choices'])

        # Convert choice dicts to Choice objects
        if 'choices' in row_dict and isinstance(row_dict['choices'], list):
            row_dict['choices'] = [
                Choice(**choice) if isinstance(choice, dict) else choice
                for choice in row_dict['choices']
            ]

        return ChoicePoint(**row_dict)


# Convenience functions for common query patterns

async def find_technology_decisions(
    engine: ChoiceQueryEngine,
    user_id: str,
    category: str = "technology_stack",
    limit: int = 10
) -> List[ChoicePoint]:
    """
    Find all technology stack decisions.

    Args:
        engine: ChoiceQueryEngine instance
        user_id: User ID
        category: Technology category tag (default: "technology_stack")
        limit: Maximum results

    Returns:
        List of technology-related Choice Points
    """
    return await engine.search_by_tags(
        user_id=user_id,
        tags=[category],
        match_all=False,
        limit=limit
    )


async def find_recent_decisions(
    engine: ChoiceQueryEngine,
    user_id: str,
    days: int = 30,
    limit: int = 10
) -> List[ChoicePoint]:
    """
    Find decisions made in the last N days.

    Args:
        engine: ChoiceQueryEngine instance
        user_id: User ID
        days: Number of days to look back
        limit: Maximum results

    Returns:
        List of recent Choice Points
    """
    from datetime import timedelta
    from_date = datetime.utcnow() - timedelta(days=days)

    return await engine.search_by_time_range(
        user_id=user_id,
        from_date=from_date,
        to_date=None,
        limit=limit
    )
