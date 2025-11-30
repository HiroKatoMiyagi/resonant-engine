"""Contradiction Detector Service - Sprint 11

This service detects contradictions between new intents and past decisions:
- Technology stack contradictions (e.g., PostgreSQL → SQLite)
- Policy shifts (e.g., microservice → monolith within 2 weeks)
- Duplicate work (similar intents with high Jaccard similarity)
- Dogma (unverified assumptions like "always", "never")
"""

import asyncpg
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID

from .models import Contradiction, IntentRelation

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """矛盾検出サービス / Contradiction Detection Service"""

    # 閾値設定 / Threshold Configuration
    TECH_STACK_KEYWORDS = {
        "database": ["postgresql", "mysql", "sqlite", "mongodb", "redis"],
        "framework": ["fastapi", "django", "flask", "express", "react", "vue", "nextjs"],
        "language": ["python", "javascript", "typescript", "go", "rust", "java"],
    }

    POLICY_SHIFT_WINDOW_DAYS = 14  # 2週間以内の方針転換を検出
    DUPLICATE_SIMILARITY_THRESHOLD = 0.85  # 類似度85%以上で重複判定

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def check_new_intent(
        self,
        user_id: str,
        new_intent_id: UUID,
        new_intent_content: str,
    ) -> List[Contradiction]:
        """
        新規Intent矛盾チェック / Check new intent for contradictions

        Args:
            user_id: ユーザーID
            new_intent_id: 新規IntentID
            new_intent_content: Intent内容

        Returns:
            List[Contradiction]: 検出された矛盾リスト
        """
        contradictions = []

        # 1. 技術スタック矛盾チェック
        tech_contradictions = await self._check_tech_stack_contradiction(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(tech_contradictions)

        # 2. 方針転換チェック
        policy_contradictions = await self._check_policy_shift(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(policy_contradictions)

        # 3. 重複作業チェック
        duplicate_contradictions = await self._check_duplicate_work(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(duplicate_contradictions)

        # 4. ドグマチェック
        dogma_contradictions = await self._check_dogma(
            user_id, new_intent_id, new_intent_content
        )
        contradictions.extend(dogma_contradictions)

        # 矛盾をDBに保存
        for contradiction in contradictions:
            await self._save_contradiction(contradiction)

        logger.info(
            f"Contradiction check for intent {new_intent_id}: "
            f"found {len(contradictions)} contradictions"
        )

        return contradictions

    async def _check_tech_stack_contradiction(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """技術スタック矛盾チェック / Technology Stack Contradiction Check"""
        contradictions = []

        # 新Intentから技術スタック抽出
        new_tech_stack = self._extract_tech_stack(new_intent_content)

        if not new_tech_stack:
            return contradictions

        # 過去のIntentを取得（技術スタック関連）
        async with self.pool.acquire() as conn:
            # Note: Assume 'intents' table exists from previous sprints
            past_intents = await conn.fetch(
                """
                SELECT id, intent_text as content, created_at
                FROM intents
                WHERE id != $1
                  AND (status IS NULL OR status != 'deprecated')
                ORDER BY created_at DESC
                LIMIT 50
            """,
                new_intent_id,
            )

        # 各過去Intentと比較
        for past_intent in past_intents:
            past_tech_stack = self._extract_tech_stack(past_intent["content"])

            # カテゴリごとに矛盾チェック
            for category, new_tech in new_tech_stack.items():
                if category in past_tech_stack:
                    past_tech = past_tech_stack[category]
                    if new_tech != past_tech:
                        # 矛盾検出！
                        contradictions.append(
                            Contradiction(
                                user_id=user_id,
                                new_intent_id=new_intent_id,
                                new_intent_content=new_intent_content,
                                conflicting_intent_id=past_intent["id"],
                                conflicting_intent_content=past_intent["content"],
                                contradiction_type="tech_stack",
                                confidence_score=0.9,
                                details={
                                    "category": category,
                                    "old_tech": past_tech,
                                    "new_tech": new_tech,
                                    "past_intent_date": past_intent[
                                        "created_at"
                                    ].isoformat(),
                                },
                            )
                        )

        return contradictions

    def _extract_tech_stack(self, content: str) -> Dict[str, str]:
        """技術スタック抽出（単純なキーワードマッチ）"""
        content_lower = content.lower()
        tech_stack = {}

        for category, keywords in self.TECH_STACK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    tech_stack[category] = keyword
                    break

        return tech_stack

    async def _check_policy_shift(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """方針転換チェック（簡易版）/ Policy Shift Check"""
        contradictions = []

        # 方針キーワード（対立するペア）
        policy_keywords = [
            ("microservice", "monolith"),
            ("async", "sync"),
            ("nosql", "sql"),
            ("serverless", "traditional"),
        ]

        # 新Intentから方針抽出
        content_lower = new_intent_content.lower()
        new_policy = None
        opposite_policy = None

        for keyword_a, keyword_b in policy_keywords:
            if keyword_a in content_lower:
                new_policy = keyword_a
                opposite_policy = keyword_b
                break
            elif keyword_b in content_lower:
                new_policy = keyword_b
                opposite_policy = keyword_a
                break

        if not new_policy:
            return contradictions

        # 過去2週間のIntentを検索
        async with self.pool.acquire() as conn:
            cutoff_date = datetime.now(timezone.utc) - timedelta(
                days=self.POLICY_SHIFT_WINDOW_DAYS
            )
            past_intents = await conn.fetch(
                """
                SELECT id, intent_text as content, created_at
                FROM intents
                WHERE id != $1
                  AND created_at > $2
                  AND (status IS NULL OR status != 'deprecated')
                ORDER BY created_at DESC
            """,
                new_intent_id,
                cutoff_date,
            )

        # 方針転換チェック
        for past_intent in past_intents:
            past_content_lower = past_intent["content"].lower()
            if opposite_policy in past_content_lower:
                # 方針転換検出！
                days_elapsed = (
                    datetime.now(timezone.utc) - past_intent["created_at"]
                ).days
                contradictions.append(
                    Contradiction(
                        user_id=user_id,
                        new_intent_id=new_intent_id,
                        new_intent_content=new_intent_content,
                        conflicting_intent_id=past_intent["id"],
                        conflicting_intent_content=past_intent["content"],
                        contradiction_type="policy_shift",
                        confidence_score=0.85,
                        details={
                            "old_policy": opposite_policy,
                            "new_policy": new_policy,
                            "days_elapsed": days_elapsed,
                        },
                    )
                )

        return contradictions

    async def _check_duplicate_work(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """重複作業チェック（Jaccard係数による類似度計算）/ Duplicate Work Check"""
        contradictions = []

        # 過去の完了/進行中Intentを取得
        async with self.pool.acquire() as conn:
            past_intents = await conn.fetch(
                """
                SELECT id, intent_text as content, created_at, status
                FROM intents
                WHERE id != $1
                  AND (status = 'completed' OR status = 'in_progress')
                ORDER BY created_at DESC
                LIMIT 30
            """,
                new_intent_id,
            )

        # 類似度計算（Jaccard係数）
        new_tokens = set(new_intent_content.lower().split())

        for past_intent in past_intents:
            past_tokens = set(past_intent["content"].lower().split())
            similarity = self._jaccard_similarity(new_tokens, past_tokens)

            if similarity >= self.DUPLICATE_SIMILARITY_THRESHOLD:
                # 重複検出！
                contradictions.append(
                    Contradiction(
                        user_id=user_id,
                        new_intent_id=new_intent_id,
                        new_intent_content=new_intent_content,
                        conflicting_intent_id=past_intent["id"],
                        conflicting_intent_content=past_intent["content"],
                        contradiction_type="duplicate",
                        confidence_score=similarity,
                        details={
                            "similarity": similarity,
                            "past_intent_status": past_intent["status"],
                            "past_intent_date": past_intent["created_at"].isoformat(),
                        },
                    )
                )

        return contradictions

    def _jaccard_similarity(self, set_a: set, set_b: set) -> float:
        """Jaccard係数計算 / Calculate Jaccard Similarity"""
        if not set_a or not set_b:
            return 0.0

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    async def _check_dogma(
        self, user_id: str, new_intent_id: UUID, new_intent_content: str
    ) -> List[Contradiction]:
        """ドグマ（未検証前提）チェック（簡易版）/ Dogma (Unverified Assumption) Check"""
        contradictions = []

        # ドグマキーワード
        dogma_keywords = [
            "always",
            "never",
            "every",
            "all users",
            "常に",
            "必ず",
            "絶対",
        ]

        content_lower = new_intent_content.lower()
        detected_dogmas = [kw for kw in dogma_keywords if kw in content_lower]

        if detected_dogmas:
            contradictions.append(
                Contradiction(
                    user_id=user_id,
                    new_intent_id=new_intent_id,
                    new_intent_content=new_intent_content,
                    contradiction_type="dogma",
                    confidence_score=0.7,
                    details={
                        "detected_keywords": detected_dogmas,
                        "warning": "未検証の前提が含まれている可能性があります",
                    },
                )
            )

        return contradictions

    async def _save_contradiction(self, contradiction: Contradiction):
        """矛盾をDBに保存 / Save contradiction to database"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO contradictions
                    (user_id, new_intent_id, new_intent_content, conflicting_intent_id,
                     conflicting_intent_content, contradiction_type, confidence_score,
                     details, resolution_status, detected_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11)
            """,
                contradiction.user_id,
                contradiction.new_intent_id,
                contradiction.new_intent_content,
                contradiction.conflicting_intent_id,
                contradiction.conflicting_intent_content,
                contradiction.contradiction_type,
                contradiction.confidence_score,
                json.dumps(contradiction.details),
                contradiction.resolution_status,
                contradiction.detected_at,
                contradiction.created_at,
            )

    async def resolve_contradiction(
        self,
        contradiction_id: UUID,
        resolution_action: str,
        resolution_rationale: str,
        resolved_by: str,
    ):
        """矛盾を解決 / Resolve contradiction"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE contradictions
                SET resolution_status = 'approved',
                    resolution_action = $1,
                    resolution_rationale = $2,
                    resolved_at = NOW(),
                    resolved_by = $3
                WHERE id = $4
            """,
                resolution_action,
                resolution_rationale,
                resolved_by,
                contradiction_id,
            )

            logger.info(
                f"Contradiction {contradiction_id} resolved as {resolution_action}"
            )

    async def get_pending_contradictions(self, user_id: str) -> List[Contradiction]:
        """未解決矛盾を取得 / Get pending contradictions"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM contradictions
                WHERE user_id = $1
                  AND resolution_status = 'pending'
                ORDER BY detected_at DESC
                LIMIT 20
            """,
                user_id,
            )

        contradictions = []
        for row in rows:
            row_dict = dict(row)
            if isinstance(row_dict["details"], str):
                row_dict["details"] = json.loads(row_dict["details"])
            contradictions.append(Contradiction(**row_dict))

        return contradictions
