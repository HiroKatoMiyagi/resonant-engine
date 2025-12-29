"""
Unit tests for Memory Management Service.

Tests business logic and service-level operations.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.services.memory.models import (
    AgentType,
    BreathingPhase,
    Choice,
    IntentStatus,
    IntentType,
    ResonanceState,
    SessionStatus,
    SnapshotType,
)
from app.services.memory.service import MemoryManagementService
from app.services.memory.in_memory_repositories import (
    InMemorySessionRepository,
    InMemoryIntentRepository,
    InMemoryResonanceRepository,
    InMemoryAgentContextRepository,
    InMemoryChoicePointRepository,
    InMemoryBreathingCycleRepository,
    InMemorySnapshotRepository,
)


@pytest.fixture
def memory_service():
    """Create a memory service with in-memory repositories"""
    return MemoryManagementService(
        session_repo=InMemorySessionRepository(),
        intent_repo=InMemoryIntentRepository(),
        resonance_repo=InMemoryResonanceRepository(),
        agent_context_repo=InMemoryAgentContextRepository(),
        choice_point_repo=InMemoryChoicePointRepository(),
        breathing_cycle_repo=InMemoryBreathingCycleRepository(),
        snapshot_repo=InMemorySnapshotRepository(),
    )


class TestSessionManagement:
    """Tests for session management"""

    @pytest.mark.asyncio
    async def test_start_session(self, memory_service):
        """Start a new session"""
        session = await memory_service.start_session("hiroaki")
        assert session.id is not None
        assert session.user_id == "hiroaki"
        assert session.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_start_session_with_metadata(self, memory_service):
        """Start session with metadata"""
        metadata = {"client": "web", "version": "1.0"}
        session = await memory_service.start_session("hiroaki", metadata)
        assert session.metadata == metadata

    @pytest.mark.asyncio
    async def test_get_session(self, memory_service):
        """Get session by ID"""
        created = await memory_service.start_session("hiroaki")
        retrieved = await memory_service.get_session(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_update_session_heartbeat(self, memory_service):
        """Update session heartbeat"""
        session = await memory_service.start_session("hiroaki")
        original_time = session.last_active
        updated = await memory_service.update_session_heartbeat(session.id)
        assert updated.last_active >= original_time

    @pytest.mark.asyncio
    async def test_update_session_status(self, memory_service):
        """Update session status"""
        session = await memory_service.start_session("hiroaki")
        updated = await memory_service.update_session_status(
            session.id, SessionStatus.PAUSED
        )
        assert updated.status == SessionStatus.PAUSED

    @pytest.mark.asyncio
    async def test_get_session_summary(self, memory_service):
        """Get comprehensive session summary"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.record_intent(
            session.id, "Test intent", IntentType.EXPLORATION
        )
        summary = await memory_service.get_session_summary(session.id)
        assert summary["total_intents"] == 1
        assert summary["completed_intents"] == 0
        assert "avg_intensity" in summary


class TestIntentManagement:
    """Tests for intent management (Breathing Phase 1: Intake)"""

    @pytest.mark.asyncio
    async def test_record_intent(self, memory_service):
        """Record a new intent"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id,
            "Design memory system",
            IntentType.FEATURE_REQUEST,
            priority=8,
        )
        assert intent.id is not None
        assert intent.intent_text == "Design memory system"
        assert intent.status == IntentStatus.PENDING
        assert intent.priority == 8

    @pytest.mark.asyncio
    async def test_record_hierarchical_intent(self, memory_service):
        """Record hierarchical intents"""
        session = await memory_service.start_session("hiroaki")
        parent = await memory_service.record_intent(
            session.id, "Parent task", IntentType.FEATURE_REQUEST
        )
        child = await memory_service.record_intent(
            session.id,
            "Child task",
            IntentType.FEATURE_REQUEST,
            parent_intent_id=parent.id,
        )
        assert child.parent_intent_id == parent.id

    @pytest.mark.asyncio
    async def test_get_intent(self, memory_service):
        """Get intent by ID"""
        session = await memory_service.start_session("hiroaki")
        created = await memory_service.record_intent(
            session.id, "Test", IntentType.BUG_FIX
        )
        retrieved = await memory_service.get_intent(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_update_intent_status(self, memory_service):
        """Update intent status"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Test", IntentType.EXPLORATION
        )
        updated = await memory_service.update_intent_status(
            intent.id, IntentStatus.IN_PROGRESS
        )
        assert updated.status == IntentStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_complete_intent(self, memory_service):
        """Complete an intent with outcome"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Test", IntentType.FEATURE_REQUEST
        )
        outcome = {"implementation": "Done", "learnings": ["Lesson 1"]}
        completed = await memory_service.complete_intent(intent.id, outcome)
        assert completed.status == IntentStatus.COMPLETED
        assert completed.completed_at is not None
        assert completed.outcome == outcome

    @pytest.mark.asyncio
    async def test_search_intents(self, memory_service):
        """Search intents by text"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.record_intent(
            session.id, "PostgreSQL schema design", IntentType.FEATURE_REQUEST
        )
        await memory_service.record_intent(
            session.id, "API implementation", IntentType.FEATURE_REQUEST
        )
        results = await memory_service.search_intents(session.id, "PostgreSQL")
        assert len(results) >= 1
        assert "PostgreSQL" in results[0].intent_text

    @pytest.mark.asyncio
    async def test_list_session_intents_by_status(self, memory_service):
        """List intents filtered by status"""
        session = await memory_service.start_session("hiroaki")
        intent1 = await memory_service.record_intent(
            session.id, "Pending", IntentType.EXPLORATION
        )
        intent2 = await memory_service.record_intent(
            session.id, "Completed", IntentType.BUG_FIX
        )
        await memory_service.complete_intent(intent2.id, {"done": True})

        pending = await memory_service.list_session_intents(
            session.id, IntentStatus.PENDING
        )
        assert len(pending) == 1
        assert pending[0].id == intent1.id


class TestResonanceManagement:
    """Tests for resonance management (Breathing Phase 2: Resonance)"""

    @pytest.mark.asyncio
    async def test_record_resonance(self, memory_service):
        """Record a resonance state"""
        session = await memory_service.start_session("hiroaki")
        resonance = await memory_service.record_resonance(
            session.id,
            ResonanceState.ALIGNED,
            0.85,
            ["yuno", "kana"],
            pattern_type="philosophical_alignment",
        )
        assert resonance.id is not None
        assert resonance.state == ResonanceState.ALIGNED
        assert resonance.intensity == 0.85
        assert resonance.agents == ["yuno", "kana"]

    @pytest.mark.asyncio
    async def test_list_session_resonances(self, memory_service):
        """List all resonances for a session"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.record_resonance(
            session.id, ResonanceState.ALIGNED, 0.8, ["kana"]
        )
        await memory_service.record_resonance(
            session.id, ResonanceState.EXPLORING, 0.6, ["yuno"]
        )
        resonances = await memory_service.list_session_resonances(session.id)
        assert len(resonances) == 2

    @pytest.mark.asyncio
    async def test_list_resonances_by_state(self, memory_service):
        """Filter resonances by state"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.record_resonance(
            session.id, ResonanceState.ALIGNED, 0.8, ["kana"]
        )
        await memory_service.record_resonance(
            session.id, ResonanceState.EXPLORING, 0.6, ["yuno"]
        )
        aligned = await memory_service.list_session_resonances(
            session.id, ResonanceState.ALIGNED
        )
        assert len(aligned) == 1
        assert aligned[0].state == ResonanceState.ALIGNED

    @pytest.mark.asyncio
    async def test_get_resonance_statistics(self, memory_service):
        """Get resonance statistics"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.record_resonance(
            session.id, ResonanceState.ALIGNED, 0.8, ["kana"]
        )
        await memory_service.record_resonance(
            session.id, ResonanceState.ALIGNED, 0.9, ["yuno"]
        )
        stats = await memory_service.get_resonance_statistics(session.id)
        assert stats["total"] == 2
        assert abs(stats["avg_intensity"] - 0.85) < 0.001  # Float precision
        assert stats["state_distribution"]["aligned"] == 2


class TestAgentContextManagement:
    """Tests for agent context management (Breathing Phase 4: Re-reflection)"""

    @pytest.mark.asyncio
    async def test_save_agent_context(self, memory_service):
        """Save agent context"""
        session = await memory_service.start_session("hiroaki")
        context = await memory_service.save_agent_context(
            session.id,
            AgentType.KANA,
            {"focus": "memory design", "decisions": []},
        )
        assert context.id is not None
        assert context.agent_type == AgentType.KANA
        assert context.version == 1
        assert context.context_data["focus"] == "memory design"

    @pytest.mark.asyncio
    async def test_agent_context_versioning(self, memory_service):
        """Agent context versioning"""
        session = await memory_service.start_session("hiroaki")
        v1 = await memory_service.save_agent_context(
            session.id, AgentType.KANA, {"version": 1}
        )
        v2 = await memory_service.save_agent_context(
            session.id, AgentType.KANA, {"version": 2}
        )
        assert v2.version == 2
        # Check that v1 is updated to point to v2
        updated_v1 = await memory_service.agent_context_repo.get_by_id(v1.id)
        assert updated_v1.superseded_by == v2.id

    @pytest.mark.asyncio
    async def test_get_latest_agent_context(self, memory_service):
        """Get latest context for an agent"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.save_agent_context(
            session.id, AgentType.YUNO, {"version": 1}
        )
        await memory_service.save_agent_context(
            session.id, AgentType.YUNO, {"version": 2}
        )
        latest = await memory_service.get_latest_agent_context(
            session.id, AgentType.YUNO
        )
        assert latest.version == 2
        assert latest.context_data["version"] == 2

    @pytest.mark.asyncio
    async def test_get_all_agent_contexts(self, memory_service):
        """Get all agent contexts for a session"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.save_agent_context(
            session.id, AgentType.YUNO, {"agent": "yuno"}
        )
        await memory_service.save_agent_context(
            session.id, AgentType.KANA, {"agent": "kana"}
        )
        await memory_service.save_agent_context(
            session.id, AgentType.TSUMU, {"agent": "tsumu"}
        )
        contexts = await memory_service.get_all_agent_contexts(session.id)
        assert len(contexts) == 3
        assert "yuno" in contexts
        assert "kana" in contexts
        assert "tsumu" in contexts


class TestChoicePointManagement:
    """Tests for choice point management (Breathing Phase 3: Structuring)"""

    @pytest.mark.asyncio
    async def test_create_choice_point(self, memory_service):
        """Create a choice point"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Test", IntentType.FEATURE_REQUEST
        )
        cp = await memory_service.create_choice_point(
            session.id,
            intent.id,
            "PostgreSQL vs SQLite?",
            [
                Choice(id="pg", description="PostgreSQL", implications={}),
                Choice(id="sqlite", description="SQLite", implications={}),
            ],
        )
        assert cp.id is not None
        assert cp.question == "PostgreSQL vs SQLite?"
        assert cp.selected_choice_id is None  # Pending

    @pytest.mark.asyncio
    async def test_decide_choice(self, memory_service):
        """Decide on a choice point"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Test", IntentType.FEATURE_REQUEST
        )
        cp = await memory_service.create_choice_point(
            session.id,
            intent.id,
            "A or B?",
            [
                Choice(id="a", description="A", implications={}),
                Choice(id="b", description="B", implications={}),
            ],
        )
        decided = await memory_service.decide_choice(
            cp.id, "a", "A is better for our use case"
        )
        assert decided.selected_choice_id == "a"
        assert decided.decided_at is not None
        assert decided.decision_rationale == "A is better for our use case"

    @pytest.mark.asyncio
    async def test_get_pending_choices(self, memory_service):
        """Get pending choice points"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Test", IntentType.EXPLORATION
        )
        cp1 = await memory_service.create_choice_point(
            session.id,
            intent.id,
            "Question 1?",
            [
                Choice(id="a", description="A", implications={}),
                Choice(id="b", description="B", implications={}),
            ],
        )
        cp2 = await memory_service.create_choice_point(
            session.id,
            intent.id,
            "Question 2?",
            [
                Choice(id="x", description="X", implications={}),
                Choice(id="y", description="Y", implications={}),
            ],
        )
        await memory_service.decide_choice(cp1.id, "a", "Decided")

        pending = await memory_service.get_pending_choices(session.id)
        assert len(pending) == 1
        assert pending[0].id == cp2.id

    @pytest.mark.asyncio
    async def test_decide_invalid_choice_raises_error(self, memory_service):
        """Invalid choice ID raises error"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Test", IntentType.EXPLORATION
        )
        cp = await memory_service.create_choice_point(
            session.id,
            intent.id,
            "A or B?",
            [
                Choice(id="a", description="A", implications={}),
                Choice(id="b", description="B", implications={}),
            ],
        )
        with pytest.raises(ValueError, match="Invalid choice ID"):
            await memory_service.decide_choice(cp.id, "invalid", "Reason")


class TestBreathingCycleManagement:
    """Tests for breathing cycle management"""

    @pytest.mark.asyncio
    async def test_start_breathing_phase(self, memory_service):
        """Start a breathing phase"""
        session = await memory_service.start_session("hiroaki")
        cycle = await memory_service.start_breathing_phase(
            session.id,
            BreathingPhase.INTAKE,
            phase_data={"action": "reading"},
        )
        assert cycle.id is not None
        assert cycle.phase == BreathingPhase.INTAKE
        assert cycle.completed_at is None
        assert cycle.success is None

    @pytest.mark.asyncio
    async def test_complete_breathing_phase(self, memory_service):
        """Complete a breathing phase"""
        session = await memory_service.start_session("hiroaki")
        cycle = await memory_service.start_breathing_phase(
            session.id, BreathingPhase.RESONANCE
        )
        completed = await memory_service.complete_breathing_phase(
            cycle.id, success=True, phase_data={"outcome": "aligned"}
        )
        assert completed.completed_at is not None
        assert completed.success is True
        assert completed.phase_data["outcome"] == "aligned"

    @pytest.mark.asyncio
    async def test_get_current_breathing_phase(self, memory_service):
        """Get current incomplete phase"""
        session = await memory_service.start_session("hiroaki")
        cycle1 = await memory_service.start_breathing_phase(
            session.id, BreathingPhase.INTAKE
        )
        await memory_service.complete_breathing_phase(cycle1.id, True)
        cycle2 = await memory_service.start_breathing_phase(
            session.id, BreathingPhase.RESONANCE
        )

        current = await memory_service.get_current_breathing_phase(session.id)
        assert current is not None
        assert current.id == cycle2.id
        assert current.phase == BreathingPhase.RESONANCE

    @pytest.mark.asyncio
    async def test_list_session_breathing_cycles(self, memory_service):
        """List all breathing cycles for a session"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.start_breathing_phase(session.id, BreathingPhase.INTAKE)
        await memory_service.start_breathing_phase(session.id, BreathingPhase.RESONANCE)
        cycles = await memory_service.list_session_breathing_cycles(session.id)
        assert len(cycles) == 2


class TestSnapshotManagement:
    """Tests for snapshot management (time axis preservation)"""

    @pytest.mark.asyncio
    async def test_create_snapshot(self, memory_service):
        """Create a temporal snapshot"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.record_intent(
            session.id, "Test", IntentType.FEATURE_REQUEST
        )
        snapshot = await memory_service.create_snapshot(
            session.id,
            SnapshotType.MILESTONE,
            description="Test milestone",
            tags=["test"],
        )
        assert snapshot.id is not None
        assert snapshot.snapshot_type == SnapshotType.MILESTONE
        assert snapshot.description == "Test milestone"
        assert "test" in snapshot.tags
        assert "session" in snapshot.snapshot_data
        assert "intents" in snapshot.snapshot_data

    @pytest.mark.asyncio
    async def test_restore_from_snapshot(self, memory_service):
        """Restore data from snapshot"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.record_intent(
            session.id, "Test intent", IntentType.EXPLORATION
        )
        snapshot = await memory_service.create_snapshot(
            session.id, SnapshotType.MANUAL
        )
        restored = await memory_service.restore_from_snapshot(snapshot.id)
        assert "session" in restored
        assert "intents" in restored
        assert len(restored["intents"]) == 1

    @pytest.mark.asyncio
    async def test_list_session_snapshots(self, memory_service):
        """List snapshots for a session"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.create_snapshot(
            session.id, SnapshotType.MANUAL, tags=["tag1"]
        )
        await memory_service.create_snapshot(
            session.id, SnapshotType.MILESTONE, tags=["tag2"]
        )
        snapshots = await memory_service.list_session_snapshots(session.id)
        assert len(snapshots) == 2

    @pytest.mark.asyncio
    async def test_list_snapshots_by_tags(self, memory_service):
        """List snapshots filtered by tags"""
        session = await memory_service.start_session("hiroaki")
        await memory_service.create_snapshot(
            session.id, SnapshotType.MANUAL, tags=["schema", "design"]
        )
        await memory_service.create_snapshot(
            session.id, SnapshotType.MILESTONE, tags=["api", "implementation"]
        )
        filtered = await memory_service.list_session_snapshots(
            session.id, tags=["schema"]
        )
        assert len(filtered) == 1
        assert "schema" in filtered[0].tags


class TestSessionContinuity:
    """Tests for session continuity (Resonance Expansion)"""

    @pytest.mark.asyncio
    async def test_continue_session(self, memory_service):
        """Continue a previous session"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Last intent", IntentType.EXPLORATION
        )
        await memory_service.save_agent_context(
            session.id, AgentType.KANA, {"focus": "testing"}
        )

        # Pause the session
        await memory_service.update_session_status(session.id, SessionStatus.PAUSED)

        # Continue
        data = await memory_service.continue_session(session.id)
        assert data["session"].status == SessionStatus.ACTIVE
        assert "kana" in data["agent_contexts"]
        assert data["last_intent"].id == intent.id

    @pytest.mark.asyncio
    async def test_continue_session_with_pending_choices(self, memory_service):
        """Continue session restores pending choices"""
        session = await memory_service.start_session("hiroaki")
        intent = await memory_service.record_intent(
            session.id, "Test", IntentType.FEATURE_REQUEST
        )
        await memory_service.create_choice_point(
            session.id,
            intent.id,
            "Pending question?",
            [
                Choice(id="a", description="A", implications={}),
                Choice(id="b", description="B", implications={}),
            ],
        )

        data = await memory_service.continue_session(session.id)
        assert len(data["pending_choices"]) == 1


class TestErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_raises_error(self, memory_service):
        """Get nonexistent session returns None"""
        result = await memory_service.get_session(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_complete_nonexistent_intent_raises_error(self, memory_service):
        """Complete nonexistent intent raises error"""
        with pytest.raises(ValueError, match="not found"):
            await memory_service.complete_intent(uuid4(), {})

    @pytest.mark.asyncio
    async def test_continue_nonexistent_session_raises_error(self, memory_service):
        """Continue nonexistent session raises error"""
        with pytest.raises(ValueError, match="not found"):
            await memory_service.continue_session(uuid4())
