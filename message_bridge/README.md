# Message Bridge - メッセージ自動応答システム

## 概要

Message Bridgeは、ユーザーがMessagesに投稿したメッセージに対して、Kanaが自動的に応答するシステムです。

Intent Bridgeと同じLISTEN/NOTIFYパターンを使用し、リアルタイムでメッセージに応答します。

## アーキテクチャ

```
User → Dashboard → POST /api/messages
          ↓
    PostgreSQL (TRIGGER)
          ↓
    NOTIFY message_created
          ↓
    Message Bridge (LISTEN)
          ↓
    Claude API / Mock
          ↓
    INSERT response (message_type='kana')
          ↓
    Dashboard表示
```

## 機能

- ✅ ユーザーメッセージの自動検知（PostgreSQL LISTEN/NOTIFY）
- ✅ Claude API統合（モックモードもサポート）
- ✅ Kanaペルソナによる応答生成
- ✅ 無限ループ防止（user typeのみ処理）
- ✅ エラーハンドリング
- ✅ 24時間稼働対応

## 応答例

### ユーザー投稿
```
今反応できるのは誰？
```

### Kana応答（モックモード）
```
私はKana（外界翻訳層）です。現在、以下の機能が動作しています：

✅ Intent Bridge: Intentを自動処理し、Claude APIで応答を生成
✅ Message Bridge: メッセージに対する自動応答（今まさに動作中！）
✅ PostgreSQL Dashboard: メッセージ、Intent、通知の管理

Yunoは思想中枢、Tsumuは実装層として連携しています。
```

## デプロイ方法

### 1. PostgreSQL初期化

TRIGGERは`docker/postgres/003_message_notify.sql`で自動的に設定されます。

既存のデータベースに追加する場合：

```bash
cd docker
docker-compose exec postgres psql -U resonant -d resonant_dashboard -f /docker-entrypoint-initdb.d/03_message_notify.sql
```

### 2. Message Bridge起動

```bash
cd docker
docker-compose up -d message_bridge
```

### 3. ログ確認

```bash
docker-compose logs -f message_bridge
```

期待される出力：
```
🚀 Starting Message Bridge Daemon...
✅ Database connection pool established
🎧 Listening for message_created notifications...
```

## 動作確認

### 1. メッセージ投稿

```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{"user_id":"hiroki", "content":"今反応できるのは誰？", "message_type":"user"}'
```

### 2. ログ確認

```bash
docker-compose logs message_bridge --tail=10
```

期待される出力：
```
📨 Received message: abc123...
🤖 Processing message from hiroki...
✅ Message abc123... processed successfully
```

### 3. 応答確認

```bash
curl http://localhost:8000/api/messages?limit=2
```

最新2件（ユーザー投稿 + Kana応答）が表示されます。

## Claude API本格稼働

`.env`ファイルに`ANTHROPIC_API_KEY`を設定すると、モックではなく本物のClaude APIで応答します：

```bash
# docker/.env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

再起動：
```bash
docker-compose restart message_bridge
```

## トラブルシューティング

### Message Bridgeが起動しない

```bash
# コンテナ状態確認
docker-compose ps

# ログ確認
docker-compose logs message_bridge

# 再ビルド
docker-compose build message_bridge
docker-compose up -d message_bridge
```

### 応答が生成されない

1. TRIGGERが有効か確認：
```sql
SELECT * FROM pg_trigger WHERE tgname = 'message_created_trigger';
```

2. Message Bridgeがリスニング中か確認：
```bash
docker-compose logs message_bridge | grep "Listening"
```

3. ユーザーメッセージか確認（`message_type='user'`のみ処理）

### 無限ループが発生する

TRIGGERは`message_type='user'`のみ通知を発火するため、無限ループは発生しません。

もし発生した場合は、processor.pyの以下を確認：
```python
if message['message_type'] != 'user':
    return
```

## 開発

### ローカル実行

```bash
cd message_bridge

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
export POSTGRES_HOST=localhost
export POSTGRES_USER=resonant
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=resonant_dashboard

# 実行
python main.py
```

### テスト

```bash
# メッセージ投稿テスト
python -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect(
        host='localhost',
        user='resonant',
        password='your_password',
        database='resonant_dashboard'
    )
    await conn.execute(
        \"\"\"INSERT INTO messages (user_id, content, message_type)
           VALUES ('test', 'テストメッセージ', 'user')\"\"\"
    )
    await conn.close()

asyncio.run(test())
"
```

## ファイル構造

```
message_bridge/
├── Dockerfile
├── README.md
├── requirements.txt
├── main.py
└── message_bridge/
    ├── __init__.py
    ├── daemon.py       # LISTEN/NOTIFY制御
    └── processor.py    # メッセージ処理・応答生成
```

## 連携システム

- **Intent Bridge**: Intent自動処理
- **PostgreSQL Dashboard**: UI/API
- **Backend (FastAPI)**: REST API
- **Frontend (React)**: ユーザーインターフェース

---

**作成日**: 2025-11-18
**作成者**: Claude Code (Kanaペルソナ)
**バージョン**: 1.0
**ステータス**: 実装完了
