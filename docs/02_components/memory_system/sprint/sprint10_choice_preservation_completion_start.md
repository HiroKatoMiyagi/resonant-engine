# Sprint 10: Choice Preservation System（完成版）作業開始指示書

## 概要

**Sprint**: 10
**タイトル**: Choice Preservation System（完成版）
**期間**: 5日間（1-2週間）
**目標**: Choice Point機能の完成（却下理由・歴史的クエリ・Context統合）

---

## Day 1: データモデル拡張 & PostgreSQL マイグレーション

### 目標
- Choiceモデル拡張（`rejection_reason`, `evaluation_score`, `selected`）
- ChoicePointモデル拡張（`tags`, `context_type`）
- PostgreSQLマイグレーション実装

### ステップ

#### 1.1 Pydanticモデル拡張

**ファイル**: `bridge/memory/models.py`（変更）

**変更箇所 1: Choiceモデル**
```python
# 既存の Choice クラス（Line 245-250付近）を以下に置き換え

class Choice(BaseModel):
    """選択肢"""
    choice_id: str
    choice_text: str

    # 🆕 Sprint 10 追加フィールド
    selected: bool = False  # この選択肢が選ばれたか
    evaluation_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # 評価スコア（0-1）
    rejection_reason: Optional[str] = Field(None, max_length=1000)  # 却下理由

    # メタデータ
    evaluated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "choice_id": "A",
                "choice_text": "PostgreSQL",
                "selected": True,
                "evaluation_score": 0.9,
                "rejection_reason": None,
                "evaluated_at": "2025-08-15T10:30:00Z"
            }
        }
```

**変更箇所 2: ChoicePointモデル**
```python
# 既存の ChoicePoint クラス（Line 229-243付近）を以下に置き換え

class ChoicePoint(BaseModel):
    """意思決定ポイント（完成版）"""
    id: Optional[UUID] = None
    user_id: str
    question: str
    choices: List[Choice]  # ← 拡張されたChoiceモデル
    selected_choice_id: Optional[str] = None
    decision_rationale: Optional[str] = None

    # 🆕 Sprint 10 追加フィールド
    tags: List[str] = Field(default_factory=list, max_items=10)  # カテゴリタグ
    context_type: str = "general"  # "architecture", "feature", "bug_fix", "general"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None

    # メタデータ
    session_id: Optional[str] = None
    intent_id: Optional[UUID] = None  # 関連Intent

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "hiroki",
                "question": "データベース選定",
                "choices": [
                    {
                        "choice_id": "A",
                        "choice_text": "PostgreSQL",
                        "selected": True,
                        "evaluation_score": 0.9,
                        "rejection_reason": None
                    },
                    {
                        "choice_id": "B",
                        "choice_text": "SQLite",
                        "selected": False,
                        "evaluation_score": 0.6,
                        "rejection_reason": "スケーラビリティ限界"
                    }
                ],
                "selected_choice_id": "A",
                "decision_rationale": "スケーラビリティと拡張性を考慮",
                "tags": ["technology_stack", "database"],
                "context_type": "architecture"
            }
        }
```

#### 1.2 PostgreSQLマイグレーション作成

**ファイル**: `docker/postgres/007_choice_preservation_completion.sql`（新規）

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

-- 3. choices配列のJSONB検索用インデックス
CREATE INDEX IF NOT EXISTS idx_choice_points_choices_gin
    ON choice_points USING GIN(choices);

-- 4. コメント追加
COMMENT ON COLUMN choice_points.tags IS 'Categorization tags (e.g., ["technology_stack", "database"])';
COMMENT ON COLUMN choice_points.context_type IS 'Context type: "architecture", "feature", "bug_fix", "general"';
COMMENT ON COLUMN choice_points.session_id IS 'Related session ID';
COMMENT ON COLUMN choice_points.intent_id IS 'Related Intent ID';
```

**実行**:
```bash
docker exec -i resonant-postgres psql -U resonant_user -d resonant_db < docker/postgres/007_choice_preservation_completion.sql
```

### Day 1 成功基準
- [ ] Choiceモデルに3つのフィールド追加完了
- [ ] ChoicePointモデルに4つのフィールド追加完了
- [ ] PostgreSQLマイグレーション実行完了
- [ ] 単体テスト2件以上作成（モデルバリデーション）

### Git Commit
```bash
git add bridge/memory/models.py docker/postgres/007_choice_preservation_completion.sql
git commit -m "Add Sprint 10 Day 1: Choice & ChoicePoint model extensions with PostgreSQL migration"
```

---

## Day 2: Historical Query Engine実装

### 目標
- ChoiceQueryEngineクラス実装
- タグ検索・時間範囲検索・フルテキスト検索実装

### ステップ

#### 2.1 ChoiceQueryEngine実装

**ファイル**: `bridge/memory/choice_query_engine.py`（新規）

```python
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

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

            result = []
            for row in rows:
                row_dict = dict(row)
                # choices JSONBをパース
                if isinstance(row_dict['choices'], str):
                    row_dict['choices'] = json.loads(row_dict['choices'])
                result.append(ChoicePoint(**row_dict))

            return result

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
            params: List[Any] = [user_id]
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

            result = []
            for row in rows:
                row_dict = dict(row)
                if isinstance(row_dict['choices'], str):
                    row_dict['choices'] = json.loads(row_dict['choices'])
                result.append(ChoicePoint(**row_dict))

            return result

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

            result = []
            for row in rows:
                row_dict = {k: v for k, v in dict(row).items() if k != 'rank'}
                if isinstance(row_dict['choices'], str):
                    row_dict['choices'] = json.loads(row_dict['choices'])
                result.append(ChoicePoint(**row_dict))

            return result

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

### Day 2 成功基準
- [ ] ChoiceQueryEngine実装完了（4メソッド）
- [ ] 単体テスト4件以上作成（各検索メソッド）

### Git Commit
```bash
git add bridge/memory/choice_query_engine.py
git commit -m "Add Sprint 10 Day 2: Historical Query Engine for Choice Points"
```

---

## Day 3: MemoryService拡張 & API Router拡張

### 目標
- MemoryServiceに却下理由対応版`decide_choice()`実装
- 検索APIエンドポイント実装

### ステップ

#### 3.1 MemoryService拡張

**ファイル**: `bridge/memory/service.py`（変更）

**追加箇所 1: __init__メソッド**
```python
from .choice_query_engine import ChoiceQueryEngine

class MemoryService:
    def __init__(self, pool: asyncpg.Pool, ...):
        self.pool = pool
        # 🆕 追加
        self.choice_query_engine = ChoiceQueryEngine(pool)
        ...
```

**追加箇所 2: create_choice_point()拡張**
```python
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
```

**追加箇所 3: decide_choice()拡張**
```python
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

            choice_dict['evaluated_at'] = datetime.utcnow().isoformat()
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
```

**追加箇所 4: 検索メソッド**
```python
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

            result = []
            for row in rows:
                row_dict = dict(row)
                if isinstance(row_dict['choices'], str):
                    row_dict['choices'] = json.loads(row_dict['choices'])
                result.append(ChoicePoint(**row_dict))

            return result
```

#### 3.2 API Router拡張

**ファイル**: `bridge/memory/api_router.py`（変更）

**追加エンドポイント 1: 検索API**
```python
from fastapi import Query

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
    from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00')) if from_date else None
    to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00')) if to_date else None

    results = await memory_service.search_choice_points(
        user_id=user_id,
        tags=tag_list,
        from_date=from_dt,
        to_date=to_dt,
        search_text=search_text,
        limit=limit
    )

    return {"results": [cp.dict() for cp in results], "count": len(results)}
```

**既存エンドポイント拡張: decide API**
```python
# 既存の PUT /choice-points/{choice_point_id}/decide エンドポイントを以下に置き換え

class DecideChoiceRequest(BaseModel):
    selected_choice_id: str
    decision_rationale: str
    rejection_reasons: Dict[str, str] = {}  # 🆕

@router.put("/choice-points/{choice_point_id}/decide")
async def decide_choice_with_rejection_reasons(
    choice_point_id: str,
    request: DecideChoiceRequest,
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
        rejection_reasons=request.rejection_reasons
    )

    return {"choice_point": choice_point.dict()}
```

### Day 3 成功基準
- [ ] MemoryService拡張完了（4メソッド）
- [ ] API Router拡張完了（2エンドポイント）
- [ ] 統合テスト3件以上作成

### Git Commit
```bash
git add bridge/memory/service.py bridge/memory/api_router.py
git commit -m "Add Sprint 10 Day 3: MemoryService and API Router extensions for choice preservation"
```

---

## Day 4: Context Assembler統合

### 目標
- Context Assemblerに過去選択注入機能実装

### ステップ

#### 4.1 Context Assembler拡張

**ファイル**: `retrieval/context_assembler.py`（変更）

**注意**: 既存のContextAssemblerクラスに追加

```python
from bridge.memory.choice_query_engine import ChoiceQueryEngine

class ContextAssembler:
    def __init__(self, ..., choice_query_engine: Optional[ChoiceQueryEngine] = None):
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
        if include_past_choices and self.choice_query_engine:
            try:
                past_choices = await self.choice_query_engine.get_relevant_choices_for_context(
                    user_id=user_id,
                    current_question=query,
                    limit=3
                )
            except Exception as e:
                logger.warning(f"Failed to retrieve past choices: {e}")

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

                if selected:
                    choice_text = f"- {cp.question}: {selected.choice_text} (decided {cp.decided_at.strftime('%Y-%m-%d')})\n"
                    choice_text += f"  Reason: {cp.decision_rationale}\n"

                    if rejected:
                        choice_text += "  Rejected alternatives:\n"
                        for r in rejected:
                            choice_text += f"    - {r.choice_text}: {r.rejection_reason}\n"

                    choice_texts.append(choice_text)

            if choice_texts:
                context_parts.append("[Past Decision History]\n" + "\n".join(choice_texts))

        return AssembledContext(
            raw_context="\n\n".join(context_parts),
            semantic_memories=semantic_memories,
            agent_context=agent_context,
            session_summary=session_summary,
            past_choices=past_choices  # 🆕
        )
```

### Day 4 成功基準
- [ ] Context Assemblerに過去選択注入機能追加
- [ ] E2Eテスト2件以上作成

### Git Commit
```bash
git add retrieval/context_assembler.py
git commit -m "Add Sprint 10 Day 4: Context Assembler integration with past choices"
```

---

## Day 5: テスト & ドキュメント

### 目標
- 単体テスト・統合テスト作成
- E2Eテスト
- APIドキュメント

### ステップ

#### 5.1 単体テスト

**ファイル**: `tests/memory/test_choice_query_engine.py`（新規）

```python
import pytest
from datetime import datetime, timedelta
from bridge.memory.choice_query_engine import ChoiceQueryEngine

@pytest.mark.asyncio
async def test_search_by_tags(db_pool):
    """タグ検索テスト"""
    engine = ChoiceQueryEngine(db_pool)
    user_id = "test_user"

    # テストデータ作成
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO choice_points
                (user_id, question, choices, selected_choice_id, tags, decided_at)
            VALUES ($1, $2, $3::jsonb, $4, $5, NOW())
        """, user_id, "DB選定", '[{"choice_id": "A", "choice_text": "PostgreSQL", "selected": true}]',
            "A", ["database", "technology"])

    # 検索実行
    results = await engine.search_by_tags(user_id, ["database"], limit=10)

    # 検証
    assert len(results) >= 1
    assert "database" in results[0].tags

@pytest.mark.asyncio
async def test_search_by_time_range(db_pool):
    """時間範囲検索テスト"""
    engine = ChoiceQueryEngine(db_pool)
    user_id = "test_user"

    # 検索実行
    from_date = datetime.utcnow() - timedelta(days=7)
    results = await engine.search_by_time_range(user_id, from_date=from_date, limit=10)

    # 検証
    for cp in results:
        assert cp.decided_at >= from_date
```

#### 5.2 E2Eテスト

**ファイル**: `tests/integration/test_choice_preservation_e2e.py`（新規）

```python
@pytest.mark.asyncio
async def test_full_choice_preservation_flow(db_pool, memory_service):
    """完全フローテスト: 作成→決定→検索→Context統合"""
    user_id = "test_user"

    # 1. Choice Point作成
    cp = await memory_service.create_choice_point(
        user_id=user_id,
        question="データベース選定",
        choices=[
            {"choice_id": "A", "choice_text": "PostgreSQL"},
            {"choice_id": "B", "choice_text": "SQLite"},
            {"choice_id": "C", "choice_text": "MongoDB"}
        ],
        tags=["database", "technology_stack"]
    )

    assert cp.id is not None

    # 2. 決定（却下理由付き）
    cp = await memory_service.decide_choice(
        choice_point_id=str(cp.id),
        selected_choice_id="A",
        decision_rationale="スケーラビリティを考慮",
        rejection_reasons={
            "B": "スケーラビリティ限界",
            "C": "リレーショナルデータに不向き"
        }
    )

    # 検証
    selected = next(c for c in cp.choices if c.choice_id == "A")
    assert selected.selected is True
    assert selected.rejection_reason is None

    rejected_b = next(c for c in cp.choices if c.choice_id == "B")
    assert rejected_b.selected is False
    assert rejected_b.rejection_reason == "スケーラビリティ限界"

    # 3. 検索
    results = await memory_service.search_choice_points(
        user_id=user_id,
        tags=["database"]
    )

    assert len(results) >= 1
    assert results[0].question == "データベース選定"
```

### Day 5 成功基準
- [ ] 単体テスト10件以上作成・全件PASS
- [ ] E2Eテスト成功
- [ ] APIドキュメント完成

### Git Commit
```bash
git add tests/
git commit -m "Add Sprint 10 Day 5: Tests and documentation for choice preservation completion"
```

---

## 最終確認

### チェックリスト

**Tier 1: 必須要件**
- [ ] `Choice`モデルに`rejection_reason`フィールド追加
- [ ] 歴史的クエリ機能実装（タグ検索・時間範囲・フルテキスト）
- [ ] Context Assemblerとの統合（過去選択の自動注入）
- [ ] 10件以上の単体/統合テストが作成され、CI で緑
- [ ] 既存Choice Point機能との後方互換性

**Tier 2: 品質要件**
- [ ] クエリレスポンス < 500ms（100件検索）
- [ ] 却下理由が全選択肢で保存可能
- [ ] タグベース検索が正確に動作
- [ ] Observability: `choice_decision_count`, `choice_query_count`

### 最終コミット

```bash
git add .
git commit -m "Complete Sprint 10: Choice Preservation System (Full Version)

- Extended Choice model with rejection_reason, evaluation_score, selected fields
- Extended ChoicePoint model with tags, context_type, session_id, intent_id
- Implemented Historical Query Engine (tag search, time-range, fulltext)
- Integrated with Context Assembler for automatic past choice injection
- Added API endpoints for search and enhanced decision recording
- 10+ unit and integration tests
- Full backward compatibility with Sprint 8 implementation"

git push -u origin claude/kiro-resonant-comparison-docs-0198CAL7HAgugbuZaP65rpBD
```

---

**作成日**: 2025-11-20
**作成者**: Kana (Claude Sonnet 4.5)
**総行数**: 950
