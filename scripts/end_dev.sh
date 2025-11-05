#!/bin/zsh
# 開発セッション終了スクリプト
# 使い方: ./scripts/end_dev.sh "完了メッセージ"

set -euo pipefail

ROOT="/Users/zero/Projects/resonant-engine"
cd "$ROOT"

# 引数チェック
if [ $# -lt 1 ]; then
    echo "❌ エラー: 完了メッセージを指定してください"
    echo ""
    echo "使い方:"
    echo "  ./scripts/end_dev.sh \"完了メッセージ\""
    echo ""
    echo "例:"
    echo "  ./scripts/end_dev.sh \"エラーハンドリング実装完了\""
    echo "  ./scripts/end_dev.sh \"Notion同期機能の実装完了\""
    exit 1
fi

RESULT_MESSAGE="$1"
STATUS="${2:-success}"

echo "🏁 開発セッションを終了します..."
echo "   結果: $RESULT_MESSAGE"
echo "   ステータス: $STATUS"
echo ""

# 1. 結果をイベントストリームに記録
echo "📝 開発結果を記録中..."
source venv/bin/activate 2>/dev/null || true

python3 << EOF
import sys
from pathlib import Path

# utils/ ディレクトリをパスに追加
utils_dir = Path("$ROOT/utils")
sys.path.insert(0, str(utils_dir))

from resonant_event_stream import get_stream

result_message = "$RESULT_MESSAGE"
status = "$STATUS"

stream = get_stream()

data = {
    "status": status,
    "message": result_message,
    "session_type": "development"
}

event_id = stream.emit(
    event_type="result",
    source="user",
    data=data,
    tags=["development", "session_end"]
)

print(f"✅ 結果を記録しました")
print(f"   Event ID: {event_id}")
print(f"   Status: {status}")
print(f"   Message: {result_message}")
EOF

echo ""

# 2. 最近の開発活動を表示
echo "📊 最近の開発活動:"
source venv/bin/activate 2>/dev/null || true
python3 utils/context_api.py recent --format text

echo ""
echo "✅ 開発セッション終了！"
echo ""
echo "💡 次のステップ:"
echo "   - 開発文脈を確認: python3 utils/context_api.py ai"
echo "   - プロジェクト状態: python3 utils/context_api.py summary"
echo ""

