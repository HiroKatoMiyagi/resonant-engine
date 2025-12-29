from contextlib import asynccontextmanager
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import db
from app.config import settings
from app.routers import (
    messages, 
    specifications, 
    intents, 
    notifications, 
    contradictions,
    re_evaluation,
    choice_points,
    memory_lifecycle,
    dashboard_analytics
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    logger.info("✅ Database connected")
    yield
    # Shutdown
    await db.disconnect()
    logger.info("Database disconnected")


app = FastAPI(
    title="Resonant Dashboard API",
    version="1.0.0",
    description="API for Resonant Engine Web Dashboard",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s "
        f"status={response.status_code}"
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(messages.router)
app.include_router(specifications.router)
app.include_router(intents.router)
app.include_router(notifications.router)
app.include_router(contradictions.router)

# 🆕 高度機能ルーター
app.include_router(re_evaluation.router)
app.include_router(choice_points.router)  # ✅ 有効化
app.include_router(memory_lifecycle.router)
app.include_router(dashboard_analytics.router)
logger.info("✅ Advanced feature routers registered")

# 🆕 Sprint 12 Routers
from app.routers import term_drift, temporal_constraint
app.include_router(term_drift.router)
app.include_router(temporal_constraint.router)
logger.info("✅ Term Drift & Temporal Constraint routers registered")

# WebSocket router (Sprint 15)
from app.routers import websocket
app.include_router(websocket.router)
logger.info("✅ WebSocket router registered")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Resonant Dashboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }
