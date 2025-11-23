# Resonant Engine 総合テスト仕様書

**作成日**: 2025-11-23
**バージョン**: 3.0（マイグレーション手順追加版）
**対象環境**: 開発環境（Docker Compose）
**テスト種別**: システムテスト / 総合テスト

---

## ⚠️ 重要事項（MUST READ FIRST）

### 絶対遵守事項（MUST）

1. **テストは必ずDockerコンテナ内で実行すること**
   ```bash
   docker exec resonant_dev pytest tests/system/ -v
   ```

2. **テスト実行前にマイグレーション確認を行うこと**
   - セクション4「マイグレーション確認・実行手順」に従う

3. **既存のconftest.pyを使用すること**
   - `tests/conftest.py`に`db_pool`フィクスチャが定義済み
   - **新たにconftest.pyを作成してはならない**

4. **エラー発生時は根本原因を調査すること**
   - 表面的な対処（パスワード変更、ハードコードなど）は禁止
   - 必ず「なぜこのエラーが発生するのか」を追求

5. **既存の動作しているテストを参考にすること**
   - `tests/bridge/`配下のテストが参考になる

### 禁止事項（MUST NOT）

| 禁止事項 | 理由 |
|---------|------|
| ローカル環境でのpytest実行 | DB接続がDockerネットワーク内でのみ有効 |
| `tests/system/conftest.py`の新規作成 | 既存の`tests/conftest.py`と競合する |
| パスワードのハードコード | 環境変数を使用すること |
| トリガーの無効化 | システムの整合性を損なう |
| 同じ仮説の繰り返し検証 | 一度否定された仮説は記録して除外 |
| 仕様書を無視した独自判断 | 本仕様書に従うこと |

---

## 目次

1. [テスト概要](#1-テスト概要)
2. [テスト環境](#2-テスト環境)
3. [前提条件](#3-前提条件)
4. [マイグレーション確認・実行手順](#4-マイグレーション確認実行手順)
5. [テスト実行手順](#5-テスト実行手順)
6. [テスト項目一覧](#6-テスト項目一覧)
7. [テストケース詳細](#7-テストケース詳細)
8. [エラー対処チェックリスト](#8-エラー対処チェックリスト)
9. [合否判定基準](#9-合否判定基準)

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
│ resonant_postgres   │ PostgreSQL 15 (pgvector) │ port:5432  │
│ resonant_dev        │ Python開発環境           │ テスト実行  │
│ resonant_api        │ Backend API (FastAPI)    │ port:8000  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 ネットワーク構成（重要）

```
Docker内部ネットワーク:
  resonant_dev → postgres:5432 (サービス名で接続)
  resonant_dev → resonant_api:8000

ローカルマシン:
  localhost:5432 → resonant_postgres
  localhost:8000 → resonant_api
```

**ポイント**: Dockerコンテナ内からDBに接続する場合、ホスト名は`postgres`（サービス名）を使用する。`localhost`は使用しない。

### 2.3 既存のconftest.py（必ず使用すること）

```python
# tests/conftest.py（既存・変更禁止）
@pytest.fixture(scope="session")
async def db_pool():
    """PostgreSQL connection pool - Docker環境用"""
    pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),  # Docker内ではサービス名
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "resonant"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        database=os.getenv("POSTGRES_DB", "postgres"),
        min_size=1,
        max_size=10,
    )
    yield pool
    await pool.close()
```

**この`db_pool`フィクスチャを使用すること。独自に接続プールを作成してはならない。**

---

## 3. 前提条件

### 3.1 環境準備チェックリスト

実行前に以下を確認すること：

- [ ] Docker / Docker Composeがインストールされている
- [ ] `.env`ファイルが正しく設定されている
- [ ] `ANTHROPIC_API_KEY`が有効である
- [ ] Dockerコンテナが起動している（`docker ps`で確認）
- [ ] `resonant_dev`コンテナが存在する
- [ ] **マイグレーションが実行済みである（セクション4参照）**

### 3.2 コンテナ起動確認

```bash
# コンテナ起動状態確認（必須）
docker ps | grep resonant

# 期待される出力:
# resonant_dev      ... Up ...
# resonant_postgres ... Up ...
# resonant_api      ... Up ...
```

---

## 4. マイグレーション確認・実行手順

### 4.1 マイグレーション必要性の判断方法

**以下のコマンドを実行して、マイグレーションが必要か判断すること。**

```bash
# Docker内でマイグレーション状態を確認
docker exec resonant_postgres psql -U resonant -d postgres -c "
SELECT 'テーブル/拡張' as type, name, '存在する' as status FROM (
    SELECT 'pgvector拡張' as name, EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector') as exists
    UNION ALL SELECT 'intents', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'intents')
    UNION ALL SELECT 'messages', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'messages')
    UNION ALL SELECT 'contradictions', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'contradictions')
    UNION ALL SELECT 'semantic_memories', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'semantic_memories')
    UNION ALL SELECT 'choice_points', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'choice_points')
    UNION ALL SELECT 'user_profiles', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profiles')
    UNION ALL SELECT 'sessions', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'sessions')
) t WHERE exists = true;
"
```

### 4.2 マイグレーションファイル一覧

| 順序 | ファイル名 | Sprint | 作成されるテーブル/拡張 |
|-----|-----------|--------|----------------------|
| 1 | `init.sql` | Sprint 1 | messages, specifications, intents, notifications |
| 2 | `002_intent_notify.sql` | Sprint 4 | トリガー: notify_intent_created, notify_intent_status_changed |
| 3 | `003_message_notify.sql` | Sprint 4 | トリガー: notify_message_created |
| 4 | `004_claude_code_tables.sql` | Sprint 4.5 | claude_code_sessions, claude_code_executions |
| 5 | `005_user_profile_tables.sql` | Sprint 8 | user_profiles, cognitive_traits, family_members, user_goals, resonant_concepts |
| 6 | `006_choice_points_initial.sql` | Sprint 8 | choice_points |
| 7 | `006_memory_lifecycle_tables.sql` | Sprint 9 | **pgvector拡張**, semantic_memories, memory_archive, memory_lifecycle_log |
| 8 | `007_choice_preservation_completion.sql` | Sprint 10 | choice_pointsの拡張 |
| 9 | `008_contradiction_detection.sql` | Sprint 11 | contradictions, intent_relations |
| 10 | `008_intents_migration.sql` | Sprint 10 | intentsテーブルの変更（description→intent_text等） |

### 4.3 マイグレーション実行手順

**マイグレーションが必要と判断された場合のみ実行すること。**

```bash
# Step 1: 基本テーブルの確認（init.sqlは通常Docker起動時に実行済み）
docker exec resonant_postgres psql -U resonant -d postgres -c "\dt"

# Step 2: 不足しているマイグレーションを順番に実行
# ※ 既に実行済みのファイルはスキップしてよい（IF NOT EXISTSで冪等性あり）

# Sprint 4: Intent通知トリガー
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/002_intent_notify.sql

# Sprint 4: Message通知トリガー
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/003_message_notify.sql

# Sprint 4.5: Claude Code統合
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/004_claude_code_tables.sql

# Sprint 8: ユーザープロフィール
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/005_user_profile_tables.sql

# Sprint 8: Choice Points初期
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/006_choice_points_initial.sql

# Sprint 9: Memory Lifecycle（pgvector + semantic_memories）★重要★
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/006_memory_lifecycle_tables.sql

# Sprint 10: Choice Points拡張
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/007_choice_preservation_completion.sql

# Sprint 11: 矛盾検出
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/008_contradiction_detection.sql

# Sprint 10: Intentsテーブル変更（トリガー修正も必要）
docker exec resonant_postgres psql -U resonant -d postgres -f /docker-entrypoint-initdb.d/008_intents_migration.sql
```

### 4.4 トリガー修正（intents_migration実行後に必要）

**intentsテーブルの`description`カラムが`intent_text`にリネームされた場合、トリガー関数も修正が必要。**

```bash
# トリガー関数の修正
docker exec resonant_postgres psql -U resonant -d postgres -c "
CREATE OR REPLACE FUNCTION notify_intent_created()
RETURNS TRIGGER AS \$\$
BEGIN
    PERFORM pg_notify(
        'intent_created',
        json_build_object(
            'id', NEW.id::text,
            'intent_text', substring(COALESCE(NEW.intent_text, ''), 1, 100),
            'priority', NEW.priority
        )::text
    );
    RETURN NEW;
END;
\$\$ LANGUAGE plpgsql;
"
```

### 4.5 マイグレーション完了確認

```bash
# 全テーブル一覧
docker exec resonant_postgres psql -U resonant -d postgres -c "\dt"

# pgvector拡張確認
docker exec resonant_postgres psql -U resonant -d postgres -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"

# 主要テーブルのカラム確認
docker exec resonant_postgres psql -U resonant -d postgres -c "\d intents"
docker exec resonant_postgres psql -U resonant -d postgres -c "\d semantic_memories"
docker exec resonant_postgres psql -U resonant -d postgres -c "\d contradictions"
```

---

## 5. テスト実行手順

### Phase 1: 環境確認（5分）

```bash
# Step 1.1: コンテナ起動確認
docker ps | grep resonant

# Step 1.2: DB接続テスト
docker exec resonant_dev python -c "
import asyncio
import asyncpg
async def test():
    pool = await asyncpg.create_pool(
        host='postgres', port=5432, user='resonant',
        password='password', database='postgres'
    )
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT 1')
        print(f'DB接続OK: {result}')
    await pool.close()
asyncio.run(test())
"

# Step 1.3: 既存テストが動作することを確認
docker exec resonant_dev pytest tests/bridge/ -v --collect-only
```

### Phase 2: マイグレーション確認

```bash
# Step 2.1: マイグレーション状態確認（セクション4.1のコマンド実行）
# Step 2.2: 必要に応じてマイグレーション実行（セクション4.3）
# Step 2.3: 完了確認（セクション4.5）
```

### Phase 3: テストファイル作成

```bash
# Step 3.1: ディレクトリ作成（存在しない場合のみ）
docker exec resonant_dev mkdir -p tests/system

# Step 3.2: __init__.py作成
docker exec resonant_dev touch tests/system/__init__.py
```

**重要**: `tests/system/conftest.py`は作成しない。`tests/conftest.py`の`db_pool`フィクスチャを使用する。

### Phase 4: テスト実行

```bash
# 全テスト実行（必ずDocker内で）
docker exec resonant_dev pytest tests/system/ -v

# 特定のテストのみ実行
docker exec resonant_dev pytest tests/system/test_db_connection.py -v

# 詳細出力付き
docker exec resonant_dev pytest tests/system/ -v --tb=long
```

---

## 6. テスト項目一覧

### 6.1 テストカテゴリ

| ID | カテゴリ | 必須 | 条件付き | 優先度 |
|----|---------|-----|---------|-------|
| ST-DB | データベース接続 | 3 | 2 | 高 |
| ST-API | REST API | 8 | 0 | 高 |
| ST-BRIDGE | BridgeSetパイプライン | 6 | 0 | 高 |
| ST-AI | Claude API (Kana) | 5 | 0 | 高 |
| ST-MEM | メモリシステム | 7 | 0 | 中 |
| ST-CTX | Context Assembler | 5 | 0 | 中 |
| ST-CONTRA | 矛盾検出 | 6 | 0 | 中 |
| ST-RT | リアルタイム通信 | 4 | 0 | 低 |
| ST-E2E | エンドツーエンド | 3 | 0 | 高 |

**総テスト項目数: 47必須 + 2条件付き = 49**

### 6.2 テスト分類の定義

| 分類 | 定義 | スキップ時の扱い |
|-----|------|----------------|
| **必須** | 常に実行され、合格が必要 | スキップ不可。失敗扱い |
| **条件付き** | 前提条件を満たす場合のみ実行 | 前提条件未達成時はスキップ可。合格率の分母から除外 |

### 6.3 条件付きテスト一覧

| テストID | テスト名 | 前提条件 | マイグレーション |
|---------|---------|---------|----------------|
| ST-DB-002 | pgvector拡張確認 | pgvector拡張がインストールされている | Sprint 9 (006_memory_lifecycle_tables.sql) |
| ST-DB-005 | semantic_memoriesテーブル・ベクトル検索 | semantic_memoriesテーブルが存在する | Sprint 9 (006_memory_lifecycle_tables.sql) |

**重要**:
- 条件付きテストがスキップされた場合、その機能は**未実装（マイグレーション未実行）**として記録すること
- スキップは「合格」ではなく「未テスト」である
- **マイグレーションを実行すれば条件付きテストも実行可能になる**

---

## 7. テストケース詳細

### 7.1 データベース接続テスト (ST-DB)

#### ST-DB-001: PostgreSQL接続確認

| 項目 | 内容 |
|-----|------|
| **テストID** | ST-DB-001 |
| **テスト名** | PostgreSQL接続確認 |
| **目的** | PostgreSQLへの接続が正常に行えることを確認 |
| **前提条件** | Docker Composeでpostgresサービスが起動している |
| **期待結果** | 接続成功、SELECT 1 が "1" を返す |

```python
# tests/system/test_db_connection.py
import pytest

@pytest.mark.asyncio
async def test_postgres_connection(db_pool):
    """ST-DB-001: PostgreSQL接続確認

    IMPORTANT: db_poolフィクスチャを使用すること（tests/conftest.pyで定義済み）
    独自に接続プールを作成してはならない。
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1
```

#### ST-DB-002: pgvector拡張確認【条件付き】

| 項目 | 内容 |
|-----|------|
| **分類** | 条件付き |
| **前提条件** | pgvector拡張がインストールされている |
| **マイグレーション** | Sprint 9: `006_memory_lifecycle_tables.sql` |
| **スキップ条件** | 拡張が未インストールの場合 |

```python
@pytest.mark.asyncio
async def test_pgvector_extension(db_pool):
    """ST-DB-002: pgvector拡張確認【条件付き】

    前提条件: pgvector拡張がインストールされていること
    マイグレーション: Sprint 9 (006_memory_lifecycle_tables.sql)
    スキップ条件: 拡張が未インストールの場合
    """
    async with db_pool.acquire() as conn:
        # 拡張存在確認（スキップ判定）
        result = await conn.fetchval(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )
        if result is None:
            pytest.skip(
                "pgvector拡張が未インストールのためスキップ（条件付きテスト）。"
                "Sprint 9マイグレーション(006_memory_lifecycle_tables.sql)を実行してください。"
            )

        # vector型テスト
        await conn.execute("SELECT '[1,2,3]'::vector")
```

#### ST-DB-003: Intentsテーブル操作

```python
@pytest.mark.asyncio
async def test_intents_crud(db_pool):
    """ST-DB-003: IntentsテーブルCRUD

    NOTE: Sprint 10マイグレーション後は description → intent_text に変更
    トリガーが定義されている場合、必要なカラムに適切な値を設定すること
    """
    import uuid
    import json

    test_id = uuid.uuid4()

    async with db_pool.acquire() as conn:
        # テーブル構造を事前に確認（Sprint 10マイグレーション対応）
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'intents'
        """)
        column_names = [c['column_name'] for c in columns]

        # Sprint 10マイグレーション後: intent_text を使用
        # Sprint 10マイグレーション前: description を使用
        text_column = 'intent_text' if 'intent_text' in column_names else 'description'

        # INSERT（カラム名を動的に決定）
        if text_column == 'intent_text':
            await conn.execute(f"""
                INSERT INTO intents (id, {text_column}, intent_type, status, priority, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, test_id, 'Test intent', 'FEATURE_REQUEST', 'pending', 0, json.dumps({"test": True}))
        else:
            await conn.execute(f"""
                INSERT INTO intents (id, {text_column}, intent_type, status, priority, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, test_id, 'Test intent', 'FEATURE_REQUEST', 'pending', 0, json.dumps({"test": True}))

        # SELECT
        row = await conn.fetchrow(
            "SELECT * FROM intents WHERE id = $1",
            test_id
        )
        assert row is not None
        assert row['status'] == 'pending'

        # UPDATE
        await conn.execute(
            "UPDATE intents SET status = 'completed' WHERE id = $1",
            test_id
        )

        # DELETE (cleanup)
        await conn.execute(
            "DELETE FROM intents WHERE id = $1",
            test_id
        )
```

#### ST-DB-004: contradictionsテーブル操作

```python
@pytest.mark.asyncio
async def test_contradictions_table(db_pool):
    """ST-DB-004: contradictionsテーブル操作

    マイグレーション: Sprint 11 (008_contradiction_detection.sql)
    """
    async with db_pool.acquire() as conn:
        # テーブル存在確認
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'contradictions'
            )
        """)
        assert exists is True, (
            "contradictionsテーブルが存在しません。"
            "Sprint 11マイグレーション(008_contradiction_detection.sql)を実行してください。"
        )

        # カラム確認
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'contradictions'
        """)
        column_names = [c['column_name'] for c in columns]
        assert 'contradiction_type' in column_names
        assert 'confidence_score' in column_names
        assert 'resolution_status' in column_names
```

#### ST-DB-005: semantic_memoriesテーブル・ベクトル検索【条件付き】

| 項目 | 内容 |
|-----|------|
| **分類** | 条件付き |
| **前提条件** | semantic_memoriesテーブルが存在する |
| **マイグレーション** | Sprint 9: `006_memory_lifecycle_tables.sql` |
| **スキップ条件** | テーブルが未作成の場合 |

**注意**: 元の仕様書では`memories`テーブルでしたが、正しくは`semantic_memories`テーブルです。

```python
@pytest.mark.asyncio
async def test_vector_similarity_search(db_pool):
    """ST-DB-005: ベクトル類似度検索【条件付き】

    前提条件: semantic_memoriesテーブルが存在すること
    マイグレーション: Sprint 9 (006_memory_lifecycle_tables.sql)
    スキップ条件: テーブルが未作成の場合

    NOTE: テーブル名は memories ではなく semantic_memories
    """
    async with db_pool.acquire() as conn:
        # テーブル存在確認（スキップ判定）
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'semantic_memories'
            )
        """)

        if not exists:
            pytest.skip(
                "semantic_memoriesテーブルが未作成のためスキップ（条件付きテスト）。"
                "Sprint 9マイグレーション(006_memory_lifecycle_tables.sql)を実行してください。"
            )

        # テスト用メモリ挿入（1536次元のダミーベクトル）
        test_vector = [0.1] * 1536
        await conn.execute("""
            INSERT INTO semantic_memories (content, embedding, memory_type, user_id)
            VALUES ('Test memory content', $1::vector, 'working', 'test_user')
        """, str(test_vector))

        # 類似検索
        results = await conn.fetch("""
            SELECT content, embedding <-> $1::vector AS distance
            FROM semantic_memories
            WHERE user_id = 'test_user'
            ORDER BY distance
            LIMIT 5
        """, str(test_vector))

        assert len(results) >= 1

        # クリーンアップ
        await conn.execute(
            "DELETE FROM semantic_memories WHERE user_id = 'test_user'"
        )
```

---

### 7.2 REST API テスト (ST-API)

#### 共通設定

```python
# tests/system/test_api.py
import httpx
import pytest

# Docker内からAPIに接続する場合のベースURL
# resonant_apiはDockerサービス名
BASE_URL = "http://resonant_api:8000"

# 注意: Dockerコンテナ外からアクセスする場合は http://localhost:8000
```

#### ST-API-001: ヘルスチェックエンドポイント

```python
@pytest.mark.asyncio
async def test_health_check():
    """ST-API-001: ヘルスチェック"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok" or "healthy" in str(data).lower()
```

---

## 8. エラー対処チェックリスト

### 8.1 パスワード認証エラー (password authentication failed)

**症状**: `password authentication failed for user "resonant"`

**対処手順**:

1. [ ] **まず確認**: 既存のテストは動作するか？
   ```bash
   docker exec resonant_dev pytest tests/bridge/ -v -k "test" --collect-only
   ```

2. [ ] **接続先の確認**: `localhost`ではなく`postgres`を使用しているか？
   - Docker内: `host='postgres'`
   - ローカル: `host='localhost'`

3. [ ] **db_poolフィクスチャを使用しているか？**
   - 独自の接続プールを作成していないか確認

4. [ ] **tests/system/conftest.pyを作成していないか？**
   - 存在する場合は削除

5. [ ] **環境変数の確認**:
   ```bash
   docker exec resonant_dev env | grep POSTGRES
   ```

**やってはいけないこと**:
- パスワードをハードコードする
- URLエンコードを試す
- pg_hba.confの変更を提案する

### 8.2 トリガーエラー

**症状**: `trigger function ... does not exist` または `column does not exist`

**対処手順**:

1. [ ] **トリガー関数の確認**:
   ```bash
   docker exec resonant_postgres psql -U resonant -d postgres -c "\df notify*"
   ```

2. [ ] **テーブル構造の確認**:
   ```bash
   docker exec resonant_postgres psql -U resonant -d postgres -c "\d intents"
   ```

3. [ ] **Sprint 10マイグレーション後の場合**: トリガー関数が`description`を参照している場合は、セクション4.4の修正を実行

**やってはいけないこと**:
- トリガーを無効化する
- カラムを削除する

### 8.3 テーブルが存在しないエラー

**症状**: `relation "xxx" does not exist`

**対処手順**:

1. [ ] **テーブル一覧確認**:
   ```bash
   docker exec resonant_postgres psql -U resonant -d postgres -c "\dt"
   ```

2. [ ] **必要なマイグレーションを特定**: セクション4.2の一覧を参照

3. [ ] **マイグレーション実行**: セクション4.3に従う

### 8.4 モジュールインポートエラー

**症状**: `ModuleNotFoundError: No module named 'xxx'`

**対処手順**:

1. [ ] **Docker内で実行しているか確認**
2. [ ] **PYTHONPATHの確認**:
   ```bash
   docker exec resonant_dev python -c "import sys; print(sys.path)"
   ```

3. [ ] **tests/conftest.pyがプロジェクトルートをpathに追加しているか確認**

### 8.5 テストが見つからない

**症状**: `no tests ran` または `collected 0 items`

**対処手順**:

1. [ ] **ファイル名が`test_`で始まっているか確認**
2. [ ] **関数名が`test_`で始まっているか確認**
3. [ ] **`pytest.mark.asyncio`デコレータがあるか確認**
4. [ ] **`__init__.py`が存在するか確認**

---

## 9. 合否判定基準

### 9.1 合格率の計算方法

```
合格率 = 合格したテスト数 / (必須テスト数 + 実行された条件付きテスト数)
```

**重要なルール**:
- **必須テスト**: スキップは許可されない。スキップした場合は「失敗」として計算
- **条件付きテスト**: 前提条件が満たされない場合はスキップ可能。分母から除外
- **スキップ ≠ 合格**: スキップされたテストは「未テスト」として報告書に明記

### 9.2 必須合格条件

| カテゴリ | 必須テスト数 | 条件付き | 必須合格率 | 備考 |
|---------|------------|---------|----------|------|
| ST-DB (データベース) | 3 | 2 | 100% | 基盤機能のため |
| ST-API (REST API) | 8 | 0 | 100% | 外部インターフェースのため |
| ST-BRIDGE (パイプライン) | 6 | 0 | 90% | コア機能のため |
| ST-AI (Claude API) | 5 | 0 | 80% | API依存のため許容 |
| ST-E2E (エンドツーエンド) | 3 | 0 | 100% | 統合動作確認のため |

**例**: ST-DBカテゴリの場合
- ST-DB-001, ST-DB-003, ST-DB-004: 必須（3件）
- ST-DB-002, ST-DB-005: 条件付き（2件）
- 必須3件がすべて合格 → **100%合格**（条件付きがスキップでも可）
- 必須3件のうち1件が失敗 → **66.7%合格**（不合格）

### 9.3 推奨合格条件

| カテゴリ | 推奨合格率 |
|---------|----------|
| ST-MEM (メモリシステム) | 90% |
| ST-CTX (Context Assembler) | 90% |
| ST-CONTRA (矛盾検出) | 90% |
| ST-RT (リアルタイム) | 80% |

### 9.4 総合判定

| 判定 | 条件 |
|-----|------|
| **合格** | 必須合格条件をすべて満たす |
| **条件付き合格** | 必須合格条件を満たし、推奨条件の70%以上を満たす |
| **不合格** | 必須合格条件を1つでも満たさない |

### 9.5 報告書の記載要件

テスト結果報告書には以下を明記すること：

```
ST-DBカテゴリ結果:
- 必須テスト: 3/3 合格 (100%)
- 条件付きテスト: 0/2 実行
  - ST-DB-002: スキップ（pgvector未インストール - Sprint 9マイグレーション未実行）
  - ST-DB-005: スキップ（semantic_memoriesテーブル未作成 - Sprint 9マイグレーション未実行）
- 判定: 合格（必須テスト100%達成）
- 推奨対応: Sprint 9マイグレーションを実行してpgvector機能を有効化
```

**スキップを「完了」と報告してはならない。**

---

## 付録A: クイックリファレンス

### テスト実行コマンド

```bash
# 全テスト実行（推奨）
docker exec resonant_dev pytest tests/system/ -v

# 特定カテゴリのみ
docker exec resonant_dev pytest tests/system/test_db_connection.py -v

# 詳細出力
docker exec resonant_dev pytest tests/system/ -v --tb=long

# 失敗テストのみ再実行
docker exec resonant_dev pytest tests/system/ --lf -v
```

### デバッグ用コマンド

```bash
# DB接続確認
docker exec resonant_dev python -c "
import asyncio, asyncpg
async def t():
    p = await asyncpg.create_pool(host='postgres', port=5432, user='resonant', password='password', database='postgres')
    async with p.acquire() as c:
        print(await c.fetchval('SELECT 1'))
    await p.close()
asyncio.run(t())
"

# テーブル一覧
docker exec resonant_postgres psql -U resonant -d postgres -c "\dt"

# pgvector拡張確認
docker exec resonant_postgres psql -U resonant -d postgres -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"

# 環境変数確認
docker exec resonant_dev env | grep -E "(POSTGRES|ANTHROPIC)"
```

### テストファイルテンプレート

```python
"""
tests/system/test_xxx.py

このファイルは tests/conftest.py の db_pool フィクスチャを使用します。
独自のconftest.pyを作成しないでください。
"""
import pytest

@pytest.mark.asyncio
async def test_example(db_pool):
    """テスト説明"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1
```

---

## 付録B: Sprint別マイグレーション詳細

### Sprint 1: 基本テーブル
- **ファイル**: `init.sql`
- **テーブル**: messages, specifications, intents, notifications
- **実行**: Docker起動時に自動実行

### Sprint 4: Intent通知
- **ファイル**: `002_intent_notify.sql`, `003_message_notify.sql`
- **内容**: LISTEN/NOTIFYトリガー

### Sprint 4.5: Claude Code統合
- **ファイル**: `004_claude_code_tables.sql`
- **テーブル**: claude_code_sessions, claude_code_executions

### Sprint 8: ユーザープロフィール
- **ファイル**: `005_user_profile_tables.sql`, `006_choice_points_initial.sql`
- **テーブル**: user_profiles, cognitive_traits, family_members, user_goals, resonant_concepts, choice_points

### Sprint 9: Memory Lifecycle（重要）
- **ファイル**: `006_memory_lifecycle_tables.sql`
- **内容**:
  - `CREATE EXTENSION IF NOT EXISTS vector;` (pgvector)
  - semantic_memories, memory_archive, memory_lifecycle_log

### Sprint 10: Choice Preservation & Intentsマイグレーション
- **ファイル**: `007_choice_preservation_completion.sql`, `008_intents_migration.sql`
- **内容**:
  - choice_points拡張
  - intentsテーブル: description→intent_text, result→outcome, processed_at→completed_at

### Sprint 11: 矛盾検出
- **ファイル**: `008_contradiction_detection.sql`
- **テーブル**: contradictions, intent_relations

---

**テスト仕様書作成者**: Claude Code
**最終更新**: 2025-11-23
**バージョン**: 3.0（マイグレーション手順追加版）
