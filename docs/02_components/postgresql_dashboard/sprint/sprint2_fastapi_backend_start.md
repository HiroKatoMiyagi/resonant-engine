# Sprint 2: FastAPI バックエンドAPI 作業開始指示書

**対象**: Tsumu (Cursor) または実装担当者
**期間**: 4日間想定
**前提**: Sprint 1 (Docker Compose + PostgreSQL) 完了

---

## 0. 重要な前提条件

- [ ] Sprint 1 Done Definition (Tier 1) 全て完了
- [ ] PostgreSQLが稼働中（`./scripts/check-health.sh` PASS）
- [ ] Python 3.11以上インストール済み
- [ ] 仕様書 `sprint2_fastapi_backend_spec.md` を通読済み

**確認コマンド**:
```bash
cd docker && ./scripts/check-health.sh
python --version  # >= 3.11
```

---

## 1. Done Definition

### Tier 1: 必須
- [ ] FastAPIアプリケーション起動（uvicorn）
- [ ] Messages CRUD API (5 endpoints)
- [ ] Specifications CRUD API (5 endpoints)
- [ ] Intents CRUD API (6 endpoints)
- [ ] Notifications CRUD API (5 endpoints)
- [ ] asyncpg接続プール設定
- [ ] Swagger UI自動生成（/docs）
- [ ] CORS設定完了
- [ ] 基本エラーハンドリング

### Tier 2: 品質保証
- [ ] 単体テスト 20件以上PASS
- [ ] API応答時間 < 100ms
- [ ] Pydanticバリデーション動作
- [ ] ログミドルウェア実装
- [ ] Dockerfile作成

---

## 2. 実装スケジュール（4日間）

### Day 1 (6時間): プロジェクト構造とデータベース接続

**タスク1**: ディレクトリ構造作成
```bash
cd /Users/zero/Projects/resonant-engine
mkdir -p backend/app/{models,routers,services,repositories}
mkdir -p backend/tests
touch backend/app/__init__.py
touch backend/app/main.py
touch backend/app/config.py
touch backend/app/database.py
touch backend/app/dependencies.py
touch backend/requirements.txt
touch backend/Dockerfile
touch backend/README.md
```

**タスク2**: requirements.txt
```text
fastapi==0.104.1
uvicorn[standard]==0.24.0
asyncpg==0.29.0
pydantic==2.5.2
python-dotenv==1.0.0
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

**タスク3**: config.py実装
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "resonant"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "resonant_dashboard"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    class Config:
        env_file = ".env"

settings = Settings()
```

**タスク4**: database.py実装（接続プール）
```python
import asyncpg
from app.config import settings

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=5,
            max_size=20
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

db = Database()
```

**タスク5**: main.py基本実装
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    print("✅ Database connected")
    yield
    await db.disconnect()
    print("Database disconnected")

app = FastAPI(
    title="Resonant Dashboard API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/")
async def root():
    return {"message": "Resonant Dashboard API", "version": "1.0.0"}
```

**検証**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env作成（docker/.envをコピー）
cp ../docker/.env .env
# POSTGRES_HOST=localhost に変更

uvicorn app.main:app --reload --port 8000

# 別ターミナル
curl http://localhost:8000/health
# {"status": "healthy", "database": "connected"}

open http://localhost:8000/docs
# Swagger UI表示
```

**完了基準**:
- [ ] FastAPIが起動
- [ ] /health エンドポイント動作
- [ ] Swagger UI表示
- [ ] データベース接続成功

---

### Day 2 (6時間): Pydanticモデルとリポジトリ層

**タスク1**: Pydanticモデル作成（4ファイル）

`app/models/message.py`:
```python
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    YUNO = "yuno"
    KANA = "kana"
    SYSTEM = "system"

class MessageCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = MessageType.USER
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    id: UUID
    user_id: str
    content: str
    message_type: MessageType
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageListResponse(BaseModel):
    items: List[MessageResponse]
    total: int
    limit: int
    offset: int
```

同様に `specification.py`, `intent.py`, `notification.py` を作成。

**タスク2**: ベースリポジトリ作成

`app/repositories/base.py`:
```python
from app.database import db

class BaseRepository:
    def __init__(self):
        self.db = db
```

**タスク3**: MessageRepository作成

`app/repositories/message_repo.py`:
```python
from uuid import UUID
from typing import List, Optional
from app.repositories.base import BaseRepository
from app.models.message import MessageCreate, MessageUpdate, MessageResponse

class MessageRepository(BaseRepository):
    async def create(self, data: MessageCreate) -> MessageResponse:
        query = """
        INSERT INTO messages (user_id, content, message_type, metadata)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """
        row = await self.db.fetchrow(
            query, data.user_id, data.content, data.message_type.value, data.metadata
        )
        return self._to_response(row)

    async def get_by_id(self, id: UUID) -> Optional[MessageResponse]:
        query = "SELECT * FROM messages WHERE id = $1"
        row = await self.db.fetchrow(query, id)
        return self._to_response(row) if row else None

    async def list(
        self,
        user_id: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[MessageResponse], int]:
        where_clauses = []
        params = []
        param_count = 0

        if user_id:
            param_count += 1
            where_clauses.append(f"user_id = ${param_count}")
            params.append(user_id)

        if message_type:
            param_count += 1
            where_clauses.append(f"message_type = ${param_count}")
            params.append(message_type)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count
        count_query = f"SELECT COUNT(*) FROM messages WHERE {where_sql}"
        total = await self.db.fetchrow(count_query, *params)
        total_count = total['count']

        # Fetch
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        query = f"""
        SELECT * FROM messages
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
        rows = await self.db.fetch(query, *params, limit, offset)

        return [self._to_response(row) for row in rows], total_count

    async def update(self, id: UUID, data: MessageUpdate) -> Optional[MessageResponse]:
        updates = []
        params = [id]
        param_count = 1

        if data.content is not None:
            param_count += 1
            updates.append(f"content = ${param_count}")
            params.append(data.content)

        if data.metadata is not None:
            param_count += 1
            updates.append(f"metadata = ${param_count}")
            params.append(data.metadata)

        if not updates:
            return await self.get_by_id(id)

        updates.append("updated_at = NOW()")
        query = f"""
        UPDATE messages SET {', '.join(updates)}
        WHERE id = $1
        RETURNING *
        """
        row = await self.db.fetchrow(query, *params)
        return self._to_response(row) if row else None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM messages WHERE id = $1 RETURNING id"
        result = await self.db.fetchrow(query, id)
        return result is not None

    def _to_response(self, row) -> MessageResponse:
        return MessageResponse(
            id=row['id'],
            user_id=row['user_id'],
            content=row['content'],
            message_type=row['message_type'],
            metadata=row['metadata'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
```

同様に他のリポジトリも作成。

**完了基準**:
- [ ] 4つのPydanticモデルファイル作成
- [ ] 4つのリポジトリファイル作成
- [ ] 型定義が完全

---

### Day 3 (6時間): APIルーター実装

**タスク1**: Messagesルーター

`app/routers/messages.py`:
```python
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.message import *
from app.repositories.message_repo import MessageRepository

router = APIRouter(prefix="/api/messages", tags=["messages"])
repo = MessageRepository()

@router.get("", response_model=MessageListResponse)
async def list_messages(
    user_id: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    items, total = await repo.list(user_id, message_type, limit, offset)
    return MessageListResponse(items=items, total=total, limit=limit, offset=offset)

@router.get("/{id}", response_model=MessageResponse)
async def get_message(id: UUID):
    msg = await repo.get_by_id(id)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
    return msg

@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(data: MessageCreate):
    return await repo.create(data)

@router.put("/{id}", response_model=MessageResponse)
async def update_message(id: UUID, data: MessageUpdate):
    msg = await repo.update(id, data)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
    return msg

@router.delete("/{id}", status_code=204)
async def delete_message(id: UUID):
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
```

**タスク2**: 他のルーター作成
- specifications.py
- intents.py
- notifications.py

**タスク3**: main.pyにルーター登録
```python
from app.routers import messages, specifications, intents, notifications

app.include_router(messages.router)
app.include_router(specifications.router)
app.include_router(intents.router)
app.include_router(notifications.router)
```

**検証**:
```bash
uvicorn app.main:app --reload

# Swagger UIで全エンドポイント確認
open http://localhost:8000/docs

# curlテスト
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{"user_id": "hiroki", "content": "Test message"}'

curl http://localhost:8000/api/messages
```

**完了基準**:
- [ ] 21エンドポイント実装完了
- [ ] Swagger UIに全API表示
- [ ] CRUD操作が動作

---

### Day 4 (6時間): テストとDocker統合

**タスク1**: テスト実装

`tests/conftest.py`:
```python
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.database import db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def setup_db():
    await db.connect()
    yield
    await db.disconnect()
```

`tests/test_messages.py`:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_message(client: AsyncClient):
    response = await client.post("/api/messages", json={
        "user_id": "test",
        "content": "Test message"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["content"] == "Test message"

@pytest.mark.asyncio
async def test_list_messages(client: AsyncClient):
    response = await client.get("/api/messages")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_get_nonexistent_message(client: AsyncClient):
    response = await client.get("/api/messages/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
```

**タスク2**: Dockerfile確認
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**タスク3**: docker-compose.yml更新
```yaml
backend:
  build:
    context: ../backend
    dockerfile: Dockerfile
  container_name: resonant_backend
  ports:
    - "8000:8000"
  environment:
    POSTGRES_HOST: postgres
    POSTGRES_PORT: 5432
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: ${POSTGRES_DB}
  depends_on:
    postgres:
      condition: service_healthy
  networks:
    - resonant_network
```

**検証**:
```bash
# テスト実行
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/ -v

# Docker統合テスト
cd ../docker
docker-compose up --build -d
curl http://localhost:8000/health
```

**完了基準**:
- [ ] テスト20件以上PASS
- [ ] Dockerでのビルド成功
- [ ] docker-compose統合完了

---

## 3. 完了報告書テンプレート

1. **Done Definition達成状況**: Tier 1: X/9, Tier 2: X/5
2. **実装成果物**: エンドポイント数、ファイル数、コード行数
3. **性能測定**: API応答時間、DB接続時間
4. **テスト結果**: テストカバレッジ、PASS/FAIL数
5. **次のアクション**: Sprint 3への準備状況

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**承認待ち**: 宏啓（プロジェクトオーナー）
