"""
Memory Unit Constructor - Builds and validates memory units

Constructs MemoryUnit objects from extracted data and inference results,
with validation and duplicate checking.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Protocol

from .models import InferenceResult, MemoryUnit


class MemoryRepository(Protocol):
    """Protocol for memory repository operations"""

    async def find_similar(
        self,
        title: str,
        timestamp: Optional[datetime],
        time_threshold_minutes: int = 5,
    ) -> Optional[MemoryUnit]:
        """Find similar memory units"""
        ...


class MemoryUnitConstructor:
    """メモリユニットの構築とバリデーション"""

    def __init__(self, memory_repo: Optional[MemoryRepository] = None) -> None:
        """
        Initialize constructor

        Args:
            memory_repo: Optional memory repository for duplicate checking
        """
        self.memory_repo = memory_repo

    async def construct(
        self, extracted: Dict[str, Any], inference: InferenceResult
    ) -> MemoryUnit:
        """
        メモリユニットを構築

        Args:
            extracted: 抽出された意味情報
            inference: 推論結果

        Returns:
            構築されたMemoryUnit

        Raises:
            ValueError: バリデーションエラー
        """
        # MemoryUnitオブジェクト生成
        memory_unit = MemoryUnit(
            user_id="hiroki",
            project_id=inference.project_id,
            type=inference.memory_type,
            title=extracted["title"],
            content=extracted["content"],
            content_raw=extracted.get("content_raw"),
            tags=inference.tags,
            ci_level=extracted.get("ci_level"),
            emotion_state=inference.emotion_state,
            started_at=extracted.get("started_at"),
            metadata={
                **extracted.get("metadata", {}),
                "inference_confidence": inference.confidence,
                "inference_reasoning": inference.reasoning,
                "project_confidence": inference.project_confidence,
            },
        )

        # バリデーション
        self._validate(memory_unit)

        # 重複チェック（リポジトリが設定されている場合）
        if self.memory_repo:
            await self._check_duplicate(memory_unit)

        return memory_unit

    def _validate(self, unit: MemoryUnit) -> None:
        """
        バリデーション

        Args:
            unit: 検証対象のMemoryUnit

        Raises:
            ValueError: バリデーションエラー
        """
        # タイトルの検証
        if not unit.title:
            raise ValueError("Title is required")

        if len(unit.title) > 200:
            raise ValueError("Title too long (max 200 chars)")

        # コンテンツの検証
        if not unit.content:
            raise ValueError("Content is required")

        if len(unit.content) > 100000:  # 100KB制限
            raise ValueError("Content too long (max 100000 chars)")

        # CI Levelの検証
        if unit.ci_level is not None:
            if not (0 <= unit.ci_level <= 100):
                raise ValueError("CI level must be 0-100")

        # タグの検証
        if len(unit.tags) > 20:
            raise ValueError("Too many tags (max 20)")

        for tag in unit.tags:
            if len(tag) > 50:
                raise ValueError(f"Tag too long: {tag[:20]}... (max 50 chars)")

        # プロジェクトIDの検証
        if unit.project_id and len(unit.project_id) > 100:
            raise ValueError("Project ID too long (max 100 chars)")

        # メタデータサイズの検証
        import json

        metadata_size = len(json.dumps(unit.metadata, default=str))
        if metadata_size > 50000:  # 50KB制限
            raise ValueError("Metadata too large (max 50KB)")

    async def _check_duplicate(self, unit: MemoryUnit) -> None:
        """
        重複チェック（同一内容の記録を防ぐ）

        Args:
            unit: チェック対象のMemoryUnit

        Note:
            重複が見つかった場合はログを記録するが、エラーにはしない
        """
        if not self.memory_repo:
            return

        try:
            existing = await self.memory_repo.find_similar(
                title=unit.title,
                timestamp=unit.started_at,
                time_threshold_minutes=5,
            )

            if existing:
                print(f"Warning: Similar memory found: {existing.id}")
        except Exception as e:
            # 重複チェックのエラーは致命的ではない
            print(f"Warning: Duplicate check failed: {e}")

    def construct_sync(
        self, extracted: Dict[str, Any], inference: InferenceResult
    ) -> MemoryUnit:
        """
        同期版のメモリユニット構築（重複チェックなし）

        Args:
            extracted: 抽出された意味情報
            inference: 推論結果

        Returns:
            構築されたMemoryUnit

        Raises:
            ValueError: バリデーションエラー
        """
        # MemoryUnitオブジェクト生成
        memory_unit = MemoryUnit(
            user_id="hiroki",
            project_id=inference.project_id,
            type=inference.memory_type,
            title=extracted["title"],
            content=extracted["content"],
            content_raw=extracted.get("content_raw"),
            tags=inference.tags,
            ci_level=extracted.get("ci_level"),
            emotion_state=inference.emotion_state,
            started_at=extracted.get("started_at"),
            metadata={
                **extracted.get("metadata", {}),
                "inference_confidence": inference.confidence,
                "inference_reasoning": inference.reasoning,
                "project_confidence": inference.project_confidence,
            },
        )

        # バリデーション
        self._validate(memory_unit)

        return memory_unit
