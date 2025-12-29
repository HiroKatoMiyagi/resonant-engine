import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_analyze_text_api(test_client):
    """用語分析APIテスト"""
    response = await test_client.post(
        "/api/v1/term-drift/analyze",
        json={
            "user_id": "test_user_e2e",
            "text": "「TestAPI」はテスト用のAPIです。HTTPで通信します。",
            "source": "test_doc.md"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "analyzed_terms" in data
    assert data["analyzed_terms"] >= 1
    assert "results" in data

@pytest.mark.asyncio
async def test_get_pending_drifts_api(test_client):
    """未解決ドリフト取得APIテスト"""
    response = await test_client.get(
        "/api/v1/term-drift/pending",
        params={"user_id": "test_user_e2e", "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_check_constraint_api(test_client):
    """制約チェックAPIテスト"""
    response = await test_client.post(
        "/api/v1/temporal-constraint/check",
        json={
            "user_id": "test_user_e2e",
            "file_path": "some_file.py",
            "modification_type": "edit",
            "modification_reason": "テスト修正",
            "requested_by": "user"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "constraint_level" in data
    assert "check_result" in data

@pytest.mark.asyncio
async def test_register_verification_api(test_client):
    """検証登録APIテスト"""
    response = await test_client.post(
        "/api/v1/temporal-constraint/verify",
        params={
            "user_id": "test_user_e2e",
            "file_path": "api_test_file.py",
            "verification_type": "integration_test",
            "test_hours": 25.0,
            "constraint_level": "high"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "registered"
    assert "verification_id" in data
