"""
Database configuration and SQLAlchemy models for Memory Management System.

This module provides:
- SQLAlchemy ORM models for 8 core tables
- Database connection management
- Session factory configuration
"""

import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Base class for all ORM models
Base = declarative_base()

# Default database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://resonant:password@localhost:5432/resonant"
)

ASYNC_DATABASE_URL = os.environ.get(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://resonant:password@localhost:5432/resonant"
)


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================


class SessionModel(Base):
    """Sessions table - User session management"""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_active = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default="active", index=True)
    metadata = Column(JSONB, default=dict)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'archived')",
            name="valid_session_status"
        ),
        Index("idx_sessions_last_active", "last_active"),
    )

    # Relationships
    intents = relationship("IntentModel", back_populates="session", cascade="all, delete-orphan")
    resonances = relationship("ResonanceModel", back_populates="session", cascade="all, delete-orphan")
    agent_contexts = relationship("AgentContextModel", back_populates="session", cascade="all, delete-orphan")
    choice_points = relationship("ChoicePointModel", back_populates="session", cascade="all, delete-orphan")
    breathing_cycles = relationship("BreathingCycleModel", back_populates="session", cascade="all, delete-orphan")
    snapshots = relationship("SnapshotModel", back_populates="session", cascade="all, delete-orphan")


class IntentModel(Base):
    """Intents table - Intent persistence"""
    __tablename__ = "intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    parent_intent_id = Column(UUID(as_uuid=True), ForeignKey("intents.id", ondelete="SET NULL"), nullable=True)

    intent_text = Column(Text, nullable=False)
    intent_type = Column(String(100), nullable=False)
    priority = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(50), nullable=False, default="pending")
    outcome = Column(JSONB, nullable=True)

    metadata = Column(JSONB, default=dict)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'cancelled', 'deferred')",
            name="valid_intent_status"
        ),
        CheckConstraint("priority >= 0 AND priority <= 10", name="valid_priority"),
        Index("idx_intents_session_id", "session_id"),
        Index("idx_intents_parent", "parent_intent_id"),
        Index("idx_intents_status", "status"),
        Index("idx_intents_created_at", "created_at"),
        Index("idx_intents_intent_type", "intent_type"),
    )

    # Relationships
    session = relationship("SessionModel", back_populates="intents")
    parent = relationship("IntentModel", remote_side=[id], backref="children")
    resonances = relationship("ResonanceModel", back_populates="intent")
    agent_contexts = relationship("AgentContextModel", back_populates="intent")
    choice_points = relationship("ChoicePointModel", back_populates="intent")
    breathing_cycles = relationship("BreathingCycleModel", back_populates="intent")


class ResonanceModel(Base):
    """Resonances table - Resonance state recording"""
    __tablename__ = "resonances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    intent_id = Column(UUID(as_uuid=True), ForeignKey("intents.id", ondelete="SET NULL"), nullable=True)

    state = Column(String(100), nullable=False)
    intensity = Column(Float, nullable=False)
    agents = Column(JSONB, nullable=False)

    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=True)

    pattern_type = Column(String(100), nullable=True)
    metadata = Column(JSONB, default=dict)

    __table_args__ = (
        CheckConstraint("intensity >= 0 AND intensity <= 1", name="valid_intensity"),
        Index("idx_resonances_session_id", "session_id"),
        Index("idx_resonances_intent_id", "intent_id"),
        Index("idx_resonances_state", "state"),
        Index("idx_resonances_timestamp", "timestamp"),
    )

    # Relationships
    session = relationship("SessionModel", back_populates="resonances")
    intent = relationship("IntentModel", back_populates="resonances")


class AgentContextModel(Base):
    """Agent contexts table - Agent context preservation"""
    __tablename__ = "agent_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    intent_id = Column(UUID(as_uuid=True), ForeignKey("intents.id", ondelete="SET NULL"), nullable=True)

    agent_type = Column(String(50), nullable=False)
    context_data = Column(JSONB, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    superseded_by = Column(UUID(as_uuid=True), ForeignKey("agent_contexts.id", ondelete="SET NULL"), nullable=True)

    metadata = Column(JSONB, default=dict)

    __table_args__ = (
        CheckConstraint(
            "agent_type IN ('yuno', 'kana', 'tsumu')",
            name="valid_agent_type"
        ),
        Index("idx_agent_contexts_session_id", "session_id"),
        Index("idx_agent_contexts_intent_id", "intent_id"),
        Index("idx_agent_contexts_agent_type", "agent_type"),
        Index("idx_agent_contexts_version", "version"),
    )

    # Relationships
    session = relationship("SessionModel", back_populates="agent_contexts")
    intent = relationship("IntentModel", back_populates="agent_contexts")


class ChoicePointModel(Base):
    """Choice points table - Choice point management"""
    __tablename__ = "choice_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    intent_id = Column(UUID(as_uuid=True), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False)

    question = Column(Text, nullable=False)
    choices = Column(JSONB, nullable=False)
    selected_choice_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    decision_rationale = Column(Text, nullable=True)
    metadata = Column(JSONB, default=dict)

    __table_args__ = (
        Index("idx_choice_points_session_id", "session_id"),
        Index("idx_choice_points_intent_id", "intent_id"),
        Index("idx_choice_points_created_at", "created_at"),
    )

    # Relationships
    session = relationship("SessionModel", back_populates="choice_points")
    intent = relationship("IntentModel", back_populates="choice_points")


class BreathingCycleModel(Base):
    """Breathing cycles table - Breathing cycle state management"""
    __tablename__ = "breathing_cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    intent_id = Column(UUID(as_uuid=True), ForeignKey("intents.id", ondelete="SET NULL"), nullable=True)

    phase = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    phase_data = Column(JSONB, default=dict)
    success = Column(Boolean, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "phase IN ('intake', 'resonance', 'structuring', 're_reflection', 'implementation', 'resonance_expansion')",
            name="valid_phase"
        ),
        Index("idx_breathing_cycles_session_id", "session_id"),
        Index("idx_breathing_cycles_intent_id", "intent_id"),
        Index("idx_breathing_cycles_phase", "phase"),
        Index("idx_breathing_cycles_started_at", "started_at"),
    )

    # Relationships
    session = relationship("SessionModel", back_populates="breathing_cycles")
    intent = relationship("IntentModel", back_populates="breathing_cycles")


class SnapshotModel(Base):
    """Snapshots table - Temporal snapshots"""
    __tablename__ = "snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)

    snapshot_type = Column(String(50), nullable=False)
    snapshot_data = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    description = Column(Text, nullable=True)

    tags = Column(ARRAY(String(255)), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "snapshot_type IN ('manual', 'auto_hourly', 'pre_major_change', 'crisis_point', 'milestone')",
            name="valid_snapshot_type"
        ),
        Index("idx_snapshots_session_id", "session_id"),
        Index("idx_snapshots_created_at", "created_at"),
        Index("idx_snapshots_type", "snapshot_type"),
    )

    # Relationships
    session = relationship("SessionModel", back_populates="snapshots")


class MemoryQueryModel(Base):
    """Memory queries table - Query logging for pattern analysis"""
    __tablename__ = "memory_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)

    query_text = Column(Text, nullable=False)
    query_params = Column(JSONB, nullable=True)

    executed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    execution_time_ms = Column(Integer, nullable=True)

    results_count = Column(Integer, nullable=True)
    results_sample = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_memory_queries_session_id", "session_id"),
        Index("idx_memory_queries_executed_at", "executed_at"),
    )


# ============================================================================
# Database Connection Management
# ============================================================================


def get_engine(url: Optional[str] = None):
    """Create a synchronous database engine"""
    return create_engine(url or DATABASE_URL)


def get_async_engine(url: Optional[str] = None):
    """Create an asynchronous database engine"""
    return create_async_engine(url or ASYNC_DATABASE_URL)


def get_session_factory(engine=None):
    """Create a session factory for synchronous sessions"""
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine)


def get_async_session_factory(engine=None):
    """Create a session factory for asynchronous sessions"""
    if engine is None:
        engine = get_async_engine()
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def create_all_tables(engine=None):
    """Create all database tables"""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)


def drop_all_tables(engine=None):
    """Drop all database tables (use with caution!)"""
    if engine is None:
        engine = get_engine()
    Base.metadata.drop_all(engine)
