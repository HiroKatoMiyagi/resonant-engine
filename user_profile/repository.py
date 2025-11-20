"""
User Profile Repository

Sprint 8: User Profile & Persistent Context
PostgreSQLへのCRUD操作
"""

import asyncpg
from typing import Optional, List
from datetime import datetime
import logging
import json

from .models import (
    UserProfile,
    CognitiveTrait,
    FamilyMember,
    UserGoal,
    ResonantConcept,
    UserProfileData,
)

logger = logging.getLogger(__name__)


class UserProfileRepository:
    """ユーザープロフィールリポジトリ"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_profile(self, user_id: str) -> Optional[UserProfileData]:
        """
        完全なユーザープロフィールを取得

        Args:
            user_id: ユーザーID

        Returns:
            UserProfileData: プロフィールデータ（見つからない場合はNone）
        """
        async with self.pool.acquire() as conn:
            # 基本プロフィール
            profile_row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1 AND is_active = TRUE",
                user_id,
            )

            if not profile_row:
                logger.warning(f"Profile not found for user: {user_id}")
                return None

            profile = UserProfile(**dict(profile_row))

            # 認知特性
            trait_rows = await conn.fetch(
                "SELECT * FROM cognitive_traits WHERE user_id = $1 ORDER BY importance_level DESC",
                user_id,
            )
            cognitive_traits = []
            for row in trait_rows:
                trait_dict = dict(row)
                if trait_dict.get('handling_strategy') and isinstance(trait_dict['handling_strategy'], str):
                    trait_dict['handling_strategy'] = json.loads(trait_dict['handling_strategy'])
                cognitive_traits.append(CognitiveTrait(**trait_dict))

            # 家族情報
            family_rows = await conn.fetch(
                "SELECT * FROM family_members WHERE user_id = $1", user_id
            )
            family_members = [FamilyMember(**dict(row)) for row in family_rows]

            # 目標
            goal_rows = await conn.fetch(
                "SELECT * FROM user_goals WHERE user_id = $1 AND status = 'active' ORDER BY priority DESC",
                user_id,
            )
            goals = [UserGoal(**dict(row)) for row in goal_rows]

            # Resonant概念
            concept_rows = await conn.fetch(
                "SELECT * FROM resonant_concepts WHERE user_id = $1 ORDER BY importance_level DESC",
                user_id,
            )
            resonant_concepts = []
            for row in concept_rows:
                concept_dict = dict(row)
                if concept_dict.get('parameters') and isinstance(concept_dict['parameters'], str):
                    concept_dict['parameters'] = json.loads(concept_dict['parameters'])
                resonant_concepts.append(ResonantConcept(**concept_dict))

            return UserProfileData(
                profile=profile,
                cognitive_traits=cognitive_traits,
                family_members=family_members,
                goals=goals,
                resonant_concepts=resonant_concepts,
            )

    async def create_or_update_profile(self, profile: UserProfile) -> UserProfile:
        """
        プロフィール作成または更新

        Args:
            profile: ユーザープロフィール

        Returns:
            UserProfile: 作成/更新されたプロフィール
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_profiles
                    (user_id, full_name, birth_date, location, is_active, encryption_key_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    birth_date = EXCLUDED.birth_date,
                    location = EXCLUDED.location,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
                RETURNING *
            """,
                profile.user_id,
                profile.full_name,
                profile.birth_date,
                profile.location,
                profile.is_active,
                profile.encryption_key_id,
            )

            return UserProfile(**dict(row))

    async def add_cognitive_trait(self, trait: CognitiveTrait) -> CognitiveTrait:
        """
        認知特性追加

        Args:
            trait: 認知特性

        Returns:
            CognitiveTrait: 追加された認知特性
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO cognitive_traits
                    (user_id, trait_type, trait_name, description, importance_level, handling_strategy)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                RETURNING *
            """,
                trait.user_id,
                trait.trait_type,
                trait.trait_name,
                trait.description,
                trait.importance_level,
                json.dumps(trait.handling_strategy) if trait.handling_strategy else None,
            )

            trait_dict = dict(row)
            if trait_dict.get('handling_strategy') and isinstance(trait_dict['handling_strategy'], str):
                trait_dict['handling_strategy'] = json.loads(trait_dict['handling_strategy'])
            return CognitiveTrait(**trait_dict)

    async def add_family_member(self, member: FamilyMember) -> FamilyMember:
        """
        家族メンバー追加

        Args:
            member: 家族メンバー

        Returns:
            FamilyMember: 追加された家族メンバー
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO family_members
                    (user_id, name, relationship, birth_date, encryption_key_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """,
                member.user_id,
                member.name,
                member.relationship,
                member.birth_date,
                member.encryption_key_id,
            )

            return FamilyMember(**dict(row))

    async def add_goal(self, goal: UserGoal) -> UserGoal:
        """
        目標追加

        Args:
            goal: ユーザー目標

        Returns:
            UserGoal: 追加された目標
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_goals
                    (user_id, goal_category, goal_title, goal_description,
                     priority, target_date, status, progress_percentage)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """,
                goal.user_id,
                goal.goal_category,
                goal.goal_title,
                goal.goal_description,
                goal.priority,
                goal.target_date,
                goal.status,
                goal.progress_percentage,
            )

            return UserGoal(**dict(row))

    async def add_resonant_concept(
        self, concept: ResonantConcept
    ) -> ResonantConcept:
        """
        Resonant概念追加

        Args:
            concept: Resonant概念

        Returns:
            ResonantConcept: 追加された概念
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO resonant_concepts
                    (user_id, concept_type, concept_name, definition, parameters, importance_level)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                RETURNING *
            """,
                concept.user_id,
                concept.concept_type,
                concept.concept_name,
                concept.definition,
                json.dumps(concept.parameters) if concept.parameters else None,
                concept.importance_level,
            )

            concept_dict = dict(row)
            if concept_dict.get('parameters') and isinstance(concept_dict['parameters'], str):
                concept_dict['parameters'] = json.loads(concept_dict['parameters'])
            return ResonantConcept(**concept_dict)

    async def update_last_sync(self, user_id: str) -> None:
        """
        最終同期時刻を更新

        Args:
            user_id: ユーザーID
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_profiles SET last_sync_at = NOW() WHERE user_id = $1",
                user_id,
            )
            logger.info(f"Updated last_sync_at for user: {user_id}")
