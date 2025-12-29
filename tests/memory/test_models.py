"""
Unit tests for Memory Management System data models.

Tests validation, serialization, and basic model functionality.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID
from pydantic import ValidationError

from app.services.memory.models import (
    Session,
    SessionStatus,
    Intent,
    IntentStatus,
    IntentType,
    Resonance,
    ResonanceState,
    AgentContext,
    AgentType,
    ChoicePoint,
    Choice,
    BreathingCycle,
    BreathingPhase,
    Snapshot,
    SnapshotType,
)


class TestSessionModel:
    """Tests for Session model"""

    def test_session_creation_with_defaults(self):
        """Session creation with default values"""
        session = Session(user_id="hiroaki")
        assert session.id is not None
        assert isinstance(session.id, UUID)
        assert session.user_id == "hiroaki"
        assert session.status == SessionStatus.ACTIVE
        assert session.started_at is not None
        assert session.last_active is not None
        assert session.metadata == {}

    def test_session_creation_with_metadata(self):
        """Session creation with metadata"""
        metadata = {"client": "web", "version": "1.0.0"}
        session = Session(user_id="hiroaki", metadata=metadata)
        assert session.metadata == metadata

    def test_session_status_enum_values(self):
        """Session status enum validation"""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.PAUSED.value == "paused"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.ARCHIVED.value == "archived"

    def test_session_json_serialization(self):
        """Session JSON serialization"""
        session = Session(user_id="hiroaki")
        json_data = session.model_dump(mode="json")
        assert "id" in json_data
        assert "user_id" in json_data
        assert json_data["user_id"] == "hiroaki"
        assert json_data["status"] == "active"


class TestIntentModel:
    """Tests for Intent model"""

    def test_intent_creation(self):
        """Intent creation with required fields"""
        session_id = uuid4()
        intent = Intent(
            session_id=session_id,
            intent_text="Design memory system",
            intent_type=IntentType.FEATURE_REQUEST,
        )
        assert intent.id is not None
        assert intent.session_id == session_id
        assert intent.status == IntentStatus.PENDING
        assert intent.priority == 0
        assert intent.parent_intent_id is None
        assert intent.completed_at is None

    def test_intent_hierarchy(self):
        """Hierarchical intent structure"""
        session_id = uuid4()
        parent = Intent(
            session_id=session_id,
            intent_text="Parent intent",
            intent_type=IntentType.FEATURE_REQUEST,
        )
        child = Intent(
            session_id=session_id,
            parent_intent_id=parent.id,
            intent_text="Child intent",
            intent_type=IntentType.FEATURE_REQUEST,
        )
        assert child.parent_intent_id == parent.id

    def test_intent_priority_validation_valid(self):
        """Priority validation - valid range"""
        for priority in [0, 5, 10]:
            intent = Intent(
                session_id=uuid4(),
                intent_text="Test",
                intent_type=IntentType.EXPLORATION,
                priority=priority,
            )
            assert intent.priority == priority

    def test_intent_priority_validation_invalid(self):
        """Priority validation - invalid values"""
        with pytest.raises(ValidationError):
            Intent(
                session_id=uuid4(),
                intent_text="Test",
                intent_type=IntentType.EXPLORATION,
                priority=11,
            )

        with pytest.raises(ValidationError):
            Intent(
                session_id=uuid4(),
                intent_text="Test",
                intent_type=IntentType.EXPLORATION,
                priority=-1,
            )

    def test_intent_status_enum(self):
        """Intent status enum values"""
        assert IntentStatus.PENDING.value == "pending"
        assert IntentStatus.IN_PROGRESS.value == "in_progress"
        assert IntentStatus.COMPLETED.value == "completed"
        assert IntentStatus.CANCELLED.value == "cancelled"
        assert IntentStatus.DEFERRED.value == "deferred"

    def test_intent_type_enum(self):
        """Intent type enum values"""
        assert IntentType.FEATURE_REQUEST.value == "feature_request"
        assert IntentType.BUG_FIX.value == "bug_fix"
        assert IntentType.EXPLORATION.value == "exploration"
        assert IntentType.OPTIMIZATION.value == "optimization"


class TestResonanceModel:
    """Tests for Resonance model"""

    def test_resonance_creation(self):
        """Resonance creation with valid data"""
        resonance = Resonance(
            session_id=uuid4(),
            state=ResonanceState.ALIGNED,
            intensity=0.85,
            agents=["yuno", "kana"],
        )
        assert resonance.id is not None
        assert resonance.state == ResonanceState.ALIGNED
        assert resonance.intensity == 0.85
        assert resonance.agents == ["yuno", "kana"]

    def test_resonance_intensity_validation_valid(self):
        """Intensity validation - valid range"""
        for intensity in [0.0, 0.5, 1.0]:
            resonance = Resonance(
                session_id=uuid4(),
                state=ResonanceState.EXPLORING,
                intensity=intensity,
                agents=["kana"],
            )
            assert resonance.intensity == intensity

    def test_resonance_intensity_validation_invalid(self):
        """Intensity validation - invalid values"""
        with pytest.raises(ValidationError):
            Resonance(
                session_id=uuid4(),
                state=ResonanceState.ALIGNED,
                intensity=1.5,
                agents=["yuno"],
            )

        with pytest.raises(ValidationError):
            Resonance(
                session_id=uuid4(),
                state=ResonanceState.ALIGNED,
                intensity=-0.1,
                agents=["yuno"],
            )

    def test_resonance_agents_validation(self):
        """Agents validation - normalized to lowercase"""
        resonance = Resonance(
            session_id=uuid4(),
            state=ResonanceState.CONVERGING,
            intensity=0.7,
            agents=["YUNO", "KANA", "TSUMU"],
        )
        assert resonance.agents == ["yuno", "kana", "tsumu"]

    def test_resonance_state_enum(self):
        """Resonance state enum values"""
        assert ResonanceState.ALIGNED.value == "aligned"
        assert ResonanceState.CONFLICTED.value == "conflicted"
        assert ResonanceState.CONVERGING.value == "converging"
        assert ResonanceState.EXPLORING.value == "exploring"
        assert ResonanceState.DIVERGING.value == "diverging"


class TestAgentContextModel:
    """Tests for AgentContext model"""

    def test_agent_context_creation(self):
        """AgentContext creation"""
        context = AgentContext(
            session_id=uuid4(),
            agent_type=AgentType.KANA,
            context_data={"focus": "memory design"},
        )
        assert context.id is not None
        assert context.agent_type == AgentType.KANA
        assert context.version == 1
        assert context.context_data == {"focus": "memory design"}
        assert context.superseded_by is None

    def test_agent_context_versioning(self):
        """AgentContext versioning"""
        session_id = uuid4()
        v1 = AgentContext(
            session_id=session_id,
            agent_type=AgentType.KANA,
            context_data={"version": 1},
            version=1,
        )
        v2 = AgentContext(
            session_id=session_id,
            agent_type=AgentType.KANA,
            context_data={"version": 2},
            version=2,
        )
        v1.superseded_by = v2.id
        assert v2.version == v1.version + 1
        assert v1.superseded_by == v2.id

    def test_agent_type_enum(self):
        """Agent type enum values"""
        assert AgentType.YUNO.value == "yuno"
        assert AgentType.KANA.value == "kana"
        assert AgentType.TSUMU.value == "tsumu"

    def test_agent_context_version_validation(self):
        """Version must be at least 1"""
        with pytest.raises(ValidationError):
            AgentContext(
                session_id=uuid4(),
                agent_type=AgentType.TSUMU,
                context_data={},
                version=0,
            )


class TestChoicePointModel:
    """Tests for ChoicePoint model"""

    def test_choice_point_creation(self):
        """ChoicePoint creation with pending state"""
        cp = ChoicePoint(
            session_id=uuid4(),
            user_id="test_user",
            intent_id=uuid4(),
            question="PostgreSQL vs SQLite?",
            choices=[
                Choice(id="pg", description="PostgreSQL", implications={}),
                Choice(id="sqlite", description="SQLite", implications={}),
            ],
        )
        assert cp.id is not None
        assert cp.question == "PostgreSQL vs SQLite?"
        assert len(cp.choices) == 2
        assert cp.selected_choice_id is None  # Pending decision
        assert cp.decided_at is None
        assert cp.decision_rationale is None

    def test_choice_point_with_decision(self):
        """ChoicePoint with decision made"""
        cp = ChoicePoint(
            session_id=uuid4(),
            user_id="test_user",
            intent_id=uuid4(),
            question="Test question?",
            choices=[
                Choice(id="a", description="Option A", implications={"pros": ["fast"]}),
                Choice(id="b", description="Option B", implications={"pros": ["simple"]}),
            ],
            selected_choice_id="a",
            decided_at=datetime.now(timezone.utc),
            decision_rationale="Option A is faster",
        )
        assert cp.selected_choice_id == "a"
        assert cp.decided_at is not None
        assert cp.decision_rationale == "Option A is faster"

    def test_choice_point_requires_at_least_two_choices(self):
        """ChoicePoint must have at least 2 choices"""
        with pytest.raises(ValidationError):
            ChoicePoint(
                session_id=uuid4(),
                user_id="test_user",
                intent_id=uuid4(),
                question="Only one choice?",
                choices=[Choice(id="only", description="Only option", implications={})],
            )

    def test_choice_point_unique_choice_ids(self):
        """Choice IDs must be unique"""
        with pytest.raises(ValidationError):
            ChoicePoint(
                session_id=uuid4(),
                user_id="test_user",
                intent_id=uuid4(),
                question="Duplicate IDs?",
                choices=[
                    Choice(id="same", description="First", implications={}),
                    Choice(id="same", description="Second", implications={}),
                ],
            )


class TestBreathingCycleModel:
    """Tests for BreathingCycle model"""

    def test_breathing_cycle_creation(self):
        """BreathingCycle creation"""
        cycle = BreathingCycle(
            session_id=uuid4(),
            phase=BreathingPhase.INTAKE,
        )
        assert cycle.id is not None
        assert cycle.phase == BreathingPhase.INTAKE
        assert cycle.completed_at is None
        assert cycle.success is None
        assert cycle.phase_data == {}

    def test_breathing_cycle_with_data(self):
        """BreathingCycle with phase data"""
        cycle = BreathingCycle(
            session_id=uuid4(),
            phase=BreathingPhase.STRUCTURING,
            phase_data={"structures": ["schema", "api"]},
        )
        assert cycle.phase_data == {"structures": ["schema", "api"]}

    def test_breathing_phase_enum(self):
        """Breathing phase enum values"""
        assert BreathingPhase.INTAKE.value == "intake"
        assert BreathingPhase.RESONANCE.value == "resonance"
        assert BreathingPhase.STRUCTURING.value == "structuring"
        assert BreathingPhase.RE_REFLECTION.value == "re_reflection"
        assert BreathingPhase.IMPLEMENTATION.value == "implementation"
        assert BreathingPhase.RESONANCE_EXPANSION.value == "resonance_expansion"

    def test_breathing_cycle_completion(self):
        """BreathingCycle completion state"""
        cycle = BreathingCycle(
            session_id=uuid4(),
            phase=BreathingPhase.IMPLEMENTATION,
            completed_at=datetime.now(timezone.utc),
            success=True,
        )
        assert cycle.completed_at is not None
        assert cycle.success is True


class TestSnapshotModel:
    """Tests for Snapshot model"""

    def test_snapshot_creation(self):
        """Snapshot creation"""
        snapshot = Snapshot(
            session_id=uuid4(),
            snapshot_type=SnapshotType.MILESTONE,
            snapshot_data={"state": "test"},
        )
        assert snapshot.id is not None
        assert snapshot.snapshot_type == SnapshotType.MILESTONE
        assert snapshot.snapshot_data == {"state": "test"}
        assert snapshot.tags == []
        assert snapshot.description is None

    def test_snapshot_with_tags(self):
        """Snapshot with tags"""
        snapshot = Snapshot(
            session_id=uuid4(),
            snapshot_type=SnapshotType.MANUAL,
            snapshot_data={},
            tags=["schema", "milestone"],
            description="Schema complete",
        )
        assert snapshot.tags == ["schema", "milestone"]
        assert snapshot.description == "Schema complete"

    def test_snapshot_type_enum(self):
        """Snapshot type enum values"""
        assert SnapshotType.MANUAL.value == "manual"
        assert SnapshotType.AUTO_HOURLY.value == "auto_hourly"
        assert SnapshotType.PRE_MAJOR_CHANGE.value == "pre_major_change"
        assert SnapshotType.CRISIS_POINT.value == "crisis_point"
        assert SnapshotType.MILESTONE.value == "milestone"

    def test_snapshot_json_serialization(self):
        """Snapshot JSON serialization"""
        snapshot = Snapshot(
            session_id=uuid4(),
            snapshot_type=SnapshotType.MILESTONE,
            snapshot_data={"key": "value"},
            tags=["test"],
        )
        json_data = snapshot.model_dump(mode="json")
        assert "id" in json_data
        assert "snapshot_type" in json_data
        assert json_data["tags"] == ["test"]


class TestUUIDGeneration:
    """Tests for UUID generation"""

    def test_all_models_generate_unique_uuids(self):
        """All models generate unique UUIDs"""
        ids = set()

        session = Session(user_id="test")
        ids.add(session.id)

        intent = Intent(
            session_id=uuid4(),
            intent_text="test",
            intent_type=IntentType.EXPLORATION,
        )
        ids.add(intent.id)

        resonance = Resonance(
            session_id=uuid4(),
            state=ResonanceState.ALIGNED,
            intensity=0.5,
            agents=["kana"],
        )
        ids.add(resonance.id)

        context = AgentContext(
            session_id=uuid4(),
            agent_type=AgentType.YUNO,
            context_data={},
        )
        ids.add(context.id)

        # All IDs should be unique
        assert len(ids) == 4


class TestDatetimeHandling:
    """Tests for datetime handling"""

    def test_datetime_defaults_are_timezone_aware(self):
        """Datetimes should be timezone-aware"""
        session = Session(user_id="test")
        assert session.started_at.tzinfo is not None
        assert session.last_active.tzinfo is not None

        intent = Intent(
            session_id=uuid4(),
            intent_text="test",
            intent_type=IntentType.BUG_FIX,
        )
        assert intent.created_at.tzinfo is not None
        assert intent.updated_at.tzinfo is not None

    def test_datetime_serialization(self):
        """Datetimes serialize to ISO format"""
        session = Session(user_id="test")
        json_data = session.model_dump(mode="json")
        # Should be ISO format string
        assert isinstance(json_data["started_at"], str)
        assert "T" in json_data["started_at"]
