#!/usr/bin/env zsh
set -euo pipefail

ROOT="/Users/zero/Projects/kiro-v3.1"
INTENT_FILE="$ROOT/bridge/intent_protocol.json"
LOG="$ROOT/logs/daemon_bridge.log"
LAST_HASH=""

TS=$(date '+%Y-%m-%d %H:%M:%S')
echo "[🪶] Intent Watcher 起動（思想層監視開始 $TS）" >> "$LOG"

while true; do
  if [ -f "$INTENT_FILE" ]; then
    HASH=$(shasum "$INTENT_FILE" | awk '{print $1}')
    if [ "$HASH" != "$LAST_HASH" ]; then
      LAST_HASH="$HASH"
      TS=$(date '+%Y-%m-%d %H:%M:%S')
      INTENT=$(cat "$INTENT_FILE" 2>/dev/null || echo "")

      echo "[$TS] 🧠 新Intent検出: $INTENT" >> "$LOG"

      if echo "$INTENT" | grep -q '"phase":"proof_write"'; then
        echo "[$TS] 🔐 proof_write intent 実行 → write_proof.sh" >> "$LOG"
        "$ROOT/scripts/write_proof.sh" &
      elif echo "$INTENT" | grep -q '"phase":"inbound_read"'; then
        echo "[$TS] 📨 inbound_read intent 実行 → inbound_collect.sh" >> "$LOG"
        "$ROOT/scripts/inbound_collect.sh" &
      elif echo "$INTENT" | grep -q '"phase":"telemetry_feedback"'; then
        echo "[$TS] 📡 telemetry_feedback intent 実行 → telemetry_feedback_loop.sh" >> "$LOG"
        "$ROOT/scripts/telemetry_feedback_loop.sh" &
      elif echo "$INTENT" | grep -q '"phase":"reflection"'; then
        echo "[$TS] 🪞 reflection intent 実行 → reflection_verification.sh" >> "$LOG"
        "$ROOT/scripts/reflection_verification.sh" &
      else
        echo "[$TS] ⚠️ 未対応intent検出（スクリプト未定義）" >> "$LOG"
      fi
    fi
  fi
  sleep 1
done