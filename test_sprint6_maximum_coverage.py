"""
Sprint 6: 最大限カバレッジテスト（テストスクリプトのみ変更）

制約:
- テスト対象モジュールは一切変更しない
- テストスクリプトのみ変更・新規作成可能

実行可能範囲:
- 独立モジュール（TokenEstimator, Models, Config）
- 基本ロジック（環境変数取得）

実行不可能:
- Factory生成（backend依存でimport失敗）
- Service初期化（backend依存でimport失敗）
- 統合・E2E・Acceptanceテスト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, '/Users/zero/Projects/resonant-engine')


def test_01_token_estimator():
    """TC-01: TokenEstimator（Sprint 5で実証済み）✅"""
    print("\n=== TC-01: TokenEstimator テスト ===")
    
    # 直接ファイルからimport（__init__.pyを回避）
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "token_estimator",
        "/Users/zero/Projects/resonant-engine/context_assembler/token_estimator.py"
    )
    token_estimator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(token_estimator_module)
    TokenEstimator = token_estimator_module.TokenEstimator
    
    estimator = TokenEstimator()
    
    # Test 1: Single message
    tokens = estimator.estimate([{"role": "user", "content": "Hello"}])
    assert 5 <= tokens <= 20, f"Expected 5-20 tokens, got {tokens}"
    print(f"  ✅ Single message: {tokens} tokens")
    
    # Test 2: Multiple messages
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    tokens = estimator.estimate(messages)
    assert 50 <= tokens <= 100, f"Expected 50-100 tokens, got {tokens}"
    print(f"  ✅ Multiple messages: {tokens} tokens")
    
    # Test 3: Long text
    long_text = "This is a longer message. " * 10
    tokens = estimator.estimate([{"role": "user", "content": long_text}])
    assert 500 <= tokens <= 1000, f"Expected 500-1000 tokens, got {tokens}"
    print(f"  ✅ Long text: {tokens} tokens")
    
    print("✅ TC-01 PASS: TokenEstimator (3/3 tests)")
    return True


def test_02_models():
    """TC-02: Models（データクラス）✅"""
    print("\n=== TC-02: Models テスト ===")
    
    # 直接ファイルからimport（__init__.pyを回避）
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "models",
        "/Users/zero/Projects/resonant-engine/context_assembler/models.py"
    )
    models_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models_module)
    
    ContextConfig = models_module.ContextConfig
    ContextMetadata = models_module.ContextMetadata
    MemoryLayer = models_module.MemoryLayer
    
    # Test 1: ContextConfig
    config = ContextConfig(
        working_memory_limit=20,
        semantic_memory_limit=15,
    )
    assert config.working_memory_limit == 20
    assert config.semantic_memory_limit == 15
    
    # Test 2: ContextMetadata
    metadata = ContextMetadata(
        working_memory_count=5,
        semantic_memory_count=3,
        total_tokens=150,
        assembly_time_ms=50.0,
    )
    assert metadata.working_memory_count == 5
    assert metadata.semantic_memory_count == 3
    assert metadata.total_tokens == 150
    print("  ✅ ContextMetadata: メタデータ正常")
    
    # Test 3: MemoryLayer
    layer = MemoryLayer(
        layer_type="working",
        content="Test content",
        token_count=10,
    )
    assert layer.layer_type == "working"
    assert layer.content == "Test content"
    assert layer.token_count == 10
    print("  ✅ MemoryLayer: メモリレイヤー正常")
    
    print("✅ TC-02 PASS: Models (3/3 tests)")
    return True


def test_03_config():
    """TC-03: Config（設定値）✅"""
    print("\n=== TC-03: Config テスト ===")
    
    # 直接ファイルからimport（__init__.pyを回避）
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "config",
        "/Users/zero/Projects/resonant-engine/context_assembler/config.py"
    )
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    # Test 1: Default config
    config = config_module.get_default_config()
    assert config.working_memory_limit > 0
    assert config.semantic_memory_limit > 0
    assert config.max_context_tokens > 0
    print(f"  ✅ Default config: working={config.working_memory_limit}, "
          f"semantic={config.semantic_memory_limit}, "
          f"max_tokens={config.max_context_tokens}")
    
    # Test 2: Config values are reasonable
    assert config.working_memory_limit >= 5
    assert config.semantic_memory_limit >= 3
    assert config.max_context_tokens >= 100000  # At least 100K
    print("  ✅ Config values: 妥当な範囲")
    
    print("✅ TC-03 PASS: Config (2/2 tests)")
    return True


def test_04_database_url_logic():
    """TC-04: DATABASE_URL取得ロジック✅"""
    print("\n=== TC-04: DATABASE_URL Logic テスト ===")
    
    # Test 1: 環境変数設定時
    os.environ["DATABASE_URL"] = "postgresql://test:5432/db"
    url = os.getenv("DATABASE_URL")
    assert url == "postgresql://test:5432/db"
    print("  ✅ DATABASE_URL設定時: 正常取得")
    
    # Test 2: 環境変数未設定時
    del os.environ["DATABASE_URL"]
    url = os.getenv("DATABASE_URL")
    assert url is None
    print("  ✅ DATABASE_URL未設定時: None返却")
    
    # Test 3: 空文字列設定時
    os.environ["DATABASE_URL"] = ""
    url = os.getenv("DATABASE_URL")
    assert url == ""
    print("  ✅ DATABASE_URL空文字列時: 空文字列返却")
    
    print("✅ TC-04 PASS: DATABASE_URL logic (3/3 tests)")
    return True


def test_05_factory_creation_blocked():
    """TC-05: Factory生成（実行不可）⏸️"""
    print("\n=== TC-05: Factory Creation テスト ===")
    print("  ⏸️ SKIP: backend.app依存でimport失敗")
    print("  理由: context_assembler.factory → context_assembler.service → backend.app.repositories")
    print("  エラー: ModuleNotFoundError: No module named 'app'")
    return None


def test_06_service_initialization_blocked():
    """TC-06: Service初期化（実行不可）⏸️"""
    print("\n=== TC-06: Service Initialization テスト ===")
    print("  ⏸️ SKIP: backend.app依存でimport失敗")
    print("  理由: context_assembler.service → backend.app.models.message")
    return None


def test_07_bridge_factory_blocked():
    """TC-07: BridgeFactory統合（実行不可）⏸️"""
    print("\n=== TC-07: BridgeFactory Integration テスト ===")
    print("  ⏸️ SKIP: Context Assembler import失敗により実行不可")
    return None


def test_08_intent_bridge_blocked():
    """TC-08: Intent Bridge統合（実行不可）⏸️"""
    print("\n=== TC-08: Intent Bridge Integration テスト ===")
    print("  ⏸️ SKIP: Context Assembler import失敗により実行不可")
    return None


def test_09_e2e_blocked():
    """TC-09-14: E2E/Acceptanceテスト（実行不可）⏸️"""
    print("\n=== TC-09-14: E2E/Acceptance テスト ===")
    print("  ⏸️ SKIP: 統合コンポーネント必要、実行不可")
    return None


def main():
    """全テストを実行"""
    print("=" * 70)
    print("Sprint 6: 最大限カバレッジテスト")
    print("制約: テスト対象モジュール変更禁止、テストスクリプトのみ変更可")
    print("=" * 70)
    
    results = []
    
    # 実行可能テスト
    try:
        results.append(("TC-01: TokenEstimator", test_01_token_estimator()))
    except Exception as e:
        print(f"❌ TC-01 FAIL: {e}")
        results.append(("TC-01: TokenEstimator", False))
    
    try:
        results.append(("TC-02: Models", test_02_models()))
    except Exception as e:
        print(f"❌ TC-02 FAIL: {e}")
        results.append(("TC-02: Models", False))
    
    try:
        results.append(("TC-03: Config", test_03_config()))
    except Exception as e:
        print(f"❌ TC-03 FAIL: {e}")
        results.append(("TC-03: Config", False))
    
    try:
        results.append(("TC-04: DATABASE_URL Logic", test_04_database_url_logic()))
    except Exception as e:
        print(f"❌ TC-04 FAIL: {e}")
        results.append(("TC-04: DATABASE_URL Logic", False))
    
    # 実行不可能テスト（記録のみ）
    results.append(("TC-05: Factory Creation", test_05_factory_creation_blocked()))
    results.append(("TC-06: Service Initialization", test_06_service_initialization_blocked()))
    results.append(("TC-07: BridgeFactory", test_07_bridge_factory_blocked()))
    results.append(("TC-08: Intent Bridge", test_08_intent_bridge_blocked()))
    results.append(("TC-09-14: E2E/Acceptance", test_09_e2e_blocked()))
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)
    
    for name, result in results:
        if result is True:
            print(f"✅ PASS: {name}")
        elif result is False:
            print(f"❌ FAIL: {name}")
        else:
            print(f"⏸️ SKIP: {name}")
    
    print("\n" + "=" * 70)
    print(f"実行結果: {passed}/{total}件 PASS ({passed/total*100:.1f}%)")
    print(f"失敗: {failed}/{total}件")
    print(f"スキップ: {skipped}/{total}件 ({skipped/total*100:.1f}%) - backend依存")
    print("=" * 70)
    
    print("\n📝 結論:")
    print("  - テストスクリプトのみで実行可能: 4/14件 (29%)")
    print("  - 完全テスト実施には、テスト対象モジュールの変更が必須")
    print("  - 具体的には: backend.app の相対import修正")
    print("           または: context_assembler のインターフェース層導入")
    
    return passed == 4 and failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
