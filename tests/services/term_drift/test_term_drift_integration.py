import pytest
from app.services.term_drift.detector import TermDriftDetector
from app.services.term_drift.models import DriftType, DriftStatus

@pytest.mark.asyncio
async def test_register_new_term_definition(db_pool):
    from uuid import uuid4
    detector = TermDriftDetector(db_pool)
    user_id = f"test_user_integration_{uuid4()}"
    
    term = {
        "term_name": "IntegrationTestTerm",
        "definition_text": "Integration Test Definition",
        "definition_source": "test_integration.py",
        "term_category": "technical"
    }
    
    def_id, drift = await detector.register_term_definition(user_id, term)
    
    assert def_id is not None
    assert drift is False
    
    # DB確認
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM term_definitions WHERE id = $1", def_id)
        assert row["term_name"] == "IntegrationTestTerm"
        assert row["is_current"] is True


@pytest.mark.asyncio
async def test_detect_drift_on_definition_change(db_pool):
    from uuid import uuid4
    detector = TermDriftDetector(db_pool)
    user_id = f"test_user_drift_{uuid4()}"
    
    # 1. 初期定義
    term1 = {
        "term_name": "DriftTerm",
        "definition_text": "Initial definition text.",
        "definition_source": "v1.md",
        "term_category": "custom"
    }
    id1, drift1 = await detector.register_term_definition(user_id, term1)
    assert drift1 is False
    
    # 2. 変更定義（大きく変更）
    term2 = {
        "term_name": "DriftTerm",
        "definition_text": "Completely different definition text for testing drift.",
        "definition_source": "v2.md",
        "term_category": "custom"
    }
    id2, drift2 = await detector.register_term_definition(user_id, term2)
    
    assert drift2 is True
    assert id1 != id2
    
    # 3. Drift確認
    drifts = await detector.get_pending_drifts(user_id)
    assert len(drifts) >= 1
    target_drift = next(d for d in drifts if d.term_name == "DriftTerm")
    assert target_drift.drift_type in [DriftType.SEMANTIC_SHIFT, DriftType.EXPANSION, DriftType.CONTRACTION]

@pytest.mark.asyncio
async def test_resolve_drift(db_pool):
    from uuid import uuid4
    detector = TermDriftDetector(db_pool)
    user_id = f"test_user_resolve_{uuid4()}"
    
    # Drift発生させる
    term1 = {"term_name": "ResolveTerm", "definition_text": "A", "term_category": "custom"}
    await detector.register_term_definition(user_id, term1)
    
    term2 = {"term_name": "ResolveTerm", "definition_text": "B", "term_category": "custom"}
    await detector.register_term_definition(user_id, term2)
    
    drifts = await detector.get_pending_drifts(user_id)
    drift_id = drifts[0].id
    
    # 解決
    success = await detector.resolve_drift(
        drift_id, "intentional_change", "Resolved via test", "tester"
    )
    assert success is True
    
    # 再確認（pendingから消えているか）
    drifts_after = await detector.get_pending_drifts(user_id)
    assert not any(d.id == drift_id for d in drifts_after)
