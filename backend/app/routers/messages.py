"""
Messages Router with Memory Integration

メッセージ送信時に：
1. メッセージをDBに保存
2. メモリストアに保存（Semantic Memory）
3. AI応答を生成（Context Assembler経由で過去の記憶を参照）
4. AI応答もメモリに保存
"""

from uuid import UUID
from typing import Optional
import os
import asyncpg
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from app.models.message import MessageCreate, MessageUpdate, MessageResponse, MessageListResponse
from app.repositories.message_repo import MessageRepository
from app.database import db
import logging

router = APIRouter(prefix="/api/messages", tags=["messages"])
repo = MessageRepository()
logger = logging.getLogger(__name__)


async def get_memory_store_service(pool: asyncpg.Pool):
    """Memory Store Service を取得"""
    try:
        from memory_store.postgres_repository import PostgresMemoryRepository
        from memory_store.embedding import MockEmbeddingService, OpenAIEmbeddingService
        from memory_store.service import MemoryStoreService
        
        memory_repo = PostgresMemoryRepository(pool)
        
        # Try OpenAI embedding if API key available, otherwise use mock
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            embedding_service = OpenAIEmbeddingService(api_key=openai_key)
            logger.info("Using OpenAI embedding service")
        else:
            embedding_service = MockEmbeddingService()
            logger.info("Using Mock embedding service (OPENAI_API_KEY not set)")
        
        return MemoryStoreService(
            repository=memory_repo,
            embedding_service=embedding_service,
        )
    except Exception as e:
        logger.warning(f"Failed to create MemoryStoreService: {e}")
        return None


async def get_ai_bridge_with_context(pool: asyncpg.Pool):
    """Context Assembler 統合版のAI Bridge を取得"""
    provider = os.getenv("AI_PROVIDER", "claude").lower()
    
    try:
        from app.dependencies import create_ai_bridge_with_memory
        bridge = await create_ai_bridge_with_memory(pool=pool)
        logger.info("AI Bridge created with context memory")
        return bridge
    except Exception as e:
        logger.warning(f"Failed to create AI Bridge with memory: {e}, using simple bridge")
        # Fallback to simple bridge
        if provider in ("openai", "gpt", "yuno", "chatgpt"):
            from app.integrations.openai import YunoAIBridge
            return YunoAIBridge()
        else:
            from app.integrations.claude import KanaAIBridge
            return KanaAIBridge()


async def save_to_memory(
    pool: asyncpg.Pool,
    content: str, 
    user_id: str,
    source_type: str = "thought",
    memory_type: str = "working"
):
    """メッセージをMemory Storeに保存"""
    try:
        memory_service = await get_memory_store_service(pool)
        if memory_service is None:
            logger.warning("Memory service not available, skipping memory save")
            return
        
        from memory_store.models import MemoryType, SourceType
        
        memory_id = await memory_service.save_memory(
            content=content,
            memory_type=MemoryType(memory_type),
            source_type=SourceType(source_type) if source_type else None,
            metadata={
                "user_id": user_id,
                "source": "message",
            }
        )
        logger.info(f"Saved memory {memory_id} for user {user_id}")
        return memory_id
    except Exception as e:
        logger.error(f"Failed to save to memory: {e}")
        return None


async def generate_ai_response(user_message: str, user_id: str):
    """
    Generate AI response using configured AI provider with context memory.
    """
    pool = None
    try:
        # Get database pool
        pool = db.pool
        
        # Get AI bridge with context memory
        ai_bridge = await get_ai_bridge_with_context(pool)
        
        # Generate response with context
        result = await ai_bridge.process_intent({
            "content": user_message,
            "user_id": user_id,
        })
        
        if result.get("status") == "ok":
            ai_response = result.get("summary", "")
            model_name = result.get("model", "unknown")
            
            # Extract context metadata if available
            context_meta = result.get("context_metadata", {})
            
            # Determine message type based on model
            msg_type = "yuno" if "gpt" in model_name.lower() else "kana"
            
            # Save AI response to database
            await repo.create(MessageCreate(
                user_id=user_id,
                content=ai_response,
                message_type=msg_type,
                metadata={
                    "model": model_name,
                    "context": context_meta,
                }
            ))
            
            # Save AI response to memory
            await save_to_memory(
                pool=pool,
                content=f"AI Response: {ai_response[:500]}",
                user_id=user_id,
                source_type="thought",
                memory_type="working"
            )
            
            logger.info(f"AI response generated for user {user_id} using {model_name}")
            if context_meta:
                logger.info(f"Context used: working_memory={context_meta.get('working_memory_count', 0)}, semantic={context_meta.get('semantic_memory_count', 0)}")
        else:
            logger.error(f"AI response failed: {result.get('reason', 'unknown error')}")
            
    except Exception as e:
        logger.error(f"Failed to generate AI response: {e}", exc_info=True)


@router.get("", response_model=MessageListResponse)
async def list_messages(
    user_id: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of messages with optional filtering"""
    items, total = await repo.list(user_id, message_type, limit, offset)
    return MessageListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=MessageResponse)
async def get_message(id: UUID):
    """Get a specific message by ID"""
    msg = await repo.get_by_id(id)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
    return msg


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(data: MessageCreate, background_tasks: BackgroundTasks):
    """
    Create a new message and generate AI response.
    """
    # Save user message to database
    message = await repo.create(data)
    
    # If it's a user message, save to memory and generate AI response
    if data.message_type == "user":
        background_tasks.add_task(
            _save_user_message_to_memory,
            content=data.content,
            user_id=data.user_id
        )
        background_tasks.add_task(
            generate_ai_response,
            user_message=data.content,
            user_id=data.user_id
        )
    
    return message


async def _save_user_message_to_memory(content: str, user_id: str):
    """Background task to save user message to memory store"""
    try:
        pool = db.pool
        await save_to_memory(
            pool=pool,
            content=f"User said: {content}",
            user_id=user_id,
            source_type="intent",
            memory_type="working"
        )
    except Exception as e:
        logger.error(f"Failed to save user message to memory: {e}")


@router.put("/{id}", response_model=MessageResponse)
async def update_message(id: UUID, data: MessageUpdate):
    """Update an existing message"""
    msg = await repo.update(id, data)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
    return msg


@router.delete("/{id}", status_code=204)
async def delete_message(id: UUID):
    """Delete a message"""
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Message {id} not found")
