"""
tests/system/test_e2e.py

ST-E2E: エンドツーエンドテスト

このファイルは tests/conftest.py の db_pool フィクスチャを使用します。
独自のconftest.pyを作成しないでください。

注意: これらのテストはシステム全体の統合動作を確認します。
"""
import pytest
import httpx
import os
import uuid
import json
from datetime import datetime


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.mark.asyncio
async def test_e2e_intent_creation_and_retrieval(db_pool):
    """ST-E2E-001: Intent作成から取得までのフロー
    
    目的: IntentをDBに作成し、APIで取得できることを確認
    前提条件: APIサーバーとDBが起動していること
    """
    test_id = uuid.uuid4()
    
    # 1. DBに直接Intentを作成
    async with db_pool.acquire() as conn:
        # テーブル構造を確認
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'intents'
        """)
        column_names = [c['column_name'] for c in columns]
        
        # Sprint 10マイグレーション対応
        text_column = 'intent_text' if 'intent_text' in column_names else 'description'
        
        await conn.execute(f"""
            INSERT INTO intents (id, {text_column}, intent_type, status, priority, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, test_id, 'E2E test intent', 'FEATURE_REQUEST', 'pending', 0, json.dumps({"test": "e2e"}))
    
    # 2. APIでIntentを取得
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/intents")
            
            assert response.status_code == 200
            
            data = response.json()
            
            # APIレスポンスがページネーション形式の場合
            if isinstance(data, dict) and 'items' in data:
                items = data['items']
            else:
                items = data
            
            assert isinstance(items, list)
            
            # 作成したIntentが含まれているか確認
            intent_ids = [item.get('id') for item in items]
            assert str(test_id) in intent_ids
            
        except httpx.ConnectError:
            pytest.skip("APIサーバーに接続できません")
        finally:
            # クリーンアップ
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM intents WHERE id = $1", test_id)


@pytest.mark.asyncio
async def test_e2e_message_creation_and_retrieval(db_pool):
    """ST-E2E-002: Message作成から取得までのフロー
    
    目的: MessageをDBに作成し、APIで取得できることを確認
    前提条件: APIサーバーとDBが起動していること
    """
    test_id = uuid.uuid4()
    test_user_id = f"e2e_user_{uuid.uuid4().hex[:8]}"
    
    # 1. DBに直接Messageを作成
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO messages (id, user_id, content, message_type, metadata)
            VALUES ($1, $2, $3, $4, $5)
        """, test_id, test_user_id, 'E2E test message', 'user', json.dumps({"test": "e2e"}))
    
    # 2. APIでMessageを取得
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/messages")
            
            assert response.status_code == 200
            
            data = response.json()
            
            # APIレスポンスがページネーション形式の場合
            if isinstance(data, dict) and 'items' in data:
                items = data['items']
            else:
                items = data
            
            assert isinstance(items, list)
            
            # 作成したMessageが含まれているか確認
            message_ids = [item.get('id') for item in items]
            assert str(test_id) in message_ids
            
        except httpx.ConnectError:
            pytest.skip("APIサーバーに接続できません")
        finally:
            # クリーンアップ
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM messages WHERE id = $1", test_id)


@pytest.mark.asyncio
async def test_e2e_system_health_check():
    """ST-E2E-003: システム全体のヘルスチェック
    
    目的: システムの主要コンポーネントが正常に動作していることを確認
    前提条件: APIサーバーとDBが起動していること
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # 1. ヘルスチェックエンドポイント
            health_response = await client.get(f"{BASE_URL}/health")
            assert health_response.status_code == 200
            
            health_data = health_response.json()
            assert health_data.get("status") in ["healthy", "ok"]
            assert health_data.get("database") == "connected"
            
            # 2. ルートエンドポイント
            root_response = await client.get(f"{BASE_URL}/")
            assert root_response.status_code == 200
            
            # 3. APIドキュメント
            docs_response = await client.get(f"{BASE_URL}/docs")
            assert docs_response.status_code == 200
            
            # 4. 主要なAPIエンドポイント
            endpoints = [
                "/api/messages",
                "/api/intents",
                "/api/specifications",
                "/api/notifications",
            ]
            
            for endpoint in endpoints:
                response = await client.get(f"{BASE_URL}{endpoint}")
                assert response.status_code == 200, f"Endpoint {endpoint} failed"
            
        except httpx.ConnectError:
            pytest.skip("APIサーバーに接続できません")
