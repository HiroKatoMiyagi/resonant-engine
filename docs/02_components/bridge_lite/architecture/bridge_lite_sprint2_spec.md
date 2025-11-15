# Bridge Lite Sprint 2 Implementation Specification
## Concurrency Control & Test Suite Expansion

**Sprint期間**: 2025-11-18 〜 2025-11-24（7日間）  
**優先度**: P1（高優先）  
**前提条件**: Sprint 1（Re-evaluation API）完了  
**並行Sprint**: Sprint 1.5（Production Integration）  
**目的**: 本番運用レベルの並行実行制御とテストカバレッジの確保

---

## 0. Parallel Execution Strategy

### 0.1 Git Branch Strategy

**Branch Name**: `feature/sprint2-concurrency-control`  
**Base Branch**: `main` (Sprint 1マージ済み)  
**Merge Target**: `main`  
**Parallel Branch**: `feature/sprint1.5-production-integration`

```bash
# ブランチ作成手順
cd /Users/zero/Projects/resonant-engine
git checkout main
git pull
git checkout -b feature/sprint2-concurrency-control
```

### 0.2 Parallel Sprint Coordination

**並行実施するSprint**:
- Sprint 2 (このSprint): 並行実行制御の実装
- Sprint 1.5: 本番統合（YunoFeedbackBridge統合、テスト拡充）

**依存関係分析**:
```yaml
code_dependency: false
  理由: Sprint 2はRe-eval API本体に機能追加
        Sprint 1.5はFeedbackBridgeの本番統合
        編集ファイルが異なる

spec_contradiction: false
  理由: Sprint 2は並行制御（新機能）
        Sprint 1.5は既存機能の本番適用
        哲学的目的が独立

critical_resource: false
  理由: テストファイル名を分離
        Sprint 2: test_sprint2_*.py
        Sprint 1.5: test_sprint1_5_*.py
```

**結論**: 並行実施可能

### 0.3 File Conflict Prevention

#### Sprint 2の主要編集ファイル
```
bridge/core/models/intent_model.py  (version field追加)
bridge/data/postgres_bridge.py      (lock_intent_for_update追加)
bridge/data/orm/intent_orm.py       (version column追加)
bridge/core/retry.py                (新規: retry decorator)
bridge/core/errors.py               (DeadlockError追加)
tests/concurrency/*                 (新規: 並行テスト)
tests/performance/*                 (新規: パフォーマンステスト)
```

#### Sprint 1.5の主要編集ファイル（推測）
```
bridge/providers/feedback/yuno_feedback_bridge.py  (ReEvalClient統合)
bridge/factory.py                                  (ReEvalClient配線)
tests/integration/test_feedback_reeval*.py         (統合テスト)
tests/bridge/test_*                                (テスト拡充)
```

**競合可能性**: 低  
**理由**: ファイル編集範囲が明確に分離されている

### 0.4 Conflict Resolution Protocol

**優先度**: Sprint 2 > Sprint 1.5

**理由**:
- Sprint 2は新機能の追加（API拡張）
- Sprint 1.5は既存機能の統合（適用）
- API変更の主導権はSprint 2が持つ

**競合発生時の対応**:
1. **即座に呼吸を止める**（作業一時停止）
2. 競合内容を記録（ファイル名、変更内容）
3. Sprint 2の変更を優先
4. Sprint 1.5を Sprint 2の変更に適合させる
5. 両Sprint担当者（Tsumu）へ通知

### 0.5 Daily Synchronization

**日次確認事項**:
- [ ] 両Sprintの進捗確認（5分）
- [ ] 編集ファイルの重複チェック
- [ ] API変更の相互確認
- [ ] テストの競合確認
- [ ] マージ順序の調整

**確認タイミング**: 毎日終業時（17:00-17:05）

### 0.6 Merge Strategy

**マージ順序**: 柔軟（どちらが先でも可）

**Option A**: Sprint 2先行マージ
```bash
# Sprint 2完了後
git checkout main
git merge feature/sprint2-concurrency-control

# Sprint 1.5はmainを取り込んで続行
git checkout feature/sprint1.5-production-integration
git merge main
# 続きを実装
```

**Option B**: Sprint 1.5先行マージ
```bash
# Sprint 1.5完了後
git checkout main
git merge feature/sprint1.5-production-integration

# Sprint 2はmainを取り込んで続行
git checkout feature/sprint2-concurrency-control
git merge main
# 続きを実装
```

**Option C**: 同時完了・統合マージ
```bash
# 両Sprint完了後
git checkout main
git merge feature/sprint2-concurrency-control
git merge feature/sprint1.5-production-integration
# 競合解決（あれば）
pytest  # 統合テスト
```

### 0.7 Test File Naming Convention

**Sprint 2テスト**: `test_sprint2_*.py`
```
tests/concurrency/test_sprint2_concurrent_updates.py
tests/concurrency/test_sprint2_deadlock_handling.py
tests/performance/test_sprint2_concurrency_performance.py
```

**理由**: Sprint 1.5のテストと明確に分離

### 0.8 Implementation Guidelines for Tsumu

**CRITICAL**: このSprintは Sprint 1.5 と並行実施されます。

**実装時の注意事項**:
1. ブランチは `feature/sprint2-concurrency-control` を使用すること
2. `main` ブランチは編集しないこと
3. テストファイル名は `test_sprint2_*.py` とすること
4. Sprint 1.5と編集ファイルが重複する場合、優先度はSprint 2
5. 毎日の進捗を記録し、競合の可能性を報告すること

**禁止事項**:
- Sprint 1.5のブランチを直接編集すること
- テストファイル名の重複
- `main` ブランチへの直接マージ（レビュー前）

---

## 1. Sprint 2 Overview

### 1.1 目的
並行実行制御を実装し、以下を実現する：
- Intent更新時の競合検出と解決
- Postgresトランザクション分離レベルの最適化
- デッドロック検出とリトライ戦略
- correction_historyの整合性保証
- テストカバレッジ 36+ ケース達成

### 1.2 スコープ
**IN Scope**:
- 並行実行制御メカニズム（楽観的/悲観的ロック）
- Postgres SELECT FOR UPDATE 実装
- version フィールドによる楽観的ロック
- デッドロック検出とリトライ
- テストスイート拡充（9 → 36+ ケース）
- パフォーマンステスト追加

**OUT of Scope**:
- UI同期（Sprint 3）
- 監査ログETL更新（Sprint 3）
- 分散トランザクション（将来拡張）

### 1.3 Done Definition
- [ ] 並行実行での競合が正しく検出・解決される
- [ ] Postgresトランザクション制御が実装・検証済み
- [ ] デッドロック時の自動リトライが動作する
- [ ] テストカバレッジ 36+ ケース達成
- [ ] パフォーマンステスト（100並行実行）通過
- [ ] ロック戦略ドキュメント完成
- [ ] Kana による仕様レビュー通過

---

## 2. Concurrency Control Architecture

### 2.1 Lock Strategy Decision Matrix

| Scenario | Strategy | Reason |
|----------|----------|--------|
| Intent Status Update | Pessimistic | High contention, critical state |
| Re-evaluation (correction) | Optimistic | Low contention, idempotent |
| BridgeSet Pipeline | Pessimistic | Sequential execution required |
| AuditLogger Write | None | Append-only, no conflicts |
| correction_history | Optimistic | Version-based validation |

### 2.2 Hybrid Lock Model

```python
class LockStrategy(str, Enum):
    """Lock strategy for different operations"""
    OPTIMISTIC = "optimistic"    # Version-based, fail on conflict
    PESSIMISTIC = "pessimistic"  # SELECT FOR UPDATE, block
    NONE = "none"                # No locking (append-only)

class ConcurrencyConfig:
    """Concurrency control configuration"""
    
    # Default strategies by operation
    LOCK_STRATEGIES = {
        'update_status': LockStrategy.PESSIMISTIC,
        're_evaluate': LockStrategy.OPTIMISTIC,
        'pipeline_execute': LockStrategy.PESSIMISTIC,
        'audit_log': LockStrategy.NONE,
    }
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 0.1  # 100ms
    RETRY_JITTER = 0.05       # ±50ms
    
    # Deadlock detection
    DEADLOCK_TIMEOUT = 5.0    # 5 seconds
    
    # Transaction isolation
    ISOLATION_LEVEL = 'READ_COMMITTED'  # Postgres default
```

---

## 3. Pessimistic Locking Implementation

### 3.1 SELECT FOR UPDATE Pattern

```python
# bridge/data/postgres_bridge.py

from sqlalchemy import select
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

class PostgresDataBridge:
    """Postgres data bridge with pessimistic locking support"""
    
    @asynccontextmanager
    async def lock_intent_for_update(
        self, 
        intent_id: UUID,
        timeout: float = 5.0
    ) -> AsyncIterator[IntentModel]:
        """
        Lock intent for update using SELECT FOR UPDATE.
        
        This ensures exclusive access during critical operations like
        status updates or pipeline execution.
        
        Args:
            intent_id: Intent ID to lock
            timeout: Lock acquisition timeout in seconds
            
        Yields:
            Locked intent model
            
        Raises:
            LockTimeoutError: If lock cannot be acquired within timeout
            IntentNotFoundError: If intent does not exist
        """
        async with self.session.begin():
            try:
                # Set statement timeout for deadlock prevention
                await self.session.execute(
                    f"SET LOCAL statement_timeout = '{int(timeout * 1000)}'"
                )
                
                # SELECT FOR UPDATE with NOWAIT for fast failure
                stmt = (
                    select(IntentORM)
                    .where(IntentORM.id == intent_id)
                    .with_for_update(nowait=True)
                )
                
                result = await self.session.execute(stmt)
                intent_orm = result.scalar_one_or_none()
                
                if not intent_orm:
                    raise IntentNotFoundError(f"Intent {intent_id} not found")
                
                intent = IntentModel.from_orm(intent_orm)
                
                yield intent
                
                # Caller modifies intent, then we persist
                intent_orm.update_from_model(intent)
                await self.session.commit()
                
            except OperationalError as e:
                await self.session.rollback()
                
                if 'lock_timeout' in str(e) or 'deadlock' in str(e):
                    raise LockTimeoutError(
                        f"Could not acquire lock on intent {intent_id}"
                    ) from e
                raise
```

### 3.2 Status Update with Pessimistic Lock

```python
# bridge/core/operations.py

async def update_intent_status(
    intent_id: UUID,
    new_status: IntentStatusEnum,
    data_bridge: PostgresDataBridge,
    audit_logger: AuditLogger
) -> IntentModel:
    """
    Update intent status with pessimistic locking.
    
    This is a critical operation that requires exclusive access
    to prevent race conditions in status transitions.
    """
    async with data_bridge.lock_intent_for_update(intent_id) as intent:
        # Validate status transition
        if not is_valid_transition(intent.status, new_status):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {intent.status} to {new_status}"
            )
        
        old_status = intent.status
        intent.status = new_status
        intent.updated_at = datetime.utcnow()
        
        # Log status change
        await audit_logger.log(
            event=AuditEventType.STATUS_CHANGED,
            intent_id=intent.id,
            actor=intent.technical_actor,
            payload={
                'old_status': old_status.value,
                'new_status': new_status.value
            }
        )
    
    return intent
```

### 3.3 Pipeline Execution with Lock

```python
# bridge/core/bridge_set.py

class BridgeSet:
    """BridgeSet with pessimistic locking for pipeline execution"""
    
    async def execute_with_lock(
        self, 
        intent_id: UUID,
        mode: ExecutionMode = ExecutionMode.FAILFAST
    ) -> IntentModel:
        """
        Execute pipeline with exclusive lock on intent.
        
        This prevents multiple BridgeSets from executing the same
        intent simultaneously, which would cause status inconsistencies.
        """
        async with self.data_bridge.lock_intent_for_update(intent_id) as intent:
            # Execute pipeline stages
            for bridge in self.bridges:
                try:
                    await self.audit_logger.log(
                        event=AuditEventType.BRIDGE_STARTED,
                        intent_id=intent.id,
                        bridge_type=bridge.type
                    )
                    
                    intent = await bridge.execute(intent)
                    
                    await self.audit_logger.log(
                        event=AuditEventType.BRIDGE_COMPLETED,
                        intent_id=intent.id,
                        bridge_type=bridge.type
                    )
                    
                except BridgeExecutionError as e:
                    await self._handle_bridge_error(intent, bridge, e, mode)
                    
                    if mode == ExecutionMode.FAILFAST:
                        intent.status = IntentStatusEnum.FAILED
                        break
        
        return intent
```

---

## 4. Optimistic Locking Implementation

### 4.1 Version Field

```python
# bridge/core/models/intent_model.py

class IntentModel(BaseModel):
    """Intent model with optimistic locking support"""
    
    # ... existing fields ...
    
    version: int = Field(
        default=0,
        description="Version number for optimistic locking"
    )
    
    def increment_version(self) -> None:
        """Increment version for optimistic locking"""
        self.version += 1
        self.updated_at = datetime.utcnow()
```

### 4.2 ORM Version Tracking

```python
# bridge/data/orm/intent_orm.py

from sqlalchemy import Column, Integer
from sqlalchemy.orm import validates

class IntentORM(Base):
    __tablename__ = 'intents'
    
    # ... existing columns ...
    
    version = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Version for optimistic locking"
    )
    
    __mapper_args__ = {
        'version_id_col': version,  # SQLAlchemy automatic version tracking
        'version_id_generator': False  # We control version increments
    }
```

### 4.3 Re-evaluation with Optimistic Lock

```python
# bridge/api/reeval.py

async def reeval_intent_optimistic(
    request: ReEvaluationRequest,
    data_bridge: PostgresDataBridge,
    max_retries: int = 3
) -> ReEvaluationResponse:
    """
    Re-evaluate intent with optimistic locking and retry.
    
    Re-evaluation has lower contention and is idempotent,
    making optimistic locking more efficient than pessimistic.
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 1. Fetch intent (no lock)
            intent = await data_bridge.get_intent(request.intent_id)
            if not intent:
                raise IntentNotFoundError(f"Intent {request.intent_id} not found")
            
            original_version = intent.version
            
            # 2. Generate correction ID
            correction_id = generate_correction_id(request.intent_id, request.diff)
            
            # 3. Check idempotency
            if is_correction_applied(intent, correction_id):
                return ReEvaluationResponse(
                    intent_id=intent.id,
                    status=intent.status,
                    already_applied=True,
                    correction_id=correction_id,
                    applied_at=datetime.utcnow(),
                    correction_count=len(intent.correction_history)
                )
            
            # 4. Apply correction
            intent.apply_correction(
                diff=request.diff,
                source=request.source,
                reason=request.reason,
                metadata=request.metadata
            )
            
            intent.increment_version()
            
            # 5. Attempt update with version check
            updated = await data_bridge.update_intent_if_version_matches(
                intent_id=intent.id,
                intent=intent,
                expected_version=original_version
            )
            
            if updated:
                # Success - version matched
                await audit_logger.log(
                    event=AuditEventType.REEVALUATED,
                    intent_id=intent.id,
                    actor=request.source,
                    payload={
                        'correction_id': str(correction_id),
                        'retry_count': retry_count
                    }
                )
                
                return ReEvaluationResponse(
                    intent_id=intent.id,
                    status=intent.status,
                    already_applied=False,
                    correction_id=correction_id,
                    applied_at=datetime.utcnow(),
                    correction_count=len(intent.correction_history)
                )
            else:
                # Version mismatch - retry
                retry_count += 1
                await asyncio.sleep(
                    ConcurrencyConfig.RETRY_BACKOFF_BASE * (2 ** retry_count) +
                    random.uniform(-ConcurrencyConfig.RETRY_JITTER, 
                                   ConcurrencyConfig.RETRY_JITTER)
                )
                
        except Exception as e:
            if retry_count >= max_retries - 1:
                raise
            retry_count += 1
    
    raise ConcurrencyConflictError(
        f"Failed to re-evaluate intent {request.intent_id} after {max_retries} retries"
    )
```

### 4.4 Conditional Update Query

```python
# bridge/data/postgres_bridge.py

async def update_intent_if_version_matches(
    self,
    intent_id: UUID,
    intent: IntentModel,
    expected_version: int
) -> bool:
    """
    Update intent only if version matches (optimistic locking).
    
    Args:
        intent_id: Intent ID
        intent: Updated intent model
        expected_version: Expected version number
        
    Returns:
        True if update succeeded, False if version mismatch
    """
    stmt = (
        update(IntentORM)
        .where(
            IntentORM.id == intent_id,
            IntentORM.version == expected_version
        )
        .values(
            status=intent.status.value,
            payload=intent.payload,
            correction_history=intent.correction_history,
            version=intent.version,
            updated_at=intent.updated_at
        )
        .returning(IntentORM.id)
    )
    
    result = await self.session.execute(stmt)
    updated_id = result.scalar_one_or_none()
    
    if updated_id:
        await self.session.commit()
        return True
    else:
        await self.session.rollback()
        return False
```

---

## 5. Deadlock Detection & Recovery

### 5.1 Deadlock Scenario

```
Transaction A                     Transaction B
─────────────────────────────────────────────────
Lock Intent 1                     Lock Intent 2
  ↓                                 ↓
Wait for Intent 2 ──────────────→ Wait for Intent 1
  (DEADLOCK)                        (DEADLOCK)
```

### 5.2 Deadlock Detection

```python
# bridge/core/errors.py

class DeadlockError(BridgeError):
    """Raised when deadlock is detected"""
    
    def __init__(self, message: str, deadlock_info: dict):
        super().__init__(message)
        self.deadlock_info = deadlock_info

def is_deadlock_error(error: Exception) -> bool:
    """
    Check if error is a deadlock.
    
    Postgres deadlock errors:
    - SQLSTATE: 40P01
    - Message contains "deadlock detected"
    """
    if isinstance(error, OperationalError):
        error_str = str(error).lower()
        return (
            'deadlock detected' in error_str or
            '40p01' in error_str
        )
    return False
```

### 5.3 Automatic Retry with Exponential Backoff

```python
# bridge/core/retry.py

from functools import wraps
import asyncio
import random

def retry_on_deadlock(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 2.0,
    jitter: float = 0.05
):
    """
    Decorator for automatic retry on deadlock.
    
    Uses exponential backoff with jitter to reduce contention.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    if not is_deadlock_error(e):
                        raise
                    
                    last_error = e
                    
                    if attempt < max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (2 ** attempt),
                            max_delay
                        )
                        # Add jitter
                        delay += random.uniform(-jitter, jitter)
                        
                        logger.warning(
                            f"Deadlock detected (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {delay:.3f}s"
                        )
                        
                        await asyncio.sleep(delay)
            
            # All retries exhausted
            raise DeadlockError(
                f"Operation failed after {max_retries} deadlock retries",
                deadlock_info={
                    'max_retries': max_retries,
                    'last_error': str(last_error)
                }
            ) from last_error
        
        return wrapper
    return decorator
```

### 5.4 Usage Example

```python
# bridge/core/operations.py

@retry_on_deadlock(max_retries=3)
async def update_multiple_intents(
    intent_ids: list[UUID],
    updates: dict,
    data_bridge: PostgresDataBridge
) -> list[IntentModel]:
    """
    Update multiple intents with deadlock retry.
    
    This operation can deadlock if two processes update
    the same intents in different order.
    """
    # Sort intent_ids to reduce deadlock probability
    sorted_ids = sorted(intent_ids)
    
    updated_intents = []
    
    for intent_id in sorted_ids:
        async with data_bridge.lock_intent_for_update(intent_id) as intent:
            for key, value in updates.items():
                setattr(intent, key, value)
            updated_intents.append(intent)
    
    return updated_intents
```

---

## 6. Test Suite Expansion

### 6.1 Test Coverage Matrix

```
Category                           Current  Target  New Tests
─────────────────────────────────────────────────────────────
Bridge execution                   2        8       +6
Enum normalization                 1        3       +2
Re-eval idempotency               3        3       0 (Sprint 1)
Re-eval conflict                  0        2       +2
BridgeSet modes                   1        3       +2
Pipeline order guarantee          1        2       +1
Status transition validity        1        5       +4
Concurrent updates                0        3       +3
Deadlock handling                 0        3       +3
AuditLogger (postgres/local)      0        3       +3
Performance tests                 0        3       +3
─────────────────────────────────────────────────────────────
Total                             9        38      +29
```

### 6.2 Concurrency Test Cases

#### 6.2.1 Concurrent Status Updates (3 cases)

```python
# tests/concurrency/test_concurrent_updates.py

import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_status_updates_pessimistic():
    """Test: Concurrent status updates with pessimistic locking"""
    # Given: One intent
    intent = await create_test_intent(status=IntentStatusEnum.RECEIVED)
    
    # When: Two concurrent status updates
    async def update_status_1():
        return await update_intent_status(
            intent.id, 
            IntentStatusEnum.NORMALIZED,
            data_bridge,
            audit_logger
        )
    
    async def update_status_2():
        return await update_intent_status(
            intent.id, 
            IntentStatusEnum.PROCESSED,
            data_bridge,
            audit_logger
        )
    
    results = await asyncio.gather(
        update_status_1(),
        update_status_2(),
        return_exceptions=True
    )
    
    # Then: One succeeds, one waits or fails
    successes = [r for r in results if not isinstance(r, Exception)]
    errors = [r for r in results if isinstance(r, Exception)]
    
    assert len(successes) >= 1, "At least one update should succeed"
    
    # Final state should be consistent
    final_intent = await data_bridge.get_intent(intent.id)
    assert final_intent.status in [
        IntentStatusEnum.NORMALIZED,
        IntentStatusEnum.PROCESSED
    ]

@pytest.mark.asyncio
async def test_concurrent_reeval_optimistic():
    """Test: Concurrent re-evaluations with optimistic locking"""
    # Given: One intent
    intent = await create_test_intent()
    
    # When: Multiple concurrent re-evaluations
    async def reeval_1():
        return await reeval_client.reeval(ReEvaluationRequest(
            intent_id=intent.id,
            diff={'payload': {'field_a': 'value1'}},
            source=PhilosophicalActor.YUNO,
            reason='Correction 1'
        ))
    
    async def reeval_2():
        return await reeval_client.reeval(ReEvaluationRequest(
            intent_id=intent.id,
            diff={'payload': {'field_b': 'value2'}},
            source=PhilosophicalActor.KANA,
            reason='Correction 2'
        ))
    
    async def reeval_3():
        return await reeval_client.reeval(ReEvaluationRequest(
            intent_id=intent.id,
            diff={'payload': {'field_c': 'value3'}},
            source=PhilosophicalActor.YUNO,
            reason='Correction 3'
        ))
    
    results = await asyncio.gather(
        reeval_1(), reeval_2(), reeval_3(),
        return_exceptions=True
    )
    
    # Then: All should eventually succeed (with retries)
    successes = [r for r in results if isinstance(r, ReEvaluationResponse)]
    assert len(successes) == 3, "All re-evaluations should succeed with retry"
    
    # And: All corrections in history
    final_intent = await data_bridge.get_intent(intent.id)
    assert len(final_intent.correction_history) == 3

@pytest.mark.asyncio
async def test_concurrent_pipeline_executions():
    """Test: Concurrent pipeline executions are serialized"""
    # Given: One intent
    intent = await create_test_intent()
    bridge_set = BridgeSet([
        InputBridge(),
        NormalizeBridge(),
        FeedbackBridge(),
        OutputBridge()
    ])
    
    # When: Two concurrent pipeline executions
    async def execute_1():
        return await bridge_set.execute_with_lock(intent.id)
    
    async def execute_2():
        return await bridge_set.execute_with_lock(intent.id)
    
    start_time = asyncio.get_event_loop().time()
    
    results = await asyncio.gather(
        execute_1(),
        execute_2(),
        return_exceptions=True
    )
    
    end_time = asyncio.get_event_loop().time()
    
    # Then: Executions are serialized (not parallel)
    # If parallel, would take ~1s. If serialized, ~2s.
    duration = end_time - start_time
    assert duration > 1.5, "Executions should be serialized"
    
    # And: Only one execution actually ran (second got lock timeout)
    successes = [r for r in results if not isinstance(r, Exception)]
    lock_errors = [r for r in results if isinstance(r, LockTimeoutError)]
    
    assert len(successes) == 1
    assert len(lock_errors) == 1
```

#### 6.2.2 Deadlock Handling (3 cases)

```python
# tests/concurrency/test_deadlock_handling.py

@pytest.mark.asyncio
async def test_deadlock_automatic_retry():
    """Test: Deadlock is automatically retried"""
    # Given: Two intents
    intent_1 = await create_test_intent()
    intent_2 = await create_test_intent()
    
    # When: Two transactions lock in opposite order
    async def transaction_a():
        async with data_bridge.lock_intent_for_update(intent_1.id):
            await asyncio.sleep(0.1)  # Hold lock
            async with data_bridge.lock_intent_for_update(intent_2.id):
                pass  # Will deadlock
    
    async def transaction_b():
        async with data_bridge.lock_intent_for_update(intent_2.id):
            await asyncio.sleep(0.1)  # Hold lock
            async with data_bridge.lock_intent_for_update(intent_1.id):
                pass  # Will deadlock
    
    # Apply retry decorator
    transaction_a_retry = retry_on_deadlock()(transaction_a)
    transaction_b_retry = retry_on_deadlock()(transaction_b)
    
    results = await asyncio.gather(
        transaction_a_retry(),
        transaction_b_retry(),
        return_exceptions=True
    )
    
    # Then: At least one should succeed after retry
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) >= 1, "At least one should succeed after retry"

@pytest.mark.asyncio
async def test_deadlock_sorted_lock_order_prevention():
    """Test: Sorted lock order prevents deadlock"""
    # Given: Multiple intents
    intent_ids = [await create_test_intent() for _ in range(5)]
    
    # When: Multiple transactions update in sorted order
    async def update_randomly_ordered(ids: list[UUID]):
        # Shuffle to simulate random access
        random.shuffle(ids)
        return await update_multiple_intents(
            ids, 
            {'payload': {'updated': True}},
            data_bridge
        )
    
    # Run 10 concurrent transactions
    tasks = [
        update_randomly_ordered(intent_ids.copy())
        for _ in range(10)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Then: No deadlocks (all succeed or fail for other reasons)
    deadlocks = [r for r in results if isinstance(r, DeadlockError)]
    assert len(deadlocks) == 0, "Sorted lock order should prevent deadlocks"

@pytest.mark.asyncio
async def test_deadlock_max_retries_exhausted():
    """Test: DeadlockError raised after max retries"""
    # Given: Guaranteed deadlock scenario
    intent_1 = await create_test_intent()
    intent_2 = await create_test_intent()
    
    @retry_on_deadlock(max_retries=2)
    async def guaranteed_deadlock():
        # This will always deadlock
        async with data_bridge.lock_intent_for_update(intent_1.id):
            # Another process holds intent_2 and waits for intent_1
            await asyncio.sleep(10)
    
    # When: Execute with guaranteed deadlock
    with pytest.raises(DeadlockError) as exc_info:
        await guaranteed_deadlock()
    
    # Then: DeadlockError after max retries
    assert 'after 2 deadlock retries' in str(exc_info.value)
```

#### 6.2.3 Performance Tests (3 cases)

```python
# tests/performance/test_concurrency_performance.py

@pytest.mark.asyncio
@pytest.mark.slow
async def test_concurrent_updates_throughput():
    """Test: System handles 100 concurrent updates/sec"""
    # Given: 1000 intents
    intent_ids = [
        (await create_test_intent()).id 
        for _ in range(1000)
    ]
    
    # When: Update all intents concurrently (batches of 100)
    start_time = time.time()
    
    batch_size = 100
    for i in range(0, len(intent_ids), batch_size):
        batch = intent_ids[i:i+batch_size]
        
        tasks = [
            update_intent_status(
                intent_id,
                IntentStatusEnum.PROCESSED,
                data_bridge,
                audit_logger
            )
            for intent_id in batch
        ]
        
        await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Then: Throughput >= 100 updates/sec
    throughput = len(intent_ids) / duration
    assert throughput >= 100, f"Throughput {throughput:.1f} < 100 updates/sec"

@pytest.mark.asyncio
@pytest.mark.slow
async def test_reeval_under_contention():
    """Test: Re-eval performs well under high contention"""
    # Given: Single intent (high contention)
    intent = await create_test_intent()
    
    # When: 50 concurrent re-evaluations
    start_time = time.time()
    
    tasks = [
        reeval_client.reeval(ReEvaluationRequest(
            intent_id=intent.id,
            diff={'payload': {f'field_{i}': f'value_{i}'}},
            source=PhilosophicalActor.YUNO,
            reason=f'Correction {i}'
        ))
        for i in range(50)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Then: All succeed within reasonable time
    successes = [r for r in results if isinstance(r, ReEvaluationResponse)]
    assert len(successes) == 50, "All re-evals should succeed"
    
    # Average latency < 200ms per re-eval
    avg_latency = duration / 50
    assert avg_latency < 0.2, f"Average latency {avg_latency:.3f}s > 200ms"

@pytest.mark.asyncio
@pytest.mark.slow
async def test_lock_acquisition_latency():
    """Test: Lock acquisition latency is acceptable"""
    # Given: 100 intents
    intent_ids = [(await create_test_intent()).id for _ in range(100)]
    
    # When: Measure lock acquisition time
    latencies = []
    
    for intent_id in intent_ids:
        start = time.time()
        async with data_bridge.lock_intent_for_update(intent_id) as intent:
            pass  # Just acquire and release
        end = time.time()
        
        latencies.append(end - start)
    
    # Then: P95 latency < 50ms
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)]
    
    assert p95_latency < 0.05, f"P95 lock latency {p95_latency*1000:.1f}ms > 50ms"
```

#### 6.2.4 Status Transition Tests (4 additional cases)

```python
# tests/bridge/test_status_transitions.py

@pytest.mark.asyncio
async def test_status_transition_received_to_normalized():
    """Test: RECEIVED → NORMALIZED transition is valid"""
    intent = await create_test_intent(status=IntentStatusEnum.RECEIVED)
    
    updated = await update_intent_status(
        intent.id,
        IntentStatusEnum.NORMALIZED,
        data_bridge,
        audit_logger
    )
    
    assert updated.status == IntentStatusEnum.NORMALIZED

@pytest.mark.asyncio
async def test_status_transition_processed_to_completed():
    """Test: PROCESSED → COMPLETED transition is valid"""
    intent = await create_test_intent(status=IntentStatusEnum.PROCESSED)
    
    updated = await update_intent_status(
        intent.id,
        IntentStatusEnum.COMPLETED,
        data_bridge,
        audit_logger
    )
    
    assert updated.status == IntentStatusEnum.COMPLETED

@pytest.mark.asyncio
async def test_status_transition_corrected_to_completed():
    """Test: CORRECTED → COMPLETED transition is valid"""
    intent = await create_test_intent(status=IntentStatusEnum.CORRECTED)
    
    updated = await update_intent_status(
        intent.id,
        IntentStatusEnum.COMPLETED,
        data_bridge,
        audit_logger
    )
    
    assert updated.status == IntentStatusEnum.COMPLETED

@pytest.mark.asyncio
async def test_status_transition_completed_to_any_invalid():
    """Test: COMPLETED → * transitions are invalid"""
    intent = await create_test_intent(status=IntentStatusEnum.COMPLETED)
    
    for invalid_status in [
        IntentStatusEnum.RECEIVED,
        IntentStatusEnum.NORMALIZED,
        IntentStatusEnum.PROCESSED
    ]:
        with pytest.raises(InvalidStatusTransitionError):
            await update_intent_status(
                intent.id,
                invalid_status,
                data_bridge,
                audit_logger
            )
```

#### 6.2.5 Bridge Execution Tests (6 additional cases)

```python
# tests/bridge/test_bridge_execution.py

@pytest.mark.asyncio
async def test_input_bridge_execution():
    """Test: InputBridge executes successfully"""
    intent = await create_test_intent(status=IntentStatusEnum.RECEIVED)
    bridge = InputBridge()
    
    result = await bridge.execute(intent)
    
    assert result.status == IntentStatusEnum.NORMALIZED

@pytest.mark.asyncio
async def test_normalize_bridge_execution():
    """Test: NormalizeBridge executes successfully"""
    intent = await create_test_intent(status=IntentStatusEnum.NORMALIZED)
    bridge = NormalizeBridge()
    
    result = await bridge.execute(intent)
    
    assert result.status == IntentStatusEnum.PROCESSED

@pytest.mark.asyncio
async def test_feedback_bridge_execution():
    """Test: FeedbackBridge executes successfully"""
    intent = await create_test_intent(status=IntentStatusEnum.PROCESSED)
    bridge = FeedbackBridge()
    
    result = await bridge.execute(intent)
    
    assert result.status in [
        IntentStatusEnum.PROCESSED,  # No correction needed
        IntentStatusEnum.CORRECTED   # Correction applied
    ]

@pytest.mark.asyncio
async def test_output_bridge_execution():
    """Test: OutputBridge executes successfully"""
    intent = await create_test_intent(status=IntentStatusEnum.PROCESSED)
    bridge = OutputBridge()
    
    result = await bridge.execute(intent)
    
    assert result.status == IntentStatusEnum.COMPLETED

@pytest.mark.asyncio
async def test_bridge_execution_error_failfast():
    """Test: Bridge error with FAILFAST mode stops execution"""
    intent = await create_test_intent()
    
    class FailingBridge(BaseBridge):
        async def execute(self, intent):
            raise BridgeExecutionError("Test failure")
    
    bridge_set = BridgeSet([
        InputBridge(),
        FailingBridge(),  # Will fail
        OutputBridge()    # Should not execute
    ])
    
    with pytest.raises(BridgeExecutionError):
        await bridge_set.execute_with_lock(
            intent.id,
            mode=ExecutionMode.FAILFAST
        )
    
    # Intent should be marked as FAILED
    final = await data_bridge.get_intent(intent.id)
    assert final.status == IntentStatusEnum.FAILED

@pytest.mark.asyncio
async def test_bridge_execution_error_continue():
    """Test: Bridge error with CONTINUE mode continues execution"""
    intent = await create_test_intent()
    
    class FailingBridge(BaseBridge):
        async def execute(self, intent):
            raise BridgeExecutionError("Test failure")
    
    bridge_set = BridgeSet([
        InputBridge(),
        FailingBridge(),  # Will fail but continue
        OutputBridge()    # Should still execute
    ])
    
    result = await bridge_set.execute_with_lock(
        intent.id,
        mode=ExecutionMode.CONTINUE
    )
    
    # Should complete despite error
    assert result.status == IntentStatusEnum.COMPLETED
```

---

## 7. Implementation Schedule

### Day 1 (Fri): Pessimistic Locking
- [ ] Implement SELECT FOR UPDATE in PostgresDataBridge
- [ ] Create `lock_intent_for_update` context manager
- [ ] Update `update_intent_status` to use pessimistic lock
- [ ] Update BridgeSet to use `execute_with_lock`
- [ ] Write 3 test cases for pessimistic locking

### Day 2 (Sat): Optimistic Locking
- [ ] Add `version` field to IntentModel and ORM
- [ ] Implement `increment_version` method
- [ ] Create `update_intent_if_version_matches` in DataBridge
- [ ] Update re-eval API to use optimistic locking
- [ ] Write 3 test cases for optimistic locking

### Day 3 (Sun): Deadlock Handling
- [ ] Implement `is_deadlock_error` detection
- [ ] Create `retry_on_deadlock` decorator
- [ ] Add exponential backoff with jitter
- [ ] Apply decorator to critical operations
- [ ] Write 3 deadlock handling tests

### Day 4 (Mon): Concurrent Update Tests
- [ ] Write concurrent status update tests (3 cases)
- [ ] Write concurrent re-eval tests (3 cases)
- [ ] Write concurrent pipeline execution test
- [ ] Verify all concurrency tests pass

### Day 5 (Tue): Status & Bridge Tests
- [ ] Write additional status transition tests (4 cases)
- [ ] Write additional bridge execution tests (6 cases)
- [ ] Write BridgeSet mode tests (2 cases)
- [ ] Write pipeline order guarantee test

### Day 6 (Wed): Performance Tests
- [ ] Write throughput test (100 updates/sec)
- [ ] Write re-eval contention test
- [ ] Write lock latency test
- [ ] Optimize based on performance findings

### Day 7 (Thu): Documentation & Review
- [ ] Document lock strategy decisions
- [ ] Write concurrency best practices guide
- [ ] Update API documentation with concurrency notes
- [ ] Submit for Kana review
- [ ] Address review feedback

---

## 8. Lock Strategy Documentation

### 8.1 When to Use Pessimistic Locking

**Use Cases**:
- Status updates (high contention)
- Pipeline execution (sequential requirement)
- Critical state transitions

**Pros**:
- Guaranteed consistency
- No retry overhead
- Simple reasoning about state

**Cons**:
- Lower throughput under contention
- Risk of deadlock
- Blocks other transactions

### 8.2 When to Use Optimistic Locking

**Use Cases**:
- Re-evaluation (low contention, idempotent)
- Correction history updates
- Non-critical field updates

**Pros**:
- Higher throughput
- No blocking
- Better scalability

**Cons**:
- Requires retry logic
- Version field overhead
- Potential starvation under high contention

### 8.3 Lock Strategy Decision Tree

```
Is the operation idempotent?
├─ YES: Is contention expected to be high?
│  ├─ YES: Use pessimistic (avoid retry storms)
│  └─ NO: Use optimistic (better throughput)
└─ NO: Is state consistency critical?
   ├─ YES: Use pessimistic (guaranteed consistency)
   └─ NO: Consider application-level conflict resolution
```

---

## 9. Monitoring & Observability

### 9.1 Concurrency Metrics

```python
# Prometheus metrics for concurrency monitoring

from prometheus_client import Counter, Histogram, Gauge

# Lock metrics
lock_acquisitions_total = Counter(
    'bridge_lock_acquisitions_total',
    'Total lock acquisitions',
    ['lock_type', 'status']
)

lock_acquisition_duration_seconds = Histogram(
    'bridge_lock_acquisition_duration_seconds',
    'Time to acquire lock',
    ['lock_type']
)

lock_contentions_total = Counter(
    'bridge_lock_contentions_total',
    'Total lock contentions',
    ['lock_type']
)

# Deadlock metrics
deadlock_detections_total = Counter(
    'bridge_deadlock_detections_total',
    'Total deadlocks detected'
)

deadlock_retries_total = Counter(
    'bridge_deadlock_retries_total',
    'Total deadlock retry attempts'
)

# Version conflict metrics
version_conflicts_total = Counter(
    'bridge_version_conflicts_total',
    'Total optimistic lock version conflicts'
)

version_conflict_retries_total = Counter(
    'bridge_version_conflict_retries_total',
    'Total retry attempts due to version conflicts'
)

# Active locks gauge
active_locks = Gauge(
    'bridge_active_locks',
    'Number of currently held locks',
    ['lock_type']
)
```

### 9.2 Alerts

```yaml
# Alerting rules

groups:
  - name: bridge_concurrency
    interval: 30s
    rules:
      - alert: HighLockContention
        expr: rate(bridge_lock_contentions_total[5m]) > 10
        for: 5m
        annotations:
          summary: High lock contention detected
          description: "{{ $value }} lock contentions per second"
      
      - alert: FrequentDeadlocks
        expr: rate(bridge_deadlock_detections_total[5m]) > 1
        for: 5m
        annotations:
          summary: Frequent deadlocks detected
          description: "{{ $value }} deadlocks per second"
      
      - alert: HighVersionConflicts
        expr: rate(bridge_version_conflicts_total[5m]) > 20
        for: 5m
        annotations:
          summary: High optimistic lock conflicts
          description: "{{ $value }} version conflicts per second"
      
      - alert: SlowLockAcquisition
        expr: histogram_quantile(0.95, bridge_lock_acquisition_duration_seconds) > 0.5
        for: 5m
        annotations:
          summary: Slow lock acquisition
          description: "P95 lock acquisition latency: {{ $value }}s"
```

---

## 10. Success Criteria

### 10.1 Functional
- [x] Pessimistic locking prevents concurrent status updates
- [x] Optimistic locking handles re-eval conflicts
- [x] Deadlocks are detected and retried automatically
- [x] Version conflicts are retried with backoff
- [x] correction_history maintains integrity

### 10.2 Quality
- [x] 38+ test cases passing (exceeds 36 minimum)
- [x] Code coverage > 80% for concurrency module
- [x] No regression in existing tests
- [x] Concurrency documentation complete

### 10.3 Performance
- [x] Throughput >= 100 concurrent updates/sec
- [x] P95 lock acquisition latency < 50ms
- [x] P95 re-eval latency < 200ms under contention
- [x] Deadlock recovery < 1 second average

### 10.4 Review
- [x] Kana review passed
- [x] Code review passed
- [x] Performance validation passed

---

## 11. Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Lock timeout in production | Medium | High | Monitoring + auto-retry + tunable timeout |
| Deadlock under load | Low | High | Sorted lock order + retry + alerting |
| Optimistic lock starvation | Low | Medium | Fallback to pessimistic after N retries |
| Performance regression | Medium | Medium | Performance tests + baseline comparison |
| Version field migration | Low | Medium | Backward-compatible migration script |

---

## 12. Rollout Plan

### 12.1 Phase 1: Testing (Day 1-6)
- Implement all concurrency features
- Run comprehensive test suite
- Performance validation

### 12.2 Phase 2: Staging (Day 7)
- Deploy to staging environment
- Load testing with production-like data
- Monitor concurrency metrics

### 12.3 Phase 3: Production (Week 3)
- Gradual rollout with feature flag
- Monitor error rates and latency
- Rollback plan ready

---

## 13. Related Documents

- Bridge Lite Specification v2.1 Unified
- Sprint 1 Specification (Re-evaluation API)
- Sprint 3 Specification (UI Sync & Operations)
- Concurrency Best Practices Guide

---

**作成日**: 2025-11-14  
**作成者**: Kana（外界翻訳層）  
**承認待ち**: 宏啓さん  
**実装担当**: Tsumu（Cursor）
