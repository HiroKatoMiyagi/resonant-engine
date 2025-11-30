# Phase 2: Choice Preservation API実装完了 作業指示書

## 概要

**Phase**: 2
**タイトル**: Choice Preservation API完全実装
**前提**: Phase 1完了（10/14エンドポイント動作確認済み）
**期間**: 1-2時間
**目標**: Choice Preservation API 4エンドポイントを有効化し、14/14エンドポイント完全動作

---

## 📋 現状

### Phase 1完了状況
- ✅ Contradiction Detection API (3エンドポイント)
- ✅ Re-evaluation API (1エンドポイント)
- ✅ Memory Lifecycle API (3エンドポイント)
- ✅ Dashboard Analytics API (3エンドポイント)
- ⚠️ Choice Preservation API (4エンドポイント) - **無効化中**

### 無効化理由
`backend/app/main.py` Line 26でコメントアウト:
```python
# app.include_router(choice_points.router)  # 一時的に無効化
```

**原因**: `MemoryStoreService`のインターフェース不一致

---

## Step 1: MemoryStoreServiceの実装状況確認（15分）

### 1.1 既存実装の確認

```bash
# MemoryStoreServiceの実際のクラス定義を確認
cat /Users/zero/Projects/resonant-engine/memory_store/service.py
```

**確認ポイント**:
1. `get_pending_choice_points(user_id)` メソッドが存在するか
2. `create_choice_point(...)` メソッドが存在するか
3. `decide_choice(...)` メソッドが存在するか
4. `search_choice_points(...)` メソッドが存在するか

### 1.2 choice_points.pyで期待されるインターフェース

**ファイル**: `backend/app/routers/choice_points.py`

```python
# 期待されるメソッド:
memory_service.get_pending_choice_points(user_id)
memory_service.create_choice_point(user_id, question, choices, tags, context_type)
memory_service.decide_choice(choice_point_id, selected_choice_id, decision_rationale, rejection_reasons)
memory_service.search_choice_points(user_id, tags, from_date, to_date, search_text, limit)
```

---

## Step 2: 対応方針の決定（10分）

### 方針A: MemoryStoreServiceに欠落メソッドを追加

**適用条件**: メソッドが存在しない場合

**実装場所**: `memory_store/service.py`

**例**:
```python
async def get_pending_choice_points(self, user_id: str) -> List[ChoicePoint]:
    """未決定の選択肢を取得"""
    async with self.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM choice_points
            WHERE user_id = $1
              AND selected_choice_id IS NULL
            ORDER BY created_at DESC
        """, user_id)
        return [self._row_to_choice_point(row) for row in rows]
```

### 方針B: Adapterパターンでラップ

**適用条件**: メソッドは存在するがシグネチャが大きく異なる場合

**実装場所**: `backend/app/adapters/memory_store_adapter.py`（新規作成）

**例**:
```python
class MemoryStoreAdapter:
    def __init__(self, service: MemoryStoreService):
        self.service = service
    
    async def get_pending_choice_points(self, user_id: str):
        # 既存のメソッドを使って実装
        return await self.service.query_choice_points(
            filters={"user_id": user_id, "decided": False}
        )
```

### 方針C: choice_points.pyを修正

**適用条件**: 既存メソッドで対応可能だが、呼び出し方が異なる場合

**実装場所**: `backend/app/routers/choice_points.py`

---

## Step 3: 実装（30-60分）

### 3.1 推奨: 方針Aで実装

#### ファイル: `memory_store/service.py` 修正

**追加するメソッド**:

```python
# ===== Choice Point関連メソッド =====

async def get_pending_choice_points(self, user_id: str) -> List[Dict[str, Any]]:
    """
    未決定の選択肢を取得
    
    Args:
        user_id: ユーザーID
    
    Returns:
        未決定のChoice Pointリスト
    """
    async with self.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                id,
                user_id,
                question,
                choices,
                tags,
                context_type,
                created_at
            FROM choice_points
            WHERE user_id = $1
              AND selected_choice_id IS NULL
            ORDER BY created_at DESC
        """, user_id)
        
        return [dict(row) for row in rows]


async def create_choice_point(
    self,
    user_id: str,
    question: str,
    choices: List[Dict[str, str]],
    tags: List[str] = None,
    context_type: str = "general"
) -> Dict[str, Any]:
    """
    Choice Point作成
    
    Args:
        user_id: ユーザーID
        question: 質問
        choices: 選択肢リスト [{"choice_id": "A", "choice_text": "..."}]
        tags: タグリスト
        context_type: コンテキストタイプ
    
    Returns:
        作成されたChoice Point
    """
    tags = tags or []
    
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO choice_points (
                user_id,
                question,
                choices,
                tags,
                context_type,
                created_at
            )
            VALUES ($1, $2, $3::jsonb, $4, $5, NOW())
            RETURNING *
        """, user_id, question, json.dumps(choices), tags, context_type)
        
        return dict(row)


async def decide_choice(
    self,
    choice_point_id: str,
    selected_choice_id: str,
    decision_rationale: str,
    rejection_reasons: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    選択を決定（却下理由付き）
    
    Args:
        choice_point_id: Choice Point ID
        selected_choice_id: 選択されたchoice_id
        decision_rationale: 選択理由
        rejection_reasons: 却下理由辞書 {"choice_id": "reason"}
    
    Returns:
        更新されたChoice Point
    """
    rejection_reasons = rejection_reasons or {}
    
    async with self.pool.acquire() as conn:
        # 既存のChoice Pointを取得
        cp_row = await conn.fetchrow("""
            SELECT * FROM choice_points WHERE id = $1
        """, choice_point_id)
        
        if not cp_row:
            raise ValueError(f"Choice Point not found: {choice_point_id}")
        
        # choicesを更新（selected, rejection_reason追加）
        choices = json.loads(cp_row['choices'])
        updated_choices = []
        
        for choice in choices:
            choice_dict = dict(choice) if isinstance(choice, dict) else {"choice_id": choice.get("choice_id"), "choice_text": choice.get("choice_text")}
            choice_dict['selected'] = (choice_dict['choice_id'] == selected_choice_id)
            
            if choice_dict['selected']:
                choice_dict['rejection_reason'] = None
            else:
                choice_dict['rejection_reason'] = rejection_reasons.get(choice_dict['choice_id'], "")
            
            choice_dict['evaluated_at'] = datetime.utcnow().isoformat()
            updated_choices.append(choice_dict)
        
        # DB更新
        row = await conn.fetchrow("""
            UPDATE choice_points
            SET 
                selected_choice_id = $1,
                decision_rationale = $2,
                choices = $3::jsonb,
                decided_at = NOW()
            WHERE id = $4
            RETURNING *
        """, selected_choice_id, decision_rationale, json.dumps(updated_choices), choice_point_id)
        
        return dict(row)


async def search_choice_points(
    self,
    user_id: str,
    tags: List[str] = None,
    from_date: datetime = None,
    to_date: datetime = None,
    search_text: str = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Choice Point検索
    
    Args:
        user_id: ユーザーID
        tags: タグフィルタ
        from_date: 開始日時
        to_date: 終了日時
        search_text: フルテキスト検索
        limit: 取得件数
    
    Returns:
        検索結果リスト
    """
    async with self.pool.acquire() as conn:
        conditions = ["user_id = $1", "selected_choice_id IS NOT NULL"]
        params = [user_id]
        param_idx = 2
        
        # タグフィルタ
        if tags:
            conditions.append(f"tags && ${param_idx}::text[]")
            params.append(tags)
            param_idx += 1
        
        # 時間範囲フィルタ
        if from_date:
            conditions.append(f"decided_at >= ${param_idx}")
            params.append(from_date)
            param_idx += 1
        
        if to_date:
            conditions.append(f"decided_at <= ${param_idx}")
            params.append(to_date)
            param_idx += 1
        
        # フルテキスト検索
        if search_text:
            conditions.append(f"question ILIKE ${param_idx}")
            params.append(f"%{search_text}%")
            param_idx += 1
        
        params.append(limit)
        
        query = f"""
            SELECT * FROM choice_points
            WHERE {' AND '.join(conditions)}
            ORDER BY decided_at DESC
            LIMIT ${param_idx}
        """
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
```

**必要なimport追加**:
```python
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
```

---

### 3.2 PostgreSQLテーブル確認

Choice Pointsテーブルが存在するか確認:

```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\d choice_points"
```

**存在しない場合**、マイグレーションを実行:

```sql
-- docker/postgres/009_choice_points_table.sql (新規作成)

CREATE TABLE IF NOT EXISTS choice_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    choices JSONB NOT NULL,
    selected_choice_id VARCHAR(50),
    decision_rationale TEXT,
    tags TEXT[] DEFAULT '{}',
    context_type VARCHAR(50) DEFAULT 'general',
    session_id VARCHAR(255),
    intent_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    decided_at TIMESTAMPTZ
);

CREATE INDEX idx_choice_points_user ON choice_points(user_id);
CREATE INDEX idx_choice_points_tags ON choice_points USING GIN(tags);
CREATE INDEX idx_choice_points_decided ON choice_points(decided_at);
```

実行:
```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -f /docker-entrypoint-initdb.d/009_choice_points_table.sql
```

---

## Step 4: choice_points.pyの有効化（10分）

### 4.1 main.pyのコメントアウト解除

**ファイル**: `backend/app/main.py`

```python
# Before (Line 26)
# app.include_router(choice_points.router)  # 一時的に無効化

# After
app.include_router(choice_points.router)  # ✅ 有効化
```

### 4.2 Dockerコンテナ再起動

```bash
cd /Users/zero/Projects/resonant-engine/docker
docker compose restart backend
```

---

## Step 5: 動作確認（15分）

### 5.1 エンドポイント確認

```bash
# 1. 未決定選択肢取得
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test_user'
# 期待: {"choice_points":[],"count":0} または実際のデータ

# 2. 選択肢作成
curl -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "question": "データベース選定",
    "choices": [
      {"choice_id": "A", "choice_text": "PostgreSQL"},
      {"choice_id": "B", "choice_text": "SQLite"}
    ],
    "tags": ["technology", "database"]
  }'
# 期待: {"choice_point":{...}}

# 3. Swagger UI確認
open http://localhost:8000/docs
# choice-preservationタグに4エンドポイント表示されることを確認
```

### 5.2 エラーが出た場合

```bash
# ログ確認
docker logs resonant_backend

# よくあるエラー:
# 1. ImportError → memory_store/service.pyの構文エラー確認
# 2. AttributeError → メソッド名の確認
# 3. Database error → choice_pointsテーブルの存在確認
```

---

## Step 6: 統合テスト（15分）

### 6.1 E2Eフロー実行

```bash
# 1. 選択肢作成
RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "question": "認証方式選定",
    "choices": [
      {"choice_id": "A", "choice_text": "JWT"},
      {"choice_id": "B", "choice_text": "Session"}
    ],
    "tags": ["security"]
  }')

CHOICE_POINT_ID=$(echo $RESPONSE | jq -r '.choice_point.id')
echo "Created Choice Point: $CHOICE_POINT_ID"

# 2. 選択決定
curl -X PUT "http://localhost:8000/api/v1/memory/choice-points/$CHOICE_POINT_ID/decide" \
  -H 'Content-Type: application/json' \
  -d '{
    "selected_choice_id": "A",
    "decision_rationale": "スケーラビリティ重視",
    "rejection_reasons": {
      "B": "セッション管理の複雑さ"
    }
  }'

# 3. 検索で確認
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_user&tags=security'
```

**期待される結果**:
- 選択肢が作成される
- 決定が成功する
- 検索で取得できる
- 却下理由が保存されている

---

## 完了基準

### ✅ Phase 2完了判定

- [ ] `memory_store/service.py`に4メソッド追加完了
- [ ] `choice_points`テーブルが存在する
- [ ] `main.py`でルーター有効化済み
- [ ] 4エンドポイントすべてが200 OKを返す
- [ ] E2Eフローが正常動作
- [ ] Swagger UIで動作確認可能

### 📊 達成率

**Phase 2完了後**:
- エンドポイント: **14/14 (100%)** ✅
- Tier 1要件: **8/8 (100%)** ✅
- Backend API統合: **完全完了** ✅

---

## トラブルシューティング

### 問題1: choice_pointsテーブルが存在しない

**エラー**:
```
relation "choice_points" does not exist
```

**解決策**:
```bash
# マイグレーション実行
docker exec resonant_postgres psql -U resonant -d resonant_dashboard <<EOF
CREATE TABLE choice_points (...);
EOF
```

### 問題2: ImportError

**エラー**:
```
ImportError: cannot import name 'MemoryStoreService'
```

**解決策**:
```bash
# setup.pyが正しくインストールされているか確認
pip show resonant-memory-store

# 再インストール
cd /Users/zero/Projects/resonant-engine/backend
pip install -e ../memory_store --force-reinstall
```

### 問題3: メソッドシグネチャ不一致

**エラー**:
```
TypeError: create_choice_point() got an unexpected keyword argument 'tags'
```

**解決策**:
- `memory_store/service.py`のメソッドシグネチャを確認
- `choice_points.py`の呼び出し方を修正

---

## 次のステップ

Phase 2完了後:

1. **統合テスト実行**: 受け入れテスト仕様書に従って全テスト実行
2. **Frontend更新**: 仕様書修正、APIクライアント更新
3. **ドキュメント更新**: 実装完了レポート更新

---

**作成日**: 2025-11-30
**想定作業時間**: 1-2時間
**前提**: Phase 1完了（10/14エンドポイント動作）
**目標**: 14/14エンドポイント完全動作
