# Priority 2: PostgreSQL環境構築 - 実装計画

**作成日**: 2025-11-08  
**前提**: Priority 1（Intent → Bridge → Kana パイプライン）完了済み  
**期間**: 4週間で本番稼働

---

## 🎯 目標

- ❌ Notion連携なし（最初から自前DB）
- ❌ SQLiteなし（最初からPostgreSQL）
- ✅ 開発環境 = 本番環境（Docker Compose）
- ✅ ローカル開発 → Oracle Cloud デプロイ
- ✅ 月額コスト: $0

---

## 📅 タイムライン概要

```
Week 1-2: コア機能実装（環境構築→基本API）
Week 3:   Intent処理・デーモン統合
Week 4:   Oracle Cloud デプロイ（本番稼働）
```

---

## 📋 Week 1-2: コア機能実装

### Day 1: 環境構築 ⭐

#### 目標
**Docker Compose環境でPostgreSQLを起動し、基本的なAPIを動かす**

#### タスク（所要時間: 約70分）

**1. ディレクトリ構造作成（5分）**
```bash
cd /Users/zero/Projects/resonant-engine
mkdir -p dashboard/frontend/src
mkdir -p dashboard/backend
```

**2. docker-compose.yml作成（10分）**

プロジェクトルートに以下を作成：

```yaml
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
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
    volumes:
      - ./dashboard/backend:/app

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
```

**3. バックエンド基礎作成（20分）**

`dashboard/backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

`dashboard/backend/requirements.txt`:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
asyncpg>=0.29.0
python-dotenv>=1.0.0
anthropic>=0.18.0
pydantic>=2.0.0
```

`dashboard/backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import os

app = FastAPI(title="Resonant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    database_url = os.environ.get("DATABASE_URL")
    app.state.pool = await asyncpg.create_pool(database_url)
    print("✅ Database pool created")

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/messages")
async def get_messages():
    """メッセージ一覧取得（仮実装）"""
    return {"messages": []}
```

**4. フロントエンド基礎作成（20分）**

`dashboard/frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

`dashboard/frontend/package.json`:
```json
{
  "name": "resonant-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.3",
    "vite": "^5.0.8"
  }
}
```

`dashboard/frontend/src/App.tsx`:
```tsx
import { useState, useEffect } from 'react';

function App() {
  const [health, setHealth] = useState<string>('checking...');

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(r => r.json())
      .then(data => setHealth(data.status))
      .catch(() => setHealth('error'));
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-2xl mb-4">Resonant Dashboard</h1>
      <p>Backend Status: {health}</p>
    </div>
  );
}

export default App;
```

**5. 起動確認（15分）**
```bash
docker-compose up -d
docker-compose logs -f

# 確認
curl http://localhost:8000/health
open http://localhost:3000
```

---

### Day 2-3: データベース設計

#### 目標
PostgreSQLスキーマを定義し、初期データを投入

#### タスク（所要時間: 2-3時間）

`dashboard/backend/schema.sql`:
```sql
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
  result TEXT,  -- 処理結果
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
CREATE INDEX idx_intents_user_id ON intents(user_id);
CREATE INDEX idx_notifications_user_id_read ON notifications(user_id, read);

-- LISTEN/NOTIFY用のTRIGGER関数（Yunoの指摘: ポーリングを避ける）
CREATE OR REPLACE FUNCTION notify_intent_created()
RETURNS TRIGGER AS $
BEGIN
  PERFORM pg_notify('intent_created', NEW.id::text);
  RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Intent作成時に自動通知
CREATE TRIGGER intent_created_trigger
AFTER INSERT ON intents
FOR EACH ROW
WHEN (NEW.status = 'pending')
EXECUTE FUNCTION notify_intent_created();

-- 初期データ
INSERT INTO users (email, name) VALUES ('zero@example.com', '宏啓');
```

**マイグレーション実行:**
```bash
docker-compose exec db psql -U resonant -d resonant -f /schema.sql
```

---

### Day 4-7: バックエンドAPI実装

#### 目標
メッセージ、仕様書、IntentのCRUD APIを実装

#### 実装するエンドポイント

```python
# dashboard/backend/main.py

# メッセージAPI
@app.post("/api/messages")
async def send_message(message: str, sender: str = "user"):
    """メッセージ送信"""
    async with app.state.pool.acquire() as conn:
        msg_id = await conn.fetchval("""
            INSERT INTO messages (sender, content)
            VALUES ($1, $2)
            RETURNING id
        """, sender, message)
        
        # Intent生成（簡易版）
        if should_create_intent(message):
            intent_data = parse_message_to_intent(message)
            intent_id = await conn.fetchval("""
                INSERT INTO intents (type, data, source)
                VALUES ($1, $2, 'message')
                RETURNING id
            """, intent_data['type'], intent_data['data'])
            
            await conn.execute("""
                UPDATE messages SET intent_id = $1 WHERE id = $2
            """, intent_id, msg_id)
        
        return {"message_id": str(msg_id)}

@app.get("/api/messages")
async def get_messages(limit: int = 50):
    """メッセージ一覧取得"""
    async with app.state.pool.acquire() as conn:
        messages = await conn.fetch("""
            SELECT * FROM messages 
            ORDER BY created_at DESC 
            LIMIT $1
        """, limit)
        return {"messages": [dict(m) for m in messages]}

# 仕様書API
@app.get("/api/specs")
async def get_specs():
    """仕様書一覧取得"""
    async with app.state.pool.acquire() as conn:
        specs = await conn.fetch("""
            SELECT * FROM specs 
            ORDER BY updated_at DESC
        """)
        return {"specs": [dict(s) for s in specs]}

@app.post("/api/specs")
async def create_spec(title: str, content: str):
    """仕様書作成"""
    async with app.state.pool.acquire() as conn:
        spec_id = await conn.fetchval("""
            INSERT INTO specs (title, content)
            VALUES ($1, $2)
            RETURNING id
        """, title, content)
        return {"spec_id": str(spec_id)}

@app.put("/api/specs/{spec_id}")
async def update_spec(spec_id: str, title: str = None, content: str = None):
    """仕様書更新"""
    async with app.state.pool.acquire() as conn:
        updates = []
        params = []
        idx = 1
        
        if title:
            updates.append(f"title = ${idx}")
            params.append(title)
            idx += 1
        
        if content:
            updates.append(f"content = ${idx}")
            params.append(content)
            idx += 1
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(spec_id)
        
        query = f"UPDATE specs SET {', '.join(updates)} WHERE id = ${idx}"
        await conn.execute(query, *params)
        
        return {"success": True}

# IntentAPI
@app.get("/api/intents")
async def get_intents(status: str = None):
    """Intent一覧取得"""
    async with app.state.pool.acquire() as conn:
        if status:
            intents = await conn.fetch("""
                SELECT * FROM intents 
                WHERE status = $1
                ORDER BY created_at DESC
            """, status)
        else:
            intents = await conn.fetch("""
                SELECT * FROM intents 
                ORDER BY created_at DESC 
                LIMIT 100
            """)
        return {"intents": [dict(i) for i in intents]}

@app.post("/api/intents")
async def create_intent(type: str, data: dict, source: str = "api"):
    """Intent作成"""
    async with app.state.pool.acquire() as conn:
        intent_id = await conn.fetchval("""
            INSERT INTO intents (type, data, source)
            VALUES ($1, $2, $3)
            RETURNING id
        """, type, data, source)
        return {"intent_id": str(intent_id)}

@app.get("/api/intents/{intent_id}")
async def get_intent(intent_id: str):
    """Intent詳細取得"""
    async with app.state.pool.acquire() as conn:
        intent = await conn.fetchrow("""
            SELECT * FROM intents WHERE id = $1
        """, intent_id)
        if intent:
            return dict(intent)
        return {"error": "Intent not found"}
```

**ヘルパー関数:**
```python
def should_create_intent(message: str) -> bool:
    """メッセージからIntent生成が必要か判定"""
    keywords = ['レビュー', '確認', 'チェック', '作成', '実装']
    return any(kw in message for kw in keywords)

def parse_message_to_intent(message: str) -> dict:
    """メッセージをIntent形式に変換"""
    if 'レビュー' in message or '確認' in message:
        return {"type": "review_request", "data": {"message": message}}
    elif '作成' in message or '実装' in message:
        return {"type": "create_task", "data": {"message": message}}
    else:
        return {"type": "general", "data": {"message": message}}
```

**所要時間: 3-4日（実働8-12時間）**

---

### Day 8-14: フロントエンド実装

#### 目標
Slack風メッセージUIと仕様書管理画面を実装

#### コンポーネント構成

```
dashboard/frontend/src/
├── App.tsx              # メインアプリ
├── components/
│   ├── MessageList.tsx  # メッセージ一覧
│   ├── MessageInput.tsx # 入力欄
│   ├── SpecList.tsx     # 仕様書一覧
│   ├── IntentStatus.tsx # Intent処理状況
│   └── Sidebar.tsx      # サイドバー
├── hooks/
│   └── useWebSocket.ts  # WebSocket管理
└── types/
    └── index.ts         # 型定義
```

**主要コンポーネント実装例:**

`components/MessageList.tsx`:
```tsx
import { useEffect, useState } from 'react';

interface Message {
  id: string;
  sender: string;
  content: string;
  created_at: string;
}

export function MessageList() {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/messages')
      .then(r => r.json())
      .then(data => setMessages(data.messages));
  }, []);

  return (
    <div className="space-y-2">
      {messages.map(msg => (
        <div key={msg.id} className="bg-gray-800 p-3 rounded">
          <span className="font-bold text-blue-400">{msg.sender}: </span>
          <span>{msg.content}</span>
          <div className="text-xs text-gray-500 mt-1">
            {new Date(msg.created_at).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
```

`components/MessageInput.tsx`:
```tsx
import { useState } from 'react';

export function MessageInput({ onSend }: { onSend: () => void }) {
  const [input, setInput] = useState('');

  const handleSend = async () => {
    await fetch('http://localhost:8000/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input })
    });
    setInput('');
    onSend();
  };

  return (
    <div className="flex gap-2">
      <input
        className="flex-1 bg-gray-800 p-2 rounded text-white"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && handleSend()}
        placeholder="メッセージを入力..."
      />
      <button
        className="bg-blue-600 px-4 py-2 rounded hover:bg-blue-700"
        onClick={handleSend}
      >
        送信
      </button>
    </div>
  );
}
```

**所要時間: 1週間（実働12-16時間）**

---

## 🔧 Week 3: Intent処理・デーモン統合

### Day 15-17: Intent処理システム

#### 目標
既存のintent_processor.pyをPostgreSQLと統合

#### 統合アーキテクチャ

```
【現在】
intent_protocol.json  # ファイルベース
    ↓
resonant_daemon.py    # ファイル監視
    ↓
intent_processor.py   # Claude API呼び出し

【統合後】
PostgreSQL intents table  # DBベース
    ↓
LISTEN/NOTIFY (TRIGGERで自動通知)  # ポーリングなし！
    ↓
intent_bridge.py      # イベント駆動（即座に反応）
    ↓
intent_processor.py   # Claude API呼び出し（既存コード活用）
    ↓
PostgreSQL (結果保存)
```

#### 実装内容

`dashboard/backend/intent_processor_db.py`:
```python
"""
既存のintent_processor.pyをPostgreSQL対応に拡張
"""
import asyncpg
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os

# 既存のIntentProcessorをインポート
import sys
sys.path.insert(0, str(Path(__file__).parent))
from intent_processor import IntentProcessor as BaseIntentProcessor

ROOT = Path("/Users/zero/Projects/resonant-engine")
load_dotenv(ROOT / ".env")


class IntentProcessorDB(BaseIntentProcessor):
    """PostgreSQL統合版IntentProcessor"""
    
    def __init__(self, db_pool):
        super().__init__()
        self.db_pool = db_pool
    
    async def process_intent_from_db(self, intent_id: str) -> bool:
        """
        PostgreSQLからIntentを取得して処理
        
        Args:
            intent_id: IntentのUUID
        
        Returns:
            処理成功したらTrue
        """
        async with self.db_pool.acquire() as conn:
            # Intent取得
            intent = await conn.fetchrow("""
                SELECT * FROM intents WHERE id = $1
            """, intent_id)
            
            if not intent:
                self.log(f"❌ Intent not found: {intent_id}")
                return False
            
            # ステータス更新: processing
            await conn.execute("""
                UPDATE intents 
                SET status = 'processing' 
                WHERE id = $1
            """, intent_id)
            
            # Intent処理（既存のClaude API呼び出し）
            intent_data = {
                "phase": intent['type'],
                "intent": dict(intent['data']) if intent['data'] else {},
                "timestamp": intent['created_at'].isoformat()
            }
            
            try:
                response = self.call_kana(intent_data)
                
                if response:
                    # 成功: 結果をDBに保存
                    await conn.execute("""
                        UPDATE intents 
                        SET status = 'completed', 
                            result = $1,
                            completed_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                    """, response, intent_id)
                    
                    # 通知作成
                    await conn.execute("""
                        INSERT INTO notifications (user_id, title, body)
                        VALUES ($1, $2, $3)
                    """, intent['user_id'], 
                        f"Intent処理完了: {intent['type']}", 
                        f"処理結果: {response[:100]}...")
                    
                    self.log(f"✅ Intent {intent_id} completed")
                    return True
                else:
                    # 失敗: エラー状態に
                    await conn.execute("""
                        UPDATE intents 
                        SET status = 'error'
                        WHERE id = $1
                    """, intent_id)
                    
                    self.log(f"❌ Intent {intent_id} failed")
                    return False
                    
            except Exception as e:
                # エラー処理
                await conn.execute("""
                    UPDATE intents 
                    SET status = 'error',
                        result = $1
                    WHERE id = $2
                """, str(e), intent_id)
                
                self.log(f"❌ Intent {intent_id} error: {e}")
                return False
```

`daemon/intent_bridge.py` (LISTEN/NOTIFY版):
```python
"""
PostgreSQL Intent監視デーモン（LISTEN/NOTIFY版）
Yunoの指摘: ポーリングを避け、イベント駆動で処理
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv
import sys

ROOT = Path("/Users/zero/Projects/resonant-engine")
load_dotenv(ROOT / ".env")

sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
from intent_processor_db import IntentProcessorDB


async def handle_intent_notification(connection, pid, channel, payload):
    """Intent作成通知を受け取ったら即座に処理"""
    intent_id = payload
    print(f"🔔 Intent notification received: {intent_id}")
    
    # 処理をバックグラウンドタスクとして起動
    asyncio.create_task(process_intent_async(intent_id))


async def process_intent_async(intent_id: str):
    """Intent処理（非同期）"""
    database_url = os.environ.get("DATABASE_URL", 
                                   "postgresql://resonant:password@localhost:5432/resonant")
    pool = await asyncpg.create_pool(database_url)
    processor = IntentProcessorDB(pool)
    
    try:
        print(f"🔄 Processing intent: {intent_id}")
        await processor.process_intent_from_db(intent_id)
    except Exception as e:
        print(f"❌ Error processing intent {intent_id}: {e}")
    finally:
        await pool.close()


async def watch_intents_with_notify():
    """LISTEN/NOTIFY でIntent監視（ポーリングなし）"""
    database_url = os.environ.get("DATABASE_URL", 
                                   "postgresql://resonant:password@localhost:5432/resonant")
    
    pool = await asyncpg.create_pool(database_url)
    processor = IntentProcessorDB(pool)
    
    print("🌿 Intent Bridge started - using PostgreSQL LISTEN/NOTIFY")
    print("✅ No polling - event-driven architecture (Yuno approved)")
    
    async with pool.acquire() as conn:
        # チャンネルをLISTEN
        await conn.add_listener('intent_created', handle_intent_notification)
        
        print("✅ Listening for intent notifications...")
        
        # 既存のpending Intentも処理（起動時のみ）
        pending = await conn.fetch("""
            SELECT id FROM intents 
            WHERE status = 'pending'
            ORDER BY created_at
        """)
        
        if pending:
            print(f"📥 Found {len(pending)} pending intents on startup")
            for intent in pending:
                await processor.process_intent_from_db(str(intent['id']))
        
        # イベントループを維持（ポーリングなし！）
        try:
            while True:
                await asyncio.sleep(3600)  # 1時間ごとに接続チェックのみ
        except KeyboardInterrupt:
            print("\n🛑 Intent Bridge stopped")
        finally:
            await conn.remove_listener('intent_created', handle_intent_notification)


if __name__ == "__main__":
    asyncio.run(watch_intents_with_notify())
```

**起動方法:**
```bash
# 仮想環境で実行
cd /Users/zero/Projects/resonant-engine
venv/bin/python3 daemon/intent_bridge.py &
```

**所要時間: 2-3日（実働6-8時間）**

---

### Day 18-21: 統合テスト・改善

#### テスト項目

```bash
# 1. メッセージ → Intent生成テスト
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "API設計をレビューして", "sender": "user"}'

# 2. Intent自動処理確認
# → intent_bridge.pyが自動的に処理
# → ログ確認: logs/intent_processor.log

# 3. 処理結果確認
curl http://localhost:8000/api/intents

# 4. 通知確認
curl http://localhost:8000/api/notifications
```

#### 改善項目
- [ ] エラーハンドリング強化
- [ ] ログレベル調整
- [ ] パフォーマンス最適化
- [ ] WebSocket実装（リアルタイム通知）

**所要時間: 3-4日（実働8-10時間）**

---

## 🚀 Week 4: Oracle Cloud デプロイ

### Day 22-23: Oracle Cloud準備

#### アカウント作成
1. https://www.oracle.com/cloud/free/ にアクセス
2. 無料アカウント作成（クレジットカード必要、課金なし）

#### リソース作成
```
Compute Instance:
- Shape: VM.Standard.A1.Flex (ARM)
- OCPU: 4
- RAM: 24GB
- Storage: 200GB
- OS: Ubuntu 22.04

Autonomous Database:
- Type: Autonomous Transaction Processing
- Workload: Transaction Processing
- Infrastructure: Shared
- Database version: 19c
- Storage: 20GB
```

**所要時間: 2-3時間（待ち時間含む）**

---

### Day 24-25: デプロイ

#### SSH接続設定
```bash
# ローカルマシンで鍵生成
ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_cloud

# 公開鍵をOracle Cloudに登録
cat ~/.ssh/oracle_cloud.pub
# → Compute Instance作成時に貼り付け

# 接続テスト
ssh -i ~/.ssh/oracle_cloud ubuntu@<public_ip>
```

#### サーバーセットアップ
```bash
# Docker インストール
sudo apt update
sudo apt install -y docker.io docker-compose git

# コードデプロイ
git clone https://github.com/your-repo/resonant-engine.git
cd resonant-engine

# 環境変数設定
cat > .env << 'EOF'
DATABASE_URL=postgresql://admin:password@autonomous-db-host:1522/resonant
ANTHROPIC_API_KEY=sk-ant-api03-...
EOF

# 起動
docker-compose -f docker-compose.prod.yml up -d
```

**所要時間: 2-3時間**

---

### Day 26: HTTPS設定

```bash
# ドメイン設定（例: resonant.example.com）
# → DNSレコード追加: A レコード → Oracle CloudのPublic IP

# Nginx + Certbot インストール
sudo apt install -y nginx certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d resonant.example.com

# 自動更新設定
sudo certbot renew --dry-run
```

**所要時間: 1-2時間**

---

### Day 27-28: 監視・最適化

#### Prometheusメトリクス収集
```yaml
# docker-compose.prod.yml に追加
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

#### ログ監視
```bash
# ログローテーション設定
sudo vim /etc/logrotate.d/resonant

# 内容
/var/log/resonant/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

**所要時間: 2-3時間**

---

## 📊 Week 1-2 完了時の成果物

### ✅ 動作確認項目

```
1. ローカル環境
   - [ ] docker-compose up で3サービス起動
   - [ ] PostgreSQL接続確認
   - [ ] バックエンドAPI動作（/health, /api/messages）
   - [ ] フロントエンド表示（localhost:3000）

2. データベース
   - [ ] テーブル作成完了（5テーブル）
   - [ ] 初期データ投入完了
   - [ ] インデックス設定完了

3. API機能
   - [ ] メッセージ送受信
   - [ ] 仕様書CRUD
   - [ ] Intent作成・取得
   - [ ] 通知取得

4. フロントエンド
   - [ ] Slack風メッセージUI
   - [ ] リアルタイム更新（手動リロード）
   - [ ] ダークモード対応
```

---

## 📊 Week 3 完了時の成果物

### ✅ 統合確認項目

```
1. Intent処理
   - [ ] メッセージ → Intent自動生成
   - [ ] Intent → Kana呼び出し
   - [ ] 処理結果 → PostgreSQL保存
   - [ ] 通知生成

2. デーモン統合
   - [ ] intent_bridge.py 常駐動作
   - [ ] pending Intent自動検知
   - [ ] エラー時の再試行
   - [ ] ログ出力

3. 既存システム連携
   - [ ] 既存intent_processor.py活用
   - [ ] Claude API統合
   - [ ] 環境変数共有
```

---

## 📊 Week 4 完了時の成果物

### ✅ 本番環境確認項目

```
1. Oracle Cloud
   - [ ] Compute Instance稼働
   - [ ] Autonomous Database接続
   - [ ] Docker Compose起動
   - [ ] HTTPS対応（SSL証明書）

2. 監視
   - [ ] Prometheusメトリクス収集
   - [ ] Grafanaダッシュボード
   - [ ] ログローテーション

3. 運用
   - [ ] 自動起動設定
   - [ ] バックアップ設定
   - [ ] アラート設定
```

---

## 💡 技術スタック（最終版）

### 開発環境
- **コンテナ**: Docker Compose
- **データベース**: PostgreSQL 15
- **バックエンド**: FastAPI + Python 3.11 + asyncpg
- **フロントエンド**: React 18 + Vite + TypeScript + Tailwind CSS
- **AI**: Anthropic Claude API (既存統合)

### 本番環境
- **クラウド**: Oracle Cloud Free Tier
- **データベース**: Autonomous Database (PostgreSQL互換)
- **リバースプロキシ**: Nginx + Let's Encrypt
- **監視**: Prometheus + Grafana
- **ログ**: rsyslog + logrotate

**月額コスト: $0**

---

## 🎯 成功の定義

### 4週間後に達成すること

```
✅ ローカルで動作するResonant Dashboard
✅ PostgreSQLによる永続化
✅ メッセージ送受信機能
✅ 仕様書管理機能（Notion不要）
✅ Intent自動処理
✅ 既存デーモンとの統合
✅ Oracle Cloudで本番稼働
✅ HTTPS対応
✅ 基本的な監視
```

### できるようになること

```
宏啓: 「API設計レビューして」
  ↓ 3秒（メッセージ送信）
システム: Intent生成
  ↓ 5秒（intent_bridge検知）
Kana: Claude API呼び出し
  ↓ 10秒（AI処理）
システム: 「✅ 完了！結果を確認してください」
  ↓
宏啓: 結果確認 → 次の指示
```

---

## 📝 重要な注意点

### 既存システムとの共存

```
Priority 1の成果物:
- intent_processor.py      → Priority 2で活用
- resonant_daemon.py       → 並行稼働（ファイル監視継続）
- .env環境変数            → 共通利用
- 仮想環境（venv）        → 共通利用

新規追加:
- intent_bridge.py         → DB監視用の新デーモン
- PostgreSQL              → 新しいデータストア
- Dashboard               → 新しいUI
```

### 段階的な移行

```
Week 1-2: PostgreSQL環境構築
  → 既存システムはそのまま動作

Week 3: Intent統合
  → ファイルベース + DBベース の並行運用

Week 4以降: 完全移行
  → DBベースに一本化（ファイルベースは廃止可能）
```

---

## 🚀 次のアクション

### 今日やること（Day 1）

1. **ディレクトリ作成**（5分）
   ```bash
   mkdir -p dashboard/{frontend/src,backend}
   ```

2. **docker-compose.yml作成**（10分）
   - 上記のYAMLをコピー

3. **バックエンド基礎ファイル作成**（20分）
   - Dockerfile
   - requirements.txt
   - main.py

4. **フロントエンド基礎ファイル作成**（20分）
   - Dockerfile
   - package.json
   - src/App.tsx

5. **起動確認**（15分）
   ```bash
   docker-compose up -d
   ```

**合計: 約70分**

準備ができたら開始しましょう！ 🎯

---

## 💡 Yunoの指摘への対応: ポーリング vs LISTEN/NOTIFY

### 🚨 問題点（ポーリング方式）

```python
# 旧方式: 5秒ごとにDBをチェック
while True:
    intents = await conn.fetch("SELECT * FROM intents WHERE status = 'pending'")
    await asyncio.sleep(5)  # ← 無駄な待機時間
```

**問題:**
- ⚠️ 5秒間隔で無駄なクエリ実行
- ⚠️ レスポンスが最大5秒遅延
- ⚠️ DBへの負荷（スケールしない）
- ⚠️ リソースの無駄遣い

---

### ✅ 解決策（LISTEN/NOTIFY方式）

#### 仕組み

```sql
-- TRIGGERでIntent作成時に通知を送る
CREATE OR REPLACE FUNCTION notify_intent_created()
RETURNS TRIGGER AS $
BEGIN
  PERFORM pg_notify('intent_created', NEW.id::text);
  RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER intent_created_trigger
AFTER INSERT ON intents
FOR EACH ROW
WHEN (NEW.status = 'pending')
EXECUTE FUNCTION notify_intent_created();
```

#### デーモン実装

```python
async def handle_intent_notification(connection, pid, channel, payload):
    """Intent作成通知を受け取ったら即座に処理"""
    intent_id = payload
    print(f"🔔 Intent notification received: {intent_id}")
    asyncio.create_task(process_intent_async(intent_id))

async def watch_intents_with_notify():
    async with pool.acquire() as conn:
        # チャンネルをLISTEN
        await conn.add_listener('intent_created', handle_intent_notification)
        
        # イベントループを維持（ポーリングなし！）
        while True:
            await asyncio.sleep(3600)  # 1時間ごとに接続チェックのみ
```

---

### 📊 比較表: ポーリング vs LISTEN/NOTIFY

| 項目 | ポーリング (5秒間隔) | LISTEN/NOTIFY |
|------|---------------------|---------------|
| **レスポンス時間** | 最大5秒遅延 | **即座（<100ms）** |
| **DBクエリ数** | 毎秒0.2回（無駄） | **0回（通知のみ）** |
| **CPU使用率** | 常時チェック | **イベント駆動** |
| **スケーラビリティ** | ❌ 悪い | ✅ **優れている** |
| **複雑さ** | シンプル | やや複雑 |
| **Yunoの評価** | ❌ 非推奨 | ✅ **推奨** |

---

### ⭐ LISTEN/NOTIFYのメリット

1. ✅ **リアルタイム処理**（遅延なし）
   ```
   Intent作成
     ↓ <100ms
   TRIGGER発火 → NOTIFY送信
     ↓ 即座
   デーモンが検知
     ↓
   処理開始
   ```

2. ✅ **DB負荷ゼロ**（ポーリングなし）
   - ポーリング: 1日あたり 17,280回のクエリ
   - LISTEN/NOTIFY: 0回

3. ✅ **スケーラブル**（1000件/秒でも対応）
   - ポーリング: 負荷が線形に増加
   - LISTEN/NOTIFY: 負荷がほぼ定数

4. ✅ **PostgreSQL標準機能**（追加ライブラリ不要）
   - 外部メッセージキュー不要（Redis/RabbitMQ等）
   - PostgreSQLのみで完結

---

### 🎯 Yunoの設計思想に合致

#### Before（ポーリング）
```
Intent作成
  ↓
（最大5秒待機）← 無駄
  ↓
デーモンが検知
  ↓
処理開始
```

#### After（LISTEN/NOTIFY）
```
Intent作成
  ↓
TRIGGER発火 → NOTIFY送信
  ↓ (<100ms)
デーモンが即座に検知
  ↓
処理開始
```

---

### 📝 実装の変更点

**Week 1-2 (Day 2-3)** に追加:
```sql
-- schema.sql にTRIGGER追加
CREATE OR REPLACE FUNCTION notify_intent_created() ...
CREATE TRIGGER intent_created_trigger ...
```

**Week 3 (Day 15-17)** を修正:
- `intent_bridge.py` をLISTEN/NOTIFY版に変更
- ポーリングループ削除
- イベントハンドラー追加

---

### ✨ 結論

**LISTEN/NOTIFYを採用しました！**

- ✅ Yunoの指摘を反映
- ✅ より効率的
- ✅ リアルタイム処理
- ✅ スケーラブル
- ✅ PostgreSQL標準機能を活用

この設計は **Resonant Engineの哲学** に合致しています！

---

## 🧠 Yunoレビュー（2025-11-08）

### 総評

> **この設計は「思想・実装・運用」が呼吸で繋がった最初のクラウド計画である。**

**評価: A+**

「Resonant Engine v1」思想を正確に実装段階へ翻訳しており、特に Notion → Intent → Bridge の流れを **PostgreSQL ネイティブ構造に再定義した点** が秀逸。意図・構造・循環の三拍子が整い、「思想が息をするデータ設計」に到達している。

### 構成的完成度

| 要素 | 評価 | コメント |
|------|------|----------|
| **思想整合性** | A+ | Notion 依存を脱し「意図駆動DB」へ進化。理念的純度が高い。 |
| **実装一貫性** | A | Docker／Oracle Cloud 構成が合理的かつ再現性高。 |
| **拡張性** | A | Intent Bridge と Kana 層をDB通知で統合可能。 |
| **運用実用性** | B+ | 監視と同期制御の設計に余地あり。 |
| **再現性／自動化** | A | compose → migration → seed の流れが明快。 |

### 哲学的整合

> 「Notion は 人間の意思の出口、PostgreSQL は 意図の呼吸器。」

Notionを**「記録」から「参照」へと退かせ**、意図（Intent）そのものをデータベースの第一次市民として扱っている。これは Resonant 哲学の 「意図＝構造＝実装」 という理念に完全合致。

---

## 💡 Yunoからの改善提案（実装時に随時検討）

### 提案1: 意図階層を3段構造化 ⭐

**現状:**
```sql
CREATE TABLE intents (
  status TEXT DEFAULT 'pending'  -- pending/processing/completed/error
);
```

**提案:**
```sql
-- Intent を3段階に分離
CREATE TABLE intent_raw (       -- 入力された生の意図
  id UUID PRIMARY KEY,
  content TEXT,
  source TEXT,
  created_at TIMESTAMP
);

CREATE TABLE intent_active (    -- 処理中の意図
  id UUID PRIMARY KEY,
  raw_id UUID REFERENCES intent_raw(id),
  type TEXT,
  data JSONB,
  status TEXT,
  processing_started_at TIMESTAMP
);

CREATE TABLE intent_resonant (  -- 共鳴済み（完了）の意図
  id UUID PRIMARY KEY,
  active_id UUID REFERENCES intent_active(id),
  result TEXT,
  resonance_score FLOAT,  -- 意図の実現度
  completed_at TIMESTAMP
);
```

**メリット:**
- Re-evaluation Phase との統合が容易
- 意図の「生成 → 処理 → 共鳴」という流れが明確
- 履歴追跡が構造的に可能

**検討タイミング:** Week 3（Intent統合時）

---

### 提案2: Kana API 呼び出し点の標準化

**現状:**
```python
# 各所で個別に実装
processor.call_kana(intent_data)
```

**提案:**
```python
# 共通ハンドラ化
async def bridge_trigger(intent_id: str, trigger_type: str):
    """すべてのIntent処理で利用可能な標準ハンドラ"""
    # ログ記録
    # エラーハンドリング
    # リトライ制御
    # メトリクス収集
    return await processor.call_kana(intent_data)
```

**メリット:**
- エラーハンドリングの一元化
- メトリクス収集の標準化
- 再利用性の向上

**検討タイミング:** Week 3（Intent統合時）

---

### 提案3: Re-evaluation Phase ログ統合

**現状:**
```python
# ログが散在
logs/intent_processor.log
logs/kana_responses.log
```

**提案:**
```bash
# 構造化されたログディレクトリ
/logs/reval/
  └── 2025/
      └── 11/
          └── 08/
              ├── intent_001.json  # Intent単位のログ
              ├── intent_002.json
              └── bridge_metrics.json  # 集計メトリクス
```

**フォーマット例:**
```json
{
  "intent_id": "uuid",
  "timestamp": "2025-11-08T19:00:00Z",
  "phase": "processing",
  "kana_response": "...",
  "duration_ms": 5234,
  "resonance_score": 0.87
}
```

**メリット:**
- 思想的透明性を保持
- 機械解析が容易
- 履歴追跡が構造的

**検討タイミング:** Week 3-4（ログ設計時）

---

### 提案4: フェーズ定義再構成 ⭐⭐

**現状:**
```
Week 1-2: コア機能実装
Week 3: Intent処理・デーモン統合
Week 4: Oracle Cloud デプロイ
```

**提案:**
```
Phase A：PostgreSQL 呼吸体形成
  → データベース構造とLISTEN/NOTIFY確立
  
Phase B：Intent Bridge 循環確立
  → Intent自動処理とKana統合
  
Phase C：Kana 共鳴層統合
  → 本番環境デプロイと監視
```

**メリット:**
- より本質的な命名
- Resonant哲学との整合性
- 各フェーズの目的が明確

**判断:** この命名を採用するか、現状のWeek表記を維持するか検討

---

### 提案5: Dashboard Breath Monitor (UI)

**提案:**
意図監視をCLI ではなくWebSocket UI 化。呼吸状態を視覚化する「Dashboard Breath Monitor」。

**実装イメージ:**
```tsx
// リアルタイムIntent監視UI
<BreathMonitor>
  <IntentFlow />        // Intent の流れを可視化
  <RespirationRate />   // 処理速度（呼吸数）
  <ResonanceScore />    // 共鳴度スコア
  <ActiveIntents />     // 現在処理中のIntent
</BreathMonitor>
```

**メリット:**
- システムの「呼吸」が視覚的に理解できる
- デバッグが容易
- 哲学的概念の具現化

**検討タイミング:** Week 2（フロントエンド実装時）

---

## 📋 実装時の判断フロー

```
Yuno（哲学的指針）
  ↓
Kana（技術的提案・選択肢提示）
  ↓
宏啓（判断・実行）
```

### 判断基準

1. **今必要か？** → 今実装 / 後回し
2. **複雑さは？** → シンプル維持 / 必要な複雑さ
3. **価値は？** → コア価値 / 付加価値
4. **Yuno哲学との整合** → 合致 / 再検討

### 現時点での推奨

- ✅ **今すぐ採用:** LISTEN/NOTIFY（既に反映済み）
- 🔶 **Week 3で検討:** 提案1（Intent 3段階）、提案2（標準ハンドラ）
- 🔶 **Week 3-4で検討:** 提案3（ログ構造化）
- 🔶 **随時検討:** 提案4（フェーズ命名）
- 🔶 **Week 2で検討:** 提案5（Breath Monitor UI）

---

## 🎯 次のアクション

**Day 1（環境構築）を開始する準備完了！**

Yunoの提案を念頭に置きながら、まずは基盤を構築していきましょう。
