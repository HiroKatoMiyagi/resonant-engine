# Sprint 10: Choice Preservation API Documentation

## Overview

Sprint 10 extends the Memory Management System with enhanced Choice Preservation capabilities:
- **Tag-based categorization** for organizing decisions
- **Context type classification** (architecture, feature, bug_fix, general)
- **Rejection reason tracking** for unselected choices
- **Historical querying** (tags, time range, full-text search)
- **Context Assembler integration** for automatic past decision injection

---

## API Endpoints

### 1. Create Enhanced Choice Point

Create a choice point with Sprint 10 enhancements (tags, context type, user_id).

**Endpoint**: `POST /api/v1/memory/choice-points/enhanced`

**Request Body**:
```json
{
  "user_id": "hiroki",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent_id": "660e8400-e29b-41d4-a716-446655440000",
  "question": "データベース選定",
  "choices": [
    {
      "id": "A",
      "description": "PostgreSQL",
      "implications": {
        "scalability": "high",
        "complexity": "medium"
      }
    },
    {
      "id": "B",
      "description": "SQLite",
      "implications": {
        "scalability": "low",
        "complexity": "low"
      }
    }
  ],
  "tags": ["database", "technology_stack", "architecture"],
  "context_type": "architecture",
  "metadata": {}
}
```

**Response**:
```json
{
  "choice_point_id": "770e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroki",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent_id": "660e8400-e29b-41d4-a716-446655440000",
  "question": "データベース選定",
  "choices": [
    {
      "id": "A",
      "description": "PostgreSQL",
      "implications": {
        "scalability": "high",
        "complexity": "medium"
      },
      "selected": false,
      "evaluation_score": null,
      "rejection_reason": null,
      "evaluated_at": null
    },
    {
      "id": "B",
      "description": "SQLite",
      "implications": {
        "scalability": "low",
        "complexity": "low"
      },
      "selected": false,
      "evaluation_score": null,
      "rejection_reason": null,
      "evaluated_at": null
    }
  ],
  "selected_choice_id": null,
  "tags": ["database", "technology_stack", "architecture"],
  "context_type": "architecture",
  "created_at": "2025-08-15T10:30:00Z",
  "decided_at": null,
  "decision_rationale": null,
  "status": "pending"
}
```

**Validation**:
- `user_id`: Required, non-empty string
- `session_id`: Required, valid UUID
- `intent_id`: Required, valid UUID
- `question`: Required, non-empty string
- `choices`: Required, minimum 2 choices, unique IDs
- `tags`: Optional, maximum 10 tags
- `context_type`: Optional, defaults to "general"

---

### 2. Decide Choice (Enhanced)

Decide on a choice point with rejection reasons for unselected choices.

**Endpoint**: `PUT /api/v1/memory/choice-points/{choice_point_id}/decide/enhanced`

**Request Body**:
```json
{
  "selected_choice_id": "A",
  "decision_rationale": "スケーラビリティと拡張性を考慮",
  "rejection_reasons": {
    "B": "スケーラビリティ限界: 複数ユーザー対応が困難",
    "C": "リレーショナルデータに不向き"
  }
}
```

**Response**:
```json
{
  "choice_point_id": "770e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroki",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent_id": "660e8400-e29b-41d4-a716-446655440000",
  "question": "データベース選定",
  "choices": [
    {
      "id": "A",
      "description": "PostgreSQL",
      "implications": {"scalability": "high"},
      "selected": true,
      "evaluation_score": 0.9,
      "rejection_reason": null,
      "evaluated_at": "2025-08-15T10:35:00Z"
    },
    {
      "id": "B",
      "description": "SQLite",
      "implications": {"scalability": "low"},
      "selected": false,
      "evaluation_score": null,
      "rejection_reason": "スケーラビリティ限界: 複数ユーザー対応が困難",
      "evaluated_at": "2025-08-15T10:35:00Z"
    }
  ],
  "selected_choice_id": "A",
  "tags": ["database", "technology_stack", "architecture"],
  "context_type": "architecture",
  "created_at": "2025-08-15T10:30:00Z",
  "decided_at": "2025-08-15T10:35:00Z",
  "decision_rationale": "スケーラビリティと拡張性を考慮",
  "status": "decided"
}
```

**Validation**:
- `selected_choice_id`: Required, must match existing choice ID
- `decision_rationale`: Required, non-empty string
- `rejection_reasons`: Optional, keys must be valid choice IDs

**Side Effects**:
- Sets `selected=true` for selected choice
- Sets `selected=false` for all other choices
- Sets `rejection_reason` for choices in `rejection_reasons`
- Sets `decided_at` to current timestamp
- Updates all choices' `evaluated_at` to current timestamp

---

### 3. Search Choice Points

Search choice points by tags, time range, or full-text query.

**Endpoint**: `GET /api/v1/memory/choice-points/search`

**Query Parameters**:
- `user_id` (required): User ID to search for
- `tags` (optional): Comma-separated tags, e.g., "database,technology"
- `from_date` (optional): ISO8601 datetime, e.g., "2025-08-01T00:00:00Z"
- `to_date` (optional): ISO8601 datetime
- `search_text` (optional): Full-text search query
- `limit` (optional): Maximum results (1-100, default: 10)

**Examples**:

#### Search by Tags
```
GET /api/v1/memory/choice-points/search?user_id=hiroki&tags=database,architecture&limit=5
```

**Response**:
```json
{
  "results": [
    {
      "choice_point_id": "770e8400-e29b-41d4-a716-446655440000",
      "user_id": "hiroki",
      "question": "データベース選定",
      "selected_choice_id": "A",
      "tags": ["database", "technology_stack", "architecture"],
      "context_type": "architecture",
      "decided_at": "2025-08-15T10:35:00Z"
    }
  ],
  "count": 1,
  "query": {
    "user_id": "hiroki",
    "tags": ["database", "architecture"],
    "limit": 5
  }
}
```

#### Search by Time Range
```
GET /api/v1/memory/choice-points/search?user_id=hiroki&from_date=2025-08-01T00:00:00Z&to_date=2025-08-31T23:59:59Z
```

**Response**: Same structure as tag search, filtered by `decided_at` within range.

#### Full-Text Search
```
GET /api/v1/memory/choice-points/search?user_id=hiroki&search_text=database&limit=10
```

**Response**: Same structure, ordered by PostgreSQL `ts_rank` relevance score.

**Notes**:
- If multiple parameters are provided, priority is: `search_text` > `tags` > `from_date/to_date`
- If no parameters (except `user_id`) are provided, returns most recent decided choice points
- All searches are scoped to the specified `user_id`

---

## Data Models

### ChoiceSchema (Sprint 10 Enhanced)

```python
{
  "id": str,                           # Unique choice ID
  "description": str,                  # Choice description
  "implications": Dict[str, Any],      # Implications of this choice

  # Sprint 10 additions
  "selected": bool,                    # Whether this choice was selected
  "evaluation_score": float | null,    # Evaluation score (0-1)
  "rejection_reason": str | null,      # Reason for rejection (max 1000 chars)
  "evaluated_at": datetime | null      # When this choice was evaluated
}
```

### ChoicePointEnhancedResponse

```python
{
  "choice_point_id": UUID,
  "user_id": str,                      # 🆕 Sprint 10
  "session_id": UUID,
  "intent_id": UUID,
  "question": str,
  "choices": List[ChoiceSchema],
  "selected_choice_id": str | null,
  "tags": List[str],                   # 🆕 Sprint 10 (max 10)
  "context_type": str,                 # 🆕 Sprint 10
  "created_at": datetime,
  "decided_at": datetime | null,
  "decision_rationale": str | null,
  "status": "pending" | "decided"      # Computed from selected_choice_id
}
```

---

## Context Assembler Integration

### Overview

Sprint 10 integrates Choice Preservation with the Context Assembler, enabling automatic injection of relevant past decisions into conversation context.

### How It Works

1. **Fetch Relevant Choices**: When assembling context, `ChoiceQueryEngine.get_relevant_choices_for_context()` is called
2. **Relevance Scoring**: Uses PostgreSQL full-text search (`ts_rank`) to find choices similar to current question
3. **Context Injection**: Relevant choices are formatted and added to the system prompt
4. **Token Management**: Past choices can be compressed if context exceeds token limit

### Assembly Options

```python
options = AssemblyOptions(
    include_past_choices=True,       # Enable/disable past choice injection
    past_choices_limit=3,            # Maximum past choices to include (1-10)
)
```

### Context Format

Past choices are injected into the system prompt as:

```
## 過去の意思決定履歴

以下は、あなたが過去に行った類似の意思決定です。一貫性を保つために参考にしてください。

1. **データベース選定**
   - 選択: PostgreSQL
   - 理由: スケーラビリティと拡張性を考慮
   - 却下した選択肢:
     • SQLite: スケーラビリティ限界: 複数ユーザー対応が困難
     • MongoDB: リレーショナルデータに不向き
   - 決定日: 2025-08-15

2. **フレームワーク選定**
   - 選択: FastAPI
   - 理由: 型安全性とドキュメント自動生成
   - 却下した選択肢:
     • Flask: 機能不足
   - 決定日: 2025-08-10
```

### Metadata

Context metadata includes:

```python
{
  "working_memory_count": 5,
  "semantic_memory_count": 3,
  "has_session_summary": true,
  "has_user_profile": true,
  "past_choices_count": 2,           # 🆕 Sprint 10
  "total_tokens": 8500,
  "compression_applied": false
}
```

---

## Use Cases

### 1. Technology Stack Decisions

**Scenario**: User asks about database choice

**Past Decision**:
- Question: "PostgreSQL vs MySQL?"
- Selected: PostgreSQL
- Rejection: MySQL (ライセンス懸念)

**Current Question**: "Should we use MongoDB or PostgreSQL?"

**Result**: Context Assembler injects past PostgreSQL decision, helping maintain consistency

---

### 2. Architecture Pattern Tracking

**Tags**: `["architecture", "design_pattern", "scalability"]`

**Context Type**: `architecture`

**Use**: Search all architecture decisions by tag to review past patterns

---

### 3. Feature Implementation Choices

**Tags**: `["feature", "user_authentication"]`

**Context Type**: `feature`

**Use**: When implementing new features, retrieve similar past feature decisions

---

## Performance Considerations

### Indexes

Sprint 10 creates the following PostgreSQL indexes:

```sql
-- Tag search (GIN index for array)
CREATE INDEX idx_choice_points_tags ON choice_points USING GIN(tags);

-- Time range queries
CREATE INDEX idx_choice_points_decided_at ON choice_points(decided_at);

-- Full-text search
CREATE INDEX idx_choice_points_question_fulltext
  ON choice_points USING GIN(to_tsvector('english', question));

-- User-scoped queries
CREATE INDEX idx_choice_points_user_id ON choice_points(user_id);

-- Context type filtering
CREATE INDEX idx_choice_points_context_type ON choice_points(context_type);

-- JSONB choices search
CREATE INDEX idx_choice_points_choices_gin ON choice_points USING GIN(choices);
```

### Query Performance Targets

- **Tag search**: < 50ms for 1000+ choice points
- **Time range search**: < 30ms
- **Full-text search**: < 100ms
- **Context assembly**: < 200ms (including choice retrieval)

---

## Error Handling

### Common Errors

#### 400 Bad Request
```json
{
  "detail": "Maximum 10 tags allowed"
}
```

**Cause**: More than 10 tags provided

---

#### 404 Not Found
```json
{
  "detail": "Choice point not found"
}
```

**Cause**: Invalid `choice_point_id` in decide endpoint

---

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "selected_choice_id"],
      "msg": "selected_choice_id 'D' not found in choices",
      "type": "value_error"
    }
  ]
}
```

**Cause**: `selected_choice_id` doesn't match any choice ID

---

## Migration Guide

### From Basic Choice Points to Sprint 10

If you have existing choice points without Sprint 10 fields:

1. **user_id**: Automatically set to `"legacy_user"` by migration
2. **tags**: Defaults to empty array `[]`
3. **context_type**: Defaults to `"general"`

### Update Existing Code

**Before**:
```python
cp = await memory_service.create_choice_point(
    session_id=session_id,
    intent_id=intent_id,
    question="Test",
    choices=[...],
)
```

**After (Sprint 10)**:
```python
cp = await memory_service.create_choice_point_enhanced(
    user_id="hiroki",
    session_id=session_id,
    intent_id=intent_id,
    question="Test",
    choices=[...],
    tags=["test", "example"],
    context_type="feature",
)
```

---

## Testing

### Unit Tests

Located in:
- `tests/memory/test_choice_models.py` (11 tests)
- `tests/memory/test_choice_query_engine.py` (10 tests)

Run:
```bash
pytest tests/memory/test_choice_*.py -v
```

### Integration Tests

Located in:
- `tests/context_assembler/test_choice_integration.py` (9 tests)
- `tests/integration/test_choice_preservation_e2e.py` (5 E2E tests)

Run:
```bash
pytest tests/integration/test_choice_preservation_e2e.py -v
```

---

## Future Enhancements (Sprint 11+)

- **Contradiction Detection**: Detect when new decisions contradict past choices
- **Choice Analytics**: Aggregate statistics on decision patterns
- **Multi-user Choice Sharing**: Share choice points across team members
- **Choice Templates**: Pre-defined choice point templates for common scenarios

---

## References

- **Sprint 10 Specification**: `docs/02_components/memory_system/architecture/sprint10_choice_preservation_completion_spec.md`
- **Start Instructions**: `docs/02_components/memory_system/sprint/sprint10_choice_preservation_completion_start.md`
- **Acceptance Tests**: `docs/02_components/memory_system/test/sprint10_choice_preservation_acceptance_test_spec.md`
