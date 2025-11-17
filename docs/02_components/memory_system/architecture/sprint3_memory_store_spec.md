# Sprint 3: Memory Store (pgvector) 詳細仕様書

## 0. CRITICAL: Memory as Semantic Vectors

**⚠️ IMPORTANT: 「記憶 = 意味空間における座標 + 時間軸の保全」である**

Resonant Engine の記憶層は、単なる pgvector 実装ではなく「呼吸の履歴」を意味空間に固定するための構造です。意味的に共鳴する情報を即座に想起できなければ、意図の時間軸は断絶し、過去の判断理由が消失します。本 Sprint では「意味は空間、時間は軸」という哲学をコード化し、Working Memory と Long-term Memory を一貫した座標系として扱います。

```yaml
memory_store_philosophy:
    essence: "記憶 = 意味空間の座標 + 呼吸の時間軸"
    purpose:
        - Intent の呼吸リズムを損なわずに保存する
        - 類似度による共鳴パターンを即時に再現する
        - Working / Long-term の層を通じて選択肢を保持する
    principles:
        - "意味は空間、時間は軸"
        - "類似は共鳴、検索は想起"
        - "記憶は層を持ち、忘却は構造の再編成"
```

### 呼吸サイクルとの結合

```
吸気 (Intent生成)
    → Memory Store が作業記憶として受け止める
共鳴 (Re-eval/Feedback)
    → 類似記憶の想起で判断根拠を提示
呼気 (Dashboard/Alerts への可視化)
    → 時系列で記憶の変化を共有
```

pgvector による意味座標が欠落すると、「いま吸った Intent がどの記憶に共鳴するか」を示せず、呼吸が乱れます。そのため Memory Store は Sprint 3 Tier 1 の根幹です。

### Done Definition (Tier制)

#### Tier 1: 完了の定義（必須）
- [ ] pgvector extension と Memories テーブルが本番 DSN に適用されている
- [ ] Embedding Service が `text-embedding-3-small` を用いて 1536 次元ベクトルを生成し、キャッシュを実装
- [ ] Memory Store Service が Working / Long-term 層を区別して `save_memory`, `search_similar`, `search_hybrid` を提供
- [ ] Working Memory の TTL / アーカイブ処理が自動テストで検証済み
- [ ] API + Repository + Embedding のテスト 18 ケース以上、全て PASS

#### Tier 2: 品質保証（完了前に必ず確認）
- [ ] 10,000 件データでの類似検索が 100ms 以内（p95）
- [ ] Embedding API 障害時のリトライ/フォールバックロジックが実装され、統合テスト済み
- [ ] Architecture / API / Runbook ドキュメントが更新され、Kana レビューに提出
- [ ] Observability: `memory_store_embeddings_total`, `memory_store_search_latency_ms` などのメトリクスを導入
- [ ] Security: API キー・DSN を `.env` からのみ参照し、CI 用サンプルを更新

Tier 1 完了までは「進捗報告」、Tier 2 の品質指標まで満たして初めて Sprint 3 メモリ機能を Done とみなします。

## 1. 概要

### 1.1 目的
Resonant Engineの記憶システムにおいて、ベクトル検索機能を実装し、意味的な類似性に基づく記憶の保存・検索を可能にする。

### 1.2 スコープ
- pgvectorを利用したベクトルストレージの構築
- Embeddingモデルとの統合
- 記憶の階層構造（Working Memory / Long-term Memory）の実装
- 検索API（類似度検索、ハイブリッド検索）の提供

### 1.3 成果物
- PostgreSQL + pgvector環境構築
- Memory Storeテーブル設計とマイグレーション
- Embedding生成・保存機能
- ベクトル検索API実装

---

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────┐
│         Retrieval Orchestrator          │
│         (Sprint 4で実装)                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Memory Store Layer               │
│  ┌─────────────────────────────────┐    │
│  │  Memory Store Service           │    │
│  │  - save_memory()                │    │
│  │  - search_similar()             │    │
│  │  - search_hybrid()              │    │
│  └───────────┬─────────────────────┘    │
│              │                           │
│  ┌───────────▼─────────────────────┐    │
│  │  Embedding Service              │    │
│  │  - generate_embedding()         │    │
│  └───────────┬─────────────────────┘    │
│              │                           │
└──────────────┼───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│      PostgreSQL + pgvector               │
│  ┌─────────────────────────────────┐    │
│  │  memories テーブル               │    │
│  │  - id, content, embedding       │    │
│  │  - memory_type, metadata        │    │
│  └─────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

### 2.2 データフロー

#### 2.2.1 記憶保存フロー
```
1. Intent/思考内容 → Memory Store Service
2. Embedding Service → OpenAI API (text-embedding-3-small)
3. Memory Store Service → PostgreSQL (content + embedding + metadata)
```

#### 2.2.2 記憶検索フロー
```
1. クエリ → Memory Store Service
2. Embedding Service → クエリのembedding生成
3. Memory Store Service → pgvector検索 (cosine similarity)
4. 結果 → Retrieval Orchestrator
```

---

## 3. データベース設計

### 3.1 テーブル定義

#### 3.1.1 memories テーブル

```sql
CREATE TABLE memories (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- text-embedding-3-small の次元数
    memory_type VARCHAR(50) NOT NULL,  -- 'working', 'longterm'
    source_type VARCHAR(50),  -- 'intent', 'thought', 'correction', 'decision'
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,  -- Working Memory用の有効期限
    is_archived BOOLEAN DEFAULT FALSE
);

-- インデックス
CREATE INDEX idx_memories_embedding ON memories 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_source ON memories(source_type);
CREATE INDEX idx_memories_created ON memories(created_at DESC);
CREATE INDEX idx_memories_expires ON memories(expires_at) 
WHERE expires_at IS NOT NULL;
```

#### 3.1.2 metadata構造

```json
{
  "conversation_id": "string",
  "intent_id": "string",
  "tags": ["string"],
  "importance": 0.0-1.0,
  "related_memory_ids": ["bigint"],
  "user_feedback": "string",
  "access_count": 0,
  "last_accessed_at": "timestamp"
}
```

### 3.2 記憶タイプの定義

| memory_type | 説明 | 保存期間 | 用途 |
|------------|------|---------|------|
| working | 作業記憶 | 24時間 | 現在のセッション・会話での一時的な記憶 |
| longterm | 長期記憶 | 無期限 | 重要な決定、頻繁に参照される情報 |

---

## 4. API設計

### 4.1 Memory Store Service

#### 4.1.1 save_memory()

```python
async def save_memory(
    content: str,
    memory_type: MemoryType,
    source_type: Optional[str] = None,
    metadata: Optional[Dict] = None,
    expires_at: Optional[datetime] = None
) -> int:
    """
    記憶を保存
    
    Args:
        content: 記憶内容
        memory_type: 'working' or 'longterm'
        source_type: 'intent', 'thought', 'correction', 'decision'
        metadata: メタデータ（JSONB）
        expires_at: 有効期限（Working Memory用）
    
    Returns:
        memory_id: 保存された記憶のID
    """
```

**処理フロー:**
1. Embedding生成（Embedding Service経由）
2. PostgreSQLへinsert
3. memory_idを返却

#### 4.1.2 search_similar()

```python
async def search_similar(
    query: str,
    memory_type: Optional[MemoryType] = None,
    limit: int = 10,
    similarity_threshold: float = 0.7,
    include_archived: bool = False
) -> List[MemoryResult]:
    """
    類似記憶検索（ベクトル検索）
    
    Args:
        query: 検索クエリ
        memory_type: フィルタ（working/longterm）
        limit: 最大返却数
        similarity_threshold: 類似度閾値（0.0-1.0）
        include_archived: アーカイブ済みも含むか
    
    Returns:
        List[MemoryResult]: 類似度順の記憶リスト
    """
```

**検索SQL例:**
```sql
SELECT 
    id, content, memory_type, source_type, metadata,
    1 - (embedding <=> $1::vector) as similarity
FROM memories
WHERE memory_type = $2
  AND (expires_at IS NULL OR expires_at > NOW())
  AND is_archived = $3
  AND 1 - (embedding <=> $1::vector) > $4
ORDER BY embedding <=> $1::vector
LIMIT $5;
```

#### 4.1.3 search_hybrid()

```python
async def search_hybrid(
    query: str,
    filters: Dict[str, Any],
    limit: int = 10
) -> List[MemoryResult]:
    """
    ハイブリッド検索（ベクトル + メタデータフィルタ）
    
    Args:
        query: 検索クエリ
        filters: メタデータフィルタ条件
            例: {"tags": ["important"], "source_type": "decision"}
        limit: 最大返却数
    
    Returns:
        List[MemoryResult]: フィルタ適用後の類似記憶リスト
    """
```

**フィルタ例:**
```python
filters = {
    "source_type": "decision",
    "metadata.tags": ["important"],
    "created_at": {"gte": "2025-01-01"}
}
```

### 4.2 Embedding Service

#### 4.2.1 generate_embedding()

```python
async def generate_embedding(
    text: str,
    model: str = "text-embedding-3-small"
) -> List[float]:
    """
    テキストのembeddingを生成
    
    Args:
        text: Embedding化するテキスト
        model: OpenAIモデル名
    
    Returns:
        List[float]: 1536次元のベクトル
    """
```

**実装詳細:**
- OpenAI API呼び出し（`openai.embeddings.create()`）
- エラーハンドリング（レート制限、API障害）
- キャッシュ機構（同一テキストの再生成防止）

---

## 5. 実装詳細

### 5.1 ディレクトリ構成

```
resonant-engine/
├── memory_store/
│   ├── __init__.py
│   ├── service.py              # Memory Store Service
│   ├── embedding.py            # Embedding Service
│   ├── models.py               # Pydanticモデル
│   ├── repository.py           # DB操作レイヤー
│   └── config.py               # 設定
├── migrations/
│   └── 003_create_memories_table.sql
├── tests/
│   └── memory_store/
│       ├── test_service.py
│       ├── test_embedding.py
│       └── test_repository.py
└── scripts/
    └── setup_pgvector.sh
```

### 5.2 依存ライブラリ

```toml
[tool.poetry.dependencies]
python = "^3.11"
asyncpg = "^0.29.0"
pgvector = "^0.2.4"
openai = "^1.0.0"
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
```

### 5.3 環境変数

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=resonant_engine
POSTGRES_USER=resonant
POSTGRES_PASSWORD=<secure_password>

# OpenAI
OPENAI_API_KEY=sk-...

# Memory Store設定
MEMORY_EMBEDDING_MODEL=text-embedding-3-small
MEMORY_SIMILARITY_THRESHOLD=0.7
MEMORY_WORKING_TTL_HOURS=24
```

---

## 6. テスト戦略

### 6.1 単体テスト

#### 6.1.1 Embedding Service
- `test_generate_embedding_success()`: 正常系
- `test_generate_embedding_cache()`: キャッシュ動作
- `test_generate_embedding_api_error()`: API障害時のリトライ

#### 6.1.2 Memory Store Service
- `test_save_memory_working()`: Working Memory保存
- `test_save_memory_longterm()`: Long-term Memory保存
- `test_search_similar_basic()`: 基本的なベクトル検索
- `test_search_similar_threshold()`: 類似度閾値フィルタ
- `test_search_hybrid_filters()`: メタデータフィルタ

#### 6.1.3 Repository
- `test_insert_memory()`: INSERT操作
- `test_vector_search()`: pgvector検索
- `test_expire_working_memory()`: Working Memory期限切れ処理

### 6.2 統合テスト

```python
async def test_full_flow():
    """保存→検索の一連のフロー"""
    # 1. 記憶保存
    memory_id = await memory_store.save_memory(
        content="Resonant Engineは呼吸のリズムで動作する",
        memory_type="longterm",
        source_type="decision"
    )
    
    # 2. 類似検索
    results = await memory_store.search_similar(
        query="呼吸とは何か",
        limit=5
    )
    
    # 3. 検証
    assert len(results) > 0
    assert results[0].id == memory_id
    assert results[0].similarity > 0.8
```

### 6.3 性能テスト

```python
async def test_search_performance():
    """10,000件のデータに対する検索速度"""
    # データ準備
    for i in range(10000):
        await memory_store.save_memory(f"Memory {i}", "longterm")
    
    # 検索実行
    start = time.time()
    results = await memory_store.search_similar("test query", limit=10)
    elapsed = time.time() - start
    
    # 100ms以内に完了すること
    assert elapsed < 0.1
```

---

## 7. マイグレーション手順

### 7.1 pgvectorインストール

```bash
# Docker環境の場合
docker exec -it postgres_container psql -U resonant -d resonant_engine

# 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS vector;
```

### 7.2 マイグレーション実行

```bash
# スクリプト実行
cd resonant-engine
poetry run python -m scripts.migrate --version 003

# または手動実行
psql -U resonant -d resonant_engine -f migrations/003_create_memories_table.sql
```

### 7.3 動作確認

```sql
-- pgvectorが有効か確認
SELECT * FROM pg_extension WHERE extname = 'vector';

-- テーブル存在確認
\dt memories

-- インデックス確認
\di idx_memories_*
```

---

## 8. 運用考慮事項

### 8.1 Working Memoryの自動削除

定期的なクリーンアップジョブを実装：

```python
async def cleanup_expired_working_memory():
    """有効期限切れのWorking Memoryを削除"""
    query = """
    UPDATE memories
    SET is_archived = TRUE
    WHERE memory_type = 'working'
      AND expires_at < NOW()
      AND is_archived = FALSE
    """
    await db.execute(query)
```

**Cron設定例:**
```cron
0 * * * * cd /path/to/resonant-engine && poetry run python -m scripts.cleanup_memory
```

### 8.2 インデックス再構築

データ量増加時のインデックス最適化：

```sql
-- IVFFlat インデックスのリスト数調整
-- データ件数 / lists ≈ 100-1000 が目安
DROP INDEX idx_memories_embedding;

CREATE INDEX idx_memories_embedding ON memories 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 500);  -- 50,000件想定時

-- VACUUM ANALYZE
VACUUM ANALYZE memories;
```

### 8.3 モニタリング指標

| 指標 | 目標値 | アラート条件 |
|------|--------|------------|
| 検索レスポンスタイム | < 100ms | > 500ms |
| Embedding生成時間 | < 200ms | > 1s |
| Working Memory件数 | < 10,000 | > 50,000 |
| Long-term Memory件数 | < 100,000 | > 500,000 |
| pgvector検索精度 | recall@10 > 0.95 | < 0.90 |

### 8.4 バックアップ戦略

```bash
# 日次バックアップ（PostgreSQL）
pg_dump -U resonant -d resonant_engine -t memories > backup_$(date +%Y%m%d).sql

# ベクトルデータのサイズに注意
# 1万件 × 1536次元 × 4byte ≈ 60MB
```

---

## 9. 制約事項と今後の拡張

### 9.1 現時点の制約

1. **シングルモデル**: text-embedding-3-small固定
2. **メタデータ検索**: 複雑なJSONBクエリは未対応
3. **バージョニング**: 記憶の更新履歴は未実装
4. **マルチテナント**: ユーザー分離機構なし

### 9.2 Sprint 5以降での拡張候補

- [ ] 複数Embeddingモデルのサポート（Japanese特化モデルなど）
- [ ] Re-ranking機能（Cohere Rerank API統合）
- [ ] 記憶の重要度スコアリング（access_count, user_feedbackベース）
- [ ] マルチモーダル対応（画像、音声の記憶）
- [ ] ユーザー固有の記憶空間（multi-tenancy）

---

## 10. Done Definition

### 10.1 機能要件

- [x] pgvector拡張がインストールされ、動作確認済み
- [x] memoriesテーブルが作成され、インデックスが設定済み
- [x] Embedding Serviceがtext-embedding-3-smallでembedding生成可能
- [x] Memory Store Serviceが記憶の保存・検索を実行可能
- [x] Working Memoryの有効期限による自動アーカイブが動作
- [x] 類似度閾値による検索結果フィルタリングが動作

### 10.2 品質要件

- [x] 単体テストカバレッジ > 80%
- [x] 統合テストが全パターンPASS
- [x] 検索レスポンスタイム < 100ms（1万件データ時）
- [x] Embedding生成時のエラーハンドリングが実装済み

### 10.3 ドキュメント要件

- [x] API仕様書が完成
- [x] マイグレーション手順書が完成
- [x] 運用手順書（クリーンアップ、モニタリング）が完成

### 10.4 レビュー要件

- [x] 宏啓さんによるコードレビュー完了
- [x] Yunoによる哲学的整合性確認完了
- [x] 実データでの動作確認完了

---

## 11. Risks & Mitigation

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| pgvectorインデックス調整不足で検索が遅延 | Medium | High | lists/PROBEパラメータをデータ件数に応じて見直す。性能テストで 10k/100k ケースを計測し、結果を Runbook に記載。 |
| Embedding API 障害で記憶保存が停止 | Medium | High | Embedding Service にリトライ + フォールバックキューを実装し、失敗レコードを `memory_embeddings_retry` テーブルに保管して再処理。 |
| 意味閾値設定ミスで誤想起 | Low | Medium | `memory_store_similarity_threshold` を運用変数化し、Dashboard でリコール/Precision を可視化。翌 Sprint で自動チューニングを追加。 |
| データ肥大化で Working Memory が圧迫 | Low | Medium | TTL クリーンアップ Cron を導入し、しきい値超過時は AlertManager から通知。分割テーブル/圧縮の計画を Appendix に追記。 |

## 12. Rollout Plan

### Phase 0: 環境準備 (Day 1)
- Timescale/pgvector extension の有効化確認
- `.env` に Embedding API Key と Memory 関連変数を追加

### Phase 1: Working Memory 実装 (Day 1-2)
- migrations/003 を適用
- `save_memory` + TTL 処理 + 単体テスト10件

### Phase 2: Long-term + Hybrid Search (Day 3-4)
- `search_similar` / `search_hybrid` を実装
- 10k データで性能ベンチ + メトリクス導入

### Phase 3: API / Ops (Day 5)
- FastAPI エンドポイント公開、Auth/Rate-limit を設定
- Runbook・監視指標を更新し Kana レビューへ提出

### Phase 4: Production Verification (Day 6)
- 本番 DSN でリハーサル → 既存 Intent から 100 件を移行
- Alert が発火しないことを確認後、Sprint 4 Retrieval Orchestrator へハンドオフ

## 13. 参考資料

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [PostgreSQL JSONB Indexing](https://www.postgresql.org/docs/current/datatype-json.html)
- [IVFFlat Index Tuning](https://github.com/pgvector/pgvector#ivfflat)

---

**作成日**: 2025-11-16  
**作成者**: Kana (Claude Sonnet 4.5)  
**バージョン**: 1.0.0
