"""
Profile Context Provider

Sprint 8: User Profile & Persistent Context
プロフィール情報をClaude用コンテキストに変換
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging
import time

from .repository import UserProfileRepository
from .models import UserProfileData, CognitiveTrait, FamilyMember, UserGoal

logger = logging.getLogger(__name__)


class ProfileContext(BaseModel):
    """プロフィールコンテキスト"""

    system_prompt_adjustment: str
    context_section: str
    response_guidelines: List[str]
    token_count: int


class ProfileContextProvider:
    """プロフィールコンテキスト提供"""

    def __init__(self, profile_repo: UserProfileRepository):
        self.profile_repo = profile_repo
        self.cache: Dict[str, tuple[ProfileContext, float]] = (
            {}
        )  # user_id -> (context, timestamp)
        self.cache_ttl = 3600  # 1時間

    async def get_profile_context(
        self,
        user_id: str,
        include_family: bool = True,
        include_goals: bool = True,
    ) -> Optional[ProfileContext]:
        """
        プロフィールコンテキストを生成

        Args:
            user_id: ユーザーID
            include_family: 家族情報を含めるか
            include_goals: 目標を含めるか

        Returns:
            ProfileContext: コンテキスト（見つからない場合はNone）
        """
        # キャッシュチェック
        if user_id in self.cache:
            cached_context, timestamp = self.cache[user_id]
            if (time.time() - timestamp) < self.cache_ttl:
                logger.debug(f"Profile context cache hit: {user_id}")
                return cached_context

        # プロフィール取得
        profile_data = await self.profile_repo.get_profile(user_id)
        if not profile_data:
            logger.warning(f"Profile not found: {user_id}")
            return None

        # System Prompt調整
        system_adjustment = self._build_system_prompt_adjustment(
            profile_data.cognitive_traits
        )

        # コンテキストセクション構築
        context_parts = [
            self._build_cognitive_traits_section(profile_data.cognitive_traits)
        ]

        if include_family and profile_data.family_members:
            context_parts.append(
                self._build_family_section(profile_data.family_members)
            )

        if include_goals and profile_data.goals:
            context_parts.append(self._build_goals_section(profile_data.goals))

        context_section = "\n\n".join(filter(None, context_parts))
        guidelines = self._build_response_guidelines(profile_data.cognitive_traits)
        token_count = self._estimate_tokens(system_adjustment + context_section)

        profile_context = ProfileContext(
            system_prompt_adjustment=system_adjustment,
            context_section=context_section,
            response_guidelines=guidelines,
            token_count=token_count,
        )

        # キャッシュ保存
        self.cache[user_id] = (profile_context, time.time())
        logger.info(
            f"✅ Profile context generated: {token_count} tokens for user {user_id}"
        )

        return profile_context

    def _build_system_prompt_adjustment(
        self, traits: List[CognitiveTrait]
    ) -> str:
        """System Prompt調整文生成"""
        critical_traits = [t for t in traits if t.importance_level == "critical"]

        if not critical_traits:
            return ""

        lines = [
            "## ユーザー認知特性への配慮",
            "",
            "このユーザーはASD（自閉スペクトラム症）の認知特性を持っています。応答時は以下を厳守してください：",
            "",
        ]

        # トリガー回避
        triggers = [t for t in traits if t.trait_type == "asd_trigger"]
        if triggers:
            lines.append("**回避すべきトリガー:**")
            for trigger in triggers[:5]:  # トークン節約のため上位5件
                lines.append(f"- {trigger.trait_name}")
            lines.append("")

        # 推奨アプローチ
        preferences = [t for t in traits if t.trait_type == "asd_preference"]
        if preferences:
            lines.append("**推奨アプローチ:**")
            for pref in preferences[:5]:  # トークン節約のため上位5件
                lines.append(f"- {pref.trait_name}")
            lines.append("")

        lines.extend(
            [
                "**具体的な対応:**",
                "- 常に複数の選択肢を提示し、押し付けない",
                "- 否定形を避け、肯定的・建設的な表現を使う",
                "- 情報を階層的・構造的に提示する",
                "- 一貫性を保ち、矛盾を避ける",
            ]
        )

        return "\n".join(lines)

    def _build_cognitive_traits_section(
        self, traits: List[CognitiveTrait]
    ) -> str:
        """認知特性セクション構築"""
        if not traits:
            return ""

        lines = ["## ユーザー認知特性", ""]

        # 重要度順にソート
        importance_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_traits = sorted(
            traits, key=lambda t: importance_order.get(t.importance_level, 99)
        )

        for trait in sorted_traits[:5]:  # トークン節約のため上位5件
            desc = trait.description or ""
            lines.append(
                f"- **{trait.trait_name}** ({trait.importance_level}): {desc}"
            )

        return "\n".join(lines)

    def _build_family_section(self, family_members: List[FamilyMember]) -> str:
        """家族セクション構築"""
        if not family_members:
            return ""

        lines = ["## 家族構成", ""]

        for member in family_members:
            age_info = ""
            if member.birth_date:
                from datetime import date

                age = (date.today() - member.birth_date).days // 365
                age_info = f" ({age}歳)"

            relationship_ja = {
                "spouse": "配偶者",
                "child": "子",
                "parent": "親",
            }.get(member.relationship, member.relationship)

            lines.append(f"- {member.name}{age_info} - {relationship_ja}")

        return "\n".join(lines)

    def _build_goals_section(self, goals: List[UserGoal]) -> str:
        """目標セクション構築"""
        if not goals:
            return ""

        lines = ["## ユーザー目標", ""]

        # 優先度順にソート
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_goals = sorted(
            goals, key=lambda g: priority_order.get(g.priority, 99)
        )

        for goal in sorted_goals[:3]:  # 上位3件
            desc = goal.goal_description or ""
            lines.append(f"- **{goal.goal_title}** ({goal.priority}): {desc}")

        return "\n".join(lines)

    def _build_response_guidelines(
        self, traits: List[CognitiveTrait]
    ) -> List[str]:
        """応答ガイドライン生成"""
        guidelines = [
            "複数の選択肢を提示する",
            "構造化された情報提示",
            "肯定的な表現を使用",
            "一貫性を保つ",
        ]

        # 認知特性から追加ガイドライン抽出
        for trait in traits[:10]:  # 上位10件チェック
            if trait.handling_strategy:
                if "approach" in trait.handling_strategy:
                    approach = trait.handling_strategy["approach"]
                    if isinstance(approach, str) and approach not in guidelines:
                        guidelines.append(approach)

        return list(set(guidelines))  # 重複除去

    def _estimate_tokens(self, text: str) -> int:
        """
        トークン数推定（簡易版）

        日本語: 1文字 ≈ 2トークン
        英語: 1文字 ≈ 0.5トークン
        """
        if not text:
            return 0

        # 日本語文字数カウント
        japanese_chars = sum(1 for c in text if ord(c) > 127)
        # 英語文字数カウント
        english_chars = len(text) - japanese_chars

        # トークン推定
        estimated_tokens = int(japanese_chars * 2 + english_chars * 0.5)

        return estimated_tokens

    def clear_cache(self, user_id: Optional[str] = None):
        """
        キャッシュクリア

        Args:
            user_id: 特定ユーザーのキャッシュをクリア（Noneの場合は全クリア）
        """
        if user_id:
            if user_id in self.cache:
                del self.cache[user_id]
                logger.info(f"Cache cleared for user: {user_id}")
        else:
            self.cache.clear()
            logger.info("All cache cleared")
