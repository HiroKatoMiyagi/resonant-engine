#!/bin/bash
# Docker環境のクリーンアップと再構築スクリプト

set -e

echo "🧹 Docker環境をクリーンアップ中..."

# 既存のコンテナを停止・削除
docker compose down -v 2>/dev/null || true

# PostgreSQLコンテナのみ起動
echo "🚀 PostgreSQLコンテナを起動中..."
docker compose up -d db

# 起動待機（10秒）
echo "⏳ PostgreSQL起動待機中..."
sleep 10

# ヘルスチェック
echo "✅ コンテナ状態確認:"
docker compose ps

echo ""
echo "✅ Docker環境の再構築完了"
echo "次: init_db.py でスキーマを適用してください"
