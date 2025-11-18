import pytest
from context_assembler.models import (
    AssemblyOptions,
    ContextConfig,
    ContextMetadata,
)


def test_context_config_defaults():
    """デフォルト設定のテスト"""
    config = ContextConfig()
    assert config.working_memory_limit == 10
    assert config.semantic_memory_limit == 5
    assert config.max_tokens == 100000
    assert config.token_safety_margin == 0.8


def test_context_config_validation():
    """設定の妥当性検証"""
    # 不正な値
    with pytest.raises(ValueError):
        ContextConfig(working_memory_limit=0)  # ge=1

    with pytest.raises(ValueError):
        ContextConfig(token_safety_margin=1.1)  # le=0.95


def test_assembly_options():
    """組み立てオプションのテスト"""
    options = AssemblyOptions(include_semantic_memory=False)
    assert options.include_semantic_memory is False
    assert options.include_session_summary is True  # デフォルト


def test_context_metadata():
    """コンテキストメタデータのテスト"""
    metadata = ContextMetadata(
        working_memory_count=5,
        semantic_memory_count=3,
        has_session_summary=True,
        total_tokens=1000,
        token_limit=80000,
        compression_applied=False,
        assembly_latency_ms=50.5,
    )

    assert metadata.working_memory_count == 5
    assert metadata.semantic_memory_count == 3
    assert metadata.has_session_summary is True
    assert metadata.total_tokens == 1000
    assert metadata.assembly_latency_ms == 50.5
