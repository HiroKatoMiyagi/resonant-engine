#!/bin/bash
# シンプルなPostgreSQLコンテナ起動スクリプト

echo "🚀 PostgreSQLコンテナを起動します..."

cd /Users/zero/Projects/resonant-engine

# コンテナ起動
docker compose up -d db

# 10秒待機
echo "⏳ 起動待機中（10秒）..."
sleep 10

# 状態確認
echo ""
echo "📊 コンテナ状態:"
docker compose ps

echo ""
echo "✅ 完了"
