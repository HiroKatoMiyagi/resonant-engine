"""Context Assembler - Configuration"""

from context_assembler.models import ContextConfig


def get_default_config() -> ContextConfig:
    """デフォルト設定を取得"""
    return ContextConfig(
        system_prompt=(
            "You are Kana, the external translator for Resonant Engine.\n"
            "You help users understand and interact with the system by "
            "translating their intentions into structured actions."
        ),
        working_memory_limit=10,
        semantic_memory_limit=5,
        max_tokens=100000,  # Claude Sonnet 4.5: 200k (安全マージン考慮)
        token_safety_margin=0.8,
    )
