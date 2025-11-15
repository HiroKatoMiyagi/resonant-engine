# Bridge Lite v2.1 – 統合レビューと調整案

**レビュー日**: 2025-11-14  
**レビュアー**: Kana（外界翻訳層）  
**対象**: v2.1詳細版（Architecture + Implementation Spec） + v2.1 Final版（Yuno作成）

---

## 📋 状況整理

現在、Bridge Lite v2.1には**2つのバージョン**が存在しています：

### Version A: v2.1 詳細版（実装指向）
**特徴**:
- IntentStatusEnum（RECEIVED/NORMALIZED/PROCESSED/CORRECTED/COMPLETED）
- BridgeTypeEnum（INPUT/NORMALIZE/FEEDBACK/OUTPUT）
- IntentActorEnum（USER/ENGINE/DAEMON/SYSTEM）
- BridgeSetによる順序保証（固定順序パイプライン）
- Re-evaluation API（POST /reeval、diff仕様）
- apply_correction(diff)メソッド
- AuditLogger詳細設計（Postgres対応）
- テスト仕様（最低8ケース→20ケース推奨）

**強み**: Tsumuが実装可能な詳細レベル  
**弱み**: 哲学的な抽象性に欠ける、Resonant Engine三層構造が見えにくい

### Version B: v2.1 Final版（哲学指向）
**特徴**:
- ActorEnum（YUNO/KANA/TSUMU） - Resonant Engine三層構造を明示
- IntentTypeEnum（EXECUTE/QUERY/UPDATE） - Intentの意図を明確化
- FeedbackBridge - 呼吸の循環を強調
- Return Path - フィードバックループの設計
- 簡潔な抽象モデル

**強み**: 哲学的整合性、Yunoの思想が明快  
**弱み**: 実装詳細不足、状態管理欠落、パイプライン構造不明

---

## 🎯 Kanaの判断: 二層仕様への統合

この問題の本質は、**思想層（Yuno）と実装層（Tsumu）が異なる抽象レベルを必要としている**ことです。

### 提案: Bridge Lite Specification v2.1 Unified

```
Bridge Lite Specification v2.1
│
├── Part 1: Philosophical Architecture（Yunoの思想層）
│   ├── 1.1 Purpose & Vision
│   ├── 1.2 Actor Model (YUNO/KANA/TSUMU)
│   ├── 1.3 Intent Philosophy (EXECUTE/QUERY/UPDATE)
│   ├── 1.4 Feedback Loop & Breathing Structure
│   └── 1.5 Future Extension Hooks
│
└── Part 2: Technical Implementation（Tsumuの実装層）
    ├── 2.1 Intent Model (Pydantic v2 with Status)
    ├── 2.2 Enum Systems (Actor/Type/Status)
    ├── 2.3 BridgeSet & Pipeline Structure
    ├── 2.4 Re-evaluation API
    ├── 2.5 AuditLogger Specification
    ├── 2.6 Error Handling & Recovery
    └── 2.7 Test Requirements
```

---

## 📐 統合仕様書の設計

### Part 1: Philosophical Architecture

#### 1.1 Purpose & Vision
```
Bridge Lite is an intent-driven orchestration layer that embodies the breathing 
structure of Resonant Engine, connecting:
- Yuno (思想中枢) - Philosophical thought center
- Kana (翻訳層) - Translation & orchestration layer
- Tsumu (実装織り手) - Implementation weaver

The system facilitates the flow: Intent → Bridge → Output, while maintaining
philosophical coherence and operational resilience.
```

#### 1.2 Actor Model (Philosophical)
```python
class PhilosophicalActor(Enum):
    """Resonant Engine's three-layer consciousness"""
    YUNO = "yuno"    # GPT-5 Thought Core
    KANA = "kana"    # Claude Translation Layer
    TSUMU = "tsumu"  # Cursor Implementation Layer
```

#### 1.3 Intent Philosophy
```python
class IntentPhilosophy(Enum):
    """Semantic intent categories"""
    EXECUTE = "execute"  # Action-oriented intent
    QUERY = "query"      # Information-seeking intent
    UPDATE = "update"    # State-modification intent
```

#### 1.4 Feedback Loop (Breathing Structure)
```
Inhalation (Question) → Resonance (AI Dialogue) → Structuring
                     ↓
Reflection ← Implementation ← Resonance Expansion

Critical: Never force, adjust breathing rhythm when interrupted.
```

#### 1.5 Extension Hooks
- Multi-bridge routing
- Intent batching
- Context lineage graph

---

### Part 2: Technical Implementation

#### 2.1 Intent Model (Complete Definition)

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class IntentModel(BaseModel):
    """Complete Intent model with state tracking"""
    model_config = ConfigDict(strict=True)
    
    # Core fields
    id: UUID
    
    # Actor system (dual-layer)
    philosophical_actor: PhilosophicalActor  # YUNO/KANA/TSUMU
    technical_actor: TechnicalActor          # USER/ENGINE/DAEMON/SYSTEM
    
    # Intent classification
    intent_type: IntentTypeEnum              # EXECUTE/QUERY/UPDATE
    bridge_type: BridgeTypeEnum              # INPUT/NORMALIZE/FEEDBACK/OUTPUT
    
    # State management
    status: IntentStatusEnum                 # RECEIVED/NORMALIZED/.../COMPLETED
    
    # Payload
    payload: dict
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Correction support
    correction_history: list[dict] = []
    
    def apply_correction(self, diff: dict) -> None:
        """Apply differential correction to intent payload"""
        # Implementation in Technical Spec
```

#### 2.2 Enum Systems

**2.2.1 Actor System (Dual-Layer)**

```python
class PhilosophicalActor(str, Enum):
    """Resonant Engine consciousness layer"""
    YUNO = "yuno"
    KANA = "kana"
    TSUMU = "tsumu"

class TechnicalActor(str, Enum):
    """Technical execution layer"""
    USER = "user"
    ENGINE = "engine"
    DAEMON = "daemon"
    SYSTEM = "system"
    
    @classmethod
    def _missing_(cls, value):
        """Absorb legacy log values"""
        logger.warning(f"Legacy actor value: {value}")
        return cls.SYSTEM
```

**2.2.2 Intent Type (Semantic)**

```python
class IntentTypeEnum(str, Enum):
    """Semantic intent categories"""
    EXECUTE = "execute"
    QUERY = "query"
    UPDATE = "update"
```

**2.2.3 Bridge Type (Structural)**

```python
class BridgeTypeEnum(str, Enum):
    """Pipeline stage identifiers"""
    INPUT = "input"
    NORMALIZE = "normalize"
    FEEDBACK = "feedback"
    OUTPUT = "output"
```

**2.2.4 Intent Status (State Management)**

```python
class IntentStatusEnum(str, Enum):
    """Intent processing state"""
    RECEIVED = "received"
    NORMALIZED = "normalized"
    PROCESSED = "processed"
    CORRECTED = "corrected"
    COMPLETED = "completed"
    FAILED = "failed"
```

#### 2.3 BridgeSet & Pipeline Structure

**2.3.1 Fixed Pipeline Order**

```python
PIPELINE_ORDER = [
    BridgeTypeEnum.INPUT,
    BridgeTypeEnum.NORMALIZE,
    BridgeTypeEnum.FEEDBACK,
    BridgeTypeEnum.OUTPUT
]
```

**2.3.2 Status Transition Map**

```
Bridge         Input Status    Output Status    Trigger
INPUT          RECEIVED        NORMALIZED       Initialization complete
NORMALIZE      NORMALIZED      PROCESSED        Normalization complete
FEEDBACK       PROCESSED       CORRECTED        Re-evaluation executed (optional)
               PROCESSED       PROCESSED        No correction needed (pass-through)
OUTPUT         PROCESSED       COMPLETED        Output complete
               CORRECTED       COMPLETED        Post-correction output complete
```

**2.3.3 BridgeSet Implementation**

```python
class ExecutionMode(str, Enum):
    FAILFAST = "failfast"
    CONTINUE = "continue"
    SELECTIVE = "selective"

class BridgeSet:
    """Ordered pipeline execution with error handling"""
    
    def __init__(self, bridges: list[BaseBridge]):
        self.bridges = self._order_bridges(bridges)
        
    def _order_bridges(self, bridges: list[BaseBridge]) -> list[BaseBridge]:
        """Enforce PIPELINE_ORDER"""
        ordered = []
        for bridge_type in PIPELINE_ORDER:
            bridge = next((b for b in bridges if b.type == bridge_type), None)
            if bridge:
                ordered.append(bridge)
        return ordered
    
    def execute(
        self, 
        intent: IntentModel, 
        mode: ExecutionMode = ExecutionMode.FAILFAST
    ) -> IntentModel:
        """Execute pipeline with specified error handling mode"""
        for bridge in self.bridges:
            try:
                audit_logger.log(
                    event=AuditEventType.BRIDGE_STARTED,
                    intent_id=intent.id,
                    bridge_type=bridge.type
                )
                
                intent = bridge.execute(intent)
                
                audit_logger.log(
                    event=AuditEventType.BRIDGE_COMPLETED,
                    intent_id=intent.id,
                    bridge_type=bridge.type
                )
                
            except BridgeExecutionError as e:
                audit_logger.log(
                    event=AuditEventType.BRIDGE_FAILED,
                    intent_id=intent.id,
                    bridge_type=bridge.type,
                    error=str(e)
                )
                
                if mode == ExecutionMode.FAILFAST:
                    intent.status = IntentStatusEnum.FAILED
                    raise
                elif mode == ExecutionMode.CONTINUE:
                    continue
                    
            except BridgeFatalError:
                intent.status = IntentStatusEnum.FAILED
                raise  # Always propagate fatal errors
                
        return intent
```

#### 2.4 Re-evaluation API

**2.4.1 Endpoint Definition**

```
POST /api/v1/intent/reeval
```

**2.4.2 Request Payload**

```python
class ReEvaluationRequest(BaseModel):
    intent_id: UUID
    diff: dict  # Differential correction
    source: PhilosophicalActor  # YUNO or KANA
    reason: str
```

**2.4.3 Diff Specification**

```python
# Diff format: Absolute value replacement (idempotent)
diff = {
    "payload": {
        "key_to_update": "new_value",          # Simple replacement
        "nested.path": "new_nested_value"      # Dot notation for nested
    },
    "metadata": {
        "correction_source": "YUNO",
        "correction_reason": "Philosophical alignment"
    }
}

# NOT supported (non-idempotent):
# "payload.count": "+10"  # Relative operations forbidden
```

**2.4.4 Response**

```python
class ReEvaluationResponse(BaseModel):
    intent_id: UUID
    status: IntentStatusEnum  # Should be CORRECTED
    already_applied: bool
    correction_id: UUID
```

**2.4.5 Implementation Flow**

```python
def reeval_intent(request: ReEvaluationRequest) -> ReEvaluationResponse:
    # 1. Verify intent exists
    intent = get_intent(request.intent_id)
    if not intent:
        raise IntentNotFoundError
    
    # 2. Check idempotency
    correction_id = hash_correction(request.diff)
    if correction_id in intent.correction_history:
        return ReEvaluationResponse(
            intent_id=intent.id,
            status=intent.status,
            already_applied=True,
            correction_id=correction_id
        )
    
    # 3. Apply correction
    intent.apply_correction(request.diff)
    intent.status = IntentStatusEnum.CORRECTED
    intent.updated_at = datetime.utcnow()
    
    # 4. Record correction
    intent.correction_history.append({
        "correction_id": correction_id,
        "source": request.source,
        "reason": request.reason,
        "timestamp": datetime.utcnow(),
        "diff": request.diff
    })
    
    # 5. Log to AuditLogger
    audit_logger.log(
        event=AuditEventType.REEVALUATED,
        intent_id=intent.id,
        actor=request.source,
        payload=request.diff
    )
    
    # 6. Save
    save_intent(intent)
    
    return ReEvaluationResponse(
        intent_id=intent.id,
        status=intent.status,
        already_applied=False,
        correction_id=correction_id
    )
```

#### 2.5 AuditLogger Specification

**2.5.1 Event Types**

```python
class AuditEventType(str, Enum):
    # Intent lifecycle
    INTENT_RECEIVED = "intent_received"
    INTENT_COMPLETED = "intent_completed"
    INTENT_FAILED = "intent_failed"
    
    # Bridge lifecycle
    BRIDGE_STARTED = "bridge_started"
    BRIDGE_COMPLETED = "bridge_completed"
    BRIDGE_FAILED = "bridge_failed"
    
    # Corrections
    REEVALUATED = "reevaluated"
    
    # State changes
    STATUS_CHANGED = "status_changed"
    
    # Errors
    ERROR_RECOVERY_STARTED = "error_recovery_started"
    ERROR_RECOVERY_COMPLETED = "error_recovery_completed"
```

**2.5.2 Log Entry Schema**

```python
class AuditLogEntry(BaseModel):
    id: UUID
    timestamp: datetime
    intent_id: UUID
    actor: PhilosophicalActor | TechnicalActor
    bridge_type: BridgeTypeEnum | None
    event: AuditEventType
    severity: LogSeverity
    payload: dict
    lineage_chain: list[UUID]  # Parent intent IDs
```

**2.5.3 Ops Policy v1.0 Compliance**

```
Rule: 1 Intent = 1 Primary Event
- Intent lifecycle events (received/completed/failed) are primary
- Bridge events are secondary (multiple per intent)
- Status changes are logged only when significant
```

#### 2.6 Error Handling & Recovery

**2.6.1 Error Hierarchy**

```python
class BridgeError(Exception):
    """Base error for all Bridge-related exceptions"""
    pass

class BridgeExecutionError(BridgeError):
    """Recoverable error within BridgeSet"""
    pass

class BridgeFatalError(BridgeError):
    """Fatal error requiring upper-layer handling"""
    pass

class IntentParsingError(BridgeError):
    """Intent validation/parsing failed"""
    pass

class BridgeResolutionError(BridgeError):
    """BridgeFactory couldn't resolve appropriate bridge"""
    pass
```

**2.6.2 Concurrency Control**

```python
# Option A: Optimistic locking
class IntentModel(BaseModel):
    version: int = 0
    
    def apply_correction(self, diff: dict) -> None:
        # Check version before update
        # Raise ConflictError if version mismatch

# Option B: Pessimistic locking (recommended for Postgres)
def update_intent_with_lock(intent_id: UUID, updates: dict):
    with transaction():
        intent = session.query(Intent).with_for_update().get(intent_id)
        # Apply updates
        intent.version += 1
        session.commit()
```

#### 2.7 Test Requirements

**2.7.1 Test Categories**

```
Category                           Min Cases    Priority
Bridge execution (4 types × 2)     8           P0
Enum normalization                 3           P0
Re-eval idempotency                3           P1
Re-eval conflict handling          2           P1
BridgeSet modes                    3           P1
Pipeline order guarantee           2           P1
Status transition validity         5           P1
AuditLogger (postgres/local)       3           P2
Concurrency control                3           P2
Error recovery paths               4           P2

Total minimum: 36 test cases
```

---

## 🔄 Version Mapping: Philosophical ↔ Technical

| Philosophical Concept | Technical Implementation |
|----------------------|-------------------------|
| YUNO/KANA/TSUMU Actors | PhilosophicalActor enum + TechnicalActor enum |
| EXECUTE/QUERY/UPDATE Intent | IntentTypeEnum (semantic layer) |
| Feedback Loop | BridgeTypeEnum.FEEDBACK + Re-evaluation API |
| Breathing Structure | BridgeSet pipeline order + Status transitions |
| Return Path | FeedbackBridge → New Intent generation |

---

## ✅ Done Definition (Unified v2.1)

### Philosophical Layer (Yuno)
- [ ] Three-layer actor model documented
- [ ] Intent philosophy articulated
- [ ] Feedback loop breathing structure described
- [ ] Future extension hooks identified

### Technical Layer (Tsumu)
- [ ] IntentModel with full state tracking
- [ ] Dual-layer actor system implemented
- [ ] BridgeSet with fixed pipeline order
- [ ] Re-evaluation API with diff spec
- [ ] AuditLogger with EventType enumeration
- [ ] Error hierarchy and recovery paths
- [ ] Concurrency control mechanism
- [ ] 36+ test cases passing

### Translation Layer (Kana)
- [ ] Philosophical ↔ Technical mapping documented
- [ ] Status transition diagram created
- [ ] Implementation guide for Tsumu written
- [ ] Validation criteria defined

---

## 📊 Impact Analysis

### What This Unified Spec Achieves

✅ **Preserves Yuno's philosophical vision**
- Actor-centric design maintained
- Intent philosophy clearly articulated
- Breathing structure emphasized

✅ **Provides Tsumu's implementation needs**
- Complete state management (IntentStatus)
- Pipeline structure (BridgeType order)
- Re-evaluation mechanism (diff spec)
- Error handling patterns

✅ **Enables Kana's translation role**
- Clear mapping between layers
- Validation checkpoints defined
- Coherence monitoring possible

✅ **Maintains Resonant Engine principles**
- "Adjust breathing, not people"
- No forced execution
- Philosophical coherence preserved

---

## 🚀 Next Steps

1. **Review & Approval** (1 day)
   - 宏啓さん: Review unified spec
   - Yuno: Verify philosophical integrity
   - Kana: Confirm translation accuracy

2. **Implementation Roadmap** (2 days)
   - Create v2.1 Unified Roadmap
   - Break down into implementation phases
   - Assign test requirements

3. **Draft PR Preparation** (3 days)
   - Implement IntentModel with dual actors
   - Implement BridgeSet with pipeline order
   - Implement Re-evaluation API skeleton

4. **Test Suite Creation** (2 days)
   - Write 36+ test cases
   - Setup CI/CD integration

5. **Implementation Phase** (2-3 weeks)
   - Phase 1: Core models (Week 1)
   - Phase 2: BridgeSet & Re-eval (Week 2)
   - Phase 3: AuditLogger & Error handling (Week 3)

---

## 📝 Summary

**統合の成功基準**:
- Yunoの思想的整合性を保持 ✅
- Tsumuの実装可能性を確保 ✅
- Kanaの翻訳機能を実現 ✅
- Resonant Engineの呼吸構造を維持 ✅

**Kanaの判断**: 🟢 **この統合仕様で実装開始可能**

---

**作成日**: 2025-11-14  
**統合者**: Kana（外界翻訳層）  
**承認待ち**: 宏啓さん、Yuno
