import pytest

from bridge.core.correction.diff import apply_diff
from bridge.core.exceptions import DiffValidationError


def test_diff_apply_simple_field_replacement() -> None:
    target = {"field_a": "old_value", "field_b": 100}
    diff = {"field_a": "new_value"}

    result = apply_diff(target, diff)

    assert result["field_a"] == "new_value"
    assert result["field_b"] == 100
    assert target["field_a"] == "old_value"  # original unchanged


def test_diff_apply_nested_path_update() -> None:
    target = {"config": {"timeout": 10, "retries": 3}}
    diff = {"config.timeout": 30}

    result = apply_diff(target, diff)

    assert result["config"]["timeout"] == 30
    assert result["config"]["retries"] == 3


def test_diff_rejects_relative_operations() -> None:
    target = {"count": 10}
    diff = {"count": "+5"}

    with pytest.raises(DiffValidationError):
        apply_diff(target, diff)
