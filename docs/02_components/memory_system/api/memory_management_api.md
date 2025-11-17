# Memory Management API Specification

**Version**: 1.0.0
**Created**: 2025-11-17
**Author**: Sonnet 4.5 (Claude Code Implementation)

## Overview

The Memory Management API provides RESTful endpoints for managing the breathing history and resonance patterns of the Resonant Engine. It supports 15+ endpoints for session management, intent tracking, resonance recording, and temporal snapshots.

## Base URL

```
/api/memory
```

## Authentication

Currently supports single-user mode. Multi-user authentication planned for Phase 4.

---

## Endpoints

### Health Check

#### GET /health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "memory_management"
}
```

---

### Session Management

#### POST /sessions

Create a new session (breathing unit).

**Request:**
```json
{
  "user_id": "hiroaki",
  "metadata": {
    "client": "web",
    "version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroaki",
  "started_at": "2025-11-17T10:00:00Z",
  "last_active": "2025-11-17T10:00:00Z",
  "status": "active"
}
```

#### GET /sessions/{session_id}

Get session details with summary.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroaki",
  "started_at": "2025-11-17T10:00:00Z",
  "last_active": "2025-11-17T10:30:00Z",
  "status": "active",
  "summary": {
    "total_intents": 5,
    "completed_intents": 3,
    "resonance_events": 12,
    "choice_points": 2,
    "breathing_cycles": 3,
    "avg_intensity": 0.78
  }
}
```

#### PUT /sessions/{session_id}/heartbeat

Update session heartbeat timestamp.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroaki",
  "started_at": "2025-11-17T10:00:00Z",
  "last_active": "2025-11-17T10:35:00Z",
  "status": "active"
}
```

#### POST /sessions/{session_id}/continue

Continue a previous session (session continuity guarantee).

**Response:**
```json
{
  "session": {
    "session_id": "...",
    "user_id": "hiroaki",
    "status": "active"
  },
  "agent_contexts": {
    "kana": {"focus": "memory design"},
    "yuno": {"philosophy": "breathing preservation"}
  },
  "pending_choices": [...],
  "last_intent": {...},
  "current_breathing_phase": {...}
}
```

---

### Intent Management (Breathing Phase 1: Intake)

#### POST /intents

Record a new intent.

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_intent_id": null,
  "intent_text": "Design memory management system",
  "intent_type": "feature_request",
  "priority": 8,
  "metadata": {}
}
```

**Intent Types:**
- `feature_request`
- `bug_fix`
- `exploration`
- `clarification`
- `optimization`
- `refactoring`
- `documentation`
- `testing`

**Response:**
```json
{
  "intent_id": "660e8400-e29b-41d4-a716-446655440001",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_intent_id": null,
  "intent_text": "Design memory management system",
  "intent_type": "feature_request",
  "priority": 8,
  "created_at": "2025-11-17T10:32:00Z",
  "updated_at": "2025-11-17T10:32:00Z",
  "completed_at": null,
  "status": "pending",
  "outcome": null
}
```

#### GET /intents

List intents for a session.

**Query Parameters:**
- `session_id` (required): UUID
- `status` (optional): pending, in_progress, completed, cancelled, deferred

**Response:**
```json
{
  "intents": [...],
  "total": 5
}
```

#### PUT /intents/{intent_id}/complete

Complete an intent with outcome.

**Request:**
```json
{
  "outcome": {
    "implementation": "Schema and API implemented",
    "learnings": ["JSONB flexibility", "Repository pattern"],
    "next_steps": ["Testing", "Documentation"]
  }
}
```

**Response:**
```json
{
  "intent_id": "...",
  "status": "completed",
  "completed_at": "2025-11-17T11:00:00Z",
  "outcome": {...}
}
```

---

### Resonance Management (Breathing Phase 2)

#### POST /resonances

Record a resonance state.

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent_id": null,
  "state": "aligned",
  "intensity": 0.85,
  "agents": ["yuno", "kana"],
  "pattern_type": "philosophical_alignment",
  "duration_ms": 1500,
  "metadata": {}
}
```

**Resonance States:**
- `aligned`
- `conflicted`
- `converging`
- `exploring`
- `diverging`

**Response:**
```json
{
  "resonance_id": "770e8400-e29b-41d4-a716-446655440002",
  "session_id": "...",
  "intent_id": null,
  "state": "aligned",
  "intensity": 0.85,
  "agents": ["yuno", "kana"],
  "timestamp": "2025-11-17T10:35:00Z",
  "duration_ms": 1500,
  "pattern_type": "philosophical_alignment"
}
```

#### GET /resonances

List resonances for a session.

**Query Parameters:**
- `session_id` (required): UUID
- `state` (optional): ResonanceState

**Response:**
```json
{
  "resonances": [...],
  "total": 12,
  "avg_intensity": 0.78
}
```

---

### Agent Context Management (Breathing Phase 4: Re-reflection)

#### POST /contexts

Save agent context (creates new version).

**Request:**
```json
{
  "session_id": "...",
  "intent_id": null,
  "agent_type": "kana",
  "context_data": {
    "current_focus": "Memory schema design",
    "recent_decisions": ["Use PostgreSQL", "JSONB for flexibility"],
    "pending_questions": ["Versioning strategy?"]
  },
  "metadata": {}
}
```

**Agent Types:**
- `yuno` - Philosophical thinking core
- `kana` - External translation layer
- `tsumu` - Implementation weaver

**Response:**
```json
{
  "context_id": "...",
  "session_id": "...",
  "intent_id": null,
  "agent_type": "kana",
  "version": 3,
  "context_data": {...},
  "created_at": "2025-11-17T10:40:00Z"
}
```

#### GET /contexts/latest

Get latest context for an agent.

**Query Parameters:**
- `session_id` (required): UUID
- `agent_type` (required): yuno, kana, tsumu

#### GET /contexts/all

Get all agent contexts for a session.

**Query Parameters:**
- `session_id` (required): UUID

**Response:**
```json
{
  "contexts": {
    "yuno": {...},
    "kana": {...},
    "tsumu": {...}
  }
}
```

---

### Choice Point Management (Breathing Phase 3: Structuring)

#### POST /choice-points

Create a choice point.

**Request:**
```json
{
  "session_id": "...",
  "intent_id": "...",
  "question": "PostgreSQL vs SQLite for initial implementation?",
  "choices": [
    {
      "id": "choice_pg",
      "description": "PostgreSQL: Full-featured, production-ready",
      "implications": {
        "pros": ["JSONB support", "Concurrent access", "Scalability"],
        "cons": ["Setup complexity", "Resource usage"]
      }
    },
    {
      "id": "choice_sqlite",
      "description": "SQLite: Simple, lightweight",
      "implications": {
        "pros": ["Zero config", "Low resource"],
        "cons": ["Limited concurrency", "No JSONB"]
      }
    }
  ],
  "metadata": {}
}
```

**Response:**
```json
{
  "choice_point_id": "...",
  "session_id": "...",
  "intent_id": "...",
  "question": "...",
  "choices": [...],
  "selected_choice_id": null,
  "created_at": "2025-11-17T10:45:00Z",
  "decided_at": null,
  "decision_rationale": null,
  "status": "pending"
}
```

#### PUT /choice-points/{choice_point_id}/decide

Record a decision.

**Request:**
```json
{
  "selected_choice_id": "choice_pg",
  "decision_rationale": "Yuno評価A+。JSONB、並行性、将来性を考慮。"
}
```

**Response:**
```json
{
  "choice_point_id": "...",
  "selected_choice_id": "choice_pg",
  "decided_at": "2025-11-17T10:50:00Z",
  "decision_rationale": "..."
}
```

#### GET /choice-points/pending

Get undecided choice points.

**Query Parameters:**
- `session_id` (required): UUID

---

### Breathing Cycle Management

#### POST /breathing-cycles

Start a breathing phase.

**Request:**
```json
{
  "session_id": "...",
  "intent_id": null,
  "phase": "structuring",
  "phase_data": {
    "structures_created": ["Database schema", "API design"],
    "tools_used": ["PostgreSQL", "FastAPI"]
  }
}
```

**Breathing Phases:**
1. `intake` - 吸う
2. `resonance` - 共鳴
3. `structuring` - 構造化
4. `re_reflection` - 再内省
5. `implementation` - 実装
6. `resonance_expansion` - 共鳴拡大

**Response:**
```json
{
  "cycle_id": "...",
  "session_id": "...",
  "intent_id": null,
  "phase": "structuring",
  "started_at": "2025-11-17T11:00:00Z",
  "completed_at": null,
  "phase_data": {...},
  "success": null
}
```

#### PUT /breathing-cycles/{cycle_id}/complete

Complete a breathing phase.

**Request:**
```json
{
  "success": true,
  "phase_data": {
    "duration_minutes": 30,
    "outcome": "Schema design completed"
  }
}
```

#### GET /breathing-cycles

List breathing cycles for a session.

**Query Parameters:**
- `session_id` (required): UUID

---

### Snapshot Management (Time Axis Preservation)

#### POST /snapshots

Create a temporal snapshot.

**Request:**
```json
{
  "session_id": "...",
  "snapshot_type": "milestone",
  "description": "Memory schema design completed",
  "tags": ["schema_design", "milestone", "sprint4"]
}
```

**Snapshot Types:**
- `manual`
- `auto_hourly`
- `pre_major_change`
- `crisis_point`
- `milestone`

**Response:**
```json
{
  "snapshot_id": "...",
  "session_id": "...",
  "snapshot_type": "milestone",
  "created_at": "2025-11-17T11:30:00Z",
  "description": "Memory schema design completed",
  "tags": ["schema_design", "milestone", "sprint4"]
}
```

#### GET /snapshots

List snapshots for a session.

**Query Parameters:**
- `session_id` (required): UUID
- `tags` (optional): List of tags to filter by

#### GET /snapshots/{snapshot_id}

Get full snapshot data.

**Response:**
```json
{
  "snapshot_id": "...",
  "snapshot_type": "milestone",
  "created_at": "...",
  "description": "...",
  "tags": [...],
  "snapshot_data": {
    "session": {...},
    "intents": [...],
    "resonances": [...],
    "agent_contexts": [...],
    "choice_points": [...],
    "breathing_cycles": [...]
  }
}
```

---

### Query API

#### POST /query

Custom memory query.

**Request:**
```json
{
  "session_id": "...",
  "query": {
    "type": "intents",
    "status": "completed"
  }
}
```

**Query Types:**
- `intents`
- `resonances`
- `choice_points`

**Response:**
```json
{
  "query_id": "...",
  "results": [...],
  "count": 10,
  "execution_time_ms": 45
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request - Invalid input |
| 404  | Not Found - Resource not found |
| 422  | Validation Error |
| 500  | Internal Server Error |

## Error Response Format

```json
{
  "detail": "Error message description"
}
```

---

## Rate Limiting

Not implemented in v1.0.0. Planned for future versions.

---

## Versioning

Current version: 1.0.0

API versioning will be implemented via URL path in future releases.
