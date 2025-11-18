# Message応答機能 デプロイガイド

## 📋 概要

ユーザーがMessagesに投稿すると、Kana（外界翻訳層）が自動的に応答するシステムを実装しました。

**実装日**: 2025-11-18
**ステータス**: 実装完了、デプロイ準備完了
**所要時間**: 約1.5時間

---

## 🎯 実装内容

### 1. PostgreSQL TRIGGER追加

**ファイル**: `docker/postgres/003_message_notify.sql`

- `message_created`通知を発火
- `user`タイプのメッセージのみ通知（無限ループ防止）

### 2. Message Bridge Daemon

**ディレクトリ**: `message_bridge/`

構造：
```
message_bridge/
├── Dockerfile
├── requirements.txt
├── main.py
├── README.md
└── message_bridge/
    ├── __init__.py
    ├── daemon.py       # LISTEN/NOTIFY制御
    └── processor.py    # メッセージ処理・応答生成
```

**機能**:
- PostgreSQL LISTEN/NOTIFY で即座にメッセージ検知
- Claude API統合（モックモードもサポート）
- Kanaペルソナで応答生成
- エラーハンドリング

### 3. Docker統合

**ファイル**: `docker/docker-compose.yml`

- `message_bridge`サービス追加
- PostgreSQL TRIGGER自動セットアップ

---

## 🚀 デプロイ手順

### 前提条件

- Docker / Docker Compose インストール済み
- PostgreSQL Dashboard（Sprint 1-4）稼働中

### ステップ1: 既存コンテナの停止（任意）

```bash
cd /home/user/resonant-engine/docker
docker-compose down
```

### ステップ2: PostgreSQL TRIGGERの適用

**新規デプロイの場合**（データベース初期化）:
```bash
docker-compose up -d postgres
```

**既存データベースの場合**:
```bash
docker-compose up -d postgres
sleep 5  # PostgreSQL起動待機

docker-compose exec postgres psql -U resonant -d resonant_dashboard -f /docker-entrypoint-initdb.d/03_message_notify.sql
```

### ステップ3: Message Bridge起動

```bash
docker-compose up -d message_bridge
```

### ステップ4: 全サービス起動確認

```bash
docker-compose ps
```

期待される出力：
```
NAME                      STATUS
resonant_backend          Up
resonant_frontend         Up
resonant_intent_bridge    Up
resonant_message_bridge   Up      ← 新規
resonant_postgres         Up (healthy)
```

### ステップ5: ログ確認

```bash
docker-compose logs -f message_bridge
```

期待される出力：
```
🚀 Starting Message Bridge Daemon...
✅ Database connection pool established
🎧 Listening for message_created notifications...
```

---

## ✅ 動作確認

### テスト1: メッセージ投稿

```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "hiroki",
    "content": "今反応できるのは誰？",
    "message_type": "user"
  }'
```

### テスト2: Message Bridge ログ確認

```bash
docker-compose logs message_bridge --tail=5
```

期待される出力：
```
📨 Received message: abc123-xxxx-xxxx-xxxx-xxxxxxxxxxxx
🤖 Processing message from hiroki...
✅ Message abc123... processed successfully
```

### テスト3: 応答確認

```bash
curl -s http://localhost:8000/api/messages?limit=2 | python3 -m json.tool
```

期待される出力：
```json
[
  {
    "id": "...",
    "user_id": "kana",
    "content": "私はKana（外界翻訳層）です。現在、以下の機能が動作しています...",
    "message_type": "kana",
    "created_at": "2025-11-18T..."
  },
  {
    "id": "...",
    "user_id": "hiroki",
    "content": "今反応できるのは誰？",
    "message_type": "user",
    "created_at": "2025-11-18T..."
  }
]
```

### テスト4: Dashboard UIで確認

1. ブラウザで `http://localhost:3000` を開く
2. **Messages** ページに移動
3. 最新メッセージに **Kanaの応答** が表示される

---

## 🔧 Claude API本格稼働（オプション）

現在はモックモードで動作していますが、Claude APIキーを設定すると本物のAI応答に切り替わります。

### 手順

1. `.env`ファイル編集：

```bash
cd /home/user/resonant-engine/docker
nano .env  # または vim .env
```

2. APIキー追加：

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

3. Message Bridge再起動：

```bash
docker-compose restart message_bridge
```

4. ログ確認：

```bash
docker-compose logs message_bridge --tail=10
```

本物のClaude応答が生成されるようになります。

---

## 🐛 トラブルシューティング

### 問題1: Message Bridgeが起動しない

**確認手順**:
```bash
docker-compose ps message_bridge
docker-compose logs message_bridge
```

**解決策**:
```bash
# 再ビルド
docker-compose build message_bridge
docker-compose up -d message_bridge
```

### 問題2: 応答が生成されない

**確認1: TRIGGERが有効か**:
```bash
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT tgname FROM pg_trigger WHERE tgname = 'message_created_trigger';"
```

期待される出力：
```
      tgname
---------------------
 message_created_trigger
```

**確認2: Message Bridgeがリスニング中か**:
```bash
docker-compose logs message_bridge | grep "Listening"
```

**確認3: メッセージタイプ**:
`message_type='user'` のメッセージのみ処理されます。

### 問題3: PostgreSQLに接続できない

**確認**:
```bash
docker-compose exec postgres pg_isready -U resonant -d resonant_dashboard
```

**解決策**:
```bash
docker-compose restart postgres
sleep 10
docker-compose restart message_bridge
```

---

## 📊 システム状態確認コマンド集

### すべてのサービス状態

```bash
docker-compose ps
```

### Message Bridge ログ（リアルタイム）

```bash
docker-compose logs -f message_bridge
```

### 最新メッセージ5件

```bash
curl -s http://localhost:8000/api/messages?limit=5 | python3 -m json.tool
```

### データベース直接確認

```bash
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT user_id, message_type, substring(content, 1, 50) as content, created_at
   FROM messages
   ORDER BY created_at DESC
   LIMIT 5;"
```

### TRIGGERリスト

```bash
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'messages'::regclass;"
```

---

## 🎨 モックモード応答パターン

Message Bridgeはモックモードで以下のようなインテリジェントな応答を生成します：

| 入力キーワード | 応答内容 |
|--------------|---------|
| 「誰」「だれ」 | Kana/Yuno/Tsumuの紹介 |
| 「できる」「機能」 | 実装済み機能リスト |
| 「ありがと」「感謝」 | 礼儀正しい応答 |
| 「状態」「ステータス」 | システムステータス |
| その他 | 一般的な応答 + 質問例 |

---

## 📝 次のステップ

### 優先度1: Claude API本格稼働

- APIキー設定（5分）
- より自然で高度な応答

### 優先度2: フロントエンド改善

- メッセージタイプごとの表示スタイル
- Kana応答の視覚的区別（アイコン等）
- リアルタイム更新（WebSocket）

### 優先度3: 機能拡張

- 会話履歴の記憶（コンテキスト保持）
- Yuno応答の追加（思想的な応答）
- Intent連携（メッセージ→Intent自動生成）

---

## 📚 関連ドキュメント

- [Message Bridge README](../../../message_bridge/README.md)
- [Sprint 4: Intent Processing Spec](./sprint4_intent_processing_spec.md)
- [Sprint 4.5: Claude Code Integration](./sprint4.5_claude_code_integration_spec.md)

---

**作成日**: 2025-11-18
**作成者**: Claude Code (Kanaペルソナ)
**レビュー**: 未実施
**ステータス**: デプロイ準備完了
