#!/bin/zsh
ROOT="/Users/zero/Projects/kiro-v3.1"
LOG="$ROOT/logs/watcher.log"
echo "[`date '+%Y-%m-%d %H:%M:%S'`] 👁️  Resonant Watcher started" >> "$LOG"

fswatch -o "$ROOT/docs" | while read num
do
  echo "[`date '+%H:%M:%S'`] 🌀 Change detected ($num)" >> "$LOG"
  "$ROOT/scripts/auto_sync_phase3.sh" >> "$LOG"
  "$ROOT/scripts/reval_bridge.sh" >> "$LOG"
  echo "[`date '+%H:%M:%S'`] 🔁 Re-evaluation Triggered" >> "$LOG"
done