-- ========================================
-- Sprint 8: User Profile & Persistent Context
-- Database Schema for User Profile Management
-- ========================================

-- 1. user_profiles テーブル
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,

    -- 基本情報（暗号化対象）
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

COMMENT ON TABLE user_profiles IS 'ユーザープロフィール基本情報';
COMMENT ON COLUMN user_profiles.full_name IS '氏名（暗号化推奨）';
COMMENT ON COLUMN user_profiles.birth_date IS '生年月日（暗号化推奨）';
COMMENT ON COLUMN user_profiles.location IS '居住地（暗号化推奨）';
COMMENT ON COLUMN user_profiles.last_sync_at IS 'CLAUDE.md最終同期日時';
COMMENT ON COLUMN user_profiles.encryption_key_id IS '暗号化キーID';

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_active ON user_profiles(is_active);

-- 2. cognitive_traits テーブル
CREATE TABLE IF NOT EXISTS cognitive_traits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,

    -- 認知特性情報
    trait_type VARCHAR(50) NOT NULL,
    trait_name VARCHAR(255) NOT NULL,
    description TEXT,
    importance_level VARCHAR(20) DEFAULT 'medium',
    handling_strategy JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE cognitive_traits IS 'ユーザー認知特性（ASD等）';
COMMENT ON COLUMN cognitive_traits.trait_type IS 'asd_trigger, asd_preference, asd_strength等';
COMMENT ON COLUMN cognitive_traits.trait_name IS '認知特性名';
COMMENT ON COLUMN cognitive_traits.importance_level IS 'critical, high, medium, low';
COMMENT ON COLUMN cognitive_traits.handling_strategy IS '対処戦略（JSON）';

CREATE INDEX idx_cognitive_traits_user_id ON cognitive_traits(user_id);
CREATE INDEX idx_cognitive_traits_importance ON cognitive_traits(importance_level);
CREATE INDEX idx_cognitive_traits_type ON cognitive_traits(trait_type);

-- 3. family_members テーブル
CREATE TABLE IF NOT EXISTS family_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,

    -- 家族情報（暗号化対象）
    name VARCHAR(255) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    birth_date DATE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- データ保護
    encryption_key_id VARCHAR(50)
);

COMMENT ON TABLE family_members IS '家族構成情報';
COMMENT ON COLUMN family_members.name IS '家族の名前（暗号化推奨）';
COMMENT ON COLUMN family_members.relationship IS 'spouse, child, parent等';
COMMENT ON COLUMN family_members.birth_date IS '生年月日（暗号化推奨）';

CREATE INDEX idx_family_members_user_id ON family_members(user_id);
CREATE INDEX idx_family_members_relationship ON family_members(relationship);

-- 4. user_goals テーブル
CREATE TABLE IF NOT EXISTS user_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,

    -- 目標情報
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

COMMENT ON TABLE user_goals IS 'ユーザー目標管理';
COMMENT ON COLUMN user_goals.goal_category IS 'financial, project, research, family等';
COMMENT ON COLUMN user_goals.priority IS 'critical, high, medium, low';
COMMENT ON COLUMN user_goals.status IS 'active, completed, paused, archived';
COMMENT ON COLUMN user_goals.progress_percentage IS '進捗率（0-100）';

CREATE INDEX idx_user_goals_user_id ON user_goals(user_id);
CREATE INDEX idx_user_goals_priority ON user_goals(priority);
CREATE INDEX idx_user_goals_status ON user_goals(status);
CREATE INDEX idx_user_goals_category ON user_goals(goal_category);

-- 5. resonant_concepts テーブル
CREATE TABLE IF NOT EXISTS resonant_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,

    -- Resonant Engine固有概念
    concept_type VARCHAR(50) NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    definition TEXT,
    parameters JSONB,
    importance_level VARCHAR(20) DEFAULT 'medium',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE resonant_concepts IS 'Resonant Engine固有概念（Hiroaki Model, ERF, Crisis Index等）';
COMMENT ON COLUMN resonant_concepts.concept_type IS 'model, metric, regulation, framework等';
COMMENT ON COLUMN resonant_concepts.concept_name IS '概念名';
COMMENT ON COLUMN resonant_concepts.parameters IS '構造化パラメータ（JSON）';
COMMENT ON COLUMN resonant_concepts.importance_level IS 'critical, high, medium, low';

CREATE INDEX idx_resonant_concepts_user_id ON resonant_concepts(user_id);
CREATE INDEX idx_resonant_concepts_type ON resonant_concepts(concept_type);
CREATE INDEX idx_resonant_concepts_importance ON resonant_concepts(importance_level);

-- 初期データ挿入（宏啓さんのプロフィール）
INSERT INTO user_profiles (user_id, full_name, birth_date, location, is_active)
VALUES ('hiroki', '加藤宏啓', '1978-06-23', '宮城県名取市', TRUE)
ON CONFLICT (user_id) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Sprint 8: User Profile tables created successfully!';
    RAISE NOTICE '   - user_profiles';
    RAISE NOTICE '   - cognitive_traits';
    RAISE NOTICE '   - family_members';
    RAISE NOTICE '   - user_goals';
    RAISE NOTICE '   - resonant_concepts';
END $$;
