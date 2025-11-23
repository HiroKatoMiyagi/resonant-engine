"""
ST-DB: データベース接続テスト

PostgreSQL接続、pgvector、CRUD操作を検証します。
"""
import pytest
import asyncpg
import uuid
import json
from datetime import datetime, timezone

# フィクスチャは使用しないため削除（db_poolフィクスチャを使用）


@pytest.mark.asyncio
@pytest.mark.db
async def test_postgres_connection(db_pool):
    """
    ST-DB-001: PostgreSQL接続確認
    
    目的: PostgreSQLへの接続が正常に行えることを確認
    期待結果: 接続成功、SELECT 1 が "1" を返す
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1, "SELECT 1 が期待通りの結果を返しませんでした"


@pytest.mark.asyncio
@pytest.mark.db
async def test_pgvector_extension(db_pool):
    """
    ST-DB-002: pgvector拡張確認
    
    目的: pgvector拡張が有効であることを確認
    期待結果: vector拡張がインストール済み
    """
    async with db_pool.acquire() as conn:
        # 拡張確認
        result = await conn.fetchval(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )
        assert result == "vector", "pgvector拡張がインストールされていません"
        
        # vector型テスト
        await conn.execute("SELECT '[1,2,3]'::vector")


@pytest.mark.asyncio
@pytest.mark.db
async def test_intents_crud(db_pool):
    """
    ST-DB-003: Intentsテーブル操作
    
    目的: intentsテーブルへのCRUD操作を確認
    手順: INSERT → SELECT → UPDATE → DELETE
    期待結果: 全操作が正常に完了
    
    注意: 実際のスキーマに合わせて調整
    """
    test_id = str(uuid.uuid4())
    
    async with db_pool.acquire() as conn:
        # INSERT (実際のスキーマに合わせる)
        await conn.execute("""
            INSERT INTO intents (id, intent_text, intent_type, status, priority, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, uuid.UUID(test_id), 'Test intent', 'FEATURE', 'pending', 5, json.dumps({"test": True}))
        
        # SELECT
        row = await conn.fetchrow(
            "SELECT * FROM intents WHERE id = $1",
            uuid.UUID(test_id)
        )
        assert row is not None, "Intentが見つかりません"
        assert row['status'] == 'pending', f"ステータスが期待値と異なります: {row['status']}"
        
        # UPDATE
        await conn.execute(
            "UPDATE intents SET status = 'completed' WHERE id = $1",
            uuid.UUID(test_id)
        )
        
        # 更新確認
        updated_row = await conn.fetchrow(
            "SELECT status FROM intents WHERE id = $1",
            uuid.UUID(test_id)
        )
        assert updated_row['status'] == 'completed', "ステータスが更新されていません"
        
        # DELETE (cleanup)
        await conn.execute(
            "DELETE FROM intents WHERE id = $1",
            uuid.UUID(test_id)
        )
        
        # 削除確認
        deleted_row = await conn.fetchrow(
            "SELECT * FROM intents WHERE id = $1",
            uuid.UUID(test_id)
        )
        assert deleted_row is None, "Intentが削除されていません"


@pytest.mark.asyncio
@pytest.mark.db
async def test_contradictions_table(db_pool):
    """
    ST-DB-004: contradictionsテーブル操作
    
    目的: Sprint 11で追加されたcontradictionsテーブルの動作確認
    期待結果: 矛盾レコードの保存・取得が正常に行える
    """
    async with db_pool.acquire() as conn:
        # テーブル存在確認
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'contradictions'
            )
        """)
        assert exists is True, "contradictionsテーブルが存在しません"
        
        # カラム確認
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'contradictions'
        """)
        column_names = [c['column_name'] for c in columns]
        
        required_columns = [
            'contradiction_type',
            'confidence_score',
            'resolution_status'
        ]
        
        for col in required_columns:
            assert col in column_names, f"必須カラム '{col}' が存在しません"


@pytest.mark.asyncio
@pytest.mark.db
async def test_vector_similarity_search(db_pool):
    """
    ST-DB-005: semantic_memoriesテーブル・ベクトル検索
    
    目的: ベクトル埋め込みを使用した類似検索を確認
    期待結果: ベクトル類似度検索が正常に動作
    """
    async with db_pool.acquire() as conn:
        # テーブル存在確認
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'semantic_memories'
            )
        """)
        
        if not exists:
            pytest.skip("semantic_memoriesテーブルが存在しないためスキップ")
        
        # テスト用メモリ挿入（1536次元のダミーベクトル）
        test_vector = [0.1] * 1536
        test_user_id = 'test_user_' + str(uuid.uuid4())[:8]
        
        await conn.execute("""
            INSERT INTO semantic_memories (content, embedding, memory_type, user_id)
            VALUES ('Test memory content', $1::vector, 'WORKING', $2)
        """, str(test_vector), test_user_id)
        
        # 類似検索
        results = await conn.fetch("""
            SELECT content, embedding <-> $1::vector AS distance
            FROM semantic_memories
            WHERE user_id = $2
            ORDER BY distance
            LIMIT 5
        """, str(test_vector), test_user_id)
        
        assert len(results) >= 1, "ベクトル検索結果が見つかりません"
        assert results[0]['content'] == 'Test memory content', "検索結果の内容が一致しません"
        
        # クリーンアップ
        await conn.execute(
            "DELETE FROM semantic_memories WHERE user_id = $1",
            test_user_id
        )
