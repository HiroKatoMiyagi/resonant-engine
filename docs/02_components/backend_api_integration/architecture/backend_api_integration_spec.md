# Backend API 高度機能統合 仕様書

## 0. CRITICAL: Backend API as Unified Interface

**⚠️ IMPORTANT: 「Backend API = 全機能への統一インターフェース」**

Backend APIは、独立モジュールとして実装された高度機能（Contradiction Detection, Re-evaluation等）をWebUIから利用可能にする統一インターフェースです。現在、これらの機能は実装済みだが、Backend APIに統合されていないため、ブラウザから利用できません。

```yaml
backend_api_integration_philosophy:
    essence: "統合 = 既存機能をWebUIに接続する橋渡し"
    purpose:
        - 独立モジュールのBackend API統合
        - WebUIからの統一的なアクセス
        - 一貫したAPI設計の維持
        - プレースホルダーの削除
    principles:
        - "既存実装を活用、車輪の再発明をしない"
        - "import して使用、実装をコピーしない"
        - "統一的なエラーハンドリング"
        - "一貫したレスポンス形式"
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] Contradiction Detection完全実装（プレースホルダー削除）
- [ ] Re-evaluation API統合
- [ ] Choice Preservation API統合
- [ ] Memory Lifecycle API統合
- [ ] Dashboard Analytics API統合
- [ ] 全エンドポイントが200 OKを返す
- [ ] 20件以上の統合テストが作成され、CI で緑
- [ ] Frontend仕様書の更新（「2つのAPI」記載削除）

#### Tier 2: 品質要件
- [ ] APIレスポンス < 2秒
- [ ] エラーハンドリング完備
- [ ] Swagger UI更新
- [ ] Docker環境で動作確認
- [ ] 既存機能（Messages等）への影響なし

---

## 1. 概要

### 1.1 目的
独立モジュールとして実装済みの高度機能をBackend API（backend/app/）に統合し、WebUIから利用可能にする。

### 1.2 背景

**現状の問題:**
```
機能実装率: 85-90%（独立モジュールとして完成）
Backend API統合率: 40%（基本CRUDのみ）
WebUIからの利用率: 40%（高度機能が使えない）
```

**実装済みの独立モジュール:**
- ✅ `bridge/contradiction/` - Contradiction Detection (100%)
- ✅ `bridge/api/reeval.py` - Re-evaluation Phase (90%)
- ✅ `memory_store/` - Choice Preservation (100%)
- ✅ `memory_lifecycle/` - Memory Lifecycle (100%)
- ✅ `bridge/api/dashboard.py` - Dashboard Analytics

**Backend APIの現状:**
- ✅ Messages, Intents, Specifications, Notifications（完全実装）
- ⚠️ WebSocket（基本機能のみ）
- ❌ Contradictions（プレースホルダーのみ）
- ❌ 高度機能（未統合）

### 1.3 目標
- プレースホルダー削除、完全実装に置き換え
- 独立モジュールをimport、Backend APIのルーターから利用
- WebUIから全機能にアクセス可能
- Frontend仕様書の修正（「2つのAPI」削除）

### 1.4 スコープ

**含む:**
- Contradiction Detection API完全実装
- Re-evaluation API統合
- Choice Preservation API統合
- Memory Lifecycle API統合
- Dashboard Analytics API統合
- requirements.txt更新
- Dockerイメージ再ビルド
- 統合テスト作成
- Frontend仕様書更新

**含まない（将来拡張）:**
- Temporal Constraint（45%実装のみ、完成後に統合）
- Term Drift Detection（未実装）
- 認証・認可機能

---

## 2. アーキテクチャ

### 2.1 全体構成

**Before（現状）:**
```
PostgreSQL ← Backend API (40%統合) ← Frontend
              ├─ Messages      ✅
              ├─ Intents        ✅
              ├─ Specifications ✅
              ├─ Notifications  ✅
              ├─ WebSocket      ⚠️
              └─ Contradictions ❌ (プレースホルダー)

独立モジュール（未統合）
├─ bridge/contradiction/     ← 使われていない
├─ bridge/api/reeval.py      ← 使われていない
├─ memory_store/             ← 使われていない
├─ memory_lifecycle/         ← 使われていない
└─ bridge/api/dashboard.py   ← 使われていない
```

**After（統合後）:**
```
PostgreSQL ← Backend API (100%統合) ← Frontend
              ├─ Messages              ✅
              ├─ Intents                ✅
              ├─ Specifications         ✅
              ├─ Notifications          ✅
              ├─ WebSocket              ✅
              ├─ Contradictions         ✅ ← import bridge.contradiction
              ├─ Re-evaluation          ✅ ← import bridge.api.reeval
              ├─ Choice Preservation    ✅ ← import memory_store
              ├─ Memory Lifecycle       ✅ ← import memory_lifecycle
              └─ Dashboard Analytics    ✅ ← import bridge.api.dashboard
```

### 2.2 ディレクトリ構造

```
resonant-engine/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── messages.py              ✅ 既存
│   │   │   ├── intents.py                ✅ 既存
│   │   │   ├── specifications.py         ✅ 既存
│   │   │   ├── notifications.py          ✅ 既存
│   │   │   ├── websocket.py              ✅ 既存
│   │   │   ├── contradictions.py         🔧 修正（プレースホルダー削除）
│   │   │   ├── re_evaluation.py          🆕 新規
│   │   │   ├── choice_points.py          🆕 新規
│   │   │   ├── memory_lifecycle.py       🆕 新規
│   │   │   └── dashboard_analytics.py    🆕 新規
│   │   ├── dependencies.py               🔧 修正（DI追加）
│   │   └── main.py                       🔧 修正（ルーター登録）
│   ├── requirements.txt                  🔧 修正（依存関係追加）
│   └── Dockerfile                        🔧 修正（COPY追加）
│
├── bridge/                               ✅ 既存（変更なし）
│   ├── contradiction/
│   └── api/
│       ├── reeval.py
│       └── dashboard.py
│
├── memory_store/                         ✅ 既存（変更なし）
├── memory_lifecycle/                     ✅ 既存（変更なし）
└── context_assembler/                    ✅ 既存（変更なし）
```

---

## 3. 統合対象機能

### 3.1 Contradiction Detection API

**実装場所**: `bridge/contradiction/`
**実装率**: 100%
**テスト**: 48件全合格

**既存のプレースホルダー（削除対象）:**
```python
# backend/app/routers/contradictions.py（現状）
@router.get("/pending")
async def get_pending_contradictions(user_id: str):
    # TODO: Connect to Bridge API or implement full contradiction detection
    return {"contradictions": [], "count": 0}  # ← これを削除
```

**統合後（完全実装）:**
```python
# backend/app/routers/contradictions.py（修正後）
from bridge.contradiction.detector import ContradictionDetector
from bridge.contradiction.models import ContradictionResult

@router.get("/pending", response_model=ContradictionListResponse)
async def get_pending_contradictions(
    user_id: str = Query(...),
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """未解決の矛盾一覧を取得"""
    contradictions = await detector.get_pending_contradictions(user_id)
    return ContradictionListResponse(
        contradictions=contradictions,
        count=len(contradictions)
    )

@router.post("/check", response_model=ContradictionListResponse)
async def check_intent_for_contradictions(
    request: CheckContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """Intentの矛盾をチェック"""
    contradictions = await detector.check_intent(
        user_id=request.user_id,
        intent_id=request.intent_id,
        intent_content=request.intent_content
    )
    return ContradictionListResponse(
        contradictions=contradictions,
        count=len(contradictions)
    )

@router.put("/{contradiction_id}/resolve")
async def resolve_contradiction(
    contradiction_id: UUID,
    request: ResolveContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """矛盾を解決"""
    result = await detector.resolve_contradiction(
        contradiction_id=contradiction_id,
        resolution_action=request.resolution_action,
        resolution_rationale=request.resolution_rationale,
        resolved_by=request.resolved_by
    )
    return {"status": "resolved", "contradiction_id": str(contradiction_id)}
```

### 3.2 Re-evaluation API

**実装場所**: `bridge/api/reeval.py`
**実装率**: 90%

**新規ルーター:**
```python
# backend/app/routers/re_evaluation.py（新規作成）
from fastapi import APIRouter, Depends, HTTPException
from bridge.api.reeval import router as reeval_router
from bridge.core.models.intent_model import IntentModel

router = APIRouter(prefix="/api/v1/intent", tags=["re-evaluation"])

@router.post("/reeval")
async def re_evaluate_intent(
    request: ReEvalRequest,
    bridge_set = Depends(get_bridge_set)
):
    """Intent再評価"""
    # bridge.api.reevalの機能を利用
    result = await bridge_set.feedback.evaluate_intent(
        intent_id=request.intent_id,
        diff=request.diff,
        source=request.source,
        reason=request.reason
    )
    return result
```

### 3.3 Choice Preservation API

**実装場所**: `memory_store/`
**実装率**: 100%

**新規ルーター:**
```python
# backend/app/routers/choice_points.py（新規作成）
from fastapi import APIRouter, Depends, Query
from memory_store.service import MemoryStoreService
from memory_store.models import ChoicePoint

router = APIRouter(prefix="/api/v1/memory/choice-points", tags=["choice-preservation"])

@router.get("/pending")
async def get_pending_choice_points(
    user_id: str = Query(...),
    memory_service: MemoryStoreService = Depends(get_memory_service)
):
    """未決定の選択肢を取得"""
    pending = await memory_service.get_pending_choice_points(user_id)
    return {"choice_points": pending, "count": len(pending)}

@router.post("/")
async def create_choice_point(
    request: CreateChoicePointRequest,
    memory_service: MemoryStoreService = Depends(get_memory_service)
):
    """新しい選択肢を作成"""
    choice_point = await memory_service.create_choice_point(
        user_id=request.user_id,
        question=request.question,
        choices=request.choices,
        tags=request.tags,
        context_type=request.context_type
    )
    return {"choice_point": choice_point}

@router.put("/{choice_point_id}/decide")
async def decide_choice(
    choice_point_id: UUID,
    request: DecideChoiceRequest,
    memory_service: MemoryStoreService = Depends(get_memory_service)
):
    """選択を決定"""
    choice_point = await memory_service.decide_choice(
        choice_point_id=str(choice_point_id),
        selected_choice_id=request.selected_choice_id,
        decision_rationale=request.decision_rationale,
        rejection_reasons=request.rejection_reasons
    )
    return {"choice_point": choice_point}

@router.get("/search")
async def search_choice_points(
    user_id: str = Query(...),
    tags: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    memory_service: MemoryStoreService = Depends(get_memory_service)
):
    """選択肢を検索"""
    results = await memory_service.search_choice_points(
        user_id=user_id,
        tags=tags.split(",") if tags else None,
        from_date=datetime.fromisoformat(from_date) if from_date else None,
        to_date=datetime.fromisoformat(to_date) if to_date else None,
        search_text=search_text,
        limit=limit
    )
    return {"results": results, "count": len(results)}
```

### 3.4 Memory Lifecycle API

**実装場所**: `memory_lifecycle/`
**実装率**: 100%

**新規ルーター:**
```python
# backend/app/routers/memory_lifecycle.py（新規作成）
from fastapi import APIRouter, Depends
from memory_lifecycle.capacity_manager import CapacityManager
from memory_lifecycle.compression_service import MemoryCompressionService

router = APIRouter(prefix="/api/v1/memory/lifecycle", tags=["memory-lifecycle"])

@router.get("/status")
async def get_memory_status(
    user_id: str = Query(...),
    capacity_manager: CapacityManager = Depends(get_capacity_manager)
):
    """メモリ使用状況を取得"""
    status = await capacity_manager.get_memory_status(user_id)
    return status

@router.post("/compress")
async def compress_memories(
    user_id: str,
    compression_service: MemoryCompressionService = Depends(get_compression_service)
):
    """メモリを圧縮"""
    result = await compression_service.compress_user_memories(user_id)
    return result

@router.delete("/expired")
async def cleanup_expired_memories(
    capacity_manager: CapacityManager = Depends(get_capacity_manager)
):
    """期限切れメモリをクリーンアップ"""
    deleted_count = await capacity_manager.cleanup_expired_memories()
    return {"deleted_count": deleted_count}
```

### 3.5 Dashboard Analytics API

**実装場所**: `bridge/api/dashboard.py`
**実装率**: 100%

**新規ルーター:**
```python
# backend/app/routers/dashboard_analytics.py（新規作成）
from fastapi import APIRouter, Depends
from bridge.api.dashboard import get_system_overview, get_timeline

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard-analytics"])

@router.get("/overview")
async def system_overview():
    """システム概要を取得"""
    overview = await get_system_overview()
    return overview

@router.get("/timeline")
async def timeline(
    granularity: str = Query("hour", regex="^(minute|hour|day)$")
):
    """タイムラインを取得"""
    timeline_data = await get_timeline(granularity)
    return timeline_data

@router.get("/corrections")
async def corrections_history(
    limit: int = Query(50, ge=1, le=200)
):
    """修正履歴を取得"""
    # bridge.api.dashboardの機能を利用
    corrections = await get_corrections_history(limit)
    return {"corrections": corrections, "count": len(corrections)}
```

---

## 4. 依存性注入（DI）

### 4.1 dependencies.py拡張

**ファイル**: `backend/app/dependencies.py`

```python
from typing import AsyncGenerator
import asyncpg
from bridge.contradiction.detector import ContradictionDetector
from memory_store.service import MemoryStoreService
from memory_lifecycle.capacity_manager import CapacityManager
from memory_lifecycle.compression_service import MemoryCompressionService
from bridge.factory.bridge_factory import BridgeFactory

# PostgreSQLプール（既存）
async def get_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """データベース接続プール取得"""
    # 既存の実装
    ...

# 🆕 Contradiction Detector
async def get_contradiction_detector() -> ContradictionDetector:
    """Contradiction Detector取得"""
    pool = await get_db_pool()
    return ContradictionDetector(db_pool=pool)

# 🆕 Memory Store Service
async def get_memory_service() -> MemoryStoreService:
    """Memory Store Service取得"""
    pool = await get_db_pool()
    return MemoryStoreService(pool=pool)

# 🆕 Capacity Manager
async def get_capacity_manager() -> CapacityManager:
    """Capacity Manager取得"""
    pool = await get_db_pool()
    return CapacityManager(pool=pool)

# 🆕 Compression Service
async def get_compression_service() -> MemoryCompressionService:
    """Memory Compression Service取得"""
    pool = await get_db_pool()
    return MemoryCompressionService(pool=pool)

# 🆕 BridgeSet
async def get_bridge_set():
    """BridgeSet取得（Re-evaluation用）"""
    return BridgeFactory.create_bridge_set()
```

---

## 5. main.py修正

### 5.1 ルーター登録

**ファイル**: `backend/app/main.py`

```python
from fastapi import FastAPI
from app.routers import (
    messages,
    intents,
    specifications,
    notifications,
    websocket,
    contradictions,         # 既存（修正）
    re_evaluation,          # 🆕
    choice_points,          # 🆕
    memory_lifecycle,       # 🆕
    dashboard_analytics     # 🆕
)

app = FastAPI(title="Resonant Engine Backend API", version="2.0.0")

# 既存ルーター
app.include_router(messages.router)
app.include_router(intents.router)
app.include_router(specifications.router)
app.include_router(notifications.router)
app.include_router(websocket.router)

# 高度機能ルーター
app.include_router(contradictions.router)      # 修正版
app.include_router(re_evaluation.router)       # 🆕
app.include_router(choice_points.router)       # 🆕
app.include_router(memory_lifecycle.router)    # 🆕
app.include_router(dashboard_analytics.router) # 🆕
```

---

## 6. requirements.txt更新

### 6.1 依存関係追加

**ファイル**: `backend/requirements.txt`

```txt
# 既存の依存関係
fastapi==0.111.0
uvicorn[standard]==0.30.0
asyncpg==0.30.0
pydantic==2.7.0
...

# 🆕 独立モジュールへの参照
-e file:../bridge
-e file:../memory_store
-e file:../memory_lifecycle
-e file:../context_assembler
-e file:../retrieval
```

### 6.2 各モジュールのsetup.py作成

**例: bridge/setup.py**
```python
from setuptools import setup, find_packages

setup(
    name="resonant-bridge",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.21.0",
        "asyncpg>=0.30.0",
        "pydantic>=2.7.0",
    ]
)
```

---

## 7. Dockerfile修正

### 7.1 COPYディレクティブ追加

**ファイル**: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 🆕 独立モジュールをコピー
COPY ../bridge /app/bridge
COPY ../memory_store /app/memory_store
COPY ../memory_lifecycle /app/memory_lifecycle
COPY ../context_assembler /app/context_assembler
COPY ../retrieval /app/retrieval

# Backend APIをコピー
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. パフォーマンス

### 8.1 レイテンシ目標

| エンドポイント | 目標 |
|--------------|------|
| GET /api/v1/contradiction/pending | < 500ms |
| POST /api/v1/contradiction/check | < 2秒 |
| POST /api/v1/intent/reeval | < 3秒 |
| GET /api/v1/memory/choice-points/pending | < 500ms |
| GET /api/v1/dashboard/overview | < 1秒 |

---

## 9. エラーハンドリング

### 9.1 統一エラーレスポンス

```python
# backend/app/exceptions.py（新規）
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code

async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

# main.pyに追加
app.add_exception_handler(APIError, api_error_handler)
```

---

## 10. テスト戦略

### 10.1 統合テスト

**ファイル**: `backend/tests/integration/test_advanced_features.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_contradiction_detection_flow(client: AsyncClient):
    """矛盾検出フロー全体テスト"""
    # 1. Intentチェック
    response = await client.post("/api/v1/contradiction/check", json={
        "user_id": "test_user",
        "intent_id": "uuid-001",
        "intent_content": "PostgreSQLからSQLiteに変更"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 0

    # 2. 未解決矛盾取得
    response = await client.get("/api/v1/contradiction/pending?user_id=test_user")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_choice_preservation_flow(client: AsyncClient):
    """選択保存フロー全体テスト"""
    # 1. Choice Point作成
    response = await client.post("/api/v1/memory/choice-points/", json={
        "user_id": "test_user",
        "question": "データベース選定",
        "choices": [
            {"choice_id": "A", "choice_text": "PostgreSQL"},
            {"choice_id": "B", "choice_text": "SQLite"}
        ],
        "tags": ["technology", "database"]
    })
    assert response.status_code == 200
    choice_point_id = response.json()["choice_point"]["id"]

    # 2. 選択決定
    response = await client.put(
        f"/api/v1/memory/choice-points/{choice_point_id}/decide",
        json={
            "selected_choice_id": "A",
            "decision_rationale": "スケーラビリティ重視",
            "rejection_reasons": {
                "B": "限界がある"
            }
        }
    )
    assert response.status_code == 200
```

---

## 11. デプロイ手順

### 11.1 ローカル開発環境

```bash
# 1. 依存関係インストール
cd /Users/zero/Projects/resonant-engine/backend
pip install -e ../bridge
pip install -e ../memory_store
pip install -e ../memory_lifecycle
pip install -r requirements.txt

# 2. サーバー起動
uvicorn app.main:app --reload --port 8000
```

### 11.2 Docker環境

```bash
# 1. イメージ再ビルド
cd /Users/zero/Projects/resonant-engine/docker
docker compose build --no-cache backend

# 2. 起動
docker compose up -d

# 3. 動作確認
curl http://localhost:8000/api/v1/contradiction/pending?user_id=test
```

---

## 12. 制約と前提

### 12.1 制約
- 独立モジュールは既存実装を変更しない
- Backend APIから import して使用のみ
- 後方互換性維持（既存APIに影響なし）

### 12.2 前提
- Docker Compose環境構築済み
- PostgreSQL 15稼働中
- 独立モジュール実装完了（85-90%）

---

## 13. Frontend更新

### 13.1 仕様書修正

**ファイル**: `docs/02_components/frontend/architecture/frontend_core_features_spec.md`

**削除する記載:**
```diff
- ## 0. バックエンドAPI構成（重要）
- 
- ### 2つのバックエンドが存在する
- 
- Dashboard Backend (backend/app/)
- Bridge API (bridge/api/)
```

**追加する記載:**
```markdown
## 0. バックエンドAPI構成

### 単一のBackend APIが全機能を提供

すべての機能は Backend API (backend/app/) に統合されています。

- 基本CRUD: Messages, Intents, Specifications, Notifications
- 高度機能: Contradiction Detection, Re-evaluation, Choice Preservation等
- WebSocket: リアルタイム通知
- Dashboard Analytics: システム概要、タイムライン
```

### 13.2 APIクライアント修正

**ファイル**: `frontend/src/api/client.ts`

```typescript
// 環境変数（修正不要、既存のまま）
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 全エンドポイントが /api/ または /api/v1/ で統一
// Bridge API用の別URLは不要
```

---

## 14. 成功基準

### 14.1 統合完了の判定

✅ 全エンドポイントが200 OKを返す:
- GET /api/v1/contradiction/pending
- POST /api/v1/contradiction/check
- POST /api/v1/intent/reeval
- GET /api/v1/memory/choice-points/pending
- GET /api/v1/dashboard/overview

✅ Swagger UIで全エンドポイント確認可能

✅ 統合テスト20件以上が全合格

✅ Dockerビルド成功、コンテナ起動成功

✅ フロントエンドから実際にデータ取得可能

---

## 15. リスク管理

### 15.1 潜在的リスク

| リスク | 影響 | 軽減策 |
|-------|------|--------|
| 依存関係の循環参照 | ビルド失敗 | setup.pyで明示的に宣言 |
| Dockerイメージサイズ増大 | ビルド時間増加 | マルチステージビルド検討 |
| 既存APIへの影響 | 既存機能の破壊 | 統合テストで確認 |
| パフォーマンス劣化 | レスポンス遅延 | 各エンドポイントで計測 |

---

## 16. 参考資料

- [Contradiction Detection実装](../../bridge/contradiction/)
- [Re-evaluation API](../../bridge/api/reeval.py)
- [Memory Store実装](../../memory_store/)
- [Frontend仕様書](../frontend/architecture/frontend_core_features_spec.md)
- [実装状況分析](../../reports/implementation_status_facts_20251130.md)

---

**作成日**: 2025-11-30
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**想定作業時間**: 2-4時間
