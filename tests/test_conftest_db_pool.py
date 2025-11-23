"""Test to verify conftest.py db_pool fixture works"""
import pytest


@pytest.mark.asyncio
async def test_db_pool_fixture(db_pool):
    """Test that db_pool fixture from conftest.py works"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1
