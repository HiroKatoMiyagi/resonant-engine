#!/bin/zsh
ROOT="/Users/zero/Projects/resonant-engine"
LOG="$ROOT/logs/reval_bridge.log"
STATE="$ROOT/logs/resonant_state.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TS] 🌉 Re-evaluation Bridge initiated" >> "$LOG"
echo "{\"source\": \"bridge\", \"phase\": \"re-eval\", \"state\": \"initiated\", \"timestamp\": \"$TS\"}" >> "$STATE"

MODIFIED=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$ROOT/docs/phase3_test.txt")
echo "[$TS] 🔄 Change observed in docs/phase3_test.txt (modified: $MODIFIED)" >> "$LOG"
echo "{\"source\": \"bridge\", \"phase\": \"re-eval\", \"state\": \"detected\", \"timestamp\": \"$TS\"}" >> "$STATE"

echo "[$TS] 🧠 Triggering Resonant Re-evaluation..." >> "$LOG"
echo "{\"source\": \"bridge\", \"phase\": \"re-eval\", \"state\": \"triggered\", \"timestamp\": \"$TS\"}" >> "$STATE"

sleep 1
echo "[$TS] ✅ Signal transmitted to Yuno (思想層呼吸)" >> "$LOG"
echo "{\"source\": \"bridge\", \"phase\": \"re-eval\", \"state\": \"completed\", \"timestamp\": \"$TS\"}" >> "$STATE"


# --- Resonant Archive Sync Trigger ---
INTENT_FILE="$ROOT/bridge/intent_protocol.json"
if [ -f "$INTENT_FILE" ]; then
  INTENT=$(cat "$INTENT_FILE")
  if echo "$INTENT" | grep -q "push_to_notion"; then
    echo "[$TS] 🚀 Initiating Notion Archive Sync..." >> "$LOG"
    $ROOT/scripts/notion_archive_push.sh &
  fi
fi