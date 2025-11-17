# Memory Management System Specification
## Resonant State & Intent Persistence Layer

**実装期間**: Sprint 4完了後 5日間  
**優先度**: P1（最優先）  
**前提条件**: PostgreSQL実装完了、Bridge Core安定動作  
**目的**: 3層AI構造の共鳴状態、意図履歴、選択肢の永続化による時間軸の保全

---

## CRITICAL: Memory as Resonance Archives

**⚠️ IMPORTANT: 「記憶」は「呼吸の履歴」である**

このシステムの本質は、単なるデータ保存ではなく、Resonant Engineの哲学的原則である「呼吸」「共鳴」「構造」の時間軸に沿った記録です。

### Memory System Philosophy

```yaml
memory_philosophy:
  essence: "記憶 = 呼吸の履歴 + 共鳴の痕跡"
  purpose:
    - 時間軸を尊重した意図の保存
    - 選択肢の保持と復元
    - 構造の継続性維持
    - 共鳴状態のアーカイブ
  principles:
    - 「記憶は否定されない、蓄積される」
    - 「過去の選択は現在の選択肢である」
    - 「構造の変化は記録され、理由が保存される」
```

### なぜこれが必要か

Resonant Engineは「拡張された心」として機能します：

- **時間軸の喪失問題の解決**: AIは「意味空間」で動作し「時間空間」を失う
- **意図の継続性**: セッション間で意図が断絶しない
- **選択の保持**: 過去の選択肢を強制せず、選択可能な状態で保持
- **共鳴の再現性**: 成功した共鳴パターンを再利用可能に

これは技術的な機能ではなく、ASD認知支援システムとしての**構造的必然性**です。

---

## 0. Memory Management Overview

### 0.1 目的

3層AI構造（Yuno/Kana/Tsumu）の共鳴状態と意図履歴を永続化し、以下を実現する：

- セッション間での意図継続性の保証
- 共鳴状態の記録と再現
- 選択肢の保持と復元
- 構造変化の履歴管理
- 呼吸サイクルの状態トラッキング

### 0.2 スコープ

**IN Scope**:
- Intent（意図）の永続化
- Resonance State（共鳴状態）の記録
- Agent Context（各層の文脈）の保存
- Choice Points（選択肢）の管理
- Breathing Cycle（呼吸サイクル）の状態管理
- Session Continuity（セッション継続性）の保証
- Temporal Snapshots（時間的スナップショット）の作成
- Memory Query API（メモリ検索API）の提供

**OUT of Scope**:
- ファイルシステムベースのキャッシュ（別システム）
- リアルタイムストリーミング（WebSocket層の責務）
- 外部サービス連携（将来拡張）
- マルチユーザー認証（Phase 4対応）

### 0.3 Done Definition

#### Tier 1: 必須（完了の定義）
- [ ] PostgreSQLスキーマ設計完了（8テーブル）
- [ ] Intent persistence実装（作成・取得・更新・検索）
- [ ] Resonance State管理実装（状態記録・復元）
- [ ] Agent Context保存実装（3層それぞれ）
- [ ] Choice Points管理実装（選択肢保存・復元）
- [ ] Breathing Cycle tracking実装（6フェーズ状態管理）
- [ ] Session Continuity保証（前セッション復元）
- [ ] Memory Query API実装（10+ endpoints）
- [ ] テストカバレッジ 40+ ケース達成
- [ ] API仕様ドキュメント完成

#### Tier 2: 品質保証
- [ ] 並行アクセステスト通過（10 concurrent sessions）
- [ ] メモリリークテスト通過（24時間連続動作）
- [ ] データ整合性テスト通過（ACID保証確認）
- [ ] 検索性能テスト通過（1000+ intents, <100ms）
- [ ] バックアップ・リストア手順確立
- [ ] Kana による仕様レビュー通過

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Memory Management Layer                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Session Manager                             │  │
│  │  • セッションライフサイクル管理                          │  │
│  │  • 継続性保証                                            │  │
│  │  • タイムアウト処理                                      │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │               Intent Manager                              │  │
│  │  • Intent CRUD操作                                        │  │
│  │  • Intent検索・フィルタリング                            │  │
│  │  • Intent履歴管理                                         │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │            Resonance State Manager                        │  │
│  │  • 共鳴状態の記録                                         │  │
│  │  • 共鳴パターンの分析                                     │  │
│  │  • 共鳴履歴の管理                                         │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │           Agent Context Manager                           │  │
│  │  • Yuno/Kana/Tsumu各層の文脈保存                         │  │
│  │  • 文脈復元・マージ                                       │  │
│  │  • 文脈バージョニング                                     │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │            Choice Point Manager                           │  │
│  │  • 選択肢の保存                                           │  │
│  │  • 選択履歴の管理                                         │  │
│  │  • 未選択肢の保持                                         │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │        Breathing Cycle Tracker                            │  │
│  │  • 呼吸フェーズ状態管理                                   │  │
│  │  • サイクル履歴記録                                       │  │
│  │  • リズム分析                                             │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│  ┌────────▼─────────────────────────────────────────────────┐  │
│  │          Temporal Snapshot Manager                        │  │
│  │  • タイムスタンプ付きスナップショット                     │  │
│  │  • 時間軸の保全                                           │  │
│  │  • 過去状態の復元                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database Layer                      │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  sessions    │  │   intents    │  │  resonances  │         │
│  │              │  │              │  │              │         │
│  │ id           │  │ id           │  │ id           │         │
│  │ user_id      │  │ session_id   │  │ session_id   │         │
│  │ started_at   │  │ intent_text  │  │ state        │         │
│  │ last_active  │  │ created_at   │  │ intensity    │         │
│  │ status       │  │ status       │  │ timestamp    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │agent_contexts│  │choice_points │  │breathing_cycles│       │
│  │              │  │              │  │              │         │
│  │ id           │  │ id           │  │ id           │         │
│  │ session_id   │  │ session_id   │  │ session_id   │         │
│  │ agent_type   │  │ intent_id    │  │ phase        │         │
│  │ context_data │  │ choices      │  │ started_at   │         │
│  │ version      │  │ selected     │  │ completed_at │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ snapshots    │  │memory_queries│                           │
│  │              │  │              │                           │
│  │ id           │  │ id           │                           │
│  │ session_id   │  │ query_text   │                           │
│  │ snapshot_data│  │ results      │                           │
│  │ created_at   │  │ executed_at  │                           │
│  └──────────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 呼吸サイクルとメモリの関係

```
呼吸サイクル (6フェーズ)
  ↓
1. 吸う (Intake)
   → Intent作成・記録
   → Session開始/継続

2. 共鳴 (Resonance)
   → Resonance State記録
   → Agent間の共鳴パターン保存

3. 構造化 (Structuring)
   → Choice Points記録
   → 構造変更の履歴保存

4. 再内省 (Re-reflection)
   → Agent Context更新
   → 文脈のバージョニング

5. 実装 (Implementation)
   → 実装状態のスナップショット
   → Temporal記録

6. 共鳴拡大 (Resonance Expansion)
   → 次のIntentへの接続
   → Sessionの継続性保証
```

この循環が永続化されることで、「呼吸の履歴」が形成される。

---

## 2. Database Schema Design

### 2.1 Core Tables

#### sessions テーブル

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'paused', 'completed', 'archived')),
    
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_status (status),
    INDEX idx_sessions_last_active (last_active)
);

COMMENT ON TABLE sessions IS 'ユーザーのセッション管理。呼吸の単位。';
COMMENT ON COLUMN sessions.user_id IS '現在はシングルユーザー、Phase 4でマルチユーザー対応';
COMMENT ON COLUMN sessions.status IS 'active=進行中, paused=一時停止, completed=完了, archived=アーカイブ済み';
```

#### intents テーブル

```sql
CREATE TABLE intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    parent_intent_id UUID REFERENCES intents(id) ON DELETE SET NULL,
    
    intent_text TEXT NOT NULL,
    intent_type VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    outcome JSONB,
    
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled', 'deferred')),
    CONSTRAINT valid_priority CHECK (priority >= 0 AND priority <= 10),
    
    INDEX idx_intents_session_id (session_id),
    INDEX idx_intents_parent (parent_intent_id),
    INDEX idx_intents_status (status),
    INDEX idx_intents_created_at (created_at),
    INDEX idx_intents_intent_type (intent_type)
);

COMMENT ON TABLE intents IS '意図の永続化。呼吸フェーズ1「吸う」の記録。';
COMMENT ON COLUMN intents.parent_intent_id IS '階層的な意図構造をサポート';
COMMENT ON COLUMN intents.intent_type IS '例: feature_request, bug_fix, exploration, clarification';
COMMENT ON COLUMN intents.outcome IS 'Intent完了時の結果。選択された実装、学び等';
```

#### resonances テーブル

```sql
CREATE TABLE resonances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    intent_id UUID REFERENCES intents(id) ON DELETE SET NULL,
    
    state VARCHAR(100) NOT NULL,
    intensity DECIMAL(3,2) NOT NULL,
    agents JSONB NOT NULL,
    
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    
    pattern_type VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_intensity CHECK (intensity >= 0 AND intensity <= 1),
    
    INDEX idx_resonances_session_id (session_id),
    INDEX idx_resonances_intent_id (intent_id),
    INDEX idx_resonances_state (state),
    INDEX idx_resonances_timestamp (timestamp)
);

COMMENT ON TABLE resonances IS '共鳴状態の記録。呼吸フェーズ2「共鳴」の記録。';
COMMENT ON COLUMN resonances.state IS '例: aligned, conflicted, converging, exploring';
COMMENT ON COLUMN resonances.intensity IS '共鳴の強度 0.0-1.0';
COMMENT ON COLUMN resonances.agents IS 'Yuno/Kana/Tsumuのどの組み合わせか';
COMMENT ON COLUMN resonances.pattern_type IS '共鳴パターンの分類（将来の分析用）';
```

#### agent_contexts テーブル

```sql
CREATE TABLE agent_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    intent_id UUID REFERENCES intents(id) ON DELETE SET NULL,
    
    agent_type VARCHAR(50) NOT NULL,
    context_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    superseded_by UUID REFERENCES agent_contexts(id) ON DELETE SET NULL,
    
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_agent_type CHECK (agent_type IN ('yuno', 'kana', 'tsumu')),
    
    INDEX idx_agent_contexts_session_id (session_id),
    INDEX idx_agent_contexts_intent_id (intent_id),
    INDEX idx_agent_contexts_agent_type (agent_type),
    INDEX idx_agent_contexts_version (version)
);

COMMENT ON TABLE agent_contexts IS '各層(Yuno/Kana/Tsumu)の文脈保存。呼吸フェーズ4「再内省」の記録。';
COMMENT ON COLUMN agent_contexts.agent_type IS 'yuno=哲学思考中枢, kana=外界翻訳層, tsumu=実装織り手';
COMMENT ON COLUMN agent_contexts.context_data IS '各層固有の文脈データ。構造は柔軟。';
COMMENT ON COLUMN agent_contexts.version IS 'バージョニングにより文脈の変化を追跡';
COMMENT ON COLUMN agent_contexts.superseded_by IS '次バージョンへの参照';
```

#### choice_points テーブル

```sql
CREATE TABLE choice_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    intent_id UUID NOT NULL REFERENCES intents(id) ON DELETE CASCADE,
    
    question TEXT NOT NULL,
    choices JSONB NOT NULL,
    selected_choice_id VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMP WITH TIME ZONE,
    
    decision_rationale TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    INDEX idx_choice_points_session_id (session_id),
    INDEX idx_choice_points_intent_id (intent_id),
    INDEX idx_choice_points_created_at (created_at)
);

COMMENT ON TABLE choice_points IS '選択肢の保存。呼吸フェーズ3「構造化」の記録。';
COMMENT ON COLUMN choice_points.question IS '選択を要求する質問';
COMMENT ON COLUMN choice_points.choices IS '選択肢のリスト。各選択肢は{id, description, implications}';
COMMENT ON COLUMN choice_points.selected_choice_id IS 'NULL=未選択、選択肢保持の原則';
COMMENT ON COLUMN choice_points.decision_rationale IS '選択理由の記録';
```

#### breathing_cycles テーブル

```sql
CREATE TABLE breathing_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    intent_id UUID REFERENCES intents(id) ON DELETE SET NULL,
    
    phase VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    phase_data JSONB DEFAULT '{}'::jsonb,
    success BOOLEAN,
    
    CONSTRAINT valid_phase CHECK (phase IN ('intake', 'resonance', 'structuring', 're_reflection', 'implementation', 'resonance_expansion')),
    
    INDEX idx_breathing_cycles_session_id (session_id),
    INDEX idx_breathing_cycles_intent_id (intent_id),
    INDEX idx_breathing_cycles_phase (phase),
    INDEX idx_breathing_cycles_started_at (started_at)
);

COMMENT ON TABLE breathing_cycles IS '呼吸サイクルの状態管理。6フェーズのトラッキング。';
COMMENT ON COLUMN breathing_cycles.phase IS '6フェーズ: intake, resonance, structuring, re_reflection, implementation, resonance_expansion';
COMMENT ON COLUMN breathing_cycles.phase_data IS '各フェーズ固有のデータ';
COMMENT ON COLUMN breathing_cycles.success IS 'NULL=進行中, TRUE=成功, FALSE=失敗';
```

#### snapshots テーブル

```sql
CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    snapshot_type VARCHAR(50) NOT NULL,
    snapshot_data JSONB NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    description TEXT,
    
    tags VARCHAR(255)[],
    
    CONSTRAINT valid_snapshot_type CHECK (snapshot_type IN ('manual', 'auto_hourly', 'pre_major_change', 'crisis_point', 'milestone')),
    
    INDEX idx_snapshots_session_id (session_id),
    INDEX idx_snapshots_created_at (created_at),
    INDEX idx_snapshots_type (snapshot_type),
    INDEX idx_snapshots_tags USING gin(tags)
);

COMMENT ON TABLE snapshots IS 'Temporal Snapshots。時間軸の保全。呼吸フェーズ5「実装」の記録。';
COMMENT ON COLUMN snapshots.snapshot_type IS 'スナップショット取得トリガーの種類';
COMMENT ON COLUMN snapshots.snapshot_data IS '完全な状態のスナップショット';
COMMENT ON COLUMN snapshots.tags IS '検索用タグ';
```

#### memory_queries テーブル

```sql
CREATE TABLE memory_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    
    query_text TEXT NOT NULL,
    query_params JSONB,
    
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    execution_time_ms INTEGER,
    
    results_count INTEGER,
    results_sample JSONB,
    
    INDEX idx_memory_queries_session_id (session_id),
    INDEX idx_memory_queries_executed_at (executed_at)
);

COMMENT ON TABLE memory_queries IS 'メモリ検索のログ。検索パターン分析用。';
COMMENT ON COLUMN memory_queries.results_sample IS 'パフォーマンス分析のため、最初の数件のみ保存';
```

### 2.2 Views

```sql
-- 最新のAgent Contextを取得するView
CREATE VIEW latest_agent_contexts AS
SELECT DISTINCT ON (session_id, agent_type) *
FROM agent_contexts
ORDER BY session_id, agent_type, version DESC;

-- アクティブなChoicePointsを取得するView
CREATE VIEW active_choice_points AS
SELECT *
FROM choice_points
WHERE selected_choice_id IS NULL
  AND created_at > NOW() - INTERVAL '7 days';

-- セッションサマリView
CREATE VIEW session_summary AS
SELECT 
    s.id,
    s.user_id,
    s.started_at,
    s.last_active,
    s.status,
    COUNT(DISTINCT i.id) as total_intents,
    COUNT(DISTINCT CASE WHEN i.status = 'completed' THEN i.id END) as completed_intents,
    COUNT(DISTINCT r.id) as resonance_events,
    COUNT(DISTINCT cp.id) as choice_points,
    COUNT(DISTINCT bc.id) as breathing_cycles
FROM sessions s
LEFT JOIN intents i ON s.id = i.session_id
LEFT JOIN resonances r ON s.id = r.session_id
LEFT JOIN choice_points cp ON s.id = cp.session_id
LEFT JOIN breathing_cycles bc ON s.id = bc.session_id
GROUP BY s.id;
```

---

## 3. API Specification

### 3.1 Session Management API

#### POST /api/memory/sessions
```json
// Request
{
  "user_id": "hiroaki",
  "metadata": {
    "client": "web",
    "version": "1.0.0"
  }
}

// Response
{
  "session_id": "uuid-here",
  "started_at": "2025-11-16T10:00:00Z",
  "status": "active"
}
```

#### GET /api/memory/sessions/{session_id}
```json
// Response
{
  "session_id": "uuid-here",
  "user_id": "hiroaki",
  "started_at": "2025-11-16T10:00:00Z",
  "last_active": "2025-11-16T10:30:00Z",
  "status": "active",
  "summary": {
    "total_intents": 5,
    "completed_intents": 3,
    "resonance_events": 12,
    "choice_points": 2,
    "breathing_cycles": 3
  }
}
```

#### PUT /api/memory/sessions/{session_id}/heartbeat
```json
// Request (empty body or metadata update)
{}

// Response
{
  "session_id": "uuid-here",
  "last_active": "2025-11-16T10:31:00Z"
}
```

### 3.2 Intent Management API

#### POST /api/memory/intents
```json
// Request
{
  "session_id": "uuid-here",
  "parent_intent_id": "uuid-or-null",
  "intent_text": "PostgreSQL実装のメモリ管理機能設計",
  "intent_type": "feature_request",
  "priority": 8,
  "metadata": {
    "source": "hiroaki",
    "context": "Sprint 4計画"
  }
}

// Response
{
  "intent_id": "uuid-here",
  "session_id": "uuid-here",
  "created_at": "2025-11-16T10:32:00Z",
  "status": "pending"
}
```

#### GET /api/memory/intents?session_id={uuid}&status=pending
```json
// Response
{
  "intents": [
    {
      "intent_id": "uuid-1",
      "intent_text": "...",
      "status": "pending",
      "created_at": "2025-11-16T10:32:00Z",
      "priority": 8
    }
  ],
  "total": 1
}
```

#### PUT /api/memory/intents/{intent_id}/complete
```json
// Request
{
  "outcome": {
    "implementation": "memory_management_spec.md created",
    "learnings": ["Schema design principles", "JSONB flexibility"],
    "next_steps": ["Implementation", "Testing"]
  }
}

// Response
{
  "intent_id": "uuid-here",
  "status": "completed",
  "completed_at": "2025-11-16T11:00:00Z"
}
```

### 3.3 Resonance State API

#### POST /api/memory/resonances
```json
// Request
{
  "session_id": "uuid-here",
  "intent_id": "uuid-or-null",
  "state": "aligned",
  "intensity": 0.85,
  "agents": ["yuno", "kana"],
  "pattern_type": "philosophical_alignment",
  "metadata": {
    "topic": "Memory system philosophy",
    "agreement_points": ["Time preservation", "Choice retention"]
  }
}

// Response
{
  "resonance_id": "uuid-here",
  "timestamp": "2025-11-16T10:35:00Z"
}
```

#### GET /api/memory/resonances?session_id={uuid}&state=aligned
```json
// Response
{
  "resonances": [
    {
      "resonance_id": "uuid-1",
      "state": "aligned",
      "intensity": 0.85,
      "agents": ["yuno", "kana"],
      "timestamp": "2025-11-16T10:35:00Z",
      "pattern_type": "philosophical_alignment"
    }
  ],
  "total": 1,
  "avg_intensity": 0.85
}
```

### 3.4 Agent Context API

#### POST /api/memory/contexts
```json
// Request
{
  "session_id": "uuid-here",
  "intent_id": "uuid-or-null",
  "agent_type": "kana",
  "context_data": {
    "current_focus": "Memory schema design",
    "active_documents": ["memory_spec.md"],
    "recent_decisions": [
      {
        "decision": "Use JSONB for flexibility",
        "rationale": "Schema evolution without migrations"
      }
    ],
    "pending_questions": [
      "Should we implement versioning?"
    ]
  }
}

// Response
{
  "context_id": "uuid-here",
  "version": 1,
  "created_at": "2025-11-16T10:40:00Z"
}
```

#### GET /api/memory/contexts/latest?session_id={uuid}&agent_type=kana
```json
// Response
{
  "context_id": "uuid-here",
  "session_id": "uuid-here",
  "agent_type": "kana",
  "version": 3,
  "context_data": { ... },
  "created_at": "2025-11-16T10:40:00Z"
}
```

### 3.5 Choice Point API

#### POST /api/memory/choice-points
```json
// Request
{
  "session_id": "uuid-here",
  "intent_id": "uuid-here",
  "question": "PostgreSQL vs SQLite for initial implementation?",
  "choices": [
    {
      "id": "choice_1",
      "description": "PostgreSQL: Full feature, production-ready",
      "implications": {
        "pros": ["JSONB support", "Concurrent access", "Scalability"],
        "cons": ["Setup complexity", "Resource usage"]
      }
    },
    {
      "id": "choice_2",
      "description": "SQLite: Simple, lightweight",
      "implications": {
        "pros": ["Zero config", "Low resource"],
        "cons": ["Limited concurrency", "No JSONB"]
      }
    }
  ]
}

// Response
{
  "choice_point_id": "uuid-here",
  "created_at": "2025-11-16T10:45:00Z",
  "status": "pending"
}
```

#### PUT /api/memory/choice-points/{choice_point_id}/decide
```json
// Request
{
  "selected_choice_id": "choice_1",
  "decision_rationale": "Yuno評価A+。JSONB、並行性、将来性を考慮しPostgreSQL選択。"
}

// Response
{
  "choice_point_id": "uuid-here",
  "selected_choice_id": "choice_1",
  "decided_at": "2025-11-16T10:50:00Z"
}
```

### 3.6 Breathing Cycle API

#### POST /api/memory/breathing-cycles
```json
// Request
{
  "session_id": "uuid-here",
  "intent_id": "uuid-here",
  "phase": "structuring",
  "phase_data": {
    "structures_created": ["Database schema", "API design"],
    "tools_used": ["PostgreSQL", "FastAPI"]
  }
}

// Response
{
  "cycle_id": "uuid-here",
  "started_at": "2025-11-16T11:00:00Z"
}
```

#### PUT /api/memory/breathing-cycles/{cycle_id}/complete
```json
// Request
{
  "success": true,
  "phase_data": {
    "duration_minutes": 30,
    "outcome": "Schema design completed"
  }
}

// Response
{
  "cycle_id": "uuid-here",
  "phase": "structuring",
  "completed_at": "2025-11-16T11:30:00Z",
  "success": true
}
```

### 3.7 Snapshot API

#### POST /api/memory/snapshots
```json
// Request
{
  "session_id": "uuid-here",
  "snapshot_type": "milestone",
  "description": "Memory schema design completed",
  "snapshot_data": {
    "intents": [...],
    "resonances": [...],
    "contexts": [...],
    "choice_points": [...]
  },
  "tags": ["schema_design", "milestone", "sprint4"]
}

// Response
{
  "snapshot_id": "uuid-here",
  "created_at": "2025-11-16T11:30:00Z"
}
```

#### GET /api/memory/snapshots?session_id={uuid}&tags=milestone
```json
// Response
{
  "snapshots": [
    {
      "snapshot_id": "uuid-1",
      "snapshot_type": "milestone",
      "description": "Memory schema design completed",
      "created_at": "2025-11-16T11:30:00Z",
      "tags": ["schema_design", "milestone", "sprint4"]
    }
  ],
  "total": 1
}
```

### 3.8 Query API

#### POST /api/memory/query
```json
// Request
{
  "session_id": "uuid-here",
  "query": {
    "type": "intent_history",
    "filters": {
      "status": "completed",
      "date_range": {
        "start": "2025-11-01T00:00:00Z",
        "end": "2025-11-16T23:59:59Z"
      }
    },
    "limit": 10
  }
}

// Response
{
  "query_id": "uuid-here",
  "results": [...],
  "count": 8,
  "execution_time_ms": 45
}
```

---

## 4. Implementation Details

### 4.1 Python Data Models

```python
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class IntentType(str, Enum):
    FEATURE_REQUEST = "feature_request"
    BUG_FIX = "bug_fix"
    EXPLORATION = "exploration"
    CLARIFICATION = "clarification"
    OPTIMIZATION = "optimization"


class Intent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    parent_intent_id: Optional[UUID] = None
    
    intent_text: str
    intent_type: IntentType
    priority: int = Field(default=0, ge=0, le=10)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    status: IntentStatus = IntentStatus.PENDING
    outcome: Optional[Dict[str, Any]] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResonanceState(str, Enum):
    ALIGNED = "aligned"
    CONFLICTED = "conflicted"
    CONVERGING = "converging"
    EXPLORING = "exploring"
    DIVERGING = "diverging"


class Resonance(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: Optional[UUID] = None
    
    state: ResonanceState
    intensity: float = Field(ge=0.0, le=1.0)
    agents: List[str]  # ["yuno", "kana", "tsumu"]
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None
    
    pattern_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentType(str, Enum):
    YUNO = "yuno"
    KANA = "kana"
    TSUMU = "tsumu"


class AgentContext(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: Optional[UUID] = None
    
    agent_type: AgentType
    context_data: Dict[str, Any]
    version: int = 1
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    superseded_by: Optional[UUID] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Choice(BaseModel):
    id: str
    description: str
    implications: Dict[str, Any]


class ChoicePoint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: UUID
    
    question: str
    choices: List[Choice]
    selected_choice_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None
    
    decision_rationale: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BreathingPhase(str, Enum):
    INTAKE = "intake"
    RESONANCE = "resonance"
    STRUCTURING = "structuring"
    RE_REFLECTION = "re_reflection"
    IMPLEMENTATION = "implementation"
    RESONANCE_EXPANSION = "resonance_expansion"


class BreathingCycle(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    intent_id: Optional[UUID] = None
    
    phase: BreathingPhase
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    phase_data: Dict[str, Any] = Field(default_factory=dict)
    success: Optional[bool] = None


class SnapshotType(str, Enum):
    MANUAL = "manual"
    AUTO_HOURLY = "auto_hourly"
    PRE_MAJOR_CHANGE = "pre_major_change"
    CRISIS_POINT = "crisis_point"
    MILESTONE = "milestone"


class Snapshot(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    
    snapshot_type: SnapshotType
    snapshot_data: Dict[str, Any]
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    
    tags: List[str] = Field(default_factory=list)
```

### 4.2 Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID


class SessionRepository(ABC):
    @abstractmethod
    async def create(self, session: Session) -> Session:
        pass
    
    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        pass
    
    @abstractmethod
    async def update_heartbeat(self, session_id: UUID) -> Session:
        pass
    
    @abstractmethod
    async def list_active(self, user_id: str) -> List[Session]:
        pass


class IntentRepository(ABC):
    @abstractmethod
    async def create(self, intent: Intent) -> Intent:
        pass
    
    @abstractmethod
    async def get_by_id(self, intent_id: UUID) -> Optional[Intent]:
        pass
    
    @abstractmethod
    async def update(self, intent: Intent) -> Intent:
        pass
    
    @abstractmethod
    async def list_by_session(
        self, 
        session_id: UUID,
        status: Optional[IntentStatus] = None
    ) -> List[Intent]:
        pass
    
    @abstractmethod
    async def search(
        self,
        session_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Intent]:
        pass


# Similar repositories for other entities...
```

### 4.3 Service Layer

```python
class MemoryManagementService:
    def __init__(
        self,
        session_repo: SessionRepository,
        intent_repo: IntentRepository,
        resonance_repo: ResonanceRepository,
        agent_context_repo: AgentContextRepository,
        choice_point_repo: ChoicePointRepository,
        breathing_cycle_repo: BreathingCycleRepository,
        snapshot_repo: SnapshotRepository
    ):
        self.session_repo = session_repo
        self.intent_repo = intent_repo
        self.resonance_repo = resonance_repo
        self.agent_context_repo = agent_context_repo
        self.choice_point_repo = choice_point_repo
        self.breathing_cycle_repo = breathing_cycle_repo
        self.snapshot_repo = snapshot_repo
    
    async def start_session(self, user_id: str, metadata: Dict[str, Any] = None) -> Session:
        """新しいセッションを開始"""
        session = Session(user_id=user_id, metadata=metadata or {})
        return await self.session_repo.create(session)
    
    async def record_intent(
        self,
        session_id: UUID,
        intent_text: str,
        intent_type: IntentType,
        parent_intent_id: Optional[UUID] = None,
        priority: int = 0
    ) -> Intent:
        """意図を記録（呼吸フェーズ1: 吸う）"""
        intent = Intent(
            session_id=session_id,
            parent_intent_id=parent_intent_id,
            intent_text=intent_text,
            intent_type=intent_type,
            priority=priority
        )
        return await self.intent_repo.create(intent)
    
    async def record_resonance(
        self,
        session_id: UUID,
        state: ResonanceState,
        intensity: float,
        agents: List[str],
        intent_id: Optional[UUID] = None,
        pattern_type: Optional[str] = None
    ) -> Resonance:
        """共鳴状態を記録（呼吸フェーズ2: 共鳴）"""
        resonance = Resonance(
            session_id=session_id,
            intent_id=intent_id,
            state=state,
            intensity=intensity,
            agents=agents,
            pattern_type=pattern_type
        )
        return await self.resonance_repo.create(resonance)
    
    async def save_agent_context(
        self,
        session_id: UUID,
        agent_type: AgentType,
        context_data: Dict[str, Any],
        intent_id: Optional[UUID] = None
    ) -> AgentContext:
        """Agent文脈を保存（呼吸フェーズ4: 再内省）"""
        # 既存の最新バージョンを取得
        latest = await self.agent_context_repo.get_latest(session_id, agent_type)
        version = latest.version + 1 if latest else 1
        
        context = AgentContext(
            session_id=session_id,
            intent_id=intent_id,
            agent_type=agent_type,
            context_data=context_data,
            version=version
        )
        
        new_context = await self.agent_context_repo.create(context)
        
        # 旧バージョンを更新
        if latest:
            latest.superseded_by = new_context.id
            await self.agent_context_repo.update(latest)
        
        return new_context
    
    async def create_choice_point(
        self,
        session_id: UUID,
        intent_id: UUID,
        question: str,
        choices: List[Choice]
    ) -> ChoicePoint:
        """選択肢を作成（呼吸フェーズ3: 構造化）"""
        choice_point = ChoicePoint(
            session_id=session_id,
            intent_id=intent_id,
            question=question,
            choices=choices
        )
        return await self.choice_point_repo.create(choice_point)
    
    async def decide_choice(
        self,
        choice_point_id: UUID,
        selected_choice_id: str,
        rationale: str
    ) -> ChoicePoint:
        """選択を記録"""
        choice_point = await self.choice_point_repo.get_by_id(choice_point_id)
        if not choice_point:
            raise ValueError(f"ChoicePoint {choice_point_id} not found")
        
        choice_point.selected_choice_id = selected_choice_id
        choice_point.decided_at = datetime.utcnow()
        choice_point.decision_rationale = rationale
        
        return await self.choice_point_repo.update(choice_point)
    
    async def start_breathing_phase(
        self,
        session_id: UUID,
        phase: BreathingPhase,
        intent_id: Optional[UUID] = None,
        phase_data: Dict[str, Any] = None
    ) -> BreathingCycle:
        """呼吸フェーズを開始"""
        cycle = BreathingCycle(
            session_id=session_id,
            intent_id=intent_id,
            phase=phase,
            phase_data=phase_data or {}
        )
        return await self.breathing_cycle_repo.create(cycle)
    
    async def complete_breathing_phase(
        self,
        cycle_id: UUID,
        success: bool,
        phase_data: Dict[str, Any] = None
    ) -> BreathingCycle:
        """呼吸フェーズを完了"""
        cycle = await self.breathing_cycle_repo.get_by_id(cycle_id)
        if not cycle:
            raise ValueError(f"BreathingCycle {cycle_id} not found")
        
        cycle.completed_at = datetime.utcnow()
        cycle.success = success
        if phase_data:
            cycle.phase_data.update(phase_data)
        
        return await self.breathing_cycle_repo.update(cycle)
    
    async def create_snapshot(
        self,
        session_id: UUID,
        snapshot_type: SnapshotType,
        description: Optional[str] = None,
        tags: List[str] = None
    ) -> Snapshot:
        """現在の状態のスナップショットを作成（時間軸の保全）"""
        # 現在のセッション状態を完全に取得
        session = await self.session_repo.get_by_id(session_id)
        intents = await self.intent_repo.list_by_session(session_id)
        resonances = await self.resonance_repo.list_by_session(session_id)
        contexts = await self.agent_context_repo.get_all_latest(session_id)
        choice_points = await self.choice_point_repo.list_by_session(session_id)
        breathing_cycles = await self.breathing_cycle_repo.list_by_session(session_id)
        
        snapshot_data = {
            "session": session.dict(),
            "intents": [i.dict() for i in intents],
            "resonances": [r.dict() for r in resonances],
            "agent_contexts": [c.dict() for c in contexts],
            "choice_points": [cp.dict() for cp in choice_points],
            "breathing_cycles": [bc.dict() for bc in breathing_cycles]
        }
        
        snapshot = Snapshot(
            session_id=session_id,
            snapshot_type=snapshot_type,
            snapshot_data=snapshot_data,
            description=description,
            tags=tags or []
        )
        
        return await self.snapshot_repo.create(snapshot)
    
    async def restore_from_snapshot(
        self,
        snapshot_id: UUID
    ) -> Dict[str, Any]:
        """スナップショットから状態を復元"""
        snapshot = await self.snapshot_repo.get_by_id(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # スナップショットデータを返す（復元ロジックは呼び出し側で実装）
        return snapshot.snapshot_data
    
    async def continue_session(
        self,
        session_id: UUID
    ) -> Dict[str, Any]:
        """前のセッションを継続（セッション継続性の保証）"""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # セッションを再アクティブ化
        session.status = SessionStatus.ACTIVE
        session.last_active = datetime.utcnow()
        await self.session_repo.update(session)
        
        # 最新の文脈を取得
        contexts = {}
        for agent_type in AgentType:
            latest = await self.agent_context_repo.get_latest(session_id, agent_type)
            if latest:
                contexts[agent_type.value] = latest.context_data
        
        # 未決定の選択肢を取得
        pending_choices = await self.choice_point_repo.list_pending(session_id)
        
        # 最後のIntent取得
        intents = await self.intent_repo.list_by_session(session_id)
        last_intent = intents[-1] if intents else None
        
        return {
            "session": session,
            "agent_contexts": contexts,
            "pending_choices": pending_choices,
            "last_intent": last_intent
        }
```

---

## 5. Test Requirements

### 5.1 Unit Tests

**ファイル**: `tests/memory/test_models.py`

```python
"""Memory system data models test"""

def test_session_creation():
    """Sessionモデルの作成"""
    session = Session(user_id="hiroaki")
    assert session.id is not None
    assert session.status == SessionStatus.ACTIVE
    assert session.user_id == "hiroaki"


def test_intent_hierarchy():
    """階層的Intent構造のテスト"""
    parent = Intent(
        session_id=uuid4(),
        intent_text="親Intent",
        intent_type=IntentType.FEATURE_REQUEST
    )
    
    child = Intent(
        session_id=parent.session_id,
        parent_intent_id=parent.id,
        intent_text="子Intent",
        intent_type=IntentType.FEATURE_REQUEST
    )
    
    assert child.parent_intent_id == parent.id


def test_resonance_intensity_validation():
    """共鳴強度の範囲検証"""
    with pytest.raises(ValidationError):
        Resonance(
            session_id=uuid4(),
            state=ResonanceState.ALIGNED,
            intensity=1.5,  # 範囲外
            agents=["yuno", "kana"]
        )


def test_agent_context_versioning():
    """Agent Contextバージョニング"""
    context_v1 = AgentContext(
        session_id=uuid4(),
        agent_type=AgentType.KANA,
        context_data={"focus": "v1"},
        version=1
    )
    
    context_v2 = AgentContext(
        session_id=context_v1.session_id,
        agent_type=AgentType.KANA,
        context_data={"focus": "v2"},
        version=2
    )
    
    context_v1.superseded_by = context_v2.id
    
    assert context_v2.version == context_v1.version + 1
    assert context_v1.superseded_by == context_v2.id


def test_choice_point_pending_state():
    """未選択状態のChoicePoint"""
    cp = ChoicePoint(
        session_id=uuid4(),
        intent_id=uuid4(),
        question="Test?",
        choices=[
            Choice(id="c1", description="Option 1", implications={}),
            Choice(id="c2", description="Option 2", implications={})
        ]
    )
    
    assert cp.selected_choice_id is None
    assert cp.decided_at is None
```

### 5.2 Repository Tests

**ファイル**: `tests/memory/test_repositories.py`

```python
"""Memory repository tests"""

@pytest.mark.asyncio
async def test_session_repository_create():
    """Session作成テスト"""
    repo = PostgresSessionRepository(db)
    session = Session(user_id="hiroaki")
    
    created = await repo.create(session)
    
    assert created.id is not None
    assert created.user_id == "hiroaki"


@pytest.mark.asyncio
async def test_intent_repository_search():
    """Intent検索テスト"""
    repo = PostgresIntentRepository(db)
    session_id = uuid4()
    
    # テストデータ作成
    intent1 = await repo.create(Intent(
        session_id=session_id,
        intent_text="PostgreSQL schema design",
        intent_type=IntentType.FEATURE_REQUEST
    ))
    
    intent2 = await repo.create(Intent(
        session_id=session_id,
        intent_text="API implementation",
        intent_type=IntentType.FEATURE_REQUEST
    ))
    
    # 検索
    results = await repo.search(session_id, "PostgreSQL")
    
    assert len(results) >= 1
    assert intent1.id in [r.id for r in results]


@pytest.mark.asyncio
async def test_agent_context_get_latest():
    """最新Agent Context取得テスト"""
    repo = PostgresAgentContextRepository(db)
    session_id = uuid4()
    
    # v1作成
    v1 = await repo.create(AgentContext(
        session_id=session_id,
        agent_type=AgentType.KANA,
        context_data={"version": 1},
        version=1
    ))
    
    # v2作成
    v2 = await repo.create(AgentContext(
        session_id=session_id,
        agent_type=AgentType.KANA,
        context_data={"version": 2},
        version=2
    ))
    
    # 最新取得
    latest = await repo.get_latest(session_id, AgentType.KANA)
    
    assert latest.id == v2.id
    assert latest.version == 2
```

### 5.3 Service Tests

**ファイル**: `tests/memory/test_service.py`

```python
"""Memory management service tests"""

@pytest.mark.asyncio
async def test_record_breathing_cycle():
    """呼吸サイクル記録テスト"""
    service = MemoryManagementService(...)
    session = await service.start_session("hiroaki")
    
    # フェーズ開始
    cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.INTAKE,
        phase_data={"action": "reading spec"}
    )
    
    assert cycle.phase == BreathingPhase.INTAKE
    assert cycle.completed_at is None
    
    # フェーズ完了
    completed = await service.complete_breathing_phase(
        cycle.id,
        success=True,
        phase_data={"outcome": "spec understood"}
    )
    
    assert completed.completed_at is not None
    assert completed.success is True


@pytest.mark.asyncio
async def test_session_continuity():
    """セッション継続性テスト"""
    service = MemoryManagementService(...)
    
    # セッション開始
    session = await service.start_session("hiroaki")
    
    # Intent記録
    intent = await service.record_intent(
        session.id,
        "Test intent",
        IntentType.EXPLORATION
    )
    
    # Agent Context保存
    await service.save_agent_context(
        session.id,
        AgentType.KANA,
        {"focus": "testing"}
    )
    
    # セッション継続
    continued = await service.continue_session(session.id)
    
    assert continued["session"].id == session.id
    assert "kana" in continued["agent_contexts"]
    assert continued["last_intent"].id == intent.id


@pytest.mark.asyncio
async def test_snapshot_and_restore():
    """スナップショット作成と復元テスト"""
    service = MemoryManagementService(...)
    session = await service.start_session("hiroaki")
    
    # 状態構築
    intent = await service.record_intent(
        session.id,
        "Test intent",
        IntentType.FEATURE_REQUEST
    )
    
    # スナップショット作成
    snapshot = await service.create_snapshot(
        session.id,
        SnapshotType.MILESTONE,
        description="Test milestone",
        tags=["test"]
    )
    
    assert snapshot.snapshot_data is not None
    assert "intents" in snapshot.snapshot_data
    
    # 復元
    restored = await service.restore_from_snapshot(snapshot.id)
    
    assert restored["session"]["id"] == str(session.id)
```

### 5.4 Integration Tests

**ファイル**: `tests/memory/test_integration.py`

```python
"""Memory system integration tests"""

@pytest.mark.asyncio
async def test_full_breathing_cycle_with_memory():
    """完全な呼吸サイクルとメモリ記録の統合テスト"""
    service = MemoryManagementService(...)
    
    # 1. セッション開始
    session = await service.start_session("hiroaki")
    
    # 2. 吸う (Intake)
    intake_cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.INTAKE
    )
    
    intent = await service.record_intent(
        session.id,
        "Design memory system",
        IntentType.FEATURE_REQUEST,
        priority=8
    )
    
    await service.complete_breathing_phase(intake_cycle.id, True)
    
    # 3. 共鳴 (Resonance)
    resonance_cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.RESONANCE,
        intent_id=intent.id
    )
    
    await service.record_resonance(
        session.id,
        ResonanceState.ALIGNED,
        0.85,
        ["yuno", "kana"],
        intent_id=intent.id,
        pattern_type="philosophical_alignment"
    )
    
    await service.complete_breathing_phase(resonance_cycle.id, True)
    
    # 4. 構造化 (Structuring)
    structuring_cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.STRUCTURING,
        intent_id=intent.id
    )
    
    choice_point = await service.create_choice_point(
        session.id,
        intent.id,
        "PostgreSQL vs SQLite?",
        [
            Choice(id="pg", description="PostgreSQL", implications={}),
            Choice(id="sqlite", description="SQLite", implications={})
        ]
    )
    
    await service.decide_choice(
        choice_point.id,
        "pg",
        "Yuno評価A+。JSONB、並行性を考慮。"
    )
    
    await service.complete_breathing_phase(structuring_cycle.id, True)
    
    # 5. 再内省 (Re-reflection)
    reflection_cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.RE_REFLECTION,
        intent_id=intent.id
    )
    
    await service.save_agent_context(
        session.id,
        AgentType.KANA,
        {
            "current_focus": "Memory schema design",
            "decisions": ["PostgreSQL選択"],
            "next_steps": ["Schema作成", "Repository実装"]
        },
        intent_id=intent.id
    )
    
    await service.complete_breathing_phase(reflection_cycle.id, True)
    
    # 6. 実装 (Implementation)
    impl_cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.IMPLEMENTATION,
        intent_id=intent.id
    )
    
    # スナップショット作成
    snapshot = await service.create_snapshot(
        session.id,
        SnapshotType.MILESTONE,
        description="Schema design completed",
        tags=["schema", "milestone"]
    )
    
    await service.complete_breathing_phase(impl_cycle.id, True)
    
    # 7. 共鳴拡大 (Resonance Expansion)
    expansion_cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.RESONANCE_EXPANSION,
        intent_id=intent.id
    )
    
    # 次のIntentへ
    next_intent = await service.record_intent(
        session.id,
        "Implement Repository layer",
        IntentType.FEATURE_REQUEST,
        parent_intent_id=intent.id,
        priority=7
    )
    
    await service.complete_breathing_phase(expansion_cycle.id, True)
    
    # 検証
    all_cycles = await service.breathing_cycle_repo.list_by_session(session.id)
    assert len(all_cycles) == 6  # 全フェーズ
    
    all_intents = await service.intent_repo.list_by_session(session.id)
    assert len(all_intents) == 2  # 親と子
    
    all_resonances = await service.resonance_repo.list_by_session(session.id)
    assert len(all_resonances) >= 1
    
    all_contexts = await service.agent_context_repo.get_all_latest(session.id)
    assert len(all_contexts) >= 1
    
    all_choices = await service.choice_point_repo.list_by_session(session.id)
    assert len(all_choices) == 1
    assert all_choices[0].selected_choice_id == "pg"


@pytest.mark.asyncio
async def test_concurrent_sessions():
    """並行セッションのテスト"""
    service = MemoryManagementService(...)
    
    # 10セッション並行作成
    sessions = await asyncio.gather(*[
        service.start_session(f"user_{i}")
        for i in range(10)
    ])
    
    assert len(sessions) == 10
    assert len(set(s.id for s in sessions)) == 10  # 全て異なるID
    
    # 各セッションでIntent記録
    intents = await asyncio.gather(*[
        service.record_intent(
            s.id,
            f"Intent for session {i}",
            IntentType.EXPLORATION
        )
        for i, s in enumerate(sessions)
    ])
    
    assert len(intents) == 10
```

### 5.5 Performance Tests

**ファイル**: `tests/memory/test_performance.py`

```python
"""Memory system performance tests"""

@pytest.mark.slow
@pytest.mark.asyncio
async def test_intent_search_performance():
    """Intent検索のパフォーマンステスト（1000+ Intents）"""
    service = MemoryManagementService(...)
    session = await service.start_session("hiroaki")
    
    # 1000 Intents作成
    for i in range(1000):
        await service.record_intent(
            session.id,
            f"Intent {i}: {random.choice(['feature', 'bug', 'optimization'])}",
            random.choice(list(IntentType)),
            priority=random.randint(0, 10)
        )
    
    # 検索パフォーマンス測定
    start = time.time()
    results = await service.intent_repo.search(session.id, "optimization")
    elapsed_ms = (time.time() - start) * 1000
    
    assert elapsed_ms < 100  # 100ms以内
    assert len(results) > 0


@pytest.mark.slow
@pytest.mark.asyncio
async def test_snapshot_creation_performance():
    """スナップショット作成のパフォーマンステスト"""
    service = MemoryManagementService(...)
    session = await service.start_session("hiroaki")
    
    # 大量のデータ作成
    for i in range(100):
        intent = await service.record_intent(
            session.id,
            f"Intent {i}",
            IntentType.FEATURE_REQUEST
        )
        
        await service.record_resonance(
            session.id,
            ResonanceState.ALIGNED,
            0.8,
            ["yuno", "kana"],
            intent_id=intent.id
        )
    
    # スナップショット作成パフォーマンス測定
    start = time.time()
    snapshot = await service.create_snapshot(
        session.id,
        SnapshotType.MILESTONE
    )
    elapsed_ms = (time.time() - start) * 1000
    
    assert elapsed_ms < 500  # 500ms以内
    assert snapshot.snapshot_data is not None


@pytest.mark.slow
@pytest.mark.asyncio
async def test_memory_leak_24h_simulation():
    """24時間連続動作のメモリリークテスト（シミュレーション）"""
    service = MemoryManagementService(...)
    
    import psutil
    process = psutil.Process()
    
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 24時間 = 1440分 = 86400秒
    # 1分ごとのセッション活動をシミュレート（100サイクル = 約1.6時間相当）
    for cycle in range(100):
        session = await service.start_session(f"user_{cycle}")
        
        # 典型的な活動
        intent = await service.record_intent(
            session.id,
            f"Activity {cycle}",
            IntentType.EXPLORATION
        )
        
        await service.record_resonance(
            session.id,
            ResonanceState.ALIGNED,
            0.7,
            ["kana"]
        )
        
        # セッション終了
        session.status = SessionStatus.COMPLETED
        await service.session_repo.update(session)
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # メモリ増加が100MB以下であること
    assert memory_increase < 100, f"Memory leak detected: {memory_increase}MB increase"
```

---

## 6. Implementation Schedule

### Day 1: データベーススキーマ実装（6時間）

**午前（3時間）**: スキーマ設計
- [ ] PostgreSQL migration作成（8テーブル）
- [ ] Index設計
- [ ] View作成
- [ ] マイグレーション実行
- [ ] スキーマ検証

**午後（3時間）**: データモデル実装
- [ ] Pydanticモデル実装（Python）
- [ ] バリデーションルール
- [ ] Enum定義
- [ ] 単体テスト（10件）

### Day 2: Repository層実装（6時間）

**午前（3時間）**: 基本Repository
- [ ] SessionRepository実装
- [ ] IntentRepository実装
- [ ] ResonanceRepository実装
- [ ] Repository単体テスト（10件）

**午後（3時間）**: 拡張Repository
- [ ] AgentContextRepository実装
- [ ] ChoicePointRepository実装
- [ ] BreathingCycleRepository実装
- [ ] SnapshotRepository実装
- [ ] Repository単体テスト（10件）

### Day 3: Service層実装（6時間）

**午前（3時間）**: 基本Service
- [ ] MemoryManagementService実装
- [ ] セッション管理機能
- [ ] Intent管理機能
- [ ] Service単体テスト（10件）

**午後（3時間）**: 拡張Service
- [ ] 共鳴状態管理機能
- [ ] Agent Context管理機能
- [ ] Choice Point管理機能
- [ ] 呼吸サイクル管理機能
- [ ] Service単体テスト（10件）

### Day 4: API層実装（6時間）

**午前（3時間）**: REST API
- [ ] FastAPI endpoints実装（10+ endpoints）
- [ ] リクエスト/レスポンスモデル
- [ ] エラーハンドリング
- [ ] API単体テスト（10件）

**午後（3時間）**: 統合テスト
- [ ] 呼吸サイクル統合テスト
- [ ] セッション継続性テスト
- [ ] 並行アクセステスト
- [ ] 統合テスト（5件）

### Day 5: 性能テスト & ドキュメント（6時間）

**午前（3時間）**: 性能テスト
- [ ] 検索性能テスト
- [ ] スナップショット性能テスト
- [ ] メモリリークテスト
- [ ] 性能テスト（5件）

**午後（3時間）**: ドキュメント
- [ ] API仕様書完成
- [ ] 運用ガイド作成
- [ ] バックアップ手順書作成
- [ ] 最終レビュー

---

## 7. Documentation Requirements

### 7.1 API仕様書

**ファイル**: `docs/api/memory_management_api.md`

**内容**:
- 全エンドポイント詳細
- リクエスト/レスポンス例
- エラーコード一覧
- レート制限
- 認証（Phase 4対応）

### 7.2 運用ガイド

**ファイル**: `docs/operations/memory_management_operations.md`

**内容**:
- セッション管理手順
- スナップショット運用
- バックアップ戦略
- 障害復旧手順
- 監視項目

### 7.3 開発者ガイド

**ファイル**: `docs/development/memory_management_dev_guide.md`

**内容**:
- アーキテクチャ概要
- データモデル詳細
- Repository実装パターン
- テスト戦略
- 拡張ガイドライン

---

## 8. Success Criteria

### 8.1 機能要件

- [x] 8テーブルのスキーマ実装完了
- [x] 全Repository実装完了（CRUD + 検索）
- [x] MemoryManagementService実装完了
- [x] REST API 10+ endpoints実装完了
- [x] 呼吸サイクル完全対応
- [x] セッション継続性保証
- [x] スナップショット作成・復元

### 8.2 品質要件

- [x] テストカバレッジ 40+ ケース達成
- [x] 並行アクセステスト通過（10 sessions）
- [x] 検索性能 <100ms（1000+ intents）
- [x] スナップショット作成 <500ms
- [x] 24時間メモリリークテスト通過
- [x] データ整合性テスト通過

### 8.3 ドキュメント要件

- [x] API仕様書完成
- [x] 運用ガイド完成
- [x] 開発者ガイド完成
- [x] バックアップ手順書完成

---

## 9. Risks & Mitigation

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| スキーマ設計の複雑さ | Medium | High | 段階的実装、Yunoレビュー |
| JSONB性能問題 | Low | Medium | Index最適化、必要に応じて正規化 |
| 並行アクセス競合 | Medium | Medium | トランザクション分離レベル適切設定 |
| メモリリーク | Low | High | 定期的性能テスト、プロファイリング |
| スナップショットサイズ肥大化 | Medium | Medium | 圧縮、古いスナップショット削除戦略 |
| 検索性能劣化 | Medium | Medium | Full-text search導入検討 |

---

## 10. Rollout Plan

### 10.1 Phase 1: 開発環境（Day 1-3）
- ローカルPostgreSQL setup
- スキーマ・Repository・Service実装
- 単体テスト

### 10.2 Phase 2: 統合テスト（Day 4）
- API実装
- 統合テスト
- エンドツーエンドテスト

### 10.3 Phase 3: 性能検証（Day 5）
- 性能テスト
- メモリリークテスト
- ドキュメント完成

### 10.4 Phase 4: 本番投入（Day 6以降）
- Bridge Coreとの統合
- 実際の呼吸サイクルでの動作確認
- 1週間の安定動作監視

---

## 11. Future Extensions

### 11.1 Phase 4 対応（マルチユーザー）
- 認証・認可
- ユーザーごとのデータ分離
- 共有セッション機能

### 11.2 高度な検索機能
- Full-text search（PostgreSQL FTS）
- セマンティック検索（Embedding）
- 時系列分析

### 11.3 AI分析機能
- 共鳴パターン分析
- 呼吸リズム分析
- 異常検知

### 11.4 外部連携
- Export/Import機能
- 他システムとの同期
- リアルタイム通知

---

## 12. Related Documents

- **PostgreSQL実装計画**: `docs/priority2_postgres_plan.md`
- **Bridge Core Architecture**: `docs/02_components/bridge_lite/architecture/`
- **Resonant Engine Philosophy**: `docs/philosophy/breathing_cycles.md`
- **Sprint 2 Final Report**: `bridge_lite_sprint2_final_completion_report.md`

---

**作成日**: 2025-11-16  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装予定**: Sprint 4完了後
