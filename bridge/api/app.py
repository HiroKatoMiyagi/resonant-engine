"""FastAPI application for Bridge Lite."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bridge.api import dashboard as dashboard_module
from bridge.api import reeval
from bridge.api import sse as sse_module
from bridge.api import websocket as websocket_module
from bridge.realtime import get_event_distributor, shutdown_event_distributor

logger = logging.getLogger(__name__)

@asynccontextmanager
async def _lifespan(_: FastAPI):
  skip_realtime = os.getenv("BRIDGE_SKIP_REALTIME_STARTUP") == "1"
  realtime_started = False

  if skip_realtime:
    logger.warning("Skipping real-time startup due to BRIDGE_SKIP_REALTIME_STARTUP=1")
  else:
    try:
      await get_event_distributor()
      await websocket_module.ensure_websocket_subscription()
      realtime_started = True
    except Exception as exc:  # pragma: no cover - initialization failure should be logged
      logger.exception("Failed to bootstrap EventDistributor: %s", exc)
      raise

  try:
    yield
  finally:
    if realtime_started:
      await shutdown_event_distributor()
    await dashboard_module.close_dashboard_service()


app = FastAPI(
    title="Bridge Lite API",
    version="2.1.0",
    description="""
    Bridge Lite API with Re-evaluation and Feedback integration.
    
    ## Features
    
    - Intent management (CRUD operations)
    - Pipeline execution with BridgeSet
    - Re-evaluation API for Intent correction
    - Feedback loop with Yuno integration
    - Audit logging and correction history tracking
    
    ## Re-evaluation Flow
    
    1. Intent is processed through pipeline (INPUT → AI → FEEDBACK → OUTPUT)
    2. FeedbackBridge (Yuno/Mock) analyzes Intent
    3. If correction needed, Re-eval API is called automatically
    4. Intent payload is updated with diff (e.g., `feedback.yuno.*`)
    5. `correction_history` is maintained for audit trail
    6. Intent status transitions to CORRECTED
    
    ## Feedback Payload Structure
    
    When YunoFeedbackBridge applies corrections, the following fields are added to `payload.feedback.yuno`:
    
    - `reason`: High-level reason for correction (str)
    - `recommended_changes`: List of specific change recommendations (list[dict])
    - `latest`: Full evaluation result from Yuno (dict)
      - `judgment`: "approved" | "requires_changes" | "rejected"
      - `evaluation_score`: Overall score (0.0-1.0)
      - `criteria`: Detailed criteria scores (dict)
      - `suggestions`: List of improvement suggestions (list[str])
      - `issues`: List of identified issues (list[str])
    
    ## Idempotency
    
    Re-evaluation requests are idempotent based on SHA256(intent_id + diff).
    Same correction applied twice returns `already_applied: true`
    without modifying Intent or `correction_history`.
    
    ## API Endpoints
    
    - `POST /api/v1/intent/reeval`: Re-evaluate and correct an Intent
    - See full documentation in `/docs` (Swagger UI)
    """,
    docs_url="/docs",
  redoc_url="/redoc",
  lifespan=_lifespan,
)

app.include_router(reeval.router)
app.include_router(websocket_module.router)
app.include_router(sse_module.router)
app.include_router(dashboard_module.router)

__all__ = ["app"]
