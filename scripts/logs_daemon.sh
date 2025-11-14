#!/bin/bash
###############################################################################
# Resonant Daemon - Logs Script
# デーモンのログをリアルタイム表示
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/daemon/logs"

echo "📝 Resonant Daemon - Logs (Ctrl+C to exit)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 最新のログファイルを tail -f
LATEST_LOG=$(ls -t "$LOG_DIR"/daemon_*.log 2>/dev/null | head -1)

if [ -n "$LATEST_LOG" ]; then
    echo "📄 Watching: $(basename "$LATEST_LOG")"
    echo ""
    tail -f "$LATEST_LOG"
else
    echo "❌ No log files found in $LOG_DIR"
    exit 1
fi
