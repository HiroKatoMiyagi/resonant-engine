from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Dict, Tuple, Type

import pytest
import pytest_asyncio

from bridge.core.bridge_set import BridgeSet
from bridge.core.constants import AuditEventType, BridgeTypeEnum, ExecutionMode, IntentStatusEnum, TechnicalActor
from bridge.core.models.intent_model import IntentModel
from bridge.core.reeval_client import ReEvalClient
from bridge.providers.ai import MockAIBridge
from bridge.providers.audit import MockAuditLogger
from bridge.providers.data import MockDataBridge
from bridge.providers.feedback import MockFeedbackBridge


@pytest_asyncio.fixture
async def data_bridge() -> AsyncIterator[MockDataBridge]:
    bridge = MockDataBridge()
    await bridge.connect()
    try:
        yield bridge
    finally:
        await bridge.disconnect()


@pytest.fixture
def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()


def _new_intent(status: IntentStatusEnum = IntentStatusEnum.RECEIVED) -> IntentModel:
    return IntentModel.new(
        intent_type="bridge-exec",
        payload={"stage": "test"},
        status=status,
        technical_actor=TechnicalActor.TEST_SUITE,
    )


def _build_bridge_set(
    *,
    data_bridge: MockDataBridge,
    audit_logger: MockAuditLogger,
    pipeline_order: Tuple[BridgeTypeEnum, ...] | None = None,
    ai: MockAIBridge | None = None,
    feedback_kwargs: Dict[str, Any] | None = None,
) -> BridgeSet:
    feedback_kwargs = feedback_kwargs or {}
    feedback = MockFeedbackBridge(**feedback_kwargs)

    cls: Type[BridgeSet]
    if pipeline_order is not None:
        class CustomBridgeSet(BridgeSet):
            PIPELINE_ORDER = pipeline_order
        cls = CustomBridgeSet
    else:
        cls = BridgeSet

    return cls(
        data=data_bridge,
        ai=ai or MockAIBridge(),
        feedback=feedback,
        audit=audit_logger,
    )


@pytest.mark.asyncio
async def test_input_bridge_sets_normalized_status(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    bridge_set = _build_bridge_set(
        data_bridge=data_bridge,
        audit_logger=audit_logger,
        pipeline_order=(BridgeTypeEnum.INPUT,),
    )

    intent = await data_bridge.save_intent(_new_intent())
    result = await bridge_set.execute(intent)

    stored = await data_bridge.get_intent(result.intent_id)
    assert stored.status == IntentStatusEnum.NORMALIZED


@pytest.mark.asyncio
async def test_normalize_bridge_sets_processed_status(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    bridge_set = _build_bridge_set(
        data_bridge=data_bridge,
        audit_logger=audit_logger,
        pipeline_order=(BridgeTypeEnum.INPUT, BridgeTypeEnum.NORMALIZE),
    )

    intent = await data_bridge.save_intent(_new_intent())
    result = await bridge_set.execute(intent)

    stored = await data_bridge.get_intent(result.intent_id)
    assert stored.status == IntentStatusEnum.PROCESSED
    assert "analysis" in stored.payload


@pytest.mark.asyncio
async def test_feedback_bridge_applies_correction(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    reeval_client = ReEvalClient(data_bridge, audit_logger)
    bridge_set = _build_bridge_set(
        data_bridge=data_bridge,
        audit_logger=audit_logger,
        pipeline_order=(BridgeTypeEnum.INPUT, BridgeTypeEnum.NORMALIZE, BridgeTypeEnum.FEEDBACK),
        feedback_kwargs={
            "judgment": "requires_changes",
            "correction_diff": {"status": "corrected", "field": "value"},
            "reeval_client": reeval_client,
        },
    )

    intent = await data_bridge.save_intent(_new_intent())
    result = await bridge_set.execute(intent)

    stored = await data_bridge.get_intent(result.intent_id)
    assert stored.status == IntentStatusEnum.CORRECTED
    assert stored.correction_history, "Correction history should be populated"


@pytest.mark.asyncio
async def test_output_bridge_marks_completed(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    bridge_set = _build_bridge_set(
        data_bridge=data_bridge,
        audit_logger=audit_logger,
        pipeline_order=(BridgeTypeEnum.INPUT, BridgeTypeEnum.OUTPUT),
    )

    intent = await data_bridge.save_intent(_new_intent())
    result = await bridge_set.execute(intent)

    stored = await data_bridge.get_intent(result.intent_id)
    assert stored.status == IntentStatusEnum.COMPLETED


class ExplodingAIBridge(MockAIBridge):
    async def process_intent(self, intent):  # type: ignore[override]
        raise RuntimeError("normalize failure")


@pytest.mark.asyncio
async def test_bridge_execution_failfast_stops_pipeline(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    bridge_set = _build_bridge_set(
        data_bridge=data_bridge,
        audit_logger=audit_logger,
        pipeline_order=(BridgeTypeEnum.INPUT, BridgeTypeEnum.NORMALIZE, BridgeTypeEnum.OUTPUT),
        ai=ExplodingAIBridge(),
    )

    persisted = await data_bridge.save_intent(_new_intent())

    with pytest.raises(RuntimeError):
        await bridge_set.execute(persisted)


@pytest.mark.asyncio
async def test_bridge_execution_continue_mode_proceeds(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    bridge_set = _build_bridge_set(
        data_bridge=data_bridge,
        audit_logger=audit_logger,
        pipeline_order=(BridgeTypeEnum.INPUT, BridgeTypeEnum.NORMALIZE, BridgeTypeEnum.OUTPUT),
        ai=ExplodingAIBridge(),
    )

    intent = await data_bridge.save_intent(_new_intent())
    result = await bridge_set.execute(intent, mode=ExecutionMode.CONTINUE)

    assert result.status == IntentStatusEnum.FAILED
    failure_entries = [entry for entry in audit_logger.entries if entry["event"] == AuditEventType.BRIDGE_FAILED.value]
    assert failure_entries, "Failure should be logged when continue mode absorbs errors"


@pytest.mark.asyncio
async def test_pipeline_order_is_preserved(data_bridge: MockDataBridge, audit_logger: MockAuditLogger) -> None:
    bridge_set = _build_bridge_set(
        data_bridge=data_bridge,
        audit_logger=audit_logger,
        pipeline_order=(
            BridgeTypeEnum.INPUT,
            BridgeTypeEnum.NORMALIZE,
            BridgeTypeEnum.FEEDBACK,
            BridgeTypeEnum.OUTPUT,
        ),
        feedback_kwargs={"reeval_client": ReEvalClient(data_bridge, audit_logger)},
    )

    intent = await data_bridge.save_intent(_new_intent())
    await bridge_set.execute(intent)

    started_events = [
        entry["bridge_type"]
        for entry in audit_logger.entries
        if entry["event"] == AuditEventType.BRIDGE_STARTED.value
    ]
    expected = [stage.value for stage in bridge_set.PIPELINE_ORDER]
    assert started_events == expected
