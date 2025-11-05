#!/bin/zsh
# 開発セッション開始スクリプト
# 使い方: ./scripts/start_dev.sh "開発の意図"

set -euo pipefail

ROOT="/Users/zero/Projects/resonant-engine"
cd "$ROOT"

# 引数チェック
if [ $# -lt 1 ]; then
    echo "❌ エラー: 開発意図を指定してください"
    echo ""
    echo "使い方:"
    echo "  ./scripts/start_dev.sh \"開発の意図\""
    echo ""
    echo "例:"
    echo "  ./scripts/start_dev.sh \"Webhook受信のエラーハンドリング改善\""
    echo "  ./scripts/start_dev.sh \"Notion同期機能の実装\""
    exit 1
fi

INTENT="$1"
CONTEXT="${2:-}"

echo "🚀 開発セッションを開始します..."
echo "   意図: $INTENT"
if [ -n "$CONTEXT" ]; then
    echo "   コンテキスト: $CONTEXT"
fi
echo ""

# 1. 意図をイベントストリームに記録
echo "📝 開発意図を記録中..."
if [ -n "$CONTEXT" ]; then
    python3 utils/record_intent.py "$INTENT" "$CONTEXT"
else
    python3 utils/record_intent.py "$INTENT"
fi

echo ""

# 2. .cursorrulesに最新の開発文脈を注入
echo "📚 .cursorrulesを更新中..."
source venv/bin/activate 2>/dev/null || true
python3 utils/resonant_digest.py --days 7 --update-cursorrules

echo ""
echo "✅ 開発セッション準備完了！"
echo ""
echo "💡 次のステップ:"
echo "   1. 開発作業を開始"
echo "   2. 完了したら: ./scripts/end_dev.sh \"完了メッセージ\""
echo ""

