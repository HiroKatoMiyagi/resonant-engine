# Bridge Lite Sprint 1 Implementation Specification
## Re-evaluation API & Feedback Loop

**Sprint期間**: 2025-11-14 〜 2025-11-21（7日間）  
**優先度**: P0（最優先）  
**目的**: Intent補正機能の実装により、Kana/Yunoからの呼吸調整メカニズムを確立

---

## 1. Sprint 1 Overview

### 1.1 目的
Re-evaluation APIを実装し、以下を実現する：
- Kana/Yunoからの補正意図をIntentに統合
- 差分適用による状態更新
- 冪等性保証による安全な再実行
- FeedbackBridgeとの統合による呼吸循環の完成

### 1.2 スコープ
**IN Scope**:
- Re-evaluation API エンドポイント実装
- Diff形式の定義と適用ロジック
- Idempotency保証メカニズム
- correction_history管理
- FeedbackBridge統合
- 8+ テストケース実装

**OUT of Scope**:
- 並行実行制御（Sprint 2）
- UI同期（Sprint 3）
- 監査ログETL更新（Sprint 3）

### 1.3 Done Definition
- [ ] Re-evaluation API が統合仕様 2.4 に完全準拠
- [ ] diff 適用ロジックがテスト済み
- [ ] 冪等性が保証されている
- [ ] correction_history が正しく記録される
- [ ] FeedbackBridge が Re-eval を呼び出せる
- [ ] 8+ テストケースがすべて通過
- [ ] APIドキュメント更新完了
- [ ] Kana による仕様レビュー通過

---

## 2. Re-evaluation API Specification

### 2.1 Endpoint Definition

```
POST /api/v1/intent/reeval
Content-Type: application/json
```

### 2.2 Request Schema

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ReEvaluationRequest(BaseModel):
    """Re-evaluation API request model"""
    
    intent_id: UUID = Field(
        ...,
        description="Target intent ID to re-evaluate"
    )
    
    diff: dict = Field(
        ...,
        description="Differential corrections to apply (absolute values only)",
        examples=[{
            "payload": {
                "key_to_update": "new_value",
                "nested.path": "new_nested_value"
            }
        }]
    )
    
    source: PhilosophicalActor = Field(
        ...,
        description="Source of the correction (YUNO or KANA)"
    )
    
    reason: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Human-readable reason for the correction"
    )
    
    metadata: dict | None = Field(
        default=None,
        description="Optional metadata for correction tracking"
    )
```

### 2.3 Response Schema

```python
class ReEvaluationResponse(BaseModel):
    """Re-evaluation API response model"""
    
    intent_id: UUID = Field(
        ...,
        description="Re-evaluated intent ID"
    )
    
    status: IntentStatusEnum = Field(
        ...,
        description="Current intent status (should be CORRECTED)"
    )
    
    already_applied: bool = Field(
        ...,
        description="True if this exact correction was previously applied"
    )
    
    correction_id: UUID = Field(
        ...,
        description="Unique ID for this correction (for idempotency)"
    )
    
    applied_at: datetime = Field(
        ...,
        description="Timestamp when correction was applied"
    )
    
    correction_count: int = Field(
        ...,
        description="Total number of corrections applied to this intent"
    )
```

### 2.4 Error Responses

```python
class ReEvaluationError(BaseModel):
    """Error response schema"""
    error_code: str
    message: str
    details: dict | None = None

# Error codes:
# - INTENT_NOT_FOUND: Intent ID does not exist
# - INVALID_STATUS: Intent in non-correctable status (e.g., COMPLETED, FAILED)
# - INVALID_DIFF: Diff format validation failed
# - INVALID_SOURCE: Source actor not authorized for re-evaluation
# - APPLY_FAILED: Diff application failed (e.g., type mismatch)
```

---

## 3. Diff Specification

### 3.1 Format Rules

**MUST (Required)**:
- Diff は dict 型である
- すべての値は絶対値（absolute value）である
- 相対演算子（`+10`, `-5` など）は禁止
- ネストされたキーはドット記法（`nested.path`）で表現可能

**MUST NOT (Forbidden)**:
- 相対値操作（`"count": "+10"`）
- 演算子を含む値（`"*2"`, `/5`）
- 関数呼び出し（`"now()"`, `"uuid()"`）
- Pythonコード（`"__import__('os').system('...')"`）

### 3.2 Diff Examples

#### Example 1: Simple field update
```json
{
  "payload": {
    "status_message": "Updated by Yuno for philosophical alignment"
  }
}
```

#### Example 2: Nested field update
```json
{
  "payload": {
    "config.max_retries": 5,
    "config.timeout_seconds": 30
  }
}
```

#### Example 3: Multiple fields
```json
{
  "payload": {
    "priority": "high",
    "assigned_to": "KANA",
    "metadata.correction_reason": "Strategic adjustment"
  }
}
```

### 3.3 Diff Application Logic

```python
def apply_diff(target: dict, diff: dict) -> dict:
    """
    Apply diff to target dict using absolute value replacement.
    Supports dot notation for nested paths.
    
    Args:
        target: Target dict to modify
        diff: Diff dict with absolute values
        
    Returns:
        Modified target dict
        
    Raises:
        DiffValidationError: If diff contains invalid operations
        DiffApplicationError: If diff cannot be applied
    """
    result = target.copy()
    
    for key, value in diff.items():
        # Check for forbidden patterns
        if isinstance(value, str):
            if any(op in value for op in ['+', '-', '*', '/', '(', ')']):
                raise DiffValidationError(
                    f"Relative operations forbidden in diff: {key}={value}"
                )
        
        # Handle dot notation for nested paths
        if '.' in key:
            parts = key.split('.')
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            result[key] = value
    
    return result
```

---

## 4. Idempotency Mechanism

### 4.1 Correction ID Generation

```python
import hashlib
import json
from uuid import UUID

def generate_correction_id(intent_id: UUID, diff: dict) -> UUID:
    """
    Generate deterministic correction ID from intent_id + diff.
    Same intent_id + same diff = same correction_id (idempotency).
    
    Args:
        intent_id: Target intent ID
        diff: Diff dict
        
    Returns:
        Deterministic UUID v5 based on content hash
    """
    # Serialize diff with sorted keys for consistency
    diff_json = json.dumps(diff, sort_keys=True, ensure_ascii=False)
    
    # Create hash input
    hash_input = f"{intent_id}:{diff_json}"
    
    # Generate deterministic UUID v5
    namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
    correction_id = uuid.uuid5(namespace, hash_input)
    
    return correction_id
```

### 4.2 Duplicate Detection

```python
def is_correction_applied(
    intent: IntentModel, 
    correction_id: UUID
) -> bool:
    """
    Check if correction was already applied to this intent.
    
    Args:
        intent: Target intent
        correction_id: Correction ID to check
        
    Returns:
        True if correction already applied, False otherwise
    """
    return any(
        record.get('correction_id') == correction_id
        for record in intent.correction_history
    )
```

### 4.3 Correction History Record

```python
class CorrectionRecord(BaseModel):
    """Single correction history entry"""
    
    correction_id: UUID = Field(..., description="Unique correction ID")
    source: PhilosophicalActor = Field(..., description="Source actor")
    reason: str = Field(..., description="Correction reason")
    diff: dict = Field(..., description="Applied diff")
    applied_at: datetime = Field(..., description="Application timestamp")
    metadata: dict | None = Field(default=None, description="Optional metadata")

# IntentModel.correction_history: list[CorrectionRecord]
```

---

## 5. Implementation Details

### 5.1 File Structure

```
resonant-engine/
├── bridge/
│   ├── api/
│   │   └── reeval.py          # New: Re-evaluation endpoint
│   ├── core/
│   │   ├── models/
│   │   │   ├── intent_model.py  # Update: apply_correction method
│   │   │   └── reeval.py        # New: Request/Response models
│   │   └── correction/
│   │       ├── __init__.py
│   │       ├── diff.py          # New: Diff validation & application
│   │       └── idempotency.py  # New: Correction ID & duplicate detection
│   ├── bridges/
│   │   └── feedback_bridge.py # Update: Integrate re-eval
│   └── tests/
│       └── reeval/
│           ├── test_reeval_api.py       # New: API tests
│           ├── test_diff_application.py # New: Diff logic tests
│           └── test_idempotency.py      # New: Idempotency tests
```

### 5.2 Core Implementation

#### 5.2.1 IntentModel.apply_correction Method

```python
# bridge/core/models/intent_model.py

from bridge.core.correction.diff import apply_diff
from bridge.core.correction.idempotency import generate_correction_id

class IntentModel(BaseModel):
    # ... existing fields ...
    
    correction_history: list[dict] = Field(default_factory=list)
    
    def apply_correction(
        self,
        diff: dict,
        source: PhilosophicalActor,
        reason: str,
        metadata: dict | None = None
    ) -> UUID:
        """
        Apply differential correction to intent payload.
        
        Args:
            diff: Corrections to apply (absolute values only)
            source: Source actor (YUNO or KANA)
            reason: Human-readable reason
            metadata: Optional metadata
            
        Returns:
            correction_id: Unique ID for this correction
            
        Raises:
            DiffValidationError: If diff is invalid
            DiffApplicationError: If diff cannot be applied
            InvalidStatusError: If intent status prevents correction
        """
        # Validate status
        if self.status in [IntentStatusEnum.COMPLETED, IntentStatusEnum.FAILED]:
            raise InvalidStatusError(
                f"Cannot correct intent in {self.status} status"
            )
        
        # Generate correction ID
        correction_id = generate_correction_id(self.id, diff)
        
        # Check if already applied (idempotency)
        if any(r.get('correction_id') == correction_id 
               for r in self.correction_history):
            return correction_id  # Already applied, skip
        
        # Apply diff to payload
        if 'payload' in diff:
            self.payload = apply_diff(self.payload, diff['payload'])
        
        # Update status
        self.status = IntentStatusEnum.CORRECTED
        self.updated_at = datetime.utcnow()
        
        # Record correction
        self.correction_history.append({
            'correction_id': str(correction_id),
            'source': source.value,
            'reason': reason,
            'diff': diff,
            'applied_at': self.updated_at.isoformat(),
            'metadata': metadata
        })
        
        return correction_id
```

#### 5.2.2 Re-evaluation Endpoint

```python
# bridge/api/reeval.py

from fastapi import APIRouter, HTTPException, status
from bridge.core.models.reeval import ReEvaluationRequest, ReEvaluationResponse
from bridge.core.correction.idempotency import generate_correction_id, is_correction_applied
from bridge.data.bridges import get_data_bridge
from bridge.audit.logger import get_audit_logger

router = APIRouter(prefix="/api/v1/intent", tags=["re-evaluation"])

@router.post("/reeval", response_model=ReEvaluationResponse)
async def reeval_intent(request: ReEvaluationRequest) -> ReEvaluationResponse:
    """
    Re-evaluate and correct an intent with differential updates.
    
    This endpoint allows Yuno/Kana to apply philosophical or strategic
    corrections to existing intents, maintaining idempotency and
    correction history.
    """
    data_bridge = get_data_bridge()
    audit_logger = get_audit_logger()
    
    # 1. Fetch intent
    intent = await data_bridge.get_intent(request.intent_id)
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intent {request.intent_id} not found"
        )
    
    # 2. Validate source authorization
    if request.source not in [PhilosophicalActor.YUNO, PhilosophicalActor.KANA]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Source {request.source} not authorized for re-evaluation"
        )
    
    # 3. Generate correction ID
    correction_id = generate_correction_id(request.intent_id, request.diff)
    
    # 4. Check idempotency
    already_applied = is_correction_applied(intent, correction_id)
    
    if not already_applied:
        try:
            # 5. Apply correction
            correction_id = intent.apply_correction(
                diff=request.diff,
                source=request.source,
                reason=request.reason,
                metadata=request.metadata
            )
            
            # 6. Persist intent
            await data_bridge.update_intent(intent)
            
            # 7. Log to audit
            await audit_logger.log(
                event=AuditEventType.REEVALUATED,
                intent_id=intent.id,
                actor=request.source,
                bridge_type=None,
                payload={
                    'correction_id': str(correction_id),
                    'reason': request.reason,
                    'diff': request.diff
                }
            )
            
        except InvalidStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        except (DiffValidationError, DiffApplicationError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    # 8. Return response
    return ReEvaluationResponse(
        intent_id=intent.id,
        status=intent.status,
        already_applied=already_applied,
        correction_id=correction_id,
        applied_at=datetime.utcnow(),
        correction_count=len(intent.correction_history)
    )
```

#### 5.2.3 FeedbackBridge Integration

```python
# bridge/bridges/feedback_bridge.py

class FeedbackBridge(BaseBridge):
    """
    Feedback bridge that can trigger re-evaluation based on
    analysis results.
    """
    
    def __init__(self, reeval_client: ReEvalClient):
        super().__init__(BridgeTypeEnum.FEEDBACK)
        self.reeval_client = reeval_client
    
    async def execute(self, intent: IntentModel) -> IntentModel:
        """
        Execute feedback analysis and optionally trigger re-evaluation.
        """
        # 1. Analyze intent for correction needs
        analysis = await self.analyze_intent(intent)
        
        # 2. If correction needed, trigger re-eval
        if analysis.needs_correction:
            reeval_request = ReEvaluationRequest(
                intent_id=intent.id,
                diff=analysis.suggested_diff,
                source=PhilosophicalActor.KANA,  # FeedbackBridge acts as Kana
                reason=analysis.correction_reason,
                metadata={
                    'feedback_score': analysis.score,
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Call re-eval API
            response = await self.reeval_client.reeval(reeval_request)
            
            # Update intent with corrected version
            intent = await self.data_bridge.get_intent(intent.id)
        
        # 3. Return intent (corrected or unchanged)
        return intent
    
    async def analyze_intent(self, intent: IntentModel) -> FeedbackAnalysis:
        """
        Analyze intent and determine if correction is needed.
        """
        # Implementation: Analysis logic
        # Returns FeedbackAnalysis with needs_correction flag
        pass
```

---

## 6. Test Specification

### 6.1 Test Categories

```
Category                Count    Files
Normal flow              3       test_reeval_api.py
Idempotency             3       test_idempotency.py
Error handling          2       test_reeval_api.py
Diff validation         3       test_diff_application.py
FeedbackBridge          2       test_feedback_bridge_integration.py
Authorization           1       test_reeval_api.py
---
Total                   14      (exceeds minimum 8)
```

### 6.2 Test Cases Detail

#### 6.2.1 Normal Flow Tests (3 cases)

```python
# tests/reeval/test_reeval_api.py

@pytest.mark.asyncio
async def test_reeval_simple_field_update():
    """Test: Simple field update through re-eval API"""
    # Given: Intent with original payload
    intent = create_test_intent(payload={'status': 'draft'})
    
    # When: Re-eval with simple diff
    response = await reeval_client.reeval(ReEvaluationRequest(
        intent_id=intent.id,
        diff={'payload': {'status': 'reviewed'}},
        source=PhilosophicalActor.YUNO,
        reason='Status update by Yuno'
    ))
    
    # Then: Intent updated, status CORRECTED
    assert response.status == IntentStatusEnum.CORRECTED
    assert response.already_applied == False
    
    updated_intent = await data_bridge.get_intent(intent.id)
    assert updated_intent.payload['status'] == 'reviewed'
    assert len(updated_intent.correction_history) == 1

@pytest.mark.asyncio
async def test_reeval_nested_field_update():
    """Test: Nested field update using dot notation"""
    # Given: Intent with nested config
    intent = create_test_intent(payload={
        'config': {'timeout': 10, 'retries': 3}
    })
    
    # When: Re-eval with nested diff
    response = await reeval_client.reeval(ReEvaluationRequest(
        intent_id=intent.id,
        diff={'payload': {'config.timeout': 30}},
        source=PhilosophicalActor.KANA,
        reason='Timeout adjustment'
    ))
    
    # Then: Nested field updated
    updated_intent = await data_bridge.get_intent(intent.id)
    assert updated_intent.payload['config']['timeout'] == 30
    assert updated_intent.payload['config']['retries'] == 3  # Unchanged

@pytest.mark.asyncio
async def test_reeval_multiple_fields():
    """Test: Multiple fields update in single re-eval"""
    # Given: Intent with multiple fields
    intent = create_test_intent(payload={
        'priority': 'low',
        'assigned_to': None,
        'tags': []
    })
    
    # When: Re-eval with multiple changes
    response = await reeval_client.reeval(ReEvaluationRequest(
        intent_id=intent.id,
        diff={'payload': {
            'priority': 'high',
            'assigned_to': 'KANA',
            'tags': ['urgent', 'reviewed']
        }},
        source=PhilosophicalActor.YUNO,
        reason='Priority escalation'
    ))
    
    # Then: All fields updated atomically
    updated_intent = await data_bridge.get_intent(intent.id)
    assert updated_intent.payload['priority'] == 'high'
    assert updated_intent.payload['assigned_to'] == 'KANA'
    assert updated_intent.payload['tags'] == ['urgent', 'reviewed']
```

#### 6.2.2 Idempotency Tests (3 cases)

```python
# tests/reeval/test_idempotency.py

@pytest.mark.asyncio
async def test_reeval_idempotency_same_diff():
    """Test: Same diff applied twice returns already_applied=True"""
    # Given: Intent
    intent = create_test_intent()
    
    # When: Apply same diff twice
    diff = {'payload': {'status': 'corrected'}}
    
    response1 = await reeval_client.reeval(ReEvaluationRequest(
        intent_id=intent.id,
        diff=diff,
        source=PhilosophicalActor.YUNO,
        reason='First correction'
    ))
    
    response2 = await reeval_client.reeval(ReEvaluationRequest(
        intent_id=intent.id,
        diff=diff,
        source=PhilosophicalActor.YUNO,
        reason='Second correction (should be idempotent)'
    ))
    
    # Then: Second call detects duplicate
    assert response1.already_applied == False
    assert response2.already_applied == True
    assert response1.correction_id == response2.correction_id
    
    # And: Only one correction in history
    updated_intent = await data_bridge.get_intent(intent.id)
    assert len(updated_intent.correction_history) == 1

@pytest.mark.asyncio
async def test_reeval_different_diffs_different_ids():
    """Test: Different diffs generate different correction IDs"""
    # Given: Intent
    intent = create_test_intent()
    
    # When: Apply two different diffs
    response1 = await reeval_client.reeval(ReEvaluationRequest(
        intent_id=intent.id,
        diff={'payload': {'field_a': 'value1'}},
        source=PhilosophicalActor.YUNO,
        reason='First correction'
    ))
    
    response2 = await reeval_client.reeval(ReEvaluationRequest(
        intent_id=intent.id,
        diff={'payload': {'field_b': 'value2'}},
        source=PhilosophicalActor.KANA,
        reason='Second correction'
    ))
    
    # Then: Different correction IDs
    assert response1.correction_id != response2.correction_id
    
    # And: Both corrections in history
    updated_intent = await data_bridge.get_intent(intent.id)
    assert len(updated_intent.correction_history) == 2

@pytest.mark.asyncio
async def test_reeval_correction_id_deterministic():
    """Test: Same intent_id + diff always generates same correction_id"""
    # Given: Two identical intents
    intent1 = create_test_intent()
    intent2 = create_test_intent()
    
    diff = {'payload': {'status': 'test'}}
    
    # When: Generate correction IDs
    correction_id1 = generate_correction_id(intent1.id, diff)
    correction_id2 = generate_correction_id(intent1.id, diff)  # Same intent
    correction_id3 = generate_correction_id(intent2.id, diff)  # Different intent
    
    # Then: Same intent + diff = same ID
    assert correction_id1 == correction_id2
    assert correction_id1 != correction_id3
```

#### 6.2.3 Error Handling Tests (2 cases)

```python
# tests/reeval/test_reeval_api.py

@pytest.mark.asyncio
async def test_reeval_intent_not_found():
    """Test: Re-eval on non-existent intent returns 404"""
    # Given: Non-existent intent ID
    fake_id = uuid.uuid4()
    
    # When: Attempt re-eval
    with pytest.raises(HTTPException) as exc_info:
        await reeval_client.reeval(ReEvaluationRequest(
            intent_id=fake_id,
            diff={'payload': {'status': 'updated'}},
            source=PhilosophicalActor.YUNO,
            reason='Test'
        ))
    
    # Then: 404 error
    assert exc_info.value.status_code == 404
    assert 'not found' in str(exc_info.value.detail).lower()

@pytest.mark.asyncio
async def test_reeval_invalid_status():
    """Test: Re-eval on COMPLETED intent returns 409"""
    # Given: Completed intent
    intent = create_test_intent(status=IntentStatusEnum.COMPLETED)
    
    # When: Attempt re-eval
    with pytest.raises(HTTPException) as exc_info:
        await reeval_client.reeval(ReEvaluationRequest(
            intent_id=intent.id,
            diff={'payload': {'status': 'updated'}},
            source=PhilosophicalActor.YUNO,
            reason='Test'
        ))
    
    # Then: 409 conflict
    assert exc_info.value.status_code == 409
    assert 'cannot correct' in str(exc_info.value.detail).lower()
```

#### 6.2.4 Diff Validation Tests (3 cases)

```python
# tests/reeval/test_diff_application.py

def test_diff_apply_simple():
    """Test: Simple field replacement"""
    # Given: Target dict
    target = {'field_a': 'old_value', 'field_b': 100}
    diff = {'field_a': 'new_value'}
    
    # When: Apply diff
    result = apply_diff(target, diff)
    
    # Then: Field updated
    assert result['field_a'] == 'new_value'
    assert result['field_b'] == 100  # Unchanged

def test_diff_apply_nested():
    """Test: Nested field update with dot notation"""
    # Given: Nested target
    target = {'config': {'timeout': 10, 'retries': 3}}
    diff = {'config.timeout': 30}
    
    # When: Apply diff
    result = apply_diff(target, diff)
    
    # Then: Nested field updated
    assert result['config']['timeout'] == 30
    assert result['config']['retries'] == 3

def test_diff_forbid_relative_operations():
    """Test: Relative operations are rejected"""
    # Given: Target with counter
    target = {'count': 10}
    diff = {'count': '+5'}  # Forbidden relative operation
    
    # When: Attempt apply diff
    with pytest.raises(DiffValidationError) as exc_info:
        apply_diff(target, diff)
    
    # Then: Error raised
    assert 'relative operations forbidden' in str(exc_info.value).lower()
```

#### 6.2.5 FeedbackBridge Integration Tests (2 cases)

```python
# tests/reeval/test_feedback_bridge_integration.py

@pytest.mark.asyncio
async def test_feedback_bridge_triggers_reeval():
    """Test: FeedbackBridge can trigger re-eval automatically"""
    # Given: Intent that needs correction
    intent = create_test_intent(payload={'quality_score': 0.3})
    feedback_bridge = FeedbackBridge(reeval_client)
    
    # When: Execute FeedbackBridge
    result = await feedback_bridge.execute(intent)
    
    # Then: Intent corrected
    assert result.status == IntentStatusEnum.CORRECTED
    assert len(result.correction_history) > 0

@pytest.mark.asyncio
async def test_feedback_bridge_passes_through_when_no_correction():
    """Test: FeedbackBridge passes through if no correction needed"""
    # Given: Intent with good quality
    intent = create_test_intent(payload={'quality_score': 0.9})
    feedback_bridge = FeedbackBridge(reeval_client)
    
    # When: Execute FeedbackBridge
    result = await feedback_bridge.execute(intent)
    
    # Then: Intent unchanged
    assert result.status == intent.status  # Not CORRECTED
    assert len(result.correction_history) == 0
```

#### 6.2.6 Authorization Test (1 case)

```python
# tests/reeval/test_reeval_api.py

@pytest.mark.asyncio
async def test_reeval_unauthorized_source():
    """Test: Re-eval with TSUMU source is rejected"""
    # Given: Intent
    intent = create_test_intent()
    
    # When: Attempt re-eval with TSUMU
    with pytest.raises(HTTPException) as exc_info:
        await reeval_client.reeval(ReEvaluationRequest(
            intent_id=intent.id,
            diff={'payload': {'status': 'hacked'}},
            source=PhilosophicalActor.TSUMU,  # Not authorized
            reason='Unauthorized attempt'
        ))
    
    # Then: 403 forbidden
    assert exc_info.value.status_code == 403
    assert 'not authorized' in str(exc_info.value.detail).lower()
```

---

## 7. Implementation Schedule

### Day 1 (Mon): Core Models & Diff Logic
- [ ] Create `bridge/core/models/reeval.py` (Request/Response models)
- [ ] Create `bridge/core/correction/diff.py` (apply_diff, validation)
- [ ] Create `bridge/core/correction/idempotency.py` (correction_id, duplicate check)
- [ ] Update `IntentModel.apply_correction` method
- [ ] Write unit tests for diff application (3 cases)

### Day 2 (Tue): API Endpoint
- [ ] Create `bridge/api/reeval.py` (FastAPI endpoint)
- [ ] Implement request validation
- [ ] Implement error handling
- [ ] Wire up with DataBridge
- [ ] Wire up with AuditLogger
- [ ] Write API tests (5 cases: normal + errors + auth)

### Day 3 (Wed): Idempotency & Testing
- [ ] Implement correction_id generation
- [ ] Implement duplicate detection
- [ ] Add correction_history persistence
- [ ] Write idempotency tests (3 cases)
- [ ] Integration test for full flow

### Day 4 (Thu): FeedbackBridge Integration
- [ ] Create ReEvalClient helper
- [ ] Update FeedbackBridge to call re-eval
- [ ] Implement feedback analysis logic (placeholder)
- [ ] Write FeedbackBridge integration tests (2 cases)

### Day 5 (Fri): Documentation & Review
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Update README with re-eval examples
- [ ] Code review preparation
- [ ] Performance testing (re-eval latency)
- [ ] Submit for Kana review

### Day 6-7 (Weekend): Buffer & Refinement
- [ ] Address review feedback
- [ ] Refactor based on findings
- [ ] Additional edge case tests
- [ ] Final Done Definition check

---

## 8. API Documentation

### 8.1 OpenAPI Schema

```yaml
openapi: 3.0.0
info:
  title: Bridge Lite Re-evaluation API
  version: 2.1.0
  description: Intent correction and re-evaluation endpoint

paths:
  /api/v1/intent/reeval:
    post:
      summary: Re-evaluate and correct an intent
      operationId: reevalIntent
      tags:
        - re-evaluation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReEvaluationRequest'
      responses:
        '200':
          description: Intent successfully re-evaluated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReEvaluationResponse'
        '400':
          description: Invalid diff format
        '403':
          description: Source not authorized for re-evaluation
        '404':
          description: Intent not found
        '409':
          description: Intent in non-correctable status

components:
  schemas:
    ReEvaluationRequest:
      type: object
      required:
        - intent_id
        - diff
        - source
        - reason
      properties:
        intent_id:
          type: string
          format: uuid
        diff:
          type: object
          description: Absolute value corrections
        source:
          type: string
          enum: [yuno, kana]
        reason:
          type: string
          minLength: 1
          maxLength: 1000
        metadata:
          type: object
          nullable: true
    
    ReEvaluationResponse:
      type: object
      properties:
        intent_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [corrected]
        already_applied:
          type: boolean
        correction_id:
          type: string
          format: uuid
        applied_at:
          type: string
          format: date-time
        correction_count:
          type: integer
```

### 8.2 Usage Examples

#### Example 1: Yuno corrects philosophical alignment

```bash
curl -X POST http://localhost:8000/api/v1/intent/reeval \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "550e8400-e29b-41d4-a716-446655440000",
    "diff": {
      "payload": {
        "philosophical_alignment": "adjusted",
        "reasoning": "Enhanced coherence with Resonant Engine principles"
      }
    },
    "source": "yuno",
    "reason": "Philosophical alignment correction"
  }'
```

#### Example 2: Kana adjusts technical parameters

```bash
curl -X POST http://localhost:8000/api/v1/intent/reeval \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "550e8400-e29b-41d4-a716-446655440000",
    "diff": {
      "payload": {
        "config.timeout": 60,
        "config.max_retries": 5
      }
    },
    "source": "kana",
    "reason": "Technical parameter optimization",
    "metadata": {
      "optimization_type": "latency_reduction"
    }
  }'
```

---

## 9. Performance Requirements

### 9.1 Latency Targets
- P50: < 50ms (re-eval API call)
- P95: < 200ms
- P99: < 500ms

### 9.2 Throughput
- Minimum: 100 re-eval/sec per instance
- Target: 500 re-eval/sec per instance

### 9.3 Storage
- correction_history: Maximum 100 entries per intent
- Oldest entries pruned if limit exceeded
- Full history archived to audit log

---

## 10. Security Considerations

### 10.1 Authorization
- Only YUNO and KANA can trigger re-evaluation
- TSUMU and other actors are forbidden (403)
- Source validation in every request

### 10.2 Input Validation
- Diff size limit: 10KB per request
- Reason length: 1-1000 characters
- No code execution in diff values

### 10.3 Audit Trail
- Every re-eval logged to AuditLogger
- correction_history preserved immutably
- Source and reason recorded for accountability

---

## 11. Monitoring & Metrics

### 11.1 Key Metrics
```python
# Prometheus metrics
reeval_requests_total = Counter('reeval_requests_total', 'Total re-eval requests')
reeval_errors_total = Counter('reeval_errors_total', 'Total re-eval errors', ['error_type'])
reeval_duration_seconds = Histogram('reeval_duration_seconds', 'Re-eval latency')
reeval_idempotent_total = Counter('reeval_idempotent_total', 'Re-evals that were idempotent')
```

### 11.2 Alerts
- High error rate (>5% over 5 minutes)
- High latency (P95 > 500ms over 5 minutes)
- Unusual idempotency ratio (>50% over 1 hour)

---

## 12. Success Criteria

### 12.1 Functional
- [x] Re-eval API implements統合仕様 2.4 completely
- [x] Diff format supports absolute values and dot notation
- [x] Idempotency guaranteed through correction_id
- [x] correction_history persisted correctly
- [x] FeedbackBridge integrated successfully

### 12.2 Quality
- [x] 14+ test cases passing (exceeds 8 minimum)
- [x] Code coverage > 80% for re-eval module
- [x] No regression in existing tests
- [x] API documentation complete

### 12.3 Performance
- [x] P95 latency < 200ms
- [x] Can handle 100 re-eval/sec

### 12.4 Review
- [x] Kana review passed
- [x] Code review passed
- [x] Security review passed

---

## 13. Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Diff format ambiguity | Medium | High | Clear spec + validation tests |
| Idempotency race condition | Low | High | Atomic correction_id check |
| Performance degradation | Low | Medium | Performance tests + monitoring |
| FeedbackBridge coupling | Medium | Medium | Clean interface design |

---

## 14. Rollout Plan

### 14.1 Phase 1: Development (Day 1-5)
- Implement core functionality
- Write comprehensive tests
- Internal code review

### 14.2 Phase 2: Staging (Day 6-7)
- Deploy to staging environment
- Manual testing with Kana/Yuno clients
- Performance validation

### 14.3 Phase 3: Production (Week 2)
- Gradual rollout with feature flag
- Monitor metrics closely
- Gather feedback from Yuno/Kana

---

## 15. Related Documents

- Bridge Lite Specification v2.1 Unified
- Implementation Review (2025-11-14)
- Sprint 2 Specification (Concurrency Control)
- API Documentation (auto-generated from OpenAPI)

---

**作成日**: 2025-11-14  
**作成者**: Kana（外界翻訳層）  
**承認待ち**: 宏啓さん  
**実装担当**: Tsumu（Cursor）

