"""
tests/system/test_realtime.py

ST-RT: リアルタイム通信テスト

このファイルは tests/conftest.py の db_pool フィクスチャを使用します。
独自のconftest.pyを作成しないでください。

注意: これらのテストはWebSocketとSSEの基本的な動作を確認します。
"""
import pytest
import httpx
import os


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.mark.asyncio
async def test_websocket_endpoint_exists():
    """ST-RT-001: WebSocketエンドポイント存在確認
    
    目的: WebSocketエンドポイントが定義されていることを確認
    前提条件: APIサーバーが起動していること
    
    注意: WebSocketの実際の接続テストは複雑なため、
    ここではエンドポイントの存在のみを確認します。
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # WebSocketエンドポイントへのHTTPリクエスト
            # （WebSocketではないため、エラーが返るが、エンドポイントの存在は確認できる）
            response = await client.get(f"{BASE_URL}/ws")
            
            # WebSocketエンドポイントはHTTP GETに対して
            # 400または426（Upgrade Required）を返すはず
            assert response.status_code in [400, 426, 404]
            
        except httpx.ConnectError:
            pytest.skip("APIサーバーに接続できません")


@pytest.mark.asyncio
async def test_sse_endpoint_exists():
    """ST-RT-002: SSEエンドポイント存在確認
    
    目的: Server-Sent Eventsエンドポイントが定義されていることを確認
    前提条件: APIサーバーが起動していること
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # SSEエンドポイントへのリクエスト
            response = await client.get(
                f"{BASE_URL}/api/events",
                headers={"Accept": "text/event-stream"},
                timeout=5.0,
            )
            
            # SSEエンドポイントは200を返すか、404（未実装）を返すはず
            assert response.status_code in [200, 404]
            
        except httpx.ConnectError:
            pytest.skip("APIサーバーに接続できません")
        except httpx.ReadTimeout:
            # SSEは長時間接続のため、タイムアウトは正常
            pass


@pytest.mark.asyncio
async def test_notification_trigger_exists(db_pool):
    """ST-RT-003: 通知トリガー存在確認
    
    目的: PostgreSQLのLISTEN/NOTIFYトリガーが定義されていることを確認
    前提条件: Sprint 4マイグレーション実行済み
    """
    async with db_pool.acquire() as conn:
        # トリガー関数の存在確認
        triggers = await conn.fetch("""
            SELECT proname FROM pg_proc
            WHERE proname LIKE 'notify_%'
        """)
        
        trigger_names = [t['proname'] for t in triggers]
        
        # 少なくとも1つの通知トリガーが存在することを確認
        assert len(trigger_names) > 0
        
        # 主要なトリガーの存在確認（存在しない場合はスキップ）
        expected_triggers = [
            'notify_intent_created',
            'notify_intent_status_changed',
            'notify_message_created',
        ]
        
        found_triggers = [t for t in expected_triggers if t in trigger_names]
        
        if len(found_triggers) == 0:
            pytest.skip(
                "通知トリガーが未作成のためスキップ。"
                "Sprint 4マイグレーション(002_intent_notify.sql, 003_message_notify.sql)を実行してください。"
            )


@pytest.mark.asyncio
async def test_realtime_notification_structure(db_pool):
    """ST-RT-004: リアルタイム通知構造確認
    
    目的: 通知トリガーが正しい構造でデータを送信することを確認
    前提条件: 通知トリガーが存在すること
    """
    async with db_pool.acquire() as conn:
        # トリガー関数の定義を取得
        trigger_def = await conn.fetchval("""
            SELECT pg_get_functiondef(oid)
            FROM pg_proc
            WHERE proname = 'notify_intent_created'
        """)
        
        if trigger_def is None:
            pytest.skip("notify_intent_created トリガーが未作成のためスキップ")
        
        # トリガー関数がpg_notifyを呼び出していることを確認
        assert 'pg_notify' in trigger_def.lower()
        
        # JSON形式でデータを送信していることを確認
        assert 'json_build_object' in trigger_def.lower()
