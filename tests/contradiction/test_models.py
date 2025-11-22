"""Tests for Contradiction models - Sprint 11 Day 1

Test Coverage:
- TC-01: Contradiction model validation
- TC-02: IntentRelation model validation
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError

from bridge.contradiction.models import Contradiction, IntentRelation


class TestContradictionModel:
    """Test Contradiction model"""

    def test_contradiction_with_all_fields(self):
        """Test creating Contradiction with all fields"""
        contradiction = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Use SQLite",
            conflicting_intent_id=uuid4(),
            conflicting_intent_content="Use PostgreSQL",
            contradiction_type="tech_stack",
            confidence_score=0.9,
            details={"old_tech": "postgresql", "new_tech": "sqlite"},
            resolution_status="pending",
        )

        assert contradiction.user_id == "hiroki"
        assert contradiction.contradiction_type == "tech_stack"
        assert contradiction.confidence_score == 0.9
        assert contradiction.resolution_status == "pending"
        assert contradiction.details["old_tech"] == "postgresql"
        assert contradiction.details["new_tech"] == "sqlite"

    def test_contradiction_minimal_fields(self):
        """Test creating Contradiction with minimal required fields"""
        contradiction = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Test content",
            contradiction_type="dogma",
            confidence_score=0.7,
        )

        assert contradiction.user_id == "hiroki"
        assert contradiction.contradiction_type == "dogma"
        assert contradiction.confidence_score == 0.7
        assert contradiction.resolution_status == "pending"  # Default value
        assert contradiction.details == {}  # Default empty dict
        assert contradiction.conflicting_intent_id is None

    def test_contradiction_type_validation(self):
        """Test contradiction_type validation"""
        with pytest.raises(ValidationError) as exc_info:
            Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="invalid_type",  # Invalid
                confidence_score=0.9,
            )
        
        assert "contradiction_type must be one of" in str(exc_info.value)

    def test_contradiction_type_valid_values(self):
        """Test all valid contradiction_type values"""
        valid_types = ["tech_stack", "policy_shift", "duplicate", "dogma"]
        
        for ctype in valid_types:
            contradiction = Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type=ctype,
                confidence_score=0.8,
            )
            assert contradiction.contradiction_type == ctype

    def test_confidence_score_validation_too_high(self):
        """Test confidence_score must be <= 1.0"""
        with pytest.raises(ValidationError):
            Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="tech_stack",
                confidence_score=1.5,  # Invalid: > 1.0
            )

    def test_confidence_score_validation_too_low(self):
        """Test confidence_score must be >= 0.0"""
        with pytest.raises(ValidationError):
            Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="tech_stack",
                confidence_score=-0.1,  # Invalid: < 0.0
            )

    def test_confidence_score_boundary_values(self):
        """Test confidence_score boundary values (0.0 and 1.0)"""
        # Test 0.0
        c1 = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Test",
            contradiction_type="tech_stack",
            confidence_score=0.0,
        )
        assert c1.confidence_score == 0.0

        # Test 1.0
        c2 = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Test",
            contradiction_type="tech_stack",
            confidence_score=1.0,
        )
        assert c2.confidence_score == 1.0

    def test_resolution_status_validation(self):
        """Test resolution_status validation"""
        with pytest.raises(ValidationError) as exc_info:
            Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="tech_stack",
                confidence_score=0.9,
                resolution_status="invalid_status",  # Invalid
            )
        
        assert "resolution_status must be one of" in str(exc_info.value)

    def test_resolution_status_valid_values(self):
        """Test all valid resolution_status values"""
        valid_statuses = ["pending", "approved", "rejected", "modified"]
        
        for status in valid_statuses:
            contradiction = Contradiction(
                user_id="hiroki",
                new_intent_id=uuid4(),
                new_intent_content="Test",
                contradiction_type="tech_stack",
                confidence_score=0.8,
                resolution_status=status,
            )
            assert contradiction.resolution_status == status

    def test_contradiction_with_resolution_info(self):
        """Test Contradiction with complete resolution information"""
        resolved_time = datetime.now(timezone.utc)
        
        contradiction = Contradiction(
            user_id="hiroki",
            new_intent_id=uuid4(),
            new_intent_content="Use SQLite",
            conflicting_intent_id=uuid4(),
            conflicting_intent_content="Use PostgreSQL",
            contradiction_type="tech_stack",
            confidence_score=0.9,
            resolution_status="approved",
            resolution_action="policy_change",
            resolution_rationale="Switching to SQLite for development simplicity",
            resolved_at=resolved_time,
            resolved_by="hiroki",
        )

        assert contradiction.resolution_status == "approved"
        assert contradiction.resolution_action == "policy_change"
        assert contradiction.resolution_rationale == "Switching to SQLite for development simplicity"
        assert contradiction.resolved_at == resolved_time
        assert contradiction.resolved_by == "hiroki"


class TestIntentRelationModel:
    """Test IntentRelation model"""

    def test_intent_relation_with_all_fields(self):
        """Test creating IntentRelation with all fields"""
        relation = IntentRelation(
            user_id="hiroki",
            source_intent_id=uuid4(),
            target_intent_id=uuid4(),
            relation_type="contradicts",
            similarity_score=0.85,
        )

        assert relation.user_id == "hiroki"
        assert relation.relation_type == "contradicts"
        assert relation.similarity_score == 0.85

    def test_intent_relation_minimal_fields(self):
        """Test creating IntentRelation with minimal required fields"""
        relation = IntentRelation(
            user_id="hiroki",
            source_intent_id=uuid4(),
            target_intent_id=uuid4(),
            relation_type="extends",
        )

        assert relation.user_id == "hiroki"
        assert relation.relation_type == "extends"
        assert relation.similarity_score is None  # Optional field

    def test_relation_type_validation(self):
        """Test relation_type validation"""
        with pytest.raises(ValidationError) as exc_info:
            IntentRelation(
                user_id="hiroki",
                source_intent_id=uuid4(),
                target_intent_id=uuid4(),
                relation_type="invalid_type",  # Invalid
            )
        
        assert "relation_type must be one of" in str(exc_info.value)

    def test_relation_type_valid_values(self):
        """Test all valid relation_type values"""
        valid_types = ["contradicts", "duplicates", "extends", "replaces"]
        
        for rtype in valid_types:
            relation = IntentRelation(
                user_id="hiroki",
                source_intent_id=uuid4(),
                target_intent_id=uuid4(),
                relation_type=rtype,
            )
            assert relation.relation_type == rtype

    def test_similarity_score_validation_too_high(self):
        """Test similarity_score must be <= 1.0"""
        with pytest.raises(ValidationError):
            IntentRelation(
                user_id="hiroki",
                source_intent_id=uuid4(),
                target_intent_id=uuid4(),
                relation_type="duplicates",
                similarity_score=1.5,  # Invalid: > 1.0
            )

    def test_similarity_score_validation_too_low(self):
        """Test similarity_score must be >= 0.0"""
        with pytest.raises(ValidationError):
            IntentRelation(
                user_id="hiroki",
                source_intent_id=uuid4(),
                target_intent_id=uuid4(),
                relation_type="duplicates",
                similarity_score=-0.1,  # Invalid: < 0.0
            )

    def test_similarity_score_boundary_values(self):
        """Test similarity_score boundary values (0.0 and 1.0)"""
        # Test 0.0
        r1 = IntentRelation(
            user_id="hiroki",
            source_intent_id=uuid4(),
            target_intent_id=uuid4(),
            relation_type="duplicates",
            similarity_score=0.0,
        )
        assert r1.similarity_score == 0.0

        # Test 1.0
        r2 = IntentRelation(
            user_id="hiroki",
            source_intent_id=uuid4(),
            target_intent_id=uuid4(),
            relation_type="duplicates",
            similarity_score=1.0,
        )
        assert r2.similarity_score == 1.0

    def test_intent_relation_auto_generated_fields(self):
        """Test auto-generated fields (id, created_at)"""
        relation = IntentRelation(
            user_id="hiroki",
            source_intent_id=uuid4(),
            target_intent_id=uuid4(),
            relation_type="contradicts",
        )

        assert relation.id is not None
        assert isinstance(relation.id, type(uuid4()))
        assert relation.created_at is not None
        assert isinstance(relation.created_at, datetime)
