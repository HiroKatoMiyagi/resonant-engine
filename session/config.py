"""Session管理設定"""

from pydantic import BaseModel, Field


class SessionConfig(BaseModel):
    """セッション管理設定"""

    # 要約生成トリガー条件
    summary_trigger_message_count: int = Field(
        default=20,
        ge=10,
        description="この数のメッセージ後に要約生成"
    )

    summary_trigger_interval_seconds: int = Field(
        default=3600,  # 1時間
        ge=300,  # 最低5分
        description="前回要約からこの秒数経過後に要約生成"
    )

    # 要約設定
    summary_max_messages: int = Field(
        default=100,
        ge=10,
        description="要約に含める最大メッセージ数"
    )

    # Claude API設定
    claude_model: str = Field(
        default="claude-3-5-haiku-20241022",  # 高速なHaikuを使用
        description="要約生成に使用するClaudeモデル"
    )

    claude_max_tokens: int = Field(
        default=500,
        ge=100,
        le=1000,
        description="要約の最大トークン数"
    )


def get_default_session_config() -> SessionConfig:
    """デフォルト設定を取得"""
    return SessionConfig()
