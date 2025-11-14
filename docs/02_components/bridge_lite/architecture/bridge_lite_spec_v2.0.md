# Bridge Lite Specification v2.0 (Draft)

## 1. FeedbackBridge Re-evaluation API

### 1.1 Overview
Introduce full Re-evaluation Phase support:
- submit_feedback
- reanalyze
- generate_correction

### 1.2 Interface Additions
```python
class FeedbackBridge(ABC):

    @abstractmethod
    async def submit_feedback(self, intent_id: str, feedback: dict) -> dict:
        ...

    @abstractmethod
    async def reanalyze(self, intent: dict, history: list[dict]) -> dict:
        ...

    @abstractmethod
    async def generate_correction(self, intent: dict, feedback_history: list[dict]) -> dict:
        ...
```

### 1.3 Yuno Provider Requirements
- Implement the above methods using GPT-5 API.
- Return structured re-evaluation and correction plans.

---

## 2. AuditLogger Operational Spec

### 2.1 Storage Format
PostgreSQL table:
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    bridge_type TEXT NOT NULL,
    operation TEXT NOT NULL,
    details JSONB,
    intent_id TEXT,
    correlation_id TEXT
);
```

### 2.2 Rotation Policy
- Archive after 14 days
- Delete after 30 days

### 2.3 Log Levels
INFO / DETAIL / ERROR

### 2.4 Interface
```python
class AuditLogger(ABC):

    @abstractmethod
    async def log(self, bridge_type: str, operation: str, details: dict, intent_id: str | None):
        ...

    @abstractmethod
    async def cleanup(self):
        ...
```

---

## 3. Daemon → Bridge Lite Integration Spec

Daemon flow:
1. Receive Intent  
2. DataBridge.save_intent  
3. AIBridge.process_intent  
4. FeedbackBridge.submit_feedback  
5. FeedbackBridge.reanalyze  
6. FeedbackBridge.generate_correction  
7. DataBridge.save_correction  
8. AuditLogger.log  

---

## 4. PostgreSQL Smoke Test Spec

### Required tests
1. Intent Save/Get works  
2. AuditLogger saves one log  
3. BridgeFactory creates postgresql impl  

### Sample Test
```python
@pytest.mark.asyncio
async def test_postgresql_bridge_smoke():
    bridge = BridgeFactory.create_data_bridge(type="postgresql")
    async with bridge:
        intent_id = await bridge.save_intent("test", {"msg": "hello"})
        result = await bridge.get_intent(intent_id)
    assert result["msg"] == "hello"
```
