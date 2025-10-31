#!/usr/bin/env python3
import os, time, json
from pathlib import Path

ROOT = Path("/Users/zero/Projects/kiro-v3.1")
BRIDGE = ROOT / "bridge"
LOGS = ROOT / "logs"
SEMANTIC_LOG = BRIDGE / "semantic_signal.log"
INTENT_FILE = BRIDGE / "intent_protocol.json"
AGENT_LOG = LOGS / "feedback_agent.log"
STATE = LOGS / "resonant_state.log"

def write_state(phase, state):
    data = {
        "source": "feedback_agent",
        "phase": phase,
        "state": state,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(STATE, "a") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def log(msg):
    with open(AGENT_LOG, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

log("🌿 Feedback Agent started")
write_state("init", "Feedback Agent active")

prev_size = SEMANTIC_LOG.stat().st_size if SEMANTIC_LOG.exists() else 0
while True:
    time.sleep(1)
    if not SEMANTIC_LOG.exists():
        continue
    size = SEMANTIC_LOG.stat().st_size
    if size > prev_size:
        prev_size = size
        with open(SEMANTIC_LOG) as f:
            lines = f.readlines()
        meaning = next((l.replace("Meaning:", "").strip() for l in reversed(lines) if l.startswith("Meaning:")), "")
        if meaning:
            log(f"🧭 New meaning detected: {meaning}")
            write_state("meaning_detected", meaning)
            intent = {
                "phase": "feedback-cycle",
                "intent": "reflect",
                "meaning": meaning,
                "meta": {"generated_by": "Yuno", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
            }
            with open(INTENT_FILE, "w") as f:
                json.dump(intent, f, ensure_ascii=False, indent=2)
            log("🌬️ Intent regenerated from meaning")
            write_state("intent_regenerated", meaning)