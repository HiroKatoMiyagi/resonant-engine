import pytest
from datetime import datetime, timedelta, timezone
from app.services.temporal_constraint.checker import TemporalConstraintChecker
from app.services.temporal_constraint.models import FileVerification, ConstraintLevel

def test_generate_warning():
    """警告メッセージ生成テスト"""
    checker = TemporalConstraintChecker(None)
    
    verified_at = datetime.now(timezone.utc) - timedelta(days=35)
    stable_since = datetime.now(timezone.utc) - timedelta(days=30)
    
    verification = FileVerification(
        user_id="test_user",
        file_path="sp_api_client.py",
        verification_type="integration_test",
        test_hours_invested=100.0,
        constraint_level=ConstraintLevel.CRITICAL,
        verified_at=verified_at,
        stable_since=stable_since
    )
    
    warning = checker._generate_warning(verification)
    
    # 検証
    assert "Temporal Constraint Warning" in warning
    assert "sp_api_client.py" in warning
    assert "VERIFIED" in warning
    assert "CRITICAL" in warning
    # Due to time calc, allow small margin or loose check
    assert "100.0h" in warning or "100h" in warning
    assert "35 days" in warning or "34 days" in warning or "35" in warning # allow small drift

def test_constraint_config():
    """制約設定読み込みテスト"""
    checker = TemporalConstraintChecker(None)
    
    # CRITICAL設定
    critical_config = checker.CONSTRAINT_CONFIG[ConstraintLevel.CRITICAL]
    assert critical_config["require_approval"] == True
    assert critical_config["require_reason"] == True
    assert critical_config["min_reason_length"] == 50
    assert len(critical_config["questions"]) >= 3
    
    # HIGH設定
    high_config = checker.CONSTRAINT_CONFIG[ConstraintLevel.HIGH]
    assert high_config["require_approval"] == False
    assert high_config["require_reason"] == True
    assert high_config["min_reason_length"] == 20
    
    # LOW設定
    low_config = checker.CONSTRAINT_CONFIG[ConstraintLevel.LOW]
    assert low_config["require_approval"] == False
    assert low_config["require_reason"] == False
