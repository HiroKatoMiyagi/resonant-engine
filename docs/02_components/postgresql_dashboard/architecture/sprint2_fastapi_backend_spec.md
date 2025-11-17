# Sprint 2: FastAPI バックエンドAPI仕様書

## 0. CRITICAL: APIの本質

**⚠️ IMPORTANT: 「API = ダッシュボードとデータベースの呼吸を繋ぐ」**

FastAPIバックエンドは、PostgreSQLに格納されたデータをReactフロントエンドに提供する「翻訳層」です。

### FastAPI Philosophy

```yaml
fastapi_philosophy:
  essence: "API = データの呼気を外界に届ける管"
  purpose:
    - PostgreSQLのデータをJSON形式で提供
    - フロントエンドとデータベースの分離
    - 型安全性とバリデーションの確保
    - リアルタイム通信基盤の準備
  principles:
    - 「RESTful設計で予測可能なAPI」
    - 「Pydanticで型安全性を保証」
    - 「非同期処理で高性能を実現」
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] FastAPIアプリケーションが起動
- [ ] Messages CRUD API (5 endpoints)
- [ ] Specifications CRUD API (5 endpoints)
- [ ] Intents CRUD API (5 endpoints)
- [ ] Notifications CRUD API (4 endpoints)
- [ ] データベース接続プール設定
- [ ] Swagger UI自動生成
- [ ] エラーハンドリング実装
- [ ] 基本的なCORSミドルウェア設定

#### Tier 2: 品質要件
- [ ] 単体テスト 20件以上
- [ ] 統合テスト 10件以上
- [ ] API応答時間 < 100ms
- [ ] Pydanticスキーマバリデーション
- [ ] ログミドルウェア実装
- [ ] Dockerfileの作成

---

## 1. 概要

### 1.1 目的
Sprint 1で構築したPostgreSQLデータベースに対するRESTful APIを実装し、Sprint 3のReactフロントエンドからのデータアクセスを可能にする。

### 1.2 スコープ

**IN Scope**:
- FastAPI アプリケーション基盤
- Messages API (CRUD + 検索)
- Specifications API (CRUD + バージョン管理)
- Intents API (CRUD + ステータス更新)
- Notifications API (CRUD + 既読管理)
- データベース接続プール（asyncpg）
- Pydantic スキーマ定義
- エラーハンドリング
- CORS設定
- Swagger UI

**OUT of Scope**:
- 認証・認可（Phase 4）
- WebSocket（Sprint 4で検討）
- ファイルアップロード
- キャッシュ層

---

## 2. アーキテクチャ

### 2.1 システム構成

```
┌─────────────────────────────────────────────────┐
│           Docker Compose Environment            │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │       FastAPI Container                  │   │
│  │  Port: 8000                              │   │
│  │                                          │   │
│  │  ┌─────────────────────────────────┐    │   │
│  │  │   Application Layer             │    │   │
│  │  │   - Routers (messages, specs..) │    │   │
│  │  │   - Middleware (CORS, logging)  │    │   │
│  │  └──────────────┬──────────────────┘    │   │
│  │                 │                        │   │
│  │  ┌──────────────▼──────────────────┐    │   │
│  │  │   Service Layer                 │    │   │
│  │  │   - Business Logic              │    │   │
│  │  │   - Validation                  │    │   │
│  │  └──────────────┬──────────────────┘    │   │
│  │                 │                        │   │
│  │  ┌──────────────▼──────────────────┐    │   │
│  │  │   Repository Layer              │    │   │
│  │  │   - Database Operations         │    │   │
│  │  │   - asyncpg Connection Pool     │    │   │
│  │  └──────────────────────────────────┘    │   │
│  └─────────────────────────────────────────┘   │
│                        │                        │
│                        ▼                        │
│  ┌─────────────────────────────────────────┐   │
│  │       PostgreSQL Container (Sprint 1)   │   │
│  │       Port: 5432                         │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 2.2 ディレクトリ構造

```
resonant-engine/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPIエントリーポイント
│   │   ├── config.py            # 設定管理
│   │   ├── database.py          # DB接続プール
│   │   ├── dependencies.py      # 依存性注入
│   │   ├── models/              # Pydanticスキーマ
│   │   │   ├── __init__.py
│   │   │   ├── message.py
│   │   │   ├── specification.py
│   │   │   ├── intent.py
│   │   │   └── notification.py
│   │   ├── routers/             # APIルーター
│   │   │   ├── __init__.py
│   │   │   ├── messages.py
│   │   │   ├── specifications.py
│   │   │   ├── intents.py
│   │   │   └── notifications.py
│   │   ├── services/            # ビジネスロジック
│   │   │   ├── __init__.py
│   │   │   ├── message_service.py
│   │   │   ├── specification_service.py
│   │   │   ├── intent_service.py
│   │   │   └── notification_service.py
│   │   └── repositories/        # データアクセス層
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── message_repo.py
│   │       ├── specification_repo.py
│   │       ├── intent_repo.py
│   │       └── notification_repo.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_messages.py
│   │   ├── test_specifications.py
│   │   ├── test_intents.py
│   │   └── test_notifications.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
└── docker/
    └── docker-compose.yml       # 更新（FastAPI追加）
```

---

## 3. データモデル（Pydantic）

### 3.1 Message Models

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


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = MessageType.USER
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    user_id: str = Field(..., min_length=1, max_length=100)


class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = None


class MessageInDB(MessageBase):
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(MessageInDB):
    pass


class MessageListResponse(BaseModel):
    items: List[MessageResponse]
    total: int
    limit: int
    offset: int
```

### 3.2 Specification Models

```python
class SpecificationStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"


class SpecificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    status: SpecificationStatus = SpecificationStatus.DRAFT
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SpecificationCreate(SpecificationBase):
    pass


class SpecificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    status: Optional[SpecificationStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SpecificationInDB(SpecificationBase):
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpecificationResponse(SpecificationInDB):
    pass
```

### 3.3 Intent Models

```python
class IntentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IntentBase(BaseModel):
    description: str = Field(..., min_length=1)
    intent_type: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentCreate(IntentBase):
    pass


class IntentUpdate(BaseModel):
    description: Optional[str] = None
    intent_type: Optional[str] = None
    status: Optional[IntentStatus] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class IntentStatusUpdate(BaseModel):
    status: IntentStatus
    result: Optional[Dict[str, Any]] = None


class IntentInDB(IntentBase):
    id: UUID
    status: IntentStatus
    result: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class IntentResponse(IntentInDB):
    pass
```

### 3.4 Notification Models

```python
class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    message: Optional[str] = None
    notification_type: NotificationType = NotificationType.INFO
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationCreate(NotificationBase):
    user_id: str = Field(..., min_length=1, max_length=100)


class NotificationInDB(NotificationBase):
    id: UUID
    user_id: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(NotificationInDB):
    pass


class NotificationMarkReadRequest(BaseModel):
    notification_ids: List[UUID]
```

---

## 4. API設計

### 4.1 Messages API

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/messages` | メッセージ一覧取得 |
| GET | `/api/messages/{id}` | メッセージ詳細取得 |
| POST | `/api/messages` | メッセージ作成 |
| PUT | `/api/messages/{id}` | メッセージ更新 |
| DELETE | `/api/messages/{id}` | メッセージ削除 |

**GET /api/messages クエリパラメータ**:
- `user_id`: ユーザーIDフィルタ
- `message_type`: メッセージタイプフィルタ
- `limit`: 取得件数（default: 50, max: 100）
- `offset`: オフセット（default: 0）
- `order_by`: ソート項目（created_at）
- `order_dir`: ソート方向（asc/desc）

### 4.2 Specifications API

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/specifications` | 仕様書一覧取得 |
| GET | `/api/specifications/{id}` | 仕様書詳細取得 |
| POST | `/api/specifications` | 仕様書作成 |
| PUT | `/api/specifications/{id}` | 仕様書更新 |
| DELETE | `/api/specifications/{id}` | 仕様書削除 |

**GET /api/specifications クエリパラメータ**:
- `status`: ステータスフィルタ
- `tags`: タグフィルタ（カンマ区切り）
- `search`: タイトル検索
- `limit`, `offset`, `order_by`, `order_dir`

### 4.3 Intents API

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/intents` | Intent一覧取得 |
| GET | `/api/intents/{id}` | Intent詳細取得 |
| POST | `/api/intents` | Intent作成 |
| PUT | `/api/intents/{id}` | Intent更新 |
| PATCH | `/api/intents/{id}/status` | ステータス更新 |
| DELETE | `/api/intents/{id}` | Intent削除 |

**GET /api/intents クエリパラメータ**:
- `status`: ステータスフィルタ
- `intent_type`: タイプフィルタ
- `priority_min`: 最小優先度
- `limit`, `offset`, `order_by`, `order_dir`

### 4.4 Notifications API

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/notifications` | 通知一覧取得 |
| GET | `/api/notifications/{id}` | 通知詳細取得 |
| POST | `/api/notifications` | 通知作成 |
| POST | `/api/notifications/mark-read` | 既読マーク |
| DELETE | `/api/notifications/{id}` | 通知削除 |

**GET /api/notifications クエリパラメータ**:
- `user_id`: ユーザーIDフィルタ
- `is_read`: 既読フィルタ
- `notification_type`: タイプフィルタ
- `limit`, `offset`

---

## 5. データベース接続

### 5.1 Connection Pool設定

```python
# app/database.py
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
            max_size=20,
            command_timeout=60
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)


db = Database()
```

### 5.2 Lifespan Events

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    print("Database connected")
    yield
    # Shutdown
    await db.disconnect()
    print("Database disconnected")


app = FastAPI(
    title="Resonant Dashboard API",
    version="1.0.0",
    lifespan=lifespan
)
```

---

## 6. エラーハンドリング

### 6.1 カスタム例外

```python
# app/exceptions.py
from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {id} not found"
        )


class ValidationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class DatabaseException(HTTPException):
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
```

### 6.2 グローバルエラーハンドラー

```python
# app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )
```

---

## 7. ミドルウェア

### 7.1 CORS設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7.2 ログミドルウェア

```python
import time
import logging
from fastapi import Request

logger = logging.getLogger("api")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s "
        f"status={response.status_code}"
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## 8. Docker Compose更新

### 8.1 docker-compose.yml追加

```yaml
services:
  postgres:
    # Sprint 1の設定（変更なし）
    ...

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: resonant_backend
    restart: unless-stopped
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${POSTGRES_USER:-resonant}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-resonant_dashboard}
      DEBUG: ${DEBUG:-true}
      LOG_LEVEL: ${LOG_LEVEL:-DEBUG}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - resonant_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 8.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.3 requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
asyncpg==0.29.0
pydantic==2.5.2
python-dotenv==1.0.0
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

---

## 9. テスト要件

### 9.1 単体テスト（20件以上）

```python
# tests/test_messages.py
@pytest.mark.asyncio
async def test_create_message():
    """メッセージ作成テスト"""
    pass

@pytest.mark.asyncio
async def test_get_message():
    """メッセージ取得テスト"""
    pass

@pytest.mark.asyncio
async def test_list_messages():
    """メッセージ一覧テスト"""
    pass

@pytest.mark.asyncio
async def test_update_message():
    """メッセージ更新テスト"""
    pass

@pytest.mark.asyncio
async def test_delete_message():
    """メッセージ削除テスト"""
    pass

# 同様に他のリソースも各5テスト以上
```

### 9.2 統合テスト（10件以上）

```python
@pytest.mark.asyncio
async def test_full_message_flow():
    """メッセージCRUDフローテスト"""
    pass

@pytest.mark.asyncio
async def test_specification_versioning():
    """仕様書バージョン管理テスト"""
    pass

@pytest.mark.asyncio
async def test_intent_status_workflow():
    """Intentステータス遷移テスト"""
    pass
```

---

## 10. 成功基準

### 10.1 機能要件
- [ ] FastAPIが正常起動
- [ ] 全CRUD操作が動作
- [ ] Swagger UIでAPI確認可能
- [ ] データベース接続が安定

### 10.2 品質要件
- [ ] API応答時間 < 100ms
- [ ] テストカバレッジ 80%以上
- [ ] エラーハンドリング完全実装
- [ ] ログ出力が適切

### 10.3 ドキュメント要件
- [ ] API仕様書（Swagger）
- [ ] README.md完成
- [ ] セットアップガイド

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**対象**: Sprint 2実装
**前提条件**: Sprint 1完了
