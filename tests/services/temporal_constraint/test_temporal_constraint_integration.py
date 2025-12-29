import pytest
from app.services.temporal_constraint.checker import TemporalConstraintChecker
from app.services.temporal_constraint.models import (
    ConstraintLevel, ModificationRequest, CheckResult
)

@pytest.mark.asyncio
async def test_register_verification(db_pool):
    from uuid import uuid4
    checker = TemporalConstraintChecker(db_pool)
    user_id = f"test_user_tc_{uuid4()}"
    file_path = "backend/verified_file.py"
    
    vid = await checker.register_verification(
        user_id, file_path, "unit_test", 10.0, ConstraintLevel.HIGH
    )
    assert vid is not None
    
    # Check DB
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT constraint_level FROM file_verifications
            WHERE id = $1
        """, vid)
        assert row['constraint_level'] == 'high'

@pytest.mark.asyncio
async def test_check_critical_constraint(db_pool):
    from uuid import uuid4
    checker = TemporalConstraintChecker(db_pool)
    user_id = f"test_user_tc_critical_{uuid4()}"
    file_path = "backend/critical.py"
    
    # Register as Critical
    await checker.register_verification(
        user_id, file_path, "manual_test", 100.0, ConstraintLevel.CRITICAL
    )
    
    # Check
    request = ModificationRequest(
        user_id=user_id,
        file_path=file_path,
        modification_type="edit",
        modification_reason="Fix bug",
        requested_by="user"
    )
    
    result = await checker.check_modification(request)
    
    assert result.constraint_level == ConstraintLevel.CRITICAL
    assert result.check_result == CheckResult.PENDING  # Requires approval
    assert "approval_required" in result.required_actions

@pytest.mark.asyncio
async def test_check_low_constraint(db_pool):
    from uuid import uuid4
    checker = TemporalConstraintChecker(db_pool)
    user_id = f"test_user_tc_low_{uuid4()}"
    file_path = "backend/low.py"
    
    # No registration = LOW
    
    request = ModificationRequest(
        user_id=user_id,
        file_path=file_path,
        modification_type="edit",
        modification_reason="Fix bug",
        requested_by="user"
    )
    
    result = await checker.check_modification(request)
    
    assert result.constraint_level == ConstraintLevel.LOW
    assert result.check_result == CheckResult.APPROVED
