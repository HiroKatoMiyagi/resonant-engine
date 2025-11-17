# Bridge Lite Sprint 3 Implementation Specification
## UI Sync & Real-time Operations

**Sprint期間**: 2025-12-02 〜 2025-12-15（14日間）  
**優先度**: P2（中優先）  
**前提条件**: Sprint 2（Concurrency Control）完了  
**目的**: リアルタイムUI同期と運用監視機能の実装

---

## CRITICAL: Database Schema Protection

**⚠️ IMPORTANT: 既存データベーススキーマの保護**

この仕様書の実装を開始する前に、以下を必ず確認してください。

### 既存スキーマ

```sql
-- intentsテーブル（既存・稼働中）
CREATE TABLE intents (
    id UUID PRIMARY KEY,
    data JSONB,          -- ← 必ずこのカラムを使用すること
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    ...
);

-- audit_logsテーブル（既存・稼働中）
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),
    intent_id UUID,
    actor VARCHAR(100),
    payload JSONB,
    created_at TIMESTAMP,
    ...
);
```

### 絶対禁止事項

- ❌ `DROP TABLE` の使用
- ❌ `DROP TABLE IF EXISTS` の使用
- ❌ 既存テーブルの削除・変更
- ❌ `data`カラムの名前変更
- ❌ 既存カラムの型変更
- ❌ 既存`schema.sql`への破壊的変更

### 実装ルール

1. **カラム名**: 必ず既存の`data`カラムを使用（`payload`ではない）
2. **新規テーブル**: UI同期・通知用の新規テーブルは追加可能
3. **スキーマ変更**: 新規カラム追加が必要な場合は実装を停止して事前報告

### 許可される操作

- ✅ 既存の`data`カラムを使用
- ✅ 新しいカラムの追加（`ALTER TABLE ADD COLUMN`）
- ✅ 新しいテーブルの作成（既存と競合しない場合）
- ✅ インデックスの追加
- ✅ PostgreSQL LISTEN/NOTIFY機能の活用

---

## 0. Sprint 3 Overview

### 0.1 目的

リアルタイムUI同期と運用監視機能を実装し、以下を実現する：
- Intent状態変更のリアルタイム通知
- WebSocket/SSEベースのUI同期
- 監査ログの効率的なETL処理
- ダッシュボード向けメトリクス収集
- 運用監視とアラート機能

### 0.2 スコープ

**IN Scope**:
- WebSocket/SSE エンドポイント実装
- Intent変更通知システム
- 監査ログETL（PostgreSQL → 時系列DB）
- リアルタイムメトリクス収集
- ダッシュボードAPI実装
- 運用アラート機能
- テストスイート拡充（38 → 50+ ケース）

**OUT of Scope**:
- フロントエンド実装（Priority 2: PostgreSQL環境構築で対応）
- 分散トランザクション（将来拡張）
- マルチテナント対応（Phase 4）
- 高度なアラートルール（カスタムルールエンジンは将来拡張）

### 0.3 Done Definition

- [ ] WebSocket/SSEエンドポイントが実装され、Intent変更をリアルタイム配信
- [ ] PostgreSQL LISTEN/NOTIFYを活用したイベント駆動アーキテクチャ
- [ ] 監査ログETLが実装され、時系列DBへの自動転送が動作
- [ ] ダッシュボード向けメトリクスAPIが実装され、リアルタイムデータを提供
- [ ] 運用アラート機能が実装され、閾値超過時に通知
- [ ] テストカバレッジ 50+ ケース達成
- [ ] WebSocket接続の負荷テスト（100同時接続）通過
- [ ] UI同期の遅延が200ms以内
- [ ] ドキュメント完成（アーキテクチャ、API、運用ガイド）
- [ ] Kana による仕様レビュー通過

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Dashboard  │  │ Intent View  │  │  Metrics Panel   │   │
│  └────────────┘  └──────────────┘  └──────────────────┘   │
└────────┬──────────────────┬──────────────────┬─────────────┘
         │ WebSocket        │ SSE              │ REST API
         │                  │                  │
┌────────▼──────────────────▼──────────────────▼─────────────┐
│                  Bridge Lite API (FastAPI)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  WebSocket   │  │  SSE Event   │  │  Metrics API     │ │
│  │  Manager     │  │  Stream      │  │  Dashboard API   │ │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
│         │                  │                   │            │
│  ┌──────▼──────────────────▼───────────────────▼─────────┐ │
│  │         Real-time Event Distribution Layer            │ │
│  │  (PostgreSQL LISTEN/NOTIFY + In-memory pub/sub)       │ │
│  └──────┬──────────────────────────────────────┬─────────┘ │
└─────────┼──────────────────────────────────────┼───────────┘
          │                                      │
┌─────────▼──────────────────┐      ┌───────────▼────────────┐
│   PostgreSQL Database      │      │   TimescaleDB          │
│  ┌──────────────────────┐  │      │  ┌──────────────────┐ │
│  │  intents (data)      │  │      │  │  audit_logs_ts   │ │
│  │  audit_logs          │  │      │  │  metrics_ts      │ │
│  │  notifications       │  │      │  │  (time-series)   │ │
│  └──────────────────────┘  │      │  └──────────────────┘ │
└────────────────────────────┘      └────────────────────────┘
```

### 1.2 Event Flow (呼吸の可視化)

```
Intent Status Change (呼吸の変化)
    ↓
PostgreSQL TRIGGER → NOTIFY 'intent_changed'
    ↓
Event Distribution Layer (共鳴の拡大)
    ├─→ WebSocket Manager → Connected Clients
    ├─→ SSE Manager → SSE Streams
    ├─→ Metrics Collector → Time-series DB
    └─→ Alert Manager → Check Thresholds → Notify
```

### 1.3 Technology Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| WebSocket | FastAPI WebSocket | Native support, async |
| SSE | FastAPI StreamingResponse | Simple, one-way |
| Event Bus | PostgreSQL LISTEN/NOTIFY | Zero-latency, built-in |
| In-memory Pub/Sub | Python asyncio Queue | Fast distribution |
| Time-series DB | TimescaleDB (PostgreSQL extension) | Compatible, scalable |
| Metrics | Prometheus client | Industry standard |
| Alerting | Custom + Email/Slack webhooks | Flexible |

---

## 2. Real-time Event System

### 2.1 PostgreSQL Event Triggers

```sql
-- Intent変更通知用TRIGGER
CREATE OR REPLACE FUNCTION notify_intent_changed()
RETURNS TRIGGER AS $$
BEGIN
    -- Intent変更時にチャンネルに通知
    PERFORM pg_notify(
        'intent_changed',
        json_build_object(
            'intent_id', NEW.id,
            'status', NEW.status,
            'version', NEW.version,
            'updated_at', NEW.updated_at,
            'event_type', TG_OP  -- 'INSERT', 'UPDATE', 'DELETE'
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER intent_changed_trigger
AFTER INSERT OR UPDATE ON intents
FOR EACH ROW
EXECUTE FUNCTION notify_intent_changed();

-- 監査ログ作成通知用TRIGGER
CREATE OR REPLACE FUNCTION notify_audit_log_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'audit_log_created',
        json_build_object(
            'log_id', NEW.id,
            'event_type', NEW.event_type,
            'intent_id', NEW.intent_id,
            'actor', NEW.actor,
            'created_at', NEW.created_at
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_created_trigger
AFTER INSERT ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION notify_audit_log_created();
```

### 2.2 Event Distribution Layer

```python
# bridge/realtime/event_distributor.py

import asyncio
import asyncpg
from typing import Dict, Set, Callable
from dataclasses import dataclass
from enum import Enum

class EventChannel(str, Enum):
    """Event channel names"""
    INTENT_CHANGED = "intent_changed"
    AUDIT_LOG_CREATED = "audit_log_created"
    METRICS_UPDATED = "metrics_updated"

@dataclass
class Event:
    """Real-time event"""
    channel: EventChannel
    payload: dict
    timestamp: datetime

class EventDistributor:
    """
    Central event distribution hub.
    
    - Listens to PostgreSQL NOTIFY
    - Distributes to WebSocket/SSE subscribers
    - Triggers ETL processes
    - Updates metrics
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.subscribers: Dict[EventChannel, Set[Callable]] = {
            channel: set() for channel in EventChannel
        }
        self._conn: Optional[asyncpg.Connection] = None
        self._running = False
    
    async def start(self):
        """Start event distribution"""
        self._conn = await asyncpg.connect(self.database_url)
        self._running = True
        
        # Add listeners for all channels
        for channel in EventChannel:
            await self._conn.add_listener(
                channel.value,
                self._handle_notification
            )
        
        logger.info("Event distributor started")
    
    async def stop(self):
        """Stop event distribution"""
        self._running = False
        
        if self._conn:
            for channel in EventChannel:
                await self._conn.remove_listener(
                    channel.value,
                    self._handle_notification
                )
            await self._conn.close()
        
        logger.info("Event distributor stopped")
    
    async def _handle_notification(
        self, 
        connection, 
        pid, 
        channel, 
        payload
    ):
        """Handle PostgreSQL notification"""
        try:
            event = Event(
                channel=EventChannel(channel),
                payload=json.loads(payload),
                timestamp=datetime.utcnow()
            )
            
            # Distribute to subscribers
            await self._distribute(event)
            
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    async def _distribute(self, event: Event):
        """Distribute event to all subscribers"""
        subscribers = self.subscribers.get(event.channel, set())
        
        # Create tasks for all subscribers
        tasks = [
            subscriber(event)
            for subscriber in subscribers
        ]
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(
        self, 
        channel: EventChannel, 
        handler: Callable[[Event], None]
    ):
        """Subscribe to event channel"""
        self.subscribers[channel].add(handler)
    
    def unsubscribe(
        self, 
        channel: EventChannel, 
        handler: Callable[[Event], None]
    ):
        """Unsubscribe from event channel"""
        self.subscribers[channel].discard(handler)

# Global singleton
event_distributor: Optional[EventDistributor] = None

async def get_event_distributor() -> EventDistributor:
    """Get or create event distributor singleton"""
    global event_distributor
    
    if event_distributor is None:
        database_url = os.environ.get("DATABASE_URL")
        event_distributor = EventDistributor(database_url)
        await event_distributor.start()
    
    return event_distributor
```

---

## 3. WebSocket Implementation

### 3.1 WebSocket Manager

```python
# bridge/realtime/websocket_manager.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio

class WebSocketManager:
    """
    Manage WebSocket connections and broadcast events.
    
    - Maintains active connections
    - Subscribes to event distributor
    - Broadcasts events to connected clients
    """
    
    def __init__(self):
        # intent_id -> Set[WebSocket]
        self.connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> subscribed intent_ids
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        intent_ids: list[str] = None
    ):
        """
        Accept WebSocket connection and subscribe to intents.
        
        Args:
            websocket: WebSocket connection
            intent_ids: List of intent IDs to subscribe (None = all)
        """
        await websocket.accept()
        
        if intent_ids:
            # Subscribe to specific intents
            self.subscriptions[websocket] = set(intent_ids)
            
            for intent_id in intent_ids:
                if intent_id not in self.connections:
                    self.connections[intent_id] = set()
                self.connections[intent_id].add(websocket)
        else:
            # Subscribe to all intents
            self.subscriptions[websocket] = {'*'}
        
        logger.info(
            f"WebSocket connected: {id(websocket)}, "
            f"subscribed to {intent_ids or 'all'}"
        )
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect WebSocket and clean up subscriptions"""
        intent_ids = self.subscriptions.get(websocket, set())
        
        for intent_id in intent_ids:
            if intent_id in self.connections:
                self.connections[intent_id].discard(websocket)
                
                # Clean up empty sets
                if not self.connections[intent_id]:
                    del self.connections[intent_id]
        
        self.subscriptions.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected: {id(websocket)}")
    
    async def broadcast_intent_event(self, event: Event):
        """
        Broadcast intent event to subscribed WebSockets.
        
        This is called by EventDistributor when intent changes.
        """
        intent_id = event.payload.get('intent_id')
        
        if not intent_id:
            return
        
        # Get connections subscribed to this intent
        connections = self.connections.get(intent_id, set()).copy()
        
        # Also send to wildcard subscribers
        wildcard_subs = [
            ws for ws, subs in self.subscriptions.items()
            if '*' in subs
        ]
        connections.update(wildcard_subs)
        
        # Broadcast to all relevant connections
        disconnected = []
        
        for websocket in connections:
            try:
                await websocket.send_json({
                    'type': 'intent_update',
                    'data': event.payload,
                    'timestamp': event.timestamp.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected
        for websocket in disconnected:
            self.disconnect(websocket)

# Global singleton
websocket_manager = WebSocketManager()
```

### 3.2 WebSocket Endpoint

```python
# bridge/api/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from bridge.realtime.websocket_manager import websocket_manager
from bridge.realtime.event_distributor import get_event_distributor, EventChannel

router = APIRouter()

@router.websocket("/ws/intents")
async def websocket_intents(
    websocket: WebSocket,
    intent_ids: list[str] = Query(None)
):
    """
    WebSocket endpoint for real-time intent updates.
    
    Query Parameters:
        intent_ids: List of intent IDs to subscribe.
                   If omitted, subscribes to all intents.
    
    Event Format:
        {
            "type": "intent_update",
            "data": {
                "intent_id": "uuid",
                "status": "processed",
                "version": 5,
                "updated_at": "2025-12-03T10:00:00Z",
                "event_type": "UPDATE"
            },
            "timestamp": "2025-12-03T10:00:00.123Z"
        }
    
    Usage:
        const ws = new WebSocket('ws://localhost:8000/ws/intents?intent_ids=uuid1&intent_ids=uuid2');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Intent updated:', data);
        };
    """
    # Connect
    await websocket_manager.connect(websocket, intent_ids)
    
    try:
        # Keep connection alive and handle client messages
        while True:
            # Wait for client message (ping/pong, subscribe changes, etc.)
            message = await websocket.receive_text()
            
            # Handle message
            data = json.loads(message)
            
            if data.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
            
            elif data.get('type') == 'subscribe':
                # Add new subscriptions
                new_intent_ids = data.get('intent_ids', [])
                # Update subscriptions logic here
            
            elif data.get('type') == 'unsubscribe':
                # Remove subscriptions
                remove_intent_ids = data.get('intent_ids', [])
                # Update subscriptions logic here
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@router.on_event("startup")
async def startup_websocket():
    """Subscribe WebSocketManager to event distributor"""
    distributor = await get_event_distributor()
    
    distributor.subscribe(
        EventChannel.INTENT_CHANGED,
        websocket_manager.broadcast_intent_event
    )
```

---

## 4. Server-Sent Events (SSE) Implementation

### 4.1 SSE Event Stream

```python
# bridge/api/sse.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from bridge.realtime.event_distributor import get_event_distributor, EventChannel
import asyncio

router = APIRouter()

@router.get("/events/intents/{intent_id}")
async def intent_event_stream(intent_id: str):
    """
    Server-Sent Events stream for a specific intent.
    
    Returns real-time updates whenever the intent changes.
    
    Usage:
        const eventSource = new EventSource('/events/intents/uuid');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Intent updated:', data);
        };
    """
    async def event_generator():
        """Generate SSE events"""
        # Create queue for this stream
        queue = asyncio.Queue()
        
        # Define event handler
        async def handle_event(event: Event):
            if event.payload.get('intent_id') == intent_id:
                await queue.put(event)
        
        # Subscribe to events
        distributor = await get_event_distributor()
        distributor.subscribe(EventChannel.INTENT_CHANGED, handle_event)
        
        try:
            while True:
                # Wait for event
                event = await queue.get()
                
                # Format as SSE
                yield f"data: {json.dumps(event.payload)}\n\n"
        
        finally:
            # Cleanup on disconnect
            distributor.unsubscribe(EventChannel.INTENT_CHANGED, handle_event)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@router.get("/events/audit-logs")
async def audit_log_event_stream():
    """
    Server-Sent Events stream for all audit logs.
    
    Returns real-time audit log entries as they are created.
    """
    async def event_generator():
        queue = asyncio.Queue()
        
        async def handle_event(event: Event):
            await queue.put(event)
        
        distributor = await get_event_distributor()
        distributor.subscribe(EventChannel.AUDIT_LOG_CREATED, handle_event)
        
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event.payload)}\n\n"
        finally:
            distributor.unsubscribe(EventChannel.AUDIT_LOG_CREATED, handle_event)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

## 5. Audit Log ETL

### 5.1 TimescaleDB Schema

```sql
-- TimescaleDB extension (PostgreSQL時系列拡張)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 監査ログ時系列テーブル
CREATE TABLE audit_logs_ts (
    time TIMESTAMPTZ NOT NULL,
    log_id INTEGER,
    event_type VARCHAR(100),
    intent_id UUID,
    actor VARCHAR(100),
    bridge_type VARCHAR(100),
    status_from VARCHAR(50),
    status_to VARCHAR(50),
    payload JSONB,
    duration_ms INTEGER,
    success BOOLEAN
);

-- Hypertableに変換（時系列最適化）
SELECT create_hypertable('audit_logs_ts', 'time');

-- インデックス
CREATE INDEX idx_audit_logs_ts_intent_id ON audit_logs_ts (intent_id, time DESC);
CREATE INDEX idx_audit_logs_ts_event_type ON audit_logs_ts (event_type, time DESC);
CREATE INDEX idx_audit_logs_ts_actor ON audit_logs_ts (actor, time DESC);

-- 自動集計ビュー（継続的集計）
CREATE MATERIALIZED VIEW audit_logs_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    event_type,
    actor,
    COUNT(*) AS event_count,
    AVG(duration_ms) AS avg_duration_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failure_count
FROM audit_logs_ts
GROUP BY bucket, event_type, actor;

-- リフレッシュポリシー（1時間ごとに自動更新）
SELECT add_continuous_aggregate_policy(
    'audit_logs_hourly',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- データ保持ポリシー（90日で自動削除）
SELECT add_retention_policy('audit_logs_ts', INTERVAL '90 days');
```

### 5.2 ETL Process

```python
# bridge/etl/audit_log_etl.py

import asyncpg
from typing import Optional
from dataclasses import dataclass

@dataclass
class AuditLogETLConfig:
    """ETL configuration"""
    source_db_url: str  # PostgreSQL (audit_logs)
    target_db_url: str  # TimescaleDB (audit_logs_ts)
    batch_size: int = 100
    interval_seconds: float = 5.0

class AuditLogETL:
    """
    ETL process for audit logs.
    
    - Reads from audit_logs table
    - Transforms to time-series format
    - Loads into TimescaleDB
    """
    
    def __init__(self, config: AuditLogETLConfig):
        self.config = config
        self.last_processed_id: Optional[int] = None
    
    async def start(self):
        """Start ETL process"""
        logger.info("Starting Audit Log ETL")
        
        # Connect to source and target
        source_conn = await asyncpg.connect(self.config.source_db_url)
        target_conn = await asyncpg.connect(self.config.target_db_url)
        
        try:
            while True:
                # Extract new audit logs
                logs = await self._extract(source_conn)
                
                if logs:
                    # Transform and load
                    await self._transform_and_load(logs, target_conn)
                    
                    logger.info(f"ETL processed {len(logs)} audit logs")
                
                # Wait before next batch
                await asyncio.sleep(self.config.interval_seconds)
        
        finally:
            await source_conn.close()
            await target_conn.close()
    
    async def _extract(self, conn: asyncpg.Connection) -> list[dict]:
        """Extract new audit logs from source DB"""
        query = """
            SELECT 
                id, event_type, intent_id, actor, payload, created_at
            FROM audit_logs
            WHERE id > $1
            ORDER BY id
            LIMIT $2
        """
        
        last_id = self.last_processed_id or 0
        
        rows = await conn.fetch(query, last_id, self.config.batch_size)
        
        if rows:
            self.last_processed_id = rows[-1]['id']
        
        return [dict(row) for row in rows]
    
    async def _transform_and_load(
        self, 
        logs: list[dict], 
        conn: asyncpg.Connection
    ):
        """Transform and load into TimescaleDB"""
        insert_query = """
            INSERT INTO audit_logs_ts (
                time, log_id, event_type, intent_id, actor,
                bridge_type, status_from, status_to, payload,
                duration_ms, success
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        for log in logs:
            payload = log.get('payload', {})
            
            # Extract fields from payload
            bridge_type = payload.get('bridge_type')
            status_from = payload.get('old_status')
            status_to = payload.get('new_status')
            duration_ms = payload.get('duration_ms')
            success = payload.get('success', True)
            
            await conn.execute(
                insert_query,
                log['created_at'],
                log['id'],
                log['event_type'],
                log['intent_id'],
                log['actor'],
                bridge_type,
                status_from,
                status_to,
                log['payload'],
                duration_ms,
                success
            )

# Event-driven ETL (alternative to polling)
class EventDrivenAuditLogETL:
    """
    Event-driven ETL using PostgreSQL LISTEN/NOTIFY.
    
    Zero-latency ETL triggered by audit log creation.
    """
    
    def __init__(self, config: AuditLogETLConfig):
        self.config = config
    
    async def start(self):
        """Start event-driven ETL"""
        distributor = await get_event_distributor()
        
        # Subscribe to audit log creation events
        distributor.subscribe(
            EventChannel.AUDIT_LOG_CREATED,
            self._handle_audit_log_event
        )
        
        logger.info("Event-driven Audit Log ETL started")
    
    async def _handle_audit_log_event(self, event: Event):
        """Handle audit log creation event"""
        log_id = event.payload.get('log_id')
        
        # Fetch full audit log
        async with asyncpg.create_pool(self.config.source_db_url) as pool:
            async with pool.acquire() as conn:
                log = await conn.fetchrow(
                    "SELECT * FROM audit_logs WHERE id = $1",
                    log_id
                )
        
        if log:
            # Transform and load immediately
            async with asyncpg.create_pool(self.config.target_db_url) as pool:
                async with pool.acquire() as conn:
                    await self._transform_and_load([dict(log)], conn)
```

---

## 6. Dashboard API & Metrics

### 6.1 Metrics Collection

```python
# bridge/metrics/collector.py

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from dataclasses import dataclass
from typing import Dict

@dataclass
class IntentMetrics:
    """Intent processing metrics"""
    total_intents = Counter(
        'bridge_intents_total',
        'Total number of intents',
        ['status']
    )
    
    processing_duration = Histogram(
        'bridge_processing_duration_seconds',
        'Intent processing duration',
        ['bridge_type']
    )
    
    active_intents = Gauge(
        'bridge_active_intents',
        'Number of active intents',
        ['status']
    )
    
    correction_count = Counter(
        'bridge_corrections_total',
        'Total number of corrections applied',
        ['source']
    )
    
    websocket_connections = Gauge(
        'bridge_websocket_connections',
        'Number of active WebSocket connections'
    )

class MetricsCollector:
    """
    Collect and expose metrics for monitoring.
    
    - Real-time metrics from PostgreSQL
    - Prometheus-compatible format
    - Dashboard API support
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.metrics = IntentMetrics()
    
    async def update_metrics(self):
        """Update metrics from database"""
        async with asyncpg.create_pool(self.database_url) as pool:
            async with pool.acquire() as conn:
                # Count intents by status
                status_counts = await conn.fetch("""
                    SELECT status, COUNT(*) as count
                    FROM intents
                    GROUP BY status
                """)
                
                for row in status_counts:
                    self.metrics.active_intents.labels(
                        status=row['status']
                    ).set(row['count'])
                
                # Count corrections
                correction_counts = await conn.fetch("""
                    SELECT 
                        COUNT(*) as count,
                        jsonb_array_length(correction_history) as total_corrections
                    FROM intents
                    WHERE jsonb_array_length(correction_history) > 0
                """)
                
                # Additional metrics...
    
    async def start_periodic_update(self, interval_seconds: float = 30):
        """Start periodic metrics update"""
        while True:
            await self.update_metrics()
            await asyncio.sleep(interval_seconds)
```

### 6.2 Dashboard API

```python
# bridge/api/dashboard.py

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

@router.get("/api/v1/dashboard/overview")
async def get_dashboard_overview():
    """
    Get dashboard overview metrics.
    
    Returns:
        {
            "total_intents": 1234,
            "status_distribution": {
                "received": 10,
                "normalized": 5,
                "processed": 800,
                "corrected": 100,
                "completed": 319,
                "failed": 0
            },
            "recent_activity": {
                "last_hour": 45,
                "last_24h": 523,
                "last_7d": 1234
            },
            "correction_rate": 0.08,  # 8%
            "avg_processing_time_ms": 1523,
            "active_websockets": 12
        }
    """
    async with get_db_pool() as pool:
        async with pool.acquire() as conn:
            # Total intents
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM intents"
            )
            
            # Status distribution
            status_dist = await conn.fetch("""
                SELECT status, COUNT(*) as count
                FROM intents
                GROUP BY status
            """)
            
            # Recent activity
            now = datetime.utcnow()
            recent_activity = {}
            
            for period, hours in [('last_hour', 1), ('last_24h', 24), ('last_7d', 168)]:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM intents
                    WHERE created_at > $1
                """, now - timedelta(hours=hours))
                recent_activity[period] = count
            
            # Correction rate
            total_with_corrections = await conn.fetchval("""
                SELECT COUNT(*) FROM intents
                WHERE jsonb_array_length(correction_history) > 0
            """)
            correction_rate = total_with_corrections / total if total > 0 else 0
            
            # Average processing time (from audit logs)
            avg_time = await conn.fetchval("""
                SELECT AVG(
                    EXTRACT(EPOCH FROM (
                        SELECT MIN(created_at) FROM audit_logs al2
                        WHERE al2.intent_id = al1.intent_id
                          AND al2.event_type = 'BRIDGE_COMPLETED'
                    )) - EXTRACT(EPOCH FROM created_at)
                ) * 1000 as avg_ms
                FROM audit_logs al1
                WHERE event_type = 'BRIDGE_STARTED'
                  AND created_at > $1
            """, now - timedelta(days=1))
            
            return {
                "total_intents": total,
                "status_distribution": {
                    row['status']: row['count']
                    for row in status_dist
                },
                "recent_activity": recent_activity,
                "correction_rate": round(correction_rate, 3),
                "avg_processing_time_ms": int(avg_time or 0),
                "active_websockets": len(websocket_manager.subscriptions)
            }

@router.get("/api/v1/dashboard/timeline")
async def get_timeline(
    start: datetime = Query(...),
    end: datetime = Query(...),
    granularity: str = Query('hour', regex='^(minute|hour|day)$')
):
    """
    Get intent creation timeline.
    
    Query Parameters:
        start: Start datetime (ISO format)
        end: End datetime (ISO format)
        granularity: Time bucket size (minute/hour/day)
    
    Returns:
        [
            {"time": "2025-12-03T10:00:00Z", "count": 45},
            {"time": "2025-12-03T11:00:00Z", "count": 52},
            ...
        ]
    """
    bucket_size = {
        'minute': '1 minute',
        'hour': '1 hour',
        'day': '1 day'
    }[granularity]
    
    async with get_db_pool() as pool:
        async with pool.acquire() as conn:
            timeline = await conn.fetch(f"""
                SELECT 
                    time_bucket($1, created_at) AS time,
                    COUNT(*) as count
                FROM intents
                WHERE created_at BETWEEN $2 AND $3
                GROUP BY time
                ORDER BY time
            """, bucket_size, start, end)
            
            return [
                {
                    "time": row['time'].isoformat(),
                    "count": row['count']
                }
                for row in timeline
            ]

@router.get("/api/v1/dashboard/corrections")
async def get_corrections_summary(
    limit: int = Query(10, le=100)
):
    """
    Get recent corrections summary.
    
    Returns:
        [
            {
                "intent_id": "uuid",
                "correction_count": 2,
                "last_correction": {
                    "applied_at": "2025-12-03T10:00:00Z",
                    "source": "YUNO",
                    "reason": "..."
                }
            },
            ...
        ]
    """
    async with get_db_pool() as pool:
        async with pool.acquire() as conn:
            corrections = await conn.fetch("""
                SELECT 
                    id as intent_id,
                    jsonb_array_length(correction_history) as correction_count,
                    correction_history->-1 as last_correction
                FROM intents
                WHERE jsonb_array_length(correction_history) > 0
                ORDER BY updated_at DESC
                LIMIT $1
            """, limit)
            
            return [
                {
                    "intent_id": str(row['intent_id']),
                    "correction_count": row['correction_count'],
                    "last_correction": row['last_correction']
                }
                for row in corrections
            ]
```

---

## 7. Operational Alerts

### 7.1 Alert Configuration

```python
# bridge/alerts/config.py

from dataclasses import dataclass
from enum import Enum

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    description: str
    severity: AlertSeverity
    condition: str  # SQL query or Python expression
    threshold: float
    cooldown_minutes: int = 5
    channels: list[AlertChannel] = None

# Default alert rules
DEFAULT_ALERT_RULES = [
    AlertRule(
        name="high_error_rate",
        description="Error rate exceeds 5% in last 10 minutes",
        severity=AlertSeverity.ERROR,
        condition="""
            SELECT 
                COUNT(CASE WHEN status = 'failed' THEN 1 END)::float / COUNT(*) as error_rate
            FROM intents
            WHERE created_at > NOW() - INTERVAL '10 minutes'
        """,
        threshold=0.05,
        cooldown_minutes=10,
        channels=[AlertChannel.SLACK, AlertChannel.EMAIL]
    ),
    AlertRule(
        name="high_correction_rate",
        description="Correction rate exceeds 20% in last hour",
        severity=AlertSeverity.WARNING,
        condition="""
            SELECT 
                COUNT(CASE WHEN jsonb_array_length(correction_history) > 0 THEN 1 END)::float / COUNT(*) as correction_rate
            FROM intents
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """,
        threshold=0.20,
        cooldown_minutes=30,
        channels=[AlertChannel.SLACK]
    ),
    AlertRule(
        name="slow_processing",
        description="Average processing time exceeds 5 seconds",
        severity=AlertSeverity.WARNING,
        condition="""
            SELECT AVG(duration_ms) / 1000.0 as avg_seconds
            FROM audit_logs_ts
            WHERE time > NOW() - INTERVAL '10 minutes'
              AND event_type = 'BRIDGE_COMPLETED'
        """,
        threshold=5.0,
        cooldown_minutes=15,
        channels=[AlertChannel.LOG]
    ),
    AlertRule(
        name="no_activity",
        description="No intents created in last 30 minutes",
        severity=AlertSeverity.INFO,
        condition="""
            SELECT COUNT(*) as count
            FROM intents
            WHERE created_at > NOW() - INTERVAL '30 minutes'
        """,
        threshold=1.0,  # Alert if count < 1
        cooldown_minutes=30,
        channels=[AlertChannel.LOG]
    )
]
```

### 7.2 Alert Manager

```python
# bridge/alerts/manager.py

import asyncpg
from datetime import datetime, timedelta
from typing import Dict, Optional
import aiohttp

class AlertManager:
    """
    Monitor metrics and trigger alerts.
    
    - Evaluates alert rules periodically
    - Sends notifications via configured channels
    - Implements cooldown to prevent alert spam
    """
    
    def __init__(
        self, 
        database_url: str,
        rules: list[AlertRule] = None
    ):
        self.database_url = database_url
        self.rules = rules or DEFAULT_ALERT_RULES
        
        # Track last alert time for cooldown
        self.last_alerts: Dict[str, datetime] = {}
    
    async def start(self, interval_seconds: float = 60):
        """Start periodic alert evaluation"""
        logger.info(f"Alert manager started with {len(self.rules)} rules")
        
        async with asyncpg.create_pool(self.database_url) as pool:
            while True:
                await self._evaluate_all_rules(pool)
                await asyncio.sleep(interval_seconds)
    
    async def _evaluate_all_rules(self, pool):
        """Evaluate all alert rules"""
        for rule in self.rules:
            try:
                await self._evaluate_rule(rule, pool)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
    
    async def _evaluate_rule(self, rule: AlertRule, pool):
        """Evaluate single alert rule"""
        # Check cooldown
        if not self._can_alert(rule):
            return
        
        # Execute condition query
        async with pool.acquire() as conn:
            result = await conn.fetchval(rule.condition)
        
        if result is None:
            return
        
        # Check threshold
        triggered = self._check_threshold(rule, result)
        
        if triggered:
            await self._send_alert(rule, result)
            self.last_alerts[rule.name] = datetime.utcnow()
    
    def _can_alert(self, rule: AlertRule) -> bool:
        """Check if alert can be sent (cooldown)"""
        last_alert = self.last_alerts.get(rule.name)
        
        if not last_alert:
            return True
        
        cooldown = timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.utcnow() - last_alert > cooldown
    
    def _check_threshold(self, rule: AlertRule, value: float) -> bool:
        """Check if value exceeds threshold"""
        if rule.name == "no_activity":
            # Special case: alert if BELOW threshold
            return value < rule.threshold
        else:
            return value > rule.threshold
    
    async def _send_alert(self, rule: AlertRule, value: float):
        """Send alert via configured channels"""
        alert_message = (
            f"[{rule.severity.upper()}] {rule.name}\n"
            f"{rule.description}\n"
            f"Current value: {value:.2f} (threshold: {rule.threshold})\n"
            f"Time: {datetime.utcnow().isoformat()}"
        )
        
        for channel in (rule.channels or []):
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email(rule, alert_message)
                
                elif channel == AlertChannel.SLACK:
                    await self._send_slack(rule, alert_message)
                
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook(rule, alert_message, value)
                
                elif channel == AlertChannel.LOG:
                    logger.warning(alert_message)
            
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
    
    async def _send_slack(self, rule: AlertRule, message: str):
        """Send Slack notification"""
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        
        if not webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured")
            return
        
        color = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9800",
            AlertSeverity.ERROR: "#f44336",
            AlertSeverity.CRITICAL: "#9c27b0"
        }[rule.severity]
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"🔔 {rule.name}",
                "text": message,
                "footer": "Bridge Lite Alert System",
                "ts": int(datetime.utcnow().timestamp())
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=payload)
    
    async def _send_email(self, rule: AlertRule, message: str):
        """Send email notification"""
        # Implementation using SMTP or email service
        pass
    
    async def _send_webhook(
        self, 
        rule: AlertRule, 
        message: str, 
        value: float
    ):
        """Send generic webhook"""
        webhook_url = os.environ.get("ALERT_WEBHOOK_URL")
        
        if not webhook_url:
            return
        
        payload = {
            "rule": rule.name,
            "severity": rule.severity.value,
            "message": message,
            "value": value,
            "threshold": rule.threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=payload)
```

---

## 8. Test Suite Expansion

### 8.1 Test Coverage Matrix

```
Category                           Sprint 2  Target  New Tests
─────────────────────────────────────────────────────────────
WebSocket connection management    0         4       +4
WebSocket event broadcasting       0         3       +3
SSE stream functionality          0         3       +3
Event distributor                 0         4       +4
Audit log ETL                     0         3       +3
Dashboard API                     0         3       +3
Metrics collection                0         2       +2
Alert evaluation                  0         3       +3
Integration tests                 0         3       +3
Load tests (100 WS connections)   0         2       +2
─────────────────────────────────────────────────────────────
Total                             38        68      +30
```

### 8.2 WebSocket Tests

```python
# tests/realtime/test_websocket.py

import pytest
from fastapi.testclient import TestClient
from bridge.api.app import app

@pytest.mark.asyncio
async def test_websocket_connect_and_disconnect():
    """Test: WebSocket connection lifecycle"""
    client = TestClient(app)
    
    with client.websocket_connect("/ws/intents") as websocket:
        # Send ping
        websocket.send_json({"type": "ping"})
        
        # Receive pong
        response = websocket.receive_json()
        assert response["type"] == "pong"
    
    # Connection should be cleaned up

@pytest.mark.asyncio
async def test_websocket_intent_subscription():
    """Test: Subscribe to specific intents"""
    client = TestClient(app)
    intent_id = str(uuid.uuid4())
    
    with client.websocket_connect(
        f"/ws/intents?intent_ids={intent_id}"
    ) as websocket:
        # Trigger intent update
        async with get_db_pool() as pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE intents 
                    SET status = 'processed' 
                    WHERE id = $1
                """, intent_id)
        
        # Receive update notification
        event = websocket.receive_json()
        
        assert event["type"] == "intent_update"
        assert event["data"]["intent_id"] == intent_id
        assert event["data"]["status"] == "processed"

@pytest.mark.asyncio
async def test_websocket_wildcard_subscription():
    """Test: Wildcard subscription receives all updates"""
    client = TestClient(app)
    
    with client.websocket_connect("/ws/intents") as websocket:
        # Create new intent
        intent_id = await create_test_intent()
        
        # Receive creation event
        event = websocket.receive_json()
        
        assert event["type"] == "intent_update"
        assert event["data"]["intent_id"] == str(intent_id)

@pytest.mark.asyncio
async def test_websocket_concurrent_connections():
    """Test: Multiple WebSocket connections work correctly"""
    client = TestClient(app)
    
    # Connect 10 WebSockets
    websockets = []
    for i in range(10):
        ws = client.websocket_connect("/ws/intents")
        websockets.append(ws)
    
    # Trigger intent update
    intent_id = await create_test_intent()
    
    # All should receive event
    for ws in websockets:
        event = ws.receive_json()
        assert event["data"]["intent_id"] == str(intent_id)
    
    # Cleanup
    for ws in websockets:
        ws.close()
```

### 8.3 ETL Tests

```python
# tests/etl/test_audit_log_etl.py

@pytest.mark.asyncio
async def test_etl_basic_flow():
    """Test: Audit logs are ETL'd to TimescaleDB"""
    # Create audit log
    log_id = await create_audit_log(
        event_type="BRIDGE_COMPLETED",
        intent_id=uuid.uuid4(),
        duration_ms=1500
    )
    
    # Wait for ETL
    await asyncio.sleep(6)  # ETL interval is 5s
    
    # Verify in TimescaleDB
    async with get_timescale_pool() as pool:
        async with pool.acquire() as conn:
            ts_log = await conn.fetchrow("""
                SELECT * FROM audit_logs_ts
                WHERE log_id = $1
            """, log_id)
            
            assert ts_log is not None
            assert ts_log['duration_ms'] == 1500

@pytest.mark.asyncio
async def test_etl_event_driven():
    """Test: Event-driven ETL has zero latency"""
    start = time.time()
    
    # Create audit log
    log_id = await create_audit_log(
        event_type="BRIDGE_STARTED",
        intent_id=uuid.uuid4()
    )
    
    # Check TimescaleDB immediately
    async with get_timescale_pool() as pool:
        async with pool.acquire() as conn:
            # Retry up to 1 second
            for _ in range(10):
                ts_log = await conn.fetchrow("""
                    SELECT * FROM audit_logs_ts
                    WHERE log_id = $1
                """, log_id)
                
                if ts_log:
                    break
                
                await asyncio.sleep(0.1)
    
    elapsed = time.time() - start
    
    assert ts_log is not None
    assert elapsed < 1.0, "Event-driven ETL should complete within 1 second"

@pytest.mark.asyncio
async def test_etl_aggregation():
    """Test: Continuous aggregation works"""
    # Create multiple logs over time
    for i in range(10):
        await create_audit_log(
            event_type="BRIDGE_COMPLETED",
            intent_id=uuid.uuid4(),
            duration_ms=1000 + i * 100
        )
    
    # Wait for aggregation
    await asyncio.sleep(10)
    
    # Check hourly aggregation
    async with get_timescale_pool() as pool:
        async with pool.acquire() as conn:
            agg = await conn.fetchrow("""
                SELECT 
                    event_count,
                    avg_duration_ms
                FROM audit_logs_hourly
                WHERE event_type = 'BRIDGE_COMPLETED'
                  AND bucket > NOW() - INTERVAL '1 hour'
                LIMIT 1
            """)
            
            assert agg['event_count'] >= 10
            assert 1000 <= agg['avg_duration_ms'] <= 2000
```

### 8.4 Load Tests

```python
# tests/performance/test_websocket_load.py

@pytest.mark.slow
@pytest.mark.asyncio
async def test_100_concurrent_websocket_connections():
    """Test: System handles 100 concurrent WebSocket connections"""
    client = TestClient(app)
    
    # Connect 100 WebSockets
    websockets = []
    
    start = time.time()
    
    for i in range(100):
        ws = client.websocket_connect("/ws/intents")
        websockets.append(ws)
    
    connection_time = time.time() - start
    
    # All connected within 5 seconds
    assert connection_time < 5.0
    
    # Trigger intent update
    intent_id = await create_test_intent()
    
    # All receive event within 1 second
    start = time.time()
    
    received_count = 0
    for ws in websockets:
        try:
            event = ws.receive_json(timeout=1.0)
            if event["data"]["intent_id"] == str(intent_id):
                received_count += 1
        except:
            pass
    
    broadcast_time = time.time() - start
    
    # At least 95% received
    assert received_count >= 95
    # Broadcast within 1 second
    assert broadcast_time < 1.0
    
    # Cleanup
    for ws in websockets:
        ws.close()

@pytest.mark.slow
@pytest.mark.asyncio
async def test_websocket_latency_under_load():
    """Test: WebSocket latency < 200ms under load"""
    client = TestClient(app)
    
    # Connect 50 WebSockets
    websockets = [
        client.websocket_connect("/ws/intents")
        for _ in range(50)
    ]
    
    latencies = []
    
    for i in range(20):
        start = time.time()
        
        # Update intent
        intent_id = await create_test_intent()
        
        # Measure time to receive event
        event = websockets[0].receive_json()
        
        latency = time.time() - start
        latencies.append(latency)
    
    # Average latency < 200ms
    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 0.2
    
    # P95 latency < 500ms
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)]
    assert p95_latency < 0.5
    
    # Cleanup
    for ws in websockets:
        ws.close()
```

---

## 9. Implementation Schedule

### Week 1 (Day 1-7): Real-time Event System

#### Day 1-2: Event Infrastructure
- [ ] PostgreSQL TRIGGER実装（intent_changed, audit_log_created）
- [ ] EventDistributor実装（LISTEN/NOTIFY統合）
- [ ] テスト4件（Event distributor tests）

#### Day 3-4: WebSocket
- [ ] WebSocketManager実装
- [ ] WebSocketエンドポイント実装
- [ ] テスト4件（WebSocket connection, subscription tests）

#### Day 5-7: SSE & Integration
- [ ] SSE実装（intent stream, audit log stream）
- [ ] テスト3件（SSE tests）
- [ ] 統合テスト3件（WebSocket + SSE + Event distributor）

### Week 2 (Day 8-14): ETL & Dashboard

#### Day 8-9: TimescaleDB Setup
- [ ] TimescaleDB schema作成
- [ ] 継続的集計ビュー作成
- [ ] テスト2件（Schema validation）

#### Day 10-11: ETL Implementation
- [ ] AuditLogETL実装（ポーリング版）
- [ ] EventDrivenAuditLogETL実装（推奨版）
- [ ] テスト3件（ETL tests）

#### Day 12-13: Dashboard API
- [ ] Dashboard API実装（overview, timeline, corrections）
- [ ] MetricsCollector実装
- [ ] テスト3件（Dashboard API tests）

#### Day 14: Alerts & Documentation
- [ ] AlertManager実装
- [ ] AlertRule設定
- [ ] テスト3件（Alert tests）
- [ ] 負荷テスト2件（100 WebSocket, latency）
- [ ] ドキュメント完成（アーキテクチャ、API、運用ガイド）

---

## 10. Success Criteria

### 10.1 Functional
- [ ] WebSocket接続が安定して動作
- [ ] Intent変更がリアルタイムで通知される
- [ ] SSEストリームが正常に動作
- [ ] 監査ログETLがゼロ遅延で動作（event-driven）
- [ ] ダッシュボードAPIが正確なメトリクスを返す
- [ ] アラートが閾値超過時に発火

### 10.2 Quality
- [ ] 68+ test cases passing（目標50+を超過）
- [ ] Code coverage > 80% for realtime module
- [ ] No regression in existing tests
- [ ] Documentation complete

### 10.3 Performance
- [ ] 100同時WebSocket接続をサポート
- [ ] WebSocket通知遅延 < 200ms
- [ ] ETL遅延 < 1秒（event-driven）
- [ ] Dashboard API応答時間 < 500ms

### 10.4 Review
- [ ] Kana review passed
- [ ] Code review passed
- [ ] Load testing passed

---

## 11. Operational Guide

### 11.1 Deployment

```bash
# 1. TimescaleDB extension有効化
psql -U resonant -d resonant -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# 2. Schema migration実行
psql -U resonant -d resonant -f migrations/sprint3_timescaledb.sql

# 3. Environment variables設定
export DATABASE_URL="postgresql://resonant:password@localhost:5432/resonant"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export ALERT_WEBHOOK_URL="https://..."

# 4. Start services
# EventDistributor (background daemon)
python -m bridge.realtime.event_distributor &

# AuditLogETL (background daemon)
python -m bridge.etl.audit_log_etl &

# AlertManager (background daemon)
python -m bridge.alerts.manager &

# FastAPI application
uvicorn bridge.api.app:app --host 0.0.0.0 --port 8000
```

### 11.2 Monitoring

```bash
# WebSocket connections
curl http://localhost:8000/api/v1/dashboard/overview | jq '.active_websockets'

# ETL lag
SELECT MAX(time) FROM audit_logs_ts;
SELECT MAX(created_at) FROM audit_logs;

# Alert status
tail -f logs/alerts.log

# Prometheus metrics
curl http://localhost:8000/metrics
```

### 11.3 Troubleshooting

**WebSocket接続が切れる:**
- NGINXタイムアウト設定確認（`proxy_read_timeout 3600s`）
- Keep-alive設定確認
- クライアント側のping/pong実装確認

**ETL遅延が大きい:**
- PostgreSQL NOTIFY動作確認（`SELECT pg_listening_channels();`）
- EventDistributor稼働確認
- TimescaleDB接続確認

**アラートが発火しない:**
- AlertManager稼働確認
- Alert rule条件確認（SQL実行テスト）
- Webhook URL設定確認

---

## 12. Future Enhancements (Out of Scope)

- **分散トランザクション**: 複数データベースにまたがるトランザクション
- **マルチテナント**: テナント分離とリソース管理
- **カスタムアラートルール**: UIからのルール設定
- **リアルタイムダッシュボード**: WebSocketベースの自動更新UI
- **高度なメトリクス**: ML-based anomaly detection

---

## 13. Related Documents

- Bridge Lite Specification v2.1 Unified
- Sprint 2 Specification (Concurrency Control)
- Priority 2: PostgreSQL環境構築計画
- TimescaleDB Documentation
- WebSocket Best Practices Guide

---

**作成日**: 2025-11-15  
**作成者**: Kana（外界翻訳層）  
**承認待ち**: 宏啓さん  
**実装担当**: Tsumu（Cursor）または Sonnet 4.5（実験継続の場合）
