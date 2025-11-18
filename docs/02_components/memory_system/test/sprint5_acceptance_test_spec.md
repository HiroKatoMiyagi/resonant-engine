# Sprint 5: Context Assembler — 受け入れテスト仕様書

**Sprint**: Sprint 5 - Context Assembler
**テスト責任者**: Kana (外界翻訳層)
**レビュアー**: Yuno (思想中枢層) / 宏啓 (プロジェクトオーナー)
**作成日**: 2025-11-18

---

## 🎯 テスト目的

**Context Assemblerが、過去の記憶を正しく統合してClaude APIに渡し、真の会話記憶機能を実現することを検証する**

### 検証項目
1. Working Memory（直近会話）が正しく取得・整形されるか
2. Semantic Memory（関連記憶）が正しくベクトル検索されるか
3. Session Summaryが正しく追加されるか
4. トークン数が正しく推定され、上限管理されるか
5. KanaAIBridgeとの統合が正しく動作するか
6. Claude APIが過去の文脈を参照して応答するか

---

## 🧪 テスト環境

### 必須環境
- Python 3.11+
- PostgreSQL 15+ (pgvector extension有効)
- Anthropic API Key設定済み

### テストデータベース
```bash
# テスト用DBを作成
createdb resonant_test

# マイグレーション実行
psql -U postgres -d resonant_test -f docker/postgres/init.sql
psql -U postgres -d resonant_test -f dashboard/backend/schema.sql
```

### 環境変数
```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/resonant_test"
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 📋 テストケース一覧

| ID | テストケース名 | 優先度 | 種類 |
|----|---------------|--------|------|
| TC-01 | Working Memory取得テスト | 必須 | 単体 |
| TC-02 | Semantic Memory取得テスト | 必須 | 単体 |
| TC-03 | Session Summary取得テスト | 必須 | 単体 |
| TC-04 | メッセージリスト構築テスト | 必須 | 単体 |
| TC-05 | トークン数推定テスト | 必須 | 単体 |
| TC-06 | トークン圧縮テスト | 必須 | 単体 |
| TC-07 | Context Validator検証テスト | 必須 | 単体 |
| TC-08 | コンテキスト組み立て統合テスト | 必須 | 統合 |
| TC-09 | KanaAIBridge統合テスト | 必須 | 統合 |
| TC-10 | E2E: 過去の記憶参照テスト | 必須 | E2E |
| TC-11 | E2E: トークン上限超過テスト | 推奨 | E2E |
| TC-12 | E2E: Context Assembler未設定時のfallbackテスト | 必須 | E2E |
| TC-13 | 性能テスト: レイテンシ < 100ms | 推奨 | 性能 |
| TC-14 | 性能テスト: 大量データでの動作 | 推奨 | 性能 |

---

## 📝 テストケース詳細

### TC-01: Working Memory取得テスト

**目的**: Context AssemblerがMessage Repositoryから直近の会話を正しく取得できることを確認

**前提条件**:
- messagesテーブルにテストデータが存在
- user_id = "test_user"で15件のメッセージが保存されている

**テスト手順**:
1. Context Assemblerを初期化
2. `_fetch_working_memory(user_id="test_user", limit=10)` を呼び出し
3. 結果を検証

**期待結果**:
- 10件のメッセージが返される
- 時系列順（古い→新しい）で並んでいる
- 各メッセージに `user_id`, `content`, `message_type`, `created_at` が含まれる

**テストコード**:
```python
@pytest.mark.asyncio
async def test_fetch_working_memory(context_assembler, message_repo):
    """Working Memory取得テスト"""
    user_id = "test_user"

    # テストデータ作成
    for i in range(15):
        await message_repo.create(MessageCreate(
            user_id=user_id,
            content=f"Message {i}",
            message_type="user" if i % 2 == 0 else "kana"
        ))

    # Working Memory取得
    working_memory = await context_assembler._fetch_working_memory(
        user_id=user_id,
        limit=10
    )

    # 検証
    assert len(working_memory) == 10
    assert working_memory[0].content == "Message 5"  # 古い方から
    assert working_memory[-1].content == "Message 14"  # 新しい方
```

**合格基準**: テストがPASSすること

---

### TC-02: Semantic Memory取得テスト

**目的**: Context AssemblerがRetrieval Orchestratorからベクトル検索で関連記憶を取得できることを確認

**前提条件**:
- memoriesテーブルにテストデータが存在
- "呼吸のリズム"に関する記憶が保存されている

**テスト手順**:
1. Memory Storeに関連記憶を保存
2. Context Assemblerを初期化
3. `_fetch_semantic_memory(query="呼吸について", limit=5)` を呼び出し
4. 結果を検証

**期待結果**:
- 最大5件のMemoryResultが返される
- 各結果に `content`, `similarity` が含まれる
- 類似度が高い順に並んでいる

**テストコード**:
```python
@pytest.mark.asyncio
async def test_fetch_semantic_memory(context_assembler, memory_store):
    """Semantic Memory取得テスト"""
    # テストデータ作成
    await memory_store.save_memory(
        "Resonant Engineは呼吸のリズムで動作する",
        MemoryType.LONGTERM,
        source_type="decision"
    )
    await memory_store.save_memory(
        "呼吸モデルは6つのフェーズからなる",
        MemoryType.LONGTERM,
        source_type="thought"
    )
    await memory_store.save_memory(
        "全く関係ない記憶",
        MemoryType.LONGTERM
    )

    # Semantic Memory取得
    semantic_memory = await context_assembler._fetch_semantic_memory(
        query="呼吸のリズムについて教えて",
        limit=5
    )

    # 検証
    assert len(semantic_memory) > 0
    assert semantic_memory[0].similarity > 0.7
    assert "呼吸" in semantic_memory[0].content or "リズム" in semantic_memory[0].content
```

**合格基準**: テストがPASSし、関連記憶が正しく検索されること

---

### TC-04: メッセージリスト構築テスト

**目的**: Context Assemblerが各メモリ階層を正しい順序でメッセージリストに構築できることを確認

**前提条件**:
- Working Memory、Semantic Memory、Session Summaryのテストデータが用意されている

**テスト手順**:
1. memory_layersを準備
2. `_build_messages(memory_layers, user_message)` を呼び出し
3. メッセージリストの構造を検証

**期待結果**:
```python
messages = [
    {"role": "system", "content": "You are Kana...\n## セッション要約\n..."},
    {"role": "assistant", "content": "## 関連する過去の記憶\n1. ...\n2. ..."},
    {"role": "user", "content": "5分前のメッセージ"},
    {"role": "assistant", "content": "5分前の応答"},
    {"role": "user", "content": "新しいメッセージ"}
]
```

**テストコード**:
```python
def test_build_messages(context_assembler):
    """メッセージリスト構築テスト"""
    # モックデータ
    memory_layers = {
        "session_summary": "Previous discussion about Resonant Engine",
        "semantic": [
            MemoryResult(
                id=1,
                content="Resonant Engineは呼吸で動く",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9,
                created_at=datetime.now()
            )
        ],
        "working": [
            MessageResponse(
                id=uuid4(),
                user_id="test",
                content="こんにちは",
                message_type="user",
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            MessageResponse(
                id=uuid4(),
                user_id="test",
                content="こんにちは！",
                message_type="kana",
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
    }

    user_message = "Memory Storeについて教えて"

    # メッセージ構築
    messages = context_assembler._build_messages(memory_layers, user_message)

    # 検証
    assert len(messages) >= 5
    assert messages[0]["role"] == "system"
    assert "Previous discussion" in messages[0]["content"]
    assert messages[1]["role"] == "assistant"
    assert "関連する過去の記憶" in messages[1]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == user_message
```

**合格基準**: テストがPASSし、メッセージリストが正しい構造で構築されること

---

### TC-05: トークン数推定テスト

**目的**: Token Estimatorが日英混在テキストのトークン数を±10%精度で推定できることを確認

**前提条件**:
- Token Estimatorが初期化されている

**テスト手順**:
1. 既知のトークン数を持つテストケースを用意
2. Token Estimatorで推定
3. 実際のトークン数と比較（±10%以内）

**期待結果**:
- 日本語テキスト: 推定誤差 ±10%
- 英語テキスト: 推定誤差 ±10%
- 混在テキスト: 推定誤差 ±10%

**テストコード**:
```python
def test_token_estimation_accuracy():
    """トークン推定精度テスト"""
    estimator = TokenEstimator()

    # テストケース
    test_cases = [
        {
            "messages": [{"role": "user", "content": "こんにちは"}],
            "expected_range": (10, 30)
        },
        {
            "messages": [{"role": "user", "content": "Hello World"}],
            "expected_range": (10, 20)
        },
        {
            "messages": [
                {"role": "system", "content": "You are Kana"},
                {"role": "user", "content": "Resonant Engineは呼吸で動く"},
                {"role": "assistant", "content": "その通りです"}
            ],
            "expected_range": (50, 100)
        }
    ]

    for case in test_cases:
        tokens = estimator.estimate(case["messages"])
        min_expected, max_expected = case["expected_range"]
        assert min_expected <= tokens <= max_expected, \
            f"Expected {min_expected}-{max_expected}, got {tokens}"
```

**合格基準**: 全テストケースで±10%以内の精度

---

### TC-06: トークン圧縮テスト

**目的**: トークン上限を超えた場合に、優先順位に従ってコンテキストが圧縮されることを確認

**前提条件**:
- Context Assemblerのmax_tokens設定が小さい値（例: 1000）
- 大量のメモリ階層データが用意されている

**テスト手順**:
1. トークン上限を1000に設定
2. 大量のWorking/Semantic Memoryを用意
3. Context Assemblerでコンテキスト組み立て
4. 圧縮が正しく動作するか検証

**期待結果**:
- 圧縮の優先順位: Session Summary削除 → Semantic Memory削減 → Working Memory削減
- System PromptとUser Messageは削除されない
- 最終的にトークン数が上限以下になる

**テストコード**:
```python
@pytest.mark.asyncio
async def test_token_compression(context_assembler):
    """トークン圧縮テスト"""
    # 小さいトークン上限を設定
    context_assembler.config.max_tokens = 1000

    # 大量のデータ
    memory_layers = {
        "session_summary": "A" * 500,  # 大きなサマリー
        "semantic": [
            MemoryResult(id=i, content="Memory " * 100, ...)
            for i in range(10)
        ],
        "working": [
            MessageResponse(id=uuid4(), content="Working " * 50, ...)
            for _ in range(10)
        ]
    }

    user_message = "Test query"

    # 最初の構築（上限超過）
    messages = context_assembler._build_messages(memory_layers, user_message)
    tokens_before = context_assembler.token_estimator.estimate(messages)
    assert tokens_before > context_assembler._get_token_limit()

    # 圧縮
    compressed_messages, tokens_after = context_assembler._compress_context(
        messages, memory_layers, user_message
    )

    # 検証
    assert tokens_after <= context_assembler._get_token_limit()
    assert compressed_messages[0]["role"] == "system"
    assert compressed_messages[-1]["role"] == "user"
    assert compressed_messages[-1]["content"] == user_message
```

**合格基準**: テストがPASSし、適切にトークンが圧縮されること

---

### TC-08: コンテキスト組み立て統合テスト

**目的**: Context Assemblerの全体フローが正しく動作することを確認

**前提条件**:
- データベースにWorking Memory、Semantic Memoryが保存されている
- Context Assembler、Retrieval Orchestrator、Message Repositoryが初期化されている

**テスト手順**:
1. テストデータを準備（過去の会話、長期記憶）
2. `assemble_context(user_message, user_id)` を呼び出し
3. 返されたAssembledContextを検証

**期待結果**:
- `messages`リストが正しい構造で返される
- `metadata`に各メモリ階層の件数、トークン数が含まれる
- レイテンシが100ms以内

**テストコード**:
```python
@pytest.mark.asyncio
async def test_full_context_assembly(context_assembler, message_repo, memory_store):
    """コンテキスト組み立て統合テスト"""
    user_id = "test_user"

    # 過去の会話を保存
    await message_repo.create(MessageCreate(
        user_id=user_id,
        content="Resonant Engineとは？",
        message_type="user"
    ))
    await message_repo.create(MessageCreate(
        user_id=user_id,
        content="呼吸のリズムで動くAIシステムです",
        message_type="kana"
    ))

    # 長期記憶を保存
    await memory_store.save_memory(
        "Memory Storeはpgvectorを使う",
        MemoryType.LONGTERM
    )

    # コンテキスト組み立て
    assembled = await context_assembler.assemble_context(
        user_message="Memory Storeについて詳しく",
        user_id=user_id
    )

    # 検証
    assert len(assembled.messages) >= 3
    assert assembled.messages[0]["role"] == "system"
    assert assembled.messages[-1]["role"] == "user"
    assert assembled.messages[-1]["content"] == "Memory Storeについて詳しく"

    # メタデータ検証
    assert assembled.metadata.working_memory_count > 0
    assert assembled.metadata.total_tokens > 0
    assert assembled.metadata.assembly_latency_ms < 100  # 100ms以内
```

**合格基準**: テストがPASSし、レイテンシが100ms以内

---

### TC-09: KanaAIBridge統合テスト

**目的**: KanaAIBridgeがContext Assemblerを使ってClaude APIを呼び出せることを確認

**前提条件**:
- ANTHROPIC_API_KEY設定済み
- Context Assemblerが初期化されている

**テスト手順**:
1. Context Assembler付きでKanaAIBridgeを初期化
2. `process_intent()` を呼び出し
3. 返されたレスポンスを検証

**期待結果**:
- `status: "ok"`が返される
- `summary`にClaude APIの応答が含まれる
- `context_metadata`にWorking Memory件数などが含まれる

**テストコード**:
```python
@pytest.mark.asyncio
@pytest.mark.integration  # API呼び出しを含むため、統合テストとしてマーク
async def test_kana_bridge_with_context_assembler(kana_bridge_with_context):
    """KanaAIBridge + Context Assembler統合テスト"""
    # Intent作成
    intent = {
        "content": "Resonant Engineの記憶システムについて簡潔に説明してください",
        "user_id": "test_user"
    }

    # 処理
    response = await kana_bridge_with_context.process_intent(intent)

    # 検証
    assert response["status"] == "ok"
    assert "summary" in response
    assert len(response["summary"]) > 0

    # Context metadataの検証
    assert "context_metadata" in response
    assert "working_memory_count" in response["context_metadata"]
    assert "total_tokens" in response["context_metadata"]
```

**合格基準**: テストがPASSし、Claude APIからの応答が返されること

---

### TC-10: E2E: 過去の記憶参照テスト

**目的**: 実際の会話フローで、Claudeが過去の記憶を参照して応答することを確認

**前提条件**:
- ANTHROPIC_API_KEY設定済み
- データベースに過去の会話と長期記憶が保存されている

**テスト手順**:
1. 1回目の会話: "私の名前はHirokiです。Resonant Engineを開発しています。"
2. 2回目の会話: "私の名前を覚えていますか？"
3. Claudeの応答に"Hiroki"が含まれることを確認

**期待結果**:
- Claudeが過去の会話を参照して"Hiroki"と応答する
- Context Metadataに`working_memory_count > 0`が含まれる

**テストコード**:
```python
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_claude_remembers_past_conversation(
    kana_bridge_with_context,
    message_repo
):
    """E2E: Claudeが過去の記憶を参照するテスト"""
    user_id = "test_user"

    # 1回目の会話
    intent1 = {
        "content": "私の名前はHirokiです。Resonant Engineを開発しています。",
        "user_id": user_id
    }
    response1 = await kana_bridge_with_context.process_intent(intent1)
    assert response1["status"] == "ok"

    # 応答を保存（Working Memoryに追加）
    await message_repo.create(MessageCreate(
        user_id=user_id,
        content=intent1["content"],
        message_type="user"
    ))
    await message_repo.create(MessageCreate(
        user_id=user_id,
        content=response1["summary"],
        message_type="kana"
    ))

    # 2回目の会話（名前を聞く）
    intent2 = {
        "content": "私の名前を覚えていますか？",
        "user_id": user_id
    }
    response2 = await kana_bridge_with_context.process_intent(intent2)

    # 検証
    assert response2["status"] == "ok"
    assert "Hiroki" in response2["summary"] or "hiroki" in response2["summary"].lower()
    assert response2["context_metadata"]["working_memory_count"] > 0
```

**合格基準**: Claudeが過去の会話を参照して正しく応答すること

---

### TC-12: E2E: Context Assembler未設定時のfallbackテスト

**目的**: Context Assemblerが設定されていない場合、従来のシンプルな動作にfallbackすることを確認

**前提条件**:
- KanaAIBridgeがContext Assembler未設定で初期化されている

**テスト手順**:
1. Context Assembler未設定でKanaAIBridgeを初期化
2. `process_intent()` を呼び出し
3. 応答が返されることを確認

**期待結果**:
- `status: "ok"`が返される
- `context_metadata`が存在しない（または空）
- 従来通り動作する

**テストコード**:
```python
@pytest.mark.asyncio
async def test_kana_bridge_without_context_assembler():
    """Context Assembler未設定時のfallbackテスト"""
    # Context Assembler未設定でKanaAIBridge初期化
    bridge = KanaAIBridge()

    intent = {
        "content": "Hello, Kana!"
    }

    response = await bridge.process_intent(intent)

    # 検証
    assert response["status"] == "ok"
    assert "summary" in response
    assert "context_metadata" not in response  # Context Assembler未使用
```

**合格基準**: テストがPASSし、fallbackが正しく動作すること

---

### TC-13: 性能テスト: レイテンシ < 100ms

**目的**: Context組み立てが100ms以内に完了することを確認

**前提条件**:
- データベースに100件のWorking Memory、1000件のSemantic Memoryが保存されている

**テスト手順**:
1. 大量のデータを準備
2. `assemble_context()` を10回実行
3. p95レイテンシを計測

**期待結果**:
- p95レイテンシ < 100ms

**テストコード**:
```python
@pytest.mark.asyncio
@pytest.mark.performance
async def test_context_assembly_latency(context_assembler):
    """性能テスト: レイテンシ < 100ms"""
    import time

    latencies = []

    for i in range(10):
        start = time.time()
        await context_assembler.assemble_context(
            user_message=f"Test query {i}",
            user_id="perf_user"
        )
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    # p95計算
    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]

    assert p95 < 100, f"p95 latency {p95:.2f}ms exceeds 100ms"
```

**合格基準**: p95レイテンシが100ms以内

---

## ✅ 合格基準

### 必須テスト（全てPASS必須）
- [ ] TC-01: Working Memory取得テスト
- [ ] TC-02: Semantic Memory取得テスト
- [ ] TC-04: メッセージリスト構築テスト
- [ ] TC-05: トークン数推定テスト
- [ ] TC-06: トークン圧縮テスト
- [ ] TC-08: コンテキスト組み立て統合テスト
- [ ] TC-09: KanaAIBridge統合テスト
- [ ] TC-10: E2E: 過去の記憶参照テスト
- [ ] TC-12: E2E: fallbackテスト

### 推奨テスト（80%以上PASS）
- [ ] TC-03: Session Summary取得テスト
- [ ] TC-07: Context Validator検証テスト
- [ ] TC-11: E2E: トークン上限超過テスト
- [ ] TC-13: 性能テスト: レイテンシ
- [ ] TC-14: 性能テスト: 大量データ

### 全体合格基準
- **必須テスト**: 100% PASS
- **推奨テスト**: 80%以上 PASS
- **カバレッジ**: 80%以上
- **性能**: Context組み立てレイテンシ p95 < 100ms

---

## 📊 テスト実行コマンド

```bash
# 全テスト実行
pytest tests/context_assembler/ -v

# 単体テストのみ
pytest tests/context_assembler/ -v -m "not integration and not e2e and not performance"

# 統合テストのみ
pytest tests/context_assembler/ -v -m integration

# E2Eテストのみ
pytest tests/context_assembler/ -v -m e2e

# 性能テストのみ
pytest tests/context_assembler/ -v -m performance

# カバレッジ計測
pytest tests/context_assembler/ --cov=context_assembler --cov-report=html
```

---

## 📝 テスト報告書テンプレート

```markdown
# Context Assembler 受け入れテスト報告書

**実施日**: YYYY-MM-DD
**テスター**: [名前]

## テスト結果サマリー

| カテゴリ | 合格 | 不合格 | スキップ | 合格率 |
|---------|------|--------|---------|--------|
| 必須テスト | X/9 | X/9 | 0 | XX% |
| 推奨テスト | X/5 | X/5 | X | XX% |
| 合計 | X/14 | X/14 | X | XX% |

## 性能メトリクス

- Context組み立てレイテンシ p95: XX ms
- トークン推定精度: ±XX%
- カバレッジ: XX%

## 不合格テストの詳細

[不合格テストがあれば記載]

## 総合評価

[ ] 合格 - 本番デプロイ可
[ ] 条件付き合格 - 軽微な修正後デプロイ可
[ ] 不合格 - 再テスト必要

## コメント

[総合的な所感]
```

---

**作成日**: 2025-11-18
**作成者**: Kana (Claude Sonnet 4.5)
