"""
Memory Management System - Repository Layer

Abstract repository interfaces for data access patterns.
These interfaces define the contract for data operations,
allowing for different backend implementations (PostgreSQL, mock, etc.)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

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


class SessionRepository(ABC):
    """Abstract repository for session operations"""

    @abstractmethod
    async def create(self, session: Session) -> Session:
        """Create a new session"""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        """Get a session by its ID"""
        pass

    @abstractmethod
    async def update(self, session: Session) -> Session:
        """Update an existing session"""
        pass

    @abstractmethod
    async def update_heartbeat(self, session_id: UUID) -> Session:
        """Update the last_active timestamp of a session"""
        pass

    @abstractmethod
    async def list_active(self, user_id: str) -> List[Session]:
        """List all active sessions for a user"""
        pass

    @abstractmethod
    async def list_by_status(self, status: str) -> List[Session]:
        """List sessions by status"""
        pass


class IntentRepository(ABC):
    """Abstract repository for intent operations"""

    @abstractmethod
    async def create(self, intent: Intent) -> Intent:
        """Create a new intent"""
        pass

    @abstractmethod
    async def get_by_id(self, intent_id: UUID) -> Optional[Intent]:
        """Get an intent by its ID"""
        pass

    @abstractmethod
    async def update(self, intent: Intent) -> Intent:
        """Update an existing intent"""
        pass

    @abstractmethod
    async def list_by_session(
        self,
        session_id: UUID,
        status: Optional[IntentStatus] = None
    ) -> List[Intent]:
        """List intents for a session, optionally filtered by status"""
        pass

    @abstractmethod
    async def search(
        self,
        session_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Intent]:
        """Search intents by text"""
        pass

    @abstractmethod
    async def list_children(self, parent_intent_id: UUID) -> List[Intent]:
        """List child intents of a parent"""
        pass


class ResonanceRepository(ABC):
    """Abstract repository for resonance operations"""

    @abstractmethod
    async def create(self, resonance: Resonance) -> Resonance:
        """Create a new resonance record"""
        pass

    @abstractmethod
    async def get_by_id(self, resonance_id: UUID) -> Optional[Resonance]:
        """Get a resonance by its ID"""
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> List[Resonance]:
        """List all resonances for a session"""
        pass

    @abstractmethod
    async def list_by_state(
        self,
        session_id: UUID,
        state: ResonanceState
    ) -> List[Resonance]:
        """List resonances by state"""
        pass

    @abstractmethod
    async def list_by_intent(self, intent_id: UUID) -> List[Resonance]:
        """List resonances for a specific intent"""
        pass

    @abstractmethod
    async def get_average_intensity(self, session_id: UUID) -> float:
        """Get the average intensity for a session"""
        pass


class AgentContextRepository(ABC):
    """Abstract repository for agent context operations"""

    @abstractmethod
    async def create(self, context: AgentContext) -> AgentContext:
        """Create a new agent context"""
        pass

    @abstractmethod
    async def get_by_id(self, context_id: UUID) -> Optional[AgentContext]:
        """Get an agent context by its ID"""
        pass

    @abstractmethod
    async def update(self, context: AgentContext) -> AgentContext:
        """Update an existing agent context"""
        pass

    @abstractmethod
    async def get_latest(
        self,
        session_id: UUID,
        agent_type: AgentType
    ) -> Optional[AgentContext]:
        """Get the latest context for an agent in a session"""
        pass

    @abstractmethod
    async def get_all_latest(self, session_id: UUID) -> List[AgentContext]:
        """Get the latest contexts for all agents in a session"""
        pass

    @abstractmethod
    async def list_versions(
        self,
        session_id: UUID,
        agent_type: AgentType
    ) -> List[AgentContext]:
        """List all versions of context for an agent"""
        pass


class ChoicePointRepository(ABC):
    """Abstract repository for choice point operations"""

    @abstractmethod
    async def create(self, choice_point: ChoicePoint) -> ChoicePoint:
        """Create a new choice point"""
        pass

    @abstractmethod
    async def get_by_id(self, choice_point_id: UUID) -> Optional[ChoicePoint]:
        """Get a choice point by its ID"""
        pass

    @abstractmethod
    async def update(self, choice_point: ChoicePoint) -> ChoicePoint:
        """Update an existing choice point"""
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> List[ChoicePoint]:
        """List all choice points for a session"""
        pass

    @abstractmethod
    async def list_pending(self, session_id: UUID) -> List[ChoicePoint]:
        """List undecided choice points for a session"""
        pass

    @abstractmethod
    async def list_by_intent(self, intent_id: UUID) -> List[ChoicePoint]:
        """List choice points for a specific intent"""
        pass


class BreathingCycleRepository(ABC):
    """Abstract repository for breathing cycle operations"""

    @abstractmethod
    async def create(self, cycle: BreathingCycle) -> BreathingCycle:
        """Create a new breathing cycle"""
        pass

    @abstractmethod
    async def get_by_id(self, cycle_id: UUID) -> Optional[BreathingCycle]:
        """Get a breathing cycle by its ID"""
        pass

    @abstractmethod
    async def update(self, cycle: BreathingCycle) -> BreathingCycle:
        """Update an existing breathing cycle"""
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> List[BreathingCycle]:
        """List all breathing cycles for a session"""
        pass

    @abstractmethod
    async def list_by_phase(
        self,
        session_id: UUID,
        phase: BreathingPhase
    ) -> List[BreathingCycle]:
        """List breathing cycles by phase"""
        pass

    @abstractmethod
    async def get_current_phase(self, session_id: UUID) -> Optional[BreathingCycle]:
        """Get the current (incomplete) breathing cycle"""
        pass


class SnapshotRepository(ABC):
    """Abstract repository for snapshot operations"""

    @abstractmethod
    async def create(self, snapshot: Snapshot) -> Snapshot:
        """Create a new snapshot"""
        pass

    @abstractmethod
    async def get_by_id(self, snapshot_id: UUID) -> Optional[Snapshot]:
        """Get a snapshot by its ID"""
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> List[Snapshot]:
        """List all snapshots for a session"""
        pass

    @abstractmethod
    async def list_by_tags(
        self,
        session_id: UUID,
        tags: List[str]
    ) -> List[Snapshot]:
        """List snapshots that match any of the given tags"""
        pass

    @abstractmethod
    async def list_by_type(
        self,
        session_id: UUID,
        snapshot_type: str
    ) -> List[Snapshot]:
        """List snapshots by type"""
        pass

    @abstractmethod
    async def get_latest(self, session_id: UUID) -> Optional[Snapshot]:
        """Get the most recent snapshot for a session"""
        pass
