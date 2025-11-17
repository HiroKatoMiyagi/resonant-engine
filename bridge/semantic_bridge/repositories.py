"""
Memory Repositories - Abstract interfaces and in-memory implementations

Provides repository interfaces and in-memory implementations for testing.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from .models import MemorySearchQuery, MemoryUnit


class MemoryUnitRepository(ABC):
    """Abstract base class for memory unit repository"""

    @abstractmethod
    async def create(self, memory_unit: MemoryUnit) -> MemoryUnit:
        """Create a new memory unit"""
        pass

    @abstractmethod
    async def get_by_id(self, memory_id: UUID) -> Optional[MemoryUnit]:
        """Get memory unit by ID"""
        pass

    @abstractmethod
    async def find_similar(
        self,
        title: str,
        timestamp: Optional[datetime],
        time_threshold_minutes: int = 5,
    ) -> Optional[MemoryUnit]:
        """Find similar memory units"""
        pass

    @abstractmethod
    async def search(self, query: MemorySearchQuery) -> List[MemoryUnit]:
        """Search memory units"""
        pass

    @abstractmethod
    async def count(self, query: MemorySearchQuery) -> int:
        """Count matching memory units"""
        pass

    @abstractmethod
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get project statistics"""
        pass

    @abstractmethod
    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get tag statistics"""
        pass

    @abstractmethod
    async def update(self, memory_unit: MemoryUnit) -> MemoryUnit:
        """Update a memory unit"""
        pass

    @abstractmethod
    async def delete(self, memory_id: UUID) -> bool:
        """Delete a memory unit"""
        pass


class InMemoryUnitRepository(MemoryUnitRepository):
    """In-memory implementation of memory unit repository for testing"""

    def __init__(self) -> None:
        """Initialize empty storage"""
        self._storage: Dict[UUID, MemoryUnit] = {}

    async def create(self, memory_unit: MemoryUnit) -> MemoryUnit:
        """Create a new memory unit"""
        self._storage[memory_unit.id] = memory_unit
        return memory_unit

    async def get_by_id(self, memory_id: UUID) -> Optional[MemoryUnit]:
        """Get memory unit by ID"""
        return self._storage.get(memory_id)

    async def find_similar(
        self,
        title: str,
        timestamp: Optional[datetime],
        time_threshold_minutes: int = 5,
    ) -> Optional[MemoryUnit]:
        """Find similar memory units"""
        for unit in self._storage.values():
            # タイトルが同じ
            if unit.title == title:
                # タイムスタンプが範囲内
                if timestamp and unit.started_at:
                    time_diff = abs((unit.started_at - timestamp).total_seconds())
                    if time_diff <= time_threshold_minutes * 60:
                        return unit
                elif not timestamp and not unit.started_at:
                    return unit

        return None

    async def search(self, query: MemorySearchQuery) -> List[MemoryUnit]:
        """Search memory units"""
        results = list(self._storage.values())

        # User IDフィルタ
        results = [u for u in results if u.user_id == query.user_id]

        # プロジェクトフィルタ
        if query.project_id:
            results = [u for u in results if u.project_id == query.project_id]
        elif query.project_ids:
            results = [u for u in results if u.project_id in query.project_ids]

        # タイプフィルタ
        if query.type:
            results = [u for u in results if u.type == query.type]
        elif query.types:
            results = [u for u in results if u.type in query.types]

        # タグフィルタ
        if query.tags:
            if query.tag_mode == "all":
                results = [u for u in results if all(tag in u.tags for tag in query.tags)]
            else:  # any
                results = [u for u in results if any(tag in u.tags for tag in query.tags)]

        # 時間範囲フィルタ
        if query.date_from:
            results = [u for u in results if u.created_at >= query.date_from]
        if query.date_to:
            results = [u for u in results if u.created_at <= query.date_to]

        # CI Levelフィルタ
        if query.ci_level_min is not None:
            results = [
                u for u in results if u.ci_level is not None and u.ci_level >= query.ci_level_min
            ]
        if query.ci_level_max is not None:
            results = [
                u for u in results if u.ci_level is not None and u.ci_level <= query.ci_level_max
            ]

        # 感情状態フィルタ
        if query.emotion_states:
            results = [u for u in results if u.emotion_state in query.emotion_states]

        # テキスト検索
        if query.text_query:
            query_lower = query.text_query.lower()
            results = [
                u
                for u in results
                if query_lower in u.title.lower() or query_lower in u.content.lower()
            ]

        # ソート
        if query.sort_by == "created_at":
            results.sort(key=lambda u: u.created_at, reverse=(query.sort_order == "desc"))
        elif query.sort_by == "ci_level":
            results.sort(
                key=lambda u: u.ci_level or 0,
                reverse=(query.sort_order == "desc"),
            )
        elif query.sort_by == "updated_at":
            results.sort(key=lambda u: u.updated_at, reverse=(query.sort_order == "desc"))

        # ページング
        return results[query.offset : query.offset + query.limit]

    async def count(self, query: MemorySearchQuery) -> int:
        """Count matching memory units"""
        # 検索と同じロジック、ただしページングなし
        results = list(self._storage.values())

        # User IDフィルタ
        results = [u for u in results if u.user_id == query.user_id]

        # プロジェクトフィルタ
        if query.project_id:
            results = [u for u in results if u.project_id == query.project_id]
        elif query.project_ids:
            results = [u for u in results if u.project_id in query.project_ids]

        # タイプフィルタ
        if query.type:
            results = [u for u in results if u.type == query.type]
        elif query.types:
            results = [u for u in results if u.type in query.types]

        # タグフィルタ
        if query.tags:
            if query.tag_mode == "all":
                results = [u for u in results if all(tag in u.tags for tag in query.tags)]
            else:  # any
                results = [u for u in results if any(tag in u.tags for tag in query.tags)]

        # 時間範囲フィルタ
        if query.date_from:
            results = [u for u in results if u.created_at >= query.date_from]
        if query.date_to:
            results = [u for u in results if u.created_at <= query.date_to]

        # CI Levelフィルタ
        if query.ci_level_min is not None:
            results = [
                u for u in results if u.ci_level is not None and u.ci_level >= query.ci_level_min
            ]
        if query.ci_level_max is not None:
            results = [
                u for u in results if u.ci_level is not None and u.ci_level <= query.ci_level_max
            ]

        # 感情状態フィルタ
        if query.emotion_states:
            results = [u for u in results if u.emotion_state in query.emotion_states]

        # テキスト検索
        if query.text_query:
            query_lower = query.text_query.lower()
            results = [
                u
                for u in results
                if query_lower in u.title.lower() or query_lower in u.content.lower()
            ]

        return len(results)

    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get project statistics"""
        project_stats: Dict[str, Dict[str, Any]] = {}

        for unit in self._storage.values():
            if unit.project_id:
                if unit.project_id not in project_stats:
                    project_stats[unit.project_id] = {
                        "project_id": unit.project_id,
                        "memory_count": 0,
                        "latest_memory_at": unit.created_at,
                    }

                project_stats[unit.project_id]["memory_count"] += 1
                if unit.created_at > project_stats[unit.project_id]["latest_memory_at"]:
                    project_stats[unit.project_id]["latest_memory_at"] = unit.created_at

        return list(project_stats.values())

    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get tag statistics"""
        tag_counts: Dict[str, int] = {}

        for unit in self._storage.values():
            for tag in unit.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return [{"tag": tag, "count": count} for tag, count in tag_counts.items()]

    async def update(self, memory_unit: MemoryUnit) -> MemoryUnit:
        """Update a memory unit"""
        if memory_unit.id not in self._storage:
            raise ValueError(f"Memory unit not found: {memory_unit.id}")

        memory_unit.updated_at = datetime.now(timezone.utc)
        self._storage[memory_unit.id] = memory_unit
        return memory_unit

    async def delete(self, memory_id: UUID) -> bool:
        """Delete a memory unit"""
        if memory_id in self._storage:
            del self._storage[memory_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored memory units"""
        self._storage.clear()

    def get_all(self) -> List[MemoryUnit]:
        """Get all stored memory units"""
        return list(self._storage.values())
