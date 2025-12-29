"""Dashboard Analytics API"""

from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime, timedelta

from app.services.dashboard.service import DashboardService
from app.dependencies import get_dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard-analytics"])


@router.get("/overview")
async def system_overview(
    service: DashboardService = Depends(get_dashboard_service)
):
    """システム概要を取得"""
    try:
        overview = await service.get_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system overview: {str(e)}")


@router.get("/timeline")
async def timeline(
    granularity: str = Query("hour", pattern="^(minute|hour|day)$"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """タイムラインを取得"""
    try:
        # デフォルトで過去24時間のタイムラインを取得
        end = datetime.now()
        start = end - timedelta(hours=24)
        timeline_data = await service.get_timeline(start, end, granularity)
        return timeline_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@router.get("/corrections")
async def corrections_history(
    limit: int = Query(50, ge=1, le=200),
    service: DashboardService = Depends(get_dashboard_service)
):
    """修正履歴を取得"""
    try:
        corrections = await service.get_corrections_summary(limit)
        return {"corrections": corrections, "count": len(corrections)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get corrections history: {str(e)}")
