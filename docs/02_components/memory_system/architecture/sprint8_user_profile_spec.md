# Sprint 8: User Profile & Persistent Context 詳細仕様書

## 0. CRITICAL: User Context as Breathing Foundation

**⚠️ IMPORTANT: 「ユーザープロフィール = 呼吸の個別化・認知特性への適応」**

User Profile システムは、ユーザーの認知特性、家族構成、目標、価値観を構造化して保持し、Context Assemblerに統合することで、AIが「ユーザーを理解した上で呼吸する」状態を実現します。特にASD認知特性への配慮（構造認知・選択肢提示・一貫性）を記憶システムレベルで実装します。

```yaml
user_profile_philosophy:
    essence: "プロフィール = 呼吸の個別化基盤"
    purpose:
        - ユーザーの認知特性に基づく応答最適化
        - 家族・目標・価値観のコンテキスト化
        - ASD認知特性への構造的配慮
        - CLAUDE.mdの構造化データベース化
    principles:
        - "認知特性は応答戦略を決定する"
        - "家族情報は感情的文脈を提供する"
        - "目標は優先順位付けの基準となる"
        - "個人情報は最高レベルで保護される"
```

### 呼吸サイクルとの関係

```
User Profile (認知特性・価値観)
    ↓
Context Assembler (3層記憶 + ユーザー文脈)
    ↓
Claude API (個別化された応答)
    ↓
認知特性に適合した出力（構造化・選択肢提示）
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] User Profileデータモデル（PostgreSQL）が実装され、CRUD操作が可能
- [ ] CLAUDE.md Parser が実装され、既存情報を自動インポート可能
- [ ] Profile Context Providerが実装され、Context Assemblerに統合
- [ ] 認知特性（ASD）に基づく応答調整機能が実装
- [ ] PII（個人識別情報）保護機能が実装（暗号化・アクセス制御）
- [ ] 15 件以上の単体/統合テストが作成され、CI で緑

#### Tier 2: 品質要件
- [ ] Profile取得レイテンシ p95 < 50ms（キャッシュあり）
- [ ] CLAUDE.mdとDBの自動同期機能実装
- [ ] 家族情報・目標のコンテキスト統合が正しく動作
- [ ] トークンオーバーヘッド < 500 tokens（プロフィール情報）
- [ ] Observability: `profile_load_latency_ms`, `profile_cache_hit_rate`
- [ ] Kana レビュー向けに「認知特性配慮設計」がドキュメント化

---

## 1. 概要

### 1.1 目的
CLAUDE.mdに記載されたユーザー情報（認知特性、家族、目標、価値観）を構造化データベースに保存し、Context Assemblerに統合することで、個別化された文脈を提供する**User Profile管理システム**を実装する。

### 1.2 背景
**現状の問題:**
- CLAUDE.mdは人間が読むテキストであり、プログラムから参照困難
- ユーザーの認知特性（ASD）が記憶システムレベルで考慮されていない
- 家族情報・目標がClaude応答に反映されていない
- 毎回同じユーザー情報を再説明する必要がある
- 個人情報が散在し、セキュリティリスクが高い

**Sprint 1-7での成果:**
- Sprint 5: Context Assembler実装（3層記憶統合）
- Sprint 6: Intent Bridge統合完了
- Sprint 7: Session Summary自動生成完了

**残課題:**
ユーザープロフィール情報がContext Assemblerに統合されていないため、個別化された応答が実現できていない。

### 1.3 目標
- CLAUDE.mdの構造化データベース化（自動インポート）
- User Profile情報をContext Assemblerに統合
- 認知特性（ASD）に基づく応答調整機能実装
- PII保護の強化（暗号化・アクセス制御）
- プロフィール情報のトークンオーバーヘッド < 500 tokens

### 1.4 スコープ
**含む:**
- User Profile データモデル設計（PostgreSQL）
- CLAUDE.md Parser実装
- Profile Context Provider実装
- Context Assembler統合
- 認知特性ベース応答調整
- PII保護機能

**含まない（将来拡張）:**
- ERF（Emotion Resonance Filter）統合（Sprint 9）
- Crisis Index統合（Sprint 10）
- ユーザー設定UI（Dashboard Phase 2）
- マルチユーザー対応（現状は宏啓さん専用）

---

## 2. ユースケース

### 2.1 ASD認知特性への配慮

**シナリオ:**
宏啓さんが「次の実装ステップを教えて」と質問した際、Claudeは以下の認知特性に基づき応答を調整する：

**認知特性（DBから取得）:**
- 強い構造認知・時系列認知
- 選択肢を奪われることが苦手
- 一貫性の破壊に強いストレス
- 「否定」よりも「選択肢提示」が安心

**応答調整:**
```
❌ 悪い応答（認知特性無視）:
"それはやめて、こっちの方法にしてください。"

✅ 良い応答（認知特性配慮）:
"次のステップには3つの選択肢があります：
1. A案: メリット... デメリット...
2. B案: メリット... デメリット...
3. C案: メリット... デメリット...
どれを選びますか？"
```

### 2.2 家族コンテキストの活用

**シナリオ:**
宏啓さんが「今日は疲れた」と発言した際、家族情報を考慮して応答する。

**家族情報（DBから取得）:**
- 妻：幸恵（1979/12/18）
- 子ども：ひなた、そら（11/5）、優月（8/17）、優陽（12/8）

**応答例:**
```
"お疲れ様です、宏啓さん。4人のお子さんがいる中での開発は大変ですね。
今日は早めに休んで、明日のセッションで続きを進めましょうか？"
```

### 2.3 目標追跡とコンテキスト

**シナリオ:**
宏啓さんが「次に何をすべきか？」と質問した際、目標情報を参照して応答する。

**目標（DBから取得）:**
- 月収50万円（家族の安全基盤）
- Resonant Engine の社会実装
- 研究発表（AAIML等）

**応答例:**
```
"現在の目標「月収50万円」に向けては、Resonant Engineの社会実装が優先です。
次のステップは：
1. Sprint 8完了（User Profile）
2. MVP版のデプロイ準備
3. AAIML論文執筆開始
優先順位はどれにしますか？"
```

### 2.4 Hiroaki Model（6段階）の支援

**シナリオ:**
宏啓さんの思考プロセス（6段階）を記憶システムが支援する。

**6段階:**
1. 問いの生成
2. AIとの対話（外化）
3. 構造化
4. 再内省
5. 現実への落とし込み
6. 共鳴（Resonance）

**システム支援:**
- Phase 1-2: Working Memory で対話履歴を保持
- Phase 3: Semantic Memory で過去の構造化を参照
- Phase 4-5: Session Summary で内省の軌跡を記録
- Phase 6: **User Profile** で価値観・目標との共鳴を確認

---

## 3. アーキテクチャ

### 3.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│               Context Assembler (拡張)                   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Memory Layer Fetcher                            │  │
│  │  - Working Memory (直近10件)                     │  │
│  │  - Semantic Memory (関連5件)                     │  │
│  │  - Session Summary                               │  │
│  │  - User Profile Context ← NEW                    │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                        │
│  ┌──────────────▼───────────────────────────────────┐  │
│  │  Message Builder (拡張)                          │  │
│  │  - System Prompt構築                             │  │
│  │  - User Profile挿入 ← NEW                        │  │
│  │  - Memory挿入                                    │  │
│  │  - Working Memory挿入                            │  │
│  │  - User Message挿入                              │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                        │
│  ┌──────────────▼───────────────────────────────────┐  │
│  │  Token Manager                                   │  │
│  │  - Profile Token推定 ← NEW                       │  │
│  │  - トークン数推定                                 │  │
│  │  - コンテキスト圧縮                               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
          ↓
    KanaAIBridge → Claude API

┌─────────────────────────────────────────────────────────┐
│         User Profile System (NEW)                        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  CLAUDE.md Parser                                │  │
│  │  - Markdown → 構造化データ                        │  │
│  │  - 自動同期（ファイル監視）                       │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                        │
│  ┌──────────────▼───────────────────────────────────┐  │
│  │  User Profile Repository                         │  │
│  │  - CRUD操作（PostgreSQL）                        │  │
│  │  - PII暗号化                                     │  │
│  │  - キャッシング（Redis）                          │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                        │
│  ┌──────────────▼───────────────────────────────────┐  │
│  │  Profile Context Provider                        │  │
│  │  - 認知特性 → System Prompt調整                   │  │
│  │  - 家族情報 → コンテキスト挿入                     │  │
│  │  - 目標 → 優先順位付け支援                        │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 データフロー

```
[User Message]
    ↓
1. Context Assembler.assemble_context(user_message, user_id)
    ↓
2. Profile Context Provider.get_profile_context(user_id)
   ├─ User Profile Repository.get_profile(user_id)
   |   └─ キャッシュチェック → DB取得 → 暗号化解除
   |
   └─ 認知特性 → System Prompt調整指示生成
    ↓
3. Memory Layer Fetcher (並行取得)
   ├─ Working Memory (直近10件)
   ├─ Semantic Memory (関連5件)
   ├─ Session Summary
   └─ User Profile Context ← NEW
    ↓
4. Message Builder
   ├─ System Prompt + Profile調整 ← NEW
   ├─ "## ユーザー認知特性" セクション挿入 ← NEW
   ├─ Semantic Memory挿入
   ├─ Working Memory挿入
   └─ User Message挿入
    ↓
5. Token Manager
   ├─ Profile Token推定（~300-500 tokens）
   └─ 合計トークン推定 → 圧縮判定
    ↓
6. Claude API呼び出し（個別化されたコンテキスト）
```

---

## 4. データモデル

### 4.1 user_profiles テーブル

**テーブル定義:**

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,

    -- 基本情報（暗号化）
    full_name VARCHAR(255),  -- 暗号化: 加藤宏啓
    birth_date DATE,          -- 暗号化: 1978-06-23
    location VARCHAR(255),    -- 暗号化: 宮城県名取市

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sync_at TIMESTAMP WITH TIME ZONE,  -- CLAUDE.md最終同期

    -- データ保護
    encryption_key_id VARCHAR(50),  -- 暗号化キーID
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

### 4.2 cognitive_traits テーブル

**テーブル定義:**

```sql
CREATE TABLE cognitive_traits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id),

    -- ASD認知特性
    trait_type VARCHAR(50) NOT NULL,  -- "asd_structure", "asd_choice", etc.
    trait_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- 影響度
    importance_level VARCHAR(20),  -- "critical", "high", "medium", "low"

    -- 対処戦略
    handling_strategy JSONB,  -- {"approach": "choice_presentation", "avoid": ["negation", "force"]}

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cognitive_traits_user_id ON cognitive_traits(user_id);
CREATE INDEX idx_cognitive_traits_importance ON cognitive_traits(importance_level);
```

**データ例:**

```sql
INSERT INTO cognitive_traits (user_id, trait_type, trait_name, description, importance_level, handling_strategy)
VALUES
    ('hiroki', 'asd_structure', '強い構造認知', '事実 → 構造化 → 意味 → 行動 という思考流れ', 'critical',
     '{"approach": "structured_presentation", "format": "hierarchical"}'),
    ('hiroki', 'asd_choice', '選択肢の重視', '選択肢を奪われることが苦手', 'critical',
     '{"approach": "choice_presentation", "avoid": ["single_option", "forced_decision"]}'),
    ('hiroki', 'asd_consistency', '一貫性重視', '一貫性の破壊に強いストレス', 'high',
     '{"approach": "consistency_check", "avoid": ["contradiction", "sudden_change"]}'),
    ('hiroki', 'asd_negation', '否定への敏感さ', '「否定」よりも「選択肢提示」が安心', 'critical',
     '{"approach": "affirmative_framing", "avoid": ["negation", "rejection"]}');
```

### 4.3 family_members テーブル

**テーブル定義:**

```sql
CREATE TABLE family_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id),

    -- 家族情報（暗号化）
    name VARCHAR(255) NOT NULL,        -- 暗号化: 幸恵
    relationship VARCHAR(50) NOT NULL, -- "spouse", "child"
    birth_date DATE,                   -- 暗号化: 1979-12-18

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- データ保護
    encryption_key_id VARCHAR(50)
);

CREATE INDEX idx_family_members_user_id ON family_members(user_id);
```

**データ例:**

```sql
INSERT INTO family_members (user_id, name, relationship, birth_date)
VALUES
    ('hiroki', '幸恵', 'spouse', '1979-12-18'),
    ('hiroki', 'ひなた', 'child', NULL),
    ('hiroki', 'そら', 'child', '2013-11-05'),
    ('hiroki', '優月', 'child', '2016-08-17'),
    ('hiroki', '優陽', 'child', '2012-12-08');
```

### 4.4 user_goals テーブル

**テーブル定義:**

```sql
CREATE TABLE user_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id),

    -- 目標情報
    goal_category VARCHAR(50) NOT NULL,  -- "financial", "project", "research", "family"
    goal_title VARCHAR(255) NOT NULL,
    goal_description TEXT,

    -- 優先順位
    priority VARCHAR(20),  -- "critical", "high", "medium", "low"
    target_date DATE,

    -- ステータス
    status VARCHAR(20) DEFAULT 'active',  -- "active", "completed", "paused"
    progress_percentage INTEGER DEFAULT 0,

    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_goals_user_id ON user_goals(user_id);
CREATE INDEX idx_user_goals_priority ON user_goals(priority);
```

**データ例:**

```sql
INSERT INTO user_goals (user_id, goal_category, goal_title, goal_description, priority, status)
VALUES
    ('hiroki', 'financial', '月収50万円達成', '家族の安全基盤を確立する', 'critical', 'active'),
    ('hiroki', 'project', 'Resonant Engine社会実装', 'MVP版リリース→実用化', 'critical', 'active'),
    ('hiroki', 'research', 'AAIML研究発表', '論文執筆・学会発表', 'high', 'active'),
    ('hiroki', 'family', '子どもの安全とresonant growth', '教育・生活環境の整備', 'high', 'active');
```

### 4.5 resonant_concepts テーブル

**テーブル定義:**

```sql
CREATE TABLE resonant_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id),

    -- Resonant Engine固有概念
    concept_type VARCHAR(50) NOT NULL,  -- "model", "regulation", "metric", "framework"
    concept_name VARCHAR(255) NOT NULL,

    -- 概念定義
    definition TEXT,
    parameters JSONB,  -- 構造化パラメータ

    -- 重要度
    importance_level VARCHAR(20),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_resonant_concepts_user_id ON resonant_concepts(user_id);
CREATE INDEX idx_resonant_concepts_type ON resonant_concepts(concept_type);
```

**データ例:**

```sql
INSERT INTO resonant_concepts (user_id, concept_type, concept_name, definition, parameters, importance_level)
VALUES
    ('hiroki', 'model', 'Hiroaki Model', '6段階の思考プロセス',
     '{"phases": ["問いの生成", "AIとの対話", "構造化", "再内省", "現実への落とし込み", "共鳴"]}', 'critical'),
    ('hiroki', 'metric', 'ERF', 'Emotion Resonance Filter',
     '{"intensity": {"range": [0, 1]}, "valence": {"range": [-1, 1]}, "cadence": {"range": [0, 1]}, "detune_threshold": {"intensity": 0.85, "valence_abs": 0.75}}', 'high'),
    ('hiroki', 'metric', 'Crisis Index', '危機指数',
     '{"formula": "E_stress + C_drift + S_break + (1 - A_sync)", "thresholds": {"pre_crisis": 70, "crisis": 85}, "max_record": 72}', 'high'),
    ('hiroki', 'regulation', 'Regulation §7', '呼吸優先原則',
     '{"principle": "まず深く動き、スピードは後から得る", "constraint": "検証/評価層の軽量化は禁止（未熟時）"}', 'critical');
```

---

## 5. コンポーネント設計

### 5.1 CLAUDE.md Parser

**ファイル:** `user_profile/claude_md_parser.py`

**責務:**
- CLAUDE.mdをパースして構造化データに変換
- ファイル変更監視と自動同期
- データ検証とエラーハンドリング

**実装詳細:**

```python
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import date
import re

class ParsedProfile(BaseModel):
    """パース済みプロフィール"""
    user_id: str
    full_name: str
    birth_date: date
    location: str
    cognitive_traits: List[Dict[str, Any]]
    family_members: List[Dict[str, Any]]
    goals: List[Dict[str, Any]]
    resonant_concepts: List[Dict[str, Any]]

class ClaudeMdParser:
    """CLAUDE.mdパーサー"""

    def __init__(self, file_path: str = "/home/user/resonant-engine/CLAUDE.md"):
        self.file_path = file_path

    def parse(self) -> ParsedProfile:
        """
        CLAUDE.mdをパースして構造化データを返す

        Returns:
            ParsedProfile: パース済みプロフィール

        Raises:
            FileNotFoundError: CLAUDE.mdが存在しない
            ValueError: パースエラー
        """
        content = self._read_file()

        return ParsedProfile(
            user_id=self._extract_user_id(content),
            full_name=self._extract_full_name(content),
            birth_date=self._extract_birth_date(content),
            location=self._extract_location(content),
            cognitive_traits=self._extract_cognitive_traits(content),
            family_members=self._extract_family_members(content),
            goals=self._extract_goals(content),
            resonant_concepts=self._extract_resonant_concepts(content)
        )

    def _extract_full_name(self, content: str) -> str:
        """フルネーム抽出"""
        match = re.search(r'ユーザー名：\*\*(.+?)（', content)
        if match:
            return match.group(1)
        raise ValueError("Full name not found")

    def _extract_birth_date(self, content: str) -> date:
        """生年月日抽出"""
        match = re.search(r'（(\d{4})/(\d{2})/(\d{2})）', content)
        if match:
            year, month, day = match.groups()
            return date(int(year), int(month), int(day))
        raise ValueError("Birth date not found")

    def _extract_cognitive_traits(self, content: str) -> List[Dict[str, Any]]:
        """認知特性抽出"""
        traits = []
        section = self._extract_section(content, "認知特性")

        trait_configs = {
            "強い構造認知": {"type": "asd_structure", "importance": "critical"},
            "選択肢を奪われることが苦手": {"type": "asd_choice", "importance": "critical"},
            "一貫性の破壊に強いストレス": {"type": "asd_consistency", "importance": "high"},
            "否定": {"type": "asd_negation", "importance": "critical"}
        }

        for trait_text, config in trait_configs.items():
            if trait_text in section:
                traits.append({
                    "trait_type": config["type"],
                    "trait_name": trait_text,
                    "description": trait_text,
                    "importance_level": config["importance"],
                    "handling_strategy": {"approach": "choice_presentation"}
                })

        return traits

    def _read_file(self) -> str:
        """ファイル読み込み"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
```

### 5.2 Profile Context Provider

**ファイル:** `user_profile/context_provider.py`

**責務:**
- プロフィール情報をClaude用コンテキストに変換
- 認知特性に基づくSystem Prompt調整
- トークン効率的なフォーマット

```python
from typing import Dict, Any, Optional
from pydantic import BaseModel

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

    async def get_profile_context(
        self,
        user_id: str,
        include_family: bool = True,
        include_goals: bool = True
    ) -> Optional[ProfileContext]:
        """プロフィールコンテキストを生成"""
        profile = await self.profile_repo.get_profile(user_id)
        if not profile:
            return None

        # System Prompt調整
        system_adjustment = self._build_system_prompt_adjustment(profile.cognitive_traits)

        # コンテキストセクション構築
        context_parts = [
            self._build_cognitive_traits_section(profile.cognitive_traits)
        ]

        if include_family:
            context_parts.append(self._build_family_section(profile.family_members))

        if include_goals:
            context_parts.append(self._build_goals_section(profile.goals))

        context_section = "\n\n".join(context_parts)
        guidelines = self._build_response_guidelines(profile.cognitive_traits)
        token_count = self._estimate_tokens(system_adjustment + context_section)

        return ProfileContext(
            system_prompt_adjustment=system_adjustment,
            context_section=context_section,
            response_guidelines=guidelines,
            token_count=token_count
        )

    def _build_system_prompt_adjustment(self, traits: List[Dict]) -> str:
        """System Prompt調整文生成"""
        critical_traits = [t for t in traits if t.get('importance_level') == 'critical']

        adjustments = [
            "**重要: ユーザー認知特性への配慮**",
            "このユーザーはASD（自閉スペクトラム症）の認知特性を持っています。応答時は以下を厳守してください：",
            "- 常に複数の選択肢を提示し、押し付けない",
            "- 否定形を避け、肯定的・建設的な表現を使う",
            "- 情報を階層的・構造的に提示する",
            "- 一貫性を保ち、矛盾を避ける"
        ]

        return "\n".join(adjustments)
```

### 5.3 Context Assembler統合

**変更内容:**

```python
class ContextAssemblerService:
    def __init__(
        self,
        profile_context_provider: ProfileContextProvider,  # ← NEW
        # ... 他のパラメータ
    ):
        self.profile_provider = profile_context_provider

    async def assemble_context(
        self,
        user_message: str,
        user_id: str,
        options: Optional[AssemblyOptions] = None
    ) -> AssembledContext:
        # 1. プロフィールコンテキスト取得
        profile_context = None
        if options.include_user_profile:
            profile_context = await self.profile_provider.get_profile_context(user_id)

        # 2. メッセージ構築（プロフィール統合）
        messages = self._build_messages(memory_layers, profile_context)

        # ...
```

---

## 6. トークン見積もり

### 6.1 プロフィール情報のトークンオーバーヘッド

**想定データ:**
- 認知特性: 4件 × 50 tokens = 200 tokens
- 家族情報: 5人 × 20 tokens = 100 tokens
- 目標: 3件 × 50 tokens = 150 tokens
- System Prompt調整: 50 tokens

**合計: 約500 tokens**

**トークン上限（Claude Sonnet 4.5）:** 200,000 tokens
**プロフィールオーバーヘッド:** 500 / 200,000 = **0.25%**

---

## 7. エラーハンドリング

### 7.1 CLAUDE.mdパースエラー

```python
try:
    parser = ClaudeMdParser()
    parsed = parser.parse()
except FileNotFoundError:
    logger.error("CLAUDE.md not found")
    # Fallback: デフォルトプロフィール使用
except ValueError as e:
    logger.error(f"Parse error: {e}")
    # Fallback: 部分的にパース済みのデータを使用
```

### 7.2 プロフィール取得失敗時

```python
profile_context = await profile_provider.get_profile_context(user_id)
if not profile_context:
    logger.warning(f"Profile not found for user {user_id}, using default")
    # Fallback: プロフィールなしで Context Assembly 続行
```

---

## 8. パフォーマンス

### 8.1 キャッシング戦略

**Layer 1: In-Memory Cache**
```python
self.cache = {}  # user_id → UserProfileData
TTL = 3600  # 1時間
```

### 8.2 レイテンシ目標

| 操作 | 目標レイテンシ |
|------|--------------|
| Profile取得（キャッシュあり） | < 10ms |
| Profile取得（キャッシュなし） | < 50ms |
| CLAUDE.md同期 | < 500ms |
| Context組み立て（Profile含む） | < 150ms |

---

## 9. セキュリティ

### 9.1 PII（個人識別情報）保護

**対象データ:**
- 氏名（full_name）
- 生年月日（birth_date）
- 居住地（location）
- 家族名（family_members.name）

**保護手段:**

```python
class EncryptionService:
    """AES-256-GCM暗号化"""

    def encrypt(self, plaintext: str) -> str:
        """暗号化"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = os.urandom(12)
        aesgcm = AESGCM(self.key.encode())
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def decrypt(self, ciphertext_b64: str) -> str:
        """復号化"""
        # ... 実装
```

---

## 10. テスト戦略

### 10.1 単体テスト

```python
def test_parse_user_name():
    parser = ClaudeMdParser("test_data/CLAUDE.md")
    parsed = parser.parse()
    assert parsed.full_name == "加藤宏啓"

def test_parse_cognitive_traits():
    parser = ClaudeMdParser("test_data/CLAUDE.md")
    parsed = parser.parse()
    assert len(parsed.cognitive_traits) >= 4
```

### 10.2 統合テスト

```python
@pytest.mark.asyncio
async def test_full_profile_integration(db_pool):
    """E2E: CLAUDE.md → DB → Context Assembly"""
    # 1. CLAUDE.md同期
    result = await sync_claude_md_to_db(pool=db_pool)
    assert result['status'] == 'ok'

    # 2. コンテキスト生成
    context = await provider.get_profile_context("hiroki")
    assert "認知特性" in context.context_section
```

---

## 11. 制約と前提

### 11.1 制約
- PostgreSQL 13+（gen_random_uuid()使用）
- Python 3.9+（asyncio、型ヒント）
- 現状は単一ユーザー（宏啓さん）専用

### 11.2 前提
- Context Assembler（Sprint 5）実装済み
- PostgreSQLスキーマ作成可能
- 環境変数`ENCRYPTION_KEY`が安全に管理されている

---

## 12. 今後の拡張

### 12.1 Sprint 9: ERF統合
- Emotion Resonance Filterによる応答調整

### 12.2 Sprint 10: Crisis Index統合
- Crisis Index監視と対応

### 12.3 マルチユーザー対応
- 複数ユーザーのプロフィール管理

---

## 13. 参考資料

- [Sprint 5: Context Assembler仕様書](./sprint5_context_assembler_spec.md)
- [Sprint 6: Intent Bridge統合仕様書](./sprint6_intent_bridge_integration_spec.md)
- [Sprint 7: Session Summary仕様書](./sprint7_session_summary_spec.md)
- [CLAUDE.md](../../CLAUDE.md)
- [PostgreSQL暗号化ベストプラクティス](https://www.postgresql.org/docs/current/encryption-options.html)
- [Claude API - System Prompts](https://docs.anthropic.com/claude/docs/system-prompts)

---

**作成日**: 2025-11-18
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**レビュー状態**: Draft
**総行数**: 878