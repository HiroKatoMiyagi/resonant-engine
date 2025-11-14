#!/bin/zsh
ROOT="/Users/zero/Projects/resonant-engine"
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
#!/bin/zsh
#
# Resonant Engine — Telemetry Feedback Loop (dynamic ROOT / safe mode)
# Purpose: Periodically read telemetry_report.json and append summarized metrics to telemetry_feedback.log
#
# Behavior:
# - ROOT is resolved in the following order:
#     1) RESONANT_ROOT environment variable (recommended, loaded by scripts/setup_env.sh)
#     2) Project root inferred as parent of this script directory
# - Ensures logs directory exists
# - Reads metrics via jq (if available); falls back to "null" if missing/unreadable
# - Writes compact, timestamped lines to logs/telemetry_feedback.log
#
# Exit codes:
#   0 = success (even if metrics are "null")
#   10 = jq not found and no readable telemetry_report.json
#

set -euo pipefail

# --- Resolve ROOT dynamically ---
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
DEFAULT_ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd -P)"
ROOT="${RESONANT_ROOT:-$DEFAULT_ROOT}"

# --- Paths ---
LOG_DIR="$ROOT/logs"
LOG="$LOG_DIR/telemetry_feedback.log"
REPORT="$LOG_DIR/telemetry_report.json"

# --- Ensure log directory exists ---
mkdir -p "$LOG_DIR"

# --- Timestamp ---
TS="$(date '+%Y-%m-%d %H:%M:%S')"

# --- Helper: safe jq read ---
_jq_read() {
  local expr="$1"
  if command -v jq >/dev/null 2>&1 && [ -r "$REPORT" ]; then
    # Use -e to fail on null/false, then coalesce to empty string; suppress errors
    jq -re "$expr // empty" "$REPORT" 2>/dev/null || true
  else
    echo ""
  fi
}

# --- Collect metrics (empty string => "null") ---
AVG_CYCLE="$(_jq_read '.avg_cycle_time_sec')"
COHERENCE="$(_jq_read '.coherence_ratio')"
STABILITY="$(_jq_read '.stability_index')"
UPDATE="$(_jq_read '.last_update')"

[ -n "$AVG_CYCLE" ] || AVG_CYCLE="null"
[ -n "$COHERENCE" ] || COHERENCE="null"
[ -n "$STABILITY" ] || STABILITY="null"
[ -n "$UPDATE" ] || UPDATE="null"

# --- Write log lines ---
{
  echo "[$TS] 🧭 Telemetry Feedback Loop initiated  (ROOT=$ROOT)"
  if ! command -v jq >/dev/null 2>&1; then
    echo "[$TS] ⚠️  jq not found. Metrics may be \"null\" unless another process writes $REPORT"
  fi
  if [ ! -r "$REPORT" ]; then
    echo "[$TS] ⚠️  telemetry_report.json not readable at: $REPORT"
  fi
  echo "[$TS] 🔁 Gathering current metrics..."
  echo "[$TS] 📡 avg_cycle_time_sec: $AVG_CYCLE, coherence: $COHERENCE, stability: $STABILITY"
  echo "[$TS] 🧩 last_update: $UPDATE"
  echo "[$TS] ✅ Telemetry Feedback Loop completed"
} >> "$LOG"

# --- Exit status semantics ---
if ! command -v jq >/dev/null 2>&1 && [ ! -r "$REPORT" ]; then
  exit 10
fi

exit 0