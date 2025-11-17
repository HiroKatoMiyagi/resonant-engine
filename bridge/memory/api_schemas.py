"""
API Request/Response Schemas for Memory Management System

These schemas define the data contracts for the REST API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from bridge.memory.models import (
    AgentType,
    BreathingPhase,
    IntentStatus,
    IntentType,
    ResonanceState,
    SessionStatus,
    SnapshotType,
)


# ============================================================================
# Session Schemas
# ============================================================================


class CreateSessionRequest(BaseModel):
    """Request to create a new session"""
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response containing session information"""
    session_id: UUID
    user_id: str
    started_at: datetime
    last_active: datetime
    status: SessionStatus


class SessionSummaryResponse(BaseModel):
    """Response containing session summary"""
    session_id: UUID
    user_id: str
    started_at: datetime
    last_active: datetime
    status: SessionStatus
    summary: Dict[str, Any]


# ============================================================================
# Intent Schemas
# ============================================================================


class CreateIntentRequest(BaseModel):
    """Request to create a new intent"""
    session_id: UUID
    parent_intent_id: Optional[UUID] = None
    intent_text: str
    intent_type: IntentType
    priority: int = Field(default=0, ge=0, le=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentResponse(BaseModel):
    """Response containing intent information"""
    intent_id: UUID
    session_id: UUID
    parent_intent_id: Optional[UUID]
    intent_text: str
    intent_type: IntentType
    priority: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    status: IntentStatus
    outcome: Optional[Dict[str, Any]]


class CompleteIntentRequest(BaseModel):
    """Request to complete an intent"""
    outcome: Dict[str, Any]


class ListIntentsResponse(BaseModel):
    """Response containing list of intents"""
    intents: List[IntentResponse]
    total: int


class SearchIntentsRequest(BaseModel):
    """Request to search intents"""
    session_id: UUID
    query: str
    limit: int = 10


# ============================================================================
# Resonance Schemas
# ============================================================================


class CreateResonanceRequest(BaseModel):
    """Request to create a resonance record"""
    session_id: UUID
    intent_id: Optional[UUID] = None
    state: ResonanceState
    intensity: float = Field(ge=0.0, le=1.0)
    agents: List[str]
    pattern_type: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResonanceResponse(BaseModel):
    """Response containing resonance information"""
    resonance_id: UUID
    session_id: UUID
    intent_id: Optional[UUID]
    state: ResonanceState
    intensity: float
    agents: List[str]
    timestamp: datetime
    duration_ms: Optional[int]
    pattern_type: Optional[str]


class ListResonancesResponse(BaseModel):
    """Response containing list of resonances"""
    resonances: List[ResonanceResponse]
    total: int
    avg_intensity: float


# ============================================================================
# Agent Context Schemas
# ============================================================================


class SaveContextRequest(BaseModel):
    """Request to save agent context"""
    session_id: UUID
    intent_id: Optional[UUID] = None
    agent_type: AgentType
    context_data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextResponse(BaseModel):
    """Response containing agent context information"""
    context_id: UUID
    session_id: UUID
    intent_id: Optional[UUID]
    agent_type: AgentType
    version: int
    context_data: Dict[str, Any]
    created_at: datetime


class AllContextsResponse(BaseModel):
    """Response containing all agent contexts"""
    contexts: Dict[str, Dict[str, Any]]


# ============================================================================
# Choice Point Schemas
# ============================================================================


class ChoiceSchema(BaseModel):
    """Schema for a single choice"""
    id: str
    description: str
    implications: Dict[str, Any] = Field(default_factory=dict)


class CreateChoicePointRequest(BaseModel):
    """Request to create a choice point"""
    session_id: UUID
    intent_id: UUID
    question: str
    choices: List[ChoiceSchema]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChoicePointResponse(BaseModel):
    """Response containing choice point information"""
    choice_point_id: UUID
    session_id: UUID
    intent_id: UUID
    question: str
    choices: List[ChoiceSchema]
    selected_choice_id: Optional[str]
    created_at: datetime
    decided_at: Optional[datetime]
    decision_rationale: Optional[str]
    status: str = "pending"

    @property
    def computed_status(self) -> str:
        return "decided" if self.selected_choice_id else "pending"


class DecideChoiceRequest(BaseModel):
    """Request to decide on a choice point"""
    selected_choice_id: str
    decision_rationale: str


class ListChoicePointsResponse(BaseModel):
    """Response containing list of choice points"""
    choice_points: List[ChoicePointResponse]
    total: int


# ============================================================================
# Breathing Cycle Schemas
# ============================================================================


class StartCycleRequest(BaseModel):
    """Request to start a breathing cycle"""
    session_id: UUID
    intent_id: Optional[UUID] = None
    phase: BreathingPhase
    phase_data: Dict[str, Any] = Field(default_factory=dict)


class CompleteCycleRequest(BaseModel):
    """Request to complete a breathing cycle"""
    success: bool
    phase_data: Dict[str, Any] = Field(default_factory=dict)


class CycleResponse(BaseModel):
    """Response containing breathing cycle information"""
    cycle_id: UUID
    session_id: UUID
    intent_id: Optional[UUID]
    phase: BreathingPhase
    started_at: datetime
    completed_at: Optional[datetime]
    phase_data: Dict[str, Any]
    success: Optional[bool]


class ListCyclesResponse(BaseModel):
    """Response containing list of breathing cycles"""
    cycles: List[CycleResponse]
    total: int


# ============================================================================
# Snapshot Schemas
# ============================================================================


class CreateSnapshotRequest(BaseModel):
    """Request to create a snapshot"""
    session_id: UUID
    snapshot_type: SnapshotType
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SnapshotResponse(BaseModel):
    """Response containing snapshot information"""
    snapshot_id: UUID
    session_id: UUID
    snapshot_type: SnapshotType
    created_at: datetime
    description: Optional[str]
    tags: List[str]


class SnapshotDataResponse(BaseModel):
    """Response containing full snapshot data"""
    snapshot_id: UUID
    session_id: UUID
    snapshot_type: SnapshotType
    created_at: datetime
    description: Optional[str]
    tags: List[str]
    snapshot_data: Dict[str, Any]


class ListSnapshotsResponse(BaseModel):
    """Response containing list of snapshots"""
    snapshots: List[SnapshotResponse]
    total: int


# ============================================================================
# Query Schemas
# ============================================================================


class QueryRequest(BaseModel):
    """Request to query memory"""
    session_id: UUID
    query: Dict[str, Any]


class QueryResponse(BaseModel):
    """Response containing query results"""
    query_id: UUID
    results: List[Any]
    count: int
    execution_time_ms: int


# ============================================================================
# Session Continuity Schemas
# ============================================================================


class ContinueSessionResponse(BaseModel):
    """Response for session continuation"""
    session: SessionResponse
    agent_contexts: Dict[str, Dict[str, Any]]
    pending_choices: List[ChoicePointResponse]
    last_intent: Optional[IntentResponse]
    current_breathing_phase: Optional[CycleResponse]


# ============================================================================
# Health Check Schemas
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Response for health check"""
    status: str = "healthy"
    version: str = "1.0.0"
    service: str = "memory_management"
