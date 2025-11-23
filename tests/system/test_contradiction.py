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
    """
    ST-CONTRA-001: ContradictionDetectorのインポート確認
    
    目的: 矛盾検出モジュールが正しくインポートできることを確認
    期待結果: インポートエラーが発生しない
    """
    from bridge.contradiction.detector import ContradictionDetector
    assert ContradictionDetector is not None


@pytest.mark.asyncio
async def test_contradiction_models():
    """
    ST-CONTRA-002: 矛盾検出モデルの確認
    
    目的: 矛盾検出用のデータモデルが正しく定義されていることを確認
    期待結果: 必要なモデルクラスがすべて存在する
    """
    from bridge.contradiction.models import (
        Contradiction,
        IntentRelation
    )
    
    # モデルクラスの確認
    assert Contradiction is not None
    assert IntentRelation is not None
    
    # 基本的なフィールドの確認（Pydantic V2対応）
    assert hasattr(Contradiction, 'model_fields')


@pytest.mark.asyncio
async def test_contradictions_table_structure(db_pool):
    """
    ST-CONTRA-003: contradictionsテーブル構造確認
    
    目的: contradictionsテーブルが正しい構造で作成されていることを確認
    期待結果: 必要なカラムがすべて存在する
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
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'contradictions'
            ORDER BY ordinal_position
        """)
        
        column_names = [c['column_name'] for c in columns]
        
        # 必須カラムの確認（実際のスキーマに合わせる）
        required_columns = [
            'id',
            'user_id',
            'new_intent_id',
            'new_intent_content',
            'contradiction_type',
            'confidence_score',
            'resolution_status',
            'created_at'
        ]
        
        for col in required_columns:
            assert col in column_names, f"必須カラム '{col}' が存在しません"


@pytest.mark.asyncio
async def test_intent_relations_table_structure(db_pool):
    """
    ST-CONTRA-004: intent_relationsテーブル構造確認
    
    目的: intent_relationsテーブルが正しい構造で作成されていることを確認
    期待結果: 必要なカラムがすべて存在する
    """
    async with db_pool.acquire() as conn:
        # テーブル存在確認
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'intent_relations'
            )
        """)
        assert exists is True, "intent_relationsテーブルが存在しません"
        
        # カラム確認
        columns = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'intent_relations'
        """)
        
        column_names = [c['column_name'] for c in columns]
        
        # 必須カラムの確認（実際のスキーマに合わせる）
        required_columns = [
            'id',
            'user_id',
            'source_intent_id',
            'target_intent_id',
            'relation_type',
            'created_at'
        ]
        
        for col in required_columns:
            assert col in column_names, f"必須カラム '{col}' が存在しません"


@pytest.mark.asyncio
async def test_contradiction_crud(db_pool):
    """
    ST-CONTRA-005: 矛盾レコードのCRUD操作
    
    目的: contradictionsテーブルへのCRUD操作が正常に動作することを確認
    期待結果: INSERT, SELECT, UPDATE, DELETE が正常に完了
    """
    async with db_pool.acquire() as conn:
        # テスト用のIntent IDを作成
        intent_id_1 = uuid.uuid4()
        intent_id_2 = uuid.uuid4()
        
        # まず、テスト用のIntentを作成
        await conn.execute("""
            INSERT INTO intents (id, intent_text, intent_type, status, priority, metadata)
            VALUES ($1, 'Test intent 1', 'FEATURE', 'pending', 5, '{}'),
                   ($2, 'Test intent 2', 'FEATURE', 'pending', 5, '{}')
        """, intent_id_1, intent_id_2)
        
        # 矛盾レコードを挿入（実際のスキーマに合わせる）
        contradiction_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO contradictions (
                id, user_id, new_intent_id, new_intent_content,
                conflicting_intent_id, conflicting_intent_content,
                contradiction_type, confidence_score, resolution_status
            )
            VALUES ($1, 'test_user', $2, 'Test intent 1', $3, 'Test intent 2',
                    'tech_stack', 0.85, 'pending')
        """, contradiction_id, intent_id_1, intent_id_2)
        
        # SELECT
        row = await conn.fetchrow(
            "SELECT * FROM contradictions WHERE id = $1",
            contradiction_id
        )
        assert row is not None, "矛盾レコードが見つかりません"
        assert row['contradiction_type'] == 'tech_stack'
        assert row['confidence_score'] == 0.85
        assert row['resolution_status'] == 'pending'
        
        # UPDATE
        await conn.execute("""
            UPDATE contradictions
            SET resolution_status = 'approved'
            WHERE id = $1
        """, contradiction_id)
        
        # 更新確認
        updated_row = await conn.fetchrow(
            "SELECT resolution_status FROM contradictions WHERE id = $1",
            contradiction_id
        )
        assert updated_row['resolution_status'] == 'approved'
        
        # DELETE (cleanup)
        await conn.execute("DELETE FROM contradictions WHERE id = $1", contradiction_id)
        await conn.execute("DELETE FROM intents WHERE id IN ($1, $2)", intent_id_1, intent_id_2)
        
        # 削除確認
        deleted_row = await conn.fetchrow(
            "SELECT * FROM contradictions WHERE id = $1",
            contradiction_id
        )
        assert deleted_row is None, "矛盾レコードが削除されていません"


@pytest.mark.asyncio
async def test_contradiction_detector_initialization(db_pool):
    """
    ST-CONTRA-006: ContradictionDetectorの初期化
    
    目的: ContradictionDetectorクラスが正しく初期化できることを確認
    期待結果: インスタンス化エラーが発生しない
    """
    from bridge.contradiction.detector import ContradictionDetector
    
    # 初期化（DB接続プールが必要）
    detector = ContradictionDetector(db_pool)
    assert detector is not None
    assert hasattr(detector, 'check_new_intent')
