#!/bin/zsh
ROOT="/Users/zero/Projects/kiro-v3.1"
LOG="$ROOT/logs/auto_sync.log"

echo "[`date '+%Y-%m-%d %H:%M:%S'`] 🔁 Auto-sync Phase3 initiated" >> "$LOG"

# docs
echo "[`date '+%H:%M:%S'`] 🔍 Scanning docs directory..." >> "$LOG"
for file in $(find "$ROOT/docs" -type f); do
  echo "Syncing $file ..." >> "$LOG"
done
echo "[`date '+%H:%M:%S'`] ✅ docs sync simulated." >> "$LOG"

# notion
echo "[`date '+%H:%M:%S'`] 🔍 Scanning notion directory..." >> "$LOG"
echo "[`date '+%H:%M:%S'`] ✅ notion sync simulated." >> "$LOG"

# openai
echo "[`date '+%H:%M:%S'`] 🔍 Scanning openai directory..." >> "$LOG"
echo "[`date '+%H:%M:%S'`] ✅ openai sync simulated." >> "$LOG"

echo "[`date '+%Y-%m-%d %H:%M:%S'`] 🌿 Auto-sync cycle complete" >> "$LOG"