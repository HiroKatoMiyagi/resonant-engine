#!/usr/bin/env python3
"""
Resonant Engine - FastAPI Backend
PostgreSQL連携API実装
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Set
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json
import sys

# Intent検出モジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
from intent_detector import detect_intent_from_message, should_auto_generate_intent

# 環境変数読み込み
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://resonant@localhost:5432/resonant")

# FastAPIアプリ初期化
app = FastAPI(
    title="Resonant Engine API",
    description="Intent駆動型開発支援プラットフォーム",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Viteデフォルトポート対応
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベース接続プール
@app.on_event("startup")
async def startup():
    """起動時にDB接続プールを作成"""
    app.state.pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10
    )
    print(f"✅ Database pool created: {DATABASE_URL}")

@app.on_event("shutdown")
async def shutdown():
    """終了時にDB接続プールをクローズ"""
    await app.state.pool.close()
    print("✅ Database pool closed")

# ========================================
# Pydanticモデル（リクエスト/レスポンス）
# ========================================

class MessageCreate(BaseModel):
    content: str
    sender: str = "user"
    thread_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    content: str
    sender: str
    created_at: datetime
    intent_id: Optional[str] = None

class SpecCreate(BaseModel):
    title: str
    content: str
    status: str = "draft"

class SpecResponse(BaseModel):
    id: str
    title: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime

class IntentResponse(BaseModel):
    id: str
    type: str
    status: str
    data: Optional[dict] = None
    created_at: datetime
    source: Optional[str] = None  # auto_generated or manual
    linked_message: Optional[dict] = None  # {id, content, sender, created_at}

# ========================================
# API エンドポイント
# ========================================

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "service": "Resonant Engine API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """DB接続確認"""
    try:
        async with app.state.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            return {
                "status": "healthy",
                "database": "connected",
                "result": result
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

# ========================================
# Messages API
# ========================================

@app.post("/api/messages", response_model=MessageResponse)
async def create_message(message: MessageCreate):
    """メッセージ作成（Intent自動生成機能付き）"""
    async with app.state.pool.acquire() as conn:
        # メッセージ保存
        row = await conn.fetchrow("""
            INSERT INTO messages (sender, content, thread_id)
            VALUES ($1, $2, $3)
            RETURNING id, sender, content, created_at, intent_id
        """, message.sender, message.content, message.thread_id)
        
        message_id = row['id']
        intent_id = row['intent_id']
        
        # Intent自動生成をチェック
        if should_auto_generate_intent(message.content):
            intent_info = detect_intent_from_message(message.content)
            
            if intent_info:
                # Intentを作成
                intent_row = await conn.fetchrow("""
                    INSERT INTO intents (type, status, data, source)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, 
                    intent_info["type"], 
                    "pending", 
                    json.dumps(intent_info["data"]),
                    "auto_generated"
                )
                
                intent_id = intent_row['id']
                
                # メッセージにintent_idを紐付け
                await conn.execute("""
                    UPDATE messages
                    SET intent_id = $1
                    WHERE id = $2
                """, intent_id, message_id)
                
                print(f"✨ Auto-generated Intent: {intent_info['type']} for message {message_id}")
        
        return MessageResponse(
            id=str(message_id),
            sender=row['sender'],
            content=row['content'],
            created_at=row['created_at'],
            intent_id=str(intent_id) if intent_id else None
        )

@app.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(limit: int = 50, thread_id: Optional[str] = None):
    """メッセージ一覧取得"""
    async with app.state.pool.acquire() as conn:
        if thread_id:
            rows = await conn.fetch("""
                SELECT id, sender, content, created_at, intent_id
                FROM messages
                WHERE thread_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, thread_id, limit)
        else:
            rows = await conn.fetch("""
                SELECT id, sender, content, created_at, intent_id
                FROM messages
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
        
        return [
            MessageResponse(
                id=str(row['id']),
                sender=row['sender'],
                content=row['content'],
                created_at=row['created_at'],
                intent_id=str(row['intent_id']) if row['intent_id'] else None
            )
            for row in rows
        ]

# ========================================
# Specs API
# ========================================

@app.post("/api/specs", response_model=SpecResponse)
async def create_spec(spec: SpecCreate):
    """仕様書作成"""
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO specs (title, content, status)
            VALUES ($1, $2, $3)
            RETURNING id, title, content, status, created_at, updated_at
        """, spec.title, spec.content, spec.status)
        
        return SpecResponse(
            id=str(row['id']),
            title=row['title'],
            content=row['content'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

@app.get("/api/specs", response_model=List[SpecResponse])
async def get_specs(limit: int = 50):
    """仕様書一覧取得"""
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, title, content, status, created_at, updated_at
            FROM specs
            ORDER BY updated_at DESC
            LIMIT $1
        """, limit)
        
        return [
            SpecResponse(
                id=str(row['id']),
                title=row['title'],
                content=row['content'],
                status=row['status'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]

@app.get("/api/specs/{spec_id}", response_model=SpecResponse)
async def get_spec(spec_id: str):
    """仕様書取得"""
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, title, content, status, created_at, updated_at
            FROM specs
            WHERE id = $1
        """, spec_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Spec not found")
        
        return SpecResponse(
            id=str(row['id']),
            title=row['title'],
            content=row['content'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

# ========================================
# Intents API
# ========================================

@app.get("/api/intents", response_model=List[IntentResponse])
async def get_intents(status: Optional[str] = None, limit: int = 50):
    """Intent一覧取得（リンクされたMessage情報も含む）"""
    async with app.state.pool.acquire() as conn:
        if status:
            rows = await conn.fetch("""
                SELECT 
                    i.id, i.type, i.status, i.data, i.created_at, i.source,
                    m.id as msg_id, m.content as msg_content, 
                    m.sender as msg_sender, m.created_at as msg_created_at
                FROM intents i
                LEFT JOIN messages m ON m.intent_id = i.id
                WHERE i.status = $1
                ORDER BY i.created_at DESC
                LIMIT $2
            """, status, limit)
        else:
            rows = await conn.fetch("""
                SELECT 
                    i.id, i.type, i.status, i.data, i.created_at, i.source,
                    m.id as msg_id, m.content as msg_content, 
                    m.sender as msg_sender, m.created_at as msg_created_at
                FROM intents i
                LEFT JOIN messages m ON m.intent_id = i.id
                ORDER BY i.created_at DESC
                LIMIT $1
            """, limit)
        
        return [
            IntentResponse(
                id=str(row['id']),
                type=row['type'],
                status=row['status'],
                data=json.loads(row['data']) if isinstance(row['data'], str) else row['data'],
                created_at=row['created_at'],
                source=row['source'],
                linked_message={
                    "id": str(row['msg_id']),
                    "content": row['msg_content'],
                    "sender": row['msg_sender'],
                    "created_at": row['msg_created_at'].isoformat() if row['msg_created_at'] else None
                } if row['msg_id'] else None
            )
            for row in rows
        ]

# ========================================
# 開発用エンドポイント
# ========================================

@app.get("/api/stats")
async def get_stats():
    """統計情報取得"""
    async with app.state.pool.acquire() as conn:
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        specs_count = await conn.fetchval("SELECT COUNT(*) FROM specs")
        messages_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
        intents_count = await conn.fetchval("SELECT COUNT(*) FROM intents")
        
        return {
            "users": users_count,
            "specs": specs_count,
            "messages": messages_count,
            "intents": intents_count
        }

# ========================================
# WebSocket リアルタイム通知
# ========================================

# 接続中のクライアント管理
active_connections: Set[WebSocket] = set()

async def notify_clients(message: dict):
    """全クライアントにメッセージをブロードキャスト"""
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.add(connection)
    
    # 切断されたクライアントを削除
    active_connections.difference_update(disconnected)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocketエンドポイント
    PostgreSQLのNOTIFYを購読して、データ変更をリアルタイム配信
    """
    await websocket.accept()
    active_connections.add(websocket)
    print(f"✅ WebSocket client connected. Total: {len(active_connections)}")
    
    # PostgreSQL LISTEN用の専用接続を作成
    listen_conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # table_changesチャネルを購読
        async def listener(connection, pid, channel, payload):
            """NOTIFY受信時のコールバック"""
            message = {
                "channel": channel,
                "payload": json.loads(payload)
            }
            await notify_clients(message)
        
        await listen_conn.add_listener('table_changes', listener)
        
        # WebSocketからのメッセージを待機（クライアント側からは送信しない）
        while True:
            try:
                # WebSocketの接続維持とクライアント側からのping対応
                data = await websocket.receive_text()
                # pingメッセージを受け取ったらpongを返す
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
            
    except WebSocketDisconnect:
        print(f"🔌 WebSocket client disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # クリーンアップ
        active_connections.discard(websocket)
        try:
            await listen_conn.close()
        except Exception:
            pass
        print(f"📊 Remaining connections: {len(active_connections)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
