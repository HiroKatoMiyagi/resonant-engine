"""
Semantic Bridge Service - Main orchestration layer

Coordinates event processing through extraction, inference, and construction
to produce semantic memory units.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from .constructor import MemoryUnitConstructor
from .extractor import SemanticExtractor
from .inferencer import TypeProjectInferencer
from .models import EventContext, InferenceResult, MemoryUnit


class MemoryPersistenceRepository(Protocol):
    """Protocol for memory persistence operations"""

    async def create(self, memory_unit: MemoryUnit) -> MemoryUnit:
        """Create a new memory unit"""
        ...


class SemanticBridgeService:
    """Semantic Bridge のメインサービス"""

    def __init__(
        self,
        memory_repo: Optional[MemoryPersistenceRepository] = None,
        semantic_extractor: Optional[SemanticExtractor] = None,
        inferencer: Optional[TypeProjectInferencer] = None,
        constructor: Optional[MemoryUnitConstructor] = None,
    ) -> None:
        """
        Initialize the Semantic Bridge Service

        Args:
            memory_repo: Repository for persisting memory units
            semantic_extractor: Extractor for meaning extraction
            inferencer: Inferencer for type and project inference
            constructor: Constructor for building memory units
        """
        self.memory_repo = memory_repo
        self.semantic_extractor = semantic_extractor or SemanticExtractor()
        self.inferencer = inferencer or TypeProjectInferencer()
        self.constructor = constructor or MemoryUnitConstructor(memory_repo)

    async def process_event(self, event: EventContext) -> MemoryUnit:
        """
        イベントを処理してメモリユニットを生成・保存

        Args:
            event: 処理対象のイベント文脈

        Returns:
            生成されたMemoryUnit

        Raises:
            ValueError: バリデーションエラー
            Exception: 保存エラー
        """
        start_time = time.time()

        # 1. 意味抽出
        extracted = self.semantic_extractor.extract_meaning(event)

        # 2. タイプ・プロジェクト推論
        inference = self.inferencer.infer(event, extracted)

        # 3. メモリユニット構築
        memory_unit = await self.constructor.construct(extracted, inference)

        # 4. 保存（リポジトリが設定されている場合）
        if self.memory_repo:
            saved_unit = await self.memory_repo.create(memory_unit)
        else:
            saved_unit = memory_unit

        # 5. 処理時間の記録
        processing_time_ms = (time.time() - start_time) * 1000

        # 6. ログ記録
        self._log_conversion(event, saved_unit, inference, processing_time_ms)

        return saved_unit

    def process_event_sync(self, event: EventContext) -> MemoryUnit:
        """
        同期版のイベント処理（保存なし）

        Args:
            event: 処理対象のイベント文脈

        Returns:
            生成されたMemoryUnit
        """
        start_time = time.time()

        # 1. 意味抽出
        extracted = self.semantic_extractor.extract_meaning(event)

        # 2. タイプ・プロジェクト推論
        inference = self.inferencer.infer(event, extracted)

        # 3. メモリユニット構築（同期版）
        memory_unit = self.constructor.construct_sync(extracted, inference)

        # 4. 処理時間の記録
        processing_time_ms = (time.time() - start_time) * 1000

        # 5. ログ記録
        self._log_conversion(event, memory_unit, inference, processing_time_ms)

        return memory_unit

    async def process_events_batch(
        self, events: List[EventContext]
    ) -> List[MemoryUnit]:
        """
        複数イベントのバッチ処理

        Args:
            events: 処理対象のイベントリスト

        Returns:
            生成されたMemoryUnitのリスト
        """
        results = []
        for event in events:
            try:
                memory_unit = await self.process_event(event)
                results.append(memory_unit)
            except Exception as e:
                print(f"Error processing event {event.intent_id}: {e}")
                # エラーが発生しても処理を継続
                continue

        return results

    def _log_conversion(
        self,
        event: EventContext,
        unit: MemoryUnit,
        inference: InferenceResult,
        processing_time_ms: float,
    ) -> None:
        """
        変換ログを記録

        Args:
            event: 元のイベント
            unit: 生成されたメモリユニット
            inference: 推論結果
            processing_time_ms: 処理時間（ミリ秒）
        """
        intent_text_preview = event.intent_text[:50]
        if len(event.intent_text) > 50:
            intent_text_preview += "..."

        print(
            f"""
        Semantic Bridge Conversion:
          Intent: {intent_text_preview}
          → Type: {unit.type.value} (confidence: {inference.confidence:.2f})
          → Project: {unit.project_id or 'None'} (confidence: {inference.project_confidence:.2f})
          → Tags: {', '.join(unit.tags[:5])}{'...' if len(unit.tags) > 5 else ''}
          → Memory ID: {unit.id}
          → Processing Time: {processing_time_ms:.2f}ms
        """
        )

    def get_extractor(self) -> SemanticExtractor:
        """Get the semantic extractor instance"""
        return self.semantic_extractor

    def get_inferencer(self) -> TypeProjectInferencer:
        """Get the type project inferencer instance"""
        return self.inferencer

    def get_constructor(self) -> MemoryUnitConstructor:
        """Get the memory unit constructor instance"""
        return self.constructor

    def update_extractor(self, extractor: SemanticExtractor) -> None:
        """Update the semantic extractor instance"""
        self.semantic_extractor = extractor

    def update_inferencer(self, inferencer: TypeProjectInferencer) -> None:
        """Update the type project inferencer instance"""
        self.inferencer = inferencer

    def update_constructor(self, constructor: MemoryUnitConstructor) -> None:
        """Update the memory unit constructor instance"""
        self.constructor = constructor
