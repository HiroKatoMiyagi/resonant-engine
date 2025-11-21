"""
REST API Router for Memory Management System

Provides 15+ endpoints for managing:
- Sessions
- Intents
- Resonances
- Agent Contexts
- Choice Points
- Breathing Cycles
- Snapshots
"""

import time
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from bridge.memory.api_schemas import (
    AllContextsResponse,
    CompleteCycleRequest,
    CompleteIntentRequest,
    ContextResponse,
    CreateChoicePointRequest,
    CreateIntentRequest,
    CreateResonanceRequest,
    CreateSessionRequest,
    CreateSnapshotRequest,
    CycleResponse,
    DecideChoiceRequest,
    HealthCheckResponse,
    IntentResponse,
    ListChoicePointsResponse,
    ListCyclesResponse,
    ListIntentsResponse,
    ListResonancesResponse,
    ListSnapshotsResponse,
    ChoicePointResponse,
    QueryRequest,
    QueryResponse,
    ResonanceResponse,
    SaveContextRequest,
    SessionResponse,
    SessionSummaryResponse,
    SnapshotDataResponse,
    SnapshotResponse,
    StartCycleRequest,
    ContinueSessionResponse,
    # Sprint 10 additions
    CreateChoicePointEnhancedRequest,
    DecideChoiceEnhancedRequest,
    ChoicePointEnhancedResponse,
    SearchChoicePointsResponse,
)
from bridge.memory.models import (
    AgentType,
    BreathingPhase,
    Choice,
    IntentStatus,
    ResonanceState,
    SessionStatus,
)
from bridge.memory.service import MemoryManagementService
from bridge.memory.in_memory_repositories import (
    InMemorySessionRepository,
    InMemoryIntentRepository,
    InMemoryResonanceRepository,
    InMemoryAgentContextRepository,
    InMemoryChoicePointRepository,
    InMemoryBreathingCycleRepository,
    InMemorySnapshotRepository,
)

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Global service instance (will be replaced with proper DI)
_service: Optional[MemoryManagementService] = None


def get_memory_service() -> MemoryManagementService:
    """Dependency to get the memory service"""
    global _service
    if _service is None:
        # Initialize with in-memory repositories for now
        _service = MemoryManagementService(
            session_repo=InMemorySessionRepository(),
            intent_repo=InMemoryIntentRepository(),
            resonance_repo=InMemoryResonanceRepository(),
            agent_context_repo=InMemoryAgentContextRepository(),
            choice_point_repo=InMemoryChoicePointRepository(),
            breathing_cycle_repo=InMemoryBreathingCycleRepository(),
            snapshot_repo=InMemorySnapshotRepository(),
        )
    return _service


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse()


# ============================================================================
# Session Endpoints
# ============================================================================


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Create a new session"""
    session = await service.start_session(request.user_id, request.metadata)
    return SessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        last_active=session.last_active,
        status=session.status,
    )


@router.get("/sessions/{session_id}", response_model=SessionSummaryResponse)
async def get_session(
    session_id: UUID,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Get session with summary"""
    summary_data = await service.get_session_summary(session_id)
    session = summary_data["session"]
    return SessionSummaryResponse(
        session_id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        last_active=session.last_active,
        status=session.status,
        summary={
            "total_intents": summary_data["total_intents"],
            "completed_intents": summary_data["completed_intents"],
            "resonance_events": summary_data["resonance_events"],
            "choice_points": summary_data["choice_points"],
            "breathing_cycles": summary_data["breathing_cycles"],
            "avg_intensity": summary_data["avg_intensity"],
        },
    )


@router.put("/sessions/{session_id}/heartbeat", response_model=SessionResponse)
async def update_heartbeat(
    session_id: UUID,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Update session heartbeat"""
    session = await service.update_session_heartbeat(session_id)
    return SessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        last_active=session.last_active,
        status=session.status,
    )


@router.post("/sessions/{session_id}/continue", response_model=ContinueSessionResponse)
async def continue_session(
    session_id: UUID,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Continue a previous session"""
    data = await service.continue_session(session_id)

    session = data["session"]
    session_resp = SessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        last_active=session.last_active,
        status=session.status,
    )

    pending_choices = []
    for cp in data["pending_choices"]:
        pending_choices.append(ChoicePointResponse(
            choice_point_id=cp.id,
            session_id=cp.session_id,
            intent_id=cp.intent_id,
            question=cp.question,
            choices=[{"id": c.id, "description": c.description, "implications": c.implications} for c in cp.choices],
            selected_choice_id=cp.selected_choice_id,
            created_at=cp.created_at,
            decided_at=cp.decided_at,
            decision_rationale=cp.decision_rationale,
        ))

    last_intent = None
    if data["last_intent"]:
        i = data["last_intent"]
        last_intent = IntentResponse(
            intent_id=i.id,
            session_id=i.session_id,
            parent_intent_id=i.parent_intent_id,
            intent_text=i.intent_text,
            intent_type=i.intent_type,
            priority=i.priority,
            created_at=i.created_at,
            updated_at=i.updated_at,
            completed_at=i.completed_at,
            status=i.status,
            outcome=i.outcome,
        )

    current_phase = None
    if data["current_breathing_phase"]:
        bc = data["current_breathing_phase"]
        current_phase = CycleResponse(
            cycle_id=bc.id,
            session_id=bc.session_id,
            intent_id=bc.intent_id,
            phase=bc.phase,
            started_at=bc.started_at,
            completed_at=bc.completed_at,
            phase_data=bc.phase_data,
            success=bc.success,
        )

    return ContinueSessionResponse(
        session=session_resp,
        agent_contexts=data["agent_contexts"],
        pending_choices=pending_choices,
        last_intent=last_intent,
        current_breathing_phase=current_phase,
    )


# ============================================================================
# Intent Endpoints
# ============================================================================


@router.post("/intents", response_model=IntentResponse)
async def create_intent(
    request: CreateIntentRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Create a new intent (Breathing Phase 1: Intake)"""
    intent = await service.record_intent(
        session_id=request.session_id,
        intent_text=request.intent_text,
        intent_type=request.intent_type,
        parent_intent_id=request.parent_intent_id,
        priority=request.priority,
        metadata=request.metadata,
    )
    return IntentResponse(
        intent_id=intent.id,
        session_id=intent.session_id,
        parent_intent_id=intent.parent_intent_id,
        intent_text=intent.intent_text,
        intent_type=intent.intent_type,
        priority=intent.priority,
        created_at=intent.created_at,
        updated_at=intent.updated_at,
        completed_at=intent.completed_at,
        status=intent.status,
        outcome=intent.outcome,
    )


@router.get("/intents", response_model=ListIntentsResponse)
async def list_intents(
    session_id: UUID = Query(...),
    status: Optional[IntentStatus] = Query(None),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """List intents for a session"""
    intents = await service.list_session_intents(session_id, status)
    return ListIntentsResponse(
        intents=[
            IntentResponse(
                intent_id=i.id,
                session_id=i.session_id,
                parent_intent_id=i.parent_intent_id,
                intent_text=i.intent_text,
                intent_type=i.intent_type,
                priority=i.priority,
                created_at=i.created_at,
                updated_at=i.updated_at,
                completed_at=i.completed_at,
                status=i.status,
                outcome=i.outcome,
            )
            for i in intents
        ],
        total=len(intents),
    )


@router.put("/intents/{intent_id}/complete", response_model=IntentResponse)
async def complete_intent(
    intent_id: UUID,
    request: CompleteIntentRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Complete an intent with outcome"""
    intent = await service.complete_intent(intent_id, request.outcome)
    return IntentResponse(
        intent_id=intent.id,
        session_id=intent.session_id,
        parent_intent_id=intent.parent_intent_id,
        intent_text=intent.intent_text,
        intent_type=intent.intent_type,
        priority=intent.priority,
        created_at=intent.created_at,
        updated_at=intent.updated_at,
        completed_at=intent.completed_at,
        status=intent.status,
        outcome=intent.outcome,
    )


# ============================================================================
# Resonance Endpoints
# ============================================================================


@router.post("/resonances", response_model=ResonanceResponse)
async def create_resonance(
    request: CreateResonanceRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Record a resonance state (Breathing Phase 2: Resonance)"""
    resonance = await service.record_resonance(
        session_id=request.session_id,
        state=request.state,
        intensity=request.intensity,
        agents=request.agents,
        intent_id=request.intent_id,
        pattern_type=request.pattern_type,
        duration_ms=request.duration_ms,
        metadata=request.metadata,
    )
    return ResonanceResponse(
        resonance_id=resonance.id,
        session_id=resonance.session_id,
        intent_id=resonance.intent_id,
        state=resonance.state,
        intensity=resonance.intensity,
        agents=resonance.agents,
        timestamp=resonance.timestamp,
        duration_ms=resonance.duration_ms,
        pattern_type=resonance.pattern_type,
    )


@router.get("/resonances", response_model=ListResonancesResponse)
async def list_resonances(
    session_id: UUID = Query(...),
    state: Optional[ResonanceState] = Query(None),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """List resonances for a session"""
    resonances = await service.list_session_resonances(session_id, state)
    stats = await service.get_resonance_statistics(session_id)
    return ListResonancesResponse(
        resonances=[
            ResonanceResponse(
                resonance_id=r.id,
                session_id=r.session_id,
                intent_id=r.intent_id,
                state=r.state,
                intensity=r.intensity,
                agents=r.agents,
                timestamp=r.timestamp,
                duration_ms=r.duration_ms,
                pattern_type=r.pattern_type,
            )
            for r in resonances
        ],
        total=len(resonances),
        avg_intensity=stats["avg_intensity"],
    )


# ============================================================================
# Agent Context Endpoints
# ============================================================================


@router.post("/contexts", response_model=ContextResponse)
async def save_context(
    request: SaveContextRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Save agent context (Breathing Phase 4: Re-reflection)"""
    context = await service.save_agent_context(
        session_id=request.session_id,
        agent_type=request.agent_type,
        context_data=request.context_data,
        intent_id=request.intent_id,
        metadata=request.metadata,
    )
    return ContextResponse(
        context_id=context.id,
        session_id=context.session_id,
        intent_id=context.intent_id,
        agent_type=context.agent_type,
        version=context.version,
        context_data=context.context_data,
        created_at=context.created_at,
    )


@router.get("/contexts/latest", response_model=ContextResponse)
async def get_latest_context(
    session_id: UUID = Query(...),
    agent_type: AgentType = Query(...),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Get latest context for an agent"""
    context = await service.get_latest_agent_context(session_id, agent_type)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return ContextResponse(
        context_id=context.id,
        session_id=context.session_id,
        intent_id=context.intent_id,
        agent_type=context.agent_type,
        version=context.version,
        context_data=context.context_data,
        created_at=context.created_at,
    )


@router.get("/contexts/all", response_model=AllContextsResponse)
async def get_all_contexts(
    session_id: UUID = Query(...),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Get all agent contexts for a session"""
    contexts = await service.get_all_agent_contexts(session_id)
    return AllContextsResponse(
        contexts={k: v.context_data for k, v in contexts.items()}
    )


# ============================================================================
# Choice Point Endpoints
# ============================================================================


@router.post("/choice-points", response_model=ChoicePointResponse)
async def create_choice_point(
    request: CreateChoicePointRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Create a choice point (Breathing Phase 3: Structuring)"""
    choices = [
        Choice(id=c.id, description=c.description, implications=c.implications)
        for c in request.choices
    ]
    cp = await service.create_choice_point(
        session_id=request.session_id,
        intent_id=request.intent_id,
        question=request.question,
        choices=choices,
        metadata=request.metadata,
    )
    return ChoicePointResponse(
        choice_point_id=cp.id,
        session_id=cp.session_id,
        intent_id=cp.intent_id,
        question=cp.question,
        choices=[{"id": c.id, "description": c.description, "implications": c.implications} for c in cp.choices],
        selected_choice_id=cp.selected_choice_id,
        created_at=cp.created_at,
        decided_at=cp.decided_at,
        decision_rationale=cp.decision_rationale,
    )


@router.put("/choice-points/{choice_point_id}/decide", response_model=ChoicePointResponse)
async def decide_choice(
    choice_point_id: UUID,
    request: DecideChoiceRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Decide on a choice point"""
    cp = await service.decide_choice(
        choice_point_id=choice_point_id,
        selected_choice_id=request.selected_choice_id,
        rationale=request.decision_rationale,
    )
    return ChoicePointResponse(
        choice_point_id=cp.id,
        session_id=cp.session_id,
        intent_id=cp.intent_id,
        question=cp.question,
        choices=[{"id": c.id, "description": c.description, "implications": c.implications} for c in cp.choices],
        selected_choice_id=cp.selected_choice_id,
        created_at=cp.created_at,
        decided_at=cp.decided_at,
        decision_rationale=cp.decision_rationale,
    )


@router.get("/choice-points/pending", response_model=ListChoicePointsResponse)
async def get_pending_choices(
    session_id: UUID = Query(...),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Get pending choice points for a session"""
    cps = await service.get_pending_choices(session_id)
    return ListChoicePointsResponse(
        choice_points=[
            ChoicePointResponse(
                choice_point_id=cp.id,
                session_id=cp.session_id,
                intent_id=cp.intent_id,
                question=cp.question,
                choices=[{"id": c.id, "description": c.description, "implications": c.implications} for c in cp.choices],
                selected_choice_id=cp.selected_choice_id,
                created_at=cp.created_at,
                decided_at=cp.decided_at,
                decision_rationale=cp.decision_rationale,
            )
            for cp in cps
        ],
        total=len(cps),
    )


# ============================================================================
# Sprint 10: Enhanced Choice Point Endpoints
# ============================================================================


@router.post("/choice-points/enhanced", response_model=ChoicePointEnhancedResponse)
async def create_choice_point_enhanced(
    request: CreateChoicePointEnhancedRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Create an enhanced choice point with Sprint 10 features"""
    from bridge.memory.api_schemas import CreateChoicePointEnhancedRequest, ChoicePointEnhancedResponse

    choices = [
        Choice(
            id=c.id,
            description=c.description,
            implications=c.implications,
            selected=c.selected,
            evaluation_score=c.evaluation_score,
            rejection_reason=c.rejection_reason,
            evaluated_at=c.evaluated_at
        )
        for c in request.choices
    ]

    cp = await service.create_choice_point_enhanced(
        user_id=request.user_id,
        session_id=request.session_id,
        intent_id=request.intent_id,
        question=request.question,
        choices=choices,
        tags=request.tags,
        context_type=request.context_type,
        metadata=request.metadata,
    )

    return ChoicePointEnhancedResponse(
        choice_point_id=cp.id,
        user_id=cp.user_id,
        session_id=cp.session_id,
        intent_id=cp.intent_id,
        question=cp.question,
        choices=[
            {
                "id": c.id,
                "description": c.description,
                "implications": c.implications,
                "selected": c.selected,
                "evaluation_score": c.evaluation_score,
                "rejection_reason": c.rejection_reason,
                "evaluated_at": c.evaluated_at
            }
            for c in cp.choices
        ],
        selected_choice_id=cp.selected_choice_id,
        tags=cp.tags,
        context_type=cp.context_type,
        created_at=cp.created_at,
        decided_at=cp.decided_at,
        decision_rationale=cp.decision_rationale,
    )


@router.put("/choice-points/{choice_point_id}/decide/enhanced", response_model=ChoicePointEnhancedResponse)
async def decide_choice_enhanced(
    choice_point_id: UUID,
    request: DecideChoiceEnhancedRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Decide on a choice point with rejection reasons (Sprint 10)"""
    from bridge.memory.api_schemas import DecideChoiceEnhancedRequest, ChoicePointEnhancedResponse

    cp = await service.decide_choice_enhanced(
        choice_point_id=choice_point_id,
        selected_choice_id=request.selected_choice_id,
        rationale=request.decision_rationale,
        rejection_reasons=request.rejection_reasons,
    )

    return ChoicePointEnhancedResponse(
        choice_point_id=cp.id,
        user_id=cp.user_id,
        session_id=cp.session_id,
        intent_id=cp.intent_id,
        question=cp.question,
        choices=[
            {
                "id": c.id,
                "description": c.description,
                "implications": c.implications,
                "selected": c.selected,
                "evaluation_score": c.evaluation_score,
                "rejection_reason": c.rejection_reason,
                "evaluated_at": c.evaluated_at
            }
            for c in cp.choices
        ],
        selected_choice_id=cp.selected_choice_id,
        tags=cp.tags,
        context_type=cp.context_type,
        created_at=cp.created_at,
        decided_at=cp.decided_at,
        decision_rationale=cp.decision_rationale,
    )


@router.get("/choice-points/search", response_model=SearchChoicePointsResponse)
async def search_choice_points(
    user_id: str = Query(...),
    tags: Optional[str] = Query(None),  # Comma-separated tags
    from_date: Optional[str] = Query(None),  # ISO8601 format
    to_date: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Search choice points by tags, time range, or full-text (Sprint 10)

    Query Parameters:
    - user_id: User ID (required)
    - tags: Comma-separated tags (e.g., "database,technology")
    - from_date: Start date (ISO8601, e.g., "2025-08-01T00:00:00Z")
    - to_date: End date (ISO8601)
    - search_text: Full-text search on question field
    - limit: Maximum results (default 10, max 100)
    """
    from datetime import datetime
    from bridge.memory.api_schemas import SearchChoicePointsResponse, ChoicePointEnhancedResponse

    # TODO: Implement search using ChoiceQueryEngine once integrated
    # For now, return empty results
    return SearchChoicePointsResponse(
        results=[],
        count=0,
        query={
            "user_id": user_id,
            "tags": tags.split(",") if tags else None,
            "from_date": from_date,
            "to_date": to_date,
            "search_text": search_text,
            "limit": limit
        }
    )


# ============================================================================
# Breathing Cycle Endpoints
# ============================================================================


@router.post("/breathing-cycles", response_model=CycleResponse)
async def start_breathing_cycle(
    request: StartCycleRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Start a new breathing cycle"""
    cycle = await service.start_breathing_phase(
        session_id=request.session_id,
        phase=request.phase,
        intent_id=request.intent_id,
        phase_data=request.phase_data,
    )
    return CycleResponse(
        cycle_id=cycle.id,
        session_id=cycle.session_id,
        intent_id=cycle.intent_id,
        phase=cycle.phase,
        started_at=cycle.started_at,
        completed_at=cycle.completed_at,
        phase_data=cycle.phase_data,
        success=cycle.success,
    )


@router.put("/breathing-cycles/{cycle_id}/complete", response_model=CycleResponse)
async def complete_breathing_cycle(
    cycle_id: UUID,
    request: CompleteCycleRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Complete a breathing cycle"""
    cycle = await service.complete_breathing_phase(
        cycle_id=cycle_id,
        success=request.success,
        phase_data=request.phase_data,
    )
    return CycleResponse(
        cycle_id=cycle.id,
        session_id=cycle.session_id,
        intent_id=cycle.intent_id,
        phase=cycle.phase,
        started_at=cycle.started_at,
        completed_at=cycle.completed_at,
        phase_data=cycle.phase_data,
        success=cycle.success,
    )


@router.get("/breathing-cycles", response_model=ListCyclesResponse)
async def list_breathing_cycles(
    session_id: UUID = Query(...),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """List breathing cycles for a session"""
    cycles = await service.list_session_breathing_cycles(session_id)
    return ListCyclesResponse(
        cycles=[
            CycleResponse(
                cycle_id=c.id,
                session_id=c.session_id,
                intent_id=c.intent_id,
                phase=c.phase,
                started_at=c.started_at,
                completed_at=c.completed_at,
                phase_data=c.phase_data,
                success=c.success,
            )
            for c in cycles
        ],
        total=len(cycles),
    )


# ============================================================================
# Snapshot Endpoints
# ============================================================================


@router.post("/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Create a temporal snapshot"""
    snapshot = await service.create_snapshot(
        session_id=request.session_id,
        snapshot_type=request.snapshot_type,
        description=request.description,
        tags=request.tags,
    )
    return SnapshotResponse(
        snapshot_id=snapshot.id,
        session_id=snapshot.session_id,
        snapshot_type=snapshot.snapshot_type,
        created_at=snapshot.created_at,
        description=snapshot.description,
        tags=snapshot.tags,
    )


@router.get("/snapshots", response_model=ListSnapshotsResponse)
async def list_snapshots(
    session_id: UUID = Query(...),
    tags: Optional[List[str]] = Query(None),
    service: MemoryManagementService = Depends(get_memory_service)
):
    """List snapshots for a session"""
    snapshots = await service.list_session_snapshots(session_id, tags)
    return ListSnapshotsResponse(
        snapshots=[
            SnapshotResponse(
                snapshot_id=s.id,
                session_id=s.session_id,
                snapshot_type=s.snapshot_type,
                created_at=s.created_at,
                description=s.description,
                tags=s.tags,
            )
            for s in snapshots
        ],
        total=len(snapshots),
    )


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotDataResponse)
async def get_snapshot(
    snapshot_id: UUID,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Get snapshot with full data"""
    data = await service.restore_from_snapshot(snapshot_id)
    # We need to get the snapshot metadata too
    snapshot_repo = service.snapshot_repo
    snapshot = await snapshot_repo.get_by_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return SnapshotDataResponse(
        snapshot_id=snapshot.id,
        session_id=snapshot.session_id,
        snapshot_type=snapshot.snapshot_type,
        created_at=snapshot.created_at,
        description=snapshot.description,
        tags=snapshot.tags,
        snapshot_data=data,
    )


# ============================================================================
# Query Endpoint
# ============================================================================


@router.post("/query", response_model=QueryResponse)
async def query_memory(
    request: QueryRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    """Query memory with custom filters"""
    start_time = time.time()
    query_id = uuid4()

    results = []
    query_type = request.query.get("type", "intents")

    if query_type == "intents":
        status = request.query.get("status")
        if status:
            status = IntentStatus(status)
        results = await service.list_session_intents(request.session_id, status)
        results = [i.model_dump(mode="json") for i in results]
    elif query_type == "resonances":
        state = request.query.get("state")
        if state:
            state = ResonanceState(state)
            results = await service.list_session_resonances(request.session_id, state)
        else:
            results = await service.list_session_resonances(request.session_id)
        results = [r.model_dump(mode="json") for r in results]
    elif query_type == "choice_points":
        results = await service.list_session_choices(request.session_id)
        results = [cp.model_dump(mode="json") for cp in results]

    execution_time_ms = int((time.time() - start_time) * 1000)

    return QueryResponse(
        query_id=query_id,
        results=results,
        count=len(results),
        execution_time_ms=execution_time_ms,
    )
