"""Tests for ContradictionDetector - Sprint 11 Day 2

Test Coverage:
- AC-01: Basic tech stack contradiction detection
- AC-04: Policy shift detection within 2 weeks
- AC-07: Duplicate work detection with high similarity
- AC-09: Jaccard similarity calculation
- AC-10: Dogma keyword detection
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.contradiction.detector import ContradictionDetector
from bridge.contradiction.models import Contradiction


class TestTechStackExtraction:
    """Test technology stack extraction"""

    def test_extract_tech_stack_database(self):
        """Test extracting database technology"""
        detector = ContradictionDetector(pool=MagicMock())
        
        content = "We should use PostgreSQL for the database"
        tech_stack = detector._extract_tech_stack(content)
        
        assert "database" in tech_stack
        assert tech_stack["database"] == "postgresql"

    def test_extract_tech_stack_framework(self):
        """Test extracting framework technology"""
        detector = ContradictionDetector(pool=MagicMock())
        
        content = "Let's build with FastAPI framework"
        tech_stack = detector._extract_tech_stack(content)
        
        assert "framework" in tech_stack
        assert tech_stack["framework"] == "fastapi"

    def test_extract_tech_stack_multiple_categories(self):
        """Test extracting multiple technology categories"""
        detector = ContradictionDetector(pool=MagicMock())
        
        content = "Use FastAPI framework with PostgreSQL database and Python language"
        tech_stack = detector._extract_tech_stack(content)
        
        assert len(tech_stack) == 3
        assert tech_stack["framework"] == "fastapi"
        assert tech_stack["database"] == "postgresql"
        assert tech_stack["language"] == "python"

    def test_extract_tech_stack_case_insensitive(self):
        """Test case-insensitive extraction"""
        detector = ContradictionDetector(pool=MagicMock())
        
        content = "Use POSTGRESQL and FASTAPI"
        tech_stack = detector._extract_tech_stack(content)
        
        assert tech_stack["database"] == "postgresql"
        assert tech_stack["framework"] == "fastapi"

    def test_extract_tech_stack_no_match(self):
        """Test when no technology keywords are found"""
        detector = ContradictionDetector(pool=MagicMock())
        
        content = "This is a general discussion about architecture"
        tech_stack = detector._extract_tech_stack(content)
        
        assert len(tech_stack) == 0


class TestJaccardSimilarity:
    """Test Jaccard similarity calculation - AC-09"""

    def test_jaccard_similarity_identical(self):
        """Test Jaccard similarity for identical sets"""
        detector = ContradictionDetector(pool=MagicMock())
        
        set_a = {"implement", "user", "login", "system"}
        set_b = {"implement", "user", "login", "system"}
        
        similarity = detector._jaccard_similarity(set_a, set_b)
        assert similarity == 1.0

    def test_jaccard_similarity_partial_overlap(self):
        """Test Jaccard similarity with partial overlap"""
        detector = ContradictionDetector(pool=MagicMock())
        
        # "implement user login authentication system" vs "implement user login system"
        # Common: implement, user, login, system (4 words)
        # Total unique: implement, user, login, authentication, system (5 words)
        # Jaccard = 4/5 = 0.8
        set_a = {"implement", "user", "login", "authentication", "system"}
        set_b = {"implement", "user", "login", "system"}
        
        similarity = detector._jaccard_similarity(set_a, set_b)
        assert similarity == pytest.approx(0.8, abs=0.01)

    def test_jaccard_similarity_no_overlap(self):
        """Test Jaccard similarity with no overlap"""
        detector = ContradictionDetector(pool=MagicMock())
        
        set_a = {"database", "postgresql"}
        set_b = {"frontend", "react"}
        
        similarity = detector._jaccard_similarity(set_a, set_b)
        assert similarity == 0.0

    def test_jaccard_similarity_empty_sets(self):
        """Test Jaccard similarity with empty sets"""
        detector = ContradictionDetector(pool=MagicMock())
        
        assert detector._jaccard_similarity(set(), set()) == 0.0
        assert detector._jaccard_similarity({"a"}, set()) == 0.0
        assert detector._jaccard_similarity(set(), {"b"}) == 0.0


class TestDogmaDetection:
    """Test dogma (unverified assumption) detection - AC-10, AC-11"""

    @pytest.mark.asyncio
    async def test_dogma_detection_english_keywords(self):
        """Test dogma detection with English keywords - AC-10"""
        detector = ContradictionDetector(pool=MagicMock())
        
        user_id = "hiroki"
        intent_id = uuid4()
        content = "All users always login before using the app"
        
        contradictions = await detector._check_dogma(user_id, intent_id, content)
        
        assert len(contradictions) == 1
        assert contradictions[0].contradiction_type == "dogma"
        assert contradictions[0].confidence_score == 0.7
        assert "always" in contradictions[0].details["detected_keywords"]

    @pytest.mark.asyncio
    async def test_dogma_detection_japanese_keywords(self):
        """Test dogma detection with Japanese keywords - AC-11"""
        detector = ContradictionDetector(pool=MagicMock())
        
        user_id = "hiroki"
        intent_id = uuid4()
        content = "ユーザーは必ずログインする"
        
        contradictions = await detector._check_dogma(user_id, intent_id, content)
        
        assert len(contradictions) == 1
        assert contradictions[0].contradiction_type == "dogma"
        assert "必ず" in contradictions[0].details["detected_keywords"]

    @pytest.mark.asyncio
    async def test_dogma_detection_multiple_keywords(self):
        """Test dogma detection with multiple keywords"""
        detector = ContradictionDetector(pool=MagicMock())
        
        user_id = "hiroki"
        intent_id = uuid4()
        content = "All users will never skip authentication and always use secure passwords"
        
        contradictions = await detector._check_dogma(user_id, intent_id, content)
        
        assert len(contradictions) == 1
        detected = contradictions[0].details["detected_keywords"]
        assert "never" in detected
        assert "always" in detected

    @pytest.mark.asyncio
    async def test_dogma_detection_no_keywords(self):
        """Test no dogma detection when keywords absent"""
        detector = ContradictionDetector(pool=MagicMock())
        
        user_id = "hiroki"
        intent_id = uuid4()
        content = "Users can optionally login to access premium features"
        
        contradictions = await detector._check_dogma(user_id, intent_id, content)
        
        assert len(contradictions) == 0


class TestContradictionDetectorIntegration:
    """Integration tests for ContradictionDetector"""

    @pytest.mark.asyncio
    async def test_check_new_intent_calls_all_checkers(self):
        """Test that check_new_intent calls all 4 detection methods"""
        mock_pool = MagicMock()
        detector = ContradictionDetector(pool=mock_pool)
        
        # Mock all checker methods
        with patch.object(detector, '_check_tech_stack_contradiction', new_callable=AsyncMock, return_value=[]) as mock_tech, \
             patch.object(detector, '_check_policy_shift', new_callable=AsyncMock, return_value=[]) as mock_policy, \
             patch.object(detector, '_check_duplicate_work', new_callable=AsyncMock, return_value=[]) as mock_duplicate, \
             patch.object(detector, '_check_dogma', new_callable=AsyncMock, return_value=[]) as mock_dogma, \
             patch.object(detector, '_save_contradiction', new_callable=AsyncMock) as mock_save:
            
            user_id = "hiroki"
            intent_id = uuid4()
            content = "Test intent content"
            
            result = await detector.check_new_intent(user_id, intent_id, content)
            
            # Verify all checkers were called
            mock_tech.assert_called_once_with(user_id, intent_id, content)
            mock_policy.assert_called_once_with(user_id, intent_id, content)
            mock_duplicate.assert_called_once_with(user_id, intent_id, content)
            mock_dogma.assert_called_once_with(user_id, intent_id, content)
            
            # No contradictions found, so save should not be called
            mock_save.assert_not_called()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_check_new_intent_saves_contradictions(self):
        """Test that detected contradictions are saved"""
        mock_pool = MagicMock()
        detector = ContradictionDetector(pool=mock_pool)
        
        # Create a mock contradiction
        mock_contradiction = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Test",
            contradiction_type="dogma",
            confidence_score=0.7,
        )
        
        with patch.object(detector, '_check_tech_stack_contradiction', new_callable=AsyncMock, return_value=[]), \
             patch.object(detector, '_check_policy_shift', new_callable=AsyncMock, return_value=[]), \
             patch.object(detector, '_check_duplicate_work', new_callable=AsyncMock, return_value=[]), \
             patch.object(detector, '_check_dogma', new_callable=AsyncMock, return_value=[mock_contradiction]), \
             patch.object(detector, '_save_contradiction', new_callable=AsyncMock) as mock_save:
            
            result = await detector.check_new_intent("hiroki", uuid4(), "Test")
            
            # Verify contradiction was saved
            mock_save.assert_called_once_with(mock_contradiction)
            assert len(result) == 1
            assert result[0] == mock_contradiction


class TestContradictionResolution:
    """Test contradiction resolution workflow"""

    @pytest.mark.asyncio
    async def test_resolve_contradiction(self):
        """Test resolving a contradiction"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        detector = ContradictionDetector(pool=mock_pool)
        
        contradiction_id = uuid4()
        resolution_action = "policy_change"
        resolution_rationale = "Switching to SQLite for development simplicity"
        resolved_by = "hiroki"
        
        await detector.resolve_contradiction(
            contradiction_id,
            resolution_action,
            resolution_rationale,
            resolved_by
        )
        
        # Verify database update was called
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "UPDATE contradictions" in call_args[0]
        assert call_args[1] == resolution_action
        assert call_args[2] == resolution_rationale
        assert call_args[3] == resolved_by
        assert call_args[4] == contradiction_id

    @pytest.mark.asyncio
    async def test_get_pending_contradictions(self):
        """Test retrieving pending contradictions"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock database response
        mock_row = {
            "id": uuid4(),
            "user_id": "hiroki",
            "new_intent_id": uuid4(),
            "new_intent_content": "Test",
            "conflicting_intent_id": None,
            "conflicting_intent_content": None,
            "contradiction_type": "dogma",
            "confidence_score": 0.7,
            "detected_at": datetime.now(timezone.utc),
            "details": '{"detected_keywords": ["always"]}',
            "resolution_status": "pending",
            "resolution_action": None,
            "resolution_rationale": None,
            "resolved_at": None,
            "resolved_by": None,
            "created_at": datetime.now(timezone.utc),
        }
        mock_conn.fetch.return_value = [mock_row]
        
        detector = ContradictionDetector(pool=mock_pool)
        
        result = await detector.get_pending_contradictions("hiroki")
        
        assert len(result) == 1
        assert result[0].user_id == "hiroki"
        assert result[0].contradiction_type == "dogma"
        assert result[0].resolution_status == "pending"
