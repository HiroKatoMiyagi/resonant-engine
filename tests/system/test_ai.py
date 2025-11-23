"""
tests/system/test_ai.py

ST-AI: Claude API (Kana) テスト

このファイルは tests/conftest.py の db_pool フィクスチャを使用します。
独自のconftest.pyを作成しないでください。

注意: これらのテストは実際のClaude APIを呼び出すため、
ANTHROPIC_API_KEYが設定されている必要があります。
"""
import pytest
import os
from typing import Dict, Any

from bridge.providers.ai.kana_ai_bridge import KanaAIBridge
from bridge.providers.ai.mock_ai_bridge import MockAIBridge


@pytest.mark.asyncio
async def test_kana_initialization():
    """ST-AI-001: Kana初期化確認
    
    目的: KanaAIBridgeが正しく初期化できることを確認
    前提条件: ANTHROPIC_API_KEYが設定されていること
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping Kana initialization test")
    
    kana = KanaAIBridge(api_key=api_key)
    
    assert kana is not None
    assert kana._model is not None
    assert kana._client is not None


@pytest.mark.asyncio
async def test_kana_simple_intent_processing():
    """ST-AI-002: シンプルなIntent処理
    
    目的: KanaがシンプルなIntentを処理できることを確認
    前提条件: ANTHROPIC_API_KEYが設定されていること
    
    注意: 実際のAPI呼び出しのため、エラーが発生する可能性があります。
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping Kana API test")
    
    kana = KanaAIBridge(api_key=api_key)
    
    intent = {
        "content": "Hello, Kana. This is a test message.",
        "user_id": "test_user",
    }
    
    result = await kana.process_intent(intent)
    
    assert result is not None
    
    # エラーの場合はスキップ（API制限やネットワークエラーの可能性）
    if result.get("status") == "error":
        pytest.skip(f"Kana API returned error: {result.get('reason')}")
    
    assert result.get("status") == "ok"
    assert "summary" in result
    assert len(result["summary"]) > 0


@pytest.mark.asyncio
async def test_kana_error_handling():
    """ST-AI-003: エラーハンドリング確認
    
    目的: Kanaが不正なAPIキーを適切に処理できることを確認
    """
    # 不正なAPIキーでKanaを初期化
    try:
        kana = KanaAIBridge(api_key="invalid_key_12345")
        
        intent = {
            "content": "Test message",
            "user_id": "test_user",
        }
        
        result = await kana.process_intent(intent)
        
        # エラーが適切に処理されることを確認
        assert result is not None
        assert result.get("status") == "error"
        assert "reason" in result
        
    except ValueError as e:
        # 初期化時にエラーが発生する場合もある
        assert "ANTHROPIC_API_KEY" in str(e)


@pytest.mark.asyncio
async def test_kana_with_context():
    """ST-AI-004: コンテキスト付きIntent処理
    
    目的: Kanaがコンテキスト情報を含むIntentを処理できることを確認
    前提条件: ANTHROPIC_API_KEYが設定されていること
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping Kana context test")
    
    kana = KanaAIBridge(api_key=api_key)
    
    intent = {
        "content": "What is the weather like today?",
        "user_id": "test_user",
        "session_id": None,  # Context Assembler未設定の場合
    }
    
    result = await kana.process_intent(intent)
    
    assert result is not None
    
    # エラーの場合はスキップ（API制限やネットワークエラーの可能性）
    if result.get("status") == "error":
        pytest.skip(f"Kana API returned error: {result.get('reason')}")
    
    assert result.get("status") == "ok"
    assert "summary" in result


@pytest.mark.asyncio
async def test_mock_ai_bridge():
    """ST-AI-005: MockAIBridge動作確認
    
    目的: テスト用のMockAIBridgeが正常に動作することを確認
    """
    mock_ai = MockAIBridge()
    
    intent = {
        "type": "test_intent",
        "payload": {"test": "data"},
    }
    
    result = await mock_ai.process_intent(intent)
    
    assert result is not None
    assert "intent_type" in result
    assert result["intent_type"] == "test_intent"
    assert "analysis" in result
    assert "summary" in result["analysis"]
