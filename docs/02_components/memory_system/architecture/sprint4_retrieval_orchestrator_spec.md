# Sprint 4: Retrieval Orchestrator 詳細仕様書

## 0. CRITICAL: Orchestration as Intelligent Recall

**⚠️ IMPORTANT: 「検索 = 人間の記憶想起戦略を模倣する知的行為」**

Retrieval Orchestrator は Memory Store を単なるデータベースではなく「文脈を持つ記憶」として扱うための知性です。クエリの意図を理解し、最適な呼吸パターン（検索戦略）を選ぶことで、ASD 認知に必要な秩序だった回答を生成します。

```yaml
retrieval_orchestrator_philosophy:
    essence: "検索 = 共鳴を起こす想起戦略の選択"
    purpose:
        - クエリの文脈と重要度を解析し、時間軸を保ったまま記憶を想起する
        - 複数の検索手法を重ね合わせ、意図に応じた共鳴を生成する
        - 結果を整理し、次の呼気（Context Assembler）へ正しい順序で渡す
    principles:
        - "人は文脈で思い出す"
        - "記憶は多面的に想起される"
        - "最適な戦略は状況によって変化する"
```

### 呼吸サイクルとの関係

```
吸気 (Question) → Query Analyzer が意図を分類
共鳴 (Resonance) → Strategy Selector / Multi Search が想起を構築
呼気 (Response) → Context Assembler へ整理された記憶を受け渡す
```

Memory Store が「記憶の座標」を保証し、Retrieval Orchestrator が「想起の呼吸」を整えることで、Resonant Engine の時間軸は守られます。

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] Query Analyzer がクエリタイプ/時間範囲/キーワード抽出を完了
- [ ] Strategy Selector + Multi Search + Reranker が一連のパイプラインとして動作し、E2E テストが PASS
- [ ] キーワード検索（ts_vector）と時系列検索が `memories` テーブルへ適用済み
- [ ] Metrics Collector が検索レイテンシ/戦略使用率を記録し、Dashboard で確認可能
- [ ] 15 件以上の単体/統合テストが作成され、CI で緑

#### Tier 2: 品質要件
- [ ] 10k レコードで Retrieval レイテンシ p95 < 150ms（vector 100ms + orchestration 50ms）
- [ ] リランキング後の MRR / hit@5 がベースラインより +10%以上向上
- [ ] SpaCy モデルやキーワード辞書の更新手順が Runbook に記載
- [ ] Observability: `retrieval_strategy_usage_total`, `retrieval_latency_ms`, `retrieval_empty_results_total`
- [ ] Kana レビュー向けに「戦略決定ロジック」「リスクと対策」がまとめられている

## 1. 概要

### 1.1 目的
Memory Store（Sprint 3）とContext Assembler（未実装）の間に位置し、記憶検索を最適化・統制する**検索オーケストレーター**を実装する。複数の検索戦略を組み合わせ、クエリに応じて最適な記憶を取得する。

### 1.2 スコープ
- クエリ分析と検索戦略の決定
- 複数検索手法の統合（ベクトル検索、キーワード検索、時系列検索）
- 検索結果のリランキングと重複排除
- 検索メトリクスの収集

### 1.3 Resonant Engineにおける位置づけ

```
呼吸フェーズ: 吸気（Question） → 共鳴（Resonance）

Intent (質問)
    ↓
┌───────────────────────────┐
│ Retrieval Orchestrator    │  ← Sprint 4 (このレイヤー)
│ - クエリ分析              │
│ - 検索戦略決定            │
│ - 複数検索の統合          │
│ - リランキング            │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ Memory Store (pgvector)   │  ← Sprint 3
│ - ベクトル検索            │
│ - メタデータフィルタ      │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ Context Assembler         │  ← Sprint 5以降
│ - コンテキスト構築        │
│ - プロンプト生成          │
└───────────────────────────┘
    ↓
Yuno / Kana (AI応答)
```

### 1.4 成果物
- Retrieval Orchestratorサービス実装
- クエリアナライザー（意図分類）
- 検索戦略エンジン
- リランキング機能
- メトリクス収集基盤

---

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────┐
│          Retrieval Orchestrator              │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Query Analyzer                      │  │
│  │  - クエリ分類（factual/conceptual）  │  │
│  │  - 時間範囲抽出                       │  │
│  │  - 重要キーワード抽出                 │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Strategy Selector                   │  │
│  │  - 検索戦略の決定                     │  │
│  │  - パラメータ最適化                   │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Multi-Search Executor               │  │
│  │  - ベクトル検索                       │  │
│  │  - キーワード検索（ts_vector）        │  │
│  │  - 時系列検索                         │  │
│  │  - ハイブリッド検索                   │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Reranker                            │  │
│  │  - スコア正規化                       │  │
│  │  - 重複排除                           │  │
│  │  - 最終順位付け                       │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Metrics Collector                   │  │
│  │  - 検索レイテンシ                     │  │
│  │  - 結果品質スコア                     │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
          ↓
    Memory Store (Sprint 3)
```

### 2.2 検索戦略の分類

| 戦略名 | 用途 | 使用する検索手法 |
|--------|------|-----------------|
| semantic_only | 概念的な質問 | ベクトル検索のみ |
| keyword_boost | 固有名詞を含む質問 | ベクトル + キーワード |
| temporal | 時間範囲指定 | 時系列 + ベクトル |
| hybrid | 複雑な複合クエリ | 全手法統合 |

---

## 3. コンポーネント設計

### 3.1 Query Analyzer

**役割**: クエリを解析し、検索に必要なメタデータを抽出

#### 3.1.1 クエリ分類

```python
class QueryType(Enum):
    FACTUAL = "factual"          # 事実確認 "〜はいつ？"
    CONCEPTUAL = "conceptual"    # 概念理解 "〜とは？"
    PROCEDURAL = "procedural"    # 手順確認 "〜はどうやる？"
    TEMPORAL = "temporal"        # 時系列 "最近の〜"
    COMPARATIVE = "comparative"  # 比較 "〜と〜の違い"

class QueryIntent:
    query_type: QueryType
    keywords: List[str]           # 重要キーワード
    time_range: Optional[TimeRange]  # 時間範囲
    source_type_hint: Optional[str]  # 推定されるソースタイプ
    importance: float             # クエリの重要度
```

**実装アプローチ**:
1. **ルールベース**: キーワードマッチング（"いつ" → FACTUAL、"最近" → TEMPORAL）
2. **LLMベース** (将来): Claude APIでクエリ意図を分類

#### 3.1.2 時間範囲抽出

```python
class TimeRange:
    start: Optional[datetime]
    end: Optional[datetime]
    relative: Optional[str]  # "last_week", "today", "this_month"

# 例
"先週のIntent" → TimeRange(relative="last_week")
"2025年1月の記憶" → TimeRange(start=2025-01-01, end=2025-01-31)
```

### 3.2 Strategy Selector

**役割**: Query Intentに基づいて最適な検索戦略を選択

#### 3.2.1 戦略マッピング

```python
def select_strategy(intent: QueryIntent) -> SearchStrategy:
    """クエリ意図から検索戦略を決定"""
    
    # ルールベースの決定木
    if intent.time_range is not None:
        return SearchStrategy.TEMPORAL
    
    if intent.query_type == QueryType.FACTUAL and intent.keywords:
        return SearchStrategy.KEYWORD_BOOST
    
    if intent.query_type == QueryType.CONCEPTUAL:
        return SearchStrategy.SEMANTIC_ONLY
    
    # デフォルト: ハイブリッド
    return SearchStrategy.HYBRID
```

#### 3.2.2 パラメータ最適化

```python
class SearchParams:
    vector_weight: float = 0.7    # ベクトル検索の重み
    keyword_weight: float = 0.3   # キーワード検索の重み
    limit: int = 10
    similarity_threshold: float = 0.6
    time_decay_factor: float = 0.1  # 古い記憶の減衰率

def optimize_params(
    intent: QueryIntent,
    strategy: SearchStrategy
) -> SearchParams:
    """戦略に応じてパラメータを調整"""
    params = SearchParams()
    
    if strategy == SearchStrategy.KEYWORD_BOOST:
        params.keyword_weight = 0.5
        params.vector_weight = 0.5
    
    if intent.time_range and intent.time_range.relative == "today":
        params.time_decay_factor = 0.0  # 新しい記憶を優先
    
    return params
```

### 3.3 Multi-Search Executor

**役割**: 複数の検索を並行実行し、結果を統合

#### 3.3.1 並行検索実行

```python
async def execute_searches(
    query: str,
    strategy: SearchStrategy,
    params: SearchParams
) -> List[SearchResult]:
    """複数検索の並行実行"""
    
    tasks = []
    
    # ベクトル検索
    if strategy.uses_vector:
        tasks.append(
            memory_store.search_similar(
                query=query,
                limit=params.limit,
                similarity_threshold=params.similarity_threshold
            )
        )
    
    # キーワード検索
    if strategy.uses_keyword:
        tasks.append(
            keyword_search(query, params.limit)
        )
    
    # 時系列検索
    if strategy.uses_temporal:
        tasks.append(
            temporal_search(query, params.time_range, params.limit)
        )
    
    # 並行実行
    results = await asyncio.gather(*tasks)
    
    # 統合
    return merge_results(results, params)
```

#### 3.3.2 キーワード検索（PostgreSQL ts_vector）

**テーブル拡張**:

```sql
-- memoriesテーブルにts_vectorカラムを追加
ALTER TABLE memories 
ADD COLUMN content_tsvector tsvector 
GENERATED ALWAYS AS (to_tsvector('japanese', content)) STORED;

-- GINインデックス作成
CREATE INDEX idx_memories_content_tsvector 
ON memories USING GIN (content_tsvector);
```

**検索クエリ**:

```python
async def keyword_search(
    query: str,
    limit: int
) -> List[MemoryResult]:
    """キーワード検索（ts_vector）"""
    sql = """
    SELECT 
        id, content, memory_type, source_type, metadata, created_at,
        ts_rank(content_tsvector, to_tsquery('japanese', $1)) as rank
    FROM memories
    WHERE content_tsvector @@ to_tsquery('japanese', $1)
      AND (expires_at IS NULL OR expires_at > NOW())
      AND is_archived = FALSE
    ORDER BY rank DESC
    LIMIT $2
    """
    
    # クエリを形態素解析してORクエリに変換
    tsquery = " | ".join(extract_keywords(query))
    
    rows = await db.fetch(sql, tsquery, limit)
    return [MemoryResult(**row, similarity=row['rank']) for row in rows]
```

#### 3.3.3 時系列検索

```python
async def temporal_search(
    query: str,
    time_range: TimeRange,
    limit: int
) -> List[MemoryResult]:
    """時系列検索"""
    # ベクトル検索 + 時間フィルタ + 新しい順
    embedding = await embedding_service.generate_embedding(query)
    
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
    
    rows = await db.fetch(
        sql,
        embedding,
        time_range.start,
        time_range.end,
        limit
    )
    return [MemoryResult(**row) for row in rows]
```

### 3.4 Reranker

**役割**: 複数検索結果を統合し、最終順位を決定

#### 3.4.1 スコア正規化

```python
def normalize_scores(
    results: List[SearchResult],
    method: str = "minmax"
) -> List[SearchResult]:
    """スコアを0-1に正規化"""
    if method == "minmax":
        scores = [r.similarity for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        for r in results:
            r.similarity = (r.similarity - min_score) / (max_score - min_score)
    
    return results
```

#### 3.4.2 重複排除

```python
def deduplicate_results(
    results: List[MemoryResult],
    threshold: float = 0.95
) -> List[MemoryResult]:
    """類似した記憶を重複排除"""
    unique_results = []
    seen_embeddings = []
    
    for result in results:
        # 既存結果と類似度計算
        is_duplicate = False
        for seen in seen_embeddings:
            similarity = cosine_similarity(result.embedding, seen)
            if similarity > threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_results.append(result)
            seen_embeddings.append(result.embedding)
    
    return unique_results
```

#### 3.4.3 加重スコアリング

```python
def rerank_results(
    vector_results: List[MemoryResult],
    keyword_results: List[MemoryResult],
    params: SearchParams
) -> List[MemoryResult]:
    """複数検索結果を統合しリランキング"""
    
    # スコア正規化
    vector_results = normalize_scores(vector_results)
    keyword_results = normalize_scores(keyword_results)
    
    # IDベースで統合
    merged = {}
    
    for r in vector_results:
        merged[r.id] = {
            "result": r,
            "vector_score": r.similarity,
            "keyword_score": 0.0
        }
    
    for r in keyword_results:
        if r.id in merged:
            merged[r.id]["keyword_score"] = r.similarity
        else:
            merged[r.id] = {
                "result": r,
                "vector_score": 0.0,
                "keyword_score": r.similarity
            }
    
    # 加重平均
    final_results = []
    for item in merged.values():
        final_score = (
            params.vector_weight * item["vector_score"] +
            params.keyword_weight * item["keyword_score"]
        )
        item["result"].similarity = final_score
        final_results.append(item["result"])
    
    # 最終ソート
    final_results.sort(key=lambda r: r.similarity, reverse=True)
    
    return final_results
```

### 3.5 Metrics Collector

**役割**: 検索品質と性能のメトリクスを収集

```python
class SearchMetrics:
    query: str
    strategy: SearchStrategy
    total_latency_ms: float
    vector_latency_ms: float
    keyword_latency_ms: float
    num_results: int
    avg_similarity: float
    timestamp: datetime

async def collect_metrics(
    query: str,
    strategy: SearchStrategy,
    results: List[MemoryResult],
    latencies: Dict[str, float]
) -> SearchMetrics:
    """メトリクス収集"""
    return SearchMetrics(
        query=query,
        strategy=strategy,
        total_latency_ms=sum(latencies.values()),
        vector_latency_ms=latencies.get("vector", 0),
        keyword_latency_ms=latencies.get("keyword", 0),
        num_results=len(results),
        avg_similarity=sum(r.similarity for r in results) / len(results),
        timestamp=datetime.utcnow()
    )
```

---

## 4. API設計

### 4.1 Retrieval Orchestrator Service

#### 4.1.1 retrieve()

```python
async def retrieve(
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
```

**処理フロー**:
```
1. Query Analyzer → QueryIntent抽出
2. Strategy Selector → 検索戦略決定
3. Multi-Search Executor → 並行検索実行
4. Reranker → 結果統合・リランキング
5. Metrics Collector → メトリクス記録
6. RetrievalResponse返却
```

**レスポンス構造**:

```python
class RetrievalResponse:
    results: List[MemoryResult]
    metadata: RetrievalMetadata

class RetrievalMetadata:
    strategy_used: SearchStrategy
    query_intent: QueryIntent
    total_latency_ms: float
    search_breakdown: Dict[str, float]  # {"vector": 50ms, "keyword": 30ms}
    num_results_before_rerank: int
    num_results_after_rerank: int
```

#### 4.1.2 使用例

```python
# 基本的な検索
response = await retrieval_orchestrator.retrieve(
    query="呼吸のリズムとは何か"
)

for memory in response.results:
    print(f"{memory.content} (similarity: {memory.similarity})")

# オプション指定
response = await retrieval_orchestrator.retrieve(
    query="先週のIntent",
    options=RetrievalOptions(
        force_strategy=SearchStrategy.TEMPORAL,
        limit=20,
        include_metadata_details=True
    )
)
```

---

## 5. 実装詳細

### 5.1 ディレクトリ構成

```
resonant-engine/
├── retrieval/
│   ├── __init__.py
│   ├── orchestrator.py       # メインサービス
│   ├── query_analyzer.py     # クエリ分析
│   ├── strategy.py           # 戦略選択
│   ├── multi_search.py       # 並行検索実行
│   ├── reranker.py           # リランキング
│   ├── metrics.py            # メトリクス収集
│   └── models.py             # Pydanticモデル
├── tests/
│   └── retrieval/
│       ├── test_orchestrator.py
│       ├── test_query_analyzer.py
│       └── test_reranker.py
└── scripts/
    └── benchmark_retrieval.sh
```

### 5.2 依存関係

```toml
[tool.poetry.dependencies]
# Sprint 3の依存関係に加えて
spacy = "^3.7.0"              # 形態素解析（日本語）
ja-core-news-sm = {url = "https://github.com/explosion/spacy-models/releases/download/ja_core_news_sm-3.7.0/ja_core_news_sm-3.7.0-py3-none-any.whl"}
```

---

## 6. テスト戦略

### 6.1 単体テスト

```python
# Query Analyzer
def test_analyze_factual_query():
    intent = analyzer.analyze("Resonant Engineはいつ開始した？")
    assert intent.query_type == QueryType.FACTUAL

def test_extract_time_range():
    intent = analyzer.analyze("先週のIntent")
    assert intent.time_range.relative == "last_week"

# Strategy Selector
def test_select_semantic_strategy():
    intent = QueryIntent(query_type=QueryType.CONCEPTUAL)
    strategy = selector.select_strategy(intent)
    assert strategy == SearchStrategy.SEMANTIC_ONLY

# Reranker
def test_deduplicate_similar_results():
    results = [
        MemoryResult(id=1, content="A", similarity=0.9),
        MemoryResult(id=2, content="A（ほぼ同じ）", similarity=0.85)
    ]
    unique = reranker.deduplicate_results(results)
    assert len(unique) == 1
```

### 6.2 統合テスト

```python
@pytest.mark.asyncio
async def test_full_retrieval_flow():
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
    assert response.results[0].similarity > 0.7
    assert response.metadata.strategy_used in [
        SearchStrategy.SEMANTIC_ONLY,
        SearchStrategy.HYBRID
    ]
```

### 6.3 性能テスト

```python
async def test_retrieval_performance():
    """10,000件データでの検索性能"""
    # データ準備
    for i in range(10000):
        await memory_store.save_memory(f"Memory {i}", MemoryType.LONGTERM)
    
    # 検索実行
    start = time.time()
    response = await orchestrator.retrieve("test query")
    elapsed = time.time() - start
    
    # 150ms以内（ベクトル検索100ms + オーケストレーション50ms）
    assert elapsed < 0.15
```

---

## 7. Done Definition

### 7.1 機能要件

- [ ] Query Analyzerがクエリ分類を実行できる
- [ ] Strategy Selectorが適切な戦略を選択できる
- [ ] Multi-Search Executorが並行検索を実行できる
- [ ] Rerankerが結果統合・重複排除を行える
- [ ] Metrics Collectorがメトリクスを記録できる
- [ ] キーワード検索（ts_vector）が動作する
- [ ] 時系列検索が動作する

### 7.2 品質要件

- [ ] 単体テストカバレッジ > 80%
- [ ] 統合テストが全てPASS
- [ ] 検索レスポンスタイム < 150ms（10,000件データ時）
- [ ] リランキング後の精度向上が確認できる

### 7.3 ドキュメント要件

- [ ] API仕様書が完成
- [ ] 検索戦略の決定ロジックがドキュメント化されている
- [ ] メトリクスの見方が文書化されている

### 7.4 レビュー要件

- [ ] 宏啓さんによるコードレビュー完了
- [ ] Yunoによる検索品質評価完了
- [ ] 実データでの動作確認完了

---

## 8. 今後の拡張

### 8.1 Sprint 5以降での拡張候補

- [ ] **LLMベースのクエリ分析**: Claude APIでより高度な意図分類
- [ ] **学習ベースのリランキング**: ユーザーフィードバックから学習
- [ ] **パーソナライズ検索**: ユーザーの過去の行動から重み調整
- [ ] **マルチモーダル検索**: 画像・音声クエリのサポート
- [ ] **Cohere Rerank API統合**: 外部リランキングサービス利用

### 8.2 制約事項

- **日本語形態素解析**: SpaCyの精度に依存
- **戦略選択**: ルールベースのため、複雑なクエリでは最適でない可能性
- **メトリクス保存**: 現状はログのみ（TimescaleDB統合は未実装）

---

## 9. Risks & Mitigation

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| クエリ分類の精度不足で誤戦略を選択 | Medium | High | ルールベースにテレメトリを接続し、誤分類例を週次でレビューして辞書を更新。将来的な LLM 分類の受け皿を models.py に用意。 |
| ts_vector 索引の再構築遅延 | Low | Medium | `VACUUM ANALYZE memories` + GIN Reindex を月次スケジュール化。高トラフィック時は分割テーブルを検討。 |
| リランキングでレスポンスが遅延 | Medium | Medium | Reranker をバッチ化し、結果件数が閾値超過時は上位 50 件のみリランキング。メトリクスで `rerank_latency_ms` を監視。 |
| Metrics 未収集で品質劣化に気づけない | Low | High | `retrieval_metrics_writer` を必須 DI とし、保存失敗時には AlertManager 経由で通知。 |

## 10. Rollout Plan

### Phase 0: Alignment (Day 0)
- Memory Store / Sprint 3 仕様を再確認し、`memories` スキーマが最新であることを確認
- SpaCy モデルと形態素辞書をローカルへダウンロード

### Phase 1: Analyzer + Strategy (Day 1-2)
- Query Analyzer / Strategy Selector を実装し、ユニットテスト 6 件を作成
- Intent サンプル 30 件で分類結果をレビューし、辞書を調整

### Phase 2: Multi Search + Index (Day 3)
- `content_tsvector` 追加、GIN インデックス作成
- keyword / temporal search を実装し、Integration Test を追加

### Phase 3: Reranker + Metrics (Day 4)
- Reranker / Metrics Collector を実装し、性能測定を記録
- Prometheus exporter へメトリクスを追加

### Phase 4: Final QA & Documentation (Day 5)
- 10k データでベンチ → レポートを docs/sprints へ添付
- Runbook / API ドキュメント更新、Kana へレビュー依頼

## 11. 参考資料

- [Memory Store仕様書（Sprint 3）](./sprint3_memory_store_spec.md)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [SpaCy Documentation](https://spacy.io/usage/spacy-101)

---

**作成日**: 2025-11-16  
**作成者**: Kana (Claude Sonnet 4.5)  
**バージョン**: 1.0.0
