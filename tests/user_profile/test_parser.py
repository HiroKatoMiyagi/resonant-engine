"""
User Profile Parser Tests

Sprint 8: User Profile & Persistent Context
CLAUDE.md Parserの単体テスト
"""

import pytest
from datetime import date
from user_profile.claude_md_parser import ClaudeMdParser


def test_parse_basic_profile():
    """基本プロフィール抽出テスト"""
    parser = ClaudeMdParser("/home/user/resonant-engine/CLAUDE.md")
    parsed = parser.parse()

    assert parsed.profile["user_id"] == "hiroki"
    assert parsed.profile["full_name"] == "加藤宏啓"
    assert parsed.profile["birth_date"] == date(1978, 6, 23)
    assert "宮城県" in parsed.profile["location"]


def test_parse_cognitive_traits():
    """認知特性抽出テスト"""
    parser = ClaudeMdParser("/home/user/resonant-engine/CLAUDE.md")
    parsed = parser.parse()

    assert len(parsed.cognitive_traits) >= 4

    # トリガーが含まれることを確認
    trait_names = [t["trait_name"] for t in parsed.cognitive_traits]
    assert any("選択肢" in name for name in trait_names)


def test_parse_family_members():
    """家族情報抽出テスト"""
    parser = ClaudeMdParser("/home/user/resonant-engine/CLAUDE.md")
    parsed = parser.parse()

    assert len(parsed.family_members) >= 5

    # 妻の情報確認
    spouse = [m for m in parsed.family_members if m["relationship"] == "spouse"]
    assert len(spouse) == 1
    assert spouse[0]["name"] == "幸恵"
    assert spouse[0]["birth_date"] == date(1979, 12, 18)


def test_parse_goals():
    """目標抽出テスト"""
    parser = ClaudeMdParser("/home/user/resonant-engine/CLAUDE.md")
    parsed = parser.parse()

    assert len(parsed.goals) >= 3

    goal_titles = [g["goal_title"] for g in parsed.goals]
    assert any("月収50万円" in title for title in goal_titles)
    assert any("Resonant Engine" in title for title in goal_titles)


def test_parse_resonant_concepts():
    """Resonant概念抽出テスト"""
    parser = ClaudeMdParser("/home/user/resonant-engine/CLAUDE.md")
    parsed = parser.parse()

    assert len(parsed.resonant_concepts) >= 3

    concept_names = [c["concept_name"] for c in parsed.resonant_concepts]
    assert "Hiroaki Model" in concept_names
    assert "ERF" in concept_names
    assert "Crisis Index" in concept_names
