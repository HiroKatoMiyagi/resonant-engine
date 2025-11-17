"""Dashboard API endpoints for Bridge Lite Sprint 3."""

from __future__ import annotations

import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from bridge.dashboard import DashboardService, PostgresDashboardRepository
from bridge.realtime.websocket_manager import websocket_manager

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


async def get_dashboard_service() -> DashboardService:
    service = getattr(get_dashboard_service, "_instance", None)
    if service is None:
        database_url = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "DATABASE_URL_NOT_CONFIGURED"},
            )
        repository = PostgresDashboardRepository(database_url)
        service = DashboardService(repository, websocket_probe=websocket_manager.active_connection_count)
        setattr(get_dashboard_service, "_instance", service)
    return service


async def close_dashboard_service() -> None:
    service: DashboardService | None = getattr(get_dashboard_service, "_instance", None)
    if service is not None:
        await service.close()
        setattr(get_dashboard_service, "_instance", None)


@router.get("/overview")
async def dashboard_overview(service: DashboardService = Depends(get_dashboard_service)):
    return await service.get_overview()


@router.get("/timeline")
async def dashboard_timeline(
    start: datetime = Query(..., description="Start datetime (ISO 8601)"),
    end: datetime = Query(..., description="End datetime (ISO 8601)"),
    granularity: str = Query("hour", regex="^(minute|hour|day)$"),
    service: DashboardService = Depends(get_dashboard_service),
):
    if end <= start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end must be after start")
    return await service.get_timeline(start, end, granularity)


@router.get("/corrections")
async def dashboard_corrections(
    limit: int = Query(10, ge=1, le=100),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_corrections_summary(limit)
