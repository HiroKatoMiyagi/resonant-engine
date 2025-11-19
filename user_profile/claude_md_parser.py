"""
CLAUDE.md Parser

Sprint 8: User Profile & Persistent Context
CLAUDE.mdから構造化データを抽出
"""

import re
from typing import List, Dict, Any
from datetime import date
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ParsedData(BaseModel):
    """パース済みデータ"""

    profile: Dict[str, Any]
    cognitive_traits: List[Dict[str, Any]]
    family_members: List[Dict[str, Any]]
    goals: List[Dict[str, Any]]
    resonant_concepts: List[Dict[str, Any]]


class ClaudeMdParser:
    """CLAUDE.mdパーサー"""

    def __init__(self, file_path: str = "CLAUDE.md"):
        self.file_path = file_path

    def parse(self) -> ParsedData:
        """
        CLAUDE.mdをパースして構造化データを返す

        Returns:
            ParsedData: パース済みデータ

        Raises:
            FileNotFoundError: ファイルが存在しない
            ValueError: パースエラー
        """
        try:
            content = self._read_file()

            return ParsedData(
                profile=self._parse_profile(content),
                cognitive_traits=self._parse_cognitive_traits(content),
                family_members=self._parse_family(content),
                goals=self._parse_goals(content),
                resonant_concepts=self._parse_resonant_concepts(content),
            )
        except FileNotFoundError:
            logger.error(f"CLAUDE.md not found at: {self.file_path}")
            raise
        except Exception as e:
            logger.error(f"CLAUDE.md parse error: {e}")
            raise ValueError(f"Parse error: {e}")

    def _read_file(self) -> str:
        """ファイル読み込み"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_profile(self, content: str) -> Dict[str, Any]:
        """基本プロフィール抽出"""
        # ユーザー名と生年月日抽出: "ユーザー名：**加藤宏啓（1978/06/23）**"
        name_match = re.search(
            r"ユーザー名：\*\*(.+?)（(\d{4})/(\d{2})/(\d{2})）\*\*", content
        )
        if not name_match:
            raise ValueError("User name and birth date not found")

        full_name = name_match.group(1)
        year, month, day = name_match.group(2), name_match.group(3), name_match.group(4)
        birth_date = date(int(year), int(month), int(day))

        # 居住地抽出: "居住：宮城県名取市"
        location_match = re.search(r"居住：(.+)", content)
        location = location_match.group(1).strip() if location_match else None

        return {
            "user_id": "hiroki",
            "full_name": full_name,
            "birth_date": birth_date,
            "location": location,
        }

    def _parse_cognitive_traits(self, content: str) -> List[Dict[str, Any]]:
        """認知特性抽出"""
        traits = []

        # セクション3: 認知特性（ASD 構造に基づく）
        section3_match = re.search(
            r"# 3\. 認知特性.*?(?=---|\Z)", content, re.DOTALL
        )
        if section3_match:
            section3 = section3_match.group(0)
            # リスト項目を抽出
            trait_items = re.findall(r"^- (.+)$", section3, re.MULTILINE)

            for item in trait_items:
                # トリガーか一般的な認知特性かを判定
                if "苦手" in item or "ストレス" in item:
                    trait_type = "asd_trigger"
                    importance = "critical"
                elif "安心" in item or "提示" in item:
                    trait_type = "asd_preference"
                    importance = "critical"
                else:
                    trait_type = "asd_strength"
                    importance = "high"

                traits.append(
                    {
                        "user_id": "hiroki",
                        "trait_type": trait_type,
                        "trait_name": item.strip(),
                        "description": f"ASD認知特性: {item.strip()}",
                        "importance_level": importance,
                        "handling_strategy": {"approach": "structured_presentation"},
                    }
                )

        # セクション16: 認知トリガーと対処
        section16_match = re.search(
            r"# 16\. 認知トリガーと対処.*?(?=---|\Z)", content, re.DOTALL
        )
        if section16_match:
            section16 = section16_match.group(0)

            # トリガー抽出
            trigger_match = re.search(
                r"### トリガー：(.*?)(?=###|\Z)", section16, re.DOTALL
            )
            if trigger_match:
                trigger_text = trigger_match.group(1)
                trigger_items = re.findall(r"^- (.+)$", trigger_text, re.MULTILINE)

                for item in trigger_items:
                    traits.append(
                        {
                            "user_id": "hiroki",
                            "trait_type": "asd_trigger",
                            "trait_name": item.strip(),
                            "description": f"認知トリガー: {item.strip()}",
                            "importance_level": "critical",
                            "handling_strategy": {"avoid": True},
                        }
                    )

            # 対処方法抽出
            handling_match = re.search(
                r"### 対処：(.*?)(?=###|\Z)", section16, re.DOTALL
            )
            if handling_match:
                handling_text = handling_match.group(1)
                handling_items = re.findall(r"^- (.+)$", handling_text, re.MULTILINE)

                for item in handling_items:
                    traits.append(
                        {
                            "user_id": "hiroki",
                            "trait_type": "asd_preference",
                            "trait_name": item.strip(),
                            "description": f"推奨アプローチ: {item.strip()}",
                            "importance_level": "high",
                            "handling_strategy": {"approach": item.strip()},
                        }
                    )

        return traits

    def _parse_family(self, content: str) -> List[Dict[str, Any]]:
        """家族情報抽出"""
        family = []

        # セクション2: 家族
        section2_match = re.search(r"# 2\. 家族.*?(?=---|\Z)", content, re.DOTALL)
        if not section2_match:
            logger.warning("Family section not found")
            return family

        section2 = section2_match.group(0)

        # 妻抽出: "妻：幸恵（1979/12/18）"
        wife_match = re.search(r"妻：(.+?)（(\d{4})/(\d{2})/(\d{2})）", section2)
        if wife_match:
            name = wife_match.group(1)
            year, month, day = (
                wife_match.group(2),
                wife_match.group(3),
                wife_match.group(4),
            )
            family.append(
                {
                    "user_id": "hiroki",
                    "name": name,
                    "relationship": "spouse",
                    "birth_date": date(int(year), int(month), int(day)),
                }
            )

        # 子ども抽出: "子ども：ひなた、そら（11/5）、優月（8/17）、優陽（12/8）"
        children_match = re.search(r"子ども：(.+)", section2)
        if children_match:
            children_text = children_match.group(1)

            # パターンマッチング
            # ひなた（誕生日なし）
            if "ひなた" in children_text:
                family.append(
                    {
                        "user_id": "hiroki",
                        "name": "ひなた",
                        "relationship": "child",
                        "birth_date": None,
                    }
                )

            # そら（11/5） - 2013年と推定
            sora_match = re.search(r"そら（(\d+)/(\d+)）", children_text)
            if sora_match:
                month, day = sora_match.group(1), sora_match.group(2)
                family.append(
                    {
                        "user_id": "hiroki",
                        "name": "そら",
                        "relationship": "child",
                        "birth_date": date(2013, int(month), int(day)),
                    }
                )

            # 優月（8/17） - 2016年と推定
            yuzuki_match = re.search(r"優月（(\d+)/(\d+)）", children_text)
            if yuzuki_match:
                month, day = yuzuki_match.group(1), yuzuki_match.group(2)
                family.append(
                    {
                        "user_id": "hiroki",
                        "name": "優月",
                        "relationship": "child",
                        "birth_date": date(2016, int(month), int(day)),
                    }
                )

            # 優陽（12/8） - 2012年と推定
            yuhi_match = re.search(r"優陽（(\d+)/(\d+)）", children_text)
            if yuhi_match:
                month, day = yuhi_match.group(1), yuhi_match.group(2)
                family.append(
                    {
                        "user_id": "hiroki",
                        "name": "優陽",
                        "relationship": "child",
                        "birth_date": date(2012, int(month), int(day)),
                    }
                )

        return family

    def _parse_goals(self, content: str) -> List[Dict[str, Any]]:
        """目標抽出"""
        goals = []

        # セクション17: 目標
        section17_match = re.search(r"# 17\. 目標.*?(?=---|\Z)", content, re.DOTALL)
        if not section17_match:
            logger.warning("Goals section not found")
            return goals

        section17 = section17_match.group(0)
        goal_items = re.findall(r"^- (.+)$", section17, re.MULTILINE)

        goal_mapping = {
            "月収50万円": {"category": "financial", "priority": "critical"},
            "Resonant Engine": {"category": "project", "priority": "critical"},
            "研究発表": {"category": "research", "priority": "high"},
            "AAIML": {"category": "research", "priority": "high"},
            "子ども": {"category": "family", "priority": "high"},
        }

        for item in goal_items:
            matched = False
            for key, config in goal_mapping.items():
                if key in item:
                    goals.append(
                        {
                            "user_id": "hiroki",
                            "goal_category": config["category"],
                            "goal_title": item.strip(),
                            "goal_description": item.strip(),
                            "priority": config["priority"],
                            "status": "active",
                        }
                    )
                    matched = True
                    break

            # マッチしなかった項目もmedium優先度で追加
            if not matched:
                goals.append(
                    {
                        "user_id": "hiroki",
                        "goal_category": "other",
                        "goal_title": item.strip(),
                        "goal_description": item.strip(),
                        "priority": "medium",
                        "status": "active",
                    }
                )

        return goals

    def _parse_resonant_concepts(self, content: str) -> List[Dict[str, Any]]:
        """Resonant概念抽出"""
        concepts = []

        # Hiroaki Model抽出（セクション4）
        hiroaki_match = re.search(
            r"# 4\. 宏啓モデル.*?(?=---|\Z)", content, re.DOTALL
        )
        if hiroaki_match:
            section = hiroaki_match.group(0)
            # フェーズ抽出
            phases = re.findall(r"^\d+\. (.+)$", section, re.MULTILINE)

            if phases:
                concepts.append(
                    {
                        "user_id": "hiroki",
                        "concept_type": "model",
                        "concept_name": "Hiroaki Model",
                        "definition": "6段階の思考プロセス（Resonant Intelligence Extension）",
                        "parameters": {"phases": phases},
                        "importance_level": "critical",
                    }
                )

        # ERF抽出（セクション6）
        erf_match = re.search(
            r"# 6\. Emotion Resonance Filter.*?(?=---|\Z)", content, re.DOTALL
        )
        if erf_match:
            concepts.append(
                {
                    "user_id": "hiroki",
                    "concept_type": "metric",
                    "concept_name": "ERF",
                    "definition": "Emotion Resonance Filter - 感情共鳴フィルター",
                    "parameters": {
                        "intensity": {"range": [0, 1], "description": "強度"},
                        "valence": {"range": [-1, 1], "description": "感情の符号"},
                        "cadence": {"range": [0, 1], "description": "リズム"},
                        "detune_threshold": {
                            "intensity": 0.85,
                            "valence_abs": 0.75,
                        },
                    },
                    "importance_level": "high",
                }
            )

        # Crisis Index抽出（セクション7）
        crisis_match = re.search(
            r"# 7\. Crisis Index.*?(?=---|\Z)", content, re.DOTALL
        )
        if crisis_match:
            concepts.append(
                {
                    "user_id": "hiroki",
                    "concept_type": "metric",
                    "concept_name": "Crisis Index",
                    "definition": "危機指数 - システム呼吸の健全性指標",
                    "parameters": {
                        "formula": "E_stress + C_drift + S_break + (1 - A_sync)",
                        "thresholds": {"pre_crisis": 70, "crisis": 85},
                        "max_record": 72,
                        "date": "2025-10-04",
                    },
                    "importance_level": "high",
                }
            )

        return concepts
