#!/bin/bash
# Message Response Feature - 動作確認テストスクリプト

set -e

API_URL="${API_URL:-http://localhost:8000}"
MESSAGES_ENDPOINT="$API_URL/api/messages"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Message Response Feature - 動作確認テスト"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# テスト1: サービス状態確認
echo "📋 テスト1: サービス状態確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /home/user/resonant-engine/docker

if docker-compose ps | grep -q "resonant_message_bridge.*Up"; then
    echo -e "${GREEN}✅ Message Bridge: 稼働中${NC}"
else
    echo -e "${RED}❌ Message Bridge: 停止${NC}"
    echo "起動してください: docker-compose up -d message_bridge"
    exit 1
fi

if docker-compose ps | grep -q "resonant_postgres.*Up"; then
    echo -e "${GREEN}✅ PostgreSQL: 稼働中${NC}"
else
    echo -e "${RED}❌ PostgreSQL: 停止${NC}"
    exit 1
fi

if docker-compose ps | grep -q "resonant_backend.*Up"; then
    echo -e "${GREEN}✅ Backend API: 稼働中${NC}"
else
    echo -e "${RED}❌ Backend API: 停止${NC}"
    exit 1
fi

echo ""

# テスト2: TRIGGER確認
echo "📋 テスト2: PostgreSQL TRIGGER確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TRIGGER_CHECK=$(docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -t -c \
  "SELECT COUNT(*) FROM pg_trigger WHERE tgname = 'message_created_trigger';")

if [ "$TRIGGER_CHECK" -eq 1 ]; then
    echo -e "${GREEN}✅ message_created_trigger: 設定済み${NC}"
else
    echo -e "${RED}❌ message_created_trigger: 未設定${NC}"
    echo "TRIGGERを設定してください:"
    echo "docker-compose exec postgres psql -U resonant -d resonant_dashboard -f /docker-entrypoint-initdb.d/03_message_notify.sql"
    exit 1
fi

echo ""

# テスト3: Message Bridge ログ確認
echo "📋 テスト3: Message Bridge ログ確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker-compose logs message_bridge --tail=20 | grep -q "Listening for message_created"; then
    echo -e "${GREEN}✅ Message Bridge: リスニング中${NC}"
else
    echo -e "${YELLOW}⚠️  Message Bridge: リスニング状態が不明${NC}"
    echo "ログ確認: docker-compose logs message_bridge"
fi

echo ""

# テスト4: メッセージ投稿
echo "📋 テスト4: メッセージ投稿"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEST_MESSAGE="テスト: 今反応できるのは誰？ ($(date +%H:%M:%S))"

echo "投稿メッセージ: $TEST_MESSAGE"

RESPONSE=$(curl -s -X POST "$MESSAGES_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"test-user\",
    \"content\": \"$TEST_MESSAGE\",
    \"message_type\": \"user\"
  }")

MESSAGE_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")

if [ -n "$MESSAGE_ID" ]; then
    echo -e "${GREEN}✅ メッセージ投稿成功: $MESSAGE_ID${NC}"
else
    echo -e "${RED}❌ メッセージ投稿失敗${NC}"
    echo "レスポンス: $RESPONSE"
    exit 1
fi

echo ""

# テスト5: Message Bridge 処理ログ確認
echo "📋 テスト5: Message Bridge 処理ログ確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "処理完了を待機中（最大10秒）..."
sleep 3

PROCESSING_LOG=$(docker-compose logs message_bridge --tail=10)

if echo "$PROCESSING_LOG" | grep -q "Received message"; then
    echo -e "${GREEN}✅ メッセージ検知: 確認${NC}"
else
    echo -e "${RED}❌ メッセージ検知: 未確認${NC}"
fi

if echo "$PROCESSING_LOG" | grep -q "Processing message"; then
    echo -e "${GREEN}✅ メッセージ処理: 実行中${NC}"
else
    echo -e "${YELLOW}⚠️  メッセージ処理: ログ未確認${NC}"
fi

if echo "$PROCESSING_LOG" | grep -q "processed successfully"; then
    echo -e "${GREEN}✅ 処理完了: 成功${NC}"
else
    echo -e "${YELLOW}⚠️  処理完了: ログ未確認（処理中の可能性）${NC}"
fi

echo ""

# テスト6: Kana応答確認
echo "📋 テスト6: Kana応答確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "応答取得を待機中（最大5秒）..."
sleep 2

MESSAGES=$(curl -s "$MESSAGES_ENDPOINT?limit=2")
KANA_MESSAGE=$(echo "$MESSAGES" | python3 -c "
import sys, json
messages = json.load(sys)
for msg in messages:
    if msg.get('message_type') == 'kana':
        print(msg.get('content', '')[:100])
        break
" 2>/dev/null || echo "")

if [ -n "$KANA_MESSAGE" ]; then
    echo -e "${GREEN}✅ Kana応答: 確認${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📨 Kanaからの応答:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$KANA_MESSAGE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo -e "${RED}❌ Kana応答: 未確認${NC}"
    echo "最新メッセージ:"
    echo "$MESSAGES" | python3 -m json.tool 2>/dev/null || echo "$MESSAGES"
fi

echo ""

# テスト7: データベース直接確認
echo "📋 テスト7: データベース直接確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT
    user_id,
    message_type,
    substring(content, 1, 60) as content_preview,
    created_at
   FROM messages
   ORDER BY created_at DESC
   LIMIT 3;"

echo ""

# 最終結果
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 テスト完了"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -n "$KANA_MESSAGE" ]; then
    echo -e "${GREEN}✅ Message Response Feature: 正常動作${NC}"
    echo ""
    echo "次のステップ:"
    echo "1. Dashboard UI (http://localhost:3000) で確認"
    echo "2. Claude API本格稼働 (.env に ANTHROPIC_API_KEY 設定)"
    echo "3. 詳細ログ確認: docker-compose logs -f message_bridge"
else
    echo -e "${YELLOW}⚠️  一部確認できない項目があります${NC}"
    echo "詳細ログ確認: docker-compose logs message_bridge"
fi

echo ""
