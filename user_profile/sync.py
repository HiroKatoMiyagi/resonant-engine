"""
CLAUDE.md Sync Service

Sprint 8: User Profile & Persistent Context
CLAUDE.mdをパースしてDBに同期
"""

import asyncpg
import logging
from typing import Dict, Any

from .claude_md_parser import ClaudeMdParser
from .repository import UserProfileRepository
from .models import (
    UserProfile,
    CognitiveTrait,
    FamilyMember,
    UserGoal,
    ResonantConcept,
)

logger = logging.getLogger(__name__)


class ClaudeMdSync:
    """CLAUDE.md同期サービス"""

    def __init__(self, pool: asyncpg.Pool, claude_md_path: str = "CLAUDE.md"):
        self.pool = pool
        self.parser = ClaudeMdParser(claude_md_path)
        self.repo = UserProfileRepository(pool)

    async def sync(self) -> Dict[str, Any]:
        """
        CLAUDE.mdをパースしてDBに同期

        Returns:
            Dict: 同期結果 {"status": "ok"|"error", "counts": {...}, "message": "..."}
        """
        logger.info("Starting CLAUDE.md sync...")

        try:
            # パース
            parsed = self.parser.parse()
            logger.info("✅ CLAUDE.md parsed successfully")

            # プロフィール同期
            profile = UserProfile(**parsed.profile)
            await self.repo.create_or_update_profile(profile)
            logger.info(f"✅ Profile synced: {profile.user_id}")

            # 認知特性同期（既存削除→新規挿入）
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM cognitive_traits WHERE user_id = $1", profile.user_id
                )

            for trait_data in parsed.cognitive_traits:
                trait = CognitiveTrait(**trait_data)
                await self.repo.add_cognitive_trait(trait)
            logger.info(
                f"✅ Cognitive traits synced: {len(parsed.cognitive_traits)} items"
            )

            # 家族同期（既存削除→新規挿入）
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM family_members WHERE user_id = $1", profile.user_id
                )

            for member_data in parsed.family_members:
                member = FamilyMember(**member_data)
                await self.repo.add_family_member(member)
            logger.info(
                f"✅ Family members synced: {len(parsed.family_members)} items"
            )

            # 目標同期（既存削除→新規挿入）
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM user_goals WHERE user_id = $1", profile.user_id
                )

            for goal_data in parsed.goals:
                goal = UserGoal(**goal_data)
                await self.repo.add_goal(goal)
            logger.info(f"✅ Goals synced: {len(parsed.goals)} items")

            # Resonant概念同期（既存削除→新規挿入）
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM resonant_concepts WHERE user_id = $1",
                    profile.user_id,
                )

            for concept_data in parsed.resonant_concepts:
                concept = ResonantConcept(**concept_data)
                await self.repo.add_resonant_concept(concept)
            logger.info(
                f"✅ Resonant concepts synced: {len(parsed.resonant_concepts)} items"
            )

            # 最終同期時刻更新
            await self.repo.update_last_sync(profile.user_id)

            logger.info("✅ CLAUDE.md sync completed successfully")

            return {
                "status": "ok",
                "counts": {
                    "cognitive_traits": len(parsed.cognitive_traits),
                    "family_members": len(parsed.family_members),
                    "goals": len(parsed.goals),
                    "resonant_concepts": len(parsed.resonant_concepts),
                },
                "message": "Sync completed successfully",
            }

        except FileNotFoundError:
            error_msg = f"CLAUDE.md not found at: {self.parser.file_path}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        except Exception as e:
            error_msg = f"CLAUDE.md sync failed: {e}"
            logger.error(error_msg)
            return {"status": "error", "message": str(e)}
