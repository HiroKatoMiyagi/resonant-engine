# Bridge Lite Module

This package provides the Bridge Lite abstraction layer described in
`docs/bridge_lite_design_v1.1.md`. It introduces three bridge families:

- **DataBridge** (`bridge/core/data_bridge.py`)
  - PostgreSQL-backed implementation (`bridge/providers/postgresql_bridge.py`)
  - In-memory mock implementation for tests (`bridge/providers/mock_bridge.py`)
- **AIBridge** (`bridge/core/ai_bridge.py`)
  - Anthropic Claude provider (`bridge/providers/claude_bridge.py`)
- **FeedbackBridge** (`bridge/core/feedback_bridge.py`)
  - Yuno (GPT-5) provider (`bridge/providers/yuno_feedback_bridge.py`)

Factory helpers in `bridge/factory/bridge_factory.py` resolve the concrete
implementations using the environment variables below:

| Variable | Values | Default |
|----------|--------|---------|
| `DATA_BRIDGE_TYPE` | `postgresql`, `mock` | `mock` |
| `AI_BRIDGE_TYPE` | `claude`, `mock` | `mock` |
| `FEEDBACK_BRIDGE_TYPE` | `yuno`, `mock` | `mock` |

```python
from bridge.factory import BridgeFactory

async def bootstrap():
    data_bridge = BridgeFactory.create_data_bridge()
    ai_bridge = BridgeFactory.create_ai_bridge()
    feedback_bridge = BridgeFactory.create_feedback_bridge()

    async with data_bridge:
        intent_id = await data_bridge.save_intent("review", {"target": "app.py"})
        print("Intent", intent_id)
```

The mock implementations are wired for testing and require no external
services. Production usage requires `DATABASE_URL`, `ANTHROPIC_API_KEY`, and
`OPENAI_API_KEY` to be configured.
