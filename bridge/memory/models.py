"""
Memory Management System - Data Models

These models represent the core data structures for persisting the
breathing history and resonance patterns of the Resonant Engine.

Philosophy:
- Memory is "breath history + resonance traces"
- Time axis must be preserved
- Choices are kept, not forced
- Structure continuity is maintained
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Session Models
# ============================================================================


class SessionStatus(str, Enum):
    """Session lifecycle status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Session(BaseModel):
    """
    User session management - represents a breathing unit.

    A session encapsulates a period of interaction where intents are processed,
    resonance occurs, and choices are made.
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Intent Models
# ============================================================================


class IntentStatus(str, Enum):
    """Intent processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class IntentType(str, Enum):
    """Types of intentions that can be recorded"""
    FEATURE_REQUEST = "feature_request"
    BUG_FIX = "bug_fix"
    EXPLORATION = "exploration"
    CLARIFICATION = "clarification"
    OPTIMIZATION = "optimization"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


class Intent(BaseModel):
    """
    Intent persistence - records the breathing phase 1 "Intake".

    Represents a user's intention, which may be hierarchical (parent-child).
    The outcome field stores the result of completed intents.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    parent_intent_id: Optional[UUID] = None

    intent_text: str
    intent_type: IntentType
    priority: int = Field(default=0, ge=0, le=10)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    status: IntentStatus = IntentStatus.PENDING
    outcome: Optional[Dict[str, Any]] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if not 0 <= v <= 10:
            raise ValueError("Priority must be between 0 and 10")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Resonance Models
# ============================================================================


class ResonanceState(str, Enum):
    """State of resonance between agents"""
    ALIGNED = "aligned"
    CONFLICTED = "conflicted"
    CONVERGING = "converging"
    EXPLORING = "exploring"
    DIVERGING = "diverging"


class Resonance(BaseModel):
    """
    Resonance state recording - breathing phase 2 "Resonance".

    Records the pattern of resonance between Yuno/Kana/Tsumu agents,
    including intensity and the type of pattern observed.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: Optional[UUID] = None

    state: ResonanceState
    intensity: float = Field(ge=0.0, le=1.0)
    agents: List[str]  # ["yuno", "kana", "tsumu"]

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = None

    pattern_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Intensity must be between 0.0 and 1.0")
        return v

    @field_validator("agents")
    @classmethod
    def validate_agents(cls, v: List[str]) -> List[str]:
        valid_agents = {"yuno", "kana", "tsumu"}
        for agent in v:
            if agent.lower() not in valid_agents:
                raise ValueError(f"Invalid agent: {agent}. Must be one of {valid_agents}")
        return [a.lower() for a in v]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Agent Context Models
# ============================================================================


class AgentType(str, Enum):
    """Types of AI agents in the 3-layer structure"""
    YUNO = "yuno"      # Philosophical thinking core
    KANA = "kana"      # External translation layer
    TSUMU = "tsumu"    # Implementation weaver


class AgentContext(BaseModel):
    """
    Agent context preservation - breathing phase 4 "Re-reflection".

    Each agent (Yuno/Kana/Tsumu) maintains its own context that evolves
    over time. Versioning allows tracking of context changes.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: Optional[UUID] = None

    agent_type: AgentType
    context_data: Dict[str, Any]
    version: int = 1

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    superseded_by: Optional[UUID] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Version must be at least 1")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Choice Point Models
# ============================================================================


class Choice(BaseModel):
    """A single choice option with its implications"""
    id: str
    description: str
    implications: Dict[str, Any] = Field(default_factory=dict)


class ChoicePoint(BaseModel):
    """
    Choice point management - breathing phase 3 "Structuring".

    Records decision points where choices are preserved, not forced.
    Selected choice can be NULL to indicate a pending decision.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: UUID

    question: str
    choices: List[Choice]
    selected_choice_id: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None

    decision_rationale: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("choices")
    @classmethod
    def validate_choices(cls, v: List[Choice]) -> List[Choice]:
        if len(v) < 2:
            raise ValueError("Must have at least 2 choices")
        choice_ids = [c.id for c in v]
        if len(choice_ids) != len(set(choice_ids)):
            raise ValueError("Choice IDs must be unique")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Breathing Cycle Models
# ============================================================================


class BreathingPhase(str, Enum):
    """The 6 phases of a breathing cycle"""
    INTAKE = "intake"                        # 1. 吸う
    RESONANCE = "resonance"                  # 2. 共鳴
    STRUCTURING = "structuring"              # 3. 構造化
    RE_REFLECTION = "re_reflection"          # 4. 再内省
    IMPLEMENTATION = "implementation"        # 5. 実装
    RESONANCE_EXPANSION = "resonance_expansion"  # 6. 共鳴拡大


class BreathingCycle(BaseModel):
    """
    Breathing cycle state management - tracks the 6 phases.

    Each cycle represents one complete breath of the system,
    recording the phase data and success/failure of the phase.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: Optional[UUID] = None

    phase: BreathingPhase
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    phase_data: Dict[str, Any] = Field(default_factory=dict)
    success: Optional[bool] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Snapshot Models
# ============================================================================


class SnapshotType(str, Enum):
    """Types of snapshots that can be created"""
    MANUAL = "manual"
    AUTO_HOURLY = "auto_hourly"
    PRE_MAJOR_CHANGE = "pre_major_change"
    CRISIS_POINT = "crisis_point"
    MILESTONE = "milestone"


class Snapshot(BaseModel):
    """
    Temporal snapshots - breathing phase 5 "Implementation".

    Preserves the complete state at a point in time, allowing
    restoration to previous states and maintaining the time axis.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID

    snapshot_type: SnapshotType
    snapshot_data: Dict[str, Any]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None

    tags: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


# ============================================================================
# Memory Query Models
# ============================================================================


class MemoryQuery(BaseModel):
    """
    Memory query logging for pattern analysis.

    Records search queries to understand access patterns and
    optimize future searches.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: Optional[UUID] = None

    query_text: str
    query_params: Optional[Dict[str, Any]] = None

    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_ms: Optional[int] = None

    results_count: Optional[int] = None
    results_sample: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
