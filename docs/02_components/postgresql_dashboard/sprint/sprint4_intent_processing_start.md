# Sprint 4: Intent自動処理・デーモン統合 作業開始指示書

**対象**: Tsumu (Cursor) または実装担当者
**期間**: 5日間想定
**前提**: Sprint 1-3 完了、Claude APIキー取得済み

---

## 1. Done Definition

### Tier 1: 必須
- [ ] LISTEN/NOTIFYトリガー設定
- [ ] intent_bridge.pyデーモン実装
- [ ] Claude API統合
- [ ] 結果DB保存
- [ ] 通知自動生成
- [ ] Dockerコンテナ化
- [ ] ログ出力

### Tier 2: 品質
- [ ] 処理レイテンシ < 5秒
- [ ] エラーリトライ機能
- [ ] メトリクス収集
- [ ] 24時間稼働テスト

---

## 2. 実装スケジュール（5日間）

### Day 1: PostgreSQL LISTEN/NOTIFY設定

**タスク1**: トリガー関数作成
```sql
-- docker/postgres/migrations/002_intent_notify.sql

CREATE OR REPLACE FUNCTION notify_intent_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'intent_created',
        json_build_object(
            'id', NEW.id::text,
            'description', substring(NEW.description, 1, 100),
            'priority', NEW.priority
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER intent_created_trigger
    AFTER INSERT ON intents
    FOR EACH ROW
    EXECUTE FUNCTION notify_intent_created();
```

**タスク2**: マイグレーション実行
```bash
cd docker
docker-compose exec postgres psql -U resonant -d resonant_dashboard \
  -f /migrations/002_intent_notify.sql
```

**タスク3**: NOTIFY動作テスト
```bash
# ターミナル1: LISTENモード
docker-compose exec postgres psql -U resonant -d resonant_dashboard
resonant_dashboard=# LISTEN intent_created;
LISTEN

# ターミナル2: INSERT実行
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "INSERT INTO intents (description) VALUES ('Test Intent');"

# ターミナル1で確認
# Asynchronous notification "intent_created" with payload "{"id":"..."}" received from server process with PID XXX.
```

**完了基準**:
- [ ] トリガー作成成功
- [ ] NOTIFY受信確認
- [ ] ペイロードJSON形式確認

---

### Day 2: Intent Bridgeデーモン基本実装

**タスク1**: プロジェクト構造
```bash
mkdir -p bridge/intent_bridge
touch bridge/intent_bridge/__init__.py
touch bridge/intent_bridge/daemon.py
touch bridge/intent_bridge/processor.py
touch bridge/intent_bridge/notifier.py
touch bridge/requirements.txt
touch bridge/Dockerfile
```

**タスク2**: requirements.txt
```text
asyncpg==0.29.0
anthropic==0.39.0
pyyaml==6.0.1
python-dotenv==1.0.0
prometheus-client==0.19.0
```

**タスク3**: daemon.py実装
```python
import asyncio
import asyncpg
import json
from datetime import datetime

class IntentBridgeDaemon:
    def __init__(self, config):
        self.config = config
        self.pool = None
        self.running = False

    async def start(self):
        print("🚀 Starting Intent Bridge Daemon...")
        self.pool = await asyncpg.create_pool(
            host=self.config['postgres_host'],
            port=self.config['postgres_port'],
            user=self.config['postgres_user'],
            password=self.config['postgres_password'],
            database=self.config['postgres_db'],
            min_size=2,
            max_size=10
        )
        print("✅ Database connection pool established")

        self.running = True
        await self.listen_loop()

    async def listen_loop(self):
        async with self.pool.acquire() as conn:
            def callback(conn, pid, channel, payload):
                asyncio.create_task(self.handle_notification(payload))

            await conn.add_listener('intent_created', callback)
            print("🎧 Listening for intent_created notifications...")

            while self.running:
                await asyncio.sleep(1)

    async def handle_notification(self, payload):
        try:
            data = json.loads(payload)
            intent_id = data['id']
            print(f"📨 Received intent: {intent_id}")

            from .processor import IntentProcessor
            processor = IntentProcessor(self.pool, self.config)
            await processor.process(intent_id)

        except Exception as e:
            print(f"❌ Error handling notification: {e}")

    async def stop(self):
        self.running = False
        if self.pool:
            await self.pool.close()
        print("Intent Bridge stopped")
```

**タスク4**: processor.py実装
```python
import anthropic
import json
from datetime import datetime

class IntentProcessor:
    def __init__(self, pool, config):
        self.pool = pool
        self.config = config
        self.claude = anthropic.Anthropic(
            api_key=config['anthropic_api_key']
        )

    async def process(self, intent_id):
        async with self.pool.acquire() as conn:
            # 1. Intent取得
            intent = await conn.fetchrow(
                "SELECT * FROM intents WHERE id = $1",
                intent_id
            )

            if not intent:
                print(f"⚠️ Intent {intent_id} not found")
                return

            # 2. ステータス更新: processing
            await conn.execute("""
                UPDATE intents
                SET status = 'processing', updated_at = NOW()
                WHERE id = $1
            """, intent_id)

            try:
                # 3. Claude API呼び出し
                print(f"🤖 Calling Claude API...")
                response = self.call_claude(intent['description'])

                # 4. 結果保存
                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1::jsonb,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(response), intent_id)

                # 5. 通知作成
                await self.create_notification(conn, intent_id, 'success')

                print(f"✅ Intent {intent_id} processed successfully")

            except Exception as e:
                await conn.execute("""
                    UPDATE intents
                    SET status = 'failed',
                        result = $1::jsonb,
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps({"error": str(e)}), intent_id)

                await self.create_notification(conn, intent_id, 'error')
                print(f"❌ Intent {intent_id} failed: {e}")

    def call_claude(self, description):
        message = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"""あなたはResonant EngineのKana（外界翻訳層）です。
以下のIntentを処理し、適切な応答を生成してください。

Intent: {description}

応答形式:
- 明確で構造化された回答
- 具体的なアクションアイテム（あれば）
- 次のステップの提案"""
            }]
        )

        return {
            "response": message.content[0].text,
            "model": message.model,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens
            },
            "processed_at": datetime.utcnow().isoformat()
        }

    async def create_notification(self, conn, intent_id, status):
        if status == 'success':
            title = "Intent処理完了"
            msg = f"Intent {str(intent_id)[:8]}... が正常に処理されました"
            notification_type = "success"
        else:
            title = "Intent処理失敗"
            msg = f"Intent {str(intent_id)[:8]}... の処理に失敗しました"
            notification_type = "error"

        await conn.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES ('hiroki', $1, $2, $3)
        """, title, msg, notification_type)
```

**完了基準**:
- [ ] デーモンが起動
- [ ] LISTEN/NOTIFY受信
- [ ] 基本処理ロジック完成

---

### Day 3: Claude API統合と通知

**タスク1**: メインエントリーポイント
```python
# bridge/main.py
import asyncio
import os
from dotenv import load_dotenv
from intent_bridge.daemon import IntentBridgeDaemon

load_dotenv()

config = {
    'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
    'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
    'postgres_user': os.getenv('POSTGRES_USER', 'resonant'),
    'postgres_password': os.getenv('POSTGRES_PASSWORD'),
    'postgres_db': os.getenv('POSTGRES_DB', 'resonant_dashboard'),
    'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
}

async def main():
    daemon = IntentBridgeDaemon(config)
    try:
        await daemon.start()
    except KeyboardInterrupt:
        await daemon.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

**タスク2**: エンドツーエンドテスト
```bash
# 1. デーモン起動
cd bridge
python main.py

# 2. Intent作成（別ターミナル）
curl -X POST http://localhost:8000/api/intents \
  -H "Content-Type: application/json" \
  -d '{"description": "API設計をレビューしてください", "priority": 8}'

# 3. 処理確認
# デーモンログで処理完了を確認
# PostgreSQLでステータス確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT id, status, result->>'response' FROM intents ORDER BY created_at DESC LIMIT 1;"
```

**タスク3**: 通知確認
```bash
# ダッシュボードで通知確認
open http://localhost:3000
# 🔔ベルアイコンに新規通知が表示される
```

**完了基準**:
- [ ] Claude API呼び出し成功
- [ ] 結果がDB保存される
- [ ] 通知が自動生成される

---

### Day 4: Dockerコンテナ化

**タスク1**: Dockerfile作成
```dockerfile
# bridge/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

**タスク2**: docker-compose.yml更新
```yaml
# docker/docker-compose.yml に追加
intent_bridge:
  build:
    context: ../bridge
    dockerfile: Dockerfile
  container_name: resonant_intent_bridge
  restart: unless-stopped
  environment:
    POSTGRES_HOST: postgres
    POSTGRES_PORT: 5432
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: ${POSTGRES_DB}
    ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  depends_on:
    postgres:
      condition: service_healthy
    backend:
      condition: service_started
  networks:
    - resonant_network
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "5"
```

**タスク3**: .env更新
```bash
# docker/.env に追加
ANTHROPIC_API_KEY=your_api_key_here
```

**タスク4**: 統合テスト
```bash
cd docker
docker-compose up --build -d
docker-compose logs -f intent_bridge

# Intent作成テスト
curl -X POST http://localhost:8000/api/intents \
  -d '{"description": "テスト自動処理"}' -H "Content-Type: application/json"

# ログで処理確認
```

**完了基準**:
- [ ] Dockerビルド成功
- [ ] 全サービス連携動作
- [ ] エンドツーエンド自動処理

---

### Day 5: 安定性テストとログ

**タスク1**: エラーハンドリング強化
```python
# processor.py に追加
async def process_with_retry(self, intent_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            await self.process(intent_id)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries} for intent {intent_id}")
                await asyncio.sleep(5 * (attempt + 1))
            else:
                raise
```

**タスク2**: ヘルスチェックエンドポイント追加
```python
# FastAPIに追加
@app.get("/health/intent-bridge")
async def intent_bridge_health():
    # 最近の処理状況を確認
    recent = await db.fetchrow("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM intents
        WHERE created_at > NOW() - INTERVAL '1 hour'
    """)
    return {
        "status": "healthy",
        "last_hour": {
            "total": recent['total'],
            "completed": recent['completed'],
            "failed": recent['failed']
        }
    }
```

**タスク3**: 24時間稼働テスト
```bash
# 定期的にIntent作成
for i in {1..100}; do
    curl -X POST http://localhost:8000/api/intents \
      -d "{\"description\": \"Test Intent #$i\", \"priority\": $((RANDOM % 10))}" \
      -H "Content-Type: application/json"
    sleep 300  # 5分間隔
done

# 成功率確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT status, COUNT(*) FROM intents GROUP BY status;"
```

**完了基準**:
- [ ] エラーリトライ動作
- [ ] ログが適切に出力
- [ ] 24時間稼働安定性確認
- [ ] 成功率 > 95%

---

## 3. 完了報告書

1. **Done Definition達成**: Tier 1: X/7, Tier 2: X/4
2. **処理統計**: 成功数、失敗数、平均レイテンシ
3. **安定性**: 連続稼働時間、エラー率
4. **次のアクション**: Sprint 5への準備

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
