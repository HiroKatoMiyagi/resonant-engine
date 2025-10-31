#!/bin/zsh
# ──────────────────────────────────────────────
# 🧩 notion_archive_push.sh
# Resonant Archive System → Notion 同期スクリプト
# ──────────────────────────────────────────────

ROOT="/Users/zero/Projects/kiro-v3.1"
LOG="$ROOT/logs/reval_bridge.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

# === Notion API 設定 ===
export NOTION_TOKEN="${NOTION_TOKEN}"
export DATABASE_ID="${DATABASE_ID}"
NOTION_VERSION="2022-06-28"

# --- Telemetry 取得 ---
TELEMETRY_FILE="$ROOT/logs/telemetry_report.json"
if [ -f "$TELEMETRY_FILE" ]; then
  STABILITY_INDEX=$(jq -r '.stability_index' "$TELEMETRY_FILE")
  COHERENCE_RATIO=$(jq -r '.coherence_ratio' "$TELEMETRY_FILE")
  LAST_UPDATE=$(jq -r '.last_update' "$TELEMETRY_FILE")
  TELEMETRY_B64=$(base64 < "$TELEMETRY_FILE" | tr -d '\n')
else
  STABILITY_INDEX="N/A"
  COHERENCE_RATIO="N/A"
  LAST_UPDATE="$TS"
  TELEMETRY_B64="N/A"
fi

echo "[📤 $TS] Starting Notion Archive Sync..." >> "$LOG"

# --- JSON ペイロード生成 ---
JSON_DATA=$(jq -n \
  --arg phase "archive_sync" \
  --arg si "$STABILITY_INDEX" \
  --arg cr "$COHERENCE_RATIO" \
  --arg lu "$LAST_UPDATE" \
  --arg tb "$TELEMETRY_B64" \
  --arg dbid "$DATABASE_ID" \
  '{
    "parent": { "database_id": $dbid },
    "properties": {
      "Phase": { "title": [{ "text": { "content": $phase } }] },
      "Stability Index": { "rich_text": [{ "text": { "content": $si } }] },
      "Coherence Ratio": { "rich_text": [{ "text": { "content": $cr } }] },
      "Last Update": { "rich_text": [{ "text": { "content": $lu } }] },
      "Telemetry (Base64)": { "rich_text": [{ "text": { "content": $tb } }] }
    }
  }')

# --- Notion API 呼び出し ---
RESPONSE=$(curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: $NOTION_VERSION" \
  -H "Content-Type: application/json" \
  -d "$JSON_DATA")

# --- 結果ログ出力 ---
if echo "$RESPONSE" | grep -q '"object":"page"'; then
  PAGE_ID=$(echo "$RESPONSE" | jq -r '.id')
  echo "[✅ $TS] Page created in Resonant Archive DB (id: $PAGE_ID)" >> "$LOG"
else
  echo "[⚠️ $TS] Notion API Error: $RESPONSE" >> "$LOG"
fi

echo "[✅ $TS] Notion archive sync completed." >> "$LOG"