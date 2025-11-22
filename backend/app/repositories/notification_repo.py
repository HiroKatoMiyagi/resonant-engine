from uuid import UUID
from typing import List, Optional, Tuple
import json
from backend.app.repositories.base import BaseRepository
from backend.app.models.notification import NotificationCreate, NotificationResponse


class NotificationRepository(BaseRepository):
    async def create(self, data: NotificationCreate) -> NotificationResponse:
        query = """
        INSERT INTO notifications (user_id, title, message, notification_type, metadata)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            data.user_id,
            data.title,
            data.message,
            data.notification_type.value,
            json.dumps(data.metadata)
        )
        return self._to_response(row)

    async def get_by_id(self, id: UUID) -> Optional[NotificationResponse]:
        query = "SELECT * FROM notifications WHERE id = $1"
        row = await self.db.fetchrow(query, id)
        return self._to_response(row) if row else None

    async def list(
        self,
        user_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[NotificationResponse], int]:
        where_clauses = []
        params = []
        param_count = 0

        if user_id:
            param_count += 1
            where_clauses.append(f"user_id = ${param_count}")
            params.append(user_id)

        if is_read is not None:
            param_count += 1
            where_clauses.append(f"is_read = ${param_count}")
            params.append(is_read)

        if notification_type:
            param_count += 1
            where_clauses.append(f"notification_type = ${param_count}")
            params.append(notification_type)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count
        count_query = f"SELECT COUNT(*) FROM notifications WHERE {where_sql}"
        total = await self.db.fetchrow(count_query, *params)
        total_count = total['count']

        # Fetch
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        query = f"""
        SELECT * FROM notifications
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
        rows = await self.db.fetch(query, *params, limit, offset)

        return [self._to_response(row) for row in rows], total_count

    async def mark_read(self, notification_ids: List[UUID]) -> int:
        if not notification_ids:
            return 0

        placeholders = ", ".join([f"${i+1}" for i in range(len(notification_ids))])
        query = f"""
        UPDATE notifications
        SET is_read = TRUE
        WHERE id IN ({placeholders})
        RETURNING id
        """
        rows = await self.db.fetch(query, *notification_ids)
        return len(rows)

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM notifications WHERE id = $1 RETURNING id"
        result = await self.db.fetchrow(query, id)
        return result is not None

    def _to_response(self, row) -> NotificationResponse:
        return NotificationResponse(
            id=row['id'],
            user_id=row['user_id'],
            title=row['title'],
            message=row['message'],
            notification_type=row['notification_type'],
            is_read=row['is_read'],
            metadata=row['metadata'] if isinstance(row['metadata'], dict) else {},
            created_at=row['created_at']
        )
