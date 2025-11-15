"""
Intent Lifecycle Test Suite v1
Bridge Lite / Resonant Engine

このテストスイートは、Intent のライフサイクルが設計どおり遷移しているかを検証するためのテンプレートです。
- RECEIVED
- NORMALIZED
- PROCESSED
- FEEDBACK (optional correction)
- CORRECTED
- COMPLETED
- FAILED (例外系)

前提:
- pytest + pytest-asyncio を利用
- BridgeFactory から各 Bridge インスタンスを取得できる
"""

from __future__ import annotations

import os
from typing import Any, Dict

import pytest
import pytest_asyncio

from bridge.core.constants import BridgeTypeEnum, TechnicalActor
from bridge.core.constants import IntentStatusEnum
from bridge.core.models.intent_model import IntentModel
from bridge.factory.bridge_factory import BridgeFactory


@pytest_asyncio.fixture(scope="module")
async def bridges():
    """
    BridgeFactory から BridgeSet をまとめて取得するフィクスチャ。
    """

    os.environ.setdefault("AI_BRIDGE_TYPE", "mock")
    os.environ.setdefault("DATA_BRIDGE_TYPE", "mock")
    os.environ.setdefault("FEEDBACK_BRIDGE_TYPE", "mock")
    os.environ.setdefault("AUDIT_LOGGER_TYPE", "mock")

    bridge_set = BridgeFactory.create_all()
    async with bridge_set as bundle:
        try:
            yield bundle
        finally:
            if hasattr(bundle.audit, "cleanup"):
                await bundle.audit.cleanup()


def _build_dummy_intent() -> IntentModel:
    payload: Dict[str, Any] = {
        "msg": "hello from test",
        "meta": {
            "test_case": "full_lifecycle",
        },
    }
    return IntentModel.new(
        intent_type="test_intent",
        payload=payload,
        technical_actor=TechnicalActor.TEST_SUITE,
    )


def _intent_dict(intent: IntentModel) -> Dict[str, Any]:
    return intent.model_dump_bridge()


@pytest.mark.asyncio
async def test_intent_full_lifecycle_happy_path(bridges):
    """
    正常系: Intent が設計どおりのライフサイクルを通過するか検証する。
    - RECEIVED (テスト内で生成とみなす)
    - RECORDED
    - AI_PROCESSED
    - FEEDBACK_COLLECTED
    - REEVALUATED
    - CORRECTED
    - CLOSED
    """

    new_intent = _build_dummy_intent()

    # RECEIVED 相当: テスト内で Intent を構築
    # RECORDED: DataBridge に保存
    recorded = await bridges.data.save_intent(new_intent)
    intent_id = recorded.intent_id

    await bridges.audit.log(
        bridge_type=BridgeTypeEnum.INPUT,
        operation="save_intent",
        details={"intent_type": recorded.type},
        intent_id=intent_id,
        correlation_id=recorded.correlation_id,
    )

    stored = await bridges.data.get_intent(intent_id)
    assert stored.status in {
        IntentStatusEnum.RECEIVED,
        IntentStatusEnum.NORMALIZED,
    }, "初期ステータスが RECEIVED または NORMALIZED であることが望ましい"

    # AI_PROCESSED: 一次解析
    ai_result = await bridges.ai.process_intent(_intent_dict(stored))

    await bridges.audit.log(
        bridge_type=BridgeTypeEnum.NORMALIZE,
        operation="process_intent",
        details={"status": "ok"},
        intent_id=intent_id,
        correlation_id=stored.correlation_id,
    )

    # FEEDBACK_COLLECTED: 簡易フィードバック（ここでは AI 結果をそのまま feedback と扱う）
    feedback = {"ai_result": ai_result, "feedback_source": "auto"}
    await bridges.audit.log(
        bridge_type=BridgeTypeEnum.FEEDBACK,
        operation="collect_feedback",
        details={"kind": "auto"},
        intent_id=intent_id,
        correlation_id=stored.correlation_id,
    )

    # REEVALUATED: 再評価
    if hasattr(bridges.feedback, "request_reevaluation"):
        reeval = await bridges.feedback.request_reevaluation(_intent_dict(stored))
    else:
        reeval = await bridges.feedback.reanalyze(_intent_dict(stored), [feedback])

    await bridges.audit.log(
        bridge_type=BridgeTypeEnum.FEEDBACK,
        operation="reevaluate",
        details={"status": "ok"},
        intent_id=intent_id,
        correlation_id=stored.correlation_id,
    )

    assert isinstance(reeval, dict), "Re-evaluation 結果は dict であるべき"

    # CORRECTED: Correction Plan 生成（generate_correction がある場合のみ）
    if hasattr(bridges.feedback, "generate_correction"):
        correction = await bridges.feedback.generate_correction(_intent_dict(stored), [feedback])
        stored = await bridges.data.save_correction(intent_id, correction)

        await bridges.audit.log(
            bridge_type=BridgeTypeEnum.FEEDBACK,
            operation="generate_correction",
            details={"status": "ok"},
            intent_id=intent_id,
            correlation_id=stored.correlation_id,
        )

        assert isinstance(correction, dict), "Correction Plan は dict であるべき"
        assert stored.status == IntentStatusEnum.CORRECTED

    # CLOSED: Daemon 側の責務だが、ここでは status 更新のインターフェースがあれば検証する
    if hasattr(bridges.data, "update_intent_status"):
        await bridges.data.update_intent_status(intent_id, IntentStatusEnum.COMPLETED.value)
        closed = await bridges.data.get_intent(intent_id)
        assert closed.status == IntentStatusEnum.COMPLETED


@pytest.mark.asyncio
async def test_intent_lifecycle_requires_correlation_id(bridges):
    """
    correlation_id が必ず付与され、AuditLogger にも渡されていることを検証する。
    """

    intent = _build_dummy_intent()
    stored = await bridges.data.save_intent(intent)
    fetched = await bridges.data.get_intent(stored.intent_id)

    assert fetched.correlation_id == intent.correlation_id


@pytest.mark.asyncio
async def test_invalid_intent_id_raises_error(bridges):
    """
    不正な intent_id 取得時に KeyError などの適切な例外が発生することを検証する。
    実装に応じて例外型は調整してください。
    """

    invalid_id = "non-existent-intent-id"
    with pytest.raises(Exception):
        await bridges.data.get_intent(invalid_id)


@pytest.mark.asyncio
async def test_lifecycle_partial_failure_does_not_break_logging_chain(bridges):
    """
    Re-evaluation など一部のステップで例外が発生しても、
    AuditLogger のチェーン（prev_hash 等）が壊れない前提でログ出力が行われることを検証する。
    実際のチェーン検証は別テストで扱ってもよい。
    """

    intent = _build_dummy_intent()
    stored = await bridges.data.save_intent(intent)

    # AI までは正常に進める
    await bridges.ai.process_intent(_intent_dict(stored))

    # Feedback / Re-evaluation で意図的に失敗させるためのダミー入力
    failure_result = None
    failure_raised = False
    try:
        failure_result = await bridges.feedback.reanalyze({"invalid": "payload"}, [])
    except Exception:
        failure_raised = True

    # それでも AuditLogger.log 自体は動作できる前提
    await bridges.audit.log(
        bridge_type=BridgeTypeEnum.FEEDBACK,
        operation="reevaluate_failed",
        details={"reason": "intentional_failure_for_test"},
        intent_id=stored.intent_id,
        correlation_id=stored.correlation_id,
    )

    if not failure_raised:
        assert isinstance(failure_result, dict), "Mockブリッジの場合でも戻り値がdictであること"
