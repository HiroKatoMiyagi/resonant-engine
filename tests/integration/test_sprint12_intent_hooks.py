import pytest
import asyncio
from app.services.term_drift.detector import TermDriftDetector

@pytest.mark.asyncio
async def test_intent_creation_triggers_term_analysis(test_client, db_pool):
    """Intent作成時に用語分析がトリガーされるかテスト"""
    from uuid import uuid4
    user_id = f"test_user_hook_{uuid4()}"
    
    # 1. Intent作成
    unique_term = f"UniqueTerm_{uuid4()}"
    response = await test_client.post(
        "/api/intents",
        json={
            "intent_text": f"「{unique_term}」はユニークな用語です。",
            "intent_type": "request",
            "priority": 1,
            "status": "pending",
            "metadata": {"user_id": user_id}
        }
    )
    
    assert response.status_code == 201
    
    # Background Taskの完了を待つ（テスト環境での挙動によるが、少し待機）
    # Note: ASGITransport might not auto-await background tasks depending on configuration.
    # However, usually it's fire-and-forget.
    await asyncio.sleep(0.5)
    
    # 2. 用語が抽出されたか確認
    # detectorを直接使うか、DBを直接見る
    # 这里ではDBを直接見る
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM term_definitions WHERE term_name = $1", 
            unique_term
        )
        
        assert row is not None
        assert row["term_name"] == unique_term
        assert "ユニークな用語" in row["definition_text"]
