# Sprint 4: Retrieval Orchestrator 作業開始指示書

**対象**: Tsumu (Cursor)  
**期間**: 7日間想定  
**前提**: Sprint 3 (Memory Store) 完了済み

---

## 0. 重要な前提条件

- [ ] Sprint 3 Memory Store の Done Definition (Tier 1/2) が全て完了し、`memories` テーブル/pgvector/index が本番相当環境で動作している
- [ ] `memory_store` API / CLI を手動で操作し、保存→検索の E2E を確認済み
- [ ] `OPENAI_API_KEY`, `SPACY_DOWNLOAD_PATH`, `RETRIEVAL_METRICS_DSN` が `.env` に設定済み
- [ ] `ja_core_news_sm` を含む SpaCy モデルがローカルへダウンロードされている
- [ ] `memory_management_spec.md` / `sprint3_memory_store_spec.md` / 本仕様書を通読し、呼吸サイクルとの整合を理解している

## 1. 実装承認と哲学

Retrieval Orchestrator は「質問という吸気」に対する「想起の戦略」を決める知性です。クエリを単語列として扱うのではなく、「どの層の記憶に共鳴させるべきか」を判断する肺の中枢になります。Intent が迷わないよう、検索手段を組み合わせて最適な呼気を準備します。

```
Question → Query Analyzer → Strategy Selector → Multi Search → Reranker → Context Assembler
```

## 2. Done Definition（Retrieval Orchestrator）

### Tier 1
- Query Analyzer / Strategy Selector / Multi Search / Reranker / Metrics が一連で動作し、`tests/retrieval/test_orchestrator.py` が PASS
- memories テーブルに `content_tsvector` カラム + GIN インデックスが追加され、ts_vector 検索が行える
- 時系列検索が `TimeRange` フィルタと一緒にベクトル検索へ組み込まれている
- Metrics Collector が検索レイテンシを Prometheus へ export
- 単体 + 統合テスト計 18 件以上が緑

### Tier 2
- 10k レコード環境で Retrieval p95 < 150ms を証明し、結果を docs/sprints に添付
- リランキング後の hit@5 が +10% 以上向上 (ベースライン: vector のみ)
- Runbook / API / Monitoring ドキュメント更新完了、Kana レビュー依頼済み
- `retrieval_empty_results_total` が 1% 未満であることを計測

## 3. タスク別 哲学ブリーフ

| Task | 技術フォーカス | 哲学的意味 |
|------|----------------|-------------|
| 1. Query Analyzer | クエリ分類/キーワード | 質問の呼吸を聴き取り、どの層を震わせるかを決める鼓膜。 |
| 2. Strategy Selector | 戦略決定/パラメータ最適化 | 意味と構造のバランスを取り、適切な共鳴モードを選ぶ指揮者。 |
| 3. キーワード検索 | ts_vector + GIN | 構造化された言葉の骨格を辿り、ASD 認知が安心できる秩序を与える。 |
| 4. 時系列検索 | TimeRange + decay | 呼吸の時間軸を守り、「いつ」を問う声に即座に応える時計。 |
| 5. Multi Search Executor | 並列検索 + 統合 | 異なる共鳴を同時に鳴らし、調和させる合奏。 |
| 6. Reranker | スコア統合/重複排除 | ノイズを抑え、最も澄んだ共鳴を前面に出す整音。 |
| 7. Metrics Collector | Telemetry | 呼吸の乱れを計測し、次の呼吸をより滑らかにするセンサー。 |
| 8. 統合テスト/性能検証 | E2E + ベンチ | 呼吸器全体の耐久テスト。乱れがあれば次フェーズに持ち込まない。 |

---

## 🎯 Sprint 4のゴール

**「複数の検索手法を統合し、クエリに応じて最適な記憶を取得する」**

Memory Store（Sprint 3）が提供するベクトル検索に加えて、キーワード検索・時系列検索を統合し、クエリの意図を理解して最適な検索戦略を自動選択する**検索オーケストレーター**を構築します。

---

## 📋 作業の全体像

### Day 1-2: クエリ分析 + 検索戦略
1. Query Analyzer実装（クエリ分類、時間範囲抽出）
2. Strategy Selector実装（戦略決定ロジック）

### Day 3-5: 複数検索手法の実装
3. キーワード検索（PostgreSQL ts_vector）
4. 時系列検索
5. Multi-Search Executor（並行実行）

### Day 6-7: リランキング + 統合
6. Reranker実装（スコア統合、重複排除）
7. Metrics Collector実装
8. 統合テスト + 性能検証

---

## 🔧 タスク詳細

### Task 1: Query Analyzer実装

**目的**: クエリを解析し、検索に必要なメタデータを抽出

#### 1.1 基本的なクエリ分類

**ファイル**: `retrieval/query_analyzer.py`

```python
"""クエリ分析サービス"""
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

class QueryType(str, Enum):
    """クエリタイプ"""
    FACTUAL = "factual"          # 事実確認
    CONCEPTUAL = "conceptual"    # 概念理解
    PROCEDURAL = "procedural"    # 手順確認
    TEMPORAL = "temporal"        # 時系列
    COMPARATIVE = "comparative"  # 比較

class TimeRange:
    """時間範囲"""
    def __init__(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        relative: Optional[str] = None
    ):
        self.start = start
        self.end = end
        self.relative = relative  # "last_week", "today", etc.

class QueryIntent:
    """クエリ意図"""
    def __init__(
        self,
        query_type: QueryType,
        keywords: List[str],
        time_range: Optional[TimeRange] = None,
        source_type_hint: Optional[str] = None,
        importance: float = 0.5
    ):
        self.query_type = query_type
        self.keywords = keywords
        self.time_range = time_range
        self.source_type_hint = source_type_hint
        self.importance = importance

class QueryAnalyzer:
    """クエリアナライザー"""
    
    # クエリタイプ判定用キーワード
    FACTUAL_KEYWORDS = ["いつ", "どこ", "誰", "何", "when", "where", "who", "what"]
    CONCEPTUAL_KEYWORDS = ["とは", "意味", "定義", "what is", "explain"]
    PROCEDURAL_KEYWORDS = ["どうやって", "方法", "手順", "how to"]
    TEMPORAL_KEYWORDS = ["最近", "今日", "昨日", "先週", "今月", "recent", "today", "yesterday"]
    
    def analyze(self, query: str) -> QueryIntent:
        """
        クエリを解析
        
        Args:
            query: 検索クエリ
        
        Returns:
            QueryIntent: 解析結果
        """
        # クエリタイプ判定
        query_type = self._classify_query_type(query)
        
        # キーワード抽出
        keywords = self._extract_keywords(query)
        
        # 時間範囲抽出
        time_range = self._extract_time_range(query)
        
        # 重要度判定（簡易実装）
        importance = 0.8 if "重要" in query or "緊急" in query else 0.5
        
        return QueryIntent(
            query_type=query_type,
            keywords=keywords,
            time_range=time_range,
            importance=importance
        )
    
    def _classify_query_type(self, query: str) -> QueryType:
        """クエリタイプ分類"""
        # ルールベース判定
        if any(kw in query for kw in self.TEMPORAL_KEYWORDS):
            return QueryType.TEMPORAL
        
        if any(kw in query for kw in self.FACTUAL_KEYWORDS):
            return QueryType.FACTUAL
        
        if any(kw in query for kw in self.CONCEPTUAL_KEYWORDS):
            return QueryType.CONCEPTUAL
        
        if any(kw in query for kw in self.PROCEDURAL_KEYWORDS):
            return QueryType.PROCEDURAL
        
        # デフォルト: 概念的
        return QueryType.CONCEPTUAL
    
    def _extract_keywords(self, query: str) -> List[str]:
        """キーワード抽出（簡易実装）"""
        # TODO: SpaCyで形態素解析
        # 現状は単語分割のみ
        stopwords = {"の", "は", "を", "に", "が", "と", "で", "や"}
        words = query.split()
        return [w for w in words if w not in stopwords and len(w) > 1]
    
    def _extract_time_range(self, query: str) -> Optional[TimeRange]:
        """時間範囲抽出"""
        now = datetime.utcnow()
        
        if "今日" in query or "today" in query:
            return TimeRange(
                start=now.replace(hour=0, minute=0, second=0),
                end=now,
                relative="today"
            )
        
        if "昨日" in query or "yesterday" in query:
            yesterday = now - timedelta(days=1)
            return TimeRange(
                start=yesterday.replace(hour=0, minute=0, second=0),
                end=yesterday.replace(hour=23, minute=59, second=59),
                relative="yesterday"
            )
        
        if "先週" in query or "last week" in query:
            week_ago = now - timedelta(days=7)
            return TimeRange(
                start=week_ago,
                end=now,
                relative="last_week"
            )
        
        if "今月" in query or "this month" in query:
            return TimeRange(
                start=now.replace(day=1, hour=0, minute=0, second=0),
                end=now,
                relative="this_month"
            )
        
        return None
```

**テスト**: `tests/retrieval/test_query_analyzer.py`

```python
"""Query Analyzerのテスト"""
import pytest
from retrieval.query_analyzer import QueryAnalyzer, QueryType

@pytest.fixture
def analyzer():
    return QueryAnalyzer()

def test_classify_factual_query(analyzer):
    """事実確認クエリの分類"""
    intent = analyzer.analyze("Resonant Engineはいつ開始した？")
    assert intent.query_type == QueryType.FACTUAL

def test_classify_conceptual_query(analyzer):
    """概念理解クエリの分類"""
    intent = analyzer.analyze("呼吸のリズムとは何か？")
    assert intent.query_type == QueryType.CONCEPTUAL

def test_extract_time_range_today(analyzer):
    """時間範囲抽出: 今日"""
    intent = analyzer.analyze("今日のIntent")
    assert intent.time_range is not None
    assert intent.time_range.relative == "today"

def test_extract_time_range_last_week(analyzer):
    """時間範囲抽出: 先週"""
    intent = analyzer.analyze("先週の記憶")
    assert intent.time_range is not None
    assert intent.time_range.relative == "last_week"

def test_extract_keywords(analyzer):
    """キーワード抽出"""
    intent = analyzer.analyze("Resonant Engineの設計原則")
    assert "Resonant" in intent.keywords
    assert "Engine" in intent.keywords
    assert "設計原則" in intent.keywords
```

**チェックポイント**:
- [ ] QueryAnalyzerが実装されている
- [ ] クエリタイプ分類が動作する
- [ ] 時間範囲抽出が動作する
- [ ] キーワード抽出が動作する
- [ ] テストが全てPASS

---

### Task 2: Strategy Selector実装

**目的**: クエリ意図に基づいて検索戦略を決定

**ファイル**: `retrieval/strategy.py`

```python
"""検索戦略の選択"""
from enum import Enum
from retrieval.query_analyzer import QueryIntent, QueryType

class SearchStrategy(str, Enum):
    """検索戦略"""
    SEMANTIC_ONLY = "semantic_only"      # ベクトル検索のみ
    KEYWORD_BOOST = "keyword_boost"      # ベクトル + キーワード
    TEMPORAL = "temporal"                # 時系列 + ベクトル
    HYBRID = "hybrid"                    # 全手法統合

class SearchParams:
    """検索パラメータ"""
    def __init__(
        self,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        limit: int = 10,
        similarity_threshold: float = 0.6,
        time_decay_factor: float = 0.1
    ):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.limit = limit
        self.similarity_threshold = similarity_threshold
        self.time_decay_factor = time_decay_factor

class StrategySelector:
    """戦略選択サービス"""
    
    def select_strategy(self, intent: QueryIntent) -> SearchStrategy:
        """
        クエリ意図から検索戦略を決定
        
        Args:
            intent: クエリ意図
        
        Returns:
            SearchStrategy: 選択された戦略
        """
        # 時間範囲指定あり → TEMPORAL
        if intent.time_range is not None:
            return SearchStrategy.TEMPORAL
        
        # 事実確認 + キーワードあり → KEYWORD_BOOST
        if intent.query_type == QueryType.FACTUAL and intent.keywords:
            return SearchStrategy.KEYWORD_BOOST
        
        # 概念理解 → SEMANTIC_ONLY
        if intent.query_type == QueryType.CONCEPTUAL:
            return SearchStrategy.SEMANTIC_ONLY
        
        # デフォルト: HYBRID
        return SearchStrategy.HYBRID
    
    def optimize_params(
        self,
        intent: QueryIntent,
        strategy: SearchStrategy
    ) -> SearchParams:
        """
        戦略に応じてパラメータを最適化
        
        Args:
            intent: クエリ意図
            strategy: 検索戦略
        
        Returns:
            SearchParams: 最適化されたパラメータ
        """
        params = SearchParams()
        
        # KEYWORD_BOOST: キーワードの重みを上げる
        if strategy == SearchStrategy.KEYWORD_BOOST:
            params.keyword_weight = 0.5
            params.vector_weight = 0.5
        
        # TEMPORAL: 時間減衰を調整
        if strategy == SearchStrategy.TEMPORAL:
            if intent.time_range and intent.time_range.relative == "today":
                params.time_decay_factor = 0.0  # 新しい記憶のみ
            else:
                params.time_decay_factor = 0.2
        
        # 重要度が高い場合は件数を増やす
        if intent.importance > 0.7:
            params.limit = 20
        
        return params
```

**テスト**: `tests/retrieval/test_strategy.py`

```python
"""Strategy Selectorのテスト"""
import pytest
from retrieval.strategy import StrategySelector, SearchStrategy
from retrieval.query_analyzer import QueryIntent, QueryType, TimeRange

@pytest.fixture
def selector():
    return StrategySelector()

def test_select_semantic_strategy(selector):
    """概念理解 → SEMANTIC_ONLY"""
    intent = QueryIntent(
        query_type=QueryType.CONCEPTUAL,
        keywords=["呼吸", "リズム"]
    )
    strategy = selector.select_strategy(intent)
    assert strategy == SearchStrategy.SEMANTIC_ONLY

def test_select_temporal_strategy(selector):
    """時間範囲指定 → TEMPORAL"""
    intent = QueryIntent(
        query_type=QueryType.FACTUAL,
        keywords=["Intent"],
        time_range=TimeRange(relative="today")
    )
    strategy = selector.select_strategy(intent)
    assert strategy == SearchStrategy.TEMPORAL

def test_optimize_params_keyword_boost(selector):
    """KEYWORD_BOOST時のパラメータ最適化"""
    intent = QueryIntent(
        query_type=QueryType.FACTUAL,
        keywords=["Resonant", "Engine"]
    )
    strategy = SearchStrategy.KEYWORD_BOOST
    params = selector.optimize_params(intent, strategy)
    
    assert params.keyword_weight == 0.5
    assert params.vector_weight == 0.5
```

**チェックポイント**:
- [ ] StrategyS electorが実装されている
- [ ] 戦略選択ロジックが動作する
- [ ] パラメータ最適化が動作する
- [ ] テストが全てPASS

---

### Task 3: キーワード検索実装（PostgreSQL ts_vector）

**目的**: 全文検索機能を追加

#### 3.1 テーブル拡張

**マイグレーションファイル**: `migrations/004_add_tsvector.sql`

```sql
-- memoriesテーブルにts_vectorカラムを追加
ALTER TABLE memories 
ADD COLUMN content_tsvector tsvector 
GENERATED ALWAYS AS (to_tsvector('japanese', content)) STORED;

-- GINインデックス作成
CREATE INDEX idx_memories_content_tsvector 
ON memories USING GIN (content_tsvector);

-- 既存データのインデックス再構築
REINDEX INDEX idx_memories_content_tsvector;
```

**実行**:

```bash
psql -U resonant -d resonant_engine -f migrations/004_add_tsvector.sql
```

#### 3.2 キーワード検索実装

**ファイル**: `retrieval/multi_search.py`（一部）

```python
"""複数検索手法の実装"""
import asyncpg
from typing import List
from memory_store.models import MemoryResult

class KeywordSearcher:
    """キーワード検索（ts_vector）"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[MemoryResult]:
        """
        キーワード検索
        
        Args:
            query: 検索クエリ
            limit: 最大返却数
        
        Returns:
            List[MemoryResult]: 検索結果
        """
        # キーワードをORクエリに変換
        keywords = query.split()
        tsquery = " | ".join(keywords)
        
        sql = """
        SELECT 
            id, content, memory_type, source_type, metadata, created_at,
            ts_rank(content_tsvector, to_tsquery('japanese', $1)) as similarity
        FROM memories
        WHERE content_tsvector @@ to_tsquery('japanese', $1)
          AND (expires_at IS NULL OR expires_at > NOW())
          AND is_archived = FALSE
        ORDER BY similarity DESC
        LIMIT $2
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, tsquery, limit)
            return [
                MemoryResult(
                    id=row['id'],
                    content=row['content'],
                    memory_type=row['memory_type'],
                    source_type=row['source_type'],
                    metadata=row['metadata'],
                    similarity=float(row['similarity']),
                    created_at=row['created_at']
                )
                for row in rows
            ]
```

**テスト**:

```python
@pytest.mark.asyncio
async def test_keyword_search(keyword_searcher, memory_store):
    """キーワード検索"""
    # データ準備
    await memory_store.save_memory(
        "Resonant Engineは呼吸のリズムで動作する",
        MemoryType.LONGTERM
    )
    await memory_store.save_memory(
        "PostgreSQLとpgvectorを使用",
        MemoryType.LONGTERM
    )
    
    # 検索
    results = await keyword_searcher.search("Resonant Engine")
    
    # 検証
    assert len(results) > 0
    assert "Resonant Engine" in results[0].content
```

**チェックポイント**:
- [ ] ts_vectorカラムが追加されている
- [ ] GINインデックスが作成されている
- [ ] KeywordSearcherが実装されている
- [ ] キーワード検索が動作する

---

### Task 4: 時系列検索実装

**ファイル**: `retrieval/multi_search.py`（続き）

```python
class TemporalSearcher:
    """時系列検索"""
    
    def __init__(self, pool: asyncpg.Pool, embedding_service):
        self.pool = pool
        self.embedding_service = embedding_service
    
    async def search(
        self,
        query: str,
        time_range: TimeRange,
        limit: int = 10
    ) -> List[MemoryResult]:
        """
        時系列検索
        
        Args:
            query: 検索クエリ
            time_range: 時間範囲
            limit: 最大返却数
        
        Returns:
            List[MemoryResult]: 検索結果（新しい順）
        """
        # Embedding生成
        embedding = await self.embedding_service.generate_embedding(query)
        
        sql = """
        SELECT 
            id, content, memory_type, source_type, metadata, created_at,
            1 - (embedding <=> $1::vector) as similarity
        FROM memories
        WHERE created_at >= $2
          AND created_at <= $3
          AND (expires_at IS NULL OR expires_at > NOW())
          AND is_archived = FALSE
        ORDER BY created_at DESC, similarity DESC
        LIMIT $4
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                sql,
                embedding,
                time_range.start,
                time_range.end,
                limit
            )
            return [MemoryResult(**dict(row)) for row in rows]
```

**テスト**:

```python
@pytest.mark.asyncio
async def test_temporal_search(temporal_searcher, memory_store):
    """時系列検索"""
    from datetime import datetime, timedelta
    
    # データ準備（今日と昨日）
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    # 昨日のデータ
    await memory_store.save_memory(
        "昨日のIntent",
        MemoryType.WORKING,
        created_at=yesterday  # TODO: created_at指定を可能にする
    )
    
    # 今日のデータ
    await memory_store.save_memory(
        "今日のIntent",
        MemoryType.WORKING
    )
    
    # 検索: 今日のみ
    time_range = TimeRange(
        start=now.replace(hour=0, minute=0),
        end=now
    )
    results = await temporal_searcher.search(
        "Intent",
        time_range,
        limit=10
    )
    
    # 検証: 今日のデータのみ
    assert len(results) == 1
    assert "今日のIntent" in results[0].content
```

**チェックポイント**:
- [ ] TemporalSearcherが実装されている
- [ ] 時間範囲フィルタが動作する
- [ ] created_at降順でソートされる

---

### Task 5: Multi-Search Executor実装

**目的**: 複数検索を並行実行し統合

**ファイル**: `retrieval/multi_search.py`（完成版）

```python
"""並行検索実行"""
import asyncio
from typing import List, Dict
from retrieval.strategy import SearchStrategy, SearchParams
from memory_store.service import MemoryStoreService

class MultiSearchExecutor:
    """複数検索の並行実行"""
    
    def __init__(
        self,
        memory_store: MemoryStoreService,
        keyword_searcher: KeywordSearcher,
        temporal_searcher: TemporalSearcher
    ):
        self.memory_store = memory_store
        self.keyword_searcher = keyword_searcher
        self.temporal_searcher = temporal_searcher
    
    async def execute(
        self,
        query: str,
        strategy: SearchStrategy,
        params: SearchParams,
        intent: QueryIntent
    ) -> Dict[str, List[MemoryResult]]:
        """
        戦略に応じて複数検索を並行実行
        
        Args:
            query: 検索クエリ
            strategy: 検索戦略
            params: 検索パラメータ
            intent: クエリ意図
        
        Returns:
            Dict[str, List[MemoryResult]]: {検索手法: 結果リスト}
        """
        tasks = {}
        
        # ベクトル検索
        if strategy in [SearchStrategy.SEMANTIC_ONLY, SearchStrategy.KEYWORD_BOOST, SearchStrategy.HYBRID]:
            tasks["vector"] = self.memory_store.search_similar(
                query=query,
                limit=params.limit,
                similarity_threshold=params.similarity_threshold
            )
        
        # キーワード検索
        if strategy in [SearchStrategy.KEYWORD_BOOST, SearchStrategy.HYBRID]:
            tasks["keyword"] = self.keyword_searcher.search(
                query=query,
                limit=params.limit
            )
        
        # 時系列検索
        if strategy == SearchStrategy.TEMPORAL and intent.time_range:
            tasks["temporal"] = self.temporal_searcher.search(
                query=query,
                time_range=intent.time_range,
                limit=params.limit
            )
        
        # 並行実行
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 結果を辞書にマッピング
        return {
            key: result if not isinstance(result, Exception) else []
            for key, result in zip(tasks.keys(), results)
        }
```

**テスト**:

```python
@pytest.mark.asyncio
async def test_multi_search_executor(multi_search_executor):
    """並行検索実行"""
    intent = QueryIntent(
        query_type=QueryType.FACTUAL,
        keywords=["Resonant", "Engine"]
    )
    params = SearchParams()
    
    results = await multi_search_executor.execute(
        query="Resonant Engine",
        strategy=SearchStrategy.KEYWORD_BOOST,
        params=params,
        intent=intent
    )
    
    # ベクトル検索とキーワード検索の両方が実行される
    assert "vector" in results
    assert "keyword" in results
```

**チェックポイント**:
- [ ] MultiSearchExecutorが実装されている
- [ ] 並行実行が動作する
- [ ] 戦略に応じて適切な検索が実行される

---

### Task 6: Reranker実装

**目的**: 複数検索結果を統合しリランキング

**ファイル**: `retrieval/reranker.py`

```python
"""リランキング"""
from typing import List, Dict
import numpy as np
from memory_store.models import MemoryResult
from retrieval.strategy import SearchParams

class Reranker:
    """検索結果のリランキング"""
    
    def rerank(
        self,
        search_results: Dict[str, List[MemoryResult]],
        params: SearchParams
    ) -> List[MemoryResult]:
        """
        複数検索結果を統合しリランキング
        
        Args:
            search_results: {検索手法: 結果リスト}
            params: 検索パラメータ
        
        Returns:
            List[MemoryResult]: リランキング後の結果
        """
        # 1. スコア正規化
        normalized = self._normalize_scores(search_results)
        
        # 2. IDベースで統合
        merged = self._merge_results(normalized, params)
        
        # 3. 重複排除
        unique = self._deduplicate(merged)
        
        # 4. 最終ソート
        unique.sort(key=lambda r: r.similarity, reverse=True)
        
        return unique[:params.limit]
    
    def _normalize_scores(
        self,
        search_results: Dict[str, List[MemoryResult]]
    ) -> Dict[str, List[MemoryResult]]:
        """スコアをMin-Max正規化"""
        normalized = {}
        
        for method, results in search_results.items():
            if not results:
                normalized[method] = []
                continue
            
            scores = [r.similarity for r in results]
            min_score = min(scores)
            max_score = max(scores)
            
            if max_score - min_score < 1e-6:
                # 全て同じスコア
                for r in results:
                    r.similarity = 1.0
            else:
                for r in results:
                    r.similarity = (r.similarity - min_score) / (max_score - min_score)
            
            normalized[method] = results
        
        return normalized
    
    def _merge_results(
        self,
        search_results: Dict[str, List[MemoryResult]],
        params: SearchParams
    ) -> List[MemoryResult]:
        """IDベースで結果を統合し、加重平均スコアを計算"""
        merged = {}
        
        # ベクトル検索結果
        for r in search_results.get("vector", []):
            merged[r.id] = {
                "result": r,
                "vector_score": r.similarity,
                "keyword_score": 0.0
            }
        
        # キーワード検索結果
        for r in search_results.get("keyword", []):
            if r.id in merged:
                merged[r.id]["keyword_score"] = r.similarity
            else:
                merged[r.id] = {
                    "result": r,
                    "vector_score": 0.0,
                    "keyword_score": r.similarity
                }
        
        # 時系列検索結果（ベクトルスコアとして扱う）
        for r in search_results.get("temporal", []):
            if r.id not in merged:
                merged[r.id] = {
                    "result": r,
                    "vector_score": r.similarity,
                    "keyword_score": 0.0
                }
        
        # 加重平均スコア計算
        final_results = []
        for item in merged.values():
            final_score = (
                params.vector_weight * item["vector_score"] +
                params.keyword_weight * item["keyword_score"]
            )
            item["result"].similarity = final_score
            final_results.append(item["result"])
        
        return final_results
    
    def _deduplicate(
        self,
        results: List[MemoryResult],
        threshold: float = 0.95
    ) -> List[MemoryResult]:
        """重複排除（簡易版: IDベース）"""
        # 本実装ではEmbedding類似度でも重複判定すべき
        # ここでは簡易的にIDユニークのみ
        seen = set()
        unique = []
        
        for r in results:
            if r.id not in seen:
                unique.append(r)
                seen.add(r.id)
        
        return unique
```

**テスト**:

```python
def test_rerank_merge_scores():
    """スコア統合のテスト"""
    reranker = Reranker()
    
    search_results = {
        "vector": [
            MemoryResult(id=1, content="A", similarity=0.9, ...),
            MemoryResult(id=2, content="B", similarity=0.7, ...)
        ],
        "keyword": [
            MemoryResult(id=1, content="A", similarity=0.8, ...),
            MemoryResult(id=3, content="C", similarity=0.6, ...)
        ]
    }
    
    params = SearchParams(vector_weight=0.6, keyword_weight=0.4)
    
    results = reranker.rerank(search_results, params)
    
    # ID=1は両方に含まれるため高スコア
    assert results[0].id == 1
    assert results[0].similarity > 0.8
```

**チェックポイント**:
- [ ] Rerankerが実装されている
- [ ] スコア正規化が動作する
- [ ] 複数検索結果が統合される
- [ ] 重複排除が動作する

---

### Task 7: Metrics Collector実装

**ファイル**: `retrieval/metrics.py`

```python
"""メトリクス収集"""
import time
from typing import Dict, List
from datetime import datetime
from retrieval.strategy import SearchStrategy
from memory_store.models import MemoryResult

class SearchMetrics:
    """検索メトリクス"""
    def __init__(
        self,
        query: str,
        strategy: SearchStrategy,
        total_latency_ms: float,
        search_latencies: Dict[str, float],
        num_results: int,
        avg_similarity: float,
        timestamp: datetime
    ):
        self.query = query
        self.strategy = strategy
        self.total_latency_ms = total_latency_ms
        self.search_latencies = search_latencies
        self.num_results = num_results
        self.avg_similarity = avg_similarity
        self.timestamp = timestamp

class MetricsCollector:
    """メトリクス収集サービス"""
    
    async def collect(
        self,
        query: str,
        strategy: SearchStrategy,
        results: List[MemoryResult],
        latencies: Dict[str, float]
    ) -> SearchMetrics:
        """
        メトリクス収集
        
        Args:
            query: 検索クエリ
            strategy: 使用した戦略
            results: 検索結果
            latencies: {検索手法: レイテンシ(ms)}
        
        Returns:
            SearchMetrics: 収集されたメトリクス
        """
        avg_similarity = (
            sum(r.similarity for r in results) / len(results)
            if results else 0.0
        )
        
        return SearchMetrics(
            query=query,
            strategy=strategy,
            total_latency_ms=sum(latencies.values()),
            search_latencies=latencies,
            num_results=len(results),
            avg_similarity=avg_similarity,
            timestamp=datetime.utcnow()
        )
    
    async def log_metrics(self, metrics: SearchMetrics):
        """メトリクスをログ出力"""
        print(f"""
        [Search Metrics]
        Query: {metrics.query}
        Strategy: {metrics.strategy}
        Total Latency: {metrics.total_latency_ms:.2f}ms
        Results: {metrics.num_results}
        Avg Similarity: {metrics.avg_similarity:.3f}
        Breakdown: {metrics.search_latencies}
        """)
```

**チェックポイント**:
- [ ] MetricsCollectorが実装されている
- [ ] メトリクス収集が動作する
- [ ] ログ出力が動作する

---

### Task 8: Retrieval Orchestrator統合

**目的**: 全コンポーネントを統合

**ファイル**: `retrieval/orchestrator.py`

```python
"""Retrieval Orchestrator"""
import time
from typing import Optional, List, Dict
from retrieval.query_analyzer import QueryAnalyzer, QueryIntent
from retrieval.strategy import StrategySelector, SearchStrategy, SearchParams
from retrieval.multi_search import MultiSearchExecutor
from retrieval.reranker import Reranker
from retrieval.metrics import MetricsCollector, SearchMetrics
from memory_store.models import MemoryResult

class RetrievalOptions:
    """検索オプション"""
    def __init__(
        self,
        force_strategy: Optional[SearchStrategy] = None,
        limit: Optional[int] = None,
        include_metadata_details: bool = False
    ):
        self.force_strategy = force_strategy
        self.limit = limit
        self.include_metadata_details = include_metadata_details

class RetrievalMetadata:
    """検索メタデータ"""
    def __init__(
        self,
        strategy_used: SearchStrategy,
        query_intent: QueryIntent,
        total_latency_ms: float,
        search_breakdown: Dict[str, float],
        num_results_before_rerank: int,
        num_results_after_rerank: int
    ):
        self.strategy_used = strategy_used
        self.query_intent = query_intent
        self.total_latency_ms = total_latency_ms
        self.search_breakdown = search_breakdown
        self.num_results_before_rerank = num_results_before_rerank
        self.num_results_after_rerank = num_results_after_rerank

class RetrievalResponse:
    """検索レスポンス"""
    def __init__(
        self,
        results: List[MemoryResult],
        metadata: RetrievalMetadata
    ):
        self.results = results
        self.metadata = metadata

class RetrievalOrchestrator:
    """検索オーケストレーター"""
    
    def __init__(
        self,
        query_analyzer: QueryAnalyzer,
        strategy_selector: StrategySelector,
        multi_search_executor: MultiSearchExecutor,
        reranker: Reranker,
        metrics_collector: MetricsCollector
    ):
        self.query_analyzer = query_analyzer
        self.strategy_selector = strategy_selector
        self.multi_search_executor = multi_search_executor
        self.reranker = reranker
        self.metrics_collector = metrics_collector
    
    async def retrieve(
        self,
        query: str,
        options: Optional[RetrievalOptions] = None
    ) -> RetrievalResponse:
        """
        記憶検索のエントリーポイント
        
        Args:
            query: 検索クエリ
            options: 検索オプション
        
        Returns:
            RetrievalResponse: 検索結果 + メタデータ
        """
        start_time = time.time()
        options = options or RetrievalOptions()
        
        # 1. Query Analyzer
        intent = self.query_analyzer.analyze(query)
        
        # 2. Strategy Selector
        if options.force_strategy:
            strategy = options.force_strategy
        else:
            strategy = self.strategy_selector.select_strategy(intent)
        
        params = self.strategy_selector.optimize_params(intent, strategy)
        if options.limit:
            params.limit = options.limit
        
        # 3. Multi-Search Executor
        search_start = time.time()
        search_results = await self.multi_search_executor.execute(
            query=query,
            strategy=strategy,
            params=params,
            intent=intent
        )
        search_latencies = {
            method: (time.time() - search_start) * 1000
            for method in search_results.keys()
        }
        
        num_before_rerank = sum(len(r) for r in search_results.values())
        
        # 4. Reranker
        rerank_start = time.time()
        final_results = self.reranker.rerank(search_results, params)
        rerank_latency = (time.time() - rerank_start) * 1000
        
        total_latency = (time.time() - start_time) * 1000
        
        # 5. Metrics Collector
        await self.metrics_collector.collect(
            query=query,
            strategy=strategy,
            results=final_results,
            latencies=search_latencies
        )
        
        # 6. Response構築
        metadata = RetrievalMetadata(
            strategy_used=strategy,
            query_intent=intent,
            total_latency_ms=total_latency,
            search_breakdown=search_latencies,
            num_results_before_rerank=num_before_rerank,
            num_results_after_rerank=len(final_results)
        )
        
        return RetrievalResponse(
            results=final_results,
            metadata=metadata
        )
```

**テスト**: `tests/retrieval/test_orchestrator.py`

```python
"""Orchestratorの統合テスト"""
import pytest
from retrieval.orchestrator import RetrievalOrchestrator, RetrievalOptions
from retrieval.strategy import SearchStrategy

@pytest.mark.asyncio
async def test_full_retrieval_flow(orchestrator, memory_store):
    """E2Eテスト"""
    # データ準備
    await memory_store.save_memory(
        "Resonant Engineは呼吸のリズムで動作する",
        MemoryType.LONGTERM,
        source_type="decision"
    )
    
    # 検索実行
    response = await orchestrator.retrieve(
        query="呼吸について教えて"
    )
    
    # 検証
    assert len(response.results) > 0
    assert response.results[0].similarity > 0.6
    assert response.metadata.strategy_used in [
        SearchStrategy.SEMANTIC_ONLY,
        SearchStrategy.HYBRID
    ]
    assert response.metadata.total_latency_ms < 200  # 200ms以内

@pytest.mark.asyncio
async def test_force_strategy(orchestrator):
    """戦略強制指定"""
    response = await orchestrator.retrieve(
        query="テストクエリ",
        options=RetrievalOptions(
            force_strategy=SearchStrategy.KEYWORD_BOOST
        )
    )
    
    assert response.metadata.strategy_used == SearchStrategy.KEYWORD_BOOST
```

**チェックポイント**:
- [ ] RetrievalOrchestratorが実装されている
- [ ] 全コンポーネントが統合されている
- [ ] E2Eテストが通る
- [ ] 性能要件（< 200ms）を満たす

---

## ✅ Done Definition確認

Sprint完了時に以下を確認してください:

### 機能要件
- [ ] Query Analyzerがクエリ分類を実行できる
- [ ] Strategy Selectorが適切な戦略を選択できる
- [ ] キーワード検索（ts_vector）が動作する
- [ ] 時系列検索が動作する
- [ ] Multi-Search Executorが並行検索を実行できる
- [ ] Rerankerが結果統合・重複排除を行える
- [ ] Metrics Collectorがメトリクスを記録できる
- [ ] Orchestratorが全体を統合して動作する

### 品質要件
- [ ] 単体テストカバレッジ > 80%
- [ ] 統合テストが全てPASS
- [ ] 検索レスポンスタイム < 150ms

### ドキュメント
- [ ] API仕様書が完成
- [ ] 検索戦略の決定ロジックがドキュメント化されている

---

## 🚨 トラブルシューティング

### ts_vectorがうまく動かない

```sql
-- 日本語辞書の確認
SELECT * FROM pg_ts_config WHERE cfgname = 'japanese';

-- 手動でts_vectorを試す
SELECT to_tsvector('japanese', 'Resonant Engineは呼吸のリズムで動作する');
```

### 並行検索が遅い

- 各検索手法の個別レイテンシを確認
- PostgreSQLのコネクションプールサイズを確認
- `asyncio.gather`が正しく並行実行されているか確認

---

## 📚 参考資料

- [Sprint 4 詳細仕様書](./sprint4_retrieval_orchestrator_spec.md)
- [Sprint 3 Memory Store仕様書](./sprint3_memory_store_spec.md)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)

---

**準備はいいですか？それでは、Sprint 4を開始してください！**

検索オーケストレーターの構築、がんばりましょう 🚀
