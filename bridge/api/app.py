"""FastAPI application for Bridge Lite."""

from fastapi import FastAPI

from bridge.api.reeval import router as reeval_router

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
)

app.include_router(reeval_router)

__all__ = ["app"]
