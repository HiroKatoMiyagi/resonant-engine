# Sprint 5: Context Assembler 詳細仕様書

## 0. CRITICAL: Assembly as Breathing Integration

**⚠️ IMPORTANT: 「コンテキスト組み立て = 記憶の呼吸を統合し、AI対話へ繋ぐ知的行為」**

Context Assembler は、Memory Store（保存）と Retrieval Orchestrator（想起）の成果を、Claude APIが理解できる「呼吸のリズムを持った対話文脈」へと変換する統合層です。過去の記憶と現在の対話を適切に配置することで、AIが「思い出しながら応答する」状態を実現します。

```yaml
context_assembler_philosophy:
    essence: "記憶の統合 = 過去と現在を呼吸のリズムで繋ぐ"
    purpose:
        - Working Memory（直近の会話）とSemantic Memory（関連記憶）を最適に配置
        - コンテキストウィンドウ制約内で最大限の記憶を活用
        - Claude APIが自然に「思い出す」ための構造を提供
    principles:
        - "記憶は階層的に想起される"
        - "文脈は時系列と関連性の両軸で構成される"
        - "トークン制約は呼吸の深さを決める"
```

### 呼吸サイクルとの関係

```
吸気 (Question) → Retrieval Orchestrator が記憶を想起
共鳴 (Resonance) → Context Assembler が記憶を統合
呼気 (Response) → Claude API が文脈を理解して応答
```

Memory StoreとRetrieval Orchestratorが「記憶の座標」を管理し、Context Assemblerが「対話への橋渡し」を行うことで、Resonant Engineの記憶システムは完結します。

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] Context Assemblerが Working Memory / Semantic Memory / Session Summary を統合してメッセージリストを生成
- [ ] KanaAIBridgeとの統合が完了し、過去の文脈を含むメッセージがClaude APIに送信される
- [ ] トークン数推定機能が実装され、コンテキストウィンドウ超過を防止
- [ ] E2Eテストが作成され、実際の会話フローで過去の記憶が参照されることを確認
- [ ] 15 件以上の単体/統合テストが作成され、CI で緑

#### Tier 2: 品質要件
- [ ] Context組み立てレイテンシ p95 < 100ms（Retrieval 150ms + Assembly 100ms = 合計250ms以内）
- [ ] トークン推定精度 ±10% 以内
- [ ] メモリ階層の優先順位制御が正しく動作（Working > Semantic > Session Summary）
- [ ] Observability: `context_assembly_latency_ms`, `context_token_count`, `memory_layer_usage`
- [ ] Kana レビュー向けに「統合ロジック」「トークン管理戦略」がまとめられている

## 1. 概要

### 1.1 目的
Retrieval Orchestrator（Sprint 4）とKanaAIBridge（AI対話層）の間に位置し、記憶を統合してClaude APIに渡す最適なコンテキストを構築する**コンテキスト組み立て層**を実装する。

### 1.2 スコープ
- Working Memory（直近会話）の取得と整形
- Semantic Memory（関連記憶）の取得と整形
- Session Summary（セッション要約）の取得
- メッセージリストの構築（Claude API形式）
- トークン数の推定とコンテキストウィンドウ管理
- KanaAIBridgeとの統合

### 1.3 Resonant Engineにおける位置づけ

```
呼吸フェーズ: 共鳴（Resonance） → 呼気（Response）

User Intent (質問)
    ↓
┌───────────────────────────┐
│ Retrieval Orchestrator    │  ← Sprint 4
│ - 記憶の想起              │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ Context Assembler         │  ← Sprint 5 (このレイヤー)
│ - Working Memory 取得     │
│ - Semantic Memory 統合    │
│ - Session Summary 追加    │
│ - メッセージリスト構築    │
│ - トークン数管理          │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ KanaAIBridge              │  ← 既存（拡張）
│ - Claude API 呼び出し     │
└───────────────────────────┘
    ↓
Claude API Response
```

### 1.4 成果物
- Context Assemblerサービス実装
- メモリ階層統合ロジック
- トークン推定機能
- KanaAIBridge拡張
- E2Eテストスイート

---

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────┐
│          Context Assembler                   │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Memory Layer Fetcher                │  │
│  │  - Working Memory (直近10件)         │  │
│  │  - Semantic Memory (関連5件)         │  │
│  │  - Session Summary                   │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Message Builder                     │  │
│  │  - System Prompt構築                 │  │
│  │  - Memory挿入                        │  │
│  │  - Working Memory挿入                │  │
│  │  - User Message挿入                  │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Token Manager                       │  │
│  │  - トークン数推定                     │  │
│  │  - コンテキスト圧縮                   │  │
│  │  - 優先順位制御                       │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Context Validator                   │  │
│  │  - メッセージ形式検証                 │  │
│  │  - トークン上限チェック               │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
          ↓
    KanaAIBridge → Claude API
```

### 2.2 メモリ階層の優先順位

| 階層 | 優先度 | 最大件数 | 削減時の動作 |
|------|--------|----------|-------------|
| System Prompt | 最高 | 1 | 削減不可 |
| User Message（現在） | 最高 | 1 | 削減不可 |
| Working Memory | 高 | 5-10件 | 古いものから削減 |
| Semantic Memory | 中 | 3-5件 | 類似度が低いものから削減 |
| Session Summary | 低 | 1 | 全削除 |

---

## 3. コンポーネント設計

### 3.1 Context Assembler Service

**役割**: コンテキスト組み立ての統括

#### 3.1.1 データモデル

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID

class ContextConfig(BaseModel):
    """コンテキスト設定"""
    system_prompt: str = "You are Kana, the external translator for Resonant Engine."
    working_memory_limit: int = Field(default=10, ge=1, le=50)
    semantic_memory_limit: int = Field(default=5, ge=1, le=20)
    max_tokens: int = Field(default=100000, ge=1000)  # Claude Sonnet 4.5: 200k
    token_safety_margin: float = Field(default=0.8, ge=0.5, le=0.95)  # 80%使用を上限

class MemoryLayer(str, Enum):
    """メモリ階層の種類"""
    SYSTEM = "system"
    WORKING = "working"
    SEMANTIC = "semantic"
    SESSION_SUMMARY = "session_summary"
    USER_MESSAGE = "user_message"

class AssembledContext(BaseModel):
    """組み立て済みコンテキスト"""
    messages: List[Dict[str, str]]
    metadata: "ContextMetadata"

class ContextMetadata(BaseModel):
    """コンテキストメタデータ"""
    working_memory_count: int = Field(..., ge=0)
    semantic_memory_count: int = Field(..., ge=0)
    has_session_summary: bool
    total_tokens: int = Field(..., ge=0)
    token_limit: int = Field(..., ge=0)
    compression_applied: bool
    assembly_latency_ms: float = Field(..., ge=0)
```

#### 3.1.2 メインAPI

```python
class ContextAssemblerService:
    """
    コンテキスト組み立てサービス

    Retrieval Orchestratorからの記憶と直近の会話履歴を統合し、
    Claude APIに渡す最適なコンテキストを構築します。
    """

    def __init__(
        self,
        retrieval_orchestrator: RetrievalOrchestrator,
        message_repository: MessageRepository,
        session_repository: SessionRepository,
        config: ContextConfig
    ):
        self.retrieval = retrieval_orchestrator
        self.message_repo = message_repository
        self.session_repo = session_repository
        self.config = config
        self.token_estimator = TokenEstimator()

    async def assemble_context(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[UUID] = None,
        options: Optional[AssemblyOptions] = None
    ) -> AssembledContext:
        """
        コンテキストを組み立てる

        Args:
            user_message: 現在のユーザーメッセージ
            user_id: ユーザーID
            session_id: セッションID（オプション）
            options: 組み立てオプション

        Returns:
            AssembledContext: メッセージリスト + メタデータ
        """
        start_time = time.time()
        options = options or AssemblyOptions()

        # 1. メモリ階層を取得
        memory_layers = await self._fetch_memory_layers(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            options=options
        )

        # 2. メッセージリストを構築
        messages = self._build_messages(memory_layers)

        # 3. トークン数を推定
        total_tokens = self.token_estimator.estimate(messages)

        # 4. トークン上限チェックと圧縮
        if total_tokens > self._get_token_limit():
            messages, total_tokens = await self._compress_context(
                messages, memory_layers
            )

        # 5. 検証
        self._validate_context(messages, total_tokens)

        assembly_time = (time.time() - start_time) * 1000

        # 6. メタデータ構築
        metadata = ContextMetadata(
            working_memory_count=len(memory_layers.get("working", [])),
            semantic_memory_count=len(memory_layers.get("semantic", [])),
            has_session_summary=memory_layers.get("session_summary") is not None,
            total_tokens=total_tokens,
            token_limit=self._get_token_limit(),
            compression_applied=total_tokens > self._get_token_limit(),
            assembly_latency_ms=assembly_time
        )

        return AssembledContext(messages=messages, metadata=metadata)
```

### 3.2 Memory Layer Fetcher

**役割**: 各メモリ階層からデータを取得

```python
async def _fetch_memory_layers(
    self,
    user_message: str,
    user_id: str,
    session_id: Optional[UUID],
    options: AssemblyOptions
) -> Dict[str, Any]:
    """
    メモリ階層を並行取得

    Returns:
        Dict with keys: "working", "semantic", "session_summary"
    """
    tasks = []

    # Working Memory（直近の会話）
    tasks.append(
        self._fetch_working_memory(
            user_id=user_id,
            limit=options.working_memory_limit or self.config.working_memory_limit
        )
    )

    # Semantic Memory（関連記憶）
    if options.include_semantic_memory:
        tasks.append(
            self._fetch_semantic_memory(
                query=user_message,
                limit=options.semantic_memory_limit or self.config.semantic_memory_limit
            )
        )
    else:
        tasks.append(asyncio.sleep(0, result=[]))

    # Session Summary
    if session_id and options.include_session_summary:
        tasks.append(self._fetch_session_summary(session_id))
    else:
        tasks.append(asyncio.sleep(0, result=None))

    # 並行実行
    working, semantic, summary = await asyncio.gather(*tasks)

    return {
        "working": working,
        "semantic": semantic,
        "session_summary": summary
    }

async def _fetch_working_memory(
    self,
    user_id: str,
    limit: int
) -> List[MessageResponse]:
    """Working Memory: 直近N件の会話"""
    messages, _ = await self.message_repo.list(
        user_id=user_id,
        limit=limit
    )
    # 時系列順（古い→新しい）に並び替え
    return list(reversed(messages))

async def _fetch_semantic_memory(
    self,
    query: str,
    limit: int
) -> List[MemoryResult]:
    """Semantic Memory: 関連する記憶をベクトル検索"""
    response = await self.retrieval.retrieve(
        query=query,
        options=RetrievalOptions(
            limit=limit,
            log_metrics=False
        )
    )
    return response.results

async def _fetch_session_summary(
    self,
    session_id: UUID
) -> Optional[str]:
    """Session Summary: セッションの要約を取得"""
    session = await self.session_repo.get_by_id(session_id)
    if session and session.metadata:
        return session.metadata.get("summary")
    return None
```

### 3.3 Message Builder

**役割**: Claude API形式のメッセージリストを構築

```python
def _build_messages(
    self,
    memory_layers: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Claude APIに渡すメッセージリストを構築

    構造:
    1. System Prompt (+ Session Summary)
    2. Semantic Memory (重要な過去の記憶)
    3. Working Memory (直近の会話)
    4. User Message (現在)
    """
    messages = []

    # 1. System Prompt
    system_content = self.config.system_prompt
    if memory_layers.get("session_summary"):
        system_content += f"\n\n## セッション要約\n{memory_layers['session_summary']}"

    messages.append({
        "role": "system",
        "content": system_content
    })

    # 2. Semantic Memory
    semantic_memories = memory_layers.get("semantic", [])
    if semantic_memories:
        memory_text = "## 関連する過去の記憶\n\n"
        for i, mem in enumerate(semantic_memories[:3], 1):
            memory_text += f"{i}. {mem.content} (関連度: {mem.similarity:.2f})\n"

        messages.append({
            "role": "assistant",
            "content": memory_text
        })

    # 3. Working Memory
    working_messages = memory_layers.get("working", [])
    for msg in working_messages[-5:]:  # 直近5件
        role = self._map_message_type_to_role(msg.message_type)
        if role:  # systemは除外
            messages.append({
                "role": role,
                "content": msg.content
            })

    return messages

def _map_message_type_to_role(self, message_type: str) -> Optional[str]:
    """MessageTypeをClaude API roleにマッピング"""
    mapping = {
        "user": "user",
        "kana": "assistant",
        "yuno": "assistant",
        "system": None  # systemメッセージは除外
    }
    return mapping.get(message_type.lower())
```

### 3.4 Token Manager

**役割**: トークン数の推定と管理

```python
class TokenEstimator:
    """トークン数推定"""

    def estimate(self, messages: List[Dict[str, str]]) -> int:
        """
        メッセージリストのトークン数を推定

        簡易推定: 日本語1文字 ≈ 2トークン、英語1単語 ≈ 1.3トークン
        """
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            # 日本語文字数
            japanese_chars = sum(1 for c in content if ord(c) > 0x3000)
            # その他の文字数
            other_chars = len(content) - japanese_chars

            # 推定
            total += japanese_chars * 2
            total += other_chars * 0.5

        # メッセージ構造オーバーヘッド（role, JSON構造など）
        total += len(messages) * 10

        return int(total)

async def _compress_context(
    self,
    messages: List[Dict[str, str]],
    memory_layers: Dict[str, Any]
) -> Tuple[List[Dict[str, str]], int]:
    """
    トークン上限を超えた場合にコンテキストを圧縮

    優先順位:
    1. Session Summary削除
    2. Semantic Memory削減（類似度が低いものから）
    3. Working Memory削減（古いものから）
    """
    compressed_layers = memory_layers.copy()

    # Phase 1: Session Summary削除
    if compressed_layers.get("session_summary"):
        compressed_layers["session_summary"] = None
        messages = self._build_messages(compressed_layers)
        tokens = self.token_estimator.estimate(messages)
        if tokens <= self._get_token_limit():
            return messages, tokens

    # Phase 2: Semantic Memory削減
    semantic = compressed_layers.get("semantic", [])
    while len(semantic) > 1:
        semantic = semantic[:-1]  # 最後（類似度が低い）から削除
        compressed_layers["semantic"] = semantic
        messages = self._build_messages(compressed_layers)
        tokens = self.token_estimator.estimate(messages)
        if tokens <= self._get_token_limit():
            return messages, tokens

    # Phase 3: Working Memory削減
    working = compressed_layers.get("working", [])
    while len(working) > 2:  # 最低2件は残す
        working = working[1:]  # 最初（古い）から削除
        compressed_layers["working"] = working
        messages = self._build_messages(compressed_layers)
        tokens = self.token_estimator.estimate(messages)
        if tokens <= self._get_token_limit():
            return messages, tokens

    # それでも超過する場合は警告
    return messages, tokens

def _get_token_limit(self) -> int:
    """トークン上限を計算（安全マージン考慮）"""
    return int(self.config.max_tokens * self.config.token_safety_margin)
```

### 3.5 Context Validator

**役割**: コンテキストの妥当性を検証

```python
def _validate_context(
    self,
    messages: List[Dict[str, str]],
    total_tokens: int
) -> None:
    """
    コンテキストの妥当性を検証

    Raises:
        ValueError: 検証エラー時
    """
    # 1. メッセージが空でないか
    if not messages:
        raise ValueError("Messages cannot be empty")

    # 2. 最初のメッセージがsystemか
    if messages[0].get("role") != "system":
        raise ValueError("First message must be system prompt")

    # 3. 最後のメッセージがuserか
    if messages[-1].get("role") != "user":
        raise ValueError("Last message must be user message")

    # 4. role/contentが存在するか
    for i, msg in enumerate(messages):
        if "role" not in msg or "content" not in msg:
            raise ValueError(f"Message {i} missing role or content")
        if not msg["content"]:
            raise ValueError(f"Message {i} has empty content")

    # 5. トークン数が上限を超えていないか（警告のみ）
    if total_tokens > self.config.max_tokens:
        import warnings
        warnings.warn(
            f"Total tokens {total_tokens} exceeds max {self.config.max_tokens}"
        )
```

---

## 4. KanaAIBridge統合

### 4.1 KanaAIBridge拡張

```python
class KanaAIBridge(AIBridge):
    """Kana (Anthropic Claude) AI bridge implementation with context memory."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        client: Optional[AsyncAnthropic] = None,
        # ↓ 追加
        context_assembler: Optional[ContextAssemblerService] = None,
    ) -> None:
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key and client is None:
            raise ValueError("ANTHROPIC_API_KEY must be configured for KanaAIBridge")
        self._model = model
        self._client = client or AsyncAnthropic(api_key=key)
        self._context_assembler = context_assembler

    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process intent with context memory support

        Args:
            intent: Intent dict with required fields:
                - content: str (user message)
                - user_id: str (optional, default "default")
                - session_id: UUID (optional)

        Returns:
            Response dict with status, summary, and metadata
        """
        user_message = intent.get("content", "")
        user_id = intent.get("user_id", "default")
        session_id = intent.get("session_id")

        # Context Assemblerが設定されている場合、文脈を構築
        if self._context_assembler:
            assembled = await self._context_assembler.assemble_context(
                user_message=user_message,
                user_id=user_id,
                session_id=session_id
            )
            messages = assembled.messages
            context_metadata = assembled.metadata
        else:
            # Fallback: 従来のシンプルな方式
            prompt = self._build_prompt(intent)
            messages = [
                {
                    "role": "system",
                    "content": "You are Kana, the external translator for Resonant Engine.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
            context_metadata = None

        # Claude API呼び出し
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.5,
                messages=messages,
            )
        except APIStatusError as exc:
            return {
                "status": "error",
                "reason": str(exc),
            }

        message = response.content[0]
        summary = getattr(message, "text", None) or str(message)

        result = {
            "status": "ok",
            "model": self._model,
            "summary": summary,
        }

        # Context metadata追加
        if context_metadata:
            result["context_metadata"] = context_metadata.dict()

        return result
```

---

## 5. テスト戦略

### 5.1 単体テスト

```python
# Token Estimator
def test_estimate_tokens_japanese():
    estimator = TokenEstimator()
    messages = [{"role": "user", "content": "こんにちは"}]
    tokens = estimator.estimate(messages)
    assert 10 <= tokens <= 30  # 5文字 * 2 + オーバーヘッド

# Message Builder
def test_build_messages_with_all_layers():
    builder = MessageBuilder(config)
    memory_layers = {
        "working": [msg1, msg2],
        "semantic": [mem1, mem2],
        "session_summary": "Previous discussion..."
    }
    messages = builder._build_messages(memory_layers)
    assert messages[0]["role"] == "system"
    assert "Previous discussion" in messages[0]["content"]
    assert any("関連する過去の記憶" in m["content"] for m in messages)

# Context Validator
def test_validate_context_missing_system_prompt():
    validator = ContextValidator()
    messages = [{"role": "user", "content": "test"}]
    with pytest.raises(ValueError, match="First message must be system"):
        validator._validate_context(messages, 100)
```

### 5.2 統合テスト

```python
@pytest.mark.asyncio
async def test_full_context_assembly_flow():
    """E2Eテスト: 実際のデータでコンテキスト組み立て"""
    # データ準備
    user_id = "test_user"

    # 過去の会話を保存
    await message_repo.create(MessageCreate(
        user_id=user_id,
        content="Resonant Engineとは何ですか？",
        message_type="user"
    ))
    await message_repo.create(MessageCreate(
        user_id=user_id,
        content="Resonant Engineは呼吸のリズムで動作するAIシステムです。",
        message_type="kana"
    ))

    # 長期記憶を保存
    await memory_store.save_memory(
        "Memory Storeはpgvectorを使った記憶システム",
        MemoryType.LONGTERM,
        source_type="decision"
    )

    # コンテキスト組み立て
    assembled = await context_assembler.assemble_context(
        user_message="Memory Storeについて詳しく教えて",
        user_id=user_id
    )

    # 検証
    assert len(assembled.messages) >= 3  # system, memory, user
    assert assembled.messages[0]["role"] == "system"
    assert assembled.messages[-1]["role"] == "user"
    assert assembled.messages[-1]["content"] == "Memory Storeについて詳しく教えて"

    # Working Memoryが含まれているか
    content_str = " ".join(m["content"] for m in assembled.messages)
    assert "Resonant Engine" in content_str

    # Semantic Memoryが含まれているか
    assert "pgvector" in content_str or "記憶システム" in content_str

    # メタデータ
    assert assembled.metadata.working_memory_count > 0
    assert assembled.metadata.total_tokens > 0
```

### 5.3 性能テスト

```python
async def test_context_assembly_performance():
    """コンテキスト組み立ての性能テスト"""
    # 大量のWorking Memory（100件）
    for i in range(100):
        await message_repo.create(MessageCreate(
            user_id="perf_user",
            content=f"Message {i}",
            message_type="user"
        ))

    # 大量のSemantic Memory（1000件）
    for i in range(1000):
        await memory_store.save_memory(
            f"Long-term memory {i}",
            MemoryType.LONGTERM
        )

    # 性能計測
    start = time.time()
    assembled = await context_assembler.assemble_context(
        user_message="Test query",
        user_id="perf_user"
    )
    elapsed = time.time() - start

    # 100ms以内（Retrieval 150msとは別）
    assert elapsed < 0.1
    assert assembled.metadata.assembly_latency_ms < 100
```

---

## 6. Done Definition

### 6.1 機能要件

- [ ] Context Assemblerがメモリ階層を並行取得できる
- [ ] Message Builderが正しい順序でメッセージリストを構築できる
- [ ] Token Estimatorがトークン数を推定できる（±10%精度）
- [ ] Token Managerがトークン超過時にコンテキストを圧縮できる
- [ ] Context Validatorが妥当性を検証できる
- [ ] KanaAIBridgeとの統合が完了し、過去の文脈がClaude APIに送信される

### 6.2 品質要件

- [ ] 単体テストカバレッジ > 80%
- [ ] 統合テストが全てPASS
- [ ] E2Eテストで実際の会話フローが動作
- [ ] Context組み立てレイテンシ < 100ms
- [ ] トークン推定精度 ±10% 以内

### 6.3 ドキュメント要件

- [ ] API仕様書が完成
- [ ] トークン管理戦略がドキュメント化されている
- [ ] KanaAIBridge統合ガイドが作成されている

### 6.4 レビュー要件

- [ ] 宏啓さんによるコードレビュー完了
- [ ] Yunoによる統合品質評価完了
- [ ] 実際の会話データでの動作確認完了

---

## 7. 今後の拡張

### 7.1 Sprint 6以降での拡張候補

- [ ] **Session Summary自動生成**: N件ごとにClaude APIで要約を生成
- [ ] **動的トークン配分**: 重要度に応じてメモリ階層のトークン配分を調整
- [ ] **マルチモーダル対応**: 画像・ファイルコンテキストの統合
- [ ] **コンテキストキャッシング**: Claude APIのPrompt Caching活用
- [ ] **ユーザー別カスタマイズ**: ユーザーごとの記憶戦略設定

### 7.2 制約事項

- **トークン推定精度**: 簡易推定のため、実際のトークン数と±10%の誤差
- **Session Summary**: 現状は既存の要約のみ使用（自動生成は未実装）
- **並行処理**: asyncio.gatherで並行化しているが、DB接続プールの上限に注意

---

## 8. Risks & Mitigation

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| トークン推定が不正確で上限超過 | Medium | High | 安全マージン80%設定 + 実トークン数との差分をログ収集し、推定式を週次で調整 |
| Context組み立てが遅延してUX悪化 | Low | Medium | 並行fetch + メトリクス監視 + p95 > 100msでアラート |
| Working Memoryが多すぎてノイズ化 | Medium | Medium | 優先順位制御 + ユーザーフィードバックで最適件数を調整（A/Bテスト） |
| KanaAIBridge統合でレグレッション | Low | High | Context Assembler未設定時は従来動作にfallback + E2Eテスト必須 |

## 9. Rollout Plan

### Phase 0: Preparation (Day 0)
- Retrieval Orchestrator / Memory Store の動作確認
- Message Repository / Session Repository の接続確認
- 依存ライブラリの確認

### Phase 1: Core Implementation (Day 1-2)
- Context Assembler Service / Memory Layer Fetcher 実装
- Message Builder / Token Estimator 実装
- 単体テスト作成（10件以上）

### Phase 2: Integration (Day 3)
- KanaAIBridge拡張
- E2Eテスト作成
- 統合テスト実施

### Phase 3: Optimization & QA (Day 4)
- Token Manager / Context Validator 実装
- 性能テスト実施
- ドキュメント作成

### Phase 4: Production Readiness (Day 5)
- レビュー対応
- 受け入れテスト実施
- デプロイ準備

## 10. 参考資料

- [Retrieval Orchestrator仕様書（Sprint 4）](./sprint4_retrieval_orchestrator_spec.md)
- [Memory Store仕様書（Sprint 3）](./sprint3_memory_store_spec.md)
- [Claude API Documentation](https://docs.anthropic.com/claude/reference/messages)
- [Token Counting Best Practices](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them)

---

**作成日**: 2025-11-18
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
