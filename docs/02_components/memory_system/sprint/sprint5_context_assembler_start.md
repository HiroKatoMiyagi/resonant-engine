# Sprint 5: Context Assembler — 作業開始指示書

**Sprint**: Sprint 5 - Context Assembler
**期間**: 5日間（実装3日 + テスト・レビュー2日）
**担当**: Tsumu (実装具現層)
**監督**: Kana (外界翻訳層) / Yuno (思想中枢層)

---

## 🎯 Sprint目標

**Claude APIに過去の文脈を渡す「記憶統合層」を実装し、真の会話記憶機能を実現する**

### Before / After

#### Before (現状)
```python
# KanaAIBridge
messages = [
    {"role": "system", "content": "You are Kana..."},
    {"role": "user", "content": "新しいメッセージ"}  # 過去の記憶なし！
]
```

#### After (Sprint 5完了後)
```python
# Context Assembler統合後
messages = [
    {"role": "system", "content": "You are Kana...\n## セッション要約\n..."},
    {"role": "assistant", "content": "## 関連する過去の記憶\n1. ...\n2. ..."},
    {"role": "user", "content": "5分前のメッセージ"},
    {"role": "assistant", "content": "5分前の応答"},
    {"role": "user", "content": "新しいメッセージ"}  # 過去の文脈を含む！
]
```

---

## 📋 前提条件

### 必須の完了Sprint
- [x] Sprint 1: Memory Management (Session/Intent管理)
- [x] Sprint 2: Semantic Bridge (記憶抽出)
- [x] Sprint 3: Memory Store (pgvector)
- [x] Sprint 4: Retrieval Orchestrator (記憶想起)

### 環境確認

```bash
# 1. PostgreSQLが起動しているか
psql -U postgres -d resonant -c "SELECT 1;"

# 2. memoriesテーブルが存在するか
psql -U postgres -d resonant -c "\d memories"

# 3. messagesテーブルが存在するか
psql -U postgres -d resonant -c "\d messages"

# 4. Python環境
python --version  # Python 3.11+
pip list | grep anthropic
pip list | grep pydantic
```

### 依存モジュールの動作確認

```python
# retrieval/orchestrator.py が動作するか
from retrieval.orchestrator import create_orchestrator
print("Retrieval Orchestrator OK")

# backend/app/repositories/message_repo.py が動作するか
from backend.app.repositories.message_repo import MessageRepository
print("Message Repository OK")

# bridge/providers/ai/kana_ai_bridge.py が動作するか
from bridge.providers.ai.kana_ai_bridge import KanaAIBridge
print("KanaAIBridge OK")
```

---

## 📦 成果物リスト

### 1. 実装ファイル

| ファイル | 説明 | 必須 |
|---------|------|------|
| `context_assembler/__init__.py` | モジュール初期化 | ✅ |
| `context_assembler/models.py` | データモデル（Pydantic） | ✅ |
| `context_assembler/service.py` | Context Assemblerメインサービス | ✅ |
| `context_assembler/token_estimator.py` | トークン数推定 | ✅ |
| `context_assembler/config.py` | 設定管理 | ✅ |
| `bridge/providers/ai/kana_ai_bridge.py` | KanaAIBridge拡張（既存ファイル修正） | ✅ |

### 2. テストファイル

| ファイル | 説明 | 必須 |
|---------|------|------|
| `tests/context_assembler/test_service.py` | サービス単体テスト | ✅ |
| `tests/context_assembler/test_token_estimator.py` | トークン推定テスト | ✅ |
| `tests/context_assembler/test_integration.py` | 統合テスト | ✅ |
| `tests/context_assembler/test_e2e.py` | E2Eテスト | ✅ |

### 3. ドキュメント

| ファイル | 説明 | 必須 |
|---------|------|------|
| `context_assembler/README.md` | 使用方法・API仕様 | ✅ |
| `docs/.../sprint5_acceptance_test_spec.md` | 受け入れテスト仕様書 | ✅ |

---

## 🛠️ 実装ステップ

### Day 1: コアモデルとToken Estimator

#### Step 1.1: ディレクトリ作成

```bash
cd /home/user/resonant-engine
mkdir -p context_assembler
mkdir -p tests/context_assembler
touch context_assembler/__init__.py
touch tests/context_assembler/__init__.py
```

#### Step 1.2: データモデル実装

`context_assembler/models.py`:

```python
"""Context Assembler - Data Models"""

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryLayer(str, Enum):
    """メモリ階層の種類"""
    SYSTEM = "system"
    WORKING = "working"
    SEMANTIC = "semantic"
    SESSION_SUMMARY = "session_summary"
    USER_MESSAGE = "user_message"


class ContextConfig(BaseModel):
    """コンテキスト設定"""
    system_prompt: str = "You are Kana, the external translator for Resonant Engine."
    working_memory_limit: int = Field(default=10, ge=1, le=50)
    semantic_memory_limit: int = Field(default=5, ge=1, le=20)
    max_tokens: int = Field(default=100000, ge=1000)
    token_safety_margin: float = Field(default=0.8, ge=0.5, le=0.95)


class AssemblyOptions(BaseModel):
    """組み立てオプション"""
    working_memory_limit: Optional[int] = None
    semantic_memory_limit: Optional[int] = None
    include_semantic_memory: bool = True
    include_session_summary: bool = True


class ContextMetadata(BaseModel):
    """コンテキストメタデータ"""
    working_memory_count: int = Field(..., ge=0)
    semantic_memory_count: int = Field(..., ge=0)
    has_session_summary: bool
    total_tokens: int = Field(..., ge=0)
    token_limit: int = Field(..., ge=0)
    compression_applied: bool
    assembly_latency_ms: float = Field(..., ge=0)


class AssembledContext(BaseModel):
    """組み立て済みコンテキスト"""
    messages: List[Dict[str, str]]
    metadata: ContextMetadata

    class Config:
        from_attributes = True
```

**テスト作成**: `tests/context_assembler/test_models.py`

```python
import pytest
from context_assembler.models import ContextConfig, AssemblyOptions, ContextMetadata


def test_context_config_defaults():
    """デフォルト設定のテスト"""
    config = ContextConfig()
    assert config.working_memory_limit == 10
    assert config.semantic_memory_limit == 5
    assert config.max_tokens == 100000
    assert config.token_safety_margin == 0.8


def test_context_config_validation():
    """設定の妥当性検証"""
    # 不正な値
    with pytest.raises(ValueError):
        ContextConfig(working_memory_limit=0)  # ge=1

    with pytest.raises(ValueError):
        ContextConfig(token_safety_margin=1.1)  # le=0.95


def test_assembly_options():
    """組み立てオプションのテスト"""
    options = AssemblyOptions(
        include_semantic_memory=False
    )
    assert options.include_semantic_memory is False
    assert options.include_session_summary is True  # デフォルト
```

**実行**: `pytest tests/context_assembler/test_models.py -v`

#### Step 1.3: Token Estimator実装

`context_assembler/token_estimator.py`:

```python
"""Token Estimator - トークン数推定"""

from typing import Dict, List


class TokenEstimator:
    """
    トークン数推定クラス

    簡易推定ロジック:
    - 日本語1文字 ≈ 2トークン
    - 英語1文字 ≈ 0.5トークン
    - メッセージ構造オーバーヘッド: 10トークン/メッセージ
    """

    def estimate(self, messages: List[Dict[str, str]]) -> int:
        """
        メッセージリストのトークン数を推定

        Args:
            messages: Claude API形式のメッセージリスト

        Returns:
            推定トークン数
        """
        total = 0

        for msg in messages:
            content = msg.get("content", "")

            # 日本語文字数（UnicodeのCJK範囲）
            japanese_chars = sum(
                1 for c in content
                if 0x3000 <= ord(c) <= 0x9FFF or 0xFF00 <= ord(c) <= 0xFFEF
            )

            # その他の文字数
            other_chars = len(content) - japanese_chars

            # 推定
            total += japanese_chars * 2
            total += other_chars * 0.5

            # メッセージ構造オーバーヘッド
            total += 10

        return int(total)

    def estimate_string(self, text: str) -> int:
        """
        単一文字列のトークン数を推定

        Args:
            text: 推定対象のテキスト

        Returns:
            推定トークン数
        """
        japanese_chars = sum(
            1 for c in text
            if 0x3000 <= ord(c) <= 0x9FFF or 0xFF00 <= ord(c) <= 0xFFEF
        )
        other_chars = len(text) - japanese_chars

        return int(japanese_chars * 2 + other_chars * 0.5)
```

**テスト作成**: `tests/context_assembler/test_token_estimator.py`

```python
from context_assembler.token_estimator import TokenEstimator


def test_estimate_japanese_text():
    """日本語テキストのトークン推定"""
    estimator = TokenEstimator()

    messages = [
        {"role": "user", "content": "こんにちは"}  # 5文字
    ]

    tokens = estimator.estimate(messages)
    # 5文字 * 2 + オーバーヘッド10 = 20
    assert 15 <= tokens <= 25


def test_estimate_english_text():
    """英語テキストのトークン推定"""
    estimator = TokenEstimator()

    messages = [
        {"role": "user", "content": "Hello World"}  # 11文字
    ]

    tokens = estimator.estimate(messages)
    # 11文字 * 0.5 + オーバーヘッド10 = 15.5
    assert 10 <= tokens <= 20


def test_estimate_mixed_text():
    """日英混在テキストのトークン推定"""
    estimator = TokenEstimator()

    messages = [
        {"role": "user", "content": "Resonant Engineは呼吸のリズムです"}
    ]

    tokens = estimator.estimate(messages)
    assert tokens > 20  # それなりの量


def test_estimate_multiple_messages():
    """複数メッセージのトークン推定"""
    estimator = TokenEstimator()

    messages = [
        {"role": "system", "content": "You are Kana"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]

    tokens = estimator.estimate(messages)
    assert tokens > 30  # 各メッセージ + オーバーヘッド


def test_estimate_string():
    """文字列トークン推定"""
    estimator = TokenEstimator()

    tokens = estimator.estimate_string("こんにちは")
    assert 8 <= tokens <= 12  # 5文字 * 2 = 10
```

**実行**: `pytest tests/context_assembler/test_token_estimator.py -v`

---

### Day 2: Context Assembler Service実装

#### Step 2.1: Config実装

`context_assembler/config.py`:

```python
"""Context Assembler - Configuration"""

from context_assembler.models import ContextConfig


def get_default_config() -> ContextConfig:
    """デフォルト設定を取得"""
    return ContextConfig(
        system_prompt=(
            "You are Kana, the external translator for Resonant Engine.\n"
            "You help users understand and interact with the system by "
            "translating their intentions into structured actions."
        ),
        working_memory_limit=10,
        semantic_memory_limit=5,
        max_tokens=100000,  # Claude Sonnet 4.5: 200k (安全マージン考慮)
        token_safety_margin=0.8
    )
```

#### Step 2.2: Context Assembler Service実装

`context_assembler/service.py`:

```python
"""Context Assembler Service - コンテキスト組み立てサービス"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from memory_store.models import MemoryResult
from backend.app.models.message import MessageResponse
from backend.app.repositories.message_repo import MessageRepository
from bridge.memory.repositories import SessionRepository
from retrieval.orchestrator import RetrievalOrchestrator, RetrievalOptions

from .models import (
    AssembledContext,
    AssemblyOptions,
    ContextConfig,
    ContextMetadata,
)
from .token_estimator import TokenEstimator


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
        config: ContextConfig,
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
        options: Optional[AssemblyOptions] = None,
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
            options=options,
        )

        # 2. メッセージリストを構築
        messages = self._build_messages(memory_layers, user_message)

        # 3. トークン数を推定
        total_tokens = self.token_estimator.estimate(messages)

        # 4. トークン上限チェックと圧縮
        compression_applied = False
        if total_tokens > self._get_token_limit():
            messages, total_tokens = self._compress_context(
                messages, memory_layers, user_message
            )
            compression_applied = True

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
            compression_applied=compression_applied,
            assembly_latency_ms=assembly_time,
        )

        return AssembledContext(messages=messages, metadata=metadata)

    async def _fetch_memory_layers(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[UUID],
        options: AssemblyOptions,
    ) -> Dict[str, Any]:
        """メモリ階層を並行取得"""
        tasks = []

        # Working Memory（直近の会話）
        tasks.append(
            self._fetch_working_memory(
                user_id=user_id,
                limit=options.working_memory_limit
                or self.config.working_memory_limit,
            )
        )

        # Semantic Memory（関連記憶）
        if options.include_semantic_memory:
            tasks.append(
                self._fetch_semantic_memory(
                    query=user_message,
                    limit=options.semantic_memory_limit
                    or self.config.semantic_memory_limit,
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
            "session_summary": summary,
        }

    async def _fetch_working_memory(
        self, user_id: str, limit: int
    ) -> List[MessageResponse]:
        """Working Memory: 直近N件の会話"""
        messages, _ = await self.message_repo.list(user_id=user_id, limit=limit)
        # 時系列順（古い→新しい）に並び替え
        return list(reversed(messages))

    async def _fetch_semantic_memory(
        self, query: str, limit: int
    ) -> List[MemoryResult]:
        """Semantic Memory: 関連する記憶をベクトル検索"""
        response = await self.retrieval.retrieve(
            query=query, options=RetrievalOptions(limit=limit, log_metrics=False)
        )
        return response.results

    async def _fetch_session_summary(self, session_id: UUID) -> Optional[str]:
        """Session Summary: セッションの要約を取得"""
        session = await self.session_repo.get_by_id(session_id)
        if session and session.metadata:
            return session.metadata.get("summary")
        return None

    def _build_messages(
        self, memory_layers: Dict[str, Any], user_message: str
    ) -> List[Dict[str, str]]:
        """Claude APIに渡すメッセージリストを構築"""
        messages = []

        # 1. System Prompt
        system_content = self.config.system_prompt
        if memory_layers.get("session_summary"):
            system_content += (
                f"\n\n## セッション要約\n{memory_layers['session_summary']}"
            )

        messages.append({"role": "system", "content": system_content})

        # 2. Semantic Memory
        semantic_memories = memory_layers.get("semantic", [])
        if semantic_memories:
            memory_text = "## 関連する過去の記憶\n\n"
            for i, mem in enumerate(semantic_memories[:3], 1):
                memory_text += (
                    f"{i}. {mem.content} (関連度: {mem.similarity:.2f})\n"
                )

            messages.append({"role": "assistant", "content": memory_text})

        # 3. Working Memory
        working_messages = memory_layers.get("working", [])
        for msg in working_messages[-5:]:  # 直近5件
            role = self._map_message_type_to_role(msg.message_type)
            if role:  # systemは除外
                messages.append({"role": role, "content": msg.content})

        # 4. Current User Message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _map_message_type_to_role(self, message_type: str) -> Optional[str]:
        """MessageTypeをClaude API roleにマッピング"""
        mapping = {
            "user": "user",
            "kana": "assistant",
            "yuno": "assistant",
            "system": None,  # systemメッセージは除外
        }
        return mapping.get(message_type.lower())

    def _compress_context(
        self,
        messages: List[Dict[str, str]],
        memory_layers: Dict[str, Any],
        user_message: str,
    ) -> Tuple[List[Dict[str, str]], int]:
        """トークン上限を超えた場合にコンテキストを圧縮"""
        compressed_layers = memory_layers.copy()

        # Phase 1: Session Summary削除
        if compressed_layers.get("session_summary"):
            compressed_layers["session_summary"] = None
            messages = self._build_messages(compressed_layers, user_message)
            tokens = self.token_estimator.estimate(messages)
            if tokens <= self._get_token_limit():
                return messages, tokens

        # Phase 2: Semantic Memory削減
        semantic = compressed_layers.get("semantic", [])
        while len(semantic) > 1:
            semantic = semantic[:-1]  # 最後（類似度が低い）から削除
            compressed_layers["semantic"] = semantic
            messages = self._build_messages(compressed_layers, user_message)
            tokens = self.token_estimator.estimate(messages)
            if tokens <= self._get_token_limit():
                return messages, tokens

        # Phase 3: Working Memory削減
        working = compressed_layers.get("working", [])
        while len(working) > 2:  # 最低2件は残す
            working = working[1:]  # 最初（古い）から削除
            compressed_layers["working"] = working
            messages = self._build_messages(compressed_layers, user_message)
            tokens = self.token_estimator.estimate(messages)
            if tokens <= self._get_token_limit():
                return messages, tokens

        # それでも超過する場合は現状を返す
        return messages, tokens

    def _get_token_limit(self) -> int:
        """トークン上限を計算（安全マージン考慮）"""
        return int(self.config.max_tokens * self.config.token_safety_margin)

    def _validate_context(
        self, messages: List[Dict[str, str]], total_tokens: int
    ) -> None:
        """コンテキストの妥当性を検証"""
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

**テスト作成**: 後述（Day 3）

---

### Day 3: KanaAIBridge統合とテスト

#### Step 3.1: KanaAIBridge拡張

`bridge/providers/ai/kana_ai_bridge.py` を修正:

```python
"""Kana (Anthropic Claude) AI bridge implementation."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from anthropic import APIStatusError, AsyncAnthropic

from bridge.core.ai_bridge import AIBridge


class KanaAIBridge(AIBridge):
    """Wrap Anthropic Claude as the Kana intent processor."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        client: Optional[AsyncAnthropic] = None,
        # ↓ 追加
        context_assembler: Optional[Any] = None,  # ContextAssemblerService
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
            intent: Intent dict with fields:
                - content: str (user message) - required
                - user_id: str - optional, default "default"
                - session_id: UUID - optional

        Returns:
            Response dict with status, summary, and optional context_metadata
        """
        user_message = intent.get("content", "")
        user_id = intent.get("user_id", "default")
        session_id = intent.get("session_id")

        # Context Assemblerが設定されている場合、文脈を構築
        if self._context_assembler:
            try:
                assembled = await self._context_assembler.assemble_context(
                    user_message=user_message,
                    user_id=user_id,
                    session_id=session_id,
                )
                messages = assembled.messages
                context_metadata = assembled.metadata
            except Exception as e:
                # Context組み立てに失敗した場合はfallback
                import warnings
                warnings.warn(f"Context assembly failed: {e}, falling back to simple mode")
                messages = self._build_simple_messages(user_message)
                context_metadata = None
        else:
            # Context Assembler未設定の場合はシンプルなメッセージ
            messages = self._build_simple_messages(user_message)
            context_metadata = None

        # Claude API呼び出し
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.5,
                messages=messages,
            )
        except APIStatusError as exc:  # pragma: no cover
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
            result["context_metadata"] = {
                "working_memory_count": context_metadata.working_memory_count,
                "semantic_memory_count": context_metadata.semantic_memory_count,
                "has_session_summary": context_metadata.has_session_summary,
                "total_tokens": context_metadata.total_tokens,
                "compression_applied": context_metadata.compression_applied,
            }

        return result

    def _build_simple_messages(self, user_message: str) -> list:
        """Fallback: シンプルなメッセージリスト（従来の動作）"""
        return [
            {
                "role": "system",
                "content": "You are Kana, the external translator for Resonant Engine.",
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

    @staticmethod
    def _build_prompt(intent: Dict[str, Any]) -> str:
        """従来のprompt構築（互換性のため残す）"""
        intent_type = intent.get("type", "unknown")
        payload = intent.get("payload", {})
        return (
            "# Intent Summary\n"
            f"Type: {intent_type}\n"
            "Describe the key considerations, potential risks, and immediate next actions.\n\n"
            "## Payload\n"
            f"{payload}"
        )
```

#### Step 3.2: E2Eテスト作成

`tests/context_assembler/test_e2e.py`:

```python
"""E2E Test for Context Assembler + KanaAIBridge Integration"""

import pytest
from uuid import uuid4

# ... (詳細は受け入れテスト仕様書に記載)


@pytest.mark.asyncio
async def test_full_context_flow_with_kana_bridge(
    context_assembler,
    message_repo,
    memory_store,
    kana_bridge,
):
    """
    完全なフロー:
    1. 過去の会話を保存
    2. 長期記憶を保存
    3. Context Assemblerで統合
    4. KanaAIBridgeでClaude API呼び出し
    5. 応答に過去の文脈が反映されているか確認
    """
    # テスト実装...
    pass
```

---

### Day 4-5: テスト完成とレビュー

- 統合テスト実施
- 性能テスト実施
- ドキュメント作成
- レビュー対応

---

## ✅ 完了条件

### 必須条件
- [ ] 全単体テストがPASS（カバレッジ > 80%）
- [ ] 全統合テストがPASS
- [ ] E2EテストがPASS（実際の会話フローで動作確認）
- [ ] KanaAIBridge統合が完了し、Context Assembler未設定時もfallbackで動作
- [ ] ドキュメントが完成（README + API仕様）

### 品質条件
- [ ] Context組み立てレイテンシ < 100ms
- [ ] トークン推定精度 ±10% 以内
- [ ] コード品質チェック（ruff, mypy）がPASS

### レビュー条件
- [ ] 宏啓さんによるコードレビュー完了
- [ ] Yunoによる設計レビュー完了
- [ ] 受け入れテスト実施完了

---

## 📚 参考資料

- [Context Assembler仕様書](../architecture/sprint5_context_assembler_spec.md)
- [受け入れテスト仕様書](../test/sprint5_acceptance_test_spec.md)
- [Claude API Documentation](https://docs.anthropic.com/claude/reference/messages)

---

**作成日**: 2025-11-18
**作成者**: Kana (Claude Sonnet 4.5)
