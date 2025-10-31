#!/bin/zsh
# ==========================================
# 🪶 Resonant Bridge Daemon – v3.1.11
# 構造層：思想層（ユノ）からの意図を受け取り
#           実際のI/O・同期・証跡生成を行う。
# ==========================================

ROOT="/Users/zero/Projects/kiro-v3.1"
LOG="$ROOT/logs/daemon_bridge.log"
INTENT_FILE="$ROOT/bridge/intent_protocol.json"

mkdir -p "$ROOT/logs"
TS=$(date '+%Y-%m-%d %H:%M:%S')
echo "[🪶] Resonant Daemon Bridge 起動中 ($TS)" >> "$LOG"

# --- Intent Watcher 自動起動 ---
nohup "$ROOT/daemon/intent_watcher.sh" >> "$LOG" 2>&1 &
echo "[<0001f9ed>] Intent Watcher 自動起動済み ($(date '+%Y-%m-%d %H:%M:%S'))" >> "$LOG"

# === Main Loop ===
while true; do
  if [ -f "$INTENT_FILE" ]; then
    INTENT=$(cat "$INTENT_FILE")

    # --- Telemetry Feedback Intent ---
    if echo "$INTENT" | grep -q "telemetry_feedback"; then
      echo "[🌐] telemetry_feedback intent 受信 → telemetry_feedback_loop.sh 実行" >> "$LOG"
      "$ROOT/scripts/telemetry_feedback_loop.sh" &
    fi

    # --- Reflection Intent ---
    if echo "$INTENT" | grep -q "reflection"; then
      echo "[🪞] reflection intent 受信 → reflection_verification.sh 実行" >> "$LOG"
      "$ROOT/scripts/reflection_verification.sh" &
    fi

    # --- Notion Archive Sync ---
    if echo "$INTENT" | grep -q "push_to_notion"; then
      echo "[🌐] Notion archive intent 受信 → notion_archive_push.sh 実行" >> "$LOG"
      "$ROOT/scripts/notion_archive_push.sh" &
    fi

    # --- Proof Generator Block (Phase 11) ---
    if echo "$INTENT" | grep -q "create_file"; then
      TS=$(date '+%Y-%m-%d %H:%M:%S')
      TARGET="$ROOT/scripts/test_output_from_proof.txt"
      echo "[$TS] File created by Resonant Daemon via intent" > "$TARGET"
      PROOF_ID=$(shasum -a 256 "$TARGET" | awk '{print $1}')
      echo "[$TS] [🧾] Proof Generated (ID: $PROOF_ID)" >> "$ROOT/logs/proof_channel.log"
      echo "[$TS] [🧾] Proof Generated (ID: $PROOF_ID)" >> "$LOG"
    fi

    # --- Introspection Intent ---
    if echo "$INTENT" | grep -q "introspection"; then
      echo "[🧠] Phase10 Introspection 実行" >> "$LOG"
      "$ROOT/scripts/phase10_introspection.sh" &
    fi

    # --- Telemetry Sync Intent ---
    if echo "$INTENT" | grep -q "telemetry_sync"; then
      echo "[🌐] Telemetry sync intent 受信 → telemetry_refresh.sh 実行" >> "$LOG"
      "$ROOT/scripts/telemetry_refresh.sh" &
    fi

    # --- Clear processed intent ---
    rm "$INTENT_FILE"
  fi

  sleep 2
done