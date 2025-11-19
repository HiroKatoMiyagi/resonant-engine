# Sprint 8: User Profile & Persistent Context 作業開始指示書

## 概要

**Sprint**: 8  
**タイトル**: User Profile & Persistent Context  
**期間**: 5日間  
**目標**: CLAUDE.mdのユーザー情報をデータベース化し、Context Assemblerに統合

---

## Day 1: Database Schema & User Profile Repository

### 目標
- PostgreSQL スキーマ設計・作成（5テーブル）
- UserProfileRepository 実装
- 基本的なCRUD操作の実装

### ステップ

#### 1.1 PostgreSQLマイグレーション作成

**ファイル**: `docker/postgres/005_user_profile_tables.sql`

```sql
-- ========================================
-- Sprint 8: User Profile Tables
-- ========================================

-- 1. user_profiles テーブル
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- 基本情報（暗号化）
    full_name VARCHAR(255),
    birth_date DATE,
    location VARCHAR(255),
    
    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    
    -- データ保護
    encryption_key_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_active ON user_profiles(is_active);

-- 2. cognitive_traits テーブル
CREATE TABLE IF NOT EXISTS cognitive_traits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    trait_type VARCHAR(50) NOT NULL,
    trait_name VARCHAR(255) NOT NULL,
    description TEXT,
    importance_level VARCHAR(20) DEFAULT 'medium',
    handling_strategy JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cognitive_traits_user_id ON cognitive_traits(user_id);
CREATE INDEX idx_cognitive_traits_importance ON cognitive_traits(importance_level);

-- 3. family_members テーブル
CREATE TABLE IF NOT EXISTS family_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    birth_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    encryption_key_id VARCHAR(50)
);

CREATE INDEX idx_family_members_user_id ON family_members(user_id);

-- 4. user_goals テーブル
CREATE TABLE IF NOT EXISTS user_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    goal_category VARCHAR(50) NOT NULL,
    goal_title VARCHAR(255) NOT NULL,
    goal_description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    target_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    progress_percentage INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_goals_user_id ON user_goals(user_id);
CREATE INDEX idx_user_goals_priority ON user_goals(priority);
CREATE INDEX idx_user_goals_status ON user_goals(status);

-- 5. resonant_concepts テーブル
CREATE TABLE IF NOT EXISTS resonant_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    concept_type VARCHAR(50) NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    definition TEXT,
    parameters JSONB,
    importance_level VARCHAR(20) DEFAULT 'medium',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_resonant_concepts_user_id ON resonant_concepts(user_id);
CREATE INDEX idx_resonant_concepts_type ON resonant_concepts(concept_type);

-- 初期データ挿入（宏啓さんのプロフィール）
INSERT INTO user_profiles (user_id, full_name, birth_date, location, is_active)
VALUES ('hiroki', '加藤宏啓', '1978-06-23', '宮城県名取市', TRUE)
ON CONFLICT (user_id) DO NOTHING;
```

**実行**:
```bash
docker exec -i resonant-postgres psql -U resonant_user -d resonant_db < docker/postgres/005_user_profile_tables.sql
```

#### 1.2 Pydanticモデル作成

**ファイル**: `user_profile/models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID

class UserProfile(BaseModel):
    """ユーザープロフィール"""
    id: Optional[UUID] = None
    user_id: str
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    encryption_key_id: Optional[str] = None
    is_active: bool = True

class CognitiveTrait(BaseModel):
    """認知特性"""
    id: Optional[UUID] = None
    user_id: str
    trait_type: str
    trait_name: str
    description: Optional[str] = None
    importance_level: str = "medium"
    handling_strategy: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FamilyMember(BaseModel):
    """家族メンバー"""
    id: Optional[UUID] = None
    user_id: str
    name: str
    relationship: str
    birth_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    encryption_key_id: Optional[str] = None

class UserGoal(BaseModel):
    """ユーザー目標"""
    id: Optional[UUID] = None
    user_id: str
    goal_category: str
    goal_title: str
    goal_description: Optional[str] = None
    priority: str = "medium"
    target_date: Optional[date] = None
    status: str = "active"
    progress_percentage: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ResonantConcept(BaseModel):
    """Resonant Engine概念"""
    id: Optional[UUID] = None
    user_id: str
    concept_type: str
    concept_name: str
    definition: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    importance_level: str = "medium"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserProfileData(BaseModel):
    """完全なユーザープロフィールデータ"""
    profile: UserProfile
    cognitive_traits: List[CognitiveTrait] = []
    family_members: List[FamilyMember] = []
    goals: List[UserGoal] = []
    resonant_concepts: List[ResonantConcept] = []
```

#### 1.3 UserProfileRepository実装

**ファイル**: `user_profile/repository.py`

```python
import asyncpg
from typing import Optional, List
from datetime import datetime
import logging

from .models import (
    UserProfile,
    CognitiveTrait,
    FamilyMember,
    UserGoal,
    ResonantConcept,
    UserProfileData
)

logger = logging.getLogger(__name__)

class UserProfileRepository:
    """ユーザープロフィールリポジトリ"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def get_profile(self, user_id: str) -> Optional[UserProfileData]:
        """
        完全なユーザープロフィールを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            UserProfileData: プロフィールデータ（見つからない場合はNone）
        """
        async with self.pool.acquire() as conn:
            # 基本プロフィール
            profile_row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1 AND is_active = TRUE",
                user_id
            )
            
            if not profile_row:
                logger.warning(f"Profile not found for user: {user_id}")
                return None
            
            profile = UserProfile(**dict(profile_row))
            
            # 認知特性
            trait_rows = await conn.fetch(
                "SELECT * FROM cognitive_traits WHERE user_id = $1 ORDER BY importance_level DESC",
                user_id
            )
            cognitive_traits = [CognitiveTrait(**dict(row)) for row in trait_rows]
            
            # 家族情報
            family_rows = await conn.fetch(
                "SELECT * FROM family_members WHERE user_id = $1",
                user_id
            )
            family_members = [FamilyMember(**dict(row)) for row in family_rows]
            
            # 目標
            goal_rows = await conn.fetch(
                "SELECT * FROM user_goals WHERE user_id = $1 AND status = 'active' ORDER BY priority DESC",
                user_id
            )
            goals = [UserGoal(**dict(row)) for row in goal_rows]
            
            # Resonant概念
            concept_rows = await conn.fetch(
                "SELECT * FROM resonant_concepts WHERE user_id = $1 ORDER BY importance_level DESC",
                user_id
            )
            resonant_concepts = [ResonantConcept(**dict(row)) for row in concept_rows]
            
            return UserProfileData(
                profile=profile,
                cognitive_traits=cognitive_traits,
                family_members=family_members,
                goals=goals,
                resonant_concepts=resonant_concepts
            )
    
    async def create_or_update_profile(self, profile: UserProfile) -> UserProfile:
        """プロフィール作成または更新"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO user_profiles 
                    (user_id, full_name, birth_date, location, is_active, encryption_key_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) 
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    birth_date = EXCLUDED.birth_date,
                    location = EXCLUDED.location,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
                RETURNING *
            """, profile.user_id, profile.full_name, profile.birth_date, 
                profile.location, profile.is_active, profile.encryption_key_id)
            
            return UserProfile(**dict(row))
    
    async def add_cognitive_trait(self, trait: CognitiveTrait) -> CognitiveTrait:
        """認知特性追加"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO cognitive_traits
                    (user_id, trait_type, trait_name, description, importance_level, handling_strategy)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                RETURNING *
            """, trait.user_id, trait.trait_type, trait.trait_name, trait.description,
                trait.importance_level, trait.handling_strategy)
            
            return CognitiveTrait(**dict(row))
    
    async def add_family_member(self, member: FamilyMember) -> FamilyMember:
        """家族メンバー追加"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO family_members
                    (user_id, name, relationship, birth_date, encryption_key_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """, member.user_id, member.name, member.relationship, 
                member.birth_date, member.encryption_key_id)
            
            return FamilyMember(**dict(row))
    
    async def add_goal(self, goal: UserGoal) -> UserGoal:
        """目標追加"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO user_goals
                    (user_id, goal_category, goal_title, goal_description, 
                     priority, target_date, status, progress_percentage)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """, goal.user_id, goal.goal_category, goal.goal_title, goal.goal_description,
                goal.priority, goal.target_date, goal.status, goal.progress_percentage)
            
            return UserGoal(**dict(row))
```

### Day 1 成功基準
- [ ] 5つのテーブルがPostgreSQLに作成済み
- [ ] UserProfileRepository がプロフィール取得可能
- [ ] 単体テスト3件以上作成（profile取得、trait追加、goal追加）

### Git Commit
```bash
git add docker/postgres/005_user_profile_tables.sql user_profile/
git commit -m "Add Sprint 8 Day 1: User Profile database schema and repository"
```

---

## Day 2: CLAUDE.md Parser実装

### 目標
- CLAUDE.mdパーサー実装
- 自動データインポート機能
- パースエラーハンドリング

### ステップ

#### 2.1 CLAUDE.md Parser実装

**ファイル**: `user_profile/claude_md_parser.py`

```python
import re
from typing import List, Dict, Any, Optional
from datetime import date
import logging

from .models import (
    UserProfile,
    CognitiveTrait,
    FamilyMember,
    UserGoal,
    ResonantConcept,
    UserProfileData
)

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
                resonant_concepts=self._parse_resonant_concepts(content)
            )
        except Exception as e:
            logger.error(f"CLAUDE.md parse error: {e}")
            raise
    
    def _read_file(self) -> str:
        """ファイル読み込み"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse_profile(self, content: str) -> Dict[str, Any]:
        """基本プロフィール抽出"""
        # ユーザー名抽出: "ユーザー名：**加藤宏啓（1978/06/23）**"
        name_match = re.search(r'ユーザー名：\*\*(.+?)（(\d{4})/(\d{2})/(\d{2})）\*\*', content)
        if not name_match:
            raise ValueError("User name and birth date not found")
        
        full_name = name_match.group(1)
        year, month, day = name_match.group(2), name_match.group(3), name_match.group(4)
        birth_date = date(int(year), int(month), int(day))
        
        # 居住地抽出: "居住：宮城県名取市"
        location_match = re.search(r'居住：(.+)', content)
        location = location_match.group(1).strip() if location_match else None
        
        return {
            "user_id": "hiroki",
            "full_name": full_name,
            "birth_date": birth_date,
            "location": location
        }
    
    def _parse_cognitive_traits(self, content: str) -> List[Dict[str, Any]]:
        """認知特性抽出"""
        traits = []
        
        # セクション3を探す
        section3_match = re.search(r'# 3\. 認知特性.*?(?=# \d+\.|\Z)', content, re.DOTALL)
        if not section3_match:
            logger.warning("Cognitive traits section not found")
            return traits
        
        section3 = section3_match.group(0)
        
        # トリガーリスト抽出
        trigger_match = re.search(r'### トリガー：(.*?)(?=###|\Z)', section3, re.DOTALL)
        if trigger_match:
            trigger_text = trigger_match.group(1)
            # リスト項目を抽出
            trigger_items = re.findall(r'- (.+)', trigger_text)
            
            for item in trigger_items:
                traits.append({
                    "user_id": "hiroki",
                    "trait_type": "asd_trigger",
                    "trait_name": item.strip(),
                    "description": f"ASDトリガー: {item.strip()}",
                    "importance_level": "critical",
                    "handling_strategy": {"avoid": True}
                })
        
        # 対処方法抽出
        handling_match = re.search(r'### 対処：(.*?)(?=###|\Z)', section3, re.DOTALL)
        if handling_match:
            handling_text = handling_match.group(1)
            handling_items = re.findall(r'- (.+)', handling_text)
            
            for item in handling_items:
                traits.append({
                    "user_id": "hiroki",
                    "trait_type": "asd_preference",
                    "trait_name": item.strip(),
                    "description": f"推奨アプローチ: {item.strip()}",
                    "importance_level": "high",
                    "handling_strategy": {"approach": item.strip()}
                })
        
        return traits
    
    def _parse_family(self, content: str) -> List[Dict[str, Any]]:
        """家族情報抽出"""
        family = []
        
        # セクション2を探す
        section2_match = re.search(r'# 2\. 家族.*?(?=# \d+\.|\Z)', content, re.DOTALL)
        if not section2_match:
            logger.warning("Family section not found")
            return family
        
        section2 = section2_match.group(0)
        
        # 妻抽出: "妻：幸恵（1979/12/18）"
        wife_match = re.search(r'妻：(.+?)（(\d{4})/(\d{2})/(\d{2})）', section2)
        if wife_match:
            name = wife_match.group(1)
            year, month, day = wife_match.group(2), wife_match.group(3), wife_match.group(4)
            family.append({
                "user_id": "hiroki",
                "name": name,
                "relationship": "spouse",
                "birth_date": date(int(year), int(month), int(day))
            })
        
        # 子ども抽出: "子ども：ひなた、そら（11/5）、優月（8/17）、優陽（12/8）"
        children_match = re.search(r'子ども：(.+)', section2)
        if children_match:
            children_text = children_match.group(1)
            # 名前と誕生日のペアを抽出
            child_patterns = [
                (r'ひなた', None),
                (r'そら（(\d+)/(\d+)）', 'そら'),
                (r'優月（(\d+)/(\d+)）', '優月'),
                (r'優陽（(\d+)/(\d+)）', '優陽')
            ]
            
            for pattern, name in child_patterns:
                match = re.search(pattern, children_text)
                if match:
                    if name:
                        month, day = match.group(1), match.group(2)
                        family.append({
                            "user_id": "hiroki",
                            "name": name,
                            "relationship": "child",
                            "birth_date": date(2013, int(month), int(day)) if name == "そら" else
                                          date(2016, int(month), int(day)) if name == "優月" else
                                          date(2012, int(month), int(day))
                        })
                    else:
                        family.append({
                            "user_id": "hiroki",
                            "name": "ひなた",
                            "relationship": "child",
                            "birth_date": None
                        })
        
        return family
    
    def _parse_goals(self, content: str) -> List[Dict[str, Any]]:
        """目標抽出"""
        goals = []
        
        # セクション17を探す
        section17_match = re.search(r'# 17\. 目標.*?(?=# \d+\.|\Z)', content, re.DOTALL)
        if not section17_match:
            logger.warning("Goals section not found")
            return goals
        
        section17 = section17_match.group(0)
        goal_items = re.findall(r'- (.+)', section17)
        
        goal_mapping = {
            "月収50万円": {"category": "financial", "priority": "critical"},
            "Resonant Engine": {"category": "project", "priority": "critical"},
            "研究発表": {"category": "research", "priority": "high"},
            "子ども": {"category": "family", "priority": "high"}
        }
        
        for item in goal_items:
            for key, config in goal_mapping.items():
                if key in item:
                    goals.append({
                        "user_id": "hiroki",
                        "goal_category": config["category"],
                        "goal_title": item.strip(),
                        "goal_description": item.strip(),
                        "priority": config["priority"],
                        "status": "active"
                    })
                    break
        
        return goals
    
    def _parse_resonant_concepts(self, content: str) -> List[Dict[str, Any]]:
        """Resonant概念抽出"""
        concepts = []
        
        # Hiroaki Model抽出
        if "宏啓モデル" in content or "Hiroaki Model" in content:
            concepts.append({
                "user_id": "hiroki",
                "concept_type": "model",
                "concept_name": "Hiroaki Model",
                "definition": "6段階の思考プロセス",
                "parameters": {
                    "phases": [
                        "問いの生成",
                        "AIとの対話（外化）",
                        "構造化",
                        "再内省",
                        "現実への落とし込み",
                        "共鳴（Resonance）"
                    ]
                },
                "importance_level": "critical"
            })
        
        # ERF抽出
        if "Emotion Resonance Filter" in content or "ERF" in content:
            concepts.append({
                "user_id": "hiroki",
                "concept_type": "metric",
                "concept_name": "ERF",
                "definition": "Emotion Resonance Filter",
                "parameters": {
                    "intensity": {"range": [0, 1]},
                    "valence": {"range": [-1, 1]},
                    "cadence": {"range": [0, 1]},
                    "detune_threshold": {"intensity": 0.85, "valence_abs": 0.75}
                },
                "importance_level": "high"
            })
        
        # Crisis Index抽出
        if "Crisis Index" in content or "危機指数" in content:
            concepts.append({
                "user_id": "hiroki",
                "concept_type": "metric",
                "concept_name": "Crisis Index",
                "definition": "危機指数",
                "parameters": {
                    "formula": "E_stress + C_drift + S_break + (1 - A_sync)",
                    "thresholds": {"pre_crisis": 70, "crisis": 85},
                    "max_record": 72
                },
                "importance_level": "high"
            })
        
        return concepts
```

#### 2.2 同期機能実装

**ファイル**: `user_profile/sync.py`

```python
import asyncpg
import logging
from typing import Dict, Any

from .claude_md_parser import ClaudeMdParser
from .repository import UserProfileRepository
from .models import (
    UserProfile,
    CognitiveTrait,
    FamilyMember,
    UserGoal,
    ResonantConcept
)

logger = logging.getLogger(__name__)

class ClaudeMdSync:
    """CLAUDE.md同期"""
    
    def __init__(self, pool: asyncpg.Pool, claude_md_path: str = "CLAUDE.md"):
        self.pool = pool
        self.parser = ClaudeMdParser(claude_md_path)
        self.repo = UserProfileRepository(pool)
    
    async def sync(self) -> Dict[str, Any]:
        """
        CLAUDE.mdをパースしてDBに同期
        
        Returns:
            Dict: 同期結果 {"status": "ok", "counts": {...}}
        """
        logger.info("Starting CLAUDE.md sync...")
        
        try:
            # パース
            parsed = self.parser.parse()
            
            # プロフィール同期
            profile = UserProfile(**parsed.profile)
            await self.repo.create_or_update_profile(profile)
            logger.info(f"✅ Profile synced: {profile.user_id}")
            
            # 認知特性同期（既存削除→新規挿入）
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM cognitive_traits WHERE user_id = $1", profile.user_id)
            
            for trait_data in parsed.cognitive_traits:
                trait = CognitiveTrait(**trait_data)
                await self.repo.add_cognitive_trait(trait)
            logger.info(f"✅ Cognitive traits synced: {len(parsed.cognitive_traits)} items")
            
            # 家族同期
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM family_members WHERE user_id = $1", profile.user_id)
            
            for member_data in parsed.family_members:
                member = FamilyMember(**member_data)
                await self.repo.add_family_member(member)
            logger.info(f"✅ Family members synced: {len(parsed.family_members)} items")
            
            # 目標同期
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM user_goals WHERE user_id = $1", profile.user_id)
            
            for goal_data in parsed.goals:
                goal = UserGoal(**goal_data)
                await self.repo.add_goal(goal)
            logger.info(f"✅ Goals synced: {len(parsed.goals)} items")
            
            # Resonant概念同期
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM resonant_concepts WHERE user_id = $1", profile.user_id)
            
            for concept_data in parsed.resonant_concepts:
                concept = ResonantConcept(**concept_data)
                async with self.pool.acquire() as conn:
                    await conn.fetchrow("""
                        INSERT INTO resonant_concepts
                            (user_id, concept_type, concept_name, definition, parameters, importance_level)
                        VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                        RETURNING *
                    """, concept.user_id, concept.concept_type, concept.concept_name,
                        concept.definition, concept.parameters, concept.importance_level)
            logger.info(f"✅ Resonant concepts synced: {len(parsed.resonant_concepts)} items")
            
            # 最終同期時刻更新
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE user_profiles SET last_sync_at = NOW() WHERE user_id = $1",
                    profile.user_id
                )
            
            return {
                "status": "ok",
                "counts": {
                    "cognitive_traits": len(parsed.cognitive_traits),
                    "family_members": len(parsed.family_members),
                    "goals": len(parsed.goals),
                    "resonant_concepts": len(parsed.resonant_concepts)
                }
            }
            
        except Exception as e:
            logger.error(f"CLAUDE.md sync failed: {e}")
            return {"status": "error", "message": str(e)}
```

### Day 2 成功基準
- [ ] CLAUDE.mdパーサーが基本情報・家族・目標を抽出可能
- [ ] sync機能でDBに自動インポート成功
- [ ] パースエラー時に適切なログ出力

### Git Commit
```bash
git add user_profile/claude_md_parser.py user_profile/sync.py
git commit -m "Add Sprint 8 Day 2: CLAUDE.md parser and sync functionality"
```

---

## Day 3: Profile Context Provider実装

### 目標
- プロフィール情報をClaude用コンテキストに変換
- 認知特性ベースのSystem Prompt調整
- トークン効率的なフォーマット

### ステップ

#### 3.1 Profile Context Provider実装

**ファイル**: `user_profile/context_provider.py`

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

from .repository import UserProfileRepository
from .models import UserProfileData, CognitiveTrait, UserGoal

logger = logging.getLogger(__name__)

class ProfileContext(BaseModel):
    """プロフィールコンテキスト"""
    system_prompt_adjustment: str
    context_section: str
    response_guidelines: List[str]
    token_count: int

class ProfileContextProvider:
    """プロフィールコンテキスト提供"""
    
    def __init__(self, profile_repo: UserProfileRepository):
        self.profile_repo = profile_repo
        self.cache: Dict[str, tuple[ProfileContext, float]] = {}  # user_id -> (context, timestamp)
        self.cache_ttl = 3600  # 1時間
    
    async def get_profile_context(
        self,
        user_id: str,
        include_family: bool = True,
        include_goals: bool = True
    ) -> Optional[ProfileContext]:
        """
        プロフィールコンテキストを生成
        
        Args:
            user_id: ユーザーID
            include_family: 家族情報を含めるか
            include_goals: 目標を含めるか
            
        Returns:
            ProfileContext: コンテキスト（見つからない場合はNone）
        """
        # キャッシュチェック
        if user_id in self.cache:
            cached_context, timestamp = self.cache[user_id]
            if (time.time() - timestamp) < self.cache_ttl:
                logger.debug(f"Profile context cache hit: {user_id}")
                return cached_context
        
        # プロフィール取得
        profile_data = await self.profile_repo.get_profile(user_id)
        if not profile_data:
            logger.warning(f"Profile not found: {user_id}")
            return None
        
        # System Prompt調整
        system_adjustment = self._build_system_prompt_adjustment(profile_data.cognitive_traits)
        
        # コンテキストセクション構築
        context_parts = [
            self._build_cognitive_traits_section(profile_data.cognitive_traits)
        ]
        
        if include_family and profile_data.family_members:
            context_parts.append(self._build_family_section(profile_data.family_members))
        
        if include_goals and profile_data.goals:
            context_parts.append(self._build_goals_section(profile_data.goals))
        
        context_section = "\n\n".join(context_parts)
        guidelines = self._build_response_guidelines(profile_data.cognitive_traits)
        token_count = self._estimate_tokens(system_adjustment + context_section)
        
        profile_context = ProfileContext(
            system_prompt_adjustment=system_adjustment,
            context_section=context_section,
            response_guidelines=guidelines,
            token_count=token_count
        )
        
        # キャッシュ保存
        self.cache[user_id] = (profile_context, time.time())
        
        return profile_context
    
    def _build_system_prompt_adjustment(self, traits: List[CognitiveTrait]) -> str:
        """System Prompt調整文生成"""
        critical_traits = [t for t in traits if t.importance_level == 'critical']
        
        if not critical_traits:
            return ""
        
        lines = [
            "## ユーザー認知特性への配慮",
            "",
            "このユーザーはASD（自閉スペクトラム症）の認知特性を持っています。応答時は以下を厳守してください：",
            ""
        ]
        
        # トリガー回避
        triggers = [t for t in traits if t.trait_type == 'asd_trigger']
        if triggers:
            lines.append("**回避すべき表現:**")
            for trigger in triggers:
                lines.append(f"- {trigger.trait_name}")
            lines.append("")
        
        # 推奨アプローチ
        preferences = [t for t in traits if t.trait_type == 'asd_preference']
        if preferences:
            lines.append("**推奨アプローチ:**")
            for pref in preferences:
                lines.append(f"- {pref.trait_name}")
            lines.append("")
        
        lines.extend([
            "**具体的な対応:**",
            "- 常に複数の選択肢を提示し、押し付けない",
            "- 否定形を避け、肯定的・建設的な表現を使う",
            "- 情報を階層的・構造的に提示する",
            "- 一貫性を保ち、矛盾を避ける"
        ])
        
        return "\n".join(lines)
    
    def _build_cognitive_traits_section(self, traits: List[CognitiveTrait]) -> str:
        """認知特性セクション構築"""
        if not traits:
            return ""
        
        lines = [
            "## ユーザー認知特性",
            ""
        ]
        
        for trait in traits[:5]:  # トークン節約のため上位5件
            lines.append(f"- **{trait.trait_name}** ({trait.importance_level}): {trait.description or ''}")
        
        return "\n".join(lines)
    
    def _build_family_section(self, family_members: List[FamilyMember]) -> str:
        """家族セクション構築"""
        if not family_members:
            return ""
        
        lines = [
            "## 家族構成",
            ""
        ]
        
        for member in family_members:
            age_info = ""
            if member.birth_date:
                from datetime import date
                age = (date.today() - member.birth_date).days // 365
                age_info = f" ({age}歳)"
            
            relationship_ja = {
                "spouse": "配偶者",
                "child": "子"
            }.get(member.relationship, member.relationship)
            
            lines.append(f"- {member.name}{age_info} - {relationship_ja}")
        
        return "\n".join(lines)
    
    def _build_goals_section(self, goals: List[UserGoal]) -> str:
        """目標セクション構築"""
        if not goals:
            return ""
        
        lines = [
            "## ユーザー目標",
            ""
        ]
        
        # 優先度順にソート
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_goals = sorted(goals, key=lambda g: priority_order.get(g.priority, 99))
        
        for goal in sorted_goals[:3]:  # 上位3件
            lines.append(f"- **{goal.goal_title}** ({goal.priority}): {goal.goal_description or ''}")
        
        return "\n".join(lines)
    
    def _build_response_guidelines(self, traits: List[CognitiveTrait]) -> List[str]:
        """応答ガイドライン生成"""
        guidelines = [
            "複数の選択肢を提示する",
            "構造化された情報提示",
            "肯定的な表現を使用"
        ]
        
        # 認知特性から追加ガイドライン抽出
        for trait in traits:
            if trait.handling_strategy:
                if "approach" in trait.handling_strategy:
                    guidelines.append(trait.handling_strategy["approach"])
        
        return list(set(guidelines))  # 重複除去
    
    def _estimate_tokens(self, text: str) -> int:
        """トークン数推定（簡易版）"""
        # 日本語: 1文字 = 約2トークン
        # 英語: 1単語 = 約1.3トークン
        japanese_chars = len([c for c in text if ord(c) > 127])
        english_chars = len(text) - japanese_chars
        
        return int(japanese_chars * 2 + english_chars * 0.5)
```

### Day 3 成功基準
- [ ] ProfileContextProviderが認知特性ベースのコンテキスト生成可能
- [ ] System Prompt調整文が適切に生成される
- [ ] トークン推定が500 tokens以下

### Git Commit
```bash
git add user_profile/context_provider.py
git commit -m "Add Sprint 8 Day 3: Profile Context Provider implementation"
```

---

## Day 4: Context Assembler統合

### 目標
- Context AssemblerにUser Profile Layerを追加
- Message BuilderにProfile情報を統合
- Token Managerでプロフィールトークンを考慮

### ステップ

#### 4.1 Context Assembler拡張

**ファイル**: `context_assembler/service.py` (変更)

```python
# 既存のimportに追加
from user_profile.context_provider import ProfileContextProvider, ProfileContext

class AssemblyOptions(BaseModel):
    # 既存フィールド
    max_working_memory: int = 10
    max_semantic_memory: int = 5
    include_session_summary: bool = True
    
    # NEW: User Profile関連
    include_user_profile: bool = True  # ← NEW
    include_family: bool = True         # ← NEW
    include_goals: bool = True          # ← NEW

class AssembledContext(BaseModel):
    # 既存フィールド
    messages: List[Dict[str, Any]]
    metadata: ContextMetadata
    
    # NEW
    profile_context: Optional[ProfileContext] = None  # ← NEW

class ContextAssemblerService:
    def __init__(
        self,
        message_repo: MessageRepository,
        retrieval: RetrievalOrchestrator,
        config: ContextConfig,
        profile_provider: Optional[ProfileContextProvider] = None,  # ← NEW
    ):
        self.message_repo = message_repo
        self.retrieval = retrieval
        self.config = config
        self.profile_provider = profile_provider  # ← NEW
    
    async def assemble_context(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        options: Optional[AssemblyOptions] = None
    ) -> AssembledContext:
        """コンテキスト組み立て（User Profile統合版）"""
        options = options or AssemblyOptions()
        
        # 1. User Profile Context取得
        profile_context = None
        if options.include_user_profile and self.profile_provider:
            try:
                profile_context = await self.profile_provider.get_profile_context(
                    user_id=user_id,
                    include_family=options.include_family,
                    include_goals=options.include_goals
                )
                logger.info(f"✅ Profile context loaded: {profile_context.token_count} tokens")
            except Exception as e:
                logger.warning(f"Failed to load profile context: {e}")
        
        # 2. Memory Layers取得（既存ロジック）
        memory_layers = await self._fetch_memory_layers(
            user_id, session_id, user_message, options
        )
        
        # 3. Messages構築（Profile統合）
        messages = self._build_messages(
            user_message=user_message,
            memory_layers=memory_layers,
            profile_context=profile_context  # ← NEW
        )
        
        # 4. Token推定（Profile含む）
        total_tokens = self._estimate_total_tokens(messages, profile_context)
        
        # 5. メタデータ構築
        metadata = ContextMetadata(
            working_memory_count=len(memory_layers.get("working_memory", [])),
            semantic_memory_count=len(memory_layers.get("semantic_memory", [])),
            session_summary_count=1 if memory_layers.get("session_summary") else 0,
            total_tokens=total_tokens,
            assembly_time_ms=0  # 後で計測
        )
        
        return AssembledContext(
            messages=messages,
            metadata=metadata,
            profile_context=profile_context
        )
    
    def _build_messages(
        self,
        user_message: str,
        memory_layers: Dict[str, Any],
        profile_context: Optional[ProfileContext] = None
    ) -> List[Dict[str, Any]]:
        """メッセージ構築（Profile統合版）"""
        messages = []
        
        # System Message構築
        system_parts = ["あなたはResonant EngineのKana（外界翻訳層）です。"]
        
        # User Profile: System Prompt調整
        if profile_context and profile_context.system_prompt_adjustment:
            system_parts.append("\n")
            system_parts.append(profile_context.system_prompt_adjustment)
        
        # User Profile: コンテキストセクション
        if profile_context and profile_context.context_section:
            system_parts.append("\n")
            system_parts.append(profile_context.context_section)
        
        # Session Summary
        if memory_layers.get("session_summary"):
            system_parts.append("\n## セッション要約\n")
            system_parts.append(memory_layers["session_summary"])
        
        # Semantic Memory
        if memory_layers.get("semantic_memory"):
            system_parts.append("\n## 関連記憶（Semantic Memory）\n")
            for mem in memory_layers["semantic_memory"]:
                system_parts.append(f"- {mem['content']}\n")
        
        messages.append({
            "role": "system",
            "content": "".join(system_parts)
        })
        
        # Working Memory（既存ロジック）
        for msg in memory_layers.get("working_memory", []):
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # User Message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _estimate_total_tokens(
        self,
        messages: List[Dict[str, Any]],
        profile_context: Optional[ProfileContext] = None
    ) -> int:
        """総トークン数推定（Profile含む）"""
        total = 0
        
        # メッセージトークン
        for msg in messages:
            content = msg.get("content", "")
            total += self._estimate_tokens(content)
        
        # Profileトークン（既にcontext内に含まれているが、念のため加算）
        if profile_context:
            total += profile_context.token_count
        
        return total
```

#### 4.2 Factory更新

**ファイル**: `context_assembler/factory.py` (変更)

```python
# 既存のimportに追加
from user_profile.repository import UserProfileRepository
from user_profile.context_provider import ProfileContextProvider

async def create_context_assembler(
    pool: Optional[asyncpg.Pool] = None,
    config: Optional[ContextConfig] = None,
) -> ContextAssemblerService:
    """Context Assemblerインスタンスを生成（User Profile統合版）"""
    
    # 既存ロジック（pool, message_repo, memory_repo, retrieval）
    # ...
    
    # NEW: User Profile Provider初期化
    try:
        profile_repo = UserProfileRepository(pool)
        profile_provider = ProfileContextProvider(profile_repo)
        logger.info("✅ Profile Context Provider initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Profile Provider: {e}")
        profile_provider = None
    
    # Context Assembler初期化
    return ContextAssemblerService(
        message_repo=message_repo,
        retrieval=retrieval,
        config=config or get_default_config(),
        profile_provider=profile_provider,  # ← NEW
    )
```

### Day 4 成功基準
- [ ] Context AssemblerがUser Profileを統合したメッセージ生成可能
- [ ] System PromptにASD認知特性への配慮が含まれる
- [ ] トークン推定が正確（Profile分を含む）

### Git Commit
```bash
git add context_assembler/service.py context_assembler/factory.py
git commit -m "Add Sprint 8 Day 4: Integrate User Profile into Context Assembler"
```

---

## Day 5: テスト＆セキュリティ

### 目標
- 単体テスト・統合テスト作成
- 暗号化機能実装
- E2Eテスト

### ステップ

#### 5.1 単体テスト

**ファイル**: `tests/user_profile/test_parser.py`

```python
import pytest
from user_profile.claude_md_parser import ClaudeMdParser

def test_parse_user_name():
    """ユーザー名抽出テスト"""
    parser = ClaudeMdParser("CLAUDE.md")
    parsed = parser.parse()
    assert parsed.profile["full_name"] == "加藤宏啓"

def test_parse_birth_date():
    """生年月日抽出テスト"""
    parser = ClaudeMdParser("CLAUDE.md")
    parsed = parser.parse()
    assert str(parsed.profile["birth_date"]) == "1978-06-23"

def test_parse_cognitive_traits():
    """認知特性抽出テスト"""
    parser = ClaudeMdParser("CLAUDE.md")
    parsed = parser.parse()
    assert len(parsed.cognitive_traits) >= 4

def test_parse_family_members():
    """家族情報抽出テスト"""
    parser = ClaudeMdParser("CLAUDE.md")
    parsed = parser.parse()
    assert len(parsed.family_members) >= 5

def test_parse_goals():
    """目標抽出テスト"""
    parser = ClaudeMdParser("CLAUDE.md")
    parsed = parser.parse()
    assert len(parsed.goals) >= 3
```

**ファイル**: `tests/user_profile/test_context_provider.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from user_profile.context_provider import ProfileContextProvider
from user_profile.models import UserProfileData, CognitiveTrait

@pytest.mark.asyncio
async def test_get_profile_context():
    """プロフィールコンテキスト取得テスト"""
    repo = MagicMock()
    repo.get_profile = AsyncMock(return_value=UserProfileData(
        profile=MagicMock(user_id="hiroki"),
        cognitive_traits=[
            CognitiveTrait(
                user_id="hiroki",
                trait_type="asd_choice",
                trait_name="選択肢重視",
                importance_level="critical"
            )
        ],
        family_members=[],
        goals=[],
        resonant_concepts=[]
    ))
    
    provider = ProfileContextProvider(repo)
    context = await provider.get_profile_context("hiroki")
    
    assert context is not None
    assert "選択肢" in context.system_prompt_adjustment
    assert context.token_count > 0

@pytest.mark.asyncio
async def test_profile_context_caching():
    """キャッシング機能テスト"""
    repo = MagicMock()
    repo.get_profile = AsyncMock(return_value=MagicMock())
    
    provider = ProfileContextProvider(repo)
    
    # 1回目
    await provider.get_profile_context("hiroki")
    # 2回目（キャッシュヒット）
    await provider.get_profile_context("hiroki")
    
    # get_profileは1回だけ呼ばれる
    assert repo.get_profile.call_count == 1
```

#### 5.2 統合テスト

**ファイル**: `tests/integration/test_user_profile_e2e.py`

```python
import pytest
import asyncpg
from user_profile.sync import ClaudeMdSync
from user_profile.repository import UserProfileRepository
from user_profile.context_provider import ProfileContextProvider
from context_assembler.factory import create_context_assembler

@pytest.mark.asyncio
async def test_full_user_profile_integration():
    """E2E: CLAUDE.md → DB → Context Assembly"""
    # DB接続
    pool = await asyncpg.create_pool(
        "postgresql://resonant_user:password@localhost/resonant_test"
    )
    
    try:
        # 1. CLAUDE.md同期
        sync_service = ClaudeMdSync(pool, "CLAUDE.md")
        result = await sync_service.sync()
        
        assert result["status"] == "ok"
        assert result["counts"]["cognitive_traits"] >= 4
        
        # 2. プロフィール取得
        repo = UserProfileRepository(pool)
        profile_data = await repo.get_profile("hiroki")
        
        assert profile_data is not None
        assert profile_data.profile.full_name == "加藤宏啓"
        assert len(profile_data.cognitive_traits) >= 4
        
        # 3. コンテキスト生成
        provider = ProfileContextProvider(repo)
        context = await provider.get_profile_context("hiroki")
        
        assert context is not None
        assert "認知特性" in context.context_section
        assert context.token_count < 600  # トークン上限チェック
        
        # 4. Context Assembler統合
        assembler = await create_context_assembler(pool)
        assembled = await assembler.assemble_context(
            user_message="次の実装ステップを教えて",
            user_id="hiroki"
        )
        
        assert assembled.profile_context is not None
        assert assembled.messages[0]["role"] == "system"
        assert "認知特性" in assembled.messages[0]["content"]
        
    finally:
        await pool.close()
```

#### 5.3 暗号化実装（オプション）

**ファイル**: `user_profile/encryption.py`

```python
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Optional

class EncryptionService:
    """AES-256-GCM暗号化サービス"""
    
    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            # 環境変数からキー取得
            key_b64 = os.getenv("ENCRYPTION_KEY")
            if not key_b64:
                raise ValueError("ENCRYPTION_KEY environment variable not set")
            key = base64.b64decode(key_b64)
        
        if len(key) != 32:  # 256 bits
            raise ValueError("Encryption key must be 32 bytes")
        
        self.aesgcm = AESGCM(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        文字列を暗号化
        
        Args:
            plaintext: 平文
            
        Returns:
            str: Base64エンコードされた暗号文（nonce + ciphertext）
        """
        nonce = os.urandom(12)  # 96 bits
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')
    
    def decrypt(self, ciphertext_b64: str) -> str:
        """
        暗号文を復号化
        
        Args:
            ciphertext_b64: Base64エンコードされた暗号文
            
        Returns:
            str: 平文
        """
        data = base64.b64decode(ciphertext_b64)
        nonce = data[:12]
        ciphertext = data[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
```

### Day 5 成功基準
- [ ] 単体テスト15件以上作成・全件PASS
- [ ] E2Eテスト成功（CLAUDE.md → DB → Context Assembly）
- [ ] 暗号化機能実装（オプション）

### Git Commit
```bash
git add tests/ user_profile/encryption.py
git commit -m "Add Sprint 8 Day 5: Tests and encryption implementation"
```

---

## 最終確認

### チェックリスト

**Tier 1: 必須要件**
- [ ] User Profile データモデル（PostgreSQL）が実装され、CRUD操作が可能
- [ ] CLAUDE.md Parser が実装され、既存情報を自動インポート可能
- [ ] Profile Context Provider が実装され、Context Assemblerに統合
- [ ] 認知特性（ASD）に基づく応答調整機能が実装
- [ ] 15 件以上の単体/統合テストが作成され、CI で緑

**Tier 2: 品質要件**
- [ ] Profile取得レイテンシ p95 < 50ms（キャッシュあり）
- [ ] CLAUDE.mdとDBの自動同期機能実装
- [ ] 家族情報・目標のコンテキスト統合が正しく動作
- [ ] トークンオーバーヘッド < 500 tokens（プロフィール情報）

### 最終コミット

```bash
git add .
git commit -m "Complete Sprint 8: User Profile & Persistent Context

- PostgreSQL schema with 5 tables (user_profiles, cognitive_traits, family_members, user_goals, resonant_concepts)
- CLAUDE.md parser with auto-sync functionality
- Profile Context Provider with ASD cognitive trait support
- Context Assembler integration with User Profile layer
- 15+ unit and integration tests
- Token overhead: ~500 tokens (0.25% of Claude limit)"

git push -u origin claude/add-conversation-memory-017fnuDD9kLAQh58XR9AKmwB
```

---

**作成日**: 2025-11-18  
**作成者**: Kana (Claude Sonnet 4.5)  
**総行数**: 912
