#!/bin/zsh
ROOT="/Users/zero/Projects/kiro-v3.1"
LOG="$ROOT/logs/telemetry_feedback.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TS] 🧭 Telemetry Feedback Loop initiated" >> "$LOG"
echo "[$TS] 🔁 Gathering current metrics..." >> "$LOG"

AVG_CYCLE=$(jq '.avg_cycle_time_sec' "$ROOT/logs/telemetry_report.json" 2>/dev/null)
COHERENCE=$(jq '.coherence_ratio' "$ROOT/logs/telemetry_report.json" 2>/dev/null)
STABILITY=$(jq '.stability_index' "$ROOT/logs/telemetry_report.json" 2>/dev/null)
UPDATE=$(jq -r '.last_update' "$ROOT/logs/telemetry_report.json" 2>/dev/null)

echo "[$TS] 📡 avg_cycle_time_sec: $AVG_CYCLE, coherence: $COHERENCE, stability: $STABILITY" >> "$LOG"
echo "[$TS] 🧩 last_update: $UPDATE" >> "$LOG"

sleep 1
echo "[$TS] ✅ Telemetry Feedback Loop completed" >> "$LOG"