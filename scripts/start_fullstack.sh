#!/bin/bash
# Resonant Engine フルスタック起動スクリプト

echo "🚀 Resonant Engine を起動中..."

# バックエンドAPIサーバー起動
echo "📡 バックエンドAPI起動..."
cd /Users/zero/Projects/resonant-engine
/Users/zero/Projects/resonant-engine/venv/bin/uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 起動待機
sleep 3

# フロントエンド起動
echo "🎨 フロントエンド起動..."
cd /Users/zero/Projects/resonant-engine/dashboard/frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Resonant Engine 起動完了！"
echo ""
echo "📡 バックエンドAPI: http://localhost:8000"
echo "🎨 フロントエンド: http://localhost:5173"
echo ""
echo "停止するには Ctrl+C を押してください"
echo ""

# 終了シグナル処理
trap "echo ''; echo '🛑 停止中...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# プロセスが終了するまで待機
wait
