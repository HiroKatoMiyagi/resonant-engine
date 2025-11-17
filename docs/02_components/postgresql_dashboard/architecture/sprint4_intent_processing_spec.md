# Sprint 4: Intent自動処理・デーモン統合仕様書

## 0. 概要

**目的**: Intent発火を自動検知し、Kana（Claude API）で処理する自動化システム
**期間**: 5日間
**前提**: Sprint 1-3 完了

---

## 1. Done Definition

### Tier 1: 必須
- [ ] intent_bridge.py（LISTEN/NOTIFY版）実装
- [ ] PostgreSQL LISTEN/NOTIFY設定
- [ ] Intent自動処理デーモン
- [ ] Claude API統合
- [ ] 処理結果のDB保存
- [ ] 通知自動生成
- [ ] 既存observer_daemon.pyとの連携
- [ ] エラーハンドリングとリトライ

### Tier 2: 品質
- [ ] 処理レイテンシ < 5秒（検知から通知まで）
- [ ] 24時間連続稼働テスト
- [ ] ログローテーション設定
- [ ] Prometheus メトリクス
- [ ] GitHub Issue自動作成（オプション）

---

## 2. システムアーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│               Intent Processing Flow                 │
│                                                      │
│  User → Dashboard → POST /api/intents               │
│                           ↓                         │
│  ┌─────────────────────────────────────┐           │
│  │      PostgreSQL                      │           │
│  │  ┌──────────────────────────────┐   │           │
│  │  │ INSERT INTO intents          │   │           │
│  │  │ NOTIFY intent_created, id    │   │           │
│  │  └──────────────────────────────┘   │           │
│  └──────────────┬──────────────────────┘           │
│                 │ NOTIFY                            │
│                 ▼                                   │
│  ┌─────────────────────────────────────┐           │
│  │     intent_bridge.py                │           │
│  │  - LISTEN intent_created            │           │
│  │  - 即座にIntent取得                 │           │
│  │  - Claude API呼び出し               │           │
│  │  - 結果をDB保存                     │           │
│  │  - 通知生成                         │           │
│  └──────────────┬──────────────────────┘           │
│                 ↓                                   │
│  Dashboard: 処理完了通知表示                        │
└─────────────────────────────────────────────────────┘
```

---

## 3. PostgreSQL LISTEN/NOTIFY設定

### 3.1 トリガー関数

```sql
-- Intent作成時に通知を発火
CREATE OR REPLACE FUNCTION notify_intent_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'intent_created',
        json_build_object(
            'id', NEW.id,
            'description', NEW.description,
            'priority', NEW.priority
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- トリガー設定
CREATE TRIGGER intent_created_trigger
    AFTER INSERT ON intents
    FOR EACH ROW
    EXECUTE FUNCTION notify_intent_created();
```

### 3.2 ステータス変更通知

```sql
CREATE OR REPLACE FUNCTION notify_intent_status_changed()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status != NEW.status THEN
        PERFORM pg_notify(
            'intent_status_changed',
            json_build_object(
                'id', NEW.id,
                'old_status', OLD.status,
                'new_status', NEW.status
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER intent_status_trigger
    AFTER UPDATE ON intents
    FOR EACH ROW
    EXECUTE FUNCTION notify_intent_status_changed();
```

---

## 4. Intent Bridge デーモン

### 4.1 基本構造

```python
# bridge/intent_bridge.py
import asyncio
import asyncpg
import anthropic
from datetime import datetime
import json

class IntentBridge:
    def __init__(self):
        self.pool = None
        self.claude = anthropic.Anthropic()
        self.running = False

    async def start(self):
        self.pool = await asyncpg.create_pool(
            host="localhost",
            database="resonant_dashboard",
            user="resonant",
            password="..."
        )
        self.running = True
        await self.listen_for_intents()

    async def listen_for_intents(self):
        async with self.pool.acquire() as conn:
            await conn.add_listener('intent_created', self.handle_notification)
            print("🎧 Listening for intent_created events...")

            while self.running:
                await asyncio.sleep(1)

    async def handle_notification(self, conn, pid, channel, payload):
        data = json.loads(payload)
        print(f"📨 Received intent: {data['id']}")
        await self.process_intent(data['id'])

    async def process_intent(self, intent_id):
        async with self.pool.acquire() as conn:
            # 1. Intent取得
            intent = await conn.fetchrow(
                "SELECT * FROM intents WHERE id = $1",
                intent_id
            )

            # 2. ステータス更新: processing
            await conn.execute(
                "UPDATE intents SET status = 'processing', updated_at = NOW() WHERE id = $1",
                intent_id
            )

            try:
                # 3. Claude API呼び出し
                response = await self.call_claude(intent['description'])

                # 4. 結果保存
                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(response), intent_id)

                # 5. 通知生成
                await self.create_notification(conn, intent_id, "success")

                print(f"✅ Intent {intent_id} processed successfully")

            except Exception as e:
                # エラー処理
                await conn.execute("""
                    UPDATE intents
                    SET status = 'failed',
                        result = $1,
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps({"error": str(e)}), intent_id)

                await self.create_notification(conn, intent_id, "error")
                print(f"❌ Intent {intent_id} failed: {e}")

    async def call_claude(self, description):
        message = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"以下のIntentを処理してください:\n\n{description}"
                }
            ]
        )
        return {
            "response": message.content[0].text,
            "model": message.model,
            "tokens": message.usage.output_tokens
        }

    async def create_notification(self, conn, intent_id, status):
        title = "Intent処理完了" if status == "success" else "Intent処理失敗"
        notification_type = "success" if status == "success" else "error"

        await conn.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES ('hiroki', $1, $2, $3)
        """, title, f"Intent ID: {intent_id}", notification_type)

if __name__ == "__main__":
    bridge = IntentBridge()
    asyncio.run(bridge.start())
```

---

## 5. 既存デーモンとの統合

### 5.1 observer_daemon.pyとの連携

```python
# observer_daemon.py に追加
class ObserverDaemon:
    def __init__(self):
        self.intent_bridge = IntentBridge()

    async def start(self):
        # Git監視タスク
        git_task = asyncio.create_task(self.watch_git_changes())

        # Intent Bridge タスク
        intent_task = asyncio.create_task(self.intent_bridge.start())

        await asyncio.gather(git_task, intent_task)
```

### 5.2 統合設定ファイル

```yaml
# config/daemon_config.yaml
observer:
  git_watch_interval: 60

intent_bridge:
  listen_channel: "intent_created"
  retry_count: 3
  retry_delay: 5

claude:
  model: "claude-sonnet-4-20250514"
  max_tokens: 4096
  temperature: 0.7

notifications:
  enabled: true
  auto_cleanup_days: 7
```

---

## 6. Docker統合

```yaml
# docker-compose.yml に追加
intent_bridge:
  build:
    context: ../bridge
    dockerfile: Dockerfile
  container_name: resonant_intent_bridge
  environment:
    POSTGRES_HOST: postgres
    ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  depends_on:
    postgres:
      condition: service_healthy
  networks:
    - resonant_network
  restart: unless-stopped
```

---

## 7. モニタリング

### 7.1 メトリクス

- `intent_processing_total`: 処理したIntent総数
- `intent_processing_duration_seconds`: 処理時間
- `intent_processing_errors_total`: エラー数
- `intent_queue_size`: 待機中Intent数

### 7.2 ログフォーマット

```
2025-11-17 10:30:45 [INFO] Intent received: abc123
2025-11-17 10:30:46 [INFO] Claude API called
2025-11-17 10:30:48 [INFO] Intent processed: abc123 (2.3s)
2025-11-17 10:30:48 [INFO] Notification created
```

---

## 8. 成功基準

- [ ] ポーリングなしで即座にIntent検知（LISTEN/NOTIFY）
- [ ] 自動処理から結果保存まで完全自動化
- [ ] 24時間連続稼働安定性
- [ ] エラー時の適切なリカバリー
- [ ] 処理レイテンシ < 5秒

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
