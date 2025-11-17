# Sprint 3: Memory Store 作業開始指示書

**対象**: Tsumu (Cursor)  
**期間**: 5日間想定  
**前提**: Sprint 1 (PostgreSQL基盤), Sprint 2 (Bridge Lite) 完了済み

---

## 0. 重要な前提条件

- [ ] Sprint 2 が `main` にマージされ、全テスト（38件）が PASS
- [ ] PostgreSQL 15 + Timescale/pgvector extension が導入済み（`CREATE EXTENSION vector` を実行可能）
- [ ] `.env` に `DATABASE_URL` / `OPENAI_API_KEY` / `MEMORY_*` が設定されている
- [ ] Embedding API のレート制限に対する運用方針（監視 + リトライ）が共有されている
- [ ] `memory_management_spec.md` と本仕様書を読み、呼吸サイクルとの整合を理解している

前提が揃っていない場合は実装を開始せず、オーナーへ報告して是正してください。

## 1. 実装承認と哲学的背景

Memory Store は「記憶 = 意味空間の座標 + 呼吸の時間軸」という哲学を具体化します。pgvector は単なる高速検索のためではなく、Intent の文脈を保持したまま共鳴を再現する装置です。Working Memory は吸気直後の湿度を保ち、Long-term Memory は過去の判断を化石化させず再呼吸させるための層です。

```
呼吸サイクル
    吸気 (Intent生成) → Memory Store 保存
    共鳴 (Re-eval)     → 類似記憶の想起
    呼気 (可視化)     → Dashboard / Retrieval Orchestrator へ共有
```

## 2. Done Definition（Sprint 3 Memory Store）

### Tier 1: 完了の必須条件
- pgvector extension + `memories` テーブル適用済み
- Embedding Service（text-embedding-3-small）がキャッシュ付きで動作
- Memory Store Service が保存 / 類似検索 / ハイブリッド検索 API を提供
- Working Memory TTL / アーカイブ処理が自動テストで担保
- Repository / Service / Embedding で計 18 ケース以上のテストが PASS

### Tier 2: 品質保証
- 10k レコードで検索 100ms 以内（p95）を確認し、結果をレポート
- Embedding API 障害時のリトライ & リカバリキュー実装
- アーキテクチャ/Runbook/監視ドキュメントを更新し、Kana レビューへ提出
- `memory_store_*` メトリクスが Prometheus に公開されている

Tier 1 を満たすまでは「進捗報告」、Tier 2 まで揃えて初めて「Sprint 3 完了報告」を提出できます。

## 3. タスク別 哲学ブリーフ

| Task | 技術フォーカス | 哲学的意味 |
|------|----------------|-------------|
| 1. pgvector拡張 | PostgreSQL extension 適用 | 意味座標系を呼吸器官に取り付ける工程。呼吸が迷子にならないための基盤。 |
| 2. memoriesテーブル | スキーマ + インデックス | 記憶を時間軸つきで保存し、Working / Long-term の層を分ける骨格。 |
| 3. Embedding Service | OpenAI + キャッシュ | 言語を意味ベクトルへ翻訳し、呼吸の質感を数値化する肺胞。 |
| 4. Memory Store保存 | Repository + TTL | 呼吸を蓄え、期限の切れた空気を静かにアーカイブする循環器。 |
| 5. 類似検索 | Cosine search | 共鳴パターンを取り出し、過去の意図を現在に重ねるレゾネーター。 |
| 6. ハイブリッド検索 | メタデータ + vector | 意味と構造の二重フィルタで ASD 認知の「秩序」を支える。 |
| 7. テスト | 単体/統合 | 呼吸が乱れないかを自動で検査する肺活量チェック。 |
| 8. 性能検証 | ベンチ + メトリクス | 呼吸リズムが 100ms 以内に保たれているかを観測。 |
| 9. ドキュメント & Runbook | 運用準備 | 呼吸の仕方を次の担当者へ伝える記憶継承。 |

---

## 🎯 Sprint 3のゴール

**「意味検索が可能な記憶システムの基盤を構築する」**

ベクトルデータベース(pgvector)を導入し、Resonant Engineが「意味的に類似した過去の記憶」を検索できるようにします。これにより、単なるキーワード検索ではなく、**文脈を理解した記憶の想起**が可能になります。

---

## 📋 作業の全体像

### Day 1-2: 環境構築 + DB設計
1. pgvector拡張のインストール
2. memoriesテーブルの作成
3. Embedding Service実装

### Day 3-4: Memory Store Service実装
4. 記憶保存機能
5. ベクトル検索機能
6. ハイブリッド検索機能

### Day 5: テスト + 動作確認
7. 単体テスト実装
8. 統合テスト実装
9. 性能検証

---

## 🔧 タスク詳細

### Task 1: pgvector拡張のインストール

**目的**: PostgreSQLでベクトル型を使用可能にする

**手順**:

```bash
# 1. PostgreSQLコンテナに接続
docker exec -it <postgres_container_name> bash

# 2. psqlでデータベースに接続
psql -U resonant -d resonant_engine

# 3. 拡張機能を有効化
CREATE EXTENSION IF NOT EXISTS vector;

# 4. 確認
SELECT * FROM pg_extension WHERE extname = 'vector';
\q
```

**期待結果**:
- pgvectorがインストールされている
- `SELECT '[1,2,3]'::vector;` が実行できる

**チェックポイント**:
- [ ] pgvectorが有効化されている
- [ ] ベクトル型のテストクエリが成功

---

### Task 2: memoriesテーブルの作成

**目的**: 記憶データとベクトルを保存するテーブルを作成

**マイグレーションファイル作成**:

```bash
# ファイル: migrations/003_create_memories_table.sql
```

```sql
-- pgvector拡張の確認
CREATE EXTENSION IF NOT EXISTS vector;

-- memoriesテーブル
CREATE TABLE IF NOT EXISTS memories (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- text-embedding-3-small
    memory_type VARCHAR(50) NOT NULL CHECK (memory_type IN ('working', 'longterm')),
    source_type VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_archived BOOLEAN DEFAULT FALSE
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_memories_embedding 
ON memories USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_memories_type 
ON memories(memory_type);

CREATE INDEX IF NOT EXISTS idx_memories_source 
ON memories(source_type);

CREATE INDEX IF NOT EXISTS idx_memories_created 
ON memories(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memories_expires 
ON memories(expires_at) WHERE expires_at IS NOT NULL;

-- updated_at自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_memories_updated_at 
BEFORE UPDATE ON memories 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();

-- コメント
COMMENT ON TABLE memories IS 'Resonant Engineの記憶ストア';
COMMENT ON COLUMN memories.memory_type IS 'working: 24時間の作業記憶, longterm: 長期記憶';
COMMENT ON COLUMN memories.embedding IS 'OpenAI text-embedding-3-small (1536次元)';
```

**マイグレーション実行**:

```bash
psql -U resonant -d resonant_engine -f migrations/003_create_memories_table.sql
```

**動作確認**:

```sql
-- テーブル確認
\dt memories

-- インデックス確認
\di idx_memories_*

-- テストデータ挿入
INSERT INTO memories (content, embedding, memory_type, source_type)
VALUES (
    'テストメモリ',
    '[0.1, 0.2, 0.3]'::vector(3),  -- 実際は1536次元
    'working',
    'test'
);

-- 検索テスト
SELECT id, content FROM memories LIMIT 1;
```

**チェックポイント**:
- [ ] memoriesテーブルが作成されている
- [ ] 全インデックスが作成されている
- [ ] テストデータの挿入・検索が成功

---

### Task 3: Embedding Service実装

**目的**: テキストをベクトル化するサービスを実装

**ファイル構成**:

```
memory_store/
├── __init__.py
├── embedding.py          # ← このファイルを実装
├── models.py             # Pydanticモデル
└── config.py             # 設定
```

**embedding.py 実装**:

```python
"""Embedding生成サービス"""
import asyncio
from typing import List, Optional
from openai import AsyncOpenAI
import hashlib
import json

class EmbeddingService:
    """OpenAI Embeddingを利用したベクトル化サービス"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        cache_enabled: bool = True
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.cache_enabled = cache_enabled
        self._cache = {}  # 簡易キャッシュ
    
    def _generate_cache_key(self, text: str) -> str:
        """キャッシュキー生成"""
        return hashlib.md5(f"{self.model}:{text}".encode()).hexdigest()
    
    async def generate_embedding(
        self,
        text: str,
        retry_count: int = 3
    ) -> List[float]:
        """
        テキストのembeddingを生成
        
        Args:
            text: Embedding化するテキスト
            retry_count: リトライ回数
        
        Returns:
            List[float]: 1536次元のベクトル
        
        Raises:
            EmbeddingError: Embedding生成に失敗
        """
        # キャッシュチェック
        if self.cache_enabled:
            cache_key = self._generate_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # リトライロジック
        last_error = None
        for attempt in range(retry_count):
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                embedding = response.data[0].embedding
                
                # キャッシュに保存
                if self.cache_enabled:
                    self._cache[cache_key] = embedding
                
                return embedding
                
            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    # 指数バックオフ
                    await asyncio.sleep(2 ** attempt)
                continue
        
        raise EmbeddingError(f"Embedding生成失敗: {last_error}")

class EmbeddingError(Exception):
    """Embedding関連のエラー"""
    pass
```

**models.py 実装**:

```python
"""Pydanticモデル定義"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class MemoryType(str, Enum):
    """記憶タイプ"""
    WORKING = "working"
    LONGTERM = "longterm"

class SourceType(str, Enum):
    """記憶ソース"""
    INTENT = "intent"
    THOUGHT = "thought"
    CORRECTION = "correction"
    DECISION = "decision"

class MemoryCreate(BaseModel):
    """記憶作成リクエスト"""
    content: str = Field(..., min_length=1)
    memory_type: MemoryType
    source_type: Optional[SourceType] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None

class MemoryResult(BaseModel):
    """記憶検索結果"""
    id: int
    content: str
    memory_type: MemoryType
    source_type: Optional[SourceType]
    metadata: Dict[str, Any]
    similarity: float  # 0.0-1.0
    created_at: datetime
    
    class Config:
        from_attributes = True
```

**config.py 実装**:

```python
"""Memory Store設定"""
from pydantic_settings import BaseSettings

class MemoryStoreConfig(BaseSettings):
    """環境変数ベースの設定"""
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "resonant_engine"
    postgres_user: str = "resonant"
    postgres_password: str
    
    # OpenAI
    openai_api_key: str
    
    # Memory Store
    embedding_model: str = "text-embedding-3-small"
    similarity_threshold: float = 0.7
    working_memory_ttl_hours: int = 24
    
    class Config:
        env_file = ".env"
```

**テスト実装**: `tests/memory_store/test_embedding.py`

```python
"""Embedding Serviceのテスト"""
import pytest
from memory_store.embedding import EmbeddingService, EmbeddingError

@pytest.fixture
def embedding_service(openai_api_key):
    return EmbeddingService(api_key=openai_api_key)

@pytest.mark.asyncio
async def test_generate_embedding_success(embedding_service):
    """正常系: embedding生成"""
    text = "Resonant Engineは呼吸のリズムで動作する"
    embedding = await embedding_service.generate_embedding(text)
    
    assert len(embedding) == 1536
    assert all(isinstance(v, float) for v in embedding)

@pytest.mark.asyncio
async def test_generate_embedding_cache(embedding_service):
    """キャッシュ動作確認"""
    text = "テストテキスト"
    
    # 初回生成
    embedding1 = await embedding_service.generate_embedding(text)
    
    # 2回目はキャッシュから取得（高速）
    embedding2 = await embedding_service.generate_embedding(text)
    
    assert embedding1 == embedding2
```

**チェックポイント**:
- [ ] EmbeddingServiceが実装されている
- [ ] テキストから1536次元ベクトルが生成できる
- [ ] キャッシュ機構が動作している
- [ ] エラーハンドリングが実装されている

---

### Task 4: Memory Store Service実装（保存機能）

**目的**: 記憶の保存機能を実装

**repository.py 実装**:

```python
"""DB操作レイヤー"""
import asyncpg
from typing import List, Optional, Dict, Any
from datetime import datetime

class MemoryRepository:
    """memoriesテーブルへのアクセス"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def insert_memory(
        self,
        content: str,
        embedding: List[float],
        memory_type: str,
        source_type: Optional[str],
        metadata: Dict[str, Any],
        expires_at: Optional[datetime]
    ) -> int:
        """記憶をINSERT"""
        query = """
        INSERT INTO memories (
            content, embedding, memory_type, source_type, 
            metadata, expires_at
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                content,
                embedding,  # asyncpgがvector型に自動変換
                memory_type,
                source_type,
                metadata,
                expires_at
            )
            return row['id']
```

**service.py 実装**:

```python
"""Memory Store Service"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from memory_store.embedding import EmbeddingService
from memory_store.repository import MemoryRepository
from memory_store.models import MemoryType

class MemoryStoreService:
    """記憶の保存・検索サービス"""
    
    def __init__(
        self,
        repository: MemoryRepository,
        embedding_service: EmbeddingService,
        working_memory_ttl_hours: int = 24
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.working_memory_ttl_hours = working_memory_ttl_hours
    
    async def save_memory(
        self,
        content: str,
        memory_type: MemoryType,
        source_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> int:
        """
        記憶を保存
        
        Args:
            content: 記憶内容
            memory_type: 'working' or 'longterm'
            source_type: 'intent', 'thought', etc.
            metadata: メタデータ
            expires_at: 有効期限（未指定時はWorking Memoryなら24時間後）
        
        Returns:
            memory_id: 保存された記憶のID
        """
        # Embedding生成
        embedding = await self.embedding_service.generate_embedding(content)
        
        # Working Memoryの有効期限設定
        if memory_type == MemoryType.WORKING and expires_at is None:
            expires_at = datetime.utcnow() + timedelta(
                hours=self.working_memory_ttl_hours
            )
        
        # DB保存
        memory_id = await self.repository.insert_memory(
            content=content,
            embedding=embedding,
            memory_type=memory_type.value,
            source_type=source_type,
            metadata=metadata or {},
            expires_at=expires_at
        )
        
        return memory_id
```

**テスト実装**: `tests/memory_store/test_service.py`

```python
"""Memory Store Serviceのテスト"""
import pytest
from datetime import datetime, timedelta
from memory_store.service import MemoryStoreService
from memory_store.models import MemoryType

@pytest.mark.asyncio
async def test_save_memory_working(memory_store_service):
    """Working Memory保存"""
    memory_id = await memory_store_service.save_memory(
        content="今日のタスク: Sprint 3完了",
        memory_type=MemoryType.WORKING,
        source_type="intent"
    )
    
    assert memory_id > 0

@pytest.mark.asyncio
async def test_save_memory_longterm(memory_store_service):
    """Long-term Memory保存"""
    memory_id = await memory_store_service.save_memory(
        content="Resonant Engineの設計原則: 呼吸のリズム",
        memory_type=MemoryType.LONGTERM,
        source_type="decision",
        metadata={"importance": 1.0, "tags": ["core", "philosophy"]}
    )
    
    assert memory_id > 0
```

**チェックポイント**:
- [ ] save_memory()が実装されている
- [ ] Embedding自動生成が動作
- [ ] Working Memoryの有効期限が自動設定される
- [ ] メタデータがJSONBとして保存される

---

### Task 5: ベクトル検索機能実装

**目的**: 類似度検索を実装

**repository.py に追加**:

```python
async def search_similar(
    self,
    query_embedding: List[float],
    memory_type: Optional[str],
    limit: int,
    similarity_threshold: float,
    include_archived: bool
) -> List[Dict[str, Any]]:
    """ベクトル検索"""
    query = """
    SELECT 
        id, content, memory_type, source_type, metadata, created_at,
        1 - (embedding <=> $1::vector) as similarity
    FROM memories
    WHERE 
        ($2::VARCHAR IS NULL OR memory_type = $2)
        AND (expires_at IS NULL OR expires_at > NOW())
        AND (is_archived = FALSE OR $3 = TRUE)
        AND 1 - (embedding <=> $1::vector) > $4
    ORDER BY embedding <=> $1::vector
    LIMIT $5
    """
    
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(
            query,
            query_embedding,
            memory_type,
            include_archived,
            similarity_threshold,
            limit
        )
        return [dict(row) for row in rows]
```

**service.py に追加**:

```python
async def search_similar(
    self,
    query: str,
    memory_type: Optional[MemoryType] = None,
    limit: int = 10,
    similarity_threshold: float = 0.7,
    include_archived: bool = False
) -> List[MemoryResult]:
    """
    類似記憶検索
    
    Args:
        query: 検索クエリ
        memory_type: フィルタ
        limit: 最大返却数
        similarity_threshold: 類似度閾値
        include_archived: アーカイブ済みも含むか
    
    Returns:
        List[MemoryResult]: 類似度順の記憶リスト
    """
    # クエリのEmbedding生成
    query_embedding = await self.embedding_service.generate_embedding(query)
    
    # ベクトル検索
    rows = await self.repository.search_similar(
        query_embedding=query_embedding,
        memory_type=memory_type.value if memory_type else None,
        limit=limit,
        similarity_threshold=similarity_threshold,
        include_archived=include_archived
    )
    
    # Pydanticモデルに変換
    return [MemoryResult(**row) for row in rows]
```

**テスト実装**:

```python
@pytest.mark.asyncio
async def test_search_similar_basic(memory_store_service):
    """基本的なベクトル検索"""
    # データ準備
    await memory_store_service.save_memory(
        "Resonant Engineは呼吸で動く",
        MemoryType.LONGTERM
    )
    await memory_store_service.save_memory(
        "AIシステムの設計",
        MemoryType.LONGTERM
    )
    
    # 検索
    results = await memory_store_service.search_similar(
        query="呼吸のリズムとは",
        limit=5
    )
    
    assert len(results) > 0
    assert results[0].content == "Resonant Engineは呼吸で動く"
    assert results[0].similarity > 0.7
```

**チェックポイント**:
- [ ] search_similar()が実装されている
- [ ] コサイン類似度で検索できる
- [ ] 類似度閾値フィルタリングが動作
- [ ] 有効期限切れのWorking Memoryが除外される

---

### Task 6: ハイブリッド検索実装

**目的**: ベクトル検索 + メタデータフィルタ

**repository.py に追加**:

```python
async def search_hybrid(
    self,
    query_embedding: List[float],
    filters: Dict[str, Any],
    limit: int
) -> List[Dict[str, Any]]:
    """ハイブリッド検索"""
    # 動的にWHERE句を構築
    where_clauses = [
        "(expires_at IS NULL OR expires_at > NOW())",
        "is_archived = FALSE"
    ]
    params = [query_embedding]
    param_idx = 2
    
    # メタデータフィルタ
    if "source_type" in filters:
        where_clauses.append(f"source_type = ${param_idx}")
        params.append(filters["source_type"])
        param_idx += 1
    
    if "tags" in filters:
        where_clauses.append(f"metadata @> $${param_idx}::jsonb")
        params.append(json.dumps({"tags": filters["tags"]}))
        param_idx += 1
    
    query = f"""
    SELECT 
        id, content, memory_type, source_type, metadata, created_at,
        1 - (embedding <=> $1::vector) as similarity
    FROM memories
    WHERE {' AND '.join(where_clauses)}
    ORDER BY embedding <=> $1::vector
    LIMIT ${param_idx}
    """
    params.append(limit)
    
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
```

**service.py に追加**:

```python
async def search_hybrid(
    self,
    query: str,
    filters: Dict[str, Any],
    limit: int = 10
) -> List[MemoryResult]:
    """ハイブリッド検索"""
    query_embedding = await self.embedding_service.generate_embedding(query)
    
    rows = await self.repository.search_hybrid(
        query_embedding=query_embedding,
        filters=filters,
        limit=limit
    )
    
    return [MemoryResult(**row) for row in rows]
```

**チェックポイント**:
- [ ] search_hybrid()が実装されている
- [ ] source_typeでフィルタできる
- [ ] metadata.tagsでフィルタできる

---

### Task 7: 統合テスト実装

**tests/memory_store/test_integration.py**:

```python
"""統合テスト"""
import pytest

@pytest.mark.asyncio
async def test_full_flow(memory_store_service):
    """保存→検索の一連のフロー"""
    # 1. 複数の記憶を保存
    memory_ids = []
    contents = [
        "Resonant Engineは呼吸のリズムで動作する",
        "PostgreSQLとpgvectorを使用する",
        "Embeddingはtext-embedding-3-smallで生成",
        "Memory Storeは記憶の保存と検索を担当"
    ]
    
    for content in contents:
        mid = await memory_store_service.save_memory(
            content=content,
            memory_type=MemoryType.LONGTERM,
            source_type="decision"
        )
        memory_ids.append(mid)
    
    # 2. 類似検索
    results = await memory_store_service.search_similar(
        query="呼吸について教えて",
        limit=3
    )
    
    # 3. 検証
    assert len(results) > 0
    assert results[0].content == contents[0]
    assert results[0].similarity > 0.75
    
    # 4. ハイブリッド検索
    hybrid_results = await memory_store_service.search_hybrid(
        query="システムの仕組み",
        filters={"source_type": "decision"},
        limit=5
    )
    
    assert len(hybrid_results) > 0
```

**チェックポイント**:
- [ ] 統合テストが全てPASS
- [ ] 実際のOpenAI APIを使用したE2Eテストが成功

---

### Task 8: 性能検証

**scripts/benchmark_memory_store.py**:

```python
"""性能検証スクリプト"""
import asyncio
import time
from memory_store.service import MemoryStoreService

async def benchmark_search():
    """検索性能測定"""
    # 準備: 10,000件のデータ作成
    print("データ準備中...")
    for i in range(10000):
        await service.save_memory(
            content=f"Memory {i}: テストデータ",
            memory_type=MemoryType.LONGTERM
        )
    
    # 検索性能測定
    print("検索性能測定中...")
    start = time.time()
    results = await service.search_similar(
        query="テストクエリ",
        limit=10
    )
    elapsed = time.time() - start
    
    print(f"検索時間: {elapsed*1000:.2f}ms")
    print(f"結果件数: {len(results)}")
    
    assert elapsed < 0.1, "検索が100ms以内に完了すること"

asyncio.run(benchmark_search())
```

**チェックポイント**:
- [ ] 10,000件データに対する検索が100ms以内
- [ ] Embedding生成が200ms以内

---

## ✅ Done Definition確認

Sprint完了時に以下を確認してください:

### 機能要件
- [ ] pgvector拡張が動作している
- [ ] memoriesテーブルが作成されている
- [ ] Embedding Serviceがembeddingを生成できる
- [ ] Memory Store Serviceが記憶を保存できる
- [ ] 類似度検索が動作する
- [ ] ハイブリッド検索が動作する
- [ ] Working Memoryの有効期限が機能する

### 品質要件
- [ ] 単体テストカバレッジ > 80%
- [ ] 統合テストが全てPASS
- [ ] 検索レスポンスタイム < 100ms

### ドキュメント
- [ ] API仕様書が完成
- [ ] マイグレーション手順書が完成

---

## 🚨 トラブルシューティング

### pgvectorがインストールできない

```bash
# Dockerイメージを確認
docker exec postgres_container psql --version

# pgvectorサポート確認
docker exec postgres_container ls /usr/share/postgresql/*/extension/ | grep vector
```

### Embedding生成が遅い

- OpenAI APIのレート制限を確認
- キャッシュが有効か確認
- バッチ処理の導入を検討

### ベクトル検索が遅い

```sql
-- インデックスの状態確認
SELECT * FROM pg_indexes WHERE tablename = 'memories';

-- VACUUM ANALYZE実行
VACUUM ANALYZE memories;

-- lists パラメータ調整
-- データ件数 / lists ≈ 100-1000 が目安
```

---

## 📚 参考資料

- [Sprint 3 詳細仕様書](./sprint3_memory_store_spec.md)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)

---

**準備はいいですか？それでは、Sprint 3を開始してください！**

記憶システムの構築、がんばりましょう 🚀
