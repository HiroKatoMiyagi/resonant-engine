#!/bin/zsh
# Resonant Daemon 起動スクリプト
# 環境変数を読み込んでからデーモンを起動

set -e

# プロジェクトルート
ROOT="/Users/zero/Projects/resonant-engine"

# 環境変数を読み込む
if [ -f "$ROOT/.env" ]; then
    echo "📥 Loading environment variables from .env..."
    export $(cat "$ROOT/.env" | grep -v '^#' | grep -v '^$' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found at $ROOT/.env"
    exit 1
fi

# API Keyが設定されているか確認
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY is not set"
    exit 1
fi

echo "✅ ANTHROPIC_API_KEY is set (${ANTHROPIC_API_KEY:0:20}...)"

# デーモンを起動
echo "🚀 Starting Resonant Daemon..."
echo "🐍 Using virtual environment Python..."
cd "$ROOT/daemon"
"$ROOT/venv/bin/python3" resonant_daemon.py
