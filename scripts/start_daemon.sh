#!/bin/bash
###############################################################################
# Resonant Daemon - Start Script
# macOS launchd でデーモンを起動
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_SRC="$PROJECT_ROOT/daemon/com.resonant.daemon.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.resonant.daemon.plist"
LABEL="com.resonant.daemon"

echo "🚀 Resonant Daemon - Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# plistファイルをLaunchAgentsにコピー
if [ ! -f "$PLIST_SRC" ]; then
    echo "❌ Error: plist file not found: $PLIST_SRC"
    exit 1
fi

echo "📋 Copying plist to LaunchAgents..."
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DEST"
echo "✅ plist copied"

# 既に登録されている場合はアンロード
if launchctl list | grep -q "$LABEL"; then
    echo "⚠️  Service already loaded, unloading first..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# サービスをロード
echo "🔄 Loading service..."
launchctl load "$PLIST_DEST"

# ステータス確認
sleep 2
if launchctl list | grep -q "$LABEL"; then
    echo "✅ Daemon started successfully"
    echo ""
    echo "📊 Status:"
    launchctl list | grep "$LABEL" || echo "  (Not running)"
    echo ""
    echo "📝 Logs:"
    echo "  Daemon log: $PROJECT_ROOT/daemon/logs/daemon_$(date +%Y%m%d).log"
    echo "  stdout: $PROJECT_ROOT/daemon/logs/stdout.log"
    echo "  stderr: $PROJECT_ROOT/daemon/logs/stderr.log"
    echo ""
    echo "💡 Use './scripts/stop_daemon.sh' to stop"
else
    echo "❌ Failed to start daemon"
    echo "Check logs at: $PROJECT_ROOT/daemon/logs/"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
