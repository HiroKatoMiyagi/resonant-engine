"""
Root pytest configuration for all tests

Ensures project root is in Python path for all test modules.
"""

import sys
import os
from pathlib import Path
import pytest
import asyncpg

# Add project root to path at start of tests
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
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
    pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "resonant"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        database=os.getenv("POSTGRES_DB", "postgres"),
        min_size=1,
        max_size=10,
    )
    
    yield pool
    
    await pool.close()
