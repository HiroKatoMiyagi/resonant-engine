# utils/intent_logger.py
import json
import uuid
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("/Users/zero/Projects/resonant-engine/logs/intent_log.jsonl")

def log_intent(source="YUNO", intent="", context=""):
    entry = {
        "intent_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "intent": intent,
        "context": context
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[Intent logged] {entry['intent_id']} - {intent}")

if __name__ == "__main__":
    import sys
    intent = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "テスト意図"
    log_intent(intent=intent)