"""
ST-CONTRA: 矛盾検出テスト

Sprint 11で実装された矛盾検出機能を検証します。
"""
import pytest
import uuid
import json
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_contradiction_detector_import():
    """ST-CONTRA-001: ContradictionDetectorのインポート確認"""
    from app.services.contradiction.detector import ContradictionDetector
    assert ContradictionDetector is not None


@pytest.mark.asyncio
async def test_contradiction_models():
    """ST-CONTRA-002: 矛盾検出モデルの確認"""
    from app.services.contradiction.models import (
        Contradiction,
        IntentRelation
    )
    assert Contradiction is not None


@pytest.mark.asyncio
async def test_contradictions_table_structure(db_pool):
    """ST-CONTRA-003: contradictionsテーブル構造確認"""
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'contradictions')")
        if not exists:
            pytest.skip("Contradictions table missing")

        columns = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'contradictions'")
        column_names = [c['column_name'] for c in columns]
        
        required_columns = ['contradiction_type', 'confidence_score', 'resolution_status']
        for col in required_columns:
            assert col in column_names, f"必須カラム '{col}' が存在しません"


@pytest.mark.asyncio
async def test_intent_relations_table_structure(db_pool):
    """ST-CONTRA-004: intent_relationsテーブル構造確認"""
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'intent_relations')")
        if not exists:
            pytest.skip("intent_relations table missing")
        
        columns = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'intent_relations'")
        column_names = [c['column_name'] for c in columns]
        assert 'source_intent_id' in column_names


@pytest.mark.asyncio
async def test_contradiction_crud(db_pool):
    """ST-CONTRA-005: 矛盾レコードのCRUD操作"""
    async with db_pool.acquire() as conn:
        intent_id_1 = uuid.uuid4()
        intent_id_2 = uuid.uuid4()
        session_id = uuid.uuid4()
        user_id = 'test_user'

        # Create Session
        await conn.execute("""
            INSERT INTO sessions (id, user_id, status, started_at, last_active)
            VALUES ($1, $2, $3, NOW(), NOW())
        """, session_id, user_id, 'active')
        
        # Create Intents
        await conn.execute("""
            INSERT INTO intents (id, session_id, intent_text, intent_type, status, priority, metadata, created_at, updated_at)
            VALUES ($1, $2, 'Test intent 1', 'FEATURE', 'pending', 5, '{}', NOW(), NOW()),
                   ($3, $2, 'Test intent 2', 'FEATURE', 'pending', 5, '{}', NOW(), NOW())
        """, intent_id_1, session_id, intent_id_2)
        
        # Insert Contradiction
        contradiction_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO contradictions (
                id, user_id, new_intent_id, new_intent_content,
                conflicting_intent_id, conflicting_intent_content,
                contradiction_type, confidence_score, resolution_status
            )
            VALUES ($1, $2, $3, 'Test intent 1', $4, 'Test intent 2',
                    'tech_stack', 0.85, 'pending')
        """, contradiction_id, user_id, intent_id_1, intent_id_2)
        
        # SELECT
        row = await conn.fetchrow("SELECT * FROM contradictions WHERE id = $1", contradiction_id)
        assert row is not None
        assert row['contradiction_type'] == 'tech_stack'
        
        # UPDATE
        await conn.execute("UPDATE contradictions SET resolution_status = 'approved' WHERE id = $1", contradiction_id)
        updated_row = await conn.fetchrow("SELECT resolution_status FROM contradictions WHERE id = $1", contradiction_id)
        assert updated_row['resolution_status'] == 'approved'
        
        # DELETE
        await conn.execute("DELETE FROM contradictions WHERE id = $1", contradiction_id)
        
        # Cleanup
        await conn.execute("DELETE FROM intents WHERE session_id = $1", session_id)
        await conn.execute("DELETE FROM sessions WHERE id = $1", session_id)


@pytest.mark.asyncio
async def test_contradiction_detector_initialization(db_pool):
    """ST-CONTRA-006: ContradictionDetectorの初期化"""
    from app.services.contradiction.detector import ContradictionDetector
    detector = ContradictionDetector(db_pool)
    assert detector is not None
