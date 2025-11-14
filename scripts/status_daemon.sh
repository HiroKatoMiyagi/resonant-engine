#!/bin/bash
###############################################################################
# Resonant Daemon - Status Script
# デーモンの状態を確認
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LABEL="com.resonant.daemon"
PID_FILE="$PROJECT_ROOT/daemon/pids/resonant_daemon.pid"
LOG_DIR="$PROJECT_ROOT/daemon/logs"

echo "📊 Resonant Daemon - Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# launchctlでのステータス確認
if launchctl list | grep -q "$LABEL"; then
    echo "✅ Service: LOADED"
    echo ""
    launchctl list | grep "$LABEL"
    echo ""
else
    echo "❌ Service: NOT LOADED"
    echo ""
fi

# PIDファイル確認
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Process: RUNNING (PID: $PID)"
    else
        echo "⚠️  Process: NOT RUNNING (stale PID file)"
    fi
else
    echo "⚠️  Process: NO PID FILE"
fi

echo ""
echo "📝 Logs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 最新のログファイルを表示
if [ -d "$LOG_DIR" ]; then
    LATEST_LOG=$(ls -t "$LOG_DIR"/daemon_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "📄 Latest log: $(basename "$LATEST_LOG")"
        echo ""
        echo "Last 10 lines:"
        tail -10 "$LATEST_LOG"
    else
        echo "⚠️  No daemon log files found"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # stdout/stderr確認
    if [ -f "$LOG_DIR/stdout.log" ]; then
        echo "📤 stdout.log (last 5 lines):"
        tail -5 "$LOG_DIR/stdout.log"
        echo ""
    fi
    
    if [ -f "$LOG_DIR/stderr.log" ] && [ -s "$LOG_DIR/stderr.log" ]; then
        echo "⚠️  stderr.log (last 5 lines):"
        tail -5 "$LOG_DIR/stderr.log"
        echo ""
    fi
else
    echo "⚠️  Log directory not found: $LOG_DIR"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
