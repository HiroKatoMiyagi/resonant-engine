#!/bin/bash
# 🪶 Resonant Trace Bridge 自動トレース実行スクリプト（v1.2 安定版）

cd /Users/zero/Projects/resonant-engine || exit 1

# 実行ログ出力先
LOG_FILE="logs/trace_auto.log"

echo "[Manual] $(date '+%Y-%m-%d %H:%M:%S') Manual trigger start" >> "$LOG_FILE"

# 強制トレース実行
python3 utils/trace_linker.py --force >> "$LOG_FILE" 2>&1

# 最新リンク確認
tail -n 1 logs/trace_map.jsonl >> "$LOG_FILE"

echo "[Manual✓] Trace Linker finished." >> "$LOG_FILE"
