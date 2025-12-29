"""BridgeFactory - Context Assembler統合テスト"""

import pytest

# Bridge migration in progress - factory has been moved to dependencies.py
pytestmark = pytest.mark.skip(reason="Bridge migration in progress - use app.dependencies instead")
import warnings
from unittest.mock import AsyncMock, patch

from bridge.factory.bridge_factory import BridgeFactory
from app.integrations import KanaAIBridge, MockAIBridge


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_success():
    """Context Assembler統合版AI Bridgeの生成成功 (TC-04)"""
    mock_pool = AsyncMock()

    # Context Assembler mockを作成
    with patch("bridge.factory.bridge_factory.create_context_assembler") as mock_ca_factory:
        mock_context_assembler = AsyncMock()
        mock_ca_factory.return_value = mock_context_assembler

        # 実行
        bridge = await BridgeFactory.create_ai_bridge_with_memory("kana", pool=mock_pool)

        # 検証
        assert bridge is not None
        assert isinstance(bridge, KanaAIBridge)
        assert hasattr(bridge, "process_intent")
        assert hasattr(bridge, "_context_assembler")
        assert bridge._context_assembler == mock_context_assembler

        # Context Assembler factoryが呼ばれたことを確認
        mock_ca_factory.assert_called_once_with(pool=mock_pool)


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_default_type():
    """bridge_type省略時に環境変数から取得 (TC-04-2)"""
    with patch("bridge.factory.bridge_factory.create_context_assembler") as mock_ca_factory, \
         patch.dict("os.environ", {"AI_BRIDGE_TYPE": "kana"}):

        mock_ca_factory.return_value = AsyncMock()

        bridge = await BridgeFactory.create_ai_bridge_with_memory()

        assert isinstance(bridge, KanaAIBridge)


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_mock():
    """Mock Bridge生成（Context Assemblerなし） (TC-04-3)"""
    bridge = await BridgeFactory.create_ai_bridge_with_memory("mock")

    assert bridge is not None
    assert isinstance(bridge, MockAIBridge)
    # MockはContext Assemblerを持たない
    assert not hasattr(bridge, "_context_assembler") or bridge._context_assembler is None


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_invalid_type():
    """未対応のbridge_typeでエラー (TC-04-4)"""
    with pytest.raises(ValueError, match="Unsupported AI_BRIDGE_TYPE"):
        await BridgeFactory.create_ai_bridge_with_memory("invalid_type")


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_fallback_on_connection_error():
    """Context Assembler初期化失敗時にFallback (TC-05)"""
    # Context Assembler初期化がConnectionErrorで失敗
    with patch("bridge.factory.bridge_factory.create_context_assembler") as mock_ca_factory:
        mock_ca_factory.side_effect = ConnectionError("Database connection failed")

        # 警告を捕捉
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            bridge = await BridgeFactory.create_ai_bridge_with_memory("kana")

            # Fallback成功
            assert bridge is not None
            assert isinstance(bridge, KanaAIBridge)

            # 警告が発生したことを確認
            assert len(w) > 0
            assert "Context Assembler initialization failed" in str(w[0].message)
            assert "Falling back to KanaAIBridge without context memory" in str(w[0].message)

            # Context Assemblerなし
            assert bridge._context_assembler is None


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_fallback_on_import_error():
    """依存関係インポート失敗時にFallback (TC-05-2)"""
    with patch("bridge.factory.bridge_factory.create_context_assembler") as mock_ca_factory:
        mock_ca_factory.side_effect = ImportError("Memory Store not found")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            bridge = await BridgeFactory.create_ai_bridge_with_memory("kana")

            # Fallback成功
            assert isinstance(bridge, KanaAIBridge)
            assert bridge._context_assembler is None

            # 警告確認
            assert len(w) > 0
            assert "Memory Store not found" in str(w[0].message)


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_fallback_on_value_error():
    """設定エラー時にFallback (TC-05-3)"""
    with patch("bridge.factory.bridge_factory.create_context_assembler") as mock_ca_factory:
        mock_ca_factory.side_effect = ValueError("Invalid configuration")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            bridge = await BridgeFactory.create_ai_bridge_with_memory("kana")

            assert isinstance(bridge, KanaAIBridge)
            assert bridge._context_assembler is None
            assert len(w) > 0


@pytest.mark.asyncio
async def test_create_ai_bridge_backward_compatibility():
    """既存のcreate_ai_bridge()は引き続き動作 (後方互換性)"""
    # 同期版のcreate_ai_bridge()が動作することを確認
    bridge = BridgeFactory.create_ai_bridge("kana")

    assert isinstance(bridge, KanaAIBridge)
    # Context Assemblerなし（従来の動作）
    assert bridge._context_assembler is None


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_pool_passed_to_factory():
    """poolがContext Assembler factoryに渡される (TC-04-5)"""
    mock_pool = AsyncMock()

    with patch("bridge.factory.bridge_factory.create_context_assembler") as mock_ca_factory:
        mock_ca_factory.return_value = AsyncMock()

        await BridgeFactory.create_ai_bridge_with_memory("kana", pool=mock_pool)

        # poolが渡されたことを確認
        mock_ca_factory.assert_called_once_with(pool=mock_pool)


@pytest.mark.asyncio
async def test_create_ai_bridge_with_memory_none_pool():
    """pool=Noneの場合、Context Assembler factoryで新規作成 (TC-04-6)"""
    with patch("bridge.factory.bridge_factory.create_context_assembler") as mock_ca_factory:
        mock_ca_factory.return_value = AsyncMock()

        await BridgeFactory.create_ai_bridge_with_memory("kana", pool=None)

        # pool=Noneが渡される
        mock_ca_factory.assert_called_once_with(pool=None)
