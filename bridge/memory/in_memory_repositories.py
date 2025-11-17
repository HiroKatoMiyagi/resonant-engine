"""
In-Memory Repository Implementations

These implementations store data in memory, useful for:
- Unit testing
- Development without database
- Rapid prototyping

Note: Data is lost when the application stops.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from bridge.memory.models import (
    AgentContext,
    AgentType,
    BreathingCycle,
    BreathingPhase,
    ChoicePoint,
    Intent,
    IntentStatus,
    Resonance,
    ResonanceState,
    Session,
    SessionStatus,
    Snapshot,
)
from bridge.memory.repositories import (
    AgentContextRepository,
    BreathingCycleRepository,
    ChoicePointRepository,
    IntentRepository,
    ResonanceRepository,
    SessionRepository,
    SnapshotRepository,
)


class InMemorySessionRepository(SessionRepository):
    """In-memory implementation of SessionRepository"""

    def __init__(self):
        self._sessions: Dict[UUID, Session] = {}

    async def create(self, session: Session) -> Session:
        self._sessions[session.id] = session
        return session

    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        return self._sessions.get(session_id)

    async def update(self, session: Session) -> Session:
        if session.id not in self._sessions:
            raise ValueError(f"Session {session.id} not found")
        self._sessions[session.id] = session
        return session

    async def update_heartbeat(self, session_id: UUID) -> Session:
        session = await self.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        session.last_active = datetime.now(timezone.utc)
        return await self.update(session)

    async def list_active(self, user_id: str) -> List[Session]:
        return [
            s for s in self._sessions.values()
            if s.user_id == user_id and s.status == SessionStatus.ACTIVE
        ]

    async def list_by_status(self, status: str) -> List[Session]:
        return [
            s for s in self._sessions.values()
            if s.status.value == status
        ]


class InMemoryIntentRepository(IntentRepository):
    """In-memory implementation of IntentRepository"""

    def __init__(self):
        self._intents: Dict[UUID, Intent] = {}

    async def create(self, intent: Intent) -> Intent:
        self._intents[intent.id] = intent
        return intent

    async def get_by_id(self, intent_id: UUID) -> Optional[Intent]:
        return self._intents.get(intent_id)

    async def update(self, intent: Intent) -> Intent:
        if intent.id not in self._intents:
            raise ValueError(f"Intent {intent.id} not found")
        intent.updated_at = datetime.now(timezone.utc)
        self._intents[intent.id] = intent
        return intent

    async def list_by_session(
        self,
        session_id: UUID,
        status: Optional[IntentStatus] = None
    ) -> List[Intent]:
        result = [
            i for i in self._intents.values()
            if i.session_id == session_id
        ]
        if status:
            result = [i for i in result if i.status == status]
        return sorted(result, key=lambda x: x.created_at)

    async def search(
        self,
        session_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Intent]:
        query_lower = query.lower()
        result = [
            i for i in self._intents.values()
            if i.session_id == session_id and query_lower in i.intent_text.lower()
        ]
        return sorted(result, key=lambda x: x.created_at, reverse=True)[:limit]

    async def list_children(self, parent_intent_id: UUID) -> List[Intent]:
        return [
            i for i in self._intents.values()
            if i.parent_intent_id == parent_intent_id
        ]


class InMemoryResonanceRepository(ResonanceRepository):
    """In-memory implementation of ResonanceRepository"""

    def __init__(self):
        self._resonances: Dict[UUID, Resonance] = {}

    async def create(self, resonance: Resonance) -> Resonance:
        self._resonances[resonance.id] = resonance
        return resonance

    async def get_by_id(self, resonance_id: UUID) -> Optional[Resonance]:
        return self._resonances.get(resonance_id)

    async def list_by_session(self, session_id: UUID) -> List[Resonance]:
        result = [
            r for r in self._resonances.values()
            if r.session_id == session_id
        ]
        return sorted(result, key=lambda x: x.timestamp)

    async def list_by_state(
        self,
        session_id: UUID,
        state: ResonanceState
    ) -> List[Resonance]:
        result = [
            r for r in self._resonances.values()
            if r.session_id == session_id and r.state == state
        ]
        return sorted(result, key=lambda x: x.timestamp)

    async def list_by_intent(self, intent_id: UUID) -> List[Resonance]:
        result = [
            r for r in self._resonances.values()
            if r.intent_id == intent_id
        ]
        return sorted(result, key=lambda x: x.timestamp)

    async def get_average_intensity(self, session_id: UUID) -> float:
        resonances = await self.list_by_session(session_id)
        if not resonances:
            return 0.0
        return sum(r.intensity for r in resonances) / len(resonances)


class InMemoryAgentContextRepository(AgentContextRepository):
    """In-memory implementation of AgentContextRepository"""

    def __init__(self):
        self._contexts: Dict[UUID, AgentContext] = {}

    async def create(self, context: AgentContext) -> AgentContext:
        self._contexts[context.id] = context
        return context

    async def get_by_id(self, context_id: UUID) -> Optional[AgentContext]:
        return self._contexts.get(context_id)

    async def update(self, context: AgentContext) -> AgentContext:
        if context.id not in self._contexts:
            raise ValueError(f"AgentContext {context.id} not found")
        self._contexts[context.id] = context
        return context

    async def get_latest(
        self,
        session_id: UUID,
        agent_type: AgentType
    ) -> Optional[AgentContext]:
        contexts = [
            c for c in self._contexts.values()
            if c.session_id == session_id and c.agent_type == agent_type
        ]
        if not contexts:
            return None
        return max(contexts, key=lambda x: x.version)

    async def get_all_latest(self, session_id: UUID) -> List[AgentContext]:
        result = []
        for agent_type in AgentType:
            latest = await self.get_latest(session_id, agent_type)
            if latest:
                result.append(latest)
        return result

    async def list_versions(
        self,
        session_id: UUID,
        agent_type: AgentType
    ) -> List[AgentContext]:
        result = [
            c for c in self._contexts.values()
            if c.session_id == session_id and c.agent_type == agent_type
        ]
        return sorted(result, key=lambda x: x.version)


class InMemoryChoicePointRepository(ChoicePointRepository):
    """In-memory implementation of ChoicePointRepository"""

    def __init__(self):
        self._choice_points: Dict[UUID, ChoicePoint] = {}

    async def create(self, choice_point: ChoicePoint) -> ChoicePoint:
        self._choice_points[choice_point.id] = choice_point
        return choice_point

    async def get_by_id(self, choice_point_id: UUID) -> Optional[ChoicePoint]:
        return self._choice_points.get(choice_point_id)

    async def update(self, choice_point: ChoicePoint) -> ChoicePoint:
        if choice_point.id not in self._choice_points:
            raise ValueError(f"ChoicePoint {choice_point.id} not found")
        self._choice_points[choice_point.id] = choice_point
        return choice_point

    async def list_by_session(self, session_id: UUID) -> List[ChoicePoint]:
        result = [
            cp for cp in self._choice_points.values()
            if cp.session_id == session_id
        ]
        return sorted(result, key=lambda x: x.created_at)

    async def list_pending(self, session_id: UUID) -> List[ChoicePoint]:
        result = [
            cp for cp in self._choice_points.values()
            if cp.session_id == session_id and cp.selected_choice_id is None
        ]
        return sorted(result, key=lambda x: x.created_at)

    async def list_by_intent(self, intent_id: UUID) -> List[ChoicePoint]:
        result = [
            cp for cp in self._choice_points.values()
            if cp.intent_id == intent_id
        ]
        return sorted(result, key=lambda x: x.created_at)


class InMemoryBreathingCycleRepository(BreathingCycleRepository):
    """In-memory implementation of BreathingCycleRepository"""

    def __init__(self):
        self._cycles: Dict[UUID, BreathingCycle] = {}

    async def create(self, cycle: BreathingCycle) -> BreathingCycle:
        self._cycles[cycle.id] = cycle
        return cycle

    async def get_by_id(self, cycle_id: UUID) -> Optional[BreathingCycle]:
        return self._cycles.get(cycle_id)

    async def update(self, cycle: BreathingCycle) -> BreathingCycle:
        if cycle.id not in self._cycles:
            raise ValueError(f"BreathingCycle {cycle.id} not found")
        self._cycles[cycle.id] = cycle
        return cycle

    async def list_by_session(self, session_id: UUID) -> List[BreathingCycle]:
        result = [
            c for c in self._cycles.values()
            if c.session_id == session_id
        ]
        return sorted(result, key=lambda x: x.started_at)

    async def list_by_phase(
        self,
        session_id: UUID,
        phase: BreathingPhase
    ) -> List[BreathingCycle]:
        result = [
            c for c in self._cycles.values()
            if c.session_id == session_id and c.phase == phase
        ]
        return sorted(result, key=lambda x: x.started_at)

    async def get_current_phase(self, session_id: UUID) -> Optional[BreathingCycle]:
        incomplete = [
            c for c in self._cycles.values()
            if c.session_id == session_id and c.completed_at is None
        ]
        if not incomplete:
            return None
        return max(incomplete, key=lambda x: x.started_at)


class InMemorySnapshotRepository(SnapshotRepository):
    """In-memory implementation of SnapshotRepository"""

    def __init__(self):
        self._snapshots: Dict[UUID, Snapshot] = {}

    async def create(self, snapshot: Snapshot) -> Snapshot:
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    async def get_by_id(self, snapshot_id: UUID) -> Optional[Snapshot]:
        return self._snapshots.get(snapshot_id)

    async def list_by_session(self, session_id: UUID) -> List[Snapshot]:
        result = [
            s for s in self._snapshots.values()
            if s.session_id == session_id
        ]
        return sorted(result, key=lambda x: x.created_at)

    async def list_by_tags(
        self,
        session_id: UUID,
        tags: List[str]
    ) -> List[Snapshot]:
        result = [
            s for s in self._snapshots.values()
            if s.session_id == session_id and any(tag in s.tags for tag in tags)
        ]
        return sorted(result, key=lambda x: x.created_at)

    async def list_by_type(
        self,
        session_id: UUID,
        snapshot_type: str
    ) -> List[Snapshot]:
        result = [
            s for s in self._snapshots.values()
            if s.session_id == session_id and s.snapshot_type.value == snapshot_type
        ]
        return sorted(result, key=lambda x: x.created_at)

    async def get_latest(self, session_id: UUID) -> Optional[Snapshot]:
        snapshots = await self.list_by_session(session_id)
        if not snapshots:
            return None
        return snapshots[-1]
