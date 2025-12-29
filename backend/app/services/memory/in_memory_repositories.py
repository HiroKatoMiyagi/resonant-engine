"""
In-Memory implementations of repositories for testing.
"""

from typing import List, Optional, Any, Dict
from uuid import UUID, uuid4
from uuid import UUID, uuid4
from datetime import datetime, timezone
from copy import deepcopy

from app.services.memory.models import (
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
    Snapshot,
)
from app.services.memory.repositories import (
    AgentContextRepository,
    BreathingCycleRepository,
    ChoicePointRepository,
    IntentRepository,
    ResonanceRepository,
    SessionRepository,
    SnapshotRepository,
)


class InMemorySessionRepository(SessionRepository):
    def __init__(self):
        self._sessions = {}

    async def create(self, session: Session) -> Session:
        if not session.id:
            session.id = uuid4()
        self._sessions[session.id] = session
        return deepcopy(session)

    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        return deepcopy(self._sessions.get(session_id))

    async def update(self, session: Session) -> Session:
        self._sessions[session.id] = session
        return deepcopy(session)

    async def update_heartbeat(self, session_id: UUID) -> Session:
        session = self._sessions.get(session_id)
        if session:
            session.last_active = datetime.now(timezone.utc) # Mock time handling
        return deepcopy(session)

    async def list_active(self, user_id: str) -> List[Session]:
        return [
            deepcopy(s)
            for s in self._sessions.values()
            if s.user_id == user_id and s.status == "active"
        ]

    async def list_by_status(self, status: str) -> List[Session]:
        return [deepcopy(s) for s in self._sessions.values() if s.status == status]


class InMemoryIntentRepository(IntentRepository):
    def __init__(self):
        self._intents = {}

    async def create(self, intent: Intent) -> Intent:
        if not intent.id:
            intent.id = uuid4()
        self._intents[intent.id] = intent
        return deepcopy(intent)

    async def get_by_id(self, intent_id: UUID) -> Optional[Intent]:
        return deepcopy(self._intents.get(intent_id))

    async def update(self, intent: Intent) -> Intent:
        self._intents[intent.id] = intent
        return deepcopy(intent)

    async def list_by_session(
        self, session_id: UUID, status: Optional[IntentStatus] = None
    ) -> List[Intent]:
        res = [i for i in self._intents.values() if i.session_id == session_id]
        if status:
            res = [i for i in res if i.status == status]
        return [deepcopy(i) for i in res]

    async def search(
        self, session_id: UUID, query: str, limit: int = 10
    ) -> List[Intent]:
        res = [
            i
            for i in self._intents.values()
            if i.session_id == session_id and query.lower() in i.intent_text.lower()
        ]
        return [deepcopy(i) for i in res]

    async def list_children(self, parent_intent_id: UUID) -> List[Intent]:
        res = [i for i in self._intents.values() if i.parent_intent_id == parent_intent_id]
        return [deepcopy(i) for i in res]


class InMemoryResonanceRepository(ResonanceRepository):
    def __init__(self):
        self._resonances = {}

    async def create(self, resonance: Resonance) -> Resonance:
        if not resonance.id:
            resonance.id = uuid4()
        self._resonances[resonance.id] = resonance
        return deepcopy(resonance)

    async def get_by_id(self, resonance_id: UUID) -> Optional[Resonance]:
        return deepcopy(self._resonances.get(resonance_id))

    async def list_by_session(self, session_id: UUID) -> List[Resonance]:
        res = [r for r in self._resonances.values() if r.session_id == session_id]
        return [deepcopy(r) for r in res]

    async def list_by_state(
        self, session_id: UUID, state: ResonanceState
    ) -> List[Resonance]:
        res = [
            r
            for r in self._resonances.values()
            if r.session_id == session_id and r.state == state
        ]
        return [deepcopy(r) for r in res]

    async def list_by_intent(self, intent_id: UUID) -> List[Resonance]:
        res = [r for r in self._resonances.values() if r.intent_id == intent_id]
        return [deepcopy(r) for r in res]

    async def get_average_intensity(self, session_id: UUID) -> float:
        res = [r for r in self._resonances.values() if r.session_id == session_id]
        if not res:
            return 0.0
        return sum(r.intensity for r in res) / len(res)


class InMemoryAgentContextRepository(AgentContextRepository):
    def __init__(self):
        self._contexts = {}

    async def create(self, context: AgentContext) -> AgentContext:
        if not context.id:
            context.id = uuid4()
        self._contexts[context.id] = context
        return deepcopy(context)

    async def get_by_id(self, context_id: UUID) -> Optional[AgentContext]:
        return deepcopy(self._contexts.get(context_id))

    async def update(self, context: AgentContext) -> AgentContext:
        self._contexts[context.id] = context
        return deepcopy(context)

    async def get_latest(
        self, session_id: UUID, agent_type: AgentType
    ) -> Optional[AgentContext]:
        res = [
            c
            for c in self._contexts.values()
            if c.session_id == session_id and c.agent_type == agent_type
        ]
        if not res:
            return None
        return deepcopy(max(res, key=lambda x: x.version))

    async def get_all_latest(self, session_id: UUID) -> List[AgentContext]:
        latest_map = {}
        for c in self._contexts.values():
            if c.session_id == session_id:
                current = latest_map.get(c.agent_type)
                if not current or c.version > current.version:
                    latest_map[c.agent_type] = c
        return [deepcopy(c) for c in latest_map.values()]

    async def list_versions(
        self, session_id: UUID, agent_type: AgentType
    ) -> List[AgentContext]:
        res = [
            c
            for c in self._contexts.values()
            if c.session_id == session_id and c.agent_type == agent_type
        ]
        return sorted([deepcopy(c) for c in res], key=lambda x: x.version)


class InMemoryChoicePointRepository(ChoicePointRepository):
    def __init__(self):
        self._choices = {}

    async def create(self, choice_point: ChoicePoint) -> ChoicePoint:
        if not choice_point.id:
            choice_point.id = uuid4()
        self._choices[choice_point.id] = choice_point
        return deepcopy(choice_point)

    async def get_by_id(self, choice_point_id: UUID) -> Optional[ChoicePoint]:
        return deepcopy(self._choices.get(choice_point_id))

    async def update(self, choice_point: ChoicePoint) -> ChoicePoint:
        self._choices[choice_point.id] = choice_point
        return deepcopy(choice_point)

    async def list_by_session(self, session_id: UUID) -> List[ChoicePoint]:
        res = [c for c in self._choices.values() if c.session_id == session_id]
        return [deepcopy(c) for c in res]

    async def list_pending(self, session_id: UUID) -> List[ChoicePoint]:
        res = [
            c
            for c in self._choices.values()
            if c.session_id == session_id and c.selected_choice_id is None
        ]
        return [deepcopy(c) for c in res]

    async def list_by_intent(self, intent_id: UUID) -> List[ChoicePoint]:
        res = [c for c in self._choices.values() if c.intent_id == intent_id]
        return [deepcopy(c) for c in res]


class InMemoryBreathingCycleRepository(BreathingCycleRepository):
    def __init__(self):
        self._cycles = {}

    async def create(self, cycle: BreathingCycle) -> BreathingCycle:
        if not cycle.id:
            cycle.id = uuid4()
        self._cycles[cycle.id] = cycle
        return deepcopy(cycle)

    async def get_by_id(self, cycle_id: UUID) -> Optional[BreathingCycle]:
        return deepcopy(self._cycles.get(cycle_id))

    async def update(self, cycle: BreathingCycle) -> BreathingCycle:
        self._cycles[cycle.id] = cycle
        return deepcopy(cycle)

    async def list_by_session(self, session_id: UUID) -> List[BreathingCycle]:
        res = [c for c in self._cycles.values() if c.session_id == session_id]
        return [deepcopy(c) for c in res]

    async def list_by_phase(
        self, session_id: UUID, phase: BreathingPhase
    ) -> List[BreathingCycle]:
        res = [
            c
            for c in self._cycles.values()
            if c.session_id == session_id and c.phase == phase
        ]
        return [deepcopy(c) for c in res]

    async def get_current_phase(self, session_id: UUID) -> Optional[BreathingCycle]:
        res = [
            c
            for c in self._cycles.values()
            if c.session_id == session_id and c.completed_at is None
        ]
        if not res:
            return None
        return deepcopy(res[-1]) # Return last started?


class InMemorySnapshotRepository(SnapshotRepository):
    def __init__(self):
        self._snapshots = {}

    async def create(self, snapshot: Snapshot) -> Snapshot:
        if not snapshot.id:
            snapshot.id = uuid4()
        self._snapshots[snapshot.id] = snapshot
        return deepcopy(snapshot)

    async def get_by_id(self, snapshot_id: UUID) -> Optional[Snapshot]:
        return deepcopy(self._snapshots.get(snapshot_id))

    async def list_by_session(self, session_id: UUID) -> List[Snapshot]:
        res = [s for s in self._snapshots.values() if s.session_id == session_id]
        return [deepcopy(s) for s in res]

    async def list_by_tags(
        self, session_id: UUID, tags: List[str]
    ) -> List[Snapshot]:
        res = []
        for s in self._snapshots.values():
            if s.session_id == session_id and any(t in s.tags for t in tags):
                res.append(s)
        return [deepcopy(s) for s in res]

    async def list_by_type(
        self, session_id: UUID, snapshot_type: str
    ) -> List[Snapshot]:
        res = [
            s
            for s in self._snapshots.values()
            if s.session_id == session_id and s.snapshot_type == snapshot_type
        ]
        return [deepcopy(s) for s in res]

    async def get_latest(self, session_id: UUID) -> Optional[Snapshot]:
        res = [s for s in self._snapshots.values() if s.session_id == session_id]
        if not res:
            return None
        return deepcopy(max(res, key=lambda x: x.created_at))
