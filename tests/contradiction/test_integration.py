"""Integration tests for Contradiction Detection - Sprint 11 Day 3

Test Coverage:
- AC-12: Contradiction resolution workflow
- AC-13: Get pending contradictions
- Database integration
"""

import pytest
import json
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.contradiction.detector import ContradictionDetector
from bridge.contradiction.models import Contradiction


@pytest.mark.asyncio
class TestContradictionDatabaseIntegration:
    """Test ContradictionDetector with database operations"""

    async def test_save_contradiction_to_database(self):
        """Test saving contradiction to database"""
        # Mock pool and connection
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        detector = ContradictionDetector(pool=mock_pool)
        
        contradiction = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Use SQLite database",
            conflicting_intent_id=uuid4(),
            conflicting_intent_content="Use PostgreSQL database",
            contradiction_type="tech_stack",
            confidence_score=0.9,
            details={"category": "database", "old_tech": "postgresql", "new_tech": "sqlite"},
        )
        
        await detector._save_contradiction(contradiction)
        
        # Verify INSERT was called
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "INSERT INTO contradictions" in call_args[0]
        assert call_args[1] == "hiroki"
        assert call_args[6] == "tech_stack"
        assert call_args[7] == 0.9

    async def test_resolve_contradiction_updates_database(self):
        """Test resolving contradiction updates database - AC-12"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        detector = ContradictionDetector(pool=mock_pool)
        
        contradiction_id = uuid4()
        await detector.resolve_contradiction(
            contradiction_id=contradiction_id,
            resolution_action="policy_change",
            resolution_rationale="Switching to SQLite for development simplicity",
            resolved_by="hiroki"
        )
        
        # Verify UPDATE was called
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "UPDATE contradictions" in call_args[0]
        assert "resolution_status = 'approved'" in call_args[0]
        assert call_args[1] == "policy_change"
        assert call_args[2] == "Switching to SQLite for development simplicity"
        assert call_args[3] == "hiroki"
        assert call_args[4] == contradiction_id

    async def test_get_pending_contradictions_from_database(self):
        """Test retrieving pending contradictions - AC-13"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock database rows
        mock_rows = [
            {
                "id": uuid4(),
                "user_id": "hiroki",
                "new_intent_id": uuid4(),
                "new_intent_content": "Use SQLite",
                "conflicting_intent_id": uuid4(),
                "conflicting_intent_content": "Use PostgreSQL",
                "contradiction_type": "tech_stack",
                "confidence_score": 0.9,
                "detected_at": datetime.now(timezone.utc),
                "details": json.dumps({"category": "database"}),
                "resolution_status": "pending",
                "resolution_action": None,
                "resolution_rationale": None,
                "resolved_at": None,
                "resolved_by": None,
                "created_at": datetime.now(timezone.utc),
            },
            {
                "id": uuid4(),
                "user_id": "hiroki",
                "new_intent_id": uuid4(),
                "new_intent_content": "All users always login",
                "conflicting_intent_id": None,
                "conflicting_intent_content": None,
                "contradiction_type": "dogma",
                "confidence_score": 0.7,
                "detected_at": datetime.now(timezone.utc),
                "details": json.dumps({"detected_keywords": ["always"]}),
                "resolution_status": "pending",
                "resolution_action": None,
                "resolution_rationale": None,
                "resolved_at": None,
                "resolved_by": None,
                "created_at": datetime.now(timezone.utc),
            }
        ]
        mock_conn.fetch.return_value = mock_rows
        
        detector = ContradictionDetector(pool=mock_pool)
        
        result = await detector.get_pending_contradictions("hiroki")
        
        # Verify query was called
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args[0]
        assert "SELECT * FROM contradictions" in call_args[0]
        assert "resolution_status = 'pending'" in call_args[0]
        assert call_args[1] == "hiroki"
        
        # Verify results
        assert len(result) == 2
        assert all(c.user_id == "hiroki" for c in result)
        assert all(c.resolution_status == "pending" for c in result)
        assert result[0].contradiction_type == "tech_stack"
        assert result[1].contradiction_type == "dogma"


@pytest.mark.asyncio
class TestContradictionWorkflow:
    """Test complete contradiction detection workflow"""

    async def test_full_contradiction_detection_workflow(self):
        """Test complete workflow: detect → save → retrieve → resolve"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock past intents query (for tech stack check)
        mock_conn.fetch.return_value = [
            {
                "id": uuid4(),
                "content": "Use PostgreSQL for database",
                "created_at": datetime.now(timezone.utc),
            }
        ]
        
        detector = ContradictionDetector(pool=mock_pool)
        
        # Step 1: Detect contradictions
        user_id = "hiroki"
        new_intent_id = uuid4()
        new_content = "Use SQLite for database"
        
        contradictions = await detector.check_new_intent(
            user_id=user_id,
            new_intent_id=new_intent_id,
            new_intent_content=new_content
        )
        
        # Verify contradiction was detected and saved
        assert len(contradictions) == 1
        assert contradictions[0].contradiction_type == "tech_stack"
        assert contradictions[0].confidence_score == 0.9
        
        # Verify save was called
        assert mock_conn.execute.called

    async def test_no_contradiction_detected(self):
        """Test when no contradictions are found"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock empty past intents
        mock_conn.fetch.return_value = []
        
        detector = ContradictionDetector(pool=mock_pool)
        
        contradictions = await detector.check_new_intent(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="This is a general discussion"
        )
        
        # No contradictions should be found
        assert len(contradictions) == 0
        
        # Save should not be called
        mock_conn.execute.assert_not_called()


@pytest.mark.asyncio
class TestContradictionDetectorFactory:
    """Test factory pattern for ContradictionDetector"""

    async def test_create_detector_with_pool(self):
        """Test creating detector with database pool"""
        mock_pool = MagicMock()
        
        detector = ContradictionDetector(pool=mock_pool)
        
        assert detector.pool == mock_pool
        assert detector.TECH_STACK_KEYWORDS is not None
        assert detector.POLICY_SHIFT_WINDOW_DAYS == 14
        assert detector.DUPLICATE_SIMILARITY_THRESHOLD == 0.85

    async def test_detector_configuration(self):
        """Test detector configuration values"""
        mock_pool = MagicMock()
        detector = ContradictionDetector(pool=mock_pool)
        
        # Verify tech stack keywords
        assert "database" in detector.TECH_STACK_KEYWORDS
        assert "framework" in detector.TECH_STACK_KEYWORDS
        assert "language" in detector.TECH_STACK_KEYWORDS
        
        # Verify database keywords
        assert "postgresql" in detector.TECH_STACK_KEYWORDS["database"]
        assert "sqlite" in detector.TECH_STACK_KEYWORDS["database"]
        assert "mongodb" in detector.TECH_STACK_KEYWORDS["database"]
        
        # Verify framework keywords
        assert "fastapi" in detector.TECH_STACK_KEYWORDS["framework"]
        assert "django" in detector.TECH_STACK_KEYWORDS["framework"]
        assert "react" in detector.TECH_STACK_KEYWORDS["framework"]
