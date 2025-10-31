#!/bin/bash
# ────────────────────────────────────────────────
# Resonant Daemon Bridge v1.0
# ユノ思想層 ↔ ローカル構造層 同調ブリッジ
# 宏啓モデル v3.1 / 2025-10-29
# ────────────────────────────────────────────────

INTENT_FILE="/Users/zero/Projects/kiro-v3.1/bridge/intent_protocol.json"
SCRIPT_DIR="/Users/zero/Projects/kiro-v3.1/scripts"
LOG_DIR="/Users/zero/Projects/kiro-v3.1/logs"
BRIDGE_LOG="${LOG_DIR}/daemon_bridge.log"

echo "[🪶] Resonant Daemon Bridge 起動中 ($(date '+%Y-%m-%d %H:%M:%S'))" | tee -a "$BRIDGE_LOG"

while true; do
  if [[ -f "$INTENT_FILE" ]]; then
    PHASE=$(jq -r '.phase' "$INTENT_FILE")
    INTENT=$(jq -r '.intent' "$INTENT_FILE")

    case "$INTENT" in
      "introspect")
        echo "[💡] Introspection intent 受信 → Phase10 起動" | tee -a "$BRIDGE_LOG"
        bash "$SCRIPT_DIR/phase10_introspection.sh"
        ;;
      "push_to_notion")
        echo "[🌐] Notion archive intent 受信 → notion_archive_push.sh 実行" | tee -a "$BRIDGE_LOG"
        bash "$SCRIPT_DIR/notion_archive_push.sh"
        ;;
      *)
        echo "[⚠️] 未定義 intent: $INTENT" | tee -a "$BRIDGE_LOG"
        ;;
    esac

    mv "$INTENT_FILE" "${INTENT_FILE}.bak_$(date '+%Y%m%d_%H%M%S')"
  fi
  sleep 2
done