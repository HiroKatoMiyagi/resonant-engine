"""
Root pytest configuration for all tests

Ensures project root is in Python path for all test modules.
"""

import sys
import os
from pathlib import Path
import pytest
import pytest_asyncio
import asyncpg

# Add project root to path at start of tests
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """
    Create a PostgreSQL connection pool for testing
    
    Uses environment variables or defaults for Docker development environment:
    - POSTGRES_HOST: postgres (Docker service name) or localhost
    - POSTGRES_PORT: 5432
    - POSTGRES_USER: resonant
    - POSTGRES_PASSWORD: password
    - POSTGRES_DB: postgres
    """
    # Use environment variables from Docker environment
    # Get actual values from environment
    db_host = os.getenv("POSTGRES_HOST", "postgres")
    db_port = int(os.getenv("POSTGRES_PORT", "5432"))
    db_user = os.getenv("POSTGRES_USER", "resonant")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB", "postgres")
    
    if not db_password:
        raise ValueError("POSTGRES_PASSWORD environment variable must be set")
    
    print(f"Connecting to PostgreSQL: {db_user}@{db_host}:{db_port}/{db_name}")
    print(f"Password length: {len(db_password)}")
    
    pool = await asyncpg.create_pool(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        min_size=1,
        max_size=10,
    )
    
    yield pool
    
    
    await pool.close()


@pytest_asyncio.fixture(scope="function")
async def test_client(db_pool):
    """
    Async test client for integration tests.
    Ensures DB is connected.
    """
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.database import db
    from app.dependencies import get_term_drift_detector, get_temporal_constraint_checker
    
    # Patch db.pool
    original_pool = db.pool
    db.pool = db_pool
    
    # Clear lru_cache to ensure new instances with correct pool are created
    get_term_drift_detector.cache_clear()
    get_temporal_constraint_checker.cache_clear()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    
    db.pool = original_pool
    # Clear again to cleanup
    get_term_drift_detector.cache_clear()
    get_temporal_constraint_checker.cache_clear()
