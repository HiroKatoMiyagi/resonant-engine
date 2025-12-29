"""
ST-DB: データベース接続テスト

PostgreSQL接続、pgvector、CRUD操作を検証します。
"""
import pytest
import asyncpg
import uuid
import json
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_postgres_connection(db_pool):
    """ST-DB-001: PostgreSQL接続確認"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1, "SELECT 1 が期待通りの結果を返しませんでした"

@pytest.mark.asyncio
async def test_pgvector_extension(db_pool):
    """ST-DB-002: pgvector拡張確認"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        assert result == "vector", "pgvector拡張がインストールされていません"
        await conn.execute("SELECT '[1,2,3]'::vector")

@pytest.mark.asyncio
async def test_intents_crud(db_pool):
    """ST-DB-003: Intentsテーブル操作"""
    test_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    user_id = "test_user"

    async with db_pool.acquire() as conn:
        # 1. Create dependency: Session
        # Note: Session table schema check needed? Assuming minimal fields.
        await conn.execute("""
            INSERT INTO sessions (id, user_id, status, started_at, last_active)
            VALUES ($1, $2, $3, NOW(), NOW())
        """, uuid.UUID(session_id), user_id, 'active')

        # INSERT
        await conn.execute("""
            INSERT INTO intents (id, session_id, intent_text, intent_type, status, priority, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, uuid.UUID(test_id), uuid.UUID(session_id), 'Test intent', 'FEATURE', 'pending', 5, json.dumps({"test": True}))
        
        # SELECT
        row = await conn.fetchrow("SELECT * FROM intents WHERE id = $1", uuid.UUID(test_id))
        assert row is not None, "Intentが見つかりません"
        assert row['status'] == 'pending', f"ステータスが期待値と異なります: {row['status']}"
        
        # UPDATE
        await conn.execute("UPDATE intents SET status = 'completed' WHERE id = $1", uuid.UUID(test_id))
        updated_row = await conn.fetchrow("SELECT status FROM intents WHERE id = $1", uuid.UUID(test_id))
        assert updated_row['status'] == 'completed', "ステータスが更新されていません"
        
        # DELETE (cleanup)
        await conn.execute("DELETE FROM intents WHERE id = $1", uuid.UUID(test_id))
        deleted_row = await conn.fetchrow("SELECT * FROM intents WHERE id = $1", uuid.UUID(test_id))
        assert deleted_row is None, "Intentが削除されていません"

        # Cleanup session
        await conn.execute("DELETE FROM sessions WHERE id = $1", uuid.UUID(session_id))

@pytest.mark.asyncio
async def test_contradictions_table(db_pool):
    """ST-DB-004: contradictionsテーブル操作"""
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'contradictions'
            )
        """)
        # If table doesn't exist, skip (it might be Sprint 11 feature not yet migrated completely)
        if not exists:
            pytest.skip("contradictions table missing, verify migration")

        columns = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'contradictions'")
        column_names = [c['column_name'] for c in columns]
        
        required_columns = ['contradiction_type', 'confidence_score', 'resolution_status']
        for col in required_columns:
            assert col in column_names, f"必須カラム '{col}' が存在しません"

@pytest.mark.asyncio
async def test_vector_similarity_search(db_pool):
    """ST-DB-005: semantic_memoriesテーブル・ベクトル検索"""
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'semantic_memories'
            )
        """)
        if not exists:
            pytest.skip("semantic_memoriesテーブルが存在しないためスキップ")
        
        test_vector = [0.1] * 1536
        test_user_id = 'test_user_' + str(uuid.uuid4())[:8]
        
        await conn.execute("""
            INSERT INTO semantic_memories (content, embedding, memory_type, user_id)
            VALUES ('Test memory content', $1::vector, 'WORKING', $2)
        """, str(test_vector), test_user_id)
        
        results = await conn.fetch("""
            SELECT content, embedding <-> $1::vector AS distance
            FROM semantic_memories
            WHERE user_id = $2
            ORDER BY distance
            LIMIT 5
        """, str(test_vector), test_user_id)
        
        assert len(results) >= 1, "ベクトル検索結果が見つかりません"
        
        await conn.execute("DELETE FROM semantic_memories WHERE user_id = $1", test_user_id)
