# Sprint 7: Session Summary自動生成 受け入れテスト仕様書

## 📋 概要

**Sprint**: Sprint 7
**テスト対象**: Session Summary自動生成機能
**テスト件数**: 12件
**実行環境**: PostgreSQL + Session Manager + SummarizationService + Context Assembler

---

## 🎯 テスト方針

### 検証レベル
1. **Unit（単体）**: Repository, Service, Managerの個別機能
2. **Integration（統合）**: コンポーネント間連携
3. **E2E（End-to-End）**: 要約生成 → 保存 → 取得の全フロー
4. **Acceptance（受け入れ）**: ユーザー要求の充足確認

### 合格基準
- 全12テストケース PASS
- カバレッジ 80%以上
- 重大な既知のバグなし

---

## 📝 テストケース一覧

| ID | カテゴリ | テスト名 | 優先度 |
|----|---------|---------|--------|
| TC-01 | Unit | SessionSummaryRepository: save/get | P1 |
| TC-02 | Unit | SummarizationService: 要約生成 | P1 |
| TC-03 | Unit | SessionManager: トリガー判定 | P1 |
| TC-04 | Unit | Context Assembler: Session Summary取得 | P1 |
| TC-05 | Integration | 要約生成 → 保存 → 取得フロー | P1 |
| TC-06 | Integration | トリガー条件: メッセージ数閾値 | P1 |
| TC-07 | Integration | トリガー条件: 時間経過 | P2 |
| TC-08 | E2E | Intent処理 → 要約自動生成 | P1 |
| TC-09 | E2E | Context Assemblerで要約取得 | P1 |
| TC-10 | E2E | 複数セッションの要約管理 | P2 |
| TC-11 | Acceptance | 長いセッションの文脈保持 | P1 |
| TC-12 | Acceptance | 要約品質確認 | P2 |

---

## 🧪 テストケース詳細

### TC-01: SessionSummaryRepository - save/get

**目的**: Session Summaryの保存と取得が正しく動作することを確認

**前提条件**:
- PostgreSQL起動中
- session_summariesテーブル作成済み

**テスト手順**:
```python
import asyncio
import asyncpg
from uuid import uuid4
from datetime import datetime
from memory_store.session_summary_repository import SessionSummaryRepository

async def test():
    # 1. 接続
    pool = await asyncpg.create_pool(
        "postgresql://postgres:password@localhost:5432/resonant_engine"
    )
    repo = SessionSummaryRepository(pool)

    # 2. 保存
    user_id = "hiroki"
    session_id = uuid4()
    summary = "Test session: Memory Store implementation completed"

    summary_id = await repo.save(
        user_id=user_id,
        session_id=session_id,
        summary=summary,
        message_count=25,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )

    # 3. 取得
    result = await repo.get_by_session(session_id)

    # 4. 検証
    assert result is not None
    assert result.summary == summary
    assert result.message_count == 25
    assert result.session_id == session_id

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ Summaryが保存される
- ✅ session_idで取得できる
- ✅ 全フィールドが正しい

**テストコード**: `tests/memory_store/test_session_summary_repository.py::test_save_and_get`

---

### TC-02: SummarizationService - 要約生成

**目的**: Claude APIを使用した要約生成が動作することを確認

**前提条件**:
- ANTHROPIC_API_KEY設定済み
- messagesテーブルにテストデータ存在

**テスト手順**:
```python
import asyncio
from uuid import uuid4
from memory_store.repository import MessageRepository
from memory_store.session_summary_repository import SessionSummaryRepository
from summarization.service import SummarizationService

async def test():
    pool = await asyncpg.create_pool(...)

    message_repo = MessageRepository(pool)
    summary_repo = SessionSummaryRepository(pool)
    service = SummarizationService(message_repo, summary_repo)

    # テストデータ: 20件のメッセージ
    user_id = "hiroki"
    session_id = uuid4()

    # （事前に20件のメッセージをmessagesテーブルに挿入）

    # 要約生成
    result = await service.create_summary(
        user_id=user_id,
        session_id=session_id,
    )

    # 検証
    assert result is not None
    assert len(result.summary) > 0
    assert result.message_count == 20
    assert "Memory Store" in result.summary  # 内容の確認

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ 要約テキストが生成される
- ✅ 3-5文の簡潔な要約
- ✅ 主要トピックが含まれる

**テストコード**: `tests/summarization/test_service.py::test_create_summary`

---

### TC-03: SessionManager - トリガー判定

**目的**: 要約生成トリガー条件の判定が正しく動作することを確認

**前提条件**:
- SessionManager初期化済み

**テスト手順**:
```python
import asyncio
from unittest.mock import AsyncMock
from session.manager import SessionManager

async def test():
    # Mock dependencies
    message_repo = AsyncMock()
    summary_repo = AsyncMock()
    summarization = AsyncMock()

    manager = SessionManager(message_repo, summary_repo, summarization)

    # ケース1: メッセージ数が20件 → 要約生成すべき
    message_repo.list.return_value = ([Mock()] * 20, 20)
    summary_repo.get_latest.return_value = None

    should_create = await manager._should_create_summary("hiroki", uuid4())
    assert should_create is True

    # ケース2: メッセージ数が10件 → 要約生成しない
    message_repo.list.return_value = ([Mock()] * 10, 10)

    should_create = await manager._should_create_summary("hiroki", uuid4())
    assert should_create is False

asyncio.run(test())
```

**期待結果**:
- ✅ メッセージ数 >= 20 で True
- ✅ メッセージ数 < 20 で False
- ✅ 時間経過条件も正しく判定

**テストコード**: `tests/session/test_manager.py::test_should_create_summary`

---

### TC-04: Context Assembler - Session Summary取得

**目的**: Context AssemblerがSession Summaryを取得できることを確認

**前提条件**:
- session_summariesテーブルにデータ存在

**テスト手順**:
```python
import asyncio
from uuid import uuid4
from context_assembler.service import ContextAssemblerService

async def test():
    pool = await asyncpg.create_pool(...)

    # 事前にSession Summaryを保存
    session_id = uuid4()
    # （summary_repo.save()で保存）

    # Context Assembler初期化
    ca = await create_context_assembler(pool=pool)

    # Session Summary取得
    summary_text = await ca._fetch_session_summary(
        user_id="hiroki",
        session_id=session_id,
    )

    # 検証
    assert summary_text is not None
    assert len(summary_text) > 0

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ Session Summaryが取得される
- ✅ session_id=Noneの場合はNoneを返す

**テストコード**: `tests/context_assembler/test_service_session_summary.py::test_fetch_session_summary`

---

### TC-05: Integration - 要約生成 → 保存 → 取得フロー

**目的**: 要約生成から取得までの全フローが動作することを確認

**前提条件**:
- 実DB接続可能
- ANTHROPIC_API_KEY設定済み

**テスト手順**:
```python
import asyncio
from uuid import uuid4

async def test():
    pool = await asyncpg.create_pool(...)

    user_id = "hiroki"
    session_id = uuid4()

    # 1. メッセージ挿入（20件）
    async with pool.acquire() as conn:
        for i in range(20):
            await conn.execute("""
                INSERT INTO messages (id, user_id, role, content, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, uuid4(), user_id, 'user' if i % 2 == 0 else 'assistant', f'Message {i}')

    # 2. 要約生成
    service = SummarizationService(...)
    summary = await service.create_summary(user_id, session_id)

    # 3. 要約取得
    repo = SessionSummaryRepository(pool)
    retrieved = await repo.get_by_session(session_id)

    # 4. 検証
    assert summary.id == retrieved.id
    assert summary.summary == retrieved.summary

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ 要約生成成功
- ✅ PostgreSQLに保存される
- ✅ 取得できる

**テストコード**: `tests/integration/test_summarization_flow.py::test_create_save_retrieve`

---

### TC-06: Integration - トリガー条件: メッセージ数閾値

**目的**: メッセージ数が20件に達したら自動的に要約生成されることを確認

**前提条件**:
- SessionManager初期化済み
- 実DB接続可能

**テスト手順**:
```python
import asyncio

async def test():
    pool = await asyncpg.create_pool(...)

    user_id = "hiroki"
    session_id = uuid4()

    # SessionManager初期化
    manager = await create_session_manager(pool)

    # メッセージ19件挿入 → 要約生成されない
    # （メッセージ挿入処理）

    result1 = await manager.check_and_create_summary(user_id, session_id)
    assert result1 is None

    # メッセージ1件追加（合計20件） → 要約生成される
    # （メッセージ挿入処理）

    result2 = await manager.check_and_create_summary(user_id, session_id)
    assert result2 is not None
    assert result2.message_count == 20

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ 19件では要約生成されない
- ✅ 20件で要約生成される

**テストコード**: `tests/session/test_manager_integration.py::test_message_count_trigger`

---

### TC-07: Integration - トリガー条件: 時間経過

**目的**: 前回要約から1時間経過したら要約生成されることを確認

**前提条件**:
- SessionManager初期化済み
- 前回の要約が存在

**テスト手順**:
```python
import asyncio
from datetime import datetime, timedelta

async def test():
    pool = await asyncpg.create_pool(...)

    user_id = "hiroki"
    session_id = uuid4()

    # 1時間前の要約を作成
    summary_repo = SessionSummaryRepository(pool)
    await summary_repo.save(
        user_id=user_id,
        session_id=session_id,
        summary="Old summary",
        message_count=20,
        start_time=datetime.now() - timedelta(hours=2),
        end_time=datetime.now() - timedelta(hours=1, minutes=5),  # 1時間5分前
    )

    # 新しいメッセージを追加（15件）
    # （メッセージ挿入）

    # トリガーチェック
    manager = await create_session_manager(pool)
    result = await manager.check_and_create_summary(user_id, session_id)

    # 検証: 1時間経過しているので要約生成される
    assert result is not None
    assert result.message_count > 20

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ 1時間経過で要約生成される
- ✅ 59分では要約生成されない（別テスト）

**テストコード**: `tests/session/test_manager_integration.py::test_time_trigger`

---

### TC-08: E2E - Intent処理 → 要約自動生成

**目的**: Intent処理完了後に自動的に要約生成されることを確認

**前提条件**:
- Intent Bridge初期化済み
- SessionManager統合済み
- 実DB接続可能

**テスト手順**:
```python
import asyncio
from uuid import uuid4

async def test():
    pool = await asyncpg.create_pool(...)

    user_id = "hiroki"
    session_id = uuid4()

    # 1. 20件のメッセージ挿入（Intent処理をシミュレート）
    for i in range(20):
        intent_id = uuid4()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO intents (id, user_id, session_id, description, status)
                VALUES ($1, $2, $3, $4, 'pending')
            """, intent_id, user_id, session_id, f"Intent {i}")

        # Intent処理
        processor = IntentProcessor(pool, {})
        await processor.initialize()
        await processor.process(intent_id)

    # 2. Session Summary確認
    summary_repo = SessionSummaryRepository(pool)
    summary = await summary_repo.get_latest(user_id, session_id)

    # 3. 検証
    assert summary is not None
    assert summary.message_count >= 20

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ Intent処理後に要約生成される
- ✅ session_summariesテーブルに保存される

**テストコード**: `tests/integration/test_intent_summarization_e2e.py::test_auto_summary_after_intent`

---

### TC-09: E2E - Context Assemblerで要約取得

**目的**: Context Assemblerが要約を自動的に取得して使用することを確認

**前提条件**:
- Session Summary存在
- Context Assembler初期化済み

**テスト手順**:
```python
import asyncio
from uuid import uuid4

async def test():
    pool = await asyncpg.create_pool(...)

    user_id = "hiroki"
    session_id = uuid4()

    # 1. Session Summary作成
    summary_repo = SessionSummaryRepository(pool)
    await summary_repo.save(
        user_id=user_id,
        session_id=session_id,
        summary="Session summary: Memory Store implementation session",
        message_count=30,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )

    # 2. Context Assembler経由で取得
    ca = await create_context_assembler(pool=pool)
    context = await ca.assemble_context(
        user_message="前回のセッションの続きから始めたい",
        user_id=user_id,
        session_id=session_id,
    )

    # 3. 検証
    assert context.metadata.has_session_summary is True

    # メッセージリストにSession Summaryが含まれることを確認
    messages_str = str(context.messages)
    assert "Session summary" in messages_str or "Memory Store implementation" in messages_str

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ Session Summaryが取得される
- ✅ context.metadata.has_session_summary = True
- ✅ messagesにSession Summaryが含まれる

**テストコード**: `tests/integration/test_context_assembler_with_summary.py::test_assemble_with_session_summary`

---

### TC-10: E2E - 複数セッションの要約管理

**目的**: 複数セッションの要約を正しく管理できることを確認

**前提条件**:
- 実DB接続可能

**テスト手順**:
```python
import asyncio
from uuid import uuid4

async def test():
    pool = await asyncpg.create_pool(...)

    user_id = "hiroki"
    session_id_1 = uuid4()
    session_id_2 = uuid4()

    summary_repo = SessionSummaryRepository(pool)

    # セッション1の要約
    await summary_repo.save(
        user_id=user_id,
        session_id=session_id_1,
        summary="Sprint 1: Bridge Lite implementation",
        message_count=25,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )

    # セッション2の要約
    await summary_repo.save(
        user_id=user_id,
        session_id=session_id_2,
        summary="Sprint 2: Memory Store implementation",
        message_count=30,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )

    # 取得
    summary1 = await summary_repo.get_by_session(session_id_1)
    summary2 = await summary_repo.get_by_session(session_id_2)

    # 検証
    assert summary1.summary == "Sprint 1: Bridge Lite implementation"
    assert summary2.summary == "Sprint 2: Memory Store implementation"
    assert summary1.session_id != summary2.session_id

    # ユーザーの要約一覧
    summaries = await summary_repo.list_by_user(user_id, limit=10)
    assert len(summaries) == 2

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ 複数セッションの要約を個別に管理
- ✅ session_idで正しく取得
- ✅ ユーザー単位での一覧取得

**テストコード**: `tests/integration/test_multi_session_summary.py::test_multiple_sessions`

---

### TC-11: Acceptance - 長いセッションの文脈保持

**目的**: 50+メッセージのセッションでも文脈を保持できることを確認

**前提条件**:
- 実DB + 実Claude API使用

**テスト手順**:
```python
import asyncio
from uuid import uuid4

async def test():
    pool = await asyncpg.create_pool(...)

    user_id = "hiroki"
    session_id = uuid4()

    # 1. 50件のメッセージを挿入
    # （Memory Storeに関する会話）

    # 2. 要約生成
    service = SummarizationService(...)
    summary = await service.create_summary(user_id, session_id)

    # 3. Context Assembler経由で使用
    ca = await create_context_assembler(pool=pool)
    context = await ca.assemble_context(
        user_message="Memory Storeの実装状況を教えて",
        user_id=user_id,
        session_id=session_id,
    )

    # 4. 検証
    # Working Memory: 10件
    # Semantic Memory: 5件
    # Session Summary: 1件（50件の要約）
    assert context.metadata.working_memory_count == 10
    assert context.metadata.semantic_memory_count >= 0
    assert context.metadata.has_session_summary is True

    # 合計で50件の文脈を16-17件に圧縮
    total_context = (
        context.metadata.working_memory_count +
        context.metadata.semantic_memory_count +
        (1 if context.metadata.has_session_summary else 0)
    )
    assert total_context < 50

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ 50件のセッションを適切に要約
- ✅ Context Assemblerで効率的に文脈提供
- ✅ データ削減しながら文脈保持

**テストコード**: `tests/acceptance/test_long_session_context.py::test_50_message_session`

---

### TC-12: Acceptance - 要約品質確認

**目的**: 生成される要約の品質が十分であることを確認

**前提条件**:
- 実DB + 実Claude API使用
- テスト用会話データ準備

**テスト手順**:
```python
import asyncio

async def test():
    pool = await asyncpg.create_pool(...)

    # テスト用会話データ: Memory Store実装の会話
    # （20メッセージ挿入）

    # 要約生成
    service = SummarizationService(...)
    summary = await service.create_summary("hiroki", session_id)

    # 品質検証
    summary_text = summary.summary

    # 1. 長さ確認（3-5文）
    sentences = summary_text.split('。')
    assert 3 <= len(sentences) <= 6

    # 2. 主要トピック含有確認
    assert "Memory Store" in summary_text
    assert "実装" in summary_text or "完了" in summary_text

    # 3. 日時情報確認
    # 要約に日時が含まれることを確認
    # （例: "2025-11-18 10:00-12:00"）

    # 4. 次のステップ言及（あれば）
    # "次" または "今後" などのキーワード

    await pool.close()

asyncio.run(test())
```

**期待結果**:
- ✅ 3-5文の簡潔な要約
- ✅ 主要トピックが含まれる
- ✅ 日時情報が含まれる
- ✅ 技術的詳細は省略される

**テストコード**: `tests/acceptance/test_summary_quality.py::test_summary_quality`

---

## 🔧 テスト実行方法

### 環境準備

```bash
# PostgreSQLテーブル作成
psql -U postgres -d resonant_engine -f migrations/007_create_session_summaries.sql

# 環境変数設定
export DATABASE_URL="postgresql://postgres:password@localhost:5432/resonant_engine"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### テスト実行

```bash
# 全テスト実行
pytest tests/memory_store/test_session_summary_repository.py -v
pytest tests/summarization/test_service.py -v
pytest tests/session/test_manager.py -v
pytest tests/integration/test_summarization*.py -v -m integration
pytest tests/acceptance/test_*.py -v -m acceptance

# E2Eテスト（実DB + 実API使用）
pytest tests/integration/ -v -m e2e
```

### カバレッジ測定

```bash
pytest --cov=memory_store --cov=summarization --cov=session \
       --cov=context_assembler --cov=intent_bridge \
       --cov-report=html
```

---

## 📊 合格判定

### Tier 1: 必須（Must Pass）

- [ ] TC-01~TC-12 全てPASS
- [ ] E2Eテスト（TC-08, TC-09）で実際にClaude APIが応答
- [ ] 要約品質確認（TC-12）で適切な要約生成
- [ ] PostgreSQLに正しく保存される

### Tier 2: 推奨（Should Pass）

- [ ] カバレッジ80%以上
- [ ] パフォーマンス: 要約生成5秒以内
- [ ] ログ出力が適切

---

## 🐛 既知の問題・制限事項

### 制限事項
1. **Session IDの管理**: messagesテーブルにsession_idカラムが必要（未実装の場合はMock）
2. **時間経過判定**: 実時間でのテストは困難（時刻をMock）
3. **Claude API コスト**: TC-02, TC-11, TC-12は実APIを使用（コスト発生）

---

## 📚 参考資料

- [Sprint 7仕様書](../architecture/sprint7_session_summary_spec.md)
- [Sprint 7作業開始指示書](../sprint/sprint7_session_summary_start.md)
- [Sprint 6受け入れテスト](./sprint6_acceptance_test_spec.md)

---

## ✅ 受け入れ完了条件

**Sprint 7を受け入れるための最終チェックリスト:**

- [ ] 全12テストケース PASS
- [ ] E2Eテストで実際のClaude API応答確認
- [ ] 要約品質確認
- [ ] PostgreSQLに正しく保存・取得可能
- [ ] Context Assemblerで要約取得確認
- [ ] カバレッジ80%以上
- [ ] ドキュメント更新完了
- [ ] コードレビュー完了
- [ ] 重大なバグなし

**全て✅の場合: Sprint 7 ACCEPTED**
