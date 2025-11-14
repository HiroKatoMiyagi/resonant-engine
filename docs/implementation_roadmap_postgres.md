# Resonant Platform - 実装ロードマップ（PostgreSQL直接開始版）

---

## 🎯 前提

- ❌ Notion連携なし（最初から自前DB）
- ❌ SQLiteなし（最初からPostgreSQL）
- ✅ 開発環境 = 本番環境（Docker Compose）
- ✅ ローカル開発 → Oracle Cloud デプロイ

**期間: 4週間で本番稼働**

---

## 📅 Week 1-2: コア機能実装

### 環境構築（Day 1）

```bash
# プロジェクト構造作成
cd /Users/zero/Projects/resonant-engine
mkdir -p dashboard/{frontend,backend}

# docker-compose.yml 作成
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  frontend:
    build: ./dashboard/frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  backend:
    build: ./dashboard/backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://resonant:password@db:5432/resonant
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=resonant
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=resonant
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

# 一発起動
docker-compose up -d
```

### データベース設計（Day 1-2）

```sql
-- /dashboard/backend/schema.sql

-- ユーザー
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 仕様書（Notionの代替）
CREATE TABLE specs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  content TEXT,  -- Markdown
  status TEXT DEFAULT 'draft',
  sync_trigger BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- メッセージ
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  thread_id UUID,
  sender TEXT NOT NULL,  -- 'user', 'yuno', 'kana', 'system'
  content TEXT NOT NULL,
  intent_id UUID,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Intent
CREATE TABLE intents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  type TEXT NOT NULL,  -- 'review_spec', 'create_task', etc.
  data JSONB,
  status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'error'
  source TEXT,  -- 'message', 'spec_trigger', 'api'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);

-- 通知
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  body TEXT,
  link TEXT,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_specs_user_id ON specs(user_id);
CREATE INDEX idx_specs_sync_trigger ON specs(sync_trigger) WHERE sync_trigger = TRUE;
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_thread_id ON messages(thread_id);
CREATE INDEX idx_intents_status ON intents(status);
CREATE INDEX idx_notifications_user_id_read ON notifications(user_id, read);
```

### バックエンド実装（Day 3-7）

```python
# /dashboard/backend/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベース接続プール
@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(
        "postgresql://resonant:password@db:5432/resonant"
    )

# メッセージAPI
@app.post("/api/messages")
async def send_message(message: str):
    """メッセージ受信 → Intent生成"""
    async with app.state.pool.acquire() as conn:
        # メッセージ保存
        msg_id = await conn.fetchval("""
            INSERT INTO messages (sender, content)
            VALUES ('user', $1)
            RETURNING id
        """, message)
        
        # Intent生成
        intent = parse_message_to_intent(message)
        if intent:
            intent_id = await conn.fetchval("""
                INSERT INTO intents (type, data, source)
                VALUES ($1, $2, 'message')
                RETURNING id
            """, intent['type'], intent['data'])
            
            # メッセージにIntent紐付け
            await conn.execute("""
                UPDATE messages SET intent_id = $1 WHERE id = $2
            """, intent_id, msg_id)
        
        return {"message_id": msg_id, "intent_id": intent_id}

# 仕様書API
@app.get("/api/specs")
async def get_specs():
    """仕様書一覧取得"""
    async with app.state.pool.acquire() as conn:
        specs = await conn.fetch("SELECT * FROM specs ORDER BY updated_at DESC")
        return [dict(spec) for spec in specs]

@app.post("/api/specs")
async def create_spec(title: str, content: str):
    """仕様書作成"""
    async with app.state.pool.acquire() as conn:
        spec_id = await conn.fetchval("""
            INSERT INTO specs (title, content)
            VALUES ($1, $2)
            RETURNING id
        """, title, content)
        return {"spec_id": spec_id}

# WebSocket（リアルタイム通知）
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 通知をpush
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        pass
```

### フロントエンド実装（Day 8-14）

```tsx
// /dashboard/frontend/src/App.tsx
import { useState, useEffect } from 'react';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    await fetch('http://localhost:8000/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input })
    });
    setInput('');
    loadMessages();
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-2xl mb-4">Resonant Dashboard</h1>
      
      {/* メッセージ一覧 */}
      <div className="mb-4 space-y-2">
        {messages.map(msg => (
          <div key={msg.id} className="bg-gray-800 p-3 rounded">
            <span className="font-bold">{msg.sender}: </span>
            {msg.content}
          </div>
        ))}
      </div>
      
      {/* 入力欄 */}
      <div className="flex gap-2">
        <input
          className="flex-1 bg-gray-800 p-2 rounded"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="メッセージを入力..."
        />
        <button
          className="bg-blue-600 px-4 py-2 rounded"
          onClick={sendMessage}
        >
          送信
        </button>
      </div>
    </div>
  );
}
```

**Week 1-2 完了時点:**
- ✅ ローカルで動作するダッシュボード
- ✅ メッセージ送受信
- ✅ PostgreSQLへのデータ保存
- ✅ 基本的なIntent生成

---

## 📅 Week 3: Intent処理・デーモン統合

### Intent処理システム（Day 15-17）

```python
# /dashboard/backend/intent_processor.py
import asyncpg

async def process_intent(intent_id: str):
    """Intentを処理"""
    async with pool.acquire() as conn:
        intent = await conn.fetchrow("""
            SELECT * FROM intents WHERE id = $1
        """, intent_id)
        
        # ステータス更新
        await conn.execute("""
            UPDATE intents SET status = 'processing' WHERE id = $1
        """, intent_id)
        
        try:
            if intent['type'] == 'review_spec':
                # 仕様書レビュー
                result = await review_spec(intent['data'])
            elif intent['type'] == 'create_task':
                # タスク作成
                result = await create_task(intent['data'])
            
            # 完了
            await conn.execute("""
                UPDATE intents 
                SET status = 'completed', completed_at = NOW()
                WHERE id = $1
            """, intent_id)
            
            # 通知作成
            await conn.execute("""
                INSERT INTO notifications (title, body, link)
                VALUES ($1, $2, $3)
            """, "処理完了", result['message'], result['link'])
            
        except Exception as e:
            await conn.execute("""
                UPDATE intents SET status = 'error' WHERE id = $1
            """, intent_id)
```

### デーモン統合（Day 18-21）

```python
# daemon/intent_bridge.py
"""
既存のresonant_daemon.pyと統合
intent_protocol.json → PostgreSQL Intent テーブル
"""
import asyncpg
import asyncio

async def watch_intents():
    """Intent テーブルを監視して処理"""
    pool = await asyncpg.create_pool(
        "postgresql://resonant:password@localhost:5432/resonant"
    )
    
    while True:
        async with pool.acquire() as conn:
            # pending状態のIntentを取得
            intents = await conn.fetch("""
                SELECT * FROM intents 
                WHERE status = 'pending'
                ORDER BY created_at
                LIMIT 10
            """)
            
            for intent in intents:
                await process_intent(intent['id'])
        
        await asyncio.sleep(5)  # 5秒ごとにチェック

if __name__ == "__main__":
    asyncio.run(watch_intents())
```

**Week 3 完了時点:**
- ✅ Intent処理の自動化
- ✅ デーモンとの統合
- ✅ 通知システム
- ✅ リアルタイム更新

---

## 📅 Week 4: Oracle Cloud デプロイ

### Oracle Cloud準備（Day 22-23）

1. Oracle Cloudアカウント作成（無料）
2. Compute Instance作成
   - Shape: Ampere A1 (4 OCPU, 24GB RAM)
   - OS: Ubuntu 22.04
3. Autonomous Database作成
   - Type: Shared Infrastructure
   - Database version: 19c
4. ネットワーク設定
   - Ingress: 80, 443, 8000
   - Security List設定

### デプロイ（Day 24-25）

```bash
# SSH接続
ssh ubuntu@<public_ip>

# Docker インストール
sudo apt update
sudo apt install -y docker.io docker-compose

# コードデプロイ
git clone https://github.com/your-repo/resonant-engine.git
cd resonant-engine

# 環境変数設定
cat > .env << 'EOF'
DATABASE_URL=postgresql://admin:password@autonomous-db-host:1522/resonant
SECRET_KEY=your-secret-key
EOF

# 起動
docker-compose -f docker-compose.prod.yml up -d
```

### HTTPS設定（Day 26）

```bash
# Certbot インストール
sudo apt install -y certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d resonant.example.com
```

### 監視・ログ設定（Day 27-28）

```yaml
# docker-compose.prod.yml に追加
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

**Week 4 完了時点:**
- ✅ Oracle Cloudで本番稼働
- ✅ HTTPS対応
- ✅ 監視・ログ
- ✅ 月額コスト: $0

---

## 🎯 4週間後の成果

### 完成するもの

1. **Resonant Dashboard**
   - Slack風メッセージUI
   - 仕様書管理（Notion不要）
   - Intent自動処理
   - リアルタイム通知

2. **インフラ**
   - Oracle Cloud Free Tier
   - PostgreSQL（20GB）
   - Docker化
   - HTTPS対応

3. **コスト**
   - 月額: $0
   - 対応ユーザー: 500人まで

### できること

```
宏啓: 「API設計レビューして」
  ↓ 3秒
システム: 「処理中...」
  ↓ 2分
システム: 「✅ 完了！GitHub Issue #123」
  ↓
宏啓: Issue確認 → 指示
```

---

## 📋 技術スタック（最終版）

### 開発環境
- Docker Compose
- PostgreSQL 15
- FastAPI + Python 3.11
- React 18 + Vite
- Tailwind CSS

### 本番環境
- Oracle Cloud Free Tier
- Autonomous Database (PostgreSQL互換)
- Docker Compose（開発と同じ）
- Nginx + Let's Encrypt

**開発環境と本番環境が完全一致 = トラブル最小化**

---

## 🚀 最初の一歩

### 今日やること（30分）

```bash
# 1. ディレクトリ作成
cd /Users/zero/Projects/resonant-engine
mkdir -p dashboard/{frontend,backend}

# 2. docker-compose.yml 作成
# （上記の内容をコピー）

# 3. 起動
docker-compose up -d

# 4. 確認
open http://localhost:3000
```

### 明日以降

- Day 1-2: データベース設計
- Day 3-7: バックエンド実装
- Day 8-14: フロントエンド実装
- Day 15-21: Intent処理・デーモン統合
- Day 22-28: Oracle Cloud デプロイ

**4週間で本番稼働！**

---

## 💡 この設計の利点

1. **シンプル**: SQLiteを挟まない
2. **高速**: PostgreSQLから直接開始
3. **実用的**: 開発環境 = 本番環境
4. **低コスト**: Oracle Free Tier = $0
5. **拡張性**: PostgreSQL = 将来のAWS移行も簡単

**Phase 1（SQLite）をスキップすることで2週間短縮！**
