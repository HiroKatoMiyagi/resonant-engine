# Semantic Bridge System Specification
## L1: Event to Memory Unit Conversion Layer

**実装期間**: Sprint 2 (5日間)  
**優先度**: P2  
**前提条件**: Sprint 1 (Memory Management) 完了、PostgreSQL稼働中  
**目的**: イベントストリームを意味的メモリユニットに変換し、永続化する

---

## CRITICAL: Semantic Bridge の本質

**⚠️ IMPORTANT: 「意味の翻訳」は「呼吸の意識化」である**

Semantic Bridgeは単なるデータ変換ではなく、Resonant Engineの「無意識的な活動」を「意識的な記憶」へ変換する層です。

### Semantic Bridge Philosophy

```yaml
semantic_bridge_philosophy:
  essence: "イベント = 生の活動 → メモリユニット = 意味の結晶"
  purpose:
    - 時系列イベントを意味単位に分節化
    - 文脈を保持しつつ構造化
    - プロジェクトとタイプの自動推論
    - 検索可能性の確保
  principles:
    - 「すべての活動には意味がある」
    - 「意味は文脈から抽出される」
    - 「分類は自動化、修正は人間」
```

### なぜこれが必要か

1. **Intent → Memory の橋渡し**
   - Intent発火イベントを記憶として固定
   - 一時的な活動を永続的な知識に変換

2. **自動的な意味抽出**
   - project_id、type、tagsを自動推論
   - 人間の負担なく構造化

3. **検索可能性の確保**
   - シンボリック検索の基盤
   - 時間軸・プロジェクト軸での検索

4. **呼吸サイクルとの統合**
   - 各フェーズの活動を自動記録
   - session_summary、daily_reflectionの自動生成

---

## 0. Semantic Bridge Overview

### 0.1 目的

Intent→Bridge→Kanaパイプラインで発生するイベントを意味的なメモリユニットに変換し、memory_itemテーブルに永続化する。

### 0.2 スコープ

**IN Scope**:
- イベントの意味的分節化
- メモリタイプの自動推論
- プロジェクトIDの自動推論
- メタデータ付与（tags, ci_level, emotion_state）
- memory_itemへの保存
- シンボリック検索API
- 基本的なCRUD操作
- 既存パイプラインとの統合

**OUT of Scope**:
- ベクトル検索（Sprint 3で実装）
- Embedding生成（Sprint 3で実装）
- 高度な検索（Sprint 4で実装）
- 日次運用フロー（Sprint 4で実装）

### 0.3 Done Definition

#### Tier 1: 必須（完了の定義）
- [ ] SemanticBridgeクラス実装完了
- [ ] イベント→メモリユニット変換ロジック実装
- [ ] メモリタイプ自動推論実装（6種類）
- [ ] プロジェクトID推論実装
- [ ] メタデータ抽出実装（tags, ci_level, emotion_state）
- [ ] memory_itemへの保存実装
- [ ] シンボリック検索API実装（5+ endpoints）
- [ ] 既存パイプライン統合完了
- [ ] テストカバレッジ 30+ ケース達成
- [ ] API仕様ドキュメント完成

#### Tier 2: 品質保証
- [ ] 推論精度テスト通過（80%以上）
- [ ] パフォーマンステスト通過（<50ms/event）
- [ ] エッジケース処理確認
- [ ] ログ・監視機能実装
- [ ] エラーハンドリング完全実装
- [ ] Kana によるレビュー通過

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Existing Intent Pipeline                        │
│                                                                  │
│  Intent発火 → observer_daemon → intent_events テーブル           │
│             → Bridge処理 → Kana応答                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Semantic Bridge (L1)                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Event Listener                               │  │
│  │  • Intent発火イベントを監視                              │  │
│  │  • Bridge処理完了イベントを監視                          │  │
│  │  • Kana応答イベントを監視                                │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │           Semantic Extractor                              │  │
│  │  • 意味的分節化                                           │  │
│  │  • 文脈抽出                                               │  │
│  │  • メタデータ生成                                         │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │         Type & Project Inferencer                         │  │
│  │  • メモリタイプ推論                                       │  │
│  │  • プロジェクトID推論                                     │  │
│  │  • タグ抽出                                               │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │         Memory Unit Constructor                           │  │
│  │  • MemoryUnitオブジェクト構築                             │  │
│  │  • バリデーション                                         │  │
│  │  • 重複チェック                                           │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │           Memory Persistence                              │  │
│  │  • memory_itemへの保存                                    │  │
│  │  • トランザクション管理                                   │  │
│  │  • エラーハンドリング                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              Memory Item Repository (from Sprint 1)              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Symbolic Search Engine                       │  │
│  │  • プロジェクトID検索                                     │  │
│  │  • タイプフィルタリング                                   │  │
│  │  • 時間範囲指定                                           │  │
│  │  • タグ検索                                               │  │
│  │  • CI Level範囲指定                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
[Intent発火]
    ↓
[observer_daemon検知]
    ↓
[intent_eventsに記録]
    ↓
[SemanticBridge.process_event()]
    ↓
    ├─ Semantic Extractor: 意味抽出
    │   ├─ Intent内容解析
    │   ├─ 文脈情報抽出
    │   └─ CI Level取得
    │
    ├─ Type & Project Inferencer: 推論
    │   ├─ メモリタイプ判定
    │   ├─ プロジェクトID判定
    │   └─ タグ生成
    │
    ├─ Memory Unit Constructor: 構築
    │   ├─ MemoryUnitオブジェクト生成
    │   ├─ バリデーション
    │   └─ 重複チェック
    │
    └─ Memory Persistence: 保存
        └─ memory_itemテーブルINSERT
    ↓
[検索可能な記憶として固定]
```

---

## 2. Data Models

### 2.1 Memory Unit (Pydantic Model)

```python
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class MemoryType(str, Enum):
    """メモリタイプ（既存のmemory_itemスキーマと一致）"""
    SESSION_SUMMARY = "session_summary"
    DAILY_REFLECTION = "daily_reflection"
    PROJECT_MILESTONE = "project_milestone"
    RESONANT_REGULATION = "resonant_regulation"
    DESIGN_NOTE = "design_note"
    CRISIS_LOG = "crisis_log"


class EmotionState(str, Enum):
    """感情状態"""
    CALM = "calm"
    FOCUSED = "focused"
    STRESSED = "stressed"
    CRISIS = "crisis"
    EXCITED = "excited"
    NEUTRAL = "neutral"


class MemoryUnit(BaseModel):
    """意味的メモリユニット"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = "hiroki"  # Phase 4までは固定
    project_id: Optional[str] = None
    type: MemoryType
    
    title: str
    content: str
    content_raw: Optional[str] = None  # 元のIntent文面
    
    tags: List[str] = Field(default_factory=list)
    ci_level: Optional[int] = None
    emotion_state: Optional[EmotionState] = None
    
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventContext(BaseModel):
    """イベントの文脈情報"""
    intent_id: UUID
    intent_text: str
    intent_type: str
    session_id: Optional[UUID] = None
    
    crisis_index: Optional[int] = None
    timestamp: datetime
    
    # Bridge処理情報
    bridge_result: Optional[Dict[str, Any]] = None
    
    # Kana応答情報
    kana_response: Optional[str] = None
    
    # その他の文脈
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 2.2 Inference Result

```python
class InferenceResult(BaseModel):
    """推論結果"""
    memory_type: MemoryType
    confidence: float  # 0.0-1.0
    reasoning: str  # 推論理由
    
    project_id: Optional[str] = None
    project_confidence: float = 0.0
    
    tags: List[str] = Field(default_factory=list)
    emotion_state: Optional[EmotionState] = None


class TypeInferenceRule(BaseModel):
    """タイプ推論ルール"""
    pattern: str  # 正規表現またはキーワード
    memory_type: MemoryType
    priority: int  # 優先度
    description: str
```

---

## 3. Core Components Implementation

### 3.1 Semantic Extractor

```python
class SemanticExtractor:
    """意味的分節化と文脈抽出"""
    
    def extract_meaning(self, event: EventContext) -> Dict[str, Any]:
        """イベントから意味を抽出"""
        return {
            'title': self._generate_title(event),
            'content': self._extract_content(event),
            'content_raw': event.intent_text,
            'ci_level': event.crisis_index,
            'emotion_state': self._infer_emotion(event),
            'started_at': event.timestamp,
            'metadata': self._extract_metadata(event)
        }
    
    def _generate_title(self, event: EventContext) -> str:
        """タイトル生成（要約的）"""
        # Intent textの最初の50文字 + 要約
        intent_text = event.intent_text
        if len(intent_text) <= 50:
            return intent_text
        
        # 最初の文を取得
        first_sentence = intent_text.split('。')[0] + '。'
        if len(first_sentence) <= 50:
            return first_sentence
        
        return intent_text[:47] + "..."
    
    def _extract_content(self, event: EventContext) -> str:
        """コンテンツ抽出"""
        parts = [event.intent_text]
        
        # Kana応答があれば追加
        if event.kana_response:
            parts.append(f"\n【応答】\n{event.kana_response}")
        
        return "\n".join(parts)
    
    def _infer_emotion(self, event: EventContext) -> Optional[EmotionState]:
        """感情状態の推論"""
        ci = event.crisis_index or 0
        
        if ci >= 70:
            return EmotionState.CRISIS
        elif ci >= 50:
            return EmotionState.STRESSED
        elif ci >= 30:
            return EmotionState.FOCUSED
        else:
            return EmotionState.CALM
    
    def _extract_metadata(self, event: EventContext) -> Dict[str, Any]:
        """メタデータ抽出"""
        return {
            'intent_id': str(event.intent_id),
            'intent_type': event.intent_type,
            'session_id': str(event.session_id) if event.session_id else None,
            'bridge_result': event.bridge_result
        }
```

### 3.2 Type & Project Inferencer

```python
class TypeProjectInferencer:
    """メモリタイプとプロジェクトIDの推論"""
    
    def __init__(self):
        self.type_rules = self._load_type_rules()
        self.project_patterns = self._load_project_patterns()
    
    def infer(self, event: EventContext, extracted: Dict[str, Any]) -> InferenceResult:
        """タイプとプロジェクトを推論"""
        # タイプ推論
        memory_type, type_confidence, reasoning = self._infer_type(event, extracted)
        
        # プロジェクト推論
        project_id, project_confidence = self._infer_project(event, extracted)
        
        # タグ生成
        tags = self._generate_tags(event, extracted, memory_type)
        
        # 感情状態（既に抽出済み）
        emotion_state = extracted.get('emotion_state')
        
        return InferenceResult(
            memory_type=memory_type,
            confidence=type_confidence,
            reasoning=reasoning,
            project_id=project_id,
            project_confidence=project_confidence,
            tags=tags,
            emotion_state=emotion_state
        )
    
    def _infer_type(self, event: EventContext, extracted: Dict[str, Any]) -> tuple:
        """メモリタイプを推論"""
        intent_text = event.intent_text.lower()
        ci_level = extracted.get('ci_level', 0)
        
        # ルールベース推論
        for rule in sorted(self.type_rules, key=lambda r: r.priority, reverse=True):
            if self._match_pattern(intent_text, rule.pattern):
                return rule.memory_type, 0.9, f"Pattern matched: {rule.description}"
        
        # CI Levelベース推論
        if ci_level >= 60:
            return MemoryType.CRISIS_LOG, 0.8, f"High CI level: {ci_level}"
        
        # デフォルト: session_summary
        return MemoryType.SESSION_SUMMARY, 0.5, "Default classification"
    
    def _infer_project(self, event: EventContext, extracted: Dict[str, Any]) -> tuple:
        """プロジェクトIDを推論"""
        intent_text = event.intent_text.lower()
        
        for project_id, patterns in self.project_patterns.items():
            for pattern in patterns:
                if pattern in intent_text:
                    return project_id, 0.9
        
        # メタデータから推論
        if event.metadata.get('project_id'):
            return event.metadata['project_id'], 1.0
        
        return None, 0.0
    
    def _generate_tags(
        self, 
        event: EventContext, 
        extracted: Dict[str, Any],
        memory_type: MemoryType
    ) -> List[str]:
        """タグを自動生成"""
        tags = []
        
        # タイプベースのタグ
        tags.append(memory_type.value)
        
        # 感情状態ベースのタグ
        if extracted.get('emotion_state'):
            tags.append(extracted['emotion_state'].value)
        
        # キーワード抽出
        keywords = self._extract_keywords(event.intent_text)
        tags.extend(keywords[:5])  # 最大5つ
        
        return list(set(tags))  # 重複除去
    
    def _load_type_rules(self) -> List[TypeInferenceRule]:
        """タイプ推論ルールをロード"""
        return [
            TypeInferenceRule(
                pattern=r"(規範|regulation|ルール|原則)",
                memory_type=MemoryType.RESONANT_REGULATION,
                priority=10,
                description="Regulation keywords detected"
            ),
            TypeInferenceRule(
                pattern=r"(マイルストーン|milestone|達成|完了した)",
                memory_type=MemoryType.PROJECT_MILESTONE,
                priority=9,
                description="Milestone keywords detected"
            ),
            TypeInferenceRule(
                pattern=r"(設計|design|アーキテクチャ|構造)",
                memory_type=MemoryType.DESIGN_NOTE,
                priority=8,
                description="Design keywords detected"
            ),
            TypeInferenceRule(
                pattern=r"(今日の振り返り|1日の|daily)",
                memory_type=MemoryType.DAILY_REFLECTION,
                priority=7,
                description="Daily reflection keywords detected"
            ),
        ]
    
    def _load_project_patterns(self) -> Dict[str, List[str]]:
        """プロジェクトパターンをロード"""
        return {
            'resonant_engine': [
                'resonant', 'engine', 'yuno', 'kana', 'tsumu',
                '呼吸', 'bridge', 'intent'
            ],
            'postgres_implementation': [
                'postgresql', 'postgres', 'database', 'db',
                'schema', 'migration'
            ],
            'memory_system': [
                'memory', 'メモリ', '記憶', 'semantic bridge'
            ]
        }
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """パターンマッチング"""
        import re
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """キーワード抽出（簡易版）"""
        # 日本語・英語の名詞的なものを抽出
        # 実装は簡易的なもの
        words = text.split()
        keywords = []
        
        for word in words:
            # 3文字以上、特定の記号を含まない
            if len(word) >= 3 and word.isalnum():
                keywords.append(word.lower())
        
        return keywords[:10]
```

### 3.3 Memory Unit Constructor

```python
class MemoryUnitConstructor:
    """メモリユニットの構築とバリデーション"""
    
    def __init__(self, memory_repo):
        self.memory_repo = memory_repo
    
    async def construct(
        self,
        extracted: Dict[str, Any],
        inference: InferenceResult
    ) -> MemoryUnit:
        """メモリユニットを構築"""
        
        # MemoryUnitオブジェクト生成
        memory_unit = MemoryUnit(
            user_id="hiroki",
            project_id=inference.project_id,
            type=inference.memory_type,
            title=extracted['title'],
            content=extracted['content'],
            content_raw=extracted['content_raw'],
            tags=inference.tags,
            ci_level=extracted.get('ci_level'),
            emotion_state=inference.emotion_state,
            started_at=extracted.get('started_at'),
            metadata={
                **extracted.get('metadata', {}),
                'inference_confidence': inference.confidence,
                'inference_reasoning': inference.reasoning,
                'project_confidence': inference.project_confidence
            }
        )
        
        # バリデーション
        self._validate(memory_unit)
        
        # 重複チェック
        await self._check_duplicate(memory_unit)
        
        return memory_unit
    
    def _validate(self, unit: MemoryUnit):
        """バリデーション"""
        if not unit.title or not unit.content:
            raise ValueError("Title and content are required")
        
        if len(unit.title) > 200:
            raise ValueError("Title too long (max 200 chars)")
        
        if unit.ci_level is not None:
            if not (0 <= unit.ci_level <= 100):
                raise ValueError("CI level must be 0-100")
    
    async def _check_duplicate(self, unit: MemoryUnit):
        """重複チェック（同一内容の記録を防ぐ）"""
        # 同じタイトル・同じ時刻（±5分）の記録がないかチェック
        existing = await self.memory_repo.find_similar(
            title=unit.title,
            timestamp=unit.started_at,
            time_threshold_minutes=5
        )
        
        if existing:
            # 重複ログを記録するが、エラーにはしない
            print(f"Warning: Similar memory found: {existing.id}")
```

### 3.4 Semantic Bridge Service

```python
class SemanticBridgeService:
    """Semantic Bridge のメインサービス"""
    
    def __init__(
        self,
        memory_repo,
        semantic_extractor: SemanticExtractor,
        inferencer: TypeProjectInferencer,
        constructor: MemoryUnitConstructor
    ):
        self.memory_repo = memory_repo
        self.semantic_extractor = semantic_extractor
        self.inferencer = inferencer
        self.constructor = constructor
    
    async def process_event(self, event: EventContext) -> MemoryUnit:
        """イベントを処理してメモリユニットを生成・保存"""
        
        # 1. 意味抽出
        extracted = self.semantic_extractor.extract_meaning(event)
        
        # 2. タイプ・プロジェクト推論
        inference = self.inferencer.infer(event, extracted)
        
        # 3. メモリユニット構築
        memory_unit = await self.constructor.construct(extracted, inference)
        
        # 4. 保存
        saved_unit = await self.memory_repo.create(memory_unit)
        
        # 5. ログ記録
        self._log_conversion(event, saved_unit, inference)
        
        return saved_unit
    
    def _log_conversion(
        self, 
        event: EventContext, 
        unit: MemoryUnit,
        inference: InferenceResult
    ):
        """変換ログを記録"""
        print(f"""
        Semantic Bridge Conversion:
          Intent: {event.intent_text[:50]}...
          → Type: {unit.type.value} (confidence: {inference.confidence})
          → Project: {unit.project_id or 'None'} (confidence: {inference.project_confidence})
          → Tags: {', '.join(unit.tags)}
          → Memory ID: {unit.id}
        """)
```

---

## 4. Symbolic Search API

### 4.1 Search Query Model

```python
class MemorySearchQuery(BaseModel):
    """メモリ検索クエリ"""
    user_id: str = "hiroki"
    
    # プロジェクトフィルタ
    project_id: Optional[str] = None
    project_ids: Optional[List[str]] = None
    
    # タイプフィルタ
    type: Optional[MemoryType] = None
    types: Optional[List[MemoryType]] = None
    
    # タグフィルタ
    tags: Optional[List[str]] = None
    tag_mode: str = "any"  # "any" or "all"
    
    # 時間範囲
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    # CI Levelフィルタ
    ci_level_min: Optional[int] = None
    ci_level_max: Optional[int] = None
    
    # 感情状態フィルタ
    emotion_states: Optional[List[EmotionState]] = None
    
    # テキスト検索（LIKE検索）
    text_query: Optional[str] = None
    
    # ページング
    limit: int = 10
    offset: int = 0
    
    # ソート
    sort_by: str = "created_at"  # created_at, ci_level
    sort_order: str = "desc"  # asc, desc
```

### 4.2 Search Repository

```python
class MemorySearchRepository:
    """メモリ検索リポジトリ"""
    
    async def search(self, query: MemorySearchQuery) -> List[MemoryUnit]:
        """シンボリック検索"""
        
        sql_parts = ["SELECT * FROM memory_item WHERE user_id = %s"]
        params = [query.user_id]
        
        # プロジェクトフィルタ
        if query.project_id:
            sql_parts.append("AND project_id = %s")
            params.append(query.project_id)
        elif query.project_ids:
            sql_parts.append("AND project_id = ANY(%s)")
            params.append(query.project_ids)
        
        # タイプフィルタ
        if query.type:
            sql_parts.append("AND type = %s")
            params.append(query.type.value)
        elif query.types:
            sql_parts.append("AND type = ANY(%s)")
            params.append([t.value for t in query.types])
        
        # タグフィルタ
        if query.tags:
            if query.tag_mode == "all":
                sql_parts.append("AND tags @> %s")
                params.append(query.tags)
            else:  # any
                sql_parts.append("AND tags && %s")
                params.append(query.tags)
        
        # 時間範囲
        if query.date_from:
            sql_parts.append("AND created_at >= %s")
            params.append(query.date_from)
        if query.date_to:
            sql_parts.append("AND created_at <= %s")
            params.append(query.date_to)
        
        # CI Level
        if query.ci_level_min is not None:
            sql_parts.append("AND ci_level >= %s")
            params.append(query.ci_level_min)
        if query.ci_level_max is not None:
            sql_parts.append("AND ci_level <= %s")
            params.append(query.ci_level_max)
        
        # 感情状態
        if query.emotion_states:
            sql_parts.append("AND emotion_state = ANY(%s)")
            params.append([e.value for e in query.emotion_states])
        
        # テキスト検索
        if query.text_query:
            sql_parts.append("AND (title ILIKE %s OR content ILIKE %s)")
            pattern = f"%{query.text_query}%"
            params.extend([pattern, pattern])
        
        # ソート
        sql_parts.append(f"ORDER BY {query.sort_by} {query.sort_order.upper()}")
        
        # ページング
        sql_parts.append("LIMIT %s OFFSET %s")
        params.extend([query.limit, query.offset])
        
        sql = " ".join(sql_parts)
        
        # 実行
        results = await self.db.fetch_all(sql, params)
        
        return [self._to_memory_unit(r) for r in results]
    
    async def count(self, query: MemorySearchQuery) -> int:
        """検索結果のカウント"""
        # search()と同じロジックでCOUNT
        pass
```

---

## 5. REST API Specification

### 5.1 Memory Creation API

#### POST /api/semantic-bridge/process

```json
// Request
{
  "event": {
    "intent_id": "uuid-here",
    "intent_text": "PostgreSQL実装のメモリ管理機能設計",
    "intent_type": "feature_request",
    "session_id": "uuid-or-null",
    "crisis_index": 25,
    "timestamp": "2025-11-16T10:00:00Z",
    "kana_response": "メモリ管理機能の設計書を作成しました..."
  }
}

// Response
{
  "memory_unit": {
    "id": "uuid-here",
    "type": "session_summary",
    "project_id": "resonant_engine",
    "title": "PostgreSQL実装のメモリ管理機能設計",
    "tags": ["session_summary", "calm", "postgresql", "memory"],
    "ci_level": 25,
    "created_at": "2025-11-16T10:00:05Z"
  },
  "inference": {
    "confidence": 0.9,
    "reasoning": "Pattern matched: Design keywords detected"
  }
}
```

### 5.2 Search API

#### POST /api/semantic-bridge/search

```json
// Request
{
  "project_id": "resonant_engine",
  "types": ["session_summary", "design_note"],
  "date_from": "2025-11-01T00:00:00Z",
  "date_to": "2025-11-16T23:59:59Z",
  "limit": 10
}

// Response
{
  "results": [
    {
      "id": "uuid-1",
      "type": "session_summary",
      "project_id": "resonant_engine",
      "title": "PostgreSQL実装のメモリ管理機能設計",
      "content": "...",
      "tags": ["session_summary", "calm", "postgresql"],
      "ci_level": 25,
      "created_at": "2025-11-16T10:00:05Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### GET /api/semantic-bridge/memory/{memory_id}

```json
// Response
{
  "id": "uuid-here",
  "user_id": "hiroki",
  "project_id": "resonant_engine",
  "type": "session_summary",
  "title": "PostgreSQL実装のメモリ管理機能設計",
  "content": "...",
  "content_raw": "...",
  "tags": ["session_summary", "calm", "postgresql"],
  "ci_level": 25,
  "emotion_state": "calm",
  "created_at": "2025-11-16T10:00:05Z",
  "metadata": {
    "intent_id": "uuid",
    "inference_confidence": 0.9
  }
}
```

#### GET /api/semantic-bridge/projects

```json
// Response
{
  "projects": [
    {
      "project_id": "resonant_engine",
      "memory_count": 45,
      "latest_memory_at": "2025-11-16T10:00:05Z"
    },
    {
      "project_id": "postgres_implementation",
      "memory_count": 12,
      "latest_memory_at": "2025-11-15T18:30:00Z"
    }
  ]
}
```

#### GET /api/semantic-bridge/tags

```json
// Response
{
  "tags": [
    {
      "tag": "postgresql",
      "count": 15
    },
    {
      "tag": "memory",
      "count": 12
    }
  ]
}
```

---

## 6. Integration with Existing Pipeline

### 6.1 observer_daemon.py への統合

```python
# observer_daemon.py への追加

from semantic_bridge.service import SemanticBridgeService
from semantic_bridge.models import EventContext

class EnhancedObserver(Observer):
    def __init__(self):
        super().__init__()
        self.semantic_bridge = SemanticBridgeService(...)  # DI
    
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

---

## 7. Testing Requirements

### 7.1 Unit Tests (30+ cases)

```python
# tests/semantic_bridge/test_extractor.py
def test_semantic_extractor_title_generation():
    """タイトル生成のテスト"""
    pass

def test_semantic_extractor_emotion_inference():
    """感情推論のテスト"""
    pass

# tests/semantic_bridge/test_inferencer.py
def test_type_inference_regulation():
    """規範タイプ推論のテスト"""
    pass

def test_type_inference_milestone():
    """マイルストーンタイプ推論のテスト"""
    pass

def test_project_inference_resonant_engine():
    """プロジェクト推論のテスト"""
    pass

def test_tag_generation():
    """タグ生成のテスト"""
    pass

# tests/semantic_bridge/test_constructor.py
def test_memory_unit_construction():
    """メモリユニット構築のテスト"""
    pass

def test_duplicate_check():
    """重複チェックのテスト"""
    pass

# tests/semantic_bridge/test_service.py
def test_full_pipeline():
    """完全パイプラインのテスト"""
    pass

# tests/semantic_bridge/test_search.py
def test_search_by_project():
    """プロジェクト検索のテスト"""
    pass

def test_search_by_type():
    """タイプ検索のテスト"""
    pass

def test_search_by_date_range():
    """日付範囲検索のテスト"""
    pass

def test_search_by_tags():
    """タグ検索のテスト"""
    pass
```

---

## 8. Success Criteria

### 8.1 機能要件
- [x] SemanticBridgeクラス実装完了
- [x] イベント→メモリユニット変換ロジック実装
- [x] メモリタイプ自動推論実装（6種類）
- [x] プロジェクトID推論実装
- [x] メタデータ抽出実装
- [x] シンボリック検索API実装（5+ endpoints）
- [x] 既存パイプライン統合完了

### 8.2 品質要件
- [x] 推論精度テスト通過（80%以上）
- [x] パフォーマンステスト通過（<50ms/event）
- [x] テストカバレッジ 30+ ケース達成
- [x] ログ・監視機能実装

### 8.3 ドキュメント要件
- [x] API仕様書完成
- [x] 統合ガイド完成

---

**作成日**: 2025-11-16  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**対象**: Sprint 2実装  
**実装予定**: Sprint 1完了後
