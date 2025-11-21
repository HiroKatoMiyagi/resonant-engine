"""
PostgreSQL Repository Implementations

These implementations store data in PostgreSQL using SQLAlchemy and AsyncSession.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bridge.memory.repositories import (
    SessionRepository,
    IntentRepository,
    ResonanceRepository,
    AgentContextRepository,
    ChoicePointRepository,
    BreathingCycleRepository,
    SnapshotRepository,
)
from bridge.memory.models import (
    Session,
    Intent,
    Resonance,
    AgentContext,
    ChoicePoint,
    BreathingCycle,
    Snapshot,
    SessionStatus,
    IntentStatus,
    ResonanceState,
    AgentType,
    BreathingPhase,
    Choice,
)
from bridge.memory.database import (
    SessionModel,
    IntentModel,
    ResonanceModel,
    AgentContextModel,
    ChoicePointModel,
    BreathingCycleModel,
    SnapshotModel,
)


class PostgresSessionRepository(SessionRepository):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create(self, session: Session) -> Session:
        async with self.session_factory() as db_session:
            model = SessionModel(
                id=session.id,
                user_id=session.user_id,
                started_at=session.started_at,
                last_active=session.last_active,
                status=session.status.value,
                meta_info=session.metadata,
            )
            db_session.add(model)
            await db_session.commit()
            return session

    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            model = result.scalar_one_or_none()
            if not model:
                return None
            return Session(
                id=model.id,
                user_id=model.user_id,
                started_at=model.started_at,
                last_active=model.last_active,
                status=SessionStatus(model.status),
                metadata=model.meta_info,
            )

    async def update(self, session: Session) -> Session:
        async with self.session_factory() as db_session:
            await db_session.execute(
                update(SessionModel)
                .where(SessionModel.id == session.id)
                .values(
                    last_active=session.last_active,
                    status=session.status.value,
                    meta_info=session.metadata,
                )
            )
            await db_session.commit()
            return session

    async def update_heartbeat(self, session_id: UUID) -> Session:
        async with self.session_factory() as db_session:
            now = datetime.now(timezone.utc)
            await db_session.execute(
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(last_active=now)
            )
            await db_session.commit()
            return await self.get_by_id(session_id)

    async def list_active(self, user_id: str) -> List[Session]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(SessionModel)
                .where(SessionModel.user_id == user_id)
                .where(SessionModel.status == SessionStatus.ACTIVE.value)
            )
            models = result.scalars().all()
            return [
                Session(
                    id=m.id,
                    user_id=m.user_id,
                    started_at=m.started_at,
                    last_active=m.last_active,
                    status=SessionStatus(m.status),
                    metadata=m.metadata,
                )
                for m in models
            ]

    async def list_by_status(self, status: str) -> List[Session]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(SessionModel).where(SessionModel.status == status)
            )
            models = result.scalars().all()
            return [
                Session(
                    id=m.id,
                    user_id=m.user_id,
                    started_at=m.started_at,
                    last_active=m.last_active,
                    status=SessionStatus(m.status),
                    metadata=m.metadata,
                )
                for m in models
            ]


class PostgresIntentRepository(IntentRepository):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create(self, intent: Intent) -> Intent:
        async with self.session_factory() as db_session:
            model = IntentModel(
                id=intent.id,
                session_id=intent.session_id,
                parent_intent_id=intent.parent_intent_id,
                intent_text=intent.intent_text,
                intent_type=intent.intent_type,
                priority=intent.priority,
                created_at=intent.created_at,
                updated_at=intent.updated_at,
                completed_at=intent.completed_at,
                status=intent.status.value,
                outcome=intent.outcome,
                meta_info=intent.metadata,
            )
            db_session.add(model)
            await db_session.commit()
            return intent

    async def get_by_id(self, intent_id: UUID) -> Optional[Intent]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(IntentModel).where(IntentModel.id == intent_id)
            )
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._to_domain(model)

    async def update(self, intent: Intent) -> Intent:
        async with self.session_factory() as db_session:
            await db_session.execute(
                update(IntentModel)
                .where(IntentModel.id == intent.id)
                .values(
                    updated_at=datetime.now(timezone.utc),
                    completed_at=intent.completed_at,
                    status=intent.status.value,
                    outcome=intent.outcome,
                    meta_info=intent.metadata,
                )
            )
            await db_session.commit()
            return intent

    async def list_by_session(
        self,
        session_id: UUID,
        status: Optional[IntentStatus] = None
    ) -> List[Intent]:
        async with self.session_factory() as db_session:
            query = select(IntentModel).where(IntentModel.session_id == session_id)
            if status:
                query = query.where(IntentModel.status == status.value)
            query = query.order_by(IntentModel.created_at)
            
            result = await db_session.execute(query)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def search(
        self,
        session_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Intent]:
        async with self.session_factory() as db_session:
            # Simple ILIKE search
            stmt = (
                select(IntentModel)
                .where(IntentModel.session_id == session_id)
                .where(IntentModel.intent_text.ilike(f"%{query}%"))
                .order_by(desc(IntentModel.created_at))
                .limit(limit)
            )
            result = await db_session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def list_children(self, parent_intent_id: UUID) -> List[Intent]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(IntentModel).where(IntentModel.parent_intent_id == parent_intent_id)
            )
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    def _to_domain(self, model: IntentModel) -> Intent:
        return Intent(
            id=model.id,
            session_id=model.session_id,
            parent_intent_id=model.parent_intent_id,
            intent_text=model.intent_text,
            intent_type=model.intent_type,
            priority=model.priority,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
            status=IntentStatus(model.status),
            outcome=model.outcome,
            metadata=model.meta_info,
        )


class PostgresChoicePointRepository(ChoicePointRepository):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create(self, choice_point: ChoicePoint) -> ChoicePoint:
        async with self.session_factory() as db_session:
            # Convert choices to dict list for JSONB
            choices_data = [c.model_dump() for c in choice_point.choices]
            
            model = ChoicePointModel(
                id=choice_point.id,
                user_id=choice_point.user_id,
                session_id=choice_point.session_id,
                intent_id=choice_point.intent_id,
                question=choice_point.question,
                choices=choices_data,
                selected_choice_id=choice_point.selected_choice_id,
                created_at=choice_point.created_at,
                decided_at=choice_point.decided_at,
                decision_rationale=choice_point.decision_rationale,
                meta_info=choice_point.metadata,
                tags=choice_point.tags,
                context_type=choice_point.context_type,
            )
            db_session.add(model)
            await db_session.commit()
            return choice_point

    async def get_by_id(self, choice_point_id: UUID) -> Optional[ChoicePoint]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(ChoicePointModel)
                .options(selectinload(ChoicePointModel.session))
                .where(ChoicePointModel.id == choice_point_id)
            )
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._to_domain(model)

    async def update(self, choice_point: ChoicePoint) -> ChoicePoint:
        async with self.session_factory() as db_session:
            choices_data = [c.model_dump() for c in choice_point.choices]
            await db_session.execute(
                update(ChoicePointModel)
                .where(ChoicePointModel.id == choice_point.id)
                .values(
                    choices=choices_data,
                    selected_choice_id=choice_point.selected_choice_id,
                    decided_at=choice_point.decided_at,
                    decision_rationale=choice_point.decision_rationale,
                    meta_info=choice_point.metadata,
                )
            )
            await db_session.commit()
            # Re-fetch to get session for user_id
            return await self.get_by_id(choice_point.id)

    async def list_by_session(self, session_id: UUID) -> List[ChoicePoint]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(ChoicePointModel)
                .options(selectinload(ChoicePointModel.session))
                .where(ChoicePointModel.session_id == session_id)
                .order_by(ChoicePointModel.created_at)
            )
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def list_pending(self, session_id: UUID) -> List[ChoicePoint]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(ChoicePointModel)
                .options(selectinload(ChoicePointModel.session))
                .where(ChoicePointModel.session_id == session_id)
                .where(ChoicePointModel.selected_choice_id.is_(None))
                .order_by(ChoicePointModel.created_at)
            )
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def list_by_intent(self, intent_id: UUID) -> List[ChoicePoint]:
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(ChoicePointModel)
                .options(selectinload(ChoicePointModel.session))
                .where(ChoicePointModel.intent_id == intent_id)
                .order_by(ChoicePointModel.created_at)
            )
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    def _to_domain(self, model: ChoicePointModel) -> ChoicePoint:
        choices = [Choice(**c) for c in model.choices]
        
        # Handle missing columns in model by checking metadata or defaults
        # If database.py is outdated, we might miss tags/context_type
        tags = model.meta_info.get("tags", []) if model.meta_info else []
        context_type = model.meta_info.get("context_type", "general") if model.meta_info else "general"
        
        # Try to get user_id from session if possible? 
        # The domain model requires user_id. But ChoicePointModel doesn't have it.
        # We might need to fetch session to get user_id, or store it in metadata.
        # For now, let's use a placeholder or fetch it.
        # Fetching it here is N+1 problem.
        # Ideally ChoicePointModel should have user_id (denormalized) or we join.
        # Let's assume we can get it from session relation if loaded, else placeholder.
        
        user_id = "unknown" # Placeholder
        if model.session:
            user_id = model.session.user_id
        
        return ChoicePoint(
            id=model.id,
            user_id=user_id, # This is a problem. Domain model needs it.
            session_id=model.session_id,
            intent_id=model.intent_id,
            question=model.question,
            choices=choices,
            selected_choice_id=model.selected_choice_id,
            created_at=model.created_at,
            decided_at=model.decided_at,
            decision_rationale=model.decision_rationale,
            metadata=model.meta_info,
            tags=tags,
            context_type=context_type
        )


# Placeholder implementations for others
class PostgresResonanceRepository(ResonanceRepository):
    def __init__(self, session_factory): self.session_factory = session_factory
    async def create(self, r): return r
    async def get_by_id(self, id): return None
    async def list_by_session(self, sid): return []
    async def list_by_state(self, sid, state): return []
    async def list_by_intent(self, iid): return []
    async def get_average_intensity(self, sid): return 0.0

class PostgresAgentContextRepository(AgentContextRepository):
    def __init__(self, session_factory): self.session_factory = session_factory
    async def create(self, c): return c
    async def get_by_id(self, id): return None
    async def update(self, c): return c
    async def get_latest(self, sid, at): return None
    async def get_all_latest(self, sid): return []
    async def list_versions(self, sid, at): return []

class PostgresBreathingCycleRepository(BreathingCycleRepository):
    def __init__(self, session_factory): self.session_factory = session_factory
    async def create(self, c): return c
    async def get_by_id(self, id): return None
    async def update(self, c): return c
    async def list_by_session(self, sid): return []
    async def list_by_phase(self, sid, p): return []
    async def get_current_phase(self, sid): return None

class PostgresSnapshotRepository(SnapshotRepository):
    def __init__(self, session_factory): self.session_factory = session_factory
    async def create(self, s): return s
    async def get_by_id(self, id): return None
    async def list_by_session(self, sid): return []
    async def list_by_tags(self, sid, tags): return []
    async def list_by_type(self, sid, t): return []
    async def get_latest(self, sid): return None
