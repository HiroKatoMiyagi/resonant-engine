# Sprint 7: Session Summary自動生成 作業開始指示書

## 📋 作業概要

**Sprint**: Sprint 7
**目的**: セッション単位で会話を自動要約し、Context Assemblerで活用することで長期的な文脈保持を強化
**期間**: 5日間
**担当**: Tsumu (Cursor) + Kana (Claude Sonnet 4.5)

---

## 🎯 ゴール

### ビフォー（Sprint 6完了時）
```python
# Context Assembler内部
memory_layers = {
    "working_memory": [最新10件],  # ✅
    "semantic_memory": [関連5件],   # ✅
    "session_summary": None,        # ❌ 常にNone
}
```

### アフター（Sprint 7完了時）
```python
# Context Assembler内部
memory_layers = {
    "working_memory": [最新10件],
    "semantic_memory": [関連5件],
    "session_summary": "2025-11-18 10:00-12:00: Memory Store実装セッション...",  # ✅
}

# PostgreSQL
session_summaries テーブル:
  - 要約テキスト自動生成
  - メッセージ数20件ごとにトリガー
  - Claude Haiku使用（高速・低コスト）
```

---

## 📊 前提確認

### 実装済みコンポーネント（Sprint 5-6）
- ✅ Context Assembler Service
- ✅ KanaAIBridge（Context Assembler統合）
- ✅ Intent Bridge（KanaAIBridge使用）
- ✅ MessageRepository
- ✅ MemoryRepository

### 確認すべき環境
```bash
# PostgreSQL起動確認
pg_ctl status

# 環境変数確認
echo $DATABASE_URL
echo $ANTHROPIC_API_KEY

# 既存テーブル確認
psql -U postgres -d resonant_engine -c "\dt"
# → messages, memories, intents が存在することを確認
```

---

## 🗓️ 実装スケジュール

### Day 1: データモデルとRepository (3-4時間)
1. session_summariesテーブル作成（マイグレーション）
2. SessionSummaryRepository実装
3. 単体テスト（5件）

### Day 2: Summarization Service (4-5時間)
1. SummarizationService実装
2. Claude API統合
3. 要約生成プロンプト設計
4. 単体テスト（8件）

### Day 3: SessionManager (3-4時間)
1. SessionManager実装
2. トリガー条件判定ロジック
3. 単体テスト（6件）

### Day 4: Context Assembler統合 (3-4時間)
1. Context Assembler修正
2. Intent Bridge修正
3. 単体テスト（7件）

### Day 5: E2Eテストと受け入れテスト (4-5時間)
1. E2Eテスト実装（3件）
2. 受け入れテスト実行（12件）
3. バグ修正
4. ドキュメント更新

---

## 📝 Day 1: データモデルとRepository

### タスク1-1: PostgreSQLマイグレーション

**ファイル**: `migrations/007_create_session_summaries.sql` (新規作成)

**実装内容**:

```sql
-- Session Summariesテーブル作成
CREATE TABLE IF NOT EXISTS session_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id UUID NOT NULL,
    summary TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 制約
    CONSTRAINT unique_session_summary UNIQUE (user_id, session_id),
    CONSTRAINT positive_message_count CHECK (message_count >= 0)
);

-- インデックス
CREATE INDEX idx_session_summaries_user_id
    ON session_summaries(user_id);

CREATE INDEX idx_session_summaries_session_id
    ON session_summaries(session_id);

CREATE INDEX idx_session_summaries_created_at
    ON session_summaries(created_at DESC);

-- コメント
COMMENT ON TABLE session_summaries IS 'セッション単位の会話要約';
COMMENT ON COLUMN session_summaries.summary IS '要約テキスト（Claude生成）';
COMMENT ON COLUMN session_summaries.message_count IS '要約に含まれるメッセージ数';
COMMENT ON COLUMN session_summaries.start_time IS 'セッション開始時刻';
COMMENT ON COLUMN session_summaries.end_time IS 'セッション終了時刻';
```

**実行**:
```bash
psql -U postgres -d resonant_engine -f migrations/007_create_session_summaries.sql
```

**検証**:
```bash
psql -U postgres -d resonant_engine -c "\d session_summaries"
```

### タスク1-2: Pythonモデル拡張

**ファイル**: `memory_store/models.py` (既存ファイル修正)

**追加内容**:

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class SessionSummaryResponse(BaseModel):
    """Session Summary応答モデル"""
    id: UUID
    user_id: str
    session_id: UUID
    summary: str
    message_count: int = Field(ge=0, description="要約に含まれるメッセージ数")
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SessionStats(BaseModel):
    """セッション統計モデル"""
    session_id: UUID
    message_count: int
    first_message_time: Optional[datetime] = None
    last_message_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    has_summary: bool = False
    last_summary_time: Optional[datetime] = None
```

### タスク1-3: SessionSummaryRepository実装

**ファイル**: `memory_store/session_summary_repository.py` (新規作成)

**実装内容**:

```python
"""Session Summary Repository - Session要約の永続化層"""

import asyncpg
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from memory_store.models import SessionSummaryResponse


class SessionSummaryRepository:
    """Session Summary永続化層"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save(
        self,
        user_id: str,
        session_id: UUID,
        summary: str,
        message_count: int,
        start_time: datetime,
        end_time: datetime,
    ) -> UUID:
        """
        Session Summaryを保存

        Args:
            user_id: ユーザーID
            session_id: セッションID
            summary: 要約テキスト
            message_count: メッセージ数
            start_time: セッション開始時刻
            end_time: セッション終了時刻

        Returns:
            UUID: 保存されたSession SummaryのID

        Note:
            同じuser_id + session_idの組み合わせの場合、UPSERTで更新
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO session_summaries (
                    user_id, session_id, summary, message_count,
                    start_time, end_time, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                ON CONFLICT (user_id, session_id)
                DO UPDATE SET
                    summary = EXCLUDED.summary,
                    message_count = EXCLUDED.message_count,
                    end_time = EXCLUDED.end_time,
                    updated_at = NOW()
                RETURNING id
            """, user_id, session_id, summary, message_count, start_time, end_time)

            return result['id']

    async def get_latest(
        self,
        user_id: str,
        session_id: Optional[UUID] = None,
    ) -> Optional[SessionSummaryResponse]:
        """
        最新のSession Summaryを取得

        Args:
            user_id: ユーザーID
            session_id: セッションID（Noneの場合は最新）

        Returns:
            SessionSummaryResponse or None
        """
        async with self.pool.acquire() as conn:
            if session_id:
                # 特定セッションの要約
                row = await conn.fetchrow("""
                    SELECT * FROM session_summaries
                    WHERE user_id = $1 AND session_id = $2
                    ORDER BY created_at DESC
                    LIMIT 1
                """, user_id, session_id)
            else:
                # ユーザーの最新要約
                row = await conn.fetchrow("""
                    SELECT * FROM session_summaries
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, user_id)

            if row:
                return SessionSummaryResponse(**dict(row))
            return None

    async def get_by_session(
        self,
        session_id: UUID,
    ) -> Optional[SessionSummaryResponse]:
        """
        特定セッションのSummaryを取得

        Args:
            session_id: セッションID

        Returns:
            SessionSummaryResponse or None
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM session_summaries
                WHERE session_id = $1
            """, session_id)

            if row:
                return SessionSummaryResponse(**dict(row))
            return None

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[SessionSummaryResponse]:
        """
        ユーザーのSession Summary一覧を取得

        Args:
            user_id: ユーザーID
            limit: 取得件数

        Returns:
            List[SessionSummaryResponse]
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM session_summaries
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)

            return [SessionSummaryResponse(**dict(row)) for row in rows]

    async def delete(self, summary_id: UUID) -> bool:
        """
        Session Summaryを削除

        Args:
            summary_id: Summary ID

        Returns:
            bool: 削除成功したらTrue
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM session_summaries
                WHERE id = $1
            """, summary_id)

            return result == "DELETE 1"
```

### タスク1-4: 単体テスト（Repository）

**ファイル**: `tests/memory_store/test_session_summary_repository.py` (新規作成)

**実装内容**:

```python
"""SessionSummaryRepository単体テスト"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from memory_store.session_summary_repository import SessionSummaryRepository
from memory_store.models import SessionSummaryResponse


@pytest.fixture
def mock_pool():
    """Mock PostgreSQL pool"""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool, conn


@pytest.mark.asyncio
async def test_save_new_summary(mock_pool):
    """新規Session Summaryの保存"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    summary_id = uuid4()
    conn.fetchrow.return_value = {'id': summary_id}

    user_id = "hiroki"
    session_id = uuid4()
    summary = "Test summary"
    start_time = datetime.now() - timedelta(hours=2)
    end_time = datetime.now()

    result_id = await repo.save(
        user_id=user_id,
        session_id=session_id,
        summary=summary,
        message_count=20,
        start_time=start_time,
        end_time=end_time,
    )

    assert result_id == summary_id
    conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_with_session_id(mock_pool):
    """特定セッションの最新要約取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    session_id = uuid4()
    conn.fetchrow.return_value = {
        'id': uuid4(),
        'user_id': 'hiroki',
        'session_id': session_id,
        'summary': 'Test summary',
        'message_count': 20,
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }

    result = await repo.get_latest(user_id="hiroki", session_id=session_id)

    assert result is not None
    assert isinstance(result, SessionSummaryResponse)
    assert result.session_id == session_id


@pytest.mark.asyncio
async def test_get_latest_without_session_id(mock_pool):
    """ユーザーの最新要約取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    conn.fetchrow.return_value = {
        'id': uuid4(),
        'user_id': 'hiroki',
        'session_id': uuid4(),
        'summary': 'Latest summary',
        'message_count': 30,
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }

    result = await repo.get_latest(user_id="hiroki")

    assert result is not None
    assert result.summary == 'Latest summary'


@pytest.mark.asyncio
async def test_get_by_session(mock_pool):
    """セッションIDで要約取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    session_id = uuid4()
    conn.fetchrow.return_value = {
        'id': uuid4(),
        'user_id': 'hiroki',
        'session_id': session_id,
        'summary': 'Session summary',
        'message_count': 25,
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }

    result = await repo.get_by_session(session_id)

    assert result is not None
    assert result.session_id == session_id


@pytest.mark.asyncio
async def test_list_by_user(mock_pool):
    """ユーザーの要約一覧取得"""
    pool, conn = mock_pool
    repo = SessionSummaryRepository(pool)

    conn.fetch.return_value = [
        {
            'id': uuid4(),
            'user_id': 'hiroki',
            'session_id': uuid4(),
            'summary': f'Summary {i}',
            'message_count': 20 + i,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
        for i in range(5)
    ]

    results = await repo.list_by_user(user_id="hiroki", limit=10)

    assert len(results) == 5
    assert all(isinstance(r, SessionSummaryResponse) for r in results)
```

**実行**:
```bash
pytest tests/memory_store/test_session_summary_repository.py -v
```

---

## 📝 Day 2: Summarization Service

### タスク2-1: 設定モデル

**ファイル**: `session/config.py` (新規作成)

```python
"""Session管理設定"""

from pydantic import BaseModel, Field


class SessionConfig(BaseModel):
    """セッション管理設定"""

    # 要約生成トリガー条件
    summary_trigger_message_count: int = Field(
        default=20,
        ge=10,
        description="この数のメッセージ後に要約生成"
    )

    summary_trigger_interval_seconds: int = Field(
        default=3600,  # 1時間
        ge=300,  # 最低5分
        description="前回要約からこの秒数経過後に要約生成"
    )

    # 要約設定
    summary_max_messages: int = Field(
        default=100,
        ge=10,
        description="要約に含める最大メッセージ数"
    )

    # Claude API設定
    claude_model: str = Field(
        default="claude-3-5-haiku-20241022",  # 高速なHaikuを使用
        description="要約生成に使用するClaudeモデル"
    )

    claude_max_tokens: int = Field(
        default=500,
        ge=100,
        le=1000,
        description="要約の最大トークン数"
    )


def get_default_session_config() -> SessionConfig:
    """デフォルト設定を取得"""
    return SessionConfig()
```

### タスク2-2: SummarizationService実装

**ファイル**: `summarization/service.py` (新規作成)

```python
"""Summarization Service - 会話要約生成サービス"""

import os
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from anthropic import AsyncAnthropic

from memory_store.repository import MessageRepository
from memory_store.session_summary_repository import SessionSummaryRepository
from memory_store.models import MessageResponse, SessionSummaryResponse
from session.config import SessionConfig, get_default_session_config


class SummarizationService:
    """会話要約生成サービス"""

    def __init__(
        self,
        message_repo: MessageRepository,
        summary_repo: SessionSummaryRepository,
        config: Optional[SessionConfig] = None,
        claude_client: Optional[AsyncAnthropic] = None,
    ):
        self.message_repo = message_repo
        self.summary_repo = summary_repo
        self.config = config or get_default_session_config()
        self.claude_client = claude_client or self._create_claude_client()

    def _create_claude_client(self) -> AsyncAnthropic:
        """Claude APIクライアントを作成"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        return AsyncAnthropic(api_key=api_key)

    async def create_summary(
        self,
        user_id: str,
        session_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> SessionSummaryResponse:
        """
        セッションの要約を生成

        Args:
            user_id: ユーザーID
            session_id: セッションID
            start_time: セッション開始時刻（Noneの場合は自動計算）
            end_time: セッション終了時刻（Noneの場合は現在時刻）

        Returns:
            SessionSummaryResponse: 生成された要約

        Raises:
            ValueError: メッセージが存在しない場合
        """
        # 1. セッションのメッセージを取得
        messages = await self._fetch_session_messages(
            user_id, session_id, start_time, end_time
        )

        if not messages:
            raise ValueError(f"No messages found for session {session_id}")

        # 2. 時刻情報を計算
        actual_start_time = start_time or messages[0].created_at
        actual_end_time = end_time or messages[-1].created_at

        # 3. Claude APIで要約生成
        summary_text = await self._generate_summary_with_claude(messages)

        # 4. 要約を保存
        summary_id = await self.summary_repo.save(
            user_id=user_id,
            session_id=session_id,
            summary=summary_text,
            message_count=len(messages),
            start_time=actual_start_time,
            end_time=actual_end_time,
        )

        # 5. 保存された要約を返す
        return await self.summary_repo.get_by_session(session_id)

    async def _fetch_session_messages(
        self,
        user_id: str,
        session_id: UUID,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> List[MessageResponse]:
        """セッションのメッセージを取得"""
        # session_idでフィルタリング（実装依存）
        # ここではmessages.session_idカラムがあると仮定

        # 簡易版: user_idで取得して時刻でフィルタ
        all_messages, _ = await self.message_repo.list(
            user_id=user_id,
            limit=self.config.summary_max_messages,
        )

        # 時刻フィルタ（start_time, end_timeがあれば）
        if start_time or end_time:
            filtered = []
            for msg in all_messages:
                if start_time and msg.created_at < start_time:
                    continue
                if end_time and msg.created_at > end_time:
                    continue
                filtered.append(msg)
            return filtered

        return all_messages

    async def _generate_summary_with_claude(
        self,
        messages: List[MessageResponse],
    ) -> str:
        """Claude APIで要約生成"""
        prompt = self._build_summarization_prompt(messages)

        response = await self.claude_client.messages.create(
            model=self.config.claude_model,
            max_tokens=self.config.claude_max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.content[0].text

    def _build_summarization_prompt(
        self,
        messages: List[MessageResponse],
    ) -> str:
        """要約生成用プロンプトを構築"""
        # メッセージを整形
        conversation = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in messages
        ])

        # 時刻情報
        start_time = messages[0].created_at.strftime("%Y-%m-%d %H:%M")
        end_time = messages[-1].created_at.strftime("%Y-%m-%d %H:%M")

        return f"""以下の会話セッションを要約してください。

要約の要件:
1. 3-5文の簡潔な要約
2. 主要なトピック、決定事項、成果を含める
3. 次のステップや未解決の課題があれば記載
4. 日時情報を含める（{start_time} - {end_time}）
5. 技術的な詳細は省略し、高レベルな概要を提供

会話（{len(messages)}メッセージ）:
{conversation}

要約（3-5文、日本語）:"""
```

### タスク2-3: 単体テスト（Summarization Service）

**ファイル**: `tests/summarization/test_service.py` (新規作成)

8件のテストを実装（省略：実際には詳細に記述）

---

## 📝 Day 3-5は省略（同様の構成）

Day 3: SessionManager実装
Day 4: Context Assembler / Intent Bridge統合
Day 5: E2Eテストと受け入れテスト

詳細は仕様書とテスト仕様書を参照。

---

## 🔧 環境設定

### 必須環境変数

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
DATABASE_URL=postgresql://postgres:password@localhost:5432/resonant_engine
```

### Python依存関係

```bash
# 既存
pip install asyncpg anthropic pydantic

# 追加確認
pip list | grep -E "asyncpg|anthropic|pydantic"
```

---

## 🐛 トラブルシューティング

### 問題1: Claude API呼び出し失敗

**エラー**:
```
anthropic.APIError: API request failed
```

**対策**:
```python
# リトライ機構追加
for attempt in range(3):
    try:
        response = await claude.messages.create(...)
        break
    except APIError as e:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)
```

### 問題2: セッションIDがない

**エラー**:
```
session_id is None
```

**対策**:
- Intent作成時にsession_idを設定
- または、user_id + 時刻でセッションを自動判定

---

## 📊 成功指標

### 実装完了判定
- [ ] session_summariesテーブル作成
- [ ] 5コンポーネント実装完了
- [ ] 単体テスト26件全てPASS
- [ ] E2Eテスト3件全てPASS
- [ ] 受け入れテスト12件全てPASS

### 動作確認
```bash
# 要約生成テスト
python -c "
import asyncio
from summarization.service import SummarizationService
# ... 実行
"
```

---

## 📚 参考資料

- [Sprint 7仕様書](../architecture/sprint7_session_summary_spec.md)
- [Sprint 7受け入れテスト仕様書](../test/sprint7_acceptance_test_spec.md)
- [Sprint 6: Intent Bridge統合](./sprint6_intent_bridge_integration_start.md)
