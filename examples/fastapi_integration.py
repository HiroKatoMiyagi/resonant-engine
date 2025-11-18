"""
FastAPI統合例: Context Assemblerを使ったチャットエンドポイント

実運用環境での統合方法を示します。
"""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncpg

from context_assembler import ContextAssemblerService, get_default_config
from bridge.providers.ai.kana_ai_bridge import KanaAIBridge
from backend.app.repositories.message_repo import MessageRepository
from backend.app.models.message import MessageCreate, MessageType
from bridge.memory.repositories import SessionRepository
from retrieval.orchestrator import create_orchestrator
from memory_store.service import MemoryStoreService
from memory_store.repository import MemoryRepository
from memory_store.embedding import EmbeddingService

app = FastAPI(title="Resonant Engine Chat API")

# グローバルな依存オブジェクト（起動時に初期化）
db_pool: Optional[asyncpg.Pool] = None
context_assembler: Optional[ContextAssemblerService] = None


@app.on_event("startup")
async def startup():
    """アプリケーション起動時の初期化"""
    global db_pool, context_assembler

    # データベース接続プール作成
    db_pool = await asyncpg.create_pool(
        "postgresql://postgres:password@localhost:5432/resonant",
        min_size=5,
        max_size=20,
    )

    # コンポーネント初期化
    message_repo = MessageRepository()
    session_repo = SessionRepository()

    memory_repo = MemoryRepository(db_pool)
    embedding_service = EmbeddingService()
    memory_store = MemoryStoreService(memory_repo, embedding_service)
    retrieval = create_orchestrator(memory_store, db_pool, embedding_service)

    # Context Assembler初期化
    config = get_default_config()
    context_assembler = ContextAssemblerService(
        retrieval_orchestrator=retrieval,
        message_repository=message_repo,
        session_repository=session_repo,
        config=config,
    )

    print("✓ Context Assembler initialized")


@app.on_event("shutdown")
async def shutdown():
    """アプリケーション終了時のクリーンアップ"""
    if db_pool:
        await db_pool.close()


# === API Models ===


class ChatRequest(BaseModel):
    """チャットリクエスト"""

    message: str
    user_id: str = "default"
    save_to_history: bool = True


class ChatResponse(BaseModel):
    """チャットレスポンス"""

    response: str
    context_used: dict


# === API Endpoints ===


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    チャットエンドポイント

    ## 動作フロー
    1. Context Assemblerで過去の文脈を取得
       - Working Memory: 直近10件
       - Semantic Memory: 関連5件
    2. KanaAIBridgeでClaude APIを呼び出し
    3. 応答をMessage Repositoryに保存

    ## 例
    ```bash
    curl -X POST http://localhost:8000/api/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "私の名前を覚えていますか？", "user_id": "hiroki"}'
    ```
    """
    if not context_assembler:
        raise HTTPException(status_code=500, detail="Context Assembler not initialized")

    # 1. ユーザーメッセージをWorking Memoryに保存
    if request.save_to_history:
        message_repo = MessageRepository()
        await message_repo.create(
            MessageCreate(
                user_id=request.user_id,
                content=request.message,
                message_type=MessageType.USER,
            )
        )

    # 2. KanaAIBridge初期化（Context Assembler付き）
    bridge = KanaAIBridge(context_assembler=context_assembler)

    # 3. Intent作成
    intent = {
        "content": request.message,
        "user_id": request.user_id,
    }

    # 4. 処理（Context Assemblerが自動的に過去の文脈を取得）
    response = await bridge.process_intent(intent)

    if response["status"] != "ok":
        raise HTTPException(status_code=500, detail=response.get("reason", "Unknown error"))

    # 5. Claudeの応答をWorking Memoryに保存
    if request.save_to_history:
        await message_repo.create(
            MessageCreate(
                user_id=request.user_id,
                content=response["summary"],
                message_type=MessageType.KANA,
            )
        )

    # 6. レスポンス返却
    return ChatResponse(
        response=response["summary"],
        context_used=response.get("context_metadata", {}),
    )


@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """
    チャット履歴取得

    ## 例
    ```bash
    curl http://localhost:8000/api/chat/history/hiroki?limit=10
    ```
    """
    message_repo = MessageRepository()
    messages, total = await message_repo.list(user_id=user_id, limit=limit)

    return {
        "user_id": user_id,
        "total": total,
        "messages": [
            {
                "content": msg.content,
                "type": msg.message_type.value,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in reversed(messages)
        ],
    }


@app.get("/api/chat/context-preview/{user_id}")
async def preview_context(user_id: str, message: str):
    """
    コンテキストプレビュー（デバッグ用）

    実際にClaude APIを呼ばずに、Context Assemblerが
    どのようなメッセージを構築するかを確認できます。

    ## 例
    ```bash
    curl "http://localhost:8000/api/chat/context-preview/hiroki?message=私の名前は？"
    ```
    """
    if not context_assembler:
        raise HTTPException(status_code=500, detail="Context Assembler not initialized")

    # Context組み立て
    assembled = await context_assembler.assemble_context(
        user_message=message,
        user_id=user_id,
    )

    return {
        "messages": assembled.messages,
        "metadata": {
            "working_memory_count": assembled.metadata.working_memory_count,
            "semantic_memory_count": assembled.metadata.semantic_memory_count,
            "has_session_summary": assembled.metadata.has_session_summary,
            "total_tokens": assembled.metadata.total_tokens,
            "compression_applied": assembled.metadata.compression_applied,
            "assembly_latency_ms": assembled.metadata.assembly_latency_ms,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
