# Sprint 10: Choice Preservation System（完成版）仕様書

## 0. CRITICAL: Choice as Living Memory

**⚠️ IMPORTANT: 「選択 = 生きた意思決定システム・呼吸する知識」**

Choice Preservation Systemは、単なる「決定の記録」ではなく、**過去の意思決定プロセス全体を生きた知識として保持**し、未来の判断に活用するシステムです。「なぜこの選択をしたのか」「なぜ他の選択を却下したのか」という思考過程を保存することで、一貫性を保ち、同じ議論の繰り返しを防ぎます。

```yaml
choice_preservation_philosophy:
    essence: "選択 = 思考過程の結晶（意思決定の呼吸）"
    purpose:
        - 過去の判断理由の完全保存
        - 却下理由の構造化記録
        - 歴史的検索による知識再利用
        - Context Assemblerとの統合
    principles:
        - "選択は結果だけでなくプロセスを保存"
        - "却下された選択肢にも価値がある"
        - "未来の自分に知識を継承する"
        - "同じ議論を二度しない"
```

### 呼吸サイクルとの関係

```
Choice Preservation (意思決定の呼吸)
    ↓
Inhale: 複数の選択肢が提示される
    ↓
Resonance: 各選択肢を評価・議論
    ↓
Structure: 選択と理由を構造化
    ↓
Decide: 最終決定と却下理由記録
    ↓
Reflect: 未来の対話で参照
    ↓
Expand: 知識として再利用
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] `Choice`モデルに`rejection_reason`フィールド追加
- [ ] 歴史的クエリ機能実装（タグ検索・時間範囲・フルテキスト）
- [ ] Context Assemblerとの統合（過去選択の自動注入）
- [ ] 10件以上の単体/統合テストが作成され、CI で緑
- [ ] 既存Choice Point機能との後方互換性

#### Tier 2: 品質要件
- [ ] クエリレスポンス < 500ms（100件検索）
- [ ] 却下理由が全選択肢で保存可能
- [ ] タグベース検索が正確に動作
- [ ] Observability: `choice_decision_count`, `choice_query_count`

---

## 1. 概要

### 1.1 目的
Sprint 8で実装された基本的なChoice Point機能を完成版に拡張し、**却下理由の構造化保存**、**歴史的クエリ**、**Context Assemblerとの統合**を実装する。

### 1.2 背景

**Sprint 8までの成果:**
- Sprint 5: Context Assembler実装（3層記憶統合）
- Sprint 6: Intent Bridge統合完了
- Sprint 7: Session Summary自動生成完了
- Sprint 8: User Profile & Persistent Context完了
  - **Choice Point基本実装済み（30%完成）**

**現状の実装:**
```python
# bridge/memory/models.py:229-271
class ChoicePoint(BaseModel):
    question: str
    choices: List[Choice]
    selected_choice_id: Optional[str]
    decision_rationale: Optional[str]
    created_at: datetime
    decided_at: Optional[datetime]

class Choice(BaseModel):
    choice_id: str
    choice_text: str
    # ❌ 却下理由がない！
```

**問題点:**
1. **却下理由が記録されない**
   - 「なぜPostgreSQLを選んだか」は記録される
   - 「なぜSQLiteを却下したか」は記録されない
   - 3ヶ月後、なぜ却下したかが分からない

2. **歴史的検索ができない**
   - 「データベース関連の選択」を検索できない
   - 「3ヶ月前の技術選定」を時間範囲で絞れない
   - フルテキスト検索が未実装

3. **Context Assemblerと連携していない**
   - 過去の選択が自動的に対話に注入されない
   - 同じ議論を繰り返してしまう

### 1.3 目標
- `Choice`モデルに却下理由フィールド追加
- タグベース・時間範囲・フルテキスト検索実装
- Context Assemblerとの統合
- APIエンドポイント拡張

### 1.4 スコープ

**含む:**
- Choiceモデル拡張（`rejection_reason`, `evaluation_score`, `tags`）
- ChoicePointモデル拡張（`tags`, `context_type`）
- 歴史的クエリ機能（タグ・時間・フルテキスト）
- Context Assembler統合
- API拡張（検索エンドポイント）

**含まない（将来拡張）:**
- AI判定による自動評価スコア計算
- グラフ可視化機能
- 選択肢のバージョニング

---

## 2. ユースケース

### 2.1 却下理由の完全保存

**シナリオ:**
データベース選定で3つの選択肢を評価し、PostgreSQLを選択。

**Before（Sprint 8）:**
```json
{
  "question": "データベース選定",
  "choices": [
    {"choice_id": "A", "choice_text": "PostgreSQL"},
    {"choice_id": "B", "choice_text": "SQLite"},
    {"choice_id": "C", "choice_text": "MongoDB"}
  ],
  "selected_choice_id": "A",
  "decision_rationale": "スケーラビリティと拡張性を考慮"
}
```

**問題**: なぜSQLiteとMongoDBを却下したか不明

**After（Sprint 10）:**
```json
{
  "question": "データベース選定",
  "choices": [
    {
      "choice_id": "A",
      "choice_text": "PostgreSQL",
      "selected": true,
      "evaluation_score": 0.9,
      "rejection_reason": null
    },
    {
      "choice_id": "B",
      "choice_text": "SQLite",
      "selected": false,
      "evaluation_score": 0.6,
      "rejection_reason": "スケーラビリティ限界: 1ユーザーならOKだが、将来的に複数ユーザー対応が必要"
    },
    {
      "choice_id": "C",
      "choice_text": "MongoDB",
      "selected": false,
      "evaluation_score": 0.4,
      "rejection_reason": "リレーショナルデータに不向き: Intentの相互参照が複雑になる"
    }
  ],
  "selected_choice_id": "A",
  "decision_rationale": "スケーラビリティと拡張性を考慮",
  "tags": ["technology_stack", "database", "architecture"]
}
```

**効果**: 3ヶ月後に「なぜSQLiteじゃないの？」と聞かれても、即座に回答可能

---

### 2.2 歴史的クエリ: タグベース検索

**シナリオ:**
「過去の技術選定決定を全部見たい」

**実装:**
```python
# APIリクエスト
GET /choice-points/search?tags=technology_stack,database&limit=10

# レスポンス
{
  "results": [
    {
      "id": "uuid-001",
      "question": "データベース選定",
      "selected_choice_text": "PostgreSQL",
      "decided_at": "2025-08-15T10:30:00Z",
      "tags": ["technology_stack", "database"]
    },
    {
      "id": "uuid-045",
      "question": "ORMライブラリ選定",
      "selected_choice_text": "SQLAlchemy",
      "decided_at": "2025-09-01T14:20:00Z",
      "tags": ["technology_stack", "database", "orm"]
    }
  ]
}
```

---

### 2.3 歴史的クエリ: 時間範囲検索

**シナリオ:**
「3ヶ月前の選択を振り返りたい」

**実装:**
```python
# APIリクエスト
GET /choice-points/search?from=2025-08-01&to=2025-08-31

# レスポンス: 8月の全決定リスト
```

---

### 2.4 Context Assemblerとの統合

**シナリオ:**
ユーザー「そういえば、データベース何使ってるんだっけ？」

**Before（Sprint 8）:**
```
AI: 「確認します...（Choice Pointを検索）→ PostgreSQLです」
```

**After（Sprint 10）:**
```
Context Assembler自動注入:
[Past Choice Memory]
- データベース選定: PostgreSQL（2025-08-15）
  理由: スケーラビリティと拡張性
  却下: SQLite（限界あり）、MongoDB（リレーショナル不向き）

AI: 「PostgreSQLを使っています（2025年8月選定）。
     SQLiteは将来の複数ユーザー対応を考慮して却下しました。」
```

**効果**: 過去の選択が自動的に対話コンテキストに含まれる

---

## 3. アーキテクチャ

### 3.1 全体構成

```
┌──────────────────────────────────────────────────────────┐
│      Choice Preservation System (Complete Version)      │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Enhanced Choice Point Model                       │ │
│  │  - Rejection reasons for all choices              │ │
│  │  - Evaluation scores                               │ │
│  │  - Tags for categorization                         │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Historical Query Engine                           │ │
│  │  - Tag-based search                                │ │
│  │  - Time-range filtering                            │ │
│  │  - Full-text search                                │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Context Assembler Integration                     │ │
│  │  - Auto-inject past choices                        │ │
│  │  - Relevance scoring                               │ │
│  │  - Deduplication                                   │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
          ↓                    ↑
    [PostgreSQL]          [Context Assembler]
    - choice_points
    - choice_point_tags (new)
```

### 3.2 データフロー

```
[Choice Point Created]
    ↓
1. Question + Choices + Tags
    ↓
2. User evaluates each choice
   ├─ Selected: reason recorded
   └─ Rejected: rejection_reason recorded
    ↓
3. Decision finalized
   ├─ All reasons saved to DB
   └─ Tags stored
    ↓
4. Historical Query (on-demand)
   ├─ Tag search
   ├─ Time-range filter
   └─ Full-text search
    ↓
5. Context Assembler (automatic)
   ├─ Query relevant past choices
   ├─ Inject into conversation context
   └─ AI references past decisions
```

---

## 4. データモデル

### 4.1 Choice モデル拡張

**変更前（Sprint 8）:**
```python
# bridge/memory/models.py:245-250
class Choice(BaseModel):
    choice_id: str
    choice_text: str
```

**変更後（Sprint 10）:**
```python
class Choice(BaseModel):
    choice_id: str
    choice_text: str

    # 🆕 追加フィールド
    selected: bool = False  # この選択肢が選ばれたか
    evaluation_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # 評価スコア（0-1）
    rejection_reason: Optional[str] = None  # 却下理由（選ばれなかった場合）

    # メタデータ
    evaluated_at: Optional[datetime] = None
```

### 4.2 ChoicePoint モデル拡張

**変更前（Sprint 8）:**
```python
# bridge/memory/models.py:229-243
class ChoicePoint(BaseModel):
    question: str
    choices: List[Choice]
    selected_choice_id: Optional[str]
    decision_rationale: Optional[str]
    created_at: datetime
    decided_at: Optional[datetime]
```

**変更後（Sprint 10）:**
```python
class ChoicePoint(BaseModel):
    id: Optional[UUID] = None
    user_id: str
    question: str
    choices: List[Choice]  # ← 拡張されたChoiceモデル使用
    selected_choice_id: Optional[str]
    decision_rationale: Optional[str]

    # 🆕 追加フィールド
    tags: List[str] = []  # カテゴリタグ（例: ["technology_stack", "database"]）
    context_type: str = "general"  # コンテキストタイプ（"architecture", "feature", "bug_fix" など）

    created_at: datetime
    decided_at: Optional[datetime]

    # メタデータ
    session_id: Optional[str] = None
    intent_id: Optional[str] = None  # 関連Intent（あれば）
```

### 4.3 PostgreSQL スキーマ拡張

**マイグレーション:**
```sql
-- ========================================
-- Sprint 10: Choice Preservation Completion
-- ========================================

-- 1. choice_points テーブル拡張
ALTER TABLE choice_points
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS context_type VARCHAR(50) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS session_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS intent_id UUID;

-- インデックス追加
CREATE INDEX IF NOT EXISTS idx_choice_points_tags ON choice_points USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_choice_points_context_type ON choice_points(context_type);
CREATE INDEX IF NOT EXISTS idx_choice_points_decided_at ON choice_points(decided_at);
CREATE INDEX IF NOT EXISTS idx_choice_points_intent_id ON choice_points(intent_id);

-- 2. フルテキスト検索用インデックス
CREATE INDEX IF NOT EXISTS idx_choice_points_question_fulltext
    ON choice_points USING GIN(to_tsvector('english', question));

-- 3. choices配列のJSONB検索用
-- choicesカラムが既にJSONBの場合、rejection_reasonでの検索を高速化
CREATE INDEX IF NOT EXISTS idx_choice_points_choices_gin
    ON choice_points USING GIN(choices);
```

---

## 5. コンポーネント設計

### 5.1 Historical Query Engine

**ファイル:** `bridge/memory/choice_query_engine.py`（新規）

```python
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .models import ChoicePoint

logger = logging.getLogger(__name__)

class ChoiceQueryEngine:
    """Choice Point歴史的クエリエンジン"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def search_by_tags(
        self,
        user_id: str,
        tags: List[str],
        match_all: bool = False,
        limit: int = 10
    ) -> List[ChoicePoint]:
        """
        タグベース検索

        Args:
            user_id: ユーザーID
            tags: 検索タグリスト
            match_all: True=全タグ一致, False=いずれか一致
            limit: 取得件数

        Returns:
            List[ChoicePoint]: 該当するChoice Pointリスト
        """
        async with self.pool.acquire() as conn:
            if match_all:
                # 全タグ一致（AND検索）
                query = """
                    SELECT * FROM choice_points
                    WHERE user_id = $1
                      AND tags @> $2::text[]
                      AND selected_choice_id IS NOT NULL
                    ORDER BY decided_at DESC
                    LIMIT $3
                """
            else:
                # いずれか一致（OR検索）
                query = """
                    SELECT * FROM choice_points
                    WHERE user_id = $1
                      AND tags && $2::text[]
                      AND selected_choice_id IS NOT NULL
                    ORDER BY decided_at DESC
                    LIMIT $3
                """

            rows = await conn.fetch(query, user_id, tags, limit)
            return [ChoicePoint(**dict(row)) for row in rows]

    async def search_by_time_range(
        self,
        user_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[ChoicePoint]:
        """
        時間範囲検索

        Args:
            user_id: ユーザーID
            from_date: 開始日時（Noneなら制限なし）
            to_date: 終了日時（Noneなら制限なし）
            limit: 取得件数

        Returns:
            List[ChoicePoint]: 該当するChoice Pointリスト
        """
        async with self.pool.acquire() as conn:
            conditions = ["user_id = $1", "selected_choice_id IS NOT NULL"]
            params = [user_id]
            param_idx = 2

            if from_date:
                conditions.append(f"decided_at >= ${param_idx}")
                params.append(from_date)
                param_idx += 1

            if to_date:
                conditions.append(f"decided_at <= ${param_idx}")
                params.append(to_date)
                param_idx += 1

            params.append(limit)

            query = f"""
                SELECT * FROM choice_points
                WHERE {' AND '.join(conditions)}
                ORDER BY decided_at DESC
                LIMIT ${param_idx}
            """

            rows = await conn.fetch(query, *params)
            return [ChoicePoint(**dict(row)) for row in rows]

    async def search_fulltext(
        self,
        user_id: str,
        search_text: str,
        limit: int = 10
    ) -> List[ChoicePoint]:
        """
        フルテキスト検索

        Args:
            user_id: ユーザーID
            search_text: 検索テキスト
            limit: 取得件数

        Returns:
            List[ChoicePoint]: 該当するChoice Pointリスト
        """
        async with self.pool.acquire() as conn:
            query = """
                SELECT *,
                       ts_rank(to_tsvector('english', question), plainto_tsquery('english', $2)) AS rank
                FROM choice_points
                WHERE user_id = $1
                  AND selected_choice_id IS NOT NULL
                  AND to_tsvector('english', question) @@ plainto_tsquery('english', $2)
                ORDER BY rank DESC, decided_at DESC
                LIMIT $3
            """

            rows = await conn.fetch(query, user_id, search_text, limit)
            return [ChoicePoint(**{k: v for k, v in dict(row).items() if k != 'rank'}) for row in rows]

    async def get_relevant_choices_for_context(
        self,
        user_id: str,
        current_question: str,
        tags: Optional[List[str]] = None,
        limit: int = 3
    ) -> List[ChoicePoint]:
        """
        Context Assembler用: 現在の質問に関連する過去の選択を取得

        Args:
            user_id: ユーザーID
            current_question: 現在の質問
            tags: タグフィルタ（あれば）
            limit: 取得件数

        Returns:
            List[ChoicePoint]: 関連する過去の選択
        """
        # フルテキスト検索で関連性スコア計算
        relevant_choices = await self.search_fulltext(
            user_id=user_id,
            search_text=current_question,
            limit=limit * 2  # 多めに取得してフィルタ
        )

        # タグフィルタ（あれば）
        if tags:
            relevant_choices = [
                cp for cp in relevant_choices
                if any(tag in cp.tags for tag in tags)
            ]

        return relevant_choices[:limit]
```

### 5.2 MemoryService 拡張

**ファイル:** `bridge/memory/service.py`（拡張）

```python
# 既存のMemoryServiceクラスに追加

from .choice_query_engine import ChoiceQueryEngine

class MemoryService:
    def __init__(self, pool: asyncpg.Pool, ...):
        self.pool = pool
        # 🆕 追加
        self.choice_query_engine = ChoiceQueryEngine(pool)
        ...

    # 既存のcreate_choice_point()メソッドを拡張
    async def create_choice_point(
        self,
        user_id: str,
        question: str,
        choices: List[Dict[str, Any]],
        tags: List[str] = [],  # 🆕
        context_type: str = "general",  # 🆕
        session_id: Optional[str] = None,  # 🆕
        intent_id: Optional[str] = None  # 🆕
    ) -> ChoicePoint:
        """
        Choice Point作成（拡張版）

        Args:
            user_id: ユーザーID
            question: 質問
            choices: 選択肢リスト
            tags: カテゴリタグ
            context_type: コンテキストタイプ
            session_id: セッションID
            intent_id: 関連IntentID

        Returns:
            ChoicePoint: 作成されたChoice Point
        """
        async with self.pool.acquire() as conn:
            choice_point_id = await conn.fetchval("""
                INSERT INTO choice_points
                    (user_id, question, choices, tags, context_type, session_id, intent_id, created_at)
                VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, NOW())
                RETURNING id
            """, user_id, question, json.dumps(choices), tags, context_type, session_id, intent_id)

            return await self.get_choice_point(str(choice_point_id))

    # 既存のdecide_choice()メソッドを拡張
    async def decide_choice(
        self,
        choice_point_id: str,
        selected_choice_id: str,
        decision_rationale: str,
        rejection_reasons: Dict[str, str] = {}  # 🆕 {"choice_id": "reason"}
    ) -> ChoicePoint:
        """
        Choice決定（却下理由付き）

        Args:
            choice_point_id: Choice Point ID
            selected_choice_id: 選択されたchoice_id
            decision_rationale: 選択理由
            rejection_reasons: 却下理由辞書 {"choice_id": "却下理由"}

        Returns:
            ChoicePoint: 更新されたChoice Point
        """
        async with self.pool.acquire() as conn:
            # Choice Pointを取得
            cp = await self.get_choice_point(choice_point_id)

            # 各選択肢に却下理由を追加
            updated_choices = []
            for choice in cp.choices:
                choice_dict = choice.dict()
                choice_dict['selected'] = (choice.choice_id == selected_choice_id)

                if choice.choice_id == selected_choice_id:
                    choice_dict['rejection_reason'] = None
                else:
                    choice_dict['rejection_reason'] = rejection_reasons.get(choice.choice_id, "")

                choice_dict['evaluated_at'] = datetime.utcnow()
                updated_choices.append(choice_dict)

            # DB更新
            await conn.execute("""
                UPDATE choice_points
                SET selected_choice_id = $1,
                    decision_rationale = $2,
                    choices = $3::jsonb,
                    decided_at = NOW()
                WHERE id = $4
            """, selected_choice_id, decision_rationale, json.dumps(updated_choices), choice_point_id)

            return await self.get_choice_point(choice_point_id)

    # 🆕 新規メソッド: 検索API
    async def search_choice_points(
        self,
        user_id: str,
        tags: Optional[List[str]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 10
    ) -> List[ChoicePoint]:
        """
        Choice Point検索（統合メソッド）

        Args:
            user_id: ユーザーID
            tags: タグフィルタ
            from_date: 開始日時
            to_date: 終了日時
            search_text: 検索テキスト
            limit: 取得件数

        Returns:
            List[ChoicePoint]: 検索結果
        """
        if search_text:
            return await self.choice_query_engine.search_fulltext(user_id, search_text, limit)
        elif tags:
            return await self.choice_query_engine.search_by_tags(user_id, tags, match_all=False, limit=limit)
        elif from_date or to_date:
            return await self.choice_query_engine.search_by_time_range(user_id, from_date, to_date, limit)
        else:
            # デフォルト: 最新のChoice Pointを返す
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM choice_points
                    WHERE user_id = $1 AND selected_choice_id IS NOT NULL
                    ORDER BY decided_at DESC
                    LIMIT $2
                """, user_id, limit)
                return [ChoicePoint(**dict(row)) for row in rows]
```

### 5.3 Context Assembler 統合

**ファイル:** `retrieval/context_assembler.py`（拡張）

```python
# 既存のContextAssemblerクラスに追加

from bridge.memory.choice_query_engine import ChoiceQueryEngine

class ContextAssembler:
    def __init__(self, ..., choice_query_engine: ChoiceQueryEngine):
        ...
        self.choice_query_engine = choice_query_engine

    async def assemble_context(
        self,
        user_id: str,
        query: str,
        session_id: str,
        include_past_choices: bool = True  # 🆕
    ) -> AssembledContext:
        """
        コンテキスト組み立て（過去選択統合版）

        Args:
            user_id: ユーザーID
            query: クエリ
            session_id: セッションID
            include_past_choices: 過去の選択を含むか

        Returns:
            AssembledContext: 組み立てられたコンテキスト
        """
        # 既存の3層メモリ取得
        semantic_memories = await self.retrieve_semantic_memories(user_id, query)
        agent_context = await self.retrieve_agent_context(user_id)
        session_summary = await self.retrieve_session_summary(session_id)

        # 🆕 過去の選択を取得
        past_choices = []
        if include_past_choices:
            past_choices = await self.choice_query_engine.get_relevant_choices_for_context(
                user_id=user_id,
                current_question=query,
                limit=3
            )

        # コンテキスト構築
        context_parts = []

        # Semantic Memories
        if semantic_memories:
            context_parts.append("[Semantic Memories]\n" + "\n".join([m['content'] for m in semantic_memories]))

        # Agent Context
        if agent_context:
            context_parts.append(f"[Agent Context]\n{agent_context.to_prompt()}")

        # Session Summary
        if session_summary:
            context_parts.append(f"[Session Summary]\n{session_summary}")

        # 🆕 Past Choices
        if past_choices:
            choice_texts = []
            for cp in past_choices:
                selected = next((c for c in cp.choices if c.choice_id == cp.selected_choice_id), None)
                rejected = [c for c in cp.choices if c.choice_id != cp.selected_choice_id and c.rejection_reason]

                choice_text = f"- {cp.question}: {selected.choice_text} (decided {cp.decided_at.strftime('%Y-%m-%d')})\n"
                choice_text += f"  Reason: {cp.decision_rationale}\n"

                if rejected:
                    choice_text += "  Rejected alternatives:\n"
                    for r in rejected:
                        choice_text += f"    - {r.choice_text}: {r.rejection_reason}\n"

                choice_texts.append(choice_text)

            context_parts.append("[Past Decision History]\n" + "\n".join(choice_texts))

        return AssembledContext(
            raw_context="\n\n".join(context_parts),
            semantic_memories=semantic_memories,
            agent_context=agent_context,
            session_summary=session_summary,
            past_choices=past_choices  # 🆕
        )
```

### 5.4 API Router 拡張

**ファイル:** `bridge/memory/api_router.py`（拡張）

```python
# 既存のAPIRouterに追加

@router.get("/choice-points/search")
async def search_choice_points(
    user_id: str = Query(...),
    tags: Optional[str] = Query(None),  # カンマ区切り "tag1,tag2"
    from_date: Optional[str] = Query(None),  # ISO8601形式
    to_date: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Choice Point検索エンドポイント

    Query Parameters:
        - user_id: ユーザーID（必須）
        - tags: タグフィルタ（カンマ区切り、例: "database,technology"）
        - from_date: 開始日時（ISO8601、例: "2025-08-01T00:00:00Z"）
        - to_date: 終了日時（ISO8601）
        - search_text: フルテキスト検索
        - limit: 取得件数（デフォルト10、最大100）
    """
    tag_list = tags.split(",") if tags else None
    from_dt = datetime.fromisoformat(from_date) if from_date else None
    to_dt = datetime.fromisoformat(to_date) if to_date else None

    results = await memory_service.search_choice_points(
        user_id=user_id,
        tags=tag_list,
        from_date=from_dt,
        to_date=to_dt,
        search_text=search_text,
        limit=limit
    )

    return {"results": [cp.dict() for cp in results], "count": len(results)}

@router.put("/choice-points/{choice_point_id}/decide")
async def decide_choice_with_rejection_reasons(
    choice_point_id: str,
    request: DecideChoiceRequest,  # 既存
    rejection_reasons: Dict[str, str] = Body({}),  # 🆕 {"choice_id": "reason"}
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Choice決定（却下理由付き）

    Request Body:
    {
      "selected_choice_id": "A",
      "decision_rationale": "スケーラビリティを考慮",
      "rejection_reasons": {
        "B": "スケーラビリティ限界",
        "C": "リレーショナルデータに不向き"
      }
    }
    """
    choice_point = await memory_service.decide_choice(
        choice_point_id=choice_point_id,
        selected_choice_id=request.selected_choice_id,
        decision_rationale=request.decision_rationale,
        rejection_reasons=rejection_reasons
    )

    return {"choice_point": choice_point.dict()}
```

---

## 6. パフォーマンス

### 6.1 レイテンシ目標

| 操作 | 目標 |
|------|------|
| Choice Point作成 | < 100ms |
| Choice決定（却下理由付き） | < 200ms |
| タグ検索（100件） | < 500ms |
| フルテキスト検索 | < 1秒 |
| Context Assembler統合 | < 1.5秒 |

---

## 7. 運用

### 7.1 タグ命名規則

**推奨タグカテゴリ:**
- **技術選定**: `technology_stack`, `database`, `framework`, `library`, `language`
- **アーキテクチャ**: `architecture`, `design_pattern`, `api_design`
- **機能**: `feature`, `ui_ux`, `performance`, `security`
- **プロジェクト管理**: `priority`, `scope`, `timeline`

**例:**
```json
{
  "question": "認証方式選定",
  "tags": ["security", "authentication", "technology_stack"]
}
```

---

## 8. 制約と前提

### 8.1 制約
- 却下理由は最大1000文字
- タグは最大10個/Choice Point
- 後方互換性: 既存のChoice Point（却下理由なし）も動作

### 8.2 前提
- Sprint 8 Choice Point基本実装済み
- PostgreSQL 13+（配列・JSONB・フルテキスト検索サポート）

---

## 9. 今後の拡張

### 9.1 Sprint 11以降候補
- AI判定による自動評価スコア計算
- 選択肢のバージョニング（決定後の変更追跡）
- グラフ可視化機能（決定木）

---

## 10. 参考資料

- [Sprint 8: User Profile仕様書](./sprint8_user_profile_spec.md)
- [Sprint 5: Context Assembler仕様書](./sprint5_context_assembler_spec.md)
- [Kiro vs Resonant Engine比較分析](../../kiro_resonant_comparison_handoff.md)

---

**作成日**: 2025-11-20
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総行数**: 850
