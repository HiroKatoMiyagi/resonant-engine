"""
Memory Management Service

This service provides high-level operations for managing the memory system,
coordinating between repositories to maintain the breathing history and
resonance patterns of the Resonant Engine.

Philosophy:
- Memory is "breath history + resonance traces"
- Time axis must be preserved (no deletions, only archives)
- Choices are kept, not forced
- Structure continuity is maintained across sessions
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from bridge.memory.models import (
    AgentContext,
    AgentType,
    BreathingCycle,
    BreathingPhase,
    Choice,
    ChoicePoint,
    Intent,
    IntentStatus,
    IntentType,
    Resonance,
    ResonanceState,
    Session,
    SessionStatus,
    Snapshot,
    SnapshotType,
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


class MemoryManagementService:
    """
    Main service for memory management operations.

    Coordinates between all repositories to provide:
    - Session management
    - Intent lifecycle tracking
    - Resonance state recording
    - Agent context preservation
    - Choice point management
    - Breathing cycle tracking
    - Temporal snapshots
    """

    def __init__(
        self,
        session_repo: SessionRepository,
        intent_repo: IntentRepository,
        resonance_repo: ResonanceRepository,
        agent_context_repo: AgentContextRepository,
        choice_point_repo: ChoicePointRepository,
        breathing_cycle_repo: BreathingCycleRepository,
        snapshot_repo: SnapshotRepository,
    ):
        self.session_repo = session_repo
        self.intent_repo = intent_repo
        self.resonance_repo = resonance_repo
        self.agent_context_repo = agent_context_repo
        self.choice_point_repo = choice_point_repo
        self.breathing_cycle_repo = breathing_cycle_repo
        self.snapshot_repo = snapshot_repo

    # ========================================================================
    # Session Management
    # ========================================================================

    async def start_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Start a new session (breathing unit).

        Args:
            user_id: The user identifier
            metadata: Optional metadata for the session

        Returns:
            The created session
        """
        session = Session(user_id=user_id, metadata=metadata or {})
        return await self.session_repo.create(session)

    async def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get a session by ID"""
        return await self.session_repo.get_by_id(session_id)

    async def update_session_heartbeat(self, session_id: UUID) -> Session:
        """Update the last_active timestamp of a session"""
        return await self.session_repo.update_heartbeat(session_id)

    async def update_session_status(
        self,
        session_id: UUID,
        status: SessionStatus
    ) -> Session:
        """Update the status of a session"""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        session.status = status
        session.last_active = datetime.now(timezone.utc)
        return await self.session_repo.update(session)

    async def get_session_summary(self, session_id: UUID) -> Dict[str, Any]:
        """Get a comprehensive summary of a session"""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        intents = await self.intent_repo.list_by_session(session_id)
        completed_intents = [i for i in intents if i.status == IntentStatus.COMPLETED]
        resonances = await self.resonance_repo.list_by_session(session_id)
        choice_points = await self.choice_point_repo.list_by_session(session_id)
        breathing_cycles = await self.breathing_cycle_repo.list_by_session(session_id)

        return {
            "session": session,
            "total_intents": len(intents),
            "completed_intents": len(completed_intents),
            "resonance_events": len(resonances),
            "choice_points": len(choice_points),
            "breathing_cycles": len(breathing_cycles),
            "avg_intensity": await self.resonance_repo.get_average_intensity(session_id),
        }

    # ========================================================================
    # Intent Management (Breathing Phase 1: Intake)
    # ========================================================================

    async def record_intent(
        self,
        session_id: UUID,
        intent_text: str,
        intent_type: IntentType,
        parent_intent_id: Optional[UUID] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Intent:
        """
        Record a new intent (Breathing Phase 1: Intake).

        Args:
            session_id: The session ID
            intent_text: Description of the intent
            intent_type: Type of intent
            parent_intent_id: Optional parent intent for hierarchical structure
            priority: Priority level (0-10)
            metadata: Optional metadata

        Returns:
            The created intent
        """
        intent = Intent(
            session_id=session_id,
            parent_intent_id=parent_intent_id,
            intent_text=intent_text,
            intent_type=intent_type,
            priority=priority,
            metadata=metadata or {},
        )
        return await self.intent_repo.create(intent)

    async def get_intent(self, intent_id: UUID) -> Optional[Intent]:
        """Get an intent by ID"""
        return await self.intent_repo.get_by_id(intent_id)

    async def update_intent_status(
        self,
        intent_id: UUID,
        status: IntentStatus
    ) -> Intent:
        """Update the status of an intent"""
        intent = await self.intent_repo.get_by_id(intent_id)
        if not intent:
            raise ValueError(f"Intent {intent_id} not found")
        intent.status = status
        return await self.intent_repo.update(intent)

    async def complete_intent(
        self,
        intent_id: UUID,
        outcome: Dict[str, Any]
    ) -> Intent:
        """
        Mark an intent as completed with its outcome.

        Args:
            intent_id: The intent ID
            outcome: The result of the intent (implementation, learnings, etc.)

        Returns:
            The updated intent
        """
        intent = await self.intent_repo.get_by_id(intent_id)
        if not intent:
            raise ValueError(f"Intent {intent_id} not found")
        intent.status = IntentStatus.COMPLETED
        intent.completed_at = datetime.now(timezone.utc)
        intent.outcome = outcome
        return await self.intent_repo.update(intent)

    async def search_intents(
        self,
        session_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Intent]:
        """Search intents by text"""
        return await self.intent_repo.search(session_id, query, limit)

    async def list_session_intents(
        self,
        session_id: UUID,
        status: Optional[IntentStatus] = None
    ) -> List[Intent]:
        """List all intents for a session"""
        return await self.intent_repo.list_by_session(session_id, status)

    # ========================================================================
    # Resonance Management (Breathing Phase 2: Resonance)
    # ========================================================================

    async def record_resonance(
        self,
        session_id: UUID,
        state: ResonanceState,
        intensity: float,
        agents: List[str],
        intent_id: Optional[UUID] = None,
        pattern_type: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resonance:
        """
        Record a resonance state (Breathing Phase 2: Resonance).

        Args:
            session_id: The session ID
            state: The resonance state
            intensity: Intensity of resonance (0.0-1.0)
            agents: List of agents involved ["yuno", "kana", "tsumu"]
            intent_id: Optional related intent
            pattern_type: Optional pattern classification
            duration_ms: Optional duration in milliseconds
            metadata: Optional metadata

        Returns:
            The created resonance record
        """
        resonance = Resonance(
            session_id=session_id,
            intent_id=intent_id,
            state=state,
            intensity=intensity,
            agents=agents,
            pattern_type=pattern_type,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        return await self.resonance_repo.create(resonance)

    async def list_session_resonances(
        self,
        session_id: UUID,
        state: Optional[ResonanceState] = None
    ) -> List[Resonance]:
        """List resonances for a session"""
        if state:
            return await self.resonance_repo.list_by_state(session_id, state)
        return await self.resonance_repo.list_by_session(session_id)

    async def get_resonance_statistics(self, session_id: UUID) -> Dict[str, Any]:
        """Get resonance statistics for a session"""
        resonances = await self.resonance_repo.list_by_session(session_id)
        if not resonances:
            return {
                "total": 0,
                "avg_intensity": 0.0,
                "state_distribution": {},
            }

        state_counts = {}
        for r in resonances:
            state_key = r.state.value
            state_counts[state_key] = state_counts.get(state_key, 0) + 1

        return {
            "total": len(resonances),
            "avg_intensity": sum(r.intensity for r in resonances) / len(resonances),
            "state_distribution": state_counts,
        }

    # ========================================================================
    # Choice Point Management (Breathing Phase 3: Structuring)
    # ========================================================================

    async def create_choice_point(
        self,
        session_id: UUID,
        intent_id: UUID,
        question: str,
        choices: List[Choice],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChoicePoint:
        """
        Create a choice point (Breathing Phase 3: Structuring).

        Choices are preserved, not forced. The selected_choice_id remains
        NULL until a decision is made.

        Args:
            session_id: The session ID
            intent_id: The related intent
            question: The question requiring a choice
            choices: List of available choices
            metadata: Optional metadata

        Returns:
            The created choice point
        """
        # Get session to retrieve user_id
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        choice_point = ChoicePoint(
            user_id=session.user_id,
            session_id=session_id,
            intent_id=intent_id,
            question=question,
            choices=choices,
            metadata=metadata or {},
        )
        return await self.choice_point_repo.create(choice_point)

    async def decide_choice(
        self,
        choice_point_id: UUID,
        selected_choice_id: str,
        rationale: str
    ) -> ChoicePoint:
        """
        Record a decision for a choice point.

        Args:
            choice_point_id: The choice point ID
            selected_choice_id: The ID of the selected choice
            rationale: The reasoning behind the decision

        Returns:
            The updated choice point
        """
        choice_point = await self.choice_point_repo.get_by_id(choice_point_id)
        if not choice_point:
            raise ValueError(f"ChoicePoint {choice_point_id} not found")

        # Validate that the selected choice exists
        valid_ids = [c.id for c in choice_point.choices]
        if selected_choice_id not in valid_ids:
            raise ValueError(f"Invalid choice ID: {selected_choice_id}")

        choice_point.selected_choice_id = selected_choice_id
        choice_point.decided_at = datetime.now(timezone.utc)
        choice_point.decision_rationale = rationale

        return await self.choice_point_repo.update(choice_point)

    async def get_pending_choices(self, session_id: UUID) -> List[ChoicePoint]:
        """Get all undecided choice points for a session"""
        return await self.choice_point_repo.list_pending(session_id)

    async def list_session_choices(self, session_id: UUID) -> List[ChoicePoint]:
        """List all choice points for a session"""
        return await self.choice_point_repo.list_by_session(session_id)

    # ========================================================================
    # Sprint 10: Enhanced Choice Point Methods
    # ========================================================================

    async def create_choice_point_enhanced(
        self,
        user_id: str,
        session_id: UUID,
        intent_id: UUID,
        question: str,
        choices: List[Choice],
        tags: Optional[List[str]] = None,
        context_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChoicePoint:
        """
        Create an enhanced choice point with Sprint 10 features.

        Args:
            user_id: User identifier (Sprint 10)
            session_id: The session ID
            intent_id: The related intent
            question: The question requiring a choice
            choices: List of available choices
            tags: Categorization tags (Sprint 10)
            context_type: Context classification (Sprint 10)
            metadata: Optional metadata

        Returns:
            The created choice point
        """
        choice_point = ChoicePoint(
            user_id=user_id,
            session_id=session_id,
            intent_id=intent_id,
            question=question,
            choices=choices,
            tags=tags or [],
            context_type=context_type,
            metadata=metadata or {},
        )
        return await self.choice_point_repo.create(choice_point)

    async def decide_choice_enhanced(
        self,
        choice_point_id: UUID,
        selected_choice_id: str,
        rationale: str,
        rejection_reasons: Optional[Dict[str, str]] = None
    ) -> ChoicePoint:
        """
        Record a decision with rejection reasons for unselected choices (Sprint 10).

        Args:
            choice_point_id: The choice point ID
            selected_choice_id: The ID of the selected choice
            rationale: The reasoning behind the decision
            rejection_reasons: Dict mapping choice_id to rejection reason

        Returns:
            The updated choice point with rejection reasons
        """
        choice_point = await self.choice_point_repo.get_by_id(choice_point_id)
        if not choice_point:
            raise ValueError(f"ChoicePoint {choice_point_id} not found")

        # Validate that the selected choice exists
        valid_ids = [c.id for c in choice_point.choices]
        if selected_choice_id not in valid_ids:
            raise ValueError(f"Invalid choice ID: {selected_choice_id}")

        # Update each choice with selection status and rejection reason
        updated_choices = []
        for choice in choice_point.choices:
            choice.selected = (choice.id == selected_choice_id)
            if choice.selected:
                choice.rejection_reason = None
            else:
                choice.rejection_reason = rejection_reasons.get(choice.id, "") if rejection_reasons else ""
            choice.evaluated_at = datetime.now(timezone.utc)
            updated_choices.append(choice)

        choice_point.choices = updated_choices
        choice_point.selected_choice_id = selected_choice_id
        choice_point.decided_at = datetime.now(timezone.utc)
        choice_point.decision_rationale = rationale

        return await self.choice_point_repo.update(choice_point)

    # ========================================================================
    # Agent Context Management (Breathing Phase 4: Re-reflection)
    # ========================================================================

    async def save_agent_context(
        self,
        session_id: UUID,
        agent_type: AgentType,
        context_data: Dict[str, Any],
        intent_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentContext:
        """
        Save agent context (Breathing Phase 4: Re-reflection).

        This creates a new version of the context, maintaining history.
        The previous version is linked via superseded_by.

        Args:
            session_id: The session ID
            agent_type: The agent type (yuno, kana, tsumu)
            context_data: The context data to save
            intent_id: Optional related intent
            metadata: Optional metadata

        Returns:
            The created context
        """
        # Get the latest version to increment
        latest = await self.agent_context_repo.get_latest(session_id, agent_type)
        version = latest.version + 1 if latest else 1

        context = AgentContext(
            session_id=session_id,
            intent_id=intent_id,
            agent_type=agent_type,
            context_data=context_data,
            version=version,
            metadata=metadata or {},
        )

        new_context = await self.agent_context_repo.create(context)

        # Update the previous version to point to the new one
        if latest:
            latest.superseded_by = new_context.id
            await self.agent_context_repo.update(latest)

        return new_context

    async def get_latest_agent_context(
        self,
        session_id: UUID,
        agent_type: AgentType
    ) -> Optional[AgentContext]:
        """Get the latest context for an agent"""
        return await self.agent_context_repo.get_latest(session_id, agent_type)

    async def get_all_agent_contexts(self, session_id: UUID) -> Dict[str, AgentContext]:
        """Get the latest contexts for all agents"""
        contexts = await self.agent_context_repo.get_all_latest(session_id)
        return {c.agent_type.value: c for c in contexts}

    # ========================================================================
    # Breathing Cycle Management
    # ========================================================================

    async def start_breathing_phase(
        self,
        session_id: UUID,
        phase: BreathingPhase,
        intent_id: Optional[UUID] = None,
        phase_data: Optional[Dict[str, Any]] = None
    ) -> BreathingCycle:
        """
        Start a new breathing phase.

        Args:
            session_id: The session ID
            phase: The breathing phase
            intent_id: Optional related intent
            phase_data: Optional phase-specific data

        Returns:
            The created breathing cycle
        """
        cycle = BreathingCycle(
            session_id=session_id,
            intent_id=intent_id,
            phase=phase,
            phase_data=phase_data or {},
        )
        return await self.breathing_cycle_repo.create(cycle)

    async def complete_breathing_phase(
        self,
        cycle_id: UUID,
        success: bool,
        phase_data: Optional[Dict[str, Any]] = None
    ) -> BreathingCycle:
        """
        Complete a breathing phase.

        Args:
            cycle_id: The breathing cycle ID
            success: Whether the phase completed successfully
            phase_data: Optional additional phase data

        Returns:
            The updated breathing cycle
        """
        cycle = await self.breathing_cycle_repo.get_by_id(cycle_id)
        if not cycle:
            raise ValueError(f"BreathingCycle {cycle_id} not found")

        cycle.completed_at = datetime.now(timezone.utc)
        cycle.success = success
        if phase_data:
            cycle.phase_data.update(phase_data)

        return await self.breathing_cycle_repo.update(cycle)

    async def get_current_breathing_phase(
        self,
        session_id: UUID
    ) -> Optional[BreathingCycle]:
        """Get the current (incomplete) breathing phase"""
        return await self.breathing_cycle_repo.get_current_phase(session_id)

    async def list_session_breathing_cycles(
        self,
        session_id: UUID
    ) -> List[BreathingCycle]:
        """List all breathing cycles for a session"""
        return await self.breathing_cycle_repo.list_by_session(session_id)

    # ========================================================================
    # Snapshot Management (Breathing Phase 5: Implementation)
    # ========================================================================

    async def create_snapshot(
        self,
        session_id: UUID,
        snapshot_type: SnapshotType,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Snapshot:
        """
        Create a snapshot of the current state (time axis preservation).

        Args:
            session_id: The session ID
            snapshot_type: The type of snapshot
            description: Optional description
            tags: Optional tags for searching

        Returns:
            The created snapshot
        """
        # Gather current state
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        intents = await self.intent_repo.list_by_session(session_id)
        resonances = await self.resonance_repo.list_by_session(session_id)
        contexts = await self.agent_context_repo.get_all_latest(session_id)
        choice_points = await self.choice_point_repo.list_by_session(session_id)
        breathing_cycles = await self.breathing_cycle_repo.list_by_session(session_id)

        snapshot_data = {
            "session": session.model_dump(mode="json"),
            "intents": [i.model_dump(mode="json") for i in intents],
            "resonances": [r.model_dump(mode="json") for r in resonances],
            "agent_contexts": [c.model_dump(mode="json") for c in contexts],
            "choice_points": [cp.model_dump(mode="json") for cp in choice_points],
            "breathing_cycles": [bc.model_dump(mode="json") for bc in breathing_cycles],
        }

        snapshot = Snapshot(
            session_id=session_id,
            snapshot_type=snapshot_type,
            snapshot_data=snapshot_data,
            description=description,
            tags=tags or [],
        )

        return await self.snapshot_repo.create(snapshot)

    async def restore_from_snapshot(self, snapshot_id: UUID) -> Dict[str, Any]:
        """
        Get snapshot data for restoration.

        Args:
            snapshot_id: The snapshot ID

        Returns:
            The snapshot data
        """
        snapshot = await self.snapshot_repo.get_by_id(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        return snapshot.snapshot_data

    async def list_session_snapshots(
        self,
        session_id: UUID,
        tags: Optional[List[str]] = None
    ) -> List[Snapshot]:
        """List snapshots for a session"""
        if tags:
            return await self.snapshot_repo.list_by_tags(session_id, tags)
        return await self.snapshot_repo.list_by_session(session_id)

    # ========================================================================
    # Session Continuity (Resonance Expansion)
    # ========================================================================

    async def continue_session(self, session_id: UUID) -> Dict[str, Any]:
        """
        Continue a previous session (session continuity guarantee).

        Restores the session state including:
        - Latest agent contexts
        - Pending choice points
        - Last intent

        Args:
            session_id: The session ID to continue

        Returns:
            Session continuation data
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Reactivate the session
        session.status = SessionStatus.ACTIVE
        session.last_active = datetime.now(timezone.utc)
        await self.session_repo.update(session)

        # Get latest contexts
        contexts = await self.get_all_agent_contexts(session_id)

        # Get pending choices
        pending_choices = await self.choice_point_repo.list_pending(session_id)

        # Get last intent
        intents = await self.intent_repo.list_by_session(session_id)
        last_intent = intents[-1] if intents else None

        # Get current breathing phase
        current_phase = await self.breathing_cycle_repo.get_current_phase(session_id)

        return {
            "session": session,
            "agent_contexts": {k: v.context_data for k, v in contexts.items()},
            "pending_choices": pending_choices,
            "last_intent": last_intent,
            "current_breathing_phase": current_phase,
        }
