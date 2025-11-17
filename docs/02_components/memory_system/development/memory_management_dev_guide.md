# Memory Management System - Developer Guide

**Version**: 1.0.0
**Created**: 2025-11-17
**Author**: Sonnet 4.5 (Claude Code Implementation)

## Overview

This guide provides technical details for developers working with the Memory Management System. It covers architecture, implementation patterns, and extension guidelines.

## Architecture

### System Layers

```
┌─────────────────────────────────────┐
│          REST API Layer             │
│  (FastAPI Router + Schemas)         │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│          Service Layer              │
│  (MemoryManagementService)          │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         Repository Layer            │
│  (Abstract + Implementations)       │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│          Data Layer                 │
│  (Pydantic Models + SQLAlchemy)     │
└─────────────────────────────────────┘
```

## File Structure

```
bridge/memory/
├── __init__.py                    # Package exports
├── models.py                      # Pydantic data models
├── database.py                    # SQLAlchemy ORM models
├── repositories.py                # Abstract repository interfaces
├── in_memory_repositories.py      # In-memory implementations
├── service.py                     # Business logic service
├── api_schemas.py                 # API request/response schemas
└── api_router.py                  # FastAPI endpoints

tests/memory/
├── __init__.py
├── test_models.py                 # Model unit tests
└── test_service.py                # Service unit tests
```

## Data Models

### Core Models

All models inherit from Pydantic BaseModel and provide:
- UUID generation
- Timezone-aware timestamps
- JSON serialization
- Field validation

Example:
```python
from bridge.memory.models import Intent, IntentType

intent = Intent(
    session_id=session_id,
    intent_text="Design memory system",
    intent_type=IntentType.FEATURE_REQUEST,
    priority=8,
)
```

### Model Hierarchy

- **Session**: Breathing unit container
  - **Intent**: User intentions (hierarchical)
    - **ChoicePoint**: Decision points
    - **Resonance**: State recordings
    - **BreathingCycle**: Phase tracking
  - **AgentContext**: Per-agent state (versioned)
  - **Snapshot**: Temporal preservation

## Repository Pattern

### Abstract Interfaces

```python
from bridge.memory.repositories import IntentRepository

class CustomIntentRepository(IntentRepository):
    async def create(self, intent: Intent) -> Intent:
        # Implementation
        pass

    async def get_by_id(self, intent_id: UUID) -> Optional[Intent]:
        # Implementation
        pass
```

### Available Repositories

1. **SessionRepository** - Session lifecycle
2. **IntentRepository** - Intent CRUD + search
3. **ResonanceRepository** - Resonance patterns
4. **AgentContextRepository** - Versioned contexts
5. **ChoicePointRepository** - Decision management
6. **BreathingCycleRepository** - Phase tracking
7. **SnapshotRepository** - Temporal preservation

### In-Memory Implementation

For testing and development:
```python
from bridge.memory.in_memory_repositories import (
    InMemorySessionRepository,
    InMemoryIntentRepository,
)

repo = InMemorySessionRepository()
session = await repo.create(Session(user_id="test"))
```

## Service Layer

### MemoryManagementService

Central service coordinating all repositories:

```python
from bridge.memory.service import MemoryManagementService
from bridge.memory.in_memory_repositories import *

service = MemoryManagementService(
    session_repo=InMemorySessionRepository(),
    intent_repo=InMemoryIntentRepository(),
    resonance_repo=InMemoryResonanceRepository(),
    agent_context_repo=InMemoryAgentContextRepository(),
    choice_point_repo=InMemoryChoicePointRepository(),
    breathing_cycle_repo=InMemoryBreathingCycleRepository(),
    snapshot_repo=InMemorySnapshotRepository(),
)
```

### Key Operations

#### Session Management
```python
# Start session
session = await service.start_session("user_id", {"client": "web"})

# Update heartbeat
await service.update_session_heartbeat(session.id)

# Continue previous session
data = await service.continue_session(session.id)
```

#### Intent Lifecycle
```python
# Record intent (Breathing Phase 1)
intent = await service.record_intent(
    session.id,
    "Design schema",
    IntentType.FEATURE_REQUEST,
    priority=8
)

# Update status
await service.update_intent_status(intent.id, IntentStatus.IN_PROGRESS)

# Complete with outcome
await service.complete_intent(intent.id, {"result": "success"})
```

#### Resonance Recording
```python
# Record resonance (Breathing Phase 2)
resonance = await service.record_resonance(
    session.id,
    ResonanceState.ALIGNED,
    intensity=0.85,
    agents=["yuno", "kana"],
    pattern_type="philosophical_alignment"
)
```

#### Choice Management
```python
# Create choice point (Breathing Phase 3)
choice_point = await service.create_choice_point(
    session.id,
    intent.id,
    "PostgreSQL vs SQLite?",
    [
        Choice(id="pg", description="PostgreSQL", implications={}),
        Choice(id="sqlite", description="SQLite", implications={}),
    ]
)

# Decide
await service.decide_choice(choice_point.id, "pg", "Better scalability")

# Get pending decisions
pending = await service.get_pending_choices(session.id)
```

#### Agent Context Versioning
```python
# Save context (Breathing Phase 4)
context = await service.save_agent_context(
    session.id,
    AgentType.KANA,
    {"focus": "memory design", "version": 1}
)

# Get latest
latest = await service.get_latest_agent_context(session.id, AgentType.KANA)

# Get all agents
all_contexts = await service.get_all_agent_contexts(session.id)
```

#### Breathing Cycles
```python
# Start phase
cycle = await service.start_breathing_phase(
    session.id,
    BreathingPhase.STRUCTURING,
    phase_data={"action": "schema_design"}
)

# Complete phase
await service.complete_breathing_phase(
    cycle.id,
    success=True,
    phase_data={"outcome": "completed"}
)
```

#### Snapshots
```python
# Create snapshot (time axis preservation)
snapshot = await service.create_snapshot(
    session.id,
    SnapshotType.MILESTONE,
    description="Schema complete",
    tags=["milestone", "schema"]
)

# Restore data
data = await service.restore_from_snapshot(snapshot.id)
```

## API Layer

### Adding New Endpoints

1. Define request/response schemas in `api_schemas.py`:
```python
class NewFeatureRequest(BaseModel):
    session_id: UUID
    data: Dict[str, Any]

class NewFeatureResponse(BaseModel):
    id: UUID
    status: str
```

2. Add endpoint in `api_router.py`:
```python
@router.post("/new-feature", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    service: MemoryManagementService = Depends(get_memory_service)
):
    # Implementation
    pass
```

## Testing

### Running Tests

```bash
# All memory tests
python -m pytest tests/memory/ -v

# Specific test file
python -m pytest tests/memory/test_models.py -v

# With coverage
python -m pytest tests/memory/ --cov=bridge/memory --cov-report=html
```

### Writing Tests

```python
import pytest
from bridge.memory.service import MemoryManagementService
from bridge.memory.in_memory_repositories import *

@pytest.fixture
def memory_service():
    return MemoryManagementService(
        session_repo=InMemorySessionRepository(),
        intent_repo=InMemoryIntentRepository(),
        # ... other repos
    )

@pytest.mark.asyncio
async def test_new_feature(memory_service):
    session = await memory_service.start_session("test")
    assert session.id is not None
```

## Extension Guidelines

### Adding New Model

1. Define Pydantic model in `models.py`
2. Add SQLAlchemy model in `database.py`
3. Create abstract repository interface
4. Implement repository (in-memory first)
5. Add service methods
6. Create API endpoints
7. Write tests

### Philosophy Compliance

When extending the system, maintain these principles:

- **Time axis preservation**: Never delete, only archive
- **Choice retention**: Undecided choices remain available
- **Versioning**: Track changes, don't overwrite
- **Breathing rhythm**: Map operations to 6 phases

### Performance Considerations

- Use JSONB indexes for frequent queries
- Implement pagination for list endpoints
- Cache frequently accessed data
- Monitor query execution times

## Deployment

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

### Database Setup

Using Docker Compose:
```bash
docker-compose up -d db
```

Using provided script:
```bash
python scripts/setup_docker_db.py
```

### Running API

```bash
uvicorn bridge.api.app:app --reload --port 8000
```

## Future Development

### Phase 4 - Multi-user Support
- Authentication/Authorization
- User-specific data isolation
- Shared session capabilities

### Advanced Features
- Full-text search with PostgreSQL FTS
- Semantic search with embeddings
- Pattern analysis and prediction
- Real-time notifications

## Common Patterns

### Hierarchical Intents
```python
parent = await service.record_intent(...)
child = await service.record_intent(
    ...,
    parent_intent_id=parent.id
)
```

### Session Continuity
```python
# End of day
await service.update_session_status(session.id, SessionStatus.PAUSED)

# Next day
data = await service.continue_session(session.id)
# data contains contexts, pending choices, last intent
```

### Full Breathing Cycle
```python
# 1. Intake
intake = await service.start_breathing_phase(session_id, BreathingPhase.INTAKE)
intent = await service.record_intent(...)
await service.complete_breathing_phase(intake.id, True)

# 2. Resonance
resonance_cycle = await service.start_breathing_phase(session_id, BreathingPhase.RESONANCE)
await service.record_resonance(...)
await service.complete_breathing_phase(resonance_cycle.id, True)

# Continue through all 6 phases...
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure pydantic and other dependencies are installed
2. **Async issues**: Use `@pytest.mark.asyncio` for async tests
3. **UUID validation**: Use proper UUID types, not strings
4. **Datetime timezone**: Always use timezone-aware datetimes

### Debug Tools

```python
# JSON dump for inspection
print(model.model_dump(mode="json"))

# Check model validation
from pydantic import ValidationError
try:
    Model(**data)
except ValidationError as e:
    print(e.errors())
```

## Resources

- Pydantic Documentation: https://docs.pydantic.dev/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Resonant Engine Philosophy: `docs/philosophy/breathing_cycles.md`
