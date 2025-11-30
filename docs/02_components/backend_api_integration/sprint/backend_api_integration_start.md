# Backend API 高度機能統合 作業開始指示書

## 概要

**Sprint**: Backend API Integration
**タイトル**: 高度機能のBackend API統合
**期間**: 2-4時間（1日以内）
**目標**: 独立モジュールをBackend APIに統合し、WebUIから利用可能にする

---

## 📋 前提条件チェックリスト

作業開始前に以下を確認してください:

- [ ] Docker環境が起動している (`docker ps` で確認)
- [ ] PostgreSQLが稼働している
- [ ] 既存のBackend APIが動作している (`curl http://localhost:8000/health`)
- [ ] 独立モジュールが存在する:
  - [ ] `bridge/contradiction/`
  - [ ] `bridge/api/reeval.py`
  - [ ] `memory_store/`
  - [ ] `memory_lifecycle/`

---

## Day 1: Backend API統合（2-4時間）

### Phase 1: setup.py作成とrequirements.txt更新（30分）

#### Step 1.1: bridgeモジュールのsetup.py作成

**ファイル**: `/Users/zero/Projects/resonant-engine/bridge/setup.py`（新規作成）

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
        "fastapi>=0.111.0",
    ],
    python_requires=">=3.11",
)
```

#### Step 1.2: memory_storeモジュールのsetup.py作成

**ファイル**: `/Users/zero/Projects/resonant-engine/memory_store/setup.py`（新規作成）

```python
from setuptools import setup, find_packages

setup(
    name="resonant-memory-store",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "asyncpg>=0.30.0",
        "pydantic>=2.7.0",
        "pgvector>=0.2.0",
    ],
    python_requires=">=3.11",
)
```

#### Step 1.3: memory_lifecycleモジュールのsetup.py作成

**ファイル**: `/Users/zero/Projects/resonant-engine/memory_lifecycle/setup.py`（新規作成）

```python
from setuptools import setup, find_packages

setup(
    name="resonant-memory-lifecycle",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "asyncpg>=0.30.0",
        "pydantic>=2.7.0",
    ],
    python_requires=">=3.11",
)
```

#### Step 1.4: backend/requirements.txt更新

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/requirements.txt`（修正）

```txt
# 既存の依存関係はそのまま
fastapi==0.111.0
uvicorn[standard]==0.30.0
asyncpg==0.30.0
pydantic==2.7.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# 🆕 独立モジュールへの参照を追加
-e file:../bridge
-e file:../memory_store
-e file:../memory_lifecycle
```

**チェックポイント**:
```bash
cd /Users/zero/Projects/resonant-engine/backend
pip install -e ../bridge
pip install -e ../memory_store
pip install -e ../memory_lifecycle
# エラーがないことを確認
```

---

### Phase 2: dependencies.py拡張（20分）

#### Step 2.1: dependencies.py修正

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/app/dependencies.py`（修正）

```python
from typing import AsyncGenerator
import asyncpg
import os
from bridge.contradiction.detector import ContradictionDetector
from memory_store.service import MemoryStoreService
from memory_lifecycle.capacity_manager import CapacityManager
from memory_lifecycle.compression_service import MemoryCompressionService
from bridge.factory.bridge_factory import BridgeFactory

# 既存のget_db_pool関数はそのまま

# 🆕 以下を追加

async def get_contradiction_detector() -> ContradictionDetector:
    """Contradiction Detector取得"""
    from app.database import get_db_pool
    pool = await get_db_pool()
    return ContradictionDetector(db_pool=pool)

async def get_memory_service() -> MemoryStoreService:
    """Memory Store Service取得"""
    from app.database import get_db_pool
    pool = await get_db_pool()
    return MemoryStoreService(pool=pool)

async def get_capacity_manager() -> CapacityManager:
    """Capacity Manager取得"""
    from app.database import get_db_pool
    pool = await get_db_pool()
    return CapacityManager(pool=pool)

async def get_compression_service() -> MemoryCompressionService:
    """Memory Compression Service取得"""
    from app.database import get_db_pool
    pool = await get_db_pool()
    return MemoryCompressionService(pool=pool)

async def get_bridge_set():
    """BridgeSet取得（Re-evaluation用）"""
    return BridgeFactory.create_bridge_set()
```

**チェックポイント**:
```bash
cd /Users/zero/Projects/resonant-engine/backend
python -c "from app.dependencies import get_contradiction_detector; print('OK')"
# "OK"が表示されることを確認
```

---

### Phase 3: contradictions.py完全実装（30分）

#### Step 3.1: プレースホルダー削除、完全実装に置き換え

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/app/routers/contradictions.py`（完全書き換え）

```python
"""Contradiction Detection API - 完全実装版"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from bridge.contradiction.detector import ContradictionDetector
from app.dependencies import get_contradiction_detector

router = APIRouter(prefix="/api/v1/contradiction", tags=["contradiction"])


# ==================== Request/Response Models ====================

class CheckContradictionRequest(BaseModel):
    """矛盾チェックリクエスト"""
    user_id: str
    intent_id: str
    intent_content: str


class ResolveContradictionRequest(BaseModel):
    """矛盾解決リクエスト"""
    resolution_action: str = Field(..., regex="^(policy_change|mistake|coexist)$")
    resolution_rationale: str = Field(..., min_length=10)
    resolved_by: str


class ContradictionResponse(BaseModel):
    """矛盾レスポンス"""
    id: str
    user_id: str
    new_intent_id: str
    new_intent_content: str
    conflicting_intent_id: Optional[str]
    conflicting_intent_content: Optional[str]
    contradiction_type: str
    confidence_score: float
    detected_at: str
    details: Dict[str, Any]
    resolution_status: str
    resolution_action: Optional[str]
    resolution_rationale: Optional[str]
    resolved_at: Optional[str]


class ContradictionListResponse(BaseModel):
    """矛盾リストレスポンス"""
    contradictions: List[ContradictionResponse]
    count: int


# ==================== Endpoints ====================

@router.get("/pending", response_model=ContradictionListResponse)
async def get_pending_contradictions(
    user_id: str = Query(..., description="User ID to get pending contradictions for"),
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """
    未解決の矛盾一覧を取得
    
    Args:
        user_id: ユーザーID
        detector: Contradiction Detector（DI）
    
    Returns:
        ContradictionListResponse: 未解決矛盾のリスト
    """
    try:
        contradictions = await detector.get_pending_contradictions(user_id)
        
        return ContradictionListResponse(
            contradictions=[
                ContradictionResponse(**c.dict()) for c in contradictions
            ],
            count=len(contradictions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending contradictions: {str(e)}")


@router.post("/check", response_model=ContradictionListResponse)
async def check_intent_for_contradictions(
    request: CheckContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """
    Intentの矛盾をチェック
    
    Args:
        request: チェックリクエスト
        detector: Contradiction Detector（DI）
    
    Returns:
        ContradictionListResponse: 検出された矛盾のリスト
    """
    try:
        contradictions = await detector.check_intent(
            user_id=request.user_id,
            intent_id=request.intent_id,
            intent_content=request.intent_content
        )
        
        return ContradictionListResponse(
            contradictions=[
                ContradictionResponse(**c.dict()) for c in contradictions
            ],
            count=len(contradictions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check contradictions: {str(e)}")


@router.put("/{contradiction_id}/resolve")
async def resolve_contradiction(
    contradiction_id: UUID,
    request: ResolveContradictionRequest,
    detector: ContradictionDetector = Depends(get_contradiction_detector)
):
    """
    矛盾を解決
    
    Args:
        contradiction_id: 矛盾ID
        request: 解決リクエスト
        detector: Contradiction Detector（DI）
    
    Returns:
        解決結果
    """
    try:
        result = await detector.resolve_contradiction(
            contradiction_id=contradiction_id,
            resolution_action=request.resolution_action,
            resolution_rationale=request.resolution_rationale,
            resolved_by=request.resolved_by
        )
        
        return {
            "status": "resolved",
            "contradiction_id": str(contradiction_id),
            "resolution_action": request.resolution_action
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve contradiction: {str(e)}")
```

**チェックポイント**:
```bash
# 構文エラーチェック
python -m py_compile /Users/zero/Projects/resonant-engine/backend/app/routers/contradictions.py
# エラーがないことを確認
```

---

### Phase 4: 新規ルーター作成（1時間）

#### Step 4.1: re_evaluation.py作成

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/app/routers/re_evaluation.py`（新規作成）

```python
"""Re-evaluation API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID

from app.dependencies import get_bridge_set

router = APIRouter(prefix="/api/v1/intent", tags=["re-evaluation"])


class ReEvalRequest(BaseModel):
    """再評価リクエスト"""
    intent_id: UUID
    diff: Dict[str, Any]
    source: str
    reason: str


@router.post("/reeval")
async def re_evaluate_intent(
    request: ReEvalRequest,
    bridge_set = Depends(get_bridge_set)
):
    """
    Intent再評価
    
    Args:
        request: 再評価リクエスト
        bridge_set: BridgeSet（DI）
    
    Returns:
        再評価結果
    """
    try:
        result = await bridge_set.feedback.evaluate_intent(
            intent_id=str(request.intent_id),
            diff=request.diff,
            source=request.source,
            reason=request.reason
        )
        
        return {
            "intent_id": str(request.intent_id),
            "status": "re-evaluated",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to re-evaluate intent: {str(e)}")
```

#### Step 4.2: choice_points.py作成

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/app/routers/choice_points.py`（新規作成）

```python
"""Choice Preservation API"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from memory_store.service import MemoryStoreService
from app.dependencies import get_memory_service

router = APIRouter(prefix="/api/v1/memory/choice-points", tags=["choice-preservation"])


# ==================== Request/Response Models ====================

class ChoiceRequest(BaseModel):
    """選択肢リクエスト"""
    choice_id: str
    choice_text: str


class CreateChoicePointRequest(BaseModel):
    """Choice Point作成リクエスト"""
    user_id: str
    question: str
    choices: List[ChoiceRequest]
    tags: List[str] = Field(default_factory=list)
    context_type: str = "general"


class DecideChoiceRequest(BaseModel):
    """選択決定リクエスト"""
    selected_choice_id: str
    decision_rationale: str
    rejection_reasons: Dict[str, str] = Field(default_factory=dict)


# ==================== Endpoints ====================

@router.get("/pending")
async def get_pending_choice_points(
    user_id: str = Query(...),
    memory_service: MemoryStoreService = Depends(get_memory_service)
):
    """未決定の選択肢を取得"""
    try:
        pending = await memory_service.get_pending_choice_points(user_id)
        return {"choice_points": pending, "count": len(pending)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending choice points: {str(e)}")


@router.post("/")
async def create_choice_point(
    request: CreateChoicePointRequest,
    memory_service: MemoryStoreService = Depends(get_memory_service)
):
    """新しい選択肢を作成"""
    try:
        choice_point = await memory_service.create_choice_point(
            user_id=request.user_id,
            question=request.question,
            choices=[c.dict() for c in request.choices],
            tags=request.tags,
            context_type=request.context_type
        )
        return {"choice_point": choice_point}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create choice point: {str(e)}")


@router.put("/{choice_point_id}/decide")
async def decide_choice(
    choice_point_id: UUID,
    request: DecideChoiceRequest,
    memory_service: MemoryStoreService = Depends(get_memory_service)
):
    """選択を決定"""
    try:
        choice_point = await memory_service.decide_choice(
            choice_point_id=str(choice_point_id),
            selected_choice_id=request.selected_choice_id,
            decision_rationale=request.decision_rationale,
            rejection_reasons=request.rejection_reasons
        )
        return {"choice_point": choice_point}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decide choice: {str(e)}")


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
    try:
        results = await memory_service.search_choice_points(
            user_id=user_id,
            tags=tags.split(",") if tags else None,
            from_date=datetime.fromisoformat(from_date) if from_date else None,
            to_date=datetime.fromisoformat(to_date) if to_date else None,
            search_text=search_text,
            limit=limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search choice points: {str(e)}")
```

#### Step 4.3: memory_lifecycle.py作成

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/app/routers/memory_lifecycle.py`（新規作成）

```python
"""Memory Lifecycle API"""

from fastapi import APIRouter, Depends, Query, HTTPException

from memory_lifecycle.capacity_manager import CapacityManager
from memory_lifecycle.compression_service import MemoryCompressionService
from app.dependencies import get_capacity_manager, get_compression_service

router = APIRouter(prefix="/api/v1/memory/lifecycle", tags=["memory-lifecycle"])


@router.get("/status")
async def get_memory_status(
    user_id: str = Query(...),
    capacity_manager: CapacityManager = Depends(get_capacity_manager)
):
    """メモリ使用状況を取得"""
    try:
        status = await capacity_manager.get_memory_status(user_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory status: {str(e)}")


@router.post("/compress")
async def compress_memories(
    user_id: str = Query(...),
    compression_service: MemoryCompressionService = Depends(get_compression_service)
):
    """メモリを圧縮"""
    try:
        result = await compression_service.compress_user_memories(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compress memories: {str(e)}")


@router.delete("/expired")
async def cleanup_expired_memories(
    capacity_manager: CapacityManager = Depends(get_capacity_manager)
):
    """期限切れメモリをクリーンアップ"""
    try:
        deleted_count = await capacity_manager.cleanup_expired_memories()
        return {"deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired memories: {str(e)}")
```

#### Step 4.4: dashboard_analytics.py作成

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/app/routers/dashboard_analytics.py`（新規作成）

```python
"""Dashboard Analytics API"""

from fastapi import APIRouter, Query, HTTPException

# bridge.api.dashboardの機能を利用
from bridge.api.dashboard import (
    get_system_overview,
    get_timeline,
    get_corrections_history
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard-analytics"])


@router.get("/overview")
async def system_overview():
    """システム概要を取得"""
    try:
        overview = await get_system_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system overview: {str(e)}")


@router.get("/timeline")
async def timeline(
    granularity: str = Query("hour", regex="^(minute|hour|day)$")
):
    """タイムラインを取得"""
    try:
        timeline_data = await get_timeline(granularity)
        return timeline_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@router.get("/corrections")
async def corrections_history(
    limit: int = Query(50, ge=1, le=200)
):
    """修正履歴を取得"""
    try:
        corrections = await get_corrections_history(limit)
        return {"corrections": corrections, "count": len(corrections)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get corrections history: {str(e)}")
```

---

### Phase 5: main.py修正（10分）

#### Step 5.1: ルーター登録

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/app/main.py`（修正）

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 既存のimport
from app.routers import (
    messages,
    intents,
    specifications,
    notifications,
    websocket,
)

# 🆕 新規import
from app.routers import (
    contradictions,        # 修正版
    re_evaluation,         # 新規
    choice_points,         # 新規
    memory_lifecycle,      # 新規
    dashboard_analytics    # 新規
)

app = FastAPI(
    title="Resonant Engine Backend API",
    version="2.0.0",
    description="統合Backend API - 全機能を提供"
)

# CORS（既存のまま）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 既存ルーター
app.include_router(messages.router)
app.include_router(intents.router)
app.include_router(specifications.router)
app.include_router(notifications.router)
app.include_router(websocket.router)

# 🆕 高度機能ルーター
app.include_router(contradictions.router)
app.include_router(re_evaluation.router)
app.include_router(choice_points.router)
app.include_router(memory_lifecycle.router)
app.include_router(dashboard_analytics.router)

# Health check（既存のまま）
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

### Phase 6: Docker対応（30分）

#### Step 6.1: Dockerfile修正

**ファイル**: `/Users/zero/Projects/resonant-engine/backend/Dockerfile`（修正）

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 🆕 独立モジュールをコピー
COPY bridge /app/bridge
COPY memory_store /app/memory_store
COPY memory_lifecycle /app/memory_lifecycle
COPY context_assembler /app/context_assembler
COPY retrieval /app/retrieval

# Backend APIをコピー
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app /app/app

# ポート公開
EXPOSE 8000

# サーバー起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 6.2: docker-compose.ymlでビルドコンテキスト確認

**ファイル**: `/Users/zero/Projects/resonant-engine/docker/docker-compose.yml`（確認のみ）

```yaml
backend:
  build:
    context: ..  # ← プロジェクトルートを指定（重要）
    dockerfile: backend/Dockerfile
```

#### Step 6.3: Dockerビルド

```bash
cd /Users/zero/Projects/resonant-engine/docker
docker compose build --no-cache backend
```

**チェックポイント**:
- ビルドが成功することを確認
- エラーが出た場合はログを確認

---

### Phase 7: 動作確認（30分）

#### Step 7.1: Docker起動

```bash
cd /Users/zero/Projects/resonant-engine/docker
docker compose up -d
```

#### Step 7.2: エンドポイント確認

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. Contradiction Detection
curl 'http://localhost:8000/api/v1/contradiction/pending?user_id=test'

# 3. Choice Points
curl 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test'

# 4. Memory Lifecycle
curl 'http://localhost:8000/api/v1/memory/lifecycle/status?user_id=test'

# 5. Dashboard Analytics
curl http://localhost:8000/api/v1/dashboard/overview

# 6. Swagger UI確認
# ブラウザで http://localhost:8000/docs を開く
```

**期待される結果**:
- 全エンドポイントが200 OKを返す
- Swagger UIで全エンドポイントが表示される

---

## トラブルシューティング

### 問題1: import エラー

**症状**:
```
ModuleNotFoundError: No module named 'bridge'
```

**解決策**:
```bash
cd /Users/zero/Projects/resonant-engine/backend
pip install -e ../bridge
pip install -e ../memory_store
pip install -e ../memory_lifecycle
```

### 問題2: Dockerビルドエラー

**症状**:
```
COPY failed: file not found in build context
```

**解決策**:
- `docker-compose.yml`の`context: ..`を確認
- プロジェクトルートからビルドしているか確認

### 問題3: 404 Not Found

**症状**:
```
curl http://localhost:8000/api/v1/contradiction/pending?user_id=test
404 Not Found
```

**解決策**:
```bash
# ルーター登録を確認
docker exec resonant_backend python -c "from app.main import app; print(app.routes)"

# ログ確認
docker logs resonant_backend
```

---

## 完了基準

### ✅ 統合完了の判定

以下すべてが満たされること:

- [ ] 全setup.pyが作成されている
- [ ] requirements.txtが更新されている
- [ ] dependencies.pyが拡張されている
- [ ] contradictions.pyがプレースホルダーから完全実装に置き換わっている
- [ ] 4つの新規ルーターが作成されている
- [ ] main.pyにルーターが登録されている
- [ ] Dockerfileが修正されている
- [ ] Dockerビルドが成功する
- [ ] 全エンドポイントが200 OKを返す
- [ ] Swagger UIで全エンドポイントが確認できる

---

## 次のステップ

統合完了後:

1. **テスト作成**: 統合テストを作成（別タスク）
2. **Frontend更新**: 仕様書修正、APIクライアント確認
3. **動作確認**: WebUIから実際にデータ取得

---

**作成日**: 2025-11-30
**作成者**: Kana (Claude Sonnet 4.5)
**想定作業時間**: 2-4時間
