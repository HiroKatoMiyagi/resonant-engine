"""
Importance Scorer Unit Tests
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加（import前に実行）
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from datetime import datetime, timedelta, timezone
from memory_lifecycle.importance_scorer import ImportanceScorer


def test_time_decay_calculation():
    """時間減衰計算テスト"""
    scorer = ImportanceScorer(None)

    # 1週間経過: 0.95^1 = 0.95
    created_at = datetime.now(timezone.utc) - timedelta(weeks=1)
    decay = scorer.calculate_time_decay(created_at)
    assert 0.94 < decay < 0.96, f"Expected ~0.95, got {decay}"

    # 4週間経過: 0.95^4 ≈ 0.815
    created_at = datetime.now(timezone.utc) - timedelta(weeks=4)
    decay = scorer.calculate_time_decay(created_at)
    assert 0.80 < decay < 0.83, f"Expected ~0.815, got {decay}"

    # 12週間経過: 0.95^12 ≈ 0.540
    created_at = datetime.now(timezone.utc) - timedelta(weeks=12)
    decay = scorer.calculate_time_decay(created_at)
    assert 0.53 < decay < 0.55, f"Expected ~0.54, got {decay}"


def test_access_boost_calculation():
    """アクセス強化計算テスト"""
    scorer = ImportanceScorer(None)

    # アクセス0回: 1.0
    boost = scorer.calculate_access_boost(0)
    assert boost == 1.0

    # アクセス1回: 1.1
    boost = scorer.calculate_access_boost(1)
    assert boost == 1.1

    # アクセス5回: 1.5
    boost = scorer.calculate_access_boost(5)
    assert boost == 1.5

    # アクセス10回: 2.0
    boost = scorer.calculate_access_boost(10)
    assert boost == 2.0


def test_comprehensive_score_calculation():
    """スコア総合計算テスト"""
    scorer = ImportanceScorer(None)

    # ケース1: 新規メモリ（1週間前、アクセスなし）
    # 0.5 × 0.95 × 1.0 = 0.475
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.now(timezone.utc) - timedelta(weeks=1),
        access_count=0
    )
    assert 0.47 < score < 0.48, f"Expected ~0.475, got {score}"

    # ケース2: 頻繁アクセスメモリ（1週間前、5回アクセス）
    # 0.5 × 0.95 × 1.5 = 0.7125
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.now(timezone.utc) - timedelta(weeks=1),
        access_count=5
    )
    assert 0.71 < score < 0.72, f"Expected ~0.7125, got {score}"

    # ケース3: 古いメモリ（4週間前、アクセスなし）
    # 0.5 × 0.815 × 1.0 = 0.4075
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.now(timezone.utc) - timedelta(weeks=4),
        access_count=0
    )
    assert 0.40 < score < 0.42, f"Expected ~0.4075, got {score}"

    # ケース4: 古くて頻繁アクセス（4週間前、10回アクセス）
    # 0.5 × 0.815 × 2.0 = 0.815
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.now(timezone.utc) - timedelta(weeks=4),
        access_count=10
    )
    assert 0.81 < score < 0.83, f"Expected ~0.815, got {score}"


def test_score_clipping():
    """スコアクリッピングテスト"""
    scorer = ImportanceScorer(None)

    # 非常に新しいメモリ with 大量アクセス → 1.0でクリップ
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
        access_count=100  # 極端に多いアクセス
    )
    assert score == 1.0, f"Expected clipped to 1.0, got {score}"

    # 非常に古いメモリ with アクセスなし → 0に近い値（MIN_SCOREでクリップ）
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.now(timezone.utc) - timedelta(weeks=100),
        access_count=0
    )
    assert score >= 0.0, f"Expected >= 0.0, got {score}"
    assert score < 0.01, f"Expected very low score, got {score}"
