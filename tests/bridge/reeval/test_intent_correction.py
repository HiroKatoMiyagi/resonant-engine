import pytest

from bridge.core.constants import IntentStatusEnum, PhilosophicalActor, TechnicalActor
from bridge.core.models.intent_model import IntentModel
from bridge.core.exceptions import DiffValidationError, InvalidStatusError


def _build_intent() -> IntentModel:
    return IntentModel.new(
        intent_type="review",
        payload={"quality_score": 0.4},
        technical_actor=TechnicalActor.DAEMON,
    )


def test_apply_correction_updates_payload_and_history() -> None:
    intent = _build_intent()
    updated, record, already_applied = intent.apply_correction(
        {"payload": {"quality_score": 0.9}},
        source=PhilosophicalActor.KANA,
        reason="Quality adjustment",
        metadata={"score": 0.9},
    )

    assert already_applied is False
    assert updated.status == IntentStatusEnum.CORRECTED
    assert updated.payload["quality_score"] == 0.9
    assert len(updated.correction_history) == 1
    assert record.reason == "Quality adjustment"
    assert record.metadata == {"score": 0.9}


def test_apply_correction_is_idempotent() -> None:
    intent = _build_intent()
    first, record, already_applied = intent.apply_correction(
        {"payload": {"state": "corrected"}},
        source=PhilosophicalActor.YUNO,
        reason="Initial correction",
    )
    assert already_applied is False

    second, record_again, already_applied_second = first.apply_correction(
        {"payload": {"state": "corrected"}},
        source=PhilosophicalActor.YUNO,
        reason="Repeat correction",
    )

    assert already_applied_second is True
    assert second is first
    assert record_again.correction_id == record.correction_id
    assert len(first.correction_history) == 1


def test_apply_correction_rejects_invalid_status() -> None:
    intent = _build_intent().with_updates(status=IntentStatusEnum.COMPLETED)

    with pytest.raises(InvalidStatusError):
        intent.apply_correction(
            {"payload": {"quality_score": 0.5}},
            source=PhilosophicalActor.KANA,
            reason="Cannot modify",
        )


def test_apply_correction_validates_diff_payload() -> None:
    intent = _build_intent()

    with pytest.raises(DiffValidationError):
        intent.apply_correction(
            {"payload": "+5"},
            source=PhilosophicalActor.KANA,
            reason="Invalid diff",
        )
