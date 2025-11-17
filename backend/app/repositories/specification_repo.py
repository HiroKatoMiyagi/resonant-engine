from uuid import UUID
from typing import List, Optional, Tuple
import json
from app.repositories.base import BaseRepository
from app.models.specification import SpecificationCreate, SpecificationUpdate, SpecificationResponse


class SpecificationRepository(BaseRepository):
    async def create(self, data: SpecificationCreate) -> SpecificationResponse:
        query = """
        INSERT INTO specifications (title, content, status, tags, metadata)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            data.title,
            data.content,
            data.status.value,
            data.tags,
            json.dumps(data.metadata)
        )
        return self._to_response(row)

    async def get_by_id(self, id: UUID) -> Optional[SpecificationResponse]:
        query = "SELECT * FROM specifications WHERE id = $1"
        row = await self.db.fetchrow(query, id)
        return self._to_response(row) if row else None

    async def list(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[SpecificationResponse], int]:
        where_clauses = []
        params = []
        param_count = 0

        if status:
            param_count += 1
            where_clauses.append(f"status = ${param_count}")
            params.append(status)

        if tags:
            param_count += 1
            where_clauses.append(f"tags && ${param_count}")
            params.append(tags)

        if search:
            param_count += 1
            where_clauses.append(f"title ILIKE ${param_count}")
            params.append(f"%{search}%")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count
        count_query = f"SELECT COUNT(*) FROM specifications WHERE {where_sql}"
        total = await self.db.fetchrow(count_query, *params)
        total_count = total['count']

        # Fetch
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        query = f"""
        SELECT * FROM specifications
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
        rows = await self.db.fetch(query, *params, limit, offset)

        return [self._to_response(row) for row in rows], total_count

    async def update(self, id: UUID, data: SpecificationUpdate) -> Optional[SpecificationResponse]:
        updates = []
        params = [id]
        param_count = 1

        if data.title is not None:
            param_count += 1
            updates.append(f"title = ${param_count}")
            params.append(data.title)

        if data.content is not None:
            param_count += 1
            updates.append(f"content = ${param_count}")
            params.append(data.content)
            updates.append("version = version + 1")

        if data.status is not None:
            param_count += 1
            updates.append(f"status = ${param_count}")
            params.append(data.status.value)

        if data.tags is not None:
            param_count += 1
            updates.append(f"tags = ${param_count}")
            params.append(data.tags)

        if data.metadata is not None:
            param_count += 1
            updates.append(f"metadata = ${param_count}::jsonb")
            params.append(json.dumps(data.metadata))

        if not updates:
            return await self.get_by_id(id)

        updates.append("updated_at = NOW()")
        query = f"""
        UPDATE specifications SET {', '.join(updates)}
        WHERE id = $1
        RETURNING *
        """
        row = await self.db.fetchrow(query, *params)
        return self._to_response(row) if row else None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM specifications WHERE id = $1 RETURNING id"
        result = await self.db.fetchrow(query, id)
        return result is not None

    def _to_response(self, row) -> SpecificationResponse:
        return SpecificationResponse(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            version=row['version'],
            status=row['status'],
            tags=row['tags'] if row['tags'] else [],
            metadata=row['metadata'] if isinstance(row['metadata'], dict) else {},
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
