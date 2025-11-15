from uuid import UUID, uuid4

from bridge.core.correction.idempotency import generate_correction_id, is_correction_applied


def test_generate_correction_id_is_deterministic() -> None:
    intent_id = uuid4()
    diff = {"payload": {"status": "test"}}

    correction_id_a = generate_correction_id(intent_id, diff)
    correction_id_b = generate_correction_id(intent_id, diff)
    correction_id_other_intent = generate_correction_id(uuid4(), diff)

    assert correction_id_a == correction_id_b
    assert correction_id_a != correction_id_other_intent


def test_is_correction_applied_detects_existing_ids() -> None:
    intent_id = uuid4()
    diff = {"payload": {"status": "corrected"}}
    correction_id = generate_correction_id(intent_id, diff)

    history = [
        {"correction_id": str(correction_id)},
        {"correction_id": str(uuid4())},
    ]

    assert is_correction_applied(history, correction_id) is True


def test_is_correction_applied_handles_uuid_objects() -> None:
    correction_id = uuid4()
    history = [{"correction_id": correction_id}]

    assert is_correction_applied(history, correction_id) is True
    assert is_correction_applied(history, uuid4()) is False
