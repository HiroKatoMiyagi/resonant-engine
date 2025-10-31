#!/bin/bash
CONFIG="/Users/zero/Projects/kiro-v3.1/bridge/daemon_config.json"
LOG="/Users/zero/Projects/kiro-v3.1/logs/daemon_bridge.log"
INTENT="/Users/zero/Projects/kiro-v3.1/bridge/intent_protocol.json"
OUTPUT_ROOT=$(jq -r '.output_root' "$CONFIG")

echo "[🪶] Resonant I/O Watcher 起動中 ($(date '+%Y-%m-%d %H:%M:%S'))" >> "$LOG"

fswatch -0 "$INTENT" | while read -d "" event; do
  PHASE=$(jq -r '.phase' "$INTENT")
  FILE=$(jq -r '.target_file // empty' "$INTENT")
  CONTENT=$(jq -r '.content // empty' "$INTENT")

  if [[ "$PHASE" == "create_file" && -n "$FILE" ]]; then
    TARGET="${OUTPUT_ROOT}${FILE}"
    echo "$CONTENT" > "$TARGET"
    echo "[💾] File created → $TARGET ($(date '+%H:%M:%S'))" >> "$LOG"
  fi
done