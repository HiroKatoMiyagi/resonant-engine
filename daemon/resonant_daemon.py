#!/usr/bin/env python3
import os, time, json
from pathlib import Path

ROOT = Path("/Users/zero/Projects/kiro-v3.1")
BRIDGE = ROOT / "bridge"
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

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

log("🌿 Resonant Daemon started")
write_state("init", "Daemon started")

last_mtime = 0
while True:
    if INTENT_FILE.exists():
        mtime = INTENT_FILE.stat().st_mtime
        if mtime != last_mtime:
            last_mtime = mtime
            log("🔄 Change detected in intent_protocol.json")
            write_state("intent_update", "Bridge launch triggered")
            os.system(f"{ROOT}/scripts/reval_bridge.sh &")
    time.sleep(1)