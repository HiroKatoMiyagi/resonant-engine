from uuid import UUID
from typing import List, Optional, Tuple
import json
from backend.app.repositories.base import BaseRepository
from backend.app.models.message import MessageCreate, MessageUpdate, MessageResponse


class MessageRepository(BaseRepository):
    async def create(self, data: MessageCreate) -> MessageResponse:
        query = """
        INSERT INTO messages (user_id, content, message_type, metadata)
        VALUES ($1, $2, $3, $4::jsonb)
        RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            data.user_id,
            data.content,
            data.message_type.value,
            json.dumps(data.metadata)
        )
        return self._to_response(row)

    async def get_by_id(self, id: UUID) -> Optional[MessageResponse]:
        query = "SELECT * FROM messages WHERE id = $1"
        row = await self.db.fetchrow(query, id)
        return self._to_response(row) if row else None

    async def list(
        self,
        user_id: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[MessageResponse], int]:
        where_clauses = []
        params = []
        param_count = 0

        if user_id:
            param_count += 1
            where_clauses.append(f"user_id = ${param_count}")
            params.append(user_id)

        if message_type:
            param_count += 1
            where_clauses.append(f"message_type = ${param_count}")
            params.append(message_type)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count
        count_query = f"SELECT COUNT(*) FROM messages WHERE {where_sql}"
        total = await self.db.fetchrow(count_query, *params)
        total_count = total['count']

        # Fetch
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        query = f"""
        SELECT * FROM messages
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
        rows = await self.db.fetch(query, *params, limit, offset)

        return [self._to_response(row) for row in rows], total_count

    async def update(self, id: UUID, data: MessageUpdate) -> Optional[MessageResponse]:
        updates = []
        params = [id]
        param_count = 1

        if data.content is not None:
            param_count += 1
            updates.append(f"content = ${param_count}")
            params.append(data.content)

        if data.metadata is not None:
            param_count += 1
            updates.append(f"metadata = ${param_count}::jsonb")
            params.append(json.dumps(data.metadata))

        if not updates:
            return await self.get_by_id(id)

        updates.append("updated_at = NOW()")
        query = f"""
        UPDATE messages SET {', '.join(updates)}
        WHERE id = $1
        RETURNING *
        """
        row = await self.db.fetchrow(query, *params)
        return self._to_response(row) if row else None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM messages WHERE id = $1 RETURNING id"
        result = await self.db.fetchrow(query, id)
        return result is not None

    def _to_response(self, row) -> MessageResponse:
        return MessageResponse(
            id=row['id'],
            user_id=row['user_id'],
            content=row['content'],
            message_type=row['message_type'],
            metadata=row['metadata'] if isinstance(row['metadata'], dict) else {},
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
