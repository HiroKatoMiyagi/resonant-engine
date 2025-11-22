from uuid import UUID
from typing import List, Optional, Tuple
import json
from backend.app.repositories.base import BaseRepository
from backend.app.models.intent import IntentCreate, IntentUpdate, IntentStatusUpdate, IntentResponse


class IntentRepository(BaseRepository):
    async def create(self, data: IntentCreate) -> IntentResponse:
        query = """
        INSERT INTO intents (description, intent_type, priority, metadata)
        VALUES ($1, $2, $3, $4::jsonb)
        RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            data.description,
            data.intent_type,
            data.priority,
            json.dumps(data.metadata)
        )
        return self._to_response(row)

    async def get_by_id(self, id: UUID) -> Optional[IntentResponse]:
        query = "SELECT * FROM intents WHERE id = $1"
        row = await self.db.fetchrow(query, id)
        return self._to_response(row) if row else None

    async def list(
        self,
        status: Optional[str] = None,
        intent_type: Optional[str] = None,
        priority_min: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[IntentResponse], int]:
        where_clauses = []
        params = []
        param_count = 0

        if status:
            param_count += 1
            where_clauses.append(f"status = ${param_count}")
            params.append(status)

        if intent_type:
            param_count += 1
            where_clauses.append(f"intent_type = ${param_count}")
            params.append(intent_type)

        if priority_min is not None:
            param_count += 1
            where_clauses.append(f"priority >= ${param_count}")
            params.append(priority_min)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count
        count_query = f"SELECT COUNT(*) FROM intents WHERE {where_sql}"
        total = await self.db.fetchrow(count_query, *params)
        total_count = total['count']

        # Fetch
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        query = f"""
        SELECT * FROM intents
        WHERE {where_sql}
        ORDER BY priority DESC, created_at DESC
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
        rows = await self.db.fetch(query, *params, limit, offset)

        return [self._to_response(row) for row in rows], total_count

    async def update(self, id: UUID, data: IntentUpdate) -> Optional[IntentResponse]:
        updates = []
        params = [id]
        param_count = 1

        if data.description is not None:
            param_count += 1
            updates.append(f"description = ${param_count}")
            params.append(data.description)

        if data.intent_type is not None:
            param_count += 1
            updates.append(f"intent_type = ${param_count}")
            params.append(data.intent_type)

        if data.status is not None:
            param_count += 1
            updates.append(f"status = ${param_count}")
            params.append(data.status.value)

        if data.priority is not None:
            param_count += 1
            updates.append(f"priority = ${param_count}")
            params.append(data.priority)

        if data.result is not None:
            param_count += 1
            updates.append(f"result = ${param_count}::jsonb")
            params.append(json.dumps(data.result))

        if data.metadata is not None:
            param_count += 1
            updates.append(f"metadata = ${param_count}::jsonb")
            params.append(json.dumps(data.metadata))

        if not updates:
            return await self.get_by_id(id)

        updates.append("updated_at = NOW()")
        query = f"""
        UPDATE intents SET {', '.join(updates)}
        WHERE id = $1
        RETURNING *
        """
        row = await self.db.fetchrow(query, *params)
        return self._to_response(row) if row else None

    async def update_status(self, id: UUID, data: IntentStatusUpdate) -> Optional[IntentResponse]:
        params = [id, data.status.value]
        result_sql = ""

        if data.result is not None:
            result_sql = ", result = $3::jsonb"
            params.append(json.dumps(data.result))

        processed_sql = ""
        if data.status.value in ["completed", "failed"]:
            processed_sql = ", processed_at = NOW()"

        query = f"""
        UPDATE intents
        SET status = $2{result_sql}{processed_sql}, updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """
        row = await self.db.fetchrow(query, *params)
        return self._to_response(row) if row else None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM intents WHERE id = $1 RETURNING id"
        result = await self.db.fetchrow(query, id)
        return result is not None

    def _to_response(self, row) -> IntentResponse:
        return IntentResponse(
            id=row['id'],
            description=row['description'],
            intent_type=row['intent_type'],
            status=row['status'],
            priority=row['priority'],
            result=row['result'] if isinstance(row['result'], dict) else None,
            metadata=row['metadata'] if isinstance(row['metadata'], dict) else {},
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            processed_at=row['processed_at']
        )
