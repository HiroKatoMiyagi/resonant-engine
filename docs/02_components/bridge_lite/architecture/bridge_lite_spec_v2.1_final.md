# Bridge Lite Specification v2.1 (Final)

## 1. Purpose
Bridge Lite is an intent-driven lightweight orchestration layer connecting Yuno (GPT-5 Thought Core) with Kana (External Translation Layer) and Tsumu (Execution Layer).  
This document defines the finalized version of the v2.1 specification after Kana's review.

---

## 2. Core Concepts

### 2.1 Intent Model (Pydantic v2)
Intent is formally defined as a typed model.

```python
class Intent(BaseModel):
    id: str
    actor: ActorEnum
    type: IntentTypeEnum
    payload: dict
    timestamp: datetime
```

---

## 3. Enums

```python
class ActorEnum(Enum):
    YUNO = "yuno"
    KANA = "kana"
    TSUMU = "tsumu"

class IntentTypeEnum(Enum):
    EXECUTE = "execute"
    QUERY = "query"
    UPDATE = "update"
```

---

## 4. Bridge Lifecycle

1. Receive Intent  
2. Validate Intent  
3. Resolve Bridge  
4. Execute Bridge Logic  
5. Output Result  
6. Log Event  
7. Return Feedback  
8. FeedbackBridge sends refinement if required

---

## 5. BridgeFactory (Revised)
BridgeFactory resolves the correct bridge and wraps it in a `BridgeSet`.

```
Intent → BridgeFactory → BridgeSet → Bridge
```

---

## 6. BridgeSet Structure
A new abstraction to improve Tsumu and Kana’s code analysis.

```
BridgeSet
 ├── bridge: BaseBridge
 ├── intents: List[Intent]
 ├── metadata: dict
```

---

## 7. Error Model

### 7.1 Error Categories
- IntentParsingError
- BridgeResolutionError
- ExecutionRuntimeError

AuditLogger records all errors with lineage propagation.

---

## 8. AuditLogger (Ops Policy Integrated)
- Must store log entry with:
  - timestamp
  - intent id
  - actor
  - bridge_type
  - severity
  - lineage chain
- Must support:
  - async logging
  - safe fallback mode
  - error recovery path

---

## 9. Sequence Diagram (v2.1 Final)
```
Yuno → Bridge Lite → BridgeFactory → Bridge → AuditLogger → FeedbackBridge → Yuno
```

---

## 10. Return Path (Kana Review Fix)
Every execution must produce a **Feedback Intent** that flows:

```
Result → Bridge Lite → FeedbackBridge → New Intent
```

---

## 11. Future Extension Hooks
- Multi-bridge routing
- Intent batching
- Context lineage graph

---

## 12. v2.1 ChangeLog
- Pydantic v2 adoption formalized
- Enums added (actor, intent type)
- BridgeSet added
- Error model clarified
- Lifecycle return path added
- Sequence diagram updated
- Ops policy linked
