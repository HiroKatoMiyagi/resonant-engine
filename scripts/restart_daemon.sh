#!/bin/bash
###############################################################################
# Resonant Daemon - Restart Script
# デーモンを再起動
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 Resonant Daemon - Restart"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 停止
"$SCRIPT_DIR/stop_daemon.sh"

echo ""
echo "⏳ Waiting 2 seconds..."
sleep 2
echo ""

# 起動
"$SCRIPT_DIR/start_daemon.sh"
