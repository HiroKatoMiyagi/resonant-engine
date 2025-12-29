from uuid import UUID, uuid4
from typing import List, Optional, Tuple, Dict, Any
import json
from datetime import datetime, timezone
from app.repositories.base import BaseRepository
from app.models.intent import IntentCreate, IntentUpdate, IntentStatusUpdate, IntentResponse
from app.services.memory.database import IntentModel

class IntentRepository(BaseRepository):
    """
    Intent Repository - Updated for Bridge Integration Schema
    
    DB Schema (intents table):
    - id: UUID
    - session_id: UUID
    - intent_text: Text
    - intent_type: String
    - priority: Integer
    - status: String
    - outcome: JSONB
    - metadata: JSONB
    - created_at, updated_at, completed_at, parent_intent_id
    """
    
    async def create(self, data: IntentCreate) -> IntentResponse:
        # Note: IntentCreate from Pydantic doesn't have session_id.
        # We need to find or create a default session for the system context.
        # For this integration phase, we'll try to find any active session or create a dummy one.
        
        # Try to find a recent session for 'system_api_user'
        SYSTEM_USER = "system_api_user"
        session_query = "SELECT id FROM sessions WHERE user_id = $1 ORDER BY last_active DESC LIMIT 1"
        session_row = await self.db.fetchrow(session_query, SYSTEM_USER)
        
        if session_row:
            session_id = session_row['id']
        else:
            # Create a new session
            session_id = uuid4()
            create_session_sql = """
            INSERT INTO sessions (id, user_id, status, started_at, last_active, metadata)
            VALUES ($1, $2, 'active', NOW(), NOW(), '{}')
            """
            await self.db.execute(create_session_sql, session_id, SYSTEM_USER)
        
        query = """
        INSERT INTO intents (
            id, session_id, intent_text, intent_type, priority, 
            status, metadata, created_at, updated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        RETURNING *
        """
        
        intent_id = uuid4()
        # Default status 'pending'
        row = await self.db.fetchrow(
            query,
            intent_id,
            session_id,
            data.intent_text,
            data.intent_type or "unknown",
            data.priority,
            "pending",
            json.dumps(data.metadata) if data.metadata else json.dumps({})
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
            params.append(status.lower()) # normalized in DB usually lowercase? Check constraints.

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
        
        # Extend params for limit/offset
        params.extend([limit, offset])

        query = f"""
        SELECT * FROM intents
        WHERE {where_sql}
        ORDER BY priority DESC, created_at DESC
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
        rows = await self.db.fetch(query, *params) # Pass params as list? No, *params unpacks.
        
        return [self._to_response(row) for row in rows], total_count

    async def update(self, id: UUID, update_data: IntentUpdate) -> Optional[IntentResponse]:
        updates = []
        params = [id]
        param_count = 1
        
        # Map fields to columns
        if update_data.intent_text is not None:
            param_count += 1
            updates.append(f"intent_text = ${param_count}")
            params.append(update_data.intent_text)
            
        if update_data.intent_type is not None:
            param_count += 1
            updates.append(f"intent_type = ${param_count}")
            params.append(update_data.intent_type)
            
        if update_data.priority is not None:
            param_count += 1
            updates.append(f"priority = ${param_count}")
            params.append(update_data.priority)
            
        if update_data.status is not None:
            param_count += 1
            updates.append(f"status = ${param_count}")
            params.append(update_data.status.value) # Enum value string
            
        if update_data.outcome is not None:
            param_count += 1
            updates.append(f"outcome = ${param_count}::jsonb")
            params.append(json.dumps(update_data.outcome))
            
        if update_data.metadata is not None:
            # For metadata, we usually want to merge, but simple replacement is easier here.
            # Or use jsonb_set etc. Let's do simple replacement for now as per previous logic roughly.
            # Actually previous logic did merge in python.
            # Doing simple update here to be safe with time.
            param_count += 1
            updates.append(f"metadata = ${param_count}::jsonb")
            params.append(json.dumps(update_data.metadata))
            
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
        updates = ["status = $2", "updated_at = NOW()"]
        params = [id, data.status.value]
        param_count = 2
        
        if data.outcome is not None:
            param_count += 1
            updates.append(f"outcome = ${param_count}::jsonb")
            params.append(json.dumps(data.outcome))
            
        if data.status.value in ["completed", "failed"]:
            updates.append("completed_at = NOW()")
            
        query = f"""
        UPDATE intents
        SET {', '.join(updates)}
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
        """Map DB row to IntentResponse"""
        row_dict = dict(row)
        
        # Handle JSON fields
        metadata = row_dict.get('metadata')
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        if metadata is None:
            metadata = {}
            
        outcome = row_dict.get('outcome')
        if isinstance(outcome, str):
            try:
                outcome = json.loads(outcome)
            except:
                outcome = None
                
        # Status normalization if needed (DB should be lowercase 'pending' etc)
        status = row_dict.get('status', 'pending').lower()
        
        return IntentResponse(
            id=row_dict['id'],
            intent_text=row_dict.get('intent_text', ''),
            intent_type=row_dict.get('intent_type'),
            status=status,
            priority=row_dict.get('priority', 0),
            outcome=outcome,
            metadata=metadata,
            created_at=row_dict['created_at'],
            updated_at=row_dict['updated_at'],
            completed_at=row_dict.get('completed_at')
        )
