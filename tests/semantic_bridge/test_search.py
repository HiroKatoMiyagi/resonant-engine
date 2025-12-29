"""
Unit tests for Memory Search Repository
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.semantic.models import (
    EmotionState,
    MemorySearchQuery,
    MemoryType,
    MemoryUnit,
)
from app.services.semantic.repositories import InMemoryUnitRepository


class TestMemorySearchRepository:
    """Tests for InMemoryUnitRepository search functionality"""

    @pytest.fixture
    def repo(self):
        """Create an InMemoryUnitRepository instance"""
        return InMemoryUnitRepository()

    @pytest.fixture
    async def populated_repo(self, repo):
        """Create repository with sample data"""
        # Create diverse memory units
        units = [
            MemoryUnit(
                user_id="hiroki",
                project_id="resonant_engine",
                type=MemoryType.DESIGN_NOTE,
                title="Design 1",
                content="Content 1",
                tags=["design_note", "focused", "bridge"],
                ci_level=30,
                emotion_state=EmotionState.FOCUSED,
            ),
            MemoryUnit(
                user_id="hiroki",
                project_id="resonant_engine",
                type=MemoryType.SESSION_SUMMARY,
                title="Session 1",
                content="Content 2",
                tags=["session_summary", "calm"],
                ci_level=20,
                emotion_state=EmotionState.CALM,
            ),
            MemoryUnit(
                user_id="hiroki",
                project_id="memory_system",
                type=MemoryType.CRISIS_LOG,
                title="Crisis 1",
                content="Content 3",
                tags=["crisis_log", "crisis"],
                ci_level=75,
                emotion_state=EmotionState.CRISIS,
            ),
            MemoryUnit(
                user_id="hiroki",
                project_id="memory_system",
                type=MemoryType.DESIGN_NOTE,
                title="Design 2",
                content="PostgreSQL schema",
                tags=["design_note", "postgresql"],
                ci_level=35,
                emotion_state=EmotionState.FOCUSED,
            ),
            MemoryUnit(
                user_id="hiroki",
                project_id="postgres_implementation",
                type=MemoryType.PROJECT_MILESTONE,
                title="Milestone 1",
                content="Content 5",
                tags=["milestone", "excited"],
                ci_level=10,
                emotion_state=EmotionState.EXCITED,
            ),
        ]

        for unit in units:
            await repo.create(unit)

        return repo

    @pytest.mark.asyncio
    async def test_search_by_project(self, populated_repo):
        """Test search by single project ID"""
        query = MemorySearchQuery(project_id="resonant_engine")
        results = await populated_repo.search(query)
        assert len(results) == 2
        assert all(u.project_id == "resonant_engine" for u in results)

    @pytest.mark.asyncio
    async def test_search_by_multiple_projects(self, populated_repo):
        """Test search by multiple project IDs"""
        query = MemorySearchQuery(project_ids=["resonant_engine", "memory_system"])
        results = await populated_repo.search(query)
        assert len(results) == 4

    @pytest.mark.asyncio
    async def test_search_by_type(self, populated_repo):
        """Test search by single memory type"""
        query = MemorySearchQuery(type=MemoryType.DESIGN_NOTE)
        results = await populated_repo.search(query)
        assert len(results) == 2
        assert all(u.type == MemoryType.DESIGN_NOTE for u in results)

    @pytest.mark.asyncio
    async def test_search_by_multiple_types(self, populated_repo):
        """Test search by multiple memory types"""
        query = MemorySearchQuery(
            types=[MemoryType.DESIGN_NOTE, MemoryType.SESSION_SUMMARY]
        )
        results = await populated_repo.search(query)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_by_tags_any(self, populated_repo):
        """Test search by tags with 'any' mode"""
        query = MemorySearchQuery(tags=["bridge", "postgresql"], tag_mode="any")
        results = await populated_repo.search(query)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_tags_all(self, populated_repo):
        """Test search by tags with 'all' mode"""
        query = MemorySearchQuery(tags=["design_note", "focused"], tag_mode="all")
        results = await populated_repo.search(query)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_ci_level_min(self, populated_repo):
        """Test search by minimum CI level"""
        query = MemorySearchQuery(ci_level_min=35)
        results = await populated_repo.search(query)
        assert len(results) == 2
        assert all(u.ci_level >= 35 for u in results)

    @pytest.mark.asyncio
    async def test_search_by_ci_level_max(self, populated_repo):
        """Test search by maximum CI level"""
        query = MemorySearchQuery(ci_level_max=30)
        results = await populated_repo.search(query)
        assert len(results) == 3
        assert all(u.ci_level <= 30 for u in results)

    @pytest.mark.asyncio
    async def test_search_by_ci_level_range(self, populated_repo):
        """Test search by CI level range"""
        query = MemorySearchQuery(ci_level_min=20, ci_level_max=35)
        results = await populated_repo.search(query)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_by_emotion_state(self, populated_repo):
        """Test search by emotion states"""
        query = MemorySearchQuery(emotion_states=[EmotionState.FOCUSED])
        results = await populated_repo.search(query)
        assert len(results) == 2
        assert all(u.emotion_state == EmotionState.FOCUSED for u in results)

    @pytest.mark.asyncio
    async def test_search_text_query(self, populated_repo):
        """Test text search in title and content"""
        query = MemorySearchQuery(text_query="PostgreSQL")
        results = await populated_repo.search(query)
        assert len(results) == 1
        assert "PostgreSQL" in results[0].content

    @pytest.mark.asyncio
    async def test_search_pagination(self, populated_repo):
        """Test search with pagination"""
        query = MemorySearchQuery(limit=2, offset=0)
        results = await populated_repo.search(query)
        assert len(results) == 2

        query2 = MemorySearchQuery(limit=2, offset=2)
        results2 = await populated_repo.search(query2)
        assert len(results2) == 2

    @pytest.mark.asyncio
    async def test_search_sorting_by_ci_level(self, populated_repo):
        """Test sorting by CI level"""
        query = MemorySearchQuery(sort_by="ci_level", sort_order="desc")
        results = await populated_repo.search(query)
        ci_levels = [u.ci_level for u in results]
        assert ci_levels == sorted(ci_levels, reverse=True)

    @pytest.mark.asyncio
    async def test_search_count(self, populated_repo):
        """Test count of search results"""
        query = MemorySearchQuery(project_id="resonant_engine")
        count = await populated_repo.count(query)
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_projects(self, populated_repo):
        """Test getting project statistics"""
        projects = await populated_repo.get_projects()
        assert len(projects) == 3
        project_ids = [p["project_id"] for p in projects]
        assert "resonant_engine" in project_ids
        assert "memory_system" in project_ids

    @pytest.mark.asyncio
    async def test_get_tags(self, populated_repo):
        """Test getting tag statistics"""
        tags = await populated_repo.get_tags()
        tag_names = [t["tag"] for t in tags]
        assert "design_note" in tag_names
        assert "focused" in tag_names

    @pytest.mark.asyncio
    async def test_find_similar(self, repo):
        """Test finding similar memory units"""
        now = datetime.now(timezone.utc)
        unit = MemoryUnit(
            type=MemoryType.SESSION_SUMMARY,
            title="Test Title",
            content="Content",
            started_at=now,
        )
        await repo.create(unit)

        # Find with same title and close timestamp
        similar = await repo.find_similar("Test Title", now, time_threshold_minutes=5)
        assert similar is not None
        assert similar.title == "Test Title"

    @pytest.mark.asyncio
    async def test_combined_filters(self, populated_repo):
        """Test search with multiple combined filters"""
        query = MemorySearchQuery(
            project_id="memory_system",
            type=MemoryType.DESIGN_NOTE,
            ci_level_min=30,
        )
        results = await populated_repo.search(query)
        assert len(results) == 1
        assert results[0].project_id == "memory_system"
        assert results[0].type == MemoryType.DESIGN_NOTE

    @pytest.mark.asyncio
    async def test_empty_results(self, populated_repo):
        """Test search with no matching results"""
        query = MemorySearchQuery(project_id="nonexistent")
        results = await populated_repo.search(query)
        assert len(results) == 0
