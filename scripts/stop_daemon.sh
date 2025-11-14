#!/bin/bash
###############################################################################
# Resonant Daemon - Stop Script
# macOS launchd からデーモンを停止
###############################################################################

set -e

PLIST_DEST="$HOME/Library/LaunchAgents/com.resonant.daemon.plist"
LABEL="com.resonant.daemon"

echo "🛑 Resonant Daemon - Stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# サービスが登録されているか確認
if ! launchctl list | grep -q "$LABEL"; then
    echo "⚠️  Daemon is not running"
    exit 0
fi

# サービスをアンロード
echo "🔄 Unloading service..."
launchctl unload "$PLIST_DEST"

# ステータス確認
sleep 1
if launchctl list | grep -q "$LABEL"; then
    echo "❌ Failed to stop daemon"
    exit 1
else
    echo "✅ Daemon stopped successfully"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
