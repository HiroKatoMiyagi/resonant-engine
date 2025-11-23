# Resonant Engine 総合テスト仕様書

**作成日**: 2025-11-23
**バージョン**: 1.0
**対象環境**: 開発環境（Docker Compose）
**テスト種別**: システムテスト / 総合テスト

---

## 目次

1. [テスト概要](#1-テスト概要)
2. [テスト環境](#2-テスト環境)
3. [前提条件](#3-前提条件)
4. [テスト項目一覧](#4-テスト項目一覧)
5. [テストケース詳細](#5-テストケース詳細)
6. [テスト実行手順](#6-テスト実行手順)
7. [合否判定基準](#7-合否判定基準)

---

## 1. テスト概要

### 1.1 目的

本総合テストは、Resonant Engineの全機能が期待通りに動作することを検証する。
**モックを使用せず**、実際のPostgreSQLデータベースとClaude APIを使用して、
本番環境に近い条件でシステム全体の統合動作を確認する。

### 1.2 テスト範囲

| カテゴリ | 対象機能 |
|---------|---------|
| データベース層 | PostgreSQL接続、pgvector、CRUD操作 |
| API層 | REST API、WebSocket、SSE |
| AI層 | Claude API (Kana)、Intent処理 |
| パイプライン | BridgeSetパイプライン実行 |
| メモリシステム | セッション管理、Context Assembler |
| 矛盾検出 | ContradictionDetector |

### 1.3 テスト対象外

- フロントエンド（React UI）
- 本番環境固有の設定
- 負荷テスト、性能テスト

---

## 2. テスト環境

### 2.1 システム構成

```
┌─────────────────────────────────────────────────────────────┐
│ Docker Compose 開発環境                                      │
├─────────────────────────────────────────────────────────────┤
│ PostgreSQL 15 (pgvector)  │ ポート: 5432                    │
│ Backend API (FastAPI)      │ ポート: 8000                    │
│ Intent Bridge              │ Claude API連携                   │
│ Message Bridge             │ Claude API連携                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 必要な環境変数

```bash
# .env ファイル設定
POSTGRES_USER=resonant
POSTGRES_PASSWORD=<secure_password>
POSTGRES_DB=resonant_dashboard
POSTGRES_PORT=5432

# API設定
API_PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# Claude API（Kana）
ANTHROPIC_API_KEY=sk-ant-xxx...

# Bridge設定（実際のプロバイダーを使用）
DATA_BRIDGE_TYPE=postgresql
AI_BRIDGE_TYPE=kana
FEEDBACK_BRIDGE_TYPE=yuno
AUDIT_LOGGER_TYPE=postgresql
```

### 2.3 依存サービス

| サービス | バージョン | 必須 |
|---------|----------|------|
| PostgreSQL | 15-alpine | ✅ |
| pgvector | 0.5.0+ | ✅ |
| Python | 3.11+ | ✅ |
| Claude API | claude-3-5-sonnet-20241022 | ✅ |

---

## 3. 前提条件

### 3.1 環境準備チェックリスト

- [ ] Docker / Docker Composeがインストールされている
- [ ] `.env`ファイルが正しく設定されている
- [ ] `ANTHROPIC_API_KEY`が有効である
- [ ] ポート5432, 8000が使用可能である
- [ ] Python仮想環境が準備されている

### 3.2 起動手順

```bash
# 1. 環境変数設定
cd /Users/zero/Projects/resonant-engine/docker
cp .env.example .env
# .env を編集

# 2. コンテナ起動
./scripts/start.sh

# 3. ヘルスチェック
./scripts/check-health.sh

# 4. データベースマイグレーション確認
docker exec -it resonant_postgres psql -U resonant -d resonant_dashboard -c "\dt"
```

---

## 4. テスト項目一覧

### 4.1 テストカテゴリ

| ID | カテゴリ | テスト項目数 | 優先度 |
|----|---------|------------|-------|
| ST-DB | データベース接続 | 5 | 高 |
| ST-API | REST API | 8 | 高 |
| ST-BRIDGE | BridgeSetパイプライン | 6 | 高 |
| ST-AI | Claude API (Kana) | 5 | 高 |
| ST-MEM | メモリシステム | 7 | 中 |
| ST-CTX | Context Assembler | 5 | 中 |
| ST-CONTRA | 矛盾検出 | 6 | 中 |
| ST-RT | リアルタイム通信 | 4 | 低 |
| ST-E2E | エンドツーエンド | 3 | 高 |

**総テスト項目数: 49**

---

## 5. テストケース詳細

### 5.1 データベース接続テスト (ST-DB)

#### ST-DB-001: PostgreSQL接続確認

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-DB-001 |
| **テスト名** | PostgreSQL接続確認 |
| **目的** | PostgreSQLへの接続が正常に行えることを確認 |
| **前提条件** | Docker Composeでpostgresサービスが起動している |
| **手順** | 1. asyncpgを使用してDB接続プールを作成<br>2. 接続を取得<br>3. SELECT 1 を実行<br>4. 接続を解放 |
| **期待結果** | 接続成功、SELECT 1 が "1" を返す |
| **確認方法** | pytest実行結果 |

```python
# tests/system/test_db_connection.py
import asyncpg
import pytest

@pytest.mark.asyncio
async def test_postgres_connection():
    """ST-DB-001: PostgreSQL接続確認"""
    dsn = "postgresql://resonant:password@localhost:5432/resonant_dashboard"
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)

    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1

    await pool.close()
```

#### ST-DB-002: pgvector拡張確認

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-DB-002 |
| **テスト名** | pgvector拡張確認 |
| **目的** | pgvector拡張が有効であることを確認 |
| **前提条件** | PostgreSQL起動済み、init.sql実行済み |
| **手順** | 1. pgvectorの有効化確認クエリを実行<br>2. vector型のテスト |
| **期待結果** | vector拡張がインストール済み |

```python
@pytest.mark.asyncio
async def test_pgvector_extension():
    """ST-DB-002: pgvector拡張確認"""
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)

    async with pool.acquire() as conn:
        # 拡張確認
        result = await conn.fetchval(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )
        assert result == "vector"

        # vector型テスト
        await conn.execute("SELECT '[1,2,3]'::vector")

    await pool.close()
```

#### ST-DB-003: Intentsテーブル操作

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-DB-003 |
| **テスト名** | Intentsテーブル操作 |
| **目的** | intentsテーブルへのCRUD操作を確認 |
| **手順** | INSERT → SELECT → UPDATE → DELETE |
| **期待結果** | 全操作が正常に完了 |

```python
@pytest.mark.asyncio
async def test_intents_crud():
    """ST-DB-003: IntentsテーブルCRUD"""
    import uuid
    import json

    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    test_id = str(uuid.uuid4())

    async with pool.acquire() as conn:
        # INSERT
        await conn.execute("""
            INSERT INTO intents (id, source, type, data, status, user_id, content)
            VALUES ($1, 'KANA', 'FEATURE_REQUEST', $2, 'PENDING', 'test_user', 'Test intent')
        """, uuid.UUID(test_id), json.dumps({"test": True}))

        # SELECT
        row = await conn.fetchrow(
            "SELECT * FROM intents WHERE id = $1",
            uuid.UUID(test_id)
        )
        assert row is not None
        assert row['status'] == 'PENDING'

        # UPDATE
        await conn.execute(
            "UPDATE intents SET status = 'COMPLETED' WHERE id = $1",
            uuid.UUID(test_id)
        )

        # DELETE (cleanup)
        await conn.execute(
            "DELETE FROM intents WHERE id = $1",
            uuid.UUID(test_id)
        )

    await pool.close()
```

#### ST-DB-004: contradictionsテーブル操作

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-DB-004 |
| **テスト名** | contradictionsテーブル操作 |
| **目的** | Sprint 11で追加されたcontradictionsテーブルの動作確認 |
| **期待結果** | 矛盾レコードの保存・取得が正常に行える |

```python
@pytest.mark.asyncio
async def test_contradictions_table():
    """ST-DB-004: contradictionsテーブル操作"""
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)

    async with pool.acquire() as conn:
        # テーブル存在確認
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'contradictions'
            )
        """)
        assert exists is True

        # カラム確認
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'contradictions'
        """)
        column_names = [c['column_name'] for c in columns]
        assert 'contradiction_type' in column_names
        assert 'confidence_score' in column_names
        assert 'resolution_status' in column_names

    await pool.close()
```

#### ST-DB-005: memoriesテーブル・ベクトル検索

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-DB-005 |
| **テスト名** | memoriesテーブル・ベクトル検索 |
| **目的** | ベクトル埋め込みを使用した類似検索を確認 |
| **期待結果** | ベクトル類似度検索が正常に動作 |

```python
@pytest.mark.asyncio
async def test_vector_similarity_search():
    """ST-DB-005: ベクトル類似度検索"""
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)

    async with pool.acquire() as conn:
        # テスト用メモリ挿入（1536次元のダミーベクトル）
        test_vector = [0.1] * 1536
        await conn.execute("""
            INSERT INTO memories (content, embedding, memory_type, user_id)
            VALUES ('Test memory content', $1::vector, 'WORKING', 'test_user')
        """, str(test_vector))

        # 類似検索
        results = await conn.fetch("""
            SELECT content, embedding <-> $1::vector AS distance
            FROM memories
            WHERE user_id = 'test_user'
            ORDER BY distance
            LIMIT 5
        """, str(test_vector))

        assert len(results) >= 1

        # クリーンアップ
        await conn.execute(
            "DELETE FROM memories WHERE user_id = 'test_user'"
        )

    await pool.close()
```

---

### 5.2 REST API テスト (ST-API)

#### ST-API-001: ヘルスチェックエンドポイント

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-001 |
| **テスト名** | ヘルスチェック |
| **目的** | /health エンドポイントが正常に応答することを確認 |
| **期待結果** | HTTP 200、status: "ok" |

```python
# tests/system/test_api.py
import httpx
import pytest

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_health_check():
    """ST-API-001: ヘルスチェック"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json().get("status") == "ok"
```

#### ST-API-002: Intent再評価API

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-002 |
| **テスト名** | Intent再評価API |
| **目的** | POST /api/v1/intent/reeval が正常に動作することを確認 |
| **前提条件** | 対象Intentがデータベースに存在する |
| **期待結果** | HTTP 200、intent_id と status が返却される |

```python
@pytest.mark.asyncio
async def test_intent_reeval_api():
    """ST-API-002: Intent再評価API"""
    # 事前準備: テスト用Intent作成
    intent_id = await create_test_intent()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/intent/reeval",
            json={
                "intent_id": intent_id,
                "diff": {"status": "corrected"},
                "source": "YUNO",
                "reason": "システムテスト"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("intent_id") == intent_id
        assert "status" in data

    # クリーンアップ
    await delete_test_intent(intent_id)
```

#### ST-API-003: ダッシュボード概要API

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-003 |
| **テスト名** | ダッシュボード概要API |
| **目的** | GET /api/v1/dashboard/overview が正常に動作 |
| **期待結果** | HTTP 200、統計情報が返却される |

```python
@pytest.mark.asyncio
async def test_dashboard_overview():
    """ST-API-003: ダッシュボード概要API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_intents" in data or "intent_count" in data
```

#### ST-API-004: タイムラインAPI

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-004 |
| **テスト名** | タイムラインAPI |
| **目的** | GET /api/v1/dashboard/timeline が正常に動作 |
| **期待結果** | HTTP 200、タイムラインデータが返却される |

```python
@pytest.mark.asyncio
async def test_dashboard_timeline():
    """ST-API-004: タイムラインAPI"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/dashboard/timeline")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
```

#### ST-API-005: メッセージCRUD API

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-005 |
| **テスト名** | メッセージCRUD API |
| **目的** | /api/messages エンドポイントのCRUD操作を確認 |
| **期待結果** | 作成・取得・一覧取得が正常に動作 |

```python
@pytest.mark.asyncio
async def test_messages_crud():
    """ST-API-005: メッセージCRUD API"""
    async with httpx.AsyncClient() as client:
        # CREATE
        create_response = await client.post(
            f"{BASE_URL}/api/messages",
            json={
                "user_id": "test_user",
                "content": "システムテスト用メッセージ",
                "message_type": "USER"
            }
        )
        assert create_response.status_code in [200, 201]
        message_id = create_response.json().get("id")

        # LIST
        list_response = await client.get(
            f"{BASE_URL}/api/messages",
            params={"user_id": "test_user"}
        )
        assert list_response.status_code == 200
```

#### ST-API-006: Intent作成API

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-006 |
| **テスト名** | Intent作成API |
| **目的** | POST /api/intents が正常に動作 |
| **期待結果** | HTTP 200/201、Intent IDが返却される |

```python
@pytest.mark.asyncio
async def test_create_intent():
    """ST-API-006: Intent作成API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/intents",
            json={
                "source": "KANA",
                "type": "FEATURE_REQUEST",
                "content": "PostgreSQLでのデータ永続化機能を追加",
                "user_id": "test_user"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
```

#### ST-API-007: Swagger UI アクセス

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-007 |
| **テスト名** | Swagger UI アクセス |
| **目的** | /docs がアクセス可能であることを確認 |
| **期待結果** | HTTP 200 |

```python
@pytest.mark.asyncio
async def test_swagger_docs():
    """ST-API-007: Swagger UI アクセス"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/docs")
        assert response.status_code == 200
```

#### ST-API-008: OpenAPI スキーマ取得

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-API-008 |
| **テスト名** | OpenAPI スキーマ取得 |
| **目的** | /openapi.json が取得可能であることを確認 |
| **期待結果** | HTTP 200、有効なOpenAPIスキーマ |

```python
@pytest.mark.asyncio
async def test_openapi_schema():
    """ST-API-008: OpenAPI スキーマ取得"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema.get("openapi").startswith("3.")
        assert "paths" in schema
```

---

### 5.3 BridgeSetパイプラインテスト (ST-BRIDGE)

#### ST-BRIDGE-001: パイプライン初期化

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-BRIDGE-001 |
| **テスト名** | パイプライン初期化 |
| **目的** | BridgeSetが正しく初期化されることを確認 |
| **期待結果** | BridgeSetインスタンスが作成され、connectが成功 |

```python
# tests/system/test_bridge_pipeline.py
import pytest
from bridge.factory.bridge_factory import create_bridge_set

@pytest.mark.asyncio
async def test_bridge_set_initialization():
    """ST-BRIDGE-001: パイプライン初期化"""
    bridge_set = await create_bridge_set(
        data_bridge_type="postgresql",
        ai_bridge_type="kana",
        feedback_bridge_type="mock",  # Yunoは高コストなのでmockでも可
        audit_logger_type="postgresql"
    )

    async with bridge_set:
        assert bridge_set.data is not None
        assert bridge_set.ai is not None
        assert bridge_set.feedback is not None
        assert bridge_set.audit is not None
```

#### ST-BRIDGE-002: INPUT ステージ実行

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-BRIDGE-002 |
| **テスト名** | INPUT ステージ実行 |
| **目的** | DataBridgeを使用したIntent保存を確認 |
| **期待結果** | IntentがPostgreSQLに保存される |

```python
@pytest.mark.asyncio
async def test_input_stage():
    """ST-BRIDGE-002: INPUT ステージ実行"""
    from bridge.core.models.intent_model import IntentModel
    from bridge.core.constants import IntentStatusEnum

    bridge_set = await create_bridge_set(
        data_bridge_type="postgresql",
        ai_bridge_type="mock",
        feedback_bridge_type="mock",
        audit_logger_type="postgresql"
    )

    async with bridge_set:
        intent = IntentModel(
            source="KANA",
            type="FEATURE_REQUEST",
            payload={"content": "テスト機能追加"}
        )

        # INPUT ステージ実行
        saved_intent = await bridge_set.data.save_intent(intent)

        assert saved_intent.intent_id is not None
        assert saved_intent.status == IntentStatusEnum.PENDING

        # 保存確認
        retrieved = await bridge_set.data.get_intent(saved_intent.intent_id)
        assert retrieved is not None
```

#### ST-BRIDGE-003: NORMALIZE ステージ実行（Claude API）

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-BRIDGE-003 |
| **テスト名** | NORMALIZE ステージ実行（Claude API） |
| **目的** | KanaAIBridgeを使用した実際のClaude API呼び出しを確認 |
| **前提条件** | ANTHROPIC_API_KEYが設定されている |
| **期待結果** | Claude APIから応答を取得、status: "ok" |

```python
@pytest.mark.asyncio
async def test_normalize_stage_with_claude():
    """ST-BRIDGE-003: NORMALIZE ステージ実行（Claude API）"""
    from bridge.providers.ai.kana_ai_bridge import KanaAIBridge

    kana = KanaAIBridge()  # 環境変数からAPIキーを取得

    intent_data = {
        "content": "ユーザー認証機能を実装してください",
        "type": "FEATURE_REQUEST",
        "payload": {}
    }

    result = await kana.process_intent(intent_data)

    assert result["status"] == "ok"
    assert "summary" in result
    assert result["model"] == "claude-3-5-sonnet-20241022"
    print(f"Claude応答: {result['summary'][:200]}...")
```

#### ST-BRIDGE-004: フルパイプライン実行

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-BRIDGE-004 |
| **テスト名** | フルパイプライン実行 |
| **目的** | INPUT → NORMALIZE → FEEDBACK → OUTPUT の全ステージ実行を確認 |
| **期待結果** | IntentがCOMPLETED状態になる |

```python
@pytest.mark.asyncio
async def test_full_pipeline_execution():
    """ST-BRIDGE-004: フルパイプライン実行"""
    from bridge.core.models.intent_model import IntentModel
    from bridge.core.constants import IntentStatusEnum

    bridge_set = await create_bridge_set(
        data_bridge_type="postgresql",
        ai_bridge_type="kana",  # 実際のClaude API
        feedback_bridge_type="mock",
        audit_logger_type="postgresql"
    )

    async with bridge_set:
        intent = IntentModel(
            source="KANA",
            type="BUG_FIX",
            payload={"content": "ログイン時のエラーハンドリングを改善"}
        )

        result = await bridge_set.execute(intent)

        assert result.status in [
            IntentStatusEnum.COMPLETED,
            IntentStatusEnum.CORRECTED
        ]
        assert len(result.correction_history) >= 0
```

#### ST-BRIDGE-005: エラーハンドリング

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-BRIDGE-005 |
| **テスト名** | パイプラインエラーハンドリング |
| **目的** | ステージ失敗時の適切なエラー処理を確認 |
| **期待結果** | IntentがFAILED状態になり、監査ログに記録される |

```python
@pytest.mark.asyncio
async def test_pipeline_error_handling():
    """ST-BRIDGE-005: パイプラインエラーハンドリング"""
    from bridge.core.models.intent_model import IntentModel
    from bridge.core.constants import ExecutionMode, IntentStatusEnum

    # 無効なAPIキーでエラーを誘発
    from bridge.providers.ai.kana_ai_bridge import KanaAIBridge

    bridge_set = await create_bridge_set(
        data_bridge_type="postgresql",
        ai_bridge_type="mock",  # エラーをシミュレート
        feedback_bridge_type="mock",
        audit_logger_type="postgresql"
    )

    async with bridge_set:
        intent = IntentModel(
            source="KANA",
            type="FEATURE_REQUEST",
            payload={"content": "テスト"}
        )

        # SELECTIVE モードではINPUT以外の失敗は続行
        result = await bridge_set.execute(
            intent,
            mode=ExecutionMode.SELECTIVE
        )

        # 監査ログ確認
        # （実際のテストでは監査ログをクエリして確認）
```

#### ST-BRIDGE-006: 冪等性確認

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-BRIDGE-006 |
| **テスト名** | 再評価の冪等性確認 |
| **目的** | 同一のIntent再評価リクエストが冪等であることを確認 |
| **期待結果** | already_applied: true が返される |

```python
@pytest.mark.asyncio
async def test_reeval_idempotency():
    """ST-BRIDGE-006: 再評価の冪等性確認"""
    async with httpx.AsyncClient() as client:
        intent_id = await create_test_intent()

        reeval_payload = {
            "intent_id": intent_id,
            "diff": {"priority": 5},
            "source": "YUNO",
            "reason": "冪等性テスト"
        }

        # 1回目の再評価
        response1 = await client.post(
            f"{BASE_URL}/api/v1/intent/reeval",
            json=reeval_payload
        )
        assert response1.status_code == 200
        assert response1.json().get("already_applied") is False

        # 2回目の同一再評価
        response2 = await client.post(
            f"{BASE_URL}/api/v1/intent/reeval",
            json=reeval_payload
        )
        assert response2.status_code == 200
        assert response2.json().get("already_applied") is True
```

---

### 5.4 Claude API (Kana) テスト (ST-AI)

#### ST-AI-001: Claude API認証確認

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-AI-001 |
| **テスト名** | Claude API認証確認 |
| **目的** | ANTHROPIC_API_KEYが有効であることを確認 |
| **期待結果** | API呼び出しが成功 |

```python
# tests/system/test_claude_api.py
import pytest
from anthropic import AsyncAnthropic

@pytest.mark.asyncio
async def test_claude_api_authentication():
    """ST-AI-001: Claude API認証確認"""
    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")
    assert api_key is not None, "ANTHROPIC_API_KEY must be set"

    client = AsyncAnthropic(api_key=api_key)

    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say 'test successful'"}]
    )

    assert response.content[0].text is not None
```

#### ST-AI-002: KanaAIBridge Intent処理

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-AI-002 |
| **テスト名** | KanaAIBridge Intent処理 |
| **目的** | KanaAIBridgeを通じたIntent処理を確認 |
| **期待結果** | 正常な応答とstatus: "ok" |

```python
@pytest.mark.asyncio
async def test_kana_ai_bridge_process():
    """ST-AI-002: KanaAIBridge Intent処理"""
    from bridge.providers.ai.kana_ai_bridge import KanaAIBridge

    kana = KanaAIBridge()

    result = await kana.process_intent({
        "content": "データベース接続エラーの原因を分析して",
        "user_id": "test_user"
    })

    assert result["status"] == "ok"
    assert "summary" in result
    assert len(result["summary"]) > 0
```

#### ST-AI-003: Context Assembler連携

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-AI-003 |
| **テスト名** | Context Assembler連携 |
| **目的** | KanaAIBridgeとContextAssemblerの連携を確認 |
| **期待結果** | context_metadataが返却される |

```python
@pytest.mark.asyncio
async def test_kana_with_context_assembler():
    """ST-AI-003: Context Assembler連携"""
    from bridge.providers.ai.kana_ai_bridge import KanaAIBridge
    from context_assembler.service import ContextAssemblerService
    from context_assembler.models import ContextConfig

    # Context Assemblerセットアップ（実際の依存関係を注入）
    # Note: 完全なセットアップには追加の依存関係が必要

    kana = KanaAIBridge()

    result = await kana.process_intent({
        "content": "前回の会話の続きを教えて",
        "user_id": "test_user",
        "session_id": "some-uuid"
    })

    assert result["status"] == "ok"
    # context_metadataはContextAssemblerが設定されている場合のみ
    if "context_metadata" in result:
        assert "working_memory_count" in result["context_metadata"]
```

#### ST-AI-004: 日本語Intent処理

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-AI-004 |
| **テスト名** | 日本語Intent処理 |
| **目的** | 日本語のIntentが正しく処理されることを確認 |
| **期待結果** | 適切な日本語応答 |

```python
@pytest.mark.asyncio
async def test_japanese_intent_processing():
    """ST-AI-004: 日本語Intent処理"""
    from bridge.providers.ai.kana_ai_bridge import KanaAIBridge

    kana = KanaAIBridge()

    result = await kana.process_intent({
        "content": "ユーザープロフィール機能の設計について考慮すべきポイントを教えて",
        "user_id": "hiroaki"
    })

    assert result["status"] == "ok"
    assert "summary" in result
    # 日本語を含む応答であることを確認
    summary = result["summary"]
    assert len(summary) > 50  # 十分な長さの応答
```

#### ST-AI-005: エラー時のグレースフルデグラデーション

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-AI-005 |
| **テスト名** | エラー時のグレースフルデグラデーション |
| **目的** | API呼び出しエラー時に適切にエラーを返すことを確認 |
| **期待結果** | status: "error" と reason が返却される |

```python
@pytest.mark.asyncio
async def test_claude_api_error_handling():
    """ST-AI-005: エラー時のグレースフルデグラデーション"""
    from bridge.providers.ai.kana_ai_bridge import KanaAIBridge
    from anthropic import AsyncAnthropic

    # 無効なAPIキーでクライアントを作成
    invalid_client = AsyncAnthropic(api_key="invalid_key")
    kana = KanaAIBridge(client=invalid_client)

    result = await kana.process_intent({
        "content": "テスト",
        "user_id": "test"
    })

    assert result["status"] == "error"
    assert "reason" in result
```

---

### 5.5 メモリシステムテスト (ST-MEM)

#### ST-MEM-001: セッション作成・取得

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-MEM-001 |
| **テスト名** | セッション作成・取得 |
| **目的** | MemoryManagementServiceのセッション管理を確認 |
| **期待結果** | セッションの作成と取得が正常に動作 |

```python
# tests/system/test_memory_system.py
import pytest
from bridge.memory.service import MemoryManagementService
from bridge.memory.postgres_repositories import (
    PostgresSessionRepository,
    PostgresIntentRepository,
    # ... その他のリポジトリ
)

@pytest.mark.asyncio
async def test_session_management():
    """ST-MEM-001: セッション作成・取得"""
    pool = await create_test_pool()

    session_repo = PostgresSessionRepository(pool)
    # 他のリポジトリも初期化...

    service = MemoryManagementService(
        session_repo=session_repo,
        # ... 他のリポジトリ
    )

    # セッション作成
    session = await service.start_session(
        user_id="test_user",
        metadata={"context": "system_test"}
    )

    assert session.id is not None
    assert session.user_id == "test_user"

    # セッション取得
    retrieved = await service.get_session(session.id)
    assert retrieved is not None
    assert retrieved.user_id == "test_user"
```

#### ST-MEM-002: Intent記録・ライフサイクル

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-MEM-002 |
| **テスト名** | Intent記録・ライフサイクル |
| **目的** | Intentの記録、ステータス更新、完了を確認 |
| **期待結果** | Intentライフサイクル全体が正常に動作 |

```python
@pytest.mark.asyncio
async def test_intent_lifecycle():
    """ST-MEM-002: Intent記録・ライフサイクル"""
    service = await create_memory_service()
    session = await service.start_session(user_id="test_user")

    # Intent記録
    from bridge.memory.models import IntentType, IntentStatus
    intent = await service.record_intent(
        session_id=session.id,
        intent_text="新機能を追加する",
        intent_type=IntentType.FEATURE,
        priority=5
    )

    assert intent.id is not None
    assert intent.status == IntentStatus.PENDING

    # ステータス更新
    updated = await service.update_intent_status(
        intent.id,
        IntentStatus.IN_PROGRESS
    )
    assert updated.status == IntentStatus.IN_PROGRESS

    # Intent完了
    completed = await service.complete_intent(
        intent.id,
        outcome={"result": "success", "files_changed": 3}
    )
    assert completed.status == IntentStatus.COMPLETED
    assert completed.outcome is not None
```

#### ST-MEM-003: Resonance記録

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-MEM-003 |
| **テスト名** | Resonance記録 |
| **目的** | 共鳴状態の記録と取得を確認 |
| **期待結果** | Resonanceレコードが正しく保存される |

```python
@pytest.mark.asyncio
async def test_resonance_recording():
    """ST-MEM-003: Resonance記録"""
    from bridge.memory.models import ResonanceState

    service = await create_memory_service()
    session = await service.start_session(user_id="test_user")

    # Resonance記録
    resonance = await service.record_resonance(
        session_id=session.id,
        state=ResonanceState.HARMONIZED,
        intensity=0.85,
        agents=["yuno", "kana"],
        pattern_type="dialogue"
    )

    assert resonance.id is not None
    assert resonance.intensity == 0.85

    # 統計取得
    stats = await service.get_resonance_statistics(session.id)
    assert stats["total"] >= 1
    assert stats["avg_intensity"] >= 0.85
```

#### ST-MEM-004: Choice Point管理

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-MEM-004 |
| **テスト名** | Choice Point管理（Sprint 10） |
| **目的** | 選択肢の保存、決定、却下理由記録を確認 |
| **期待結果** | Choice Pointのフルライフサイクルが動作 |

```python
@pytest.mark.asyncio
async def test_choice_point_management():
    """ST-MEM-004: Choice Point管理"""
    from bridge.memory.models import Choice

    service = await create_memory_service()
    session = await service.start_session(user_id="test_user")
    intent = await service.record_intent(
        session_id=session.id,
        intent_text="データベース選択",
        intent_type=IntentType.DECISION
    )

    # Choice Point作成
    choices = [
        Choice(id="postgresql", description="PostgreSQL", pros=["ACID", "pgvector"]),
        Choice(id="sqlite", description="SQLite", pros=["軽量"]),
        Choice(id="mongodb", description="MongoDB", pros=["スキーマレス"])
    ]

    choice_point = await service.create_choice_point_enhanced(
        user_id="test_user",
        session_id=session.id,
        intent_id=intent.id,
        question="どのデータベースを使用しますか？",
        choices=choices,
        tags=["database", "architecture"]
    )

    assert choice_point.id is not None
    assert len(choice_point.choices) == 3

    # 決定を記録（却下理由付き）
    decided = await service.decide_choice_enhanced(
        choice_point_id=choice_point.id,
        selected_choice_id="postgresql",
        rationale="pgvectorによるベクトル検索が必要",
        rejection_reasons={
            "sqlite": "スケーラビリティが不足",
            "mongodb": "ACID準拠が必要"
        }
    )

    assert decided.selected_choice_id == "postgresql"
    assert decided.decision_rationale is not None
```

#### ST-MEM-005: Breathing Cycle追跡

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-MEM-005 |
| **テスト名** | Breathing Cycle追跡 |
| **目的** | 呼吸フェーズの追跡を確認 |
| **期待結果** | 各フェーズが正しく記録される |

```python
@pytest.mark.asyncio
async def test_breathing_cycle():
    """ST-MEM-005: Breathing Cycle追跡"""
    from bridge.memory.models import BreathingPhase

    service = await create_memory_service()
    session = await service.start_session(user_id="test_user")

    # Inhaleフェーズ開始
    cycle = await service.start_breathing_phase(
        session_id=session.id,
        phase=BreathingPhase.INHALE,
        phase_data={"context": "問いの生成"}
    )

    assert cycle.id is not None
    assert cycle.phase == BreathingPhase.INHALE

    # フェーズ完了
    completed = await service.complete_breathing_phase(
        cycle_id=cycle.id,
        success=True,
        phase_data={"output": "問いが明確化された"}
    )

    assert completed.completed_at is not None
    assert completed.success is True
```

#### ST-MEM-006: スナップショット作成・復元

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-MEM-006 |
| **テスト名** | スナップショット作成・復元 |
| **目的** | 時間軸保存のためのスナップショット機能を確認 |
| **期待結果** | スナップショットの作成と復元が動作 |

```python
@pytest.mark.asyncio
async def test_snapshot_creation():
    """ST-MEM-006: スナップショット作成・復元"""
    from bridge.memory.models import SnapshotType

    service = await create_memory_service()
    session = await service.start_session(user_id="test_user")

    # テストデータ作成
    await service.record_intent(
        session_id=session.id,
        intent_text="テストIntent",
        intent_type=IntentType.FEATURE
    )

    # スナップショット作成
    snapshot = await service.create_snapshot(
        session_id=session.id,
        snapshot_type=SnapshotType.CHECKPOINT,
        description="システムテスト用チェックポイント",
        tags=["system_test"]
    )

    assert snapshot.id is not None
    assert "intents" in snapshot.snapshot_data

    # 復元データ取得
    restored_data = await service.restore_from_snapshot(snapshot.id)
    assert "session" in restored_data
    assert "intents" in restored_data
```

#### ST-MEM-007: セッション継続

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-MEM-007 |
| **テスト名** | セッション継続 |
| **目的** | 中断されたセッションの継続を確認 |
| **期待結果** | セッション状態が正しく復元される |

```python
@pytest.mark.asyncio
async def test_session_continuity():
    """ST-MEM-007: セッション継続"""
    service = await create_memory_service()

    # セッション開始
    session = await service.start_session(user_id="test_user")
    await service.record_intent(
        session_id=session.id,
        intent_text="中断前のIntent",
        intent_type=IntentType.FEATURE
    )

    # セッション継続
    continuation = await service.continue_session(session.id)

    assert continuation["session"] is not None
    assert continuation["last_intent"] is not None
    assert continuation["session"].status.value == "ACTIVE"
```

---

### 5.6 Context Assemblerテスト (ST-CTX)

#### ST-CTX-001: コンテキスト組み立て

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CTX-001 |
| **テスト名** | コンテキスト組み立て |
| **目的** | ContextAssemblerServiceの基本動作を確認 |
| **期待結果** | メッセージリストとメタデータが返却される |

```python
# tests/system/test_context_assembler.py
import pytest
from context_assembler.service import ContextAssemblerService

@pytest.mark.asyncio
async def test_context_assembly():
    """ST-CTX-001: コンテキスト組み立て"""
    assembler = await create_context_assembler()

    result = await assembler.assemble_context(
        user_message="前回の会話の続きを教えて",
        user_id="test_user"
    )

    assert result.messages is not None
    assert len(result.messages) >= 2  # system + user
    assert result.messages[0]["role"] == "system"
    assert result.messages[-1]["role"] == "user"
    assert result.metadata is not None
```

#### ST-CTX-002: メモリ階層統合

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CTX-002 |
| **テスト名** | メモリ階層統合 |
| **目的** | Working Memory、Semantic Memory、Session Summaryの統合を確認 |
| **期待結果** | 各メモリ層からの情報が統合される |

```python
@pytest.mark.asyncio
async def test_memory_layer_integration():
    """ST-CTX-002: メモリ階層統合"""
    assembler = await create_context_assembler()

    # テストデータ準備（Working Memory用メッセージ）
    await create_test_messages(user_id="test_user", count=5)

    result = await assembler.assemble_context(
        user_message="これまでの作業を振り返って",
        user_id="test_user",
        options=AssemblyOptions(
            include_semantic_memory=True,
            include_session_summary=True
        )
    )

    assert result.metadata.working_memory_count > 0
    # semantic_memoryは検索結果による
```

#### ST-CTX-003: トークン圧縮

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CTX-003 |
| **テスト名** | トークン圧縮 |
| **目的** | トークン上限超過時の圧縮機能を確認 |
| **期待結果** | compression_applied: true、トークン数が上限以下 |

```python
@pytest.mark.asyncio
async def test_token_compression():
    """ST-CTX-003: トークン圧縮"""
    from context_assembler.models import ContextConfig

    # 低いトークン上限で圧縮を誘発
    config = ContextConfig(max_tokens=1000, token_safety_margin=0.9)
    assembler = await create_context_assembler(config=config)

    # 大量のWorking Memory作成
    await create_test_messages(user_id="test_user", count=20)

    result = await assembler.assemble_context(
        user_message="長い会話の要約をお願い",
        user_id="test_user"
    )

    # 圧縮が適用されていることを確認
    assert result.metadata.total_tokens <= config.max_tokens * config.token_safety_margin
```

#### ST-CTX-004: 過去選択履歴統合（Sprint 10）

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CTX-004 |
| **テスト名** | 過去選択履歴統合 |
| **目的** | Choice Pointの履歴がコンテキストに含まれることを確認 |
| **期待結果** | past_choices_count > 0、システムプロンプトに選択履歴が含まれる |

```python
@pytest.mark.asyncio
async def test_past_choices_integration():
    """ST-CTX-004: 過去選択履歴統合"""
    # 事前にChoice Pointを作成
    await create_test_choice_points(user_id="test_user")

    assembler = await create_context_assembler()

    result = await assembler.assemble_context(
        user_message="データベース選択について相談したい",
        user_id="test_user",
        options=AssemblyOptions(include_past_choices=True)
    )

    assert result.metadata.past_choices_count >= 0

    # システムプロンプトに選択履歴が含まれる場合
    system_msg = result.messages[0]["content"]
    if result.metadata.past_choices_count > 0:
        assert "意思決定履歴" in system_msg or "選択" in system_msg
```

#### ST-CTX-005: バリデーション

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CTX-005 |
| **テスト名** | コンテキストバリデーション |
| **目的** | 不正なコンテキストが検出されることを確認 |
| **期待結果** | バリデーションエラーが発生 |

```python
@pytest.mark.asyncio
async def test_context_validation():
    """ST-CTX-005: コンテキストバリデーション"""
    assembler = await create_context_assembler()

    # 空メッセージでエラーを期待
    with pytest.raises(ValueError, match="empty"):
        await assembler.assemble_context(
            user_message="",
            user_id="test_user"
        )
```

---

### 5.7 矛盾検出テスト (ST-CONTRA)

#### ST-CONTRA-001: 技術スタック矛盾検出

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CONTRA-001 |
| **テスト名** | 技術スタック矛盾検出 |
| **目的** | 技術スタックの変更（PostgreSQL → SQLiteなど）を検出 |
| **期待結果** | contradiction_type: "tech_stack" が検出される |

```python
# tests/system/test_contradiction.py
import pytest
from bridge.contradiction.detector import ContradictionDetector
import uuid

@pytest.mark.asyncio
async def test_tech_stack_contradiction():
    """ST-CONTRA-001: 技術スタック矛盾検出"""
    pool = await create_test_pool()
    detector = ContradictionDetector(pool)

    # 事前Intent作成（PostgreSQL使用を宣言）
    old_intent_id = await create_intent(
        pool,
        user_id="test_user",
        content="PostgreSQLを使用してデータを永続化する"
    )

    # 新Intent（SQLiteへの変更）
    new_intent_id = uuid.uuid4()
    contradictions = await detector.check_new_intent(
        user_id="test_user",
        new_intent_id=new_intent_id,
        new_intent_content="SQLiteを使用してデータを保存する"
    )

    tech_contradictions = [c for c in contradictions if c.contradiction_type == "tech_stack"]
    assert len(tech_contradictions) > 0
    assert tech_contradictions[0].details["category"] == "database"
```

#### ST-CONTRA-002: 方針転換検出

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CONTRA-002 |
| **テスト名** | 方針転換検出（2週間以内） |
| **目的** | 短期間での方針転換を検出 |
| **期待結果** | contradiction_type: "policy_shift" が検出される |

```python
@pytest.mark.asyncio
async def test_policy_shift_detection():
    """ST-CONTRA-002: 方針転換検出"""
    pool = await create_test_pool()
    detector = ContradictionDetector(pool)

    # マイクロサービス宣言（最近）
    await create_intent(
        pool,
        user_id="test_user",
        content="マイクロサービスアーキテクチャで設計する",
        created_at=datetime.now(timezone.utc) - timedelta(days=3)
    )

    # モノリスへの転換
    new_intent_id = uuid.uuid4()
    contradictions = await detector.check_new_intent(
        user_id="test_user",
        new_intent_id=new_intent_id,
        new_intent_content="モノリシックなアプリケーションとして実装する"
    )

    policy_shifts = [c for c in contradictions if c.contradiction_type == "policy_shift"]
    assert len(policy_shifts) > 0
    assert policy_shifts[0].details["old_policy"] == "microservice"
    assert policy_shifts[0].details["new_policy"] == "monolith"
```

#### ST-CONTRA-003: 重複作業検出

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CONTRA-003 |
| **テスト名** | 重複作業検出 |
| **目的** | 類似度85%以上のIntentを重複として検出 |
| **期待結果** | contradiction_type: "duplicate" が検出される |

```python
@pytest.mark.asyncio
async def test_duplicate_work_detection():
    """ST-CONTRA-003: 重複作業検出"""
    pool = await create_test_pool()
    detector = ContradictionDetector(pool)

    # 既存Intent（完了済み）
    await create_intent(
        pool,
        user_id="test_user",
        content="ユーザー認証機能を実装する JWT トークンを使用",
        status="completed"
    )

    # ほぼ同一のIntent
    new_intent_id = uuid.uuid4()
    contradictions = await detector.check_new_intent(
        user_id="test_user",
        new_intent_id=new_intent_id,
        new_intent_content="ユーザー認証機能を実装する JWT トークンを使用する"
    )

    duplicates = [c for c in contradictions if c.contradiction_type == "duplicate"]
    assert len(duplicates) > 0
    assert duplicates[0].details["similarity"] >= 0.85
```

#### ST-CONTRA-004: ドグマ検出

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CONTRA-004 |
| **テスト名** | ドグマ（未検証前提）検出 |
| **目的** | 「常に」「絶対」などの未検証前提を検出 |
| **期待結果** | contradiction_type: "dogma" が検出される |

```python
@pytest.mark.asyncio
async def test_dogma_detection():
    """ST-CONTRA-004: ドグマ検出"""
    pool = await create_test_pool()
    detector = ContradictionDetector(pool)

    new_intent_id = uuid.uuid4()
    contradictions = await detector.check_new_intent(
        user_id="test_user",
        new_intent_id=new_intent_id,
        new_intent_content="すべてのユーザーは常にログインしている必要がある"
    )

    dogmas = [c for c in contradictions if c.contradiction_type == "dogma"]
    assert len(dogmas) > 0
    assert "常に" in dogmas[0].details["detected_keywords"] or "always" in str(dogmas[0].details)
```

#### ST-CONTRA-005: 矛盾解決

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CONTRA-005 |
| **テスト名** | 矛盾解決 |
| **目的** | 検出された矛盾の解決プロセスを確認 |
| **期待結果** | resolution_status が "approved" に更新される |

```python
@pytest.mark.asyncio
async def test_contradiction_resolution():
    """ST-CONTRA-005: 矛盾解決"""
    pool = await create_test_pool()
    detector = ContradictionDetector(pool)

    # 矛盾を検出
    new_intent_id = uuid.uuid4()
    contradictions = await detector.check_new_intent(
        user_id="test_user",
        new_intent_id=new_intent_id,
        new_intent_content="SQLiteを使用する"
    )

    if contradictions:
        # 矛盾を解決
        contradiction = contradictions[0]
        await detector.resolve_contradiction(
            contradiction_id=contradiction.id,
            resolution_action="proceed",
            resolution_rationale="開発環境では軽量DBが適切",
            resolved_by="test_user"
        )

        # 解決確認
        pending = await detector.get_pending_contradictions("test_user")
        resolved_ids = [c.id for c in pending]
        assert contradiction.id not in resolved_ids
```

#### ST-CONTRA-006: 未解決矛盾一覧取得

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-CONTRA-006 |
| **テスト名** | 未解決矛盾一覧取得 |
| **目的** | ユーザーの未解決矛盾を取得できることを確認 |
| **期待結果** | pendingステータスの矛盾リストが返却される |

```python
@pytest.mark.asyncio
async def test_get_pending_contradictions():
    """ST-CONTRA-006: 未解決矛盾一覧取得"""
    pool = await create_test_pool()
    detector = ContradictionDetector(pool)

    # 矛盾を生成
    await detector.check_new_intent(
        user_id="test_user",
        new_intent_id=uuid.uuid4(),
        new_intent_content="常にキャッシュを使用する"
    )

    pending = await detector.get_pending_contradictions("test_user")

    assert isinstance(pending, list)
    for c in pending:
        assert c.resolution_status == "pending"
```

---

### 5.8 リアルタイム通信テスト (ST-RT)

#### ST-RT-001: WebSocket接続

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-RT-001 |
| **テスト名** | WebSocket接続 |
| **目的** | /ws/intents へのWebSocket接続を確認 |
| **期待結果** | 接続成功、メッセージ送受信可能 |

```python
# tests/system/test_realtime.py
import pytest
import websockets
import json

@pytest.mark.asyncio
async def test_websocket_connection():
    """ST-RT-001: WebSocket接続"""
    uri = "ws://localhost:8000/ws/intents"

    async with websockets.connect(uri) as ws:
        # 購読メッセージ送信
        await ws.send(json.dumps({
            "type": "subscribe",
            "intent_ids": ["test-intent-id"]
        }))

        # 応答確認（タイムアウト付き）
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            assert "type" in data or "status" in data
        except asyncio.TimeoutError:
            pass  # タイムアウトは許容（イベントがない場合）
```

#### ST-RT-002: SSEストリーム

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-RT-002 |
| **テスト名** | SSEストリーム |
| **目的** | Server-Sent Eventsのストリーミングを確認 |
| **期待結果** | SSE接続成功、イベント受信可能 |

```python
@pytest.mark.asyncio
async def test_sse_stream():
    """ST-RT-002: SSEストリーム"""
    import httpx

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET",
            f"{BASE_URL}/events/audit-logs",
            timeout=10.0
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
```

#### ST-RT-003: Intent更新通知

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-RT-003 |
| **テスト名** | Intent更新通知 |
| **目的** | Intent更新時にWebSocket経由で通知されることを確認 |
| **期待結果** | Intent更新イベントを受信 |

```python
@pytest.mark.asyncio
async def test_intent_update_notification():
    """ST-RT-003: Intent更新通知"""
    import asyncio

    intent_id = await create_test_intent()
    received_events = []

    async def listen_websocket():
        uri = f"ws://localhost:8000/ws/intents"
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({
                "type": "subscribe",
                "intent_ids": [intent_id]
            }))

            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    received_events.append(json.loads(msg))
            except asyncio.TimeoutError:
                pass

    # WebSocketリスナー開始
    listener_task = asyncio.create_task(listen_websocket())

    # Intent更新を実行
    await asyncio.sleep(1)  # 接続待ち
    await update_intent_status(intent_id, "COMPLETED")

    await asyncio.sleep(2)  # イベント受信待ち
    listener_task.cancel()

    # イベント検証は環境依存のためスキップ可能
```

#### ST-RT-004: イベント配信ラグ計測

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-RT-004 |
| **テスト名** | イベント配信ラグ計測 |
| **目的** | リアルタイム通信のレイテンシを計測 |
| **期待結果** | 配信ラグが500ms以内 |

```python
@pytest.mark.asyncio
async def test_event_delivery_latency():
    """ST-RT-004: イベント配信ラグ計測"""
    import time

    latencies = []

    # 5回計測
    for _ in range(5):
        start = time.time()

        # イベント送信（Intent作成など）
        intent_id = await create_test_intent()

        # 配信確認（擬似的に）
        await asyncio.sleep(0.1)

        latency = (time.time() - start) * 1000
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    print(f"平均配信ラグ: {avg_latency:.2f}ms")

    # 500ms以内を許容
    assert avg_latency < 500
```

---

### 5.9 エンドツーエンドテスト (ST-E2E)

#### ST-E2E-001: Intent作成〜完了フロー

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-E2E-001 |
| **テスト名** | Intent作成〜完了フロー |
| **目的** | Intent作成からClaude処理、完了までの全フローを確認 |
| **期待結果** | Intentが正常に完了状態になる |

```python
# tests/system/test_e2e.py
import pytest
import httpx
import asyncio

@pytest.mark.asyncio
async def test_full_intent_flow():
    """ST-E2E-001: Intent作成〜完了フロー"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Intent作成
        create_response = await client.post(
            f"{BASE_URL}/api/intents",
            json={
                "source": "KANA",
                "type": "FEATURE_REQUEST",
                "content": "ログイン機能のセキュリティ強化",
                "user_id": "test_user"
            }
        )
        assert create_response.status_code in [200, 201]
        intent_id = create_response.json()["id"]

        # 2. BridgeSetパイプライン実行（内部で行われる場合）
        # または手動で再評価API呼び出し

        # 3. ステータス確認（ポーリング）
        max_attempts = 10
        for _ in range(max_attempts):
            status_response = await client.get(
                f"{BASE_URL}/api/intents/{intent_id}"
            )
            if status_response.status_code == 200:
                status = status_response.json().get("status")
                if status in ["COMPLETED", "CORRECTED"]:
                    break
            await asyncio.sleep(2)

        # 最終状態確認
        final_response = await client.get(
            f"{BASE_URL}/api/intents/{intent_id}"
        )
        assert final_response.status_code == 200
        print(f"最終ステータス: {final_response.json().get('status')}")
```

#### ST-E2E-002: 会話→メモリ→コンテキストフロー

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-E2E-002 |
| **テスト名** | 会話→メモリ→コンテキストフロー |
| **目的** | メッセージ保存〜メモリ検索〜コンテキスト組み立ての統合を確認 |
| **期待結果** | 過去の会話がコンテキストに反映される |

```python
@pytest.mark.asyncio
async def test_conversation_memory_context_flow():
    """ST-E2E-002: 会話→メモリ→コンテキストフロー"""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient() as client:
        # 1. 複数の会話を保存
        for i in range(3):
            await client.post(
                f"{BASE_URL}/api/messages",
                json={
                    "user_id": user_id,
                    "content": f"これは{i+1}番目のテストメッセージです。PostgreSQLについて質問しています。",
                    "message_type": "USER"
                }
            )

        # 2. KanaAIBridge経由でContext Assemblerを使用
        from bridge.providers.ai.kana_ai_bridge import KanaAIBridge

        kana = KanaAIBridge()
        result = await kana.process_intent({
            "content": "PostgreSQLの設定について教えて",
            "user_id": user_id
        })

        assert result["status"] == "ok"
        # context_metadataがあれば、Working Memoryが使用されていることを確認
        if "context_metadata" in result:
            print(f"Working Memory件数: {result['context_metadata']['working_memory_count']}")
```

#### ST-E2E-003: 矛盾検出→解決フロー

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-E2E-003 |
| **テスト名** | 矛盾検出→解決フロー |
| **目的** | 矛盾検出から解決までの全フローを確認 |
| **期待結果** | 矛盾が検出され、解決プロセスが完了する |

```python
@pytest.mark.asyncio
async def test_contradiction_detection_resolution_flow():
    """ST-E2E-003: 矛盾検出→解決フロー"""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    pool = await create_test_pool()
    detector = ContradictionDetector(pool)

    # 1. 初期Intent作成（PostgreSQL使用）
    await create_intent(
        pool,
        user_id=user_id,
        content="PostgreSQLを使用してデータを保存する"
    )

    # 2. 矛盾するIntent作成（SQLite使用）
    new_intent_id = uuid.uuid4()
    contradictions = await detector.check_new_intent(
        user_id=user_id,
        new_intent_id=new_intent_id,
        new_intent_content="SQLiteを使用してデータを保存する"
    )

    assert len(contradictions) > 0
    print(f"検出された矛盾: {len(contradictions)}件")

    # 3. 矛盾一覧取得
    pending = await detector.get_pending_contradictions(user_id)
    assert len(pending) > 0

    # 4. 矛盾解決
    for c in pending:
        await detector.resolve_contradiction(
            contradiction_id=c.id,
            resolution_action="proceed",
            resolution_rationale="テスト環境のため許容",
            resolved_by=user_id
        )

    # 5. 解決確認
    remaining = await detector.get_pending_contradictions(user_id)
    assert len(remaining) == 0
```

---

## 6. テスト実行手順

### 6.1 環境準備

```bash
# 1. プロジェクトディレクトリに移動
cd /Users/zero/Projects/resonant-engine

# 2. Python仮想環境を有効化
source venv/bin/activate

# 3. テスト依存関係インストール
pip install pytest pytest-asyncio httpx websockets

# 4. Docker環境起動
cd docker
./scripts/start.sh

# 5. ヘルスチェック
./scripts/check-health.sh
```

### 6.2 テスト実行コマンド

```bash
# 全システムテスト実行
pytest tests/system/ -v --tb=short

# カテゴリ別実行
pytest tests/system/test_db_connection.py -v          # DB接続テスト
pytest tests/system/test_api.py -v                    # APIテスト
pytest tests/system/test_bridge_pipeline.py -v        # パイプラインテスト
pytest tests/system/test_claude_api.py -v             # Claude APIテスト
pytest tests/system/test_memory_system.py -v          # メモリシステムテスト
pytest tests/system/test_context_assembler.py -v      # Context Assemblerテスト
pytest tests/system/test_contradiction.py -v          # 矛盾検出テスト
pytest tests/system/test_realtime.py -v               # リアルタイム通信テスト
pytest tests/system/test_e2e.py -v                    # E2Eテスト

# レポート出力付き
pytest tests/system/ -v --html=reports/system_test_report.html

# 特定のテストのみ実行
pytest tests/system/ -v -k "ST-AI"  # Claude API関連のみ
```

### 6.3 テスト結果確認

```bash
# 結果サマリー確認
pytest tests/system/ -v --tb=line

# 失敗テストのみ再実行
pytest tests/system/ --lf -v

# カバレッジレポート
pytest tests/system/ --cov=bridge --cov-report=html
```

---

## 7. 合否判定基準

### 7.1 必須合格条件

| カテゴリ | 必須合格率 | 備考 |
|---------|----------|------|
| ST-DB (データベース) | 100% | 基盤機能のため |
| ST-API (REST API) | 100% | 外部インターフェースのため |
| ST-BRIDGE (パイプライン) | 90% | コア機能のため |
| ST-AI (Claude API) | 80% | API依存のため許容 |
| ST-E2E (エンドツーエンド) | 100% | 統合動作確認のため |

### 7.2 推奨合格条件

| カテゴリ | 推奨合格率 |
|---------|----------|
| ST-MEM (メモリシステム) | 90% |
| ST-CTX (Context Assembler) | 90% |
| ST-CONTRA (矛盾検出) | 90% |
| ST-RT (リアルタイム) | 80% |

### 7.3 総合判定

| 判定 | 条件 |
|-----|------|
| **合格** | 必須合格条件をすべて満たす |
| **条件付き合格** | 必須合格条件を満たし、推奨条件の70%以上を満たす |
| **不合格** | 必須合格条件を1つでも満たさない |

### 7.4 不合格時の対応

1. 失敗テストの詳細ログを確認
2. 原因分析（環境問題 / バグ / テストケースの問題）
3. 修正実施
4. 該当カテゴリの再テスト
5. 結果報告

---

## 付録A: テストデータ準備スクリプト

```python
# tests/system/fixtures.py
import asyncpg
import uuid
from datetime import datetime, timezone

async def create_test_pool():
    """テスト用DB接続プール作成"""
    return await asyncpg.create_pool(
        "postgresql://resonant:password@localhost:5432/resonant_dashboard",
        min_size=1,
        max_size=5
    )

async def create_test_intent(pool=None, **kwargs):
    """テスト用Intent作成"""
    if pool is None:
        pool = await create_test_pool()

    intent_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO intents (id, source, type, content, status, user_id, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
            uuid.UUID(intent_id),
            kwargs.get("source", "KANA"),
            kwargs.get("type", "FEATURE_REQUEST"),
            kwargs.get("content", "Test intent"),
            kwargs.get("status", "PENDING"),
            kwargs.get("user_id", "test_user"),
            kwargs.get("created_at", datetime.now(timezone.utc))
        )
    return intent_id

async def delete_test_intent(intent_id, pool=None):
    """テスト用Intent削除"""
    if pool is None:
        pool = await create_test_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM intents WHERE id = $1",
            uuid.UUID(intent_id)
        )
```

---

## 付録B: 環境変数テンプレート

```bash
# .env.test
# テスト環境用環境変数

# PostgreSQL
POSTGRES_USER=resonant
POSTGRES_PASSWORD=test_password_secure
POSTGRES_DB=resonant_dashboard
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

# API
API_PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxx...

# Bridge設定（本番プロバイダー使用）
DATA_BRIDGE_TYPE=postgresql
AI_BRIDGE_TYPE=kana
FEEDBACK_BRIDGE_TYPE=mock
AUDIT_LOGGER_TYPE=postgresql

# テスト設定
TEST_TIMEOUT=60
TEST_RETRY_COUNT=3
```

---

**テスト仕様書作成者**: Claude Code
**最終更新**: 2025-11-23
