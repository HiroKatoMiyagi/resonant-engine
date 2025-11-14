#!/usr/bin/env python3
import os, sys, time, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from pathlib import Path

# Priority 1: Intent → Bridge → Kana 統合
ROOT = Path("/Users/zero/Projects/resonant-engine")
BRIDGE = ROOT / "bridge"
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

# Intent Processor統合
sys.path.insert(0, str(ROOT))
try:
    from dashboard.backend.intent_processor import IntentProcessor
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    PROCESSOR_AVAILABLE = False
    print(f"⚠️ IntentProcessor import failed: {e}")

LOG = LOGS / "daemon.log"
STATE = LOGS / "resonant_state.log"
INTENT_FILE = BRIDGE / "intent_protocol.json"

def write_state(phase, state):
    data = {
        "source": "daemon",
        "phase": phase,
        "state": state,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(STATE, "a") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

log("🌿 Resonant Daemon started (Priority 1: Intent→Bridge→Kana統合版)")
write_state("init", "Daemon started with IntentProcessor")

if PROCESSOR_AVAILABLE:
    processor = IntentProcessor()
    log("✅ IntentProcessor initialized")
else:
    log("⚠️ IntentProcessor not available, falling back to legacy mode")

last_mtime = 0
while True:
    if INTENT_FILE.exists():
        mtime = INTENT_FILE.stat().st_mtime
        if mtime != last_mtime:
            last_mtime = mtime
            log("🔄 Change detected in intent_protocol.json")
            write_state("intent_update", "Intent processing triggered")
            
            # Priority 1: IntentProcessor経由でKana呼び出し
            if PROCESSOR_AVAILABLE:
                try:
                    success = processor.process_intent()
                    if success:
                        log("✅ Intent processed successfully via Kana")
                        write_state("intent_processed", "Kana response received")
                    else:
                        log("⚠️ Intent processing failed")
                        write_state("intent_failed", "Processing error")
                except Exception as e:
                    log(f"❌ Intent processing error: {e}")
                    write_state("intent_error", str(e))
            else:
                # Fallback: 旧方式（reval_bridge.sh）
                log("⚠️ Using legacy bridge script")
                os.system(f"{ROOT}/scripts/reval_bridge.sh &")
    
    time.sleep(1)