"""Memory Lifecycle API"""

from fastapi import APIRouter, Depends, Query, HTTPException

from memory_lifecycle.capacity_manager import CapacityManager
from memory_lifecycle.compression_service import MemoryCompressionService
from app.dependencies import get_capacity_manager, get_compression_service

router = APIRouter(prefix="/api/v1/memory/lifecycle", tags=["memory-lifecycle"])


@router.get("/status")
async def get_memory_status(
    user_id: str = Query(...),
    capacity_manager: CapacityManager = Depends(get_capacity_manager)
):
    """メモリ使用状況を取得"""
    try:
        status = await capacity_manager.get_memory_status(user_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory status: {str(e)}")


@router.post("/compress")
async def compress_memories(
    user_id: str = Query(...),
    compression_service: MemoryCompressionService = Depends(get_compression_service)
):
    """メモリを圧縮"""
    try:
        result = await compression_service.compress_user_memories(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compress memories: {str(e)}")


@router.delete("/expired")
async def cleanup_expired_memories(
    capacity_manager: CapacityManager = Depends(get_capacity_manager)
):
    """期限切れメモリをクリーンアップ"""
    try:
        deleted_count = await capacity_manager.cleanup_expired_memories()
        return {"deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired memories: {str(e)}")
