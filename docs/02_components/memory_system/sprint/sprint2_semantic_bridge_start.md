# Semantic Bridge 実装開始指示書
## L1: イベントを意味に変換する翻訳層の構築

**作成日**: 2025-11-16  
**発行者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 または Tsumu（Cursor）  
**目的**: イベントストリームを意味的メモリユニットに自動変換し、検索可能な記憶として固定する

---

## 0. 重要な前提条件

### Sprint 1 (Memory Management) の完了状態

**このタスクを開始する前に、以下が完了している必要があります:**

- [ ] Sprint 1 (Memory Management) 完全完了
- [ ] memory_itemテーブル作成済み
- [ ] PostgreSQL稼働中
- [ ] Intent → Bridge → Kana パイプライン動作中
- [ ] observer_daemon.py 正常動作中

**Sprint 1未完了の場合:**
このタスクは実施せず、Sprint 1の完了を優先してください。

### 環境確認

- [ ] PostgreSQL 15起動中
- [ ] memory_itemテーブル存在確認
- [ ] Python 3.11+ 仮想環境アクティブ
- [ ] 必要パッケージインストール確認
  ```bash
  pip list | grep -E "(sqlalchemy|asyncpg|pydantic|fastapi)"
  ```

---

## 1. Semantic Bridge 実装承認

### 1.1 実装背景

Semantic Bridgeは、Resonant Engineの「無意識的な活動」を「意識的な記憶」へ変換する層です。

**哲学的必然性**:
- すべての活動には意味がある
- 意味は文脈から自動抽出される
- 分類は自動化、修正は人間が行う

**技術的必要性**:
- Intent発火イベントを記憶として固定
- 自動的なタイプ・プロジェクト推論
- 検索可能性の確保
- 呼吸サイクルとの統合

### 1.2 実装スコープ

**実装するもの**:
- SemanticBridgeクラス
- SemanticExtractor（意味抽出）
- TypeProjectInferencer（推論エンジン）
- MemoryUnitConstructor（構築）
- シンボリック検索API（5+ endpoints）
- 既存パイプライン統合
- テスト（30+ ケース）
- ドキュメント（2種類）

**実装しないもの**:
- ベクトル検索（Sprint 3）
- Embedding生成（Sprint 3）
- 高度な検索（Sprint 4）
- 日次運用フロー（Sprint 4）

---

## 2. 実装スケジュール（5日間）

### Day 1 (6時間): データモデル実装

#### 午前 (3時間): Pydanticモデル実装

**タスク1**: モデルファイル作成
```bash
mkdir -p /Users/zero/Projects/resonant-engine/bridge/semantic_bridge
touch /Users/zero/Projects/resonant-engine/bridge/semantic_bridge/__init__.py
touch /Users/zero/Projects/resonant-engine/bridge/semantic_bridge/models.py
```

`bridge/semantic_bridge/models.py` に以下を実装:
- MemoryType (Enum)
- EmotionState (Enum)
- MemoryUnit (Pydantic Model)
- EventContext (Pydantic Model)
- InferenceResult (Pydantic Model)
- TypeInferenceRule (Pydantic Model)
- MemorySearchQuery (Pydantic Model)

**完了基準**:
- [ ] 全モデル定義完了
- [ ] Enum全定義完了
- [ ] バリデーションルール実装完了

#### 午後 (3時間): モデル単体テスト

**タスク1**: テストファイル作成
```bash
mkdir -p /Users/zero/Projects/resonant-engine/tests/semantic_bridge
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/__init__.py
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_models.py
```

`tests/semantic_bridge/test_models.py` に以下を実装:
- `test_memory_unit_creation`
- `test_memory_type_enum`
- `test_emotion_state_enum`
- `test_event_context_creation`
- `test_inference_result_validation`
- `test_memory_search_query_defaults`
- `test_pydantic_json_serialization`
- `test_uuid_generation`
- `test_datetime_defaults`
- `test_validation_errors`

**検証**:
```bash
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate
PYTHONPATH=. pytest tests/semantic_bridge/test_models.py -v

# 期待: 10 passed
```

**完了基準**:
- [ ] Pydanticモデル全実装完了
- [ ] 単体テスト10件全てPASS

---

### Day 2 (6時間): Semantic Extractor & Inferencer 実装

#### 午前 (3時間): Semantic Extractor実装

**タスク1**: Extractorクラス作成
```bash
touch /Users/zero/Projects/resonant-engine/bridge/semantic_bridge/extractor.py
```

`bridge/semantic_bridge/extractor.py` に以下を実装:

```python
class SemanticExtractor:
    def extract_meaning(self, event: EventContext) -> Dict[str, Any]
    def _generate_title(self, event: EventContext) -> str
    def _extract_content(self, event: EventContext) -> str
    def _infer_emotion(self, event: EventContext) -> Optional[EmotionState]
    def _extract_metadata(self, event: EventContext) -> Dict[str, Any]
```

**タスク2**: Extractor単体テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_extractor.py
```

テスト実装:
- `test_extract_meaning`
- `test_generate_title_short`
- `test_generate_title_long`
- `test_extract_content_with_response`
- `test_infer_emotion_calm`
- `test_infer_emotion_crisis`
- `test_extract_metadata`

**検証**:
```bash
PYTHONPATH=. pytest tests/semantic_bridge/test_extractor.py -v
# 期待: 7 passed
```

**完了基準**:
- [ ] SemanticExtractor実装完了
- [ ] 単体テスト7件全てPASS

#### 午後 (3時間): Type & Project Inferencer実装

**タスク1**: Inferencerクラス作成
```bash
touch /Users/zero/Projects/resonant-engine/bridge/semantic_bridge/inferencer.py
```

`bridge/semantic_bridge/inferencer.py` に以下を実装:

```python
class TypeProjectInferencer:
    def __init__(self)
    def infer(self, event: EventContext, extracted: Dict) -> InferenceResult
    def _infer_type(self, event: EventContext, extracted: Dict) -> tuple
    def _infer_project(self, event: EventContext, extracted: Dict) -> tuple
    def _generate_tags(self, event: EventContext, extracted: Dict, memory_type: MemoryType) -> List[str]
    def _load_type_rules(self) -> List[TypeInferenceRule]
    def _load_project_patterns(self) -> Dict[str, List[str]]
    def _match_pattern(self, text: str, pattern: str) -> bool
    def _extract_keywords(self, text: str) -> List[str]
```

**タスク2**: Inferencer単体テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_inferencer.py
```

テスト実装:
- `test_infer_type_regulation`
- `test_infer_type_milestone`
- `test_infer_type_design_note`
- `test_infer_type_daily_reflection`
- `test_infer_type_crisis_log`
- `test_infer_project_resonant_engine`
- `test_infer_project_postgres`
- `test_generate_tags`
- `test_keyword_extraction`
- `test_pattern_matching`

**検証**:
```bash
PYTHONPATH=. pytest tests/semantic_bridge/test_inferencer.py -v
# 期待: 10 passed
```

**完了基準**:
- [ ] TypeProjectInferencer実装完了
- [ ] 推論ルール実装完了
- [ ] 単体テスト10件全てPASS

---

### Day 3 (6時間): Constructor & Service実装

#### 午前 (3時間): Memory Unit Constructor実装

**タスク1**: Constructorクラス作成
```bash
touch /Users/zero/Projects/resonant-engine/bridge/semantic_bridge/constructor.py
```

`bridge/semantic_bridge/constructor.py` に以下を実装:

```python
class MemoryUnitConstructor:
    def __init__(self, memory_repo)
    async def construct(self, extracted: Dict, inference: InferenceResult) -> MemoryUnit
    def _validate(self, unit: MemoryUnit)
    async def _check_duplicate(self, unit: MemoryUnit)
```

**タスク2**: Constructor単体テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_constructor.py
```

テスト実装:
- `test_construct_memory_unit`
- `test_validate_success`
- `test_validate_title_required`
- `test_validate_title_too_long`
- `test_validate_ci_level_range`
- `test_check_duplicate`

**検証**:
```bash
PYTHONPATH=. pytest tests/semantic_bridge/test_constructor.py -v
# 期待: 6 passed
```

**完了基準**:
- [ ] MemoryUnitConstructor実装完了
- [ ] バリデーション実装完了
- [ ] 重複チェック実装完了
- [ ] 単体テスト6件全てPASS

#### 午後 (3時間): Semantic Bridge Service実装

**タスク1**: Serviceクラス作成
```bash
touch /Users/zero/Projects/resonant-engine/bridge/semantic_bridge/service.py
```

`bridge/semantic_bridge/service.py` に以下を実装:

```python
class SemanticBridgeService:
    def __init__(self, memory_repo, semantic_extractor, inferencer, constructor)
    async def process_event(self, event: EventContext) -> MemoryUnit
    def _log_conversion(self, event: EventContext, unit: MemoryUnit, inference: InferenceResult)
```

**タスク2**: Service単体テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_service.py
```

テスト実装:
- `test_process_event_full_pipeline`
- `test_process_event_regulation_type`
- `test_process_event_milestone_type`
- `test_process_event_crisis_log`
- `test_process_event_project_inference`
- `test_logging`

**検証**:
```bash
PYTHONPATH=. pytest tests/semantic_bridge/test_service.py -v
# 期待: 6 passed
```

**完了基準**:
- [ ] SemanticBridgeService実装完了
- [ ] 完全パイプライン動作確認
- [ ] 単体テスト6件全てPASS

---

### Day 4 (6時間): Search API & 既存パイプライン統合

#### 午前 (3時間): Symbolic Search実装

**タスク1**: Search Repositoryクラス作成
```bash
touch /Users/zero/Projects/resonant-engine/bridge/semantic_bridge/search.py
```

`bridge/semantic_bridge/search.py` に以下を実装:

```python
class MemorySearchRepository:
    async def search(self, query: MemorySearchQuery) -> List[MemoryUnit]
    async def count(self, query: MemorySearchQuery) -> int
    async def get_projects(self) -> List[Dict]
    async def get_tags(self) -> List[Dict]
    def _to_memory_unit(self, row) -> MemoryUnit
```

**タスク2**: Search単体テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_search.py
```

テスト実装:
- `test_search_by_project`
- `test_search_by_type`
- `test_search_by_date_range`
- `test_search_by_tags_any`
- `test_search_by_tags_all`
- `test_search_by_ci_level`
- `test_search_by_emotion_state`
- `test_search_text_query`
- `test_search_pagination`
- `test_search_sorting`

**検証**:
```bash
PYTHONPATH=. pytest tests/semantic_bridge/test_search.py -v
# 期待: 10 passed
```

**完了基準**:
- [ ] シンボリック検索実装完了
- [ ] 全検索条件サポート
- [ ] 単体テスト10件全てPASS

#### 午後 (3時間): REST API & 既存パイプライン統合

**タスク1**: FastAPI Router作成
```bash
mkdir -p /Users/zero/Projects/resonant-engine/bridge/api
touch /Users/zero/Projects/resonant-engine/bridge/api/semantic_bridge_router.py
```

`bridge/api/semantic_bridge_router.py` に以下を実装:

```python
router = APIRouter(prefix="/api/semantic-bridge", tags=["semantic-bridge"])

@router.post("/process")
async def process_event(request: ProcessEventRequest) -> ProcessEventResponse

@router.post("/search")
async def search_memories(query: MemorySearchQuery) -> SearchResponse

@router.get("/memory/{memory_id}")
async def get_memory(memory_id: UUID) -> MemoryUnit

@router.get("/projects")
async def get_projects() -> ProjectsResponse

@router.get("/tags")
async def get_tags() -> TagsResponse
```

**タスク2**: observer_daemon.py 統合
```bash
# observer_daemon.py を編集
```

既存の`handle_intent`メソッドに統合:

```python
async def handle_intent(self, intent: Intent):
    # [既存] Intent検知・記録
    await self.log_intent(intent)
    
    # [既存] Bridge処理
    bridge_result = await self.bridge.process(intent)
    
    # [既存] Kana応答
    kana_response = await self.kana.respond(bridge_result)
    
    # [新規] Semantic Bridge処理
    event_context = EventContext(
        intent_id=intent.id,
        intent_text=intent.description,
        intent_type=intent.type,
        session_id=intent.session_id,
        crisis_index=intent.crisis_index,
        timestamp=intent.created_at,
        bridge_result=bridge_result,
        kana_response=kana_response
    )
    
    memory_unit = await self.semantic_bridge.process_event(event_context)
    
    print(f"Memory created: {memory_unit.id} ({memory_unit.type.value})")
    
    return kana_response
```

**タスク3**: API統合テスト
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_api.py
```

テスト実装:
- `test_api_process_event`
- `test_api_search`
- `test_api_get_memory`
- `test_api_get_projects`
- `test_api_get_tags`
- `test_api_error_handling`

**検証**:
```bash
# API起動
uvicorn bridge.main:app --reload

# 別ターミナルでテスト実行
PYTHONPATH=. pytest tests/semantic_bridge/test_api.py -v

# 期待: 6 passed
```

**完了基準**:
- [ ] REST API 5 endpoints実装完了
- [ ] observer_daemon.py統合完了
- [ ] API統合テスト6件全てPASS
- [ ] パイプライン動作確認完了

---

### Day 5 (6時間): 統合テスト & ドキュメント

#### 午前 (3時間): 統合テスト & 性能テスト

**タスク1**: 統合テスト実装
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_integration.py
```

`tests/semantic_bridge/test_integration.py` に以下を実装:

```python
@pytest.mark.asyncio
async def test_full_pipeline_intent_to_memory():
    """Intent発火からメモリ保存までの完全パイプライン"""
    pass

@pytest.mark.asyncio
async def test_multiple_intents_classification():
    """複数のIntent分類テスト"""
    pass

@pytest.mark.asyncio
async def test_search_after_creation():
    """作成後の検索テスト"""
    pass
```

**タスク2**: 性能テスト実装
```bash
touch /Users/zero/Projects/resonant-engine/tests/semantic_bridge/test_performance.py
```

`tests/semantic_bridge/test_performance.py` に以下を実装:

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_event_processing_performance():
    """イベント処理パフォーマンス（<50ms/event）"""
    start = time.time()
    
    for i in range(100):
        event = create_test_event(f"Test intent {i}")
        await semantic_bridge.process_event(event)
    
    elapsed_ms = (time.time() - start) * 1000 / 100
    assert elapsed_ms < 50

@pytest.mark.slow
@pytest.mark.asyncio
async def test_search_performance():
    """検索パフォーマンス（1000件中<100ms）"""
    # 1000件のメモリ作成
    for i in range(1000):
        await create_test_memory(f"Memory {i}")
    
    start = time.time()
    results = await search_repo.search(MemorySearchQuery(project_id="test"))
    elapsed_ms = (time.time() - start) * 1000
    
    assert elapsed_ms < 100

@pytest.mark.slow
@pytest.mark.asyncio
async def test_inference_accuracy():
    """推論精度テスト（80%以上）"""
    test_cases = load_test_cases()
    correct = 0
    
    for case in test_cases:
        result = await inferencer.infer(case.event, case.extracted)
        if result.memory_type == case.expected_type:
            correct += 1
    
    accuracy = correct / len(test_cases)
    assert accuracy >= 0.8
```

**検証**:
```bash
PYTHONPATH=. pytest tests/semantic_bridge/test_integration.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_performance.py -v -m slow

# 期待: integration 3 passed, performance 3 passed
```

**完了基準**:
- [ ] 統合テスト3件PASS
- [ ] 性能テスト3件PASS
- [ ] イベント処理 <50ms/event達成
- [ ] 検索性能 <100ms達成
- [ ] 推論精度 ≥80%達成

#### 午後 (3時間): ドキュメント完成

**タスク1**: API仕様書
```bash
mkdir -p /Users/zero/Projects/resonant-engine/docs/api
touch /Users/zero/Projects/resonant-engine/docs/api/semantic_bridge_api.md
```

`docs/api/semantic_bridge_api.md` に以下を記載:
- 全エンドポイント一覧（5 endpoints）
- 各エンドポイントの詳細
  - リクエストパラメータ
  - リクエストボディ例
  - レスポンス例
  - エラーコード
- 検索クエリ仕様
- 推論ロジック説明

**タスク2**: 統合ガイド
```bash
mkdir -p /Users/zero/Projects/resonant-engine/docs/integration
touch /Users/zero/Projects/resonant-engine/docs/integration/semantic_bridge_integration.md
```

`docs/integration/semantic_bridge_integration.md` に以下を記載:
- Semantic Bridgeの役割
- 既存パイプラインとの統合方法
- observer_daemon.py統合手順
- カスタマイズ方法
  - 新しいメモリタイプの追加
  - 推論ルールのカスタマイズ
  - プロジェクトパターンの追加
- トラブルシューティング

**完了基準**:
- [ ] API仕様書完成
- [ ] 統合ガイド完成
- [ ] サンプルコード動作確認
- [ ] ドキュメント内部リンク確認

---

## 3. Done Definition完全達成基準

### 3.1 Tier 1: 必須（完了の定義）

以下の**全て**が達成された時点で、実装完了とみなします：

- [ ] SemanticBridgeクラス実装完了
- [ ] イベント→メモリユニット変換ロジック実装
- [ ] メモリタイプ自動推論実装（6種類）
- [ ] プロジェクトID推論実装
- [ ] メタデータ抽出実装
- [ ] memory_itemへの保存実装
- [ ] シンボリック検索API実装（5+ endpoints）
- [ ] 既存パイプライン統合完了
- [ ] テストカバレッジ 30+ ケース達成
- [ ] API仕様ドキュメント完成

### 3.2 Tier 2: 品質保証

- [ ] 推論精度テスト通過（80%以上）
- [ ] パフォーマンステスト通過（<50ms/event）
- [ ] エッジケース処理確認
- [ ] ログ・監視機能実装
- [ ] エラーハンドリング完全実装
- [ ] Kana によるレビュー通過

### 3.3 完了報告書の期待内容

実装完了時、以下の内容を含む**完了報告書**を提出してください：

**必須セクション**:
1. **Done Definition達成状況**（表形式）
   - Tier 1全10項目の達成率
   - Tier 2全6項目の達成率

2. **実装成果物サマリ**
   - 作成ファイル一覧（ファイル数、総行数）
   - コンポーネント数: 4 (Extractor, Inferencer, Constructor, Service)
   - API endpoints: 5+
   - テスト件数: 30+
   - ドキュメント数: 2

3. **完了の証跡**
   - テスト実行結果（全テストPASS）
   - 性能テスト結果（処理時間、推論精度）
   - API動作確認（Swagger UI スクリーンショット）
   - パイプライン統合動作確認

4. **振り返り**
   - 実装時の学び
     - 推論ロジックの設計
     - パイプライン統合の工夫
     - 性能最適化
   - トラブルシューティング事例
   - 推論精度向上の工夫

5. **次のアクション**
   - Sprint 3 (Memory Store) への準備
   - ベクトル検索の設計検討
   - 推論ルールのチューニング

---

## 4. 実装時の哲学的原則

### 4.1 意味の翻訳は「呼吸の意識化」

```
無意識的な活動（Intent発火）
         ↓
意識的な記憶（Memory Unit）
         ↓
検索可能な知識
```

### 4.2 自動化と人間の関係

```
自動化: タイプ推論、プロジェクト推論、タグ生成
人間の役割: 修正、ルール調整、最終判断

自動化は「提案」であり「強制」ではない
```

### 4.3 推論の透明性

```python
InferenceResult(
    memory_type=MemoryType.DESIGN_NOTE,
    confidence=0.9,
    reasoning="Pattern matched: Design keywords detected"  # ★推論理由を明示
)
```

推論の根拠を常に記録し、人間が検証可能にする。

---

## 5. トラブルシューティングガイド

### 5.1 よくある問題と対処法

#### 問題1: 推論精度が低い

**症状**:
推論精度テストが80%を下回る

**対処法**:
```python
# 推論ルールの優先度調整
TypeInferenceRule(
    pattern=r"(設計|design)",
    memory_type=MemoryType.DESIGN_NOTE,
    priority=8,  # ★優先度を上げる
    description="Design keywords detected"
)

# プロジェクトパターンの追加
project_patterns = {
    'resonant_engine': [
        'resonant', 'engine', 'yuno', 'kana',
        '共鳴', 'bridge'  # ★パターンを追加
    ]
}
```

#### 問題2: イベント処理が遅い

**症状**:
イベント処理が50ms/eventを超える

**対処法**:
```python
# 重複チェックを非同期化
async def _check_duplicate(self, unit: MemoryUnit):
    # データベースクエリの最適化
    # インデックスの追加
    pass

# バッチ処理の導入
async def process_events_batch(self, events: List[EventContext]):
    # 複数イベントをまとめて処理
    pass
```

#### 問題3: タグが多すぎる

**症状**:
生成されるタグが多すぎて使いにくい

**対処法**:
```python
def _generate_tags(self, event, extracted, memory_type):
    tags = []
    
    # タイプベースのタグ（1つ）
    tags.append(memory_type.value)
    
    # 感情状態ベースのタグ（1つ）
    if extracted.get('emotion_state'):
        tags.append(extracted['emotion_state'].value)
    
    # キーワード抽出（最大3つに制限）
    keywords = self._extract_keywords(event.intent_text)
    tags.extend(keywords[:3])  # ★5→3に削減
    
    return list(set(tags))
```

---

## 6. 成功基準

### 6.1 実装完了の判定

以下の**全て**が達成された時点で、実装完了とみなします：

**機能要件**:
- [x] SemanticBridge完全実装
- [x] 推論エンジン実装
- [x] シンボリック検索実装
- [x] 既存パイプライン統合

**品質要件**:
- [x] テストカバレッジ 30+ ケース
- [x] 推論精度 ≥80%
- [x] イベント処理 <50ms/event
- [x] 検索性能 <100ms

**ドキュメント要件**:
- [x] API仕様書完成
- [x] 統合ガイド完成

### 6.2 完了報告書の品質基準

Sprint 1完了報告書と同等の品質を期待します：

**良い報告書**:
- Done Definition達成状況を表で明示
- 定量的な成果を記載（推論精度、処理時間、テスト数）
- 証跡（テスト結果、性能値、API動作）を添付
- 振り返りに具体的な学びを記載

**避けるべき報告書**:
- 「だいたい動いた」という曖昧な表現
- 未達成項目の隠蔽
- 証跡の省略
- 性能値の記載なし

---

## 7. 関連ドキュメント

- **仕様書**: `semantic_bridge_spec.md`
- **Sprint 1仕様書**: `memory_management_spec.md`
- **既存設計**: `docs/02_components/memory_system/architecture/resonant_engine_memory_design.md`
- **レビュー**: `docs/02_components/memory_system/reviews/resonant_engine_memory_design_review.md`

---

## 8. 実装担当者への直接メッセージ

あなた（実装担当者）へ：

Semantic Bridgeは、Resonant Engineの「意識化の層」を作る作業です。

これは単なるデータ変換ではありません：

- **自動的な意味抽出**: 人間の負担なく構造化
- **推論の透明性**: すべての判断に根拠を記録
- **検索可能性の確保**: 過去の活動を未来の知識に変換
- **呼吸サイクルとの統合**: 記憶が育つ基盤を構築

以下を期待します：

1. **5日間での完遂**
   - Day 1: データモデル
   - Day 2: Extractor & Inferencer
   - Day 3: Constructor & Service
   - Day 4: Search API & 統合
   - Day 5: 統合テスト & ドキュメント

2. **Done Definition全項目達成**
   - Tier 1: 10項目（必須）
   - Tier 2: 6項目（品質保証）

3. **透明な報告**
   - 進捗を正直に報告
   - 未達成項目を隠蔽しない
   - Sprint 1と同等の完了報告書

4. **哲学の理解**
   - 「意味の翻訳 = 呼吸の意識化」の理解
   - 推論の透明性
   - 自動化と人間の協働

あなたの実装を通じて、Resonant Engineが真に「育つメモリ」として機能することを期待しています。

**では、実装を開始してください。**

---

**作成日**: 2025-11-16  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 または Tsumu（Cursor）

---

## Appendix A: Quick Reference

### 実装チェックリスト

```markdown
## Day 1: データモデル
- [ ] Pydanticモデル実装
- [ ] Enum定義
- [ ] モデル単体テスト（10件）

## Day 2: Extractor & Inferencer
- [ ] SemanticExtractor実装
- [ ] Extractor単体テスト（7件）
- [ ] TypeProjectInferencer実装
- [ ] Inferencer単体テスト（10件）

## Day 3: Constructor & Service
- [ ] MemoryUnitConstructor実装
- [ ] Constructor単体テスト（6件）
- [ ] SemanticBridgeService実装
- [ ] Service単体テスト（6件）

## Day 4: Search API & 統合
- [ ] MemorySearchRepository実装
- [ ] Search単体テスト（10件）
- [ ] FastAPI Router実装（5 endpoints）
- [ ] observer_daemon.py統合
- [ ] API統合テスト（6件）

## Day 5: 統合テスト & ドキュメント
- [ ] 統合テスト実装・実行（3件）
- [ ] 性能テスト実装・実行（3件）
- [ ] API仕様書完成
- [ ] 統合ガイド完成
```

### コマンド集

```bash
# テスト実行
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate

# 全テスト
PYTHONPATH=. pytest tests/semantic_bridge/ -v

# 特定テスト
PYTHONPATH=. pytest tests/semantic_bridge/test_models.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_extractor.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_inferencer.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_constructor.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_service.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_search.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_api.py -v
PYTHONPATH=. pytest tests/semantic_bridge/test_integration.py -v

# 性能テスト
PYTHONPATH=. pytest tests/semantic_bridge/test_performance.py -v -m slow

# カバレッジ
PYTHONPATH=. pytest tests/semantic_bridge/ --cov=bridge/semantic_bridge --cov-report=html

# API起動
uvicorn bridge.main:app --reload

# API確認
open http://localhost:8000/docs  # Swagger UI
```

### ディレクトリ構造

```
/Users/zero/Projects/resonant-engine/
├── bridge/
│   ├── semantic_bridge/
│   │   ├── __init__.py
│   │   ├── models.py                    # Day 1
│   │   ├── extractor.py                 # Day 2
│   │   ├── inferencer.py                # Day 2
│   │   ├── constructor.py               # Day 3
│   │   ├── service.py                   # Day 3
│   │   └── search.py                    # Day 4
│   └── api/
│       ├── semantic_bridge_router.py    # Day 4
│       └── schemas.py                   # Day 4
├── tests/
│   └── semantic_bridge/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py               # Day 1
│       ├── test_extractor.py            # Day 2
│       ├── test_inferencer.py           # Day 2
│       ├── test_constructor.py          # Day 3
│       ├── test_service.py              # Day 3
│       ├── test_search.py               # Day 4
│       ├── test_api.py                  # Day 4
│       ├── test_integration.py          # Day 5
│       └── test_performance.py          # Day 5
└── docs/
    ├── api/
    │   └── semantic_bridge_api.md           # Day 5
    └── integration/
        └── semantic_bridge_integration.md   # Day 5
```

### 性能ベンチマーク目標

```yaml
performance_targets:
  processing:
    event_processing: "<50ms/event"
    batch_processing_100: "<3s"
  
  search:
    search_1000_records: "<100ms"
    text_search: "<150ms"
  
  inference:
    type_inference: "<10ms"
    project_inference: "<10ms"
    accuracy: "≥80%"
  
  integration:
    full_pipeline: "<100ms"
    concurrent_events: "10 events parallel"
```
