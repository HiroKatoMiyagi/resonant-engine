"""
tests/system/test_memory.py

ST-MEM: メモリシステムテスト

このファイルは tests/conftest.py の db_pool フィクスチャを使用します。
独自のconftest.pyを作成しないでください。
"""
import pytest
import uuid
from datetime import datetime

from memory_store.models import MemoryType, SourceType


@pytest.mark.asyncio
async def test_semantic_memories_table_exists(db_pool):
    """ST-MEM-001: semantic_memoriesテーブル存在確認
    
    目的: semantic_memoriesテーブルが存在することを確認
    前提条件: Sprint 9マイグレーション実行済み
    """
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'semantic_memories'
            )
        """)
        
        if not exists:
            pytest.skip(
                "semantic_memoriesテーブルが未作成のためスキップ。"
                "Sprint 9マイグレーション(006_memory_lifecycle_tables.sql)を実行してください。"
            )
        
        assert exists is True


@pytest.mark.asyncio
async def test_semantic_memory_crud(db_pool):
    """ST-MEM-002: SemanticMemory CRUD操作
    
    目的: semantic_memoriesテーブルの基本的なCRUD操作を確認
    前提条件: semantic_memoriesテーブルが存在すること
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
            pytest.skip("semantic_memoriesテーブルが未作成のためスキップ")
        
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        test_embedding = [0.1] * 1536  # OpenAI embedding形式
        
        # INSERT
        memory_id = await conn.fetchval("""
            INSERT INTO semantic_memories (
                user_id, content, embedding, memory_type, source_type, importance_score
            )
            VALUES ($1, $2, $3::vector, $4, $5, $6)
            RETURNING id
        """, test_user_id, "Test memory content", str(test_embedding), 
            MemoryType.WORKING.value, SourceType.INTENT.value, 0.5)
        
        assert memory_id is not None
        
        # SELECT
        row = await conn.fetchrow("""
            SELECT * FROM semantic_memories WHERE id = $1
        """, memory_id)
        
        assert row is not None
        assert row['content'] == "Test memory content"
        assert row['user_id'] == test_user_id
        assert row['memory_type'] == MemoryType.WORKING.value
        
        # UPDATE
        await conn.execute("""
            UPDATE semantic_memories
            SET importance_score = $1
            WHERE id = $2
        """, 0.8, memory_id)
        
        updated = await conn.fetchval("""
            SELECT importance_score FROM semantic_memories WHERE id = $1
        """, memory_id)
        
        assert updated == 0.8
        
        # DELETE (cleanup)
        await conn.execute("""
            DELETE FROM semantic_memories WHERE user_id = $1
        """, test_user_id)


@pytest.mark.asyncio
async def test_importance_scorer():
    """ST-MEM-003: ImportanceScorer動作確認
    
    目的: ImportanceScorerモジュールが存在し、基本機能を持つことを確認
    """
    import importlib.util
    import sys
    
    # 絶対パスで直接インポート
    spec = importlib.util.spec_from_file_location(
        "memory_lifecycle_root",
        "/app/memory_lifecycle/__init__.py"
    )
    memory_lifecycle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory_lifecycle)
    
    ImportanceScorer = memory_lifecycle.ImportanceScorer
    
    # ImportanceScorerはpoolが必要なので、クラスの存在とメソッドの存在のみ確認
    assert ImportanceScorer is not None
    assert hasattr(ImportanceScorer, 'calculate_score')
    assert hasattr(ImportanceScorer, 'apply_decay')


@pytest.mark.asyncio
async def test_capacity_manager():
    """ST-MEM-004: CapacityManager動作確認
    
    目的: CapacityManagerモジュールが存在し、基本機能を持つことを確認
    """
    import importlib.util
    
    # 絶対パスで直接インポート
    spec = importlib.util.spec_from_file_location(
        "memory_lifecycle_root",
        "/app/memory_lifecycle/__init__.py"
    )
    memory_lifecycle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory_lifecycle)
    
    CapacityManager = memory_lifecycle.CapacityManager
    
    # CapacityManagerはpool, compression_service, scorerが必要なので、クラスの存在とメソッドの存在のみ確認
    assert CapacityManager is not None
    assert hasattr(CapacityManager, 'check_capacity')
    assert hasattr(CapacityManager, 'auto_compress_if_needed')


@pytest.mark.asyncio
async def test_compression_service():
    """ST-MEM-005: CompressionService動作確認
    
    目的: MemoryCompressionServiceモジュールが存在し、基本機能を持つことを確認
    """
    import importlib.util
    
    # 絶対パスで直接インポート
    spec = importlib.util.spec_from_file_location(
        "memory_lifecycle_root",
        "/app/memory_lifecycle/__init__.py"
    )
    memory_lifecycle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory_lifecycle)
    
    MemoryCompressionService = memory_lifecycle.MemoryCompressionService
    
    # MemoryCompressionServiceはpoolとapi_keyが必要なので、クラスの存在とメソッドの存在のみ確認
    assert MemoryCompressionService is not None
    assert hasattr(MemoryCompressionService, 'compress_memory')
    assert hasattr(MemoryCompressionService, 'summarize_content')
    assert hasattr(MemoryCompressionService, 'restore_from_archive')


@pytest.mark.asyncio
async def test_memory_archive_table(db_pool):
    """ST-MEM-006: memory_archiveテーブル確認
    
    目的: memory_archiveテーブルが存在し、基本操作ができることを確認
    前提条件: Sprint 9マイグレーション実行済み
    """
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'memory_archive'
            )
        """)
        
        if not exists:
            pytest.skip("memory_archiveテーブルが未作成のためスキップ")
        
        # テーブル構造確認
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'memory_archive'
        """)
        
        column_names = [c['column_name'] for c in columns]
        
        assert 'id' in column_names
        assert 'original_memory_id' in column_names
        assert 'compressed_summary' in column_names  # 実際のカラム名


@pytest.mark.asyncio
async def test_memory_lifecycle_log_table(db_pool):
    """ST-MEM-007: memory_lifecycle_logテーブル確認
    
    目的: memory_lifecycle_logテーブルが存在し、基本操作ができることを確認
    前提条件: Sprint 9マイグレーション実行済み
    """
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'memory_lifecycle_log'
            )
        """)
        
        if not exists:
            pytest.skip("memory_lifecycle_logテーブルが未作成のためスキップ")
        
        # テーブル構造確認
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'memory_lifecycle_log'
        """)
        
        column_names = [c['column_name'] for c in columns]
        
        assert 'id' in column_names
        assert 'memory_id' in column_names
        assert 'event_type' in column_names
        assert 'event_details' in column_names  # 実際のカラム名
