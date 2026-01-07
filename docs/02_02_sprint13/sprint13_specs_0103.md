# Sprint 13: フロントエンドUI統合設計仕様書

**作成日**: 2026-01-03
**Sprint**: 13
**対象**: バックエンド機能のフロントエンドUI統合
**前提**: Sprint 12 Term Drift/Temporal Constraint完了、Phase 3 FileModificationService完了

---

## 1. エグゼクティブサマリー

### 1.1 現状分析

| カテゴリ | バックエンド | フロントエンド | ギャップ |
|---------|-------------|---------------|---------|
| 基本CRUD | 100% | 100% | なし |
| Contradiction Detection | 100% | 60% | 解決UI未実装 |
| Dashboard Analytics | 100% | 10% | UIページ未作成 |
| Choice Preservation | 100% | 10% | UIページ未作成 |
| Term Drift Detection | 100% | 0% | 完全未対応 |
| Temporal Constraint | 100% | 0% | 完全未対応 |
| File Modification | 100% | 0% | 完全未対応 |
| Memory Lifecycle | 100% | 10% | UIページ未作成 |

**総合フロントエンド実装率**: 35%

### 1.2 Sprint 13 目標

フロントエンドUI実装率を **35% → 85%** に引き上げる。

---

## 2. 優先度と実装フェーズ

### Phase 13-A: 既存API統合済み機能のUI完成（優先度: 高）

1. **Contradiction Resolve UI** - 矛盾解決機能
2. **Dashboard Analytics Page** - システム概要ダッシュボード
3. **Choice Points Page** - 選択肢管理ページ
4. **Memory Lifecycle Page** - メモリ管理ページ

### Phase 13-B: 新規API統合 + UI実装（優先度: 中）

5. **Term Drift Detection UI** - 用語ドリフト検出ページ
6. **Temporal Constraint UI** - 時間的制約ページ
7. **File Modification UI** - ファイル操作ページ

---

## 3. 詳細設計

### 3.1 Contradiction Resolve UI

#### 3.1.1 概要
既存の`ContradictionItem.tsx`に解決機能を追加。

#### 3.1.2 コンポーネント構成

```
components/contradiction/
├── ContradictionDashboard.tsx  # 既存（変更なし）
├── ContradictionItem.tsx       # 既存（解決ボタン追加）
├── ContradictionResolveModal.tsx  # 新規
└── ContradictionDetail.tsx     # 新規
```

#### 3.1.3 新規コンポーネント: ContradictionResolveModal

**Props**:
```typescript
interface ContradictionResolveModalProps {
  contradiction: Contradiction;
  isOpen: boolean;
  onClose: () => void;
  onResolve: (data: ResolveContradictionRequest) => Promise<void>;
}
```

**機能**:
- 解決アクション選択（policy_change / mistake / coexist）
- 解決根拠入力（10文字以上必須）
- キャンセル/確定ボタン

**UI設計**:
```
┌─────────────────────────────────────────────┐
│  矛盾の解決                              ✕  │
├─────────────────────────────────────────────┤
│  矛盾タイプ: tech_stack                      │
│  信頼度: 85%                                │
│                                             │
│  新規Intent:                                │
│  ┌─────────────────────────────────────┐   │
│  │ PostgreSQLをメインDBとして使用      │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  競合Intent:                                │
│  ┌─────────────────────────────────────┐   │
│  │ SQLiteを軽量DBとして使用            │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  解決アクション:                            │
│  ○ policy_change - 方針変更として承認      │
│  ○ mistake - 誤りとして棄却               │
│  ○ coexist - 共存可能として承認           │
│                                             │
│  解決根拠:                                  │
│  ┌─────────────────────────────────────┐   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│         [キャンセル]  [解決を確定]          │
└─────────────────────────────────────────────┘
```

#### 3.1.4 API統合

既存の`contradictionsApi.resolve()`を使用:
```typescript
// api/client.ts（既存）
contradictionsApi.resolve(contradictionId, {
  resolution_action: 'policy_change' | 'mistake' | 'coexist',
  resolution_rationale: string,
  resolved_by: string
})
```

---

### 3.2 Dashboard Analytics Page

#### 3.2.1 概要
システム全体の状態を可視化するダッシュボードページ。

#### 3.2.2 ファイル構成

```
pages/
└── DashboardPage.tsx           # 新規

components/dashboard/
├── SystemOverview.tsx          # 新規
├── TimelineChart.tsx           # 新規
├── CorrectionsTable.tsx        # 新規
└── HealthIndicator.tsx         # 新規
```

#### 3.2.3 SystemOverview コンポーネント

**表示項目**:
- total_users: 総ユーザー数
- active_sessions: アクティブセッション数
- total_intents / completed_intents: Intent完了率
- pending_contradictions: 未解決矛盾数
- system_health: システム健全性（healthy/warning/error）
- memory_usage_mb / cpu_usage_percent: リソース使用状況

**UI設計**:
```
┌─────────────────────────────────────────────────────────────┐
│  System Overview                              Last: 10:00   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Users    │ │ Sessions │ │ Intents  │ │ Pending  │       │
│  │   12     │ │    5     │ │  85%     │ │    3     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                             │
│  System Health: ● healthy                                   │
│  Memory: ████████░░ 80%   CPU: ████░░░░░░ 40%              │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2.4 TimelineChart コンポーネント

**機能**:
- 時間粒度セレクター（minute / hour / day）
- イベントタイムライン表示
- イベントタイプ別フィルター

**API統合**:
```typescript
dashboardApi.getTimeline(granularity: 'minute' | 'hour' | 'day')
```

#### 3.2.5 CorrectionsTable コンポーネント

**表示項目**:
- correction_type: 修正タイプ
- original_value / corrected_value: 変更前後
- corrected_by: 修正者
- correction_reason: 修正理由
- corrected_at: 修正日時

---

### 3.3 Choice Points Page

#### 3.3.1 概要
Resonant Engine の選択肢保存・決定機能のUI。

#### 3.3.2 ファイル構成

```
pages/
└── ChoicePointsPage.tsx        # 新規

components/choice-points/
├── ChoicePointList.tsx         # 新規
├── ChoicePointItem.tsx         # 新規
├── ChoicePointDecideModal.tsx  # 新規
└── ChoicePointCreateForm.tsx   # 新規
```

#### 3.3.3 ChoicePointItem コンポーネント

**表示項目**:
```typescript
interface ChoicePoint {
  id: string;
  question: string;
  choices: { choice_id: string; choice_text: string }[];
  tags: string[];
  context_type: string;
  status: 'pending' | 'decided' | 'expired';
  selected_choice_id: string | null;
  decision_rationale: string | null;
  rejection_reasons: Record<string, string>;
}
```

**UI設計**:
```
┌─────────────────────────────────────────────────────────────┐
│  ● pending                                    #design #db   │
├─────────────────────────────────────────────────────────────┤
│  どのデータベースを使用するか？                             │
│                                                             │
│  選択肢:                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ○ PostgreSQL - 信頼性の高いリレーショナルDB        │   │
│  │ ○ SQLite - 軽量でシンプル                          │   │
│  │ ○ MongoDB - ドキュメント指向                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [決定する]                                                 │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.4 ChoicePointDecideModal コンポーネント

**Props**:
```typescript
interface ChoicePointDecideModalProps {
  choicePoint: ChoicePoint;
  isOpen: boolean;
  onClose: () => void;
  onDecide: (data: DecideChoiceRequest) => Promise<void>;
}
```

**フォーム項目**:
- selected_choice_id: ラジオボタンで選択
- decision_rationale: 選択理由（10文字以上）
- rejection_reasons: 非選択の理由（オプション）

---

### 3.4 Memory Lifecycle Page

#### 3.4.1 概要
メモリ使用状況の監視と管理機能。

#### 3.4.2 ファイル構成

```
pages/
└── MemoryPage.tsx              # 新規

components/memory/
├── MemoryStatusCard.tsx        # 新規
├── MemoryUsageChart.tsx        # 新規
├── CompressionButton.tsx       # 新規
└── CleanupButton.tsx           # 新規
```

#### 3.4.3 MemoryStatusCard コンポーネント

**表示項目**:
```typescript
interface MemoryStatus {
  total_memories: number;
  active_memories: number;
  compressed_memories: number;
  expired_memories: number;
  memory_usage_mb: number;
  capacity_limit_mb: number;
  usage_percentage: number;
  last_cleanup_at: string | null;
  next_cleanup_at: string | null;
}
```

**UI設計**:
```
┌─────────────────────────────────────────────────────────────┐
│  Memory Status                          Usage: 75%          │
├─────────────────────────────────────────────────────────────┤
│  ████████████████████████░░░░░░░░ 150MB / 200MB            │
│                                                             │
│  Active: 1,200    Compressed: 300    Expired: 50           │
│                                                             │
│  Last Cleanup: 2026-01-02 15:00                            │
│  Next Cleanup: 2026-01-03 15:00                            │
│                                                             │
│  [圧縮を実行]  [期限切れを削除]                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.5 Term Drift Detection UI

#### 3.5.1 概要
用語定義のドリフト（意味の変化）を検出・管理するUI。

#### 3.5.2 ファイル構成

```
types/
└── termDrift.ts                # 新規

api/
└── termDrift.ts                # 新規

pages/
└── TermDriftPage.tsx           # 新規

components/term-drift/
├── TermDriftList.tsx           # 新規
├── TermDriftItem.tsx           # 新規
├── TermDriftResolveModal.tsx   # 新規
└── TermAnalyzeForm.tsx         # 新規
```

#### 3.5.3 型定義（types/termDrift.ts）

```typescript
export type TermCategory = 'domain_object' | 'technical' | 'process' | 'custom';
export type DriftType = 'expansion' | 'contraction' | 'semantic_shift' | 'context_change';
export type DriftStatus = 'pending' | 'acknowledged' | 'resolved' | 'dismissed';

export interface TermDefinition {
  id: string;
  user_id: string;
  term_name: string;
  term_category: TermCategory;
  definition_text: string;
  definition_context: string | null;
  definition_source: string | null;
  structured_definition: Record<string, unknown> | null;
  version: number;
  is_current: boolean;
  defined_at: string;
}

export interface TermDrift {
  id: string;
  user_id: string;
  term_name: string;
  original_definition_id: string | null;
  new_definition_id: string | null;
  drift_type: DriftType;
  confidence_score: number;
  change_summary: string;
  impact_analysis: Record<string, unknown> | null;
  status: DriftStatus;
  detected_at: string;
}

export interface TermDriftResolution {
  resolution_action: 'intentional_change' | 'rollback' | 'migration_needed';
  resolution_note: string;  // min 10 chars
  resolved_by: string;
}

export interface AnalyzeRequest {
  user_id: string;
  text: string;
  source: string;
}

export interface AnalyzeResult {
  analyzed_terms: number;
  drifts_detected: number;
  results: {
    term_name: string;
    definition_id: string;
    drift_detected: boolean;
  }[];
}
```

#### 3.5.4 API統合（api/termDrift.ts）

```typescript
import api from './client';
import type { TermDrift, TermDriftResolution, AnalyzeRequest, AnalyzeResult } from '../types/termDrift';

export const termDriftApi = {
  getPending: (userId: string, limit: number = 50) =>
    api.get<TermDrift[]>('/v1/term-drift/pending', { params: { user_id: userId, limit } }),

  analyze: (data: AnalyzeRequest) =>
    api.post<AnalyzeResult>('/v1/term-drift/analyze', data),

  resolve: (driftId: string, data: TermDriftResolution) =>
    api.put<{ status: string; drift_id: string }>(`/v1/term-drift/${driftId}/resolve`, data),
};
```

#### 3.5.5 TermDriftItem コンポーネント

**UI設計**:
```
┌─────────────────────────────────────────────────────────────┐
│  Intent                           ● semantic_shift          │
│  Confidence: 78%                                            │
├─────────────────────────────────────────────────────────────┤
│  変更サマリー:                                              │
│  「Intent」の定義が拡張されました。                         │
│  以前: ユーザーの意図を表すオブジェクト                     │
│  現在: ユーザーの意図と目標を表す構造化オブジェクト         │
│                                                             │
│  影響分析:                                                  │
│  - 3つのIntentインスタンスに影響                           │
│  - マイグレーションが必要な可能性あり                       │
│                                                             │
│  [詳細を見る]  [解決する]                                   │
└─────────────────────────────────────────────────────────────┘
```

#### 3.5.6 TermAnalyzeForm コンポーネント

テキストを入力して用語抽出・ドリフトチェックを行うフォーム。

**機能**:
- テキスト入力エリア
- ソース選択（document, chat, specification等）
- 分析実行ボタン
- 結果表示（検出された用語一覧、ドリフト警告）

---

### 3.6 Temporal Constraint UI

#### 3.6.1 概要
ファイルの時間的制約（安定性レベル）を管理するUI。

#### 3.6.2 ファイル構成

```
types/
└── temporalConstraint.ts       # 新規

api/
└── temporalConstraint.ts       # 新規

pages/
└── TemporalConstraintPage.tsx  # 新規

components/temporal-constraint/
├── ConstraintList.tsx          # 新規
├── ConstraintItem.tsx          # 新規
├── ConstraintCheckForm.tsx     # 新規
└── VerificationRegisterForm.tsx # 新規
```

#### 3.6.3 型定義（types/temporalConstraint.ts）

```typescript
export type ConstraintLevel = 'critical' | 'high' | 'medium' | 'low';
export type CheckResult = 'approved' | 'rejected' | 'pending';

export interface FileVerification {
  id: string;
  user_id: string;
  file_path: string;
  file_hash: string | null;
  verification_type: string;
  verification_description: string | null;
  test_hours_invested: number;
  constraint_level: ConstraintLevel;
  verified_at: string;
  stable_since: string | null;
  verified_by: string | null;
}

export interface TemporalConstraintCheck {
  file_path: string;
  constraint_level: ConstraintLevel;
  check_result: CheckResult;
  verification_info: FileVerification | null;
  warning_message: string | null;
  required_actions: string[];
  questions: string[];
}

export interface ModificationRequest {
  user_id: string;
  file_path: string;
  modification_type: 'edit' | 'delete' | 'rename';
  modification_reason: string;
  requested_by: 'user' | 'ai_agent' | 'system';
}

export interface VerificationRegisterResult {
  status: string;
  verification_id: string;
  file_path: string;
  constraint_level: string;
}
```

#### 3.6.4 API統合（api/temporalConstraint.ts）

```typescript
import api from './client';
import type {
  TemporalConstraintCheck,
  ModificationRequest,
  ConstraintLevel,
  VerificationRegisterResult
} from '../types/temporalConstraint';

export const temporalConstraintApi = {
  check: (data: ModificationRequest) =>
    api.post<TemporalConstraintCheck>('/v1/temporal-constraint/check', data),

  verify: (params: {
    user_id: string;
    file_path: string;
    verification_type: string;
    test_hours?: number;
    constraint_level?: ConstraintLevel;
    description?: string;
    verified_by?: string;
  }) =>
    api.post<VerificationRegisterResult>('/v1/temporal-constraint/verify', null, { params }),

  markStable: (params: { user_id: string; file_path: string }) =>
    api.post<{ status: string; file_path: string }>('/v1/temporal-constraint/mark-stable', null, { params }),

  upgradeCritical: (params: { user_id: string; file_path: string; reason: string }) =>
    api.post<{ status: string; file_path: string }>('/v1/temporal-constraint/upgrade-critical', null, { params }),
};
```

#### 3.6.5 ConstraintCheckForm コンポーネント

**機能**:
- ファイルパス入力
- 変更タイプ選択（edit / delete / rename）
- 変更理由入力
- チェック実行ボタン
- 結果表示（approved/rejected/pending）

**UI設計**:
```
┌─────────────────────────────────────────────────────────────┐
│  Temporal Constraint Check                                  │
├─────────────────────────────────────────────────────────────┤
│  ファイルパス:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ /app/services/memory/service.py                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  変更タイプ:  ○ edit  ○ delete  ○ rename                   │
│                                                             │
│  変更理由:                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ バグ修正のため                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [チェック実行]                                             │
│                                                             │
│  結果: ✅ approved (MEDIUM)                                 │
│  警告: 変更は許可されますが、テスト実行を推奨します         │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.7 File Modification UI

#### 3.7.1 概要
セキュアなファイル操作（書き込み・削除・リネーム）のUI。

#### 3.7.2 ファイル構成

```
types/
└── fileModification.ts         # 新規

api/
└── fileModification.ts         # 新規

pages/
└── FileModificationPage.tsx    # 新規

components/file-modification/
├── FileOperationForm.tsx       # 新規
├── FileOperationResult.tsx     # 新規
├── OperationLogTable.tsx       # 新規
└── ConstraintLevelBadge.tsx    # 新規
```

#### 3.7.3 型定義（types/fileModification.ts）

```typescript
export type ConstraintLevel = 'critical' | 'high' | 'medium' | 'low';
export type CheckResult = 'approved' | 'rejected' | 'pending' | 'blocked';
export type Operation = 'write' | 'delete' | 'rename';

export interface FileModificationRequest {
  user_id: string;
  file_path: string;
  operation: Operation;
  content?: string;      // write時のみ
  new_path?: string;     // rename時のみ
  reason: string;
  requested_by: string;
  force?: boolean;
}

export interface FileModificationResult {
  success: boolean;
  operation: string;
  file_path: string;
  message: string;
  constraint_level: ConstraintLevel;
  check_result: CheckResult;
  backup_path: string | null;
  file_hash: string | null;
  timestamp: string;
}

export interface FileReadRequest {
  user_id: string;
  file_path: string;
  requested_by: string;
}

export interface FileReadResult {
  success: boolean;
  file_path: string;
  content: string | null;
  file_hash: string | null;
  message: string;
}

export interface ConstraintCheckResult {
  file_path: string;
  constraint_level: string;
  check_result: string;
  can_proceed: boolean;
  warning_message: string | null;
  required_actions: string[];
  questions: string[];
  min_reason_length: number;
  current_reason_length: number;
}

export interface OperationLog {
  id: string;
  user_id: string;
  file_path: string;
  operation: string;
  reason: string;
  requested_by: string;
  constraint_level: string;
  result: string;
  backup_path: string | null;
  created_at: string;
}

export interface OperationLogsResult {
  total: number;
  logs: OperationLog[];
}
```

#### 3.7.4 API統合（api/fileModification.ts）

```typescript
import api from './client';
import type {
  FileModificationRequest,
  FileModificationResult,
  FileReadResult,
  ConstraintCheckResult,
  OperationLogsResult
} from '../types/fileModification';

export const fileModificationApi = {
  write: (data: FileModificationRequest) =>
    api.post<FileModificationResult>('/v1/files/write', data),

  delete: (data: FileModificationRequest) =>
    api.post<FileModificationResult>('/v1/files/delete', data),

  rename: (data: FileModificationRequest) =>
    api.post<FileModificationResult>('/v1/files/rename', data),

  read: (params: { user_id: string; file_path: string; requested_by?: string }) =>
    api.get<FileReadResult>('/v1/files/read', { params }),

  check: (data: FileModificationRequest) =>
    api.post<ConstraintCheckResult>('/v1/files/check', data),

  getLogs: (params: {
    user_id: string;
    limit?: number;
    offset?: number;
    operation?: string;
    result?: string;
  }) =>
    api.get<OperationLogsResult>('/v1/files/logs', { params }),
};
```

#### 3.7.5 FileOperationForm コンポーネント

**UI設計**:
```
┌─────────────────────────────────────────────────────────────┐
│  File Operation                                             │
├─────────────────────────────────────────────────────────────┤
│  操作:  ○ write  ○ delete  ○ rename  ○ read                │
│                                                             │
│  ファイルパス:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ /app/config/settings.py                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [write選択時]                                              │
│  コンテンツ:                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ # Settings...                                       │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  操作理由:                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 設定値の更新                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ※ MEDIUM: 20文字以上、HIGH: 50文字以上が必要               │
│                                                             │
│  [制約チェック]  [実行]                                     │
└─────────────────────────────────────────────────────────────┘
```

#### 3.7.6 OperationLogTable コンポーネント

**表示項目**:
- timestamp: 操作日時
- operation: 操作タイプ
- file_path: ファイルパス
- result: 結果（approved/rejected/blocked）
- constraint_level: 制約レベル
- reason: 操作理由

**フィルター機能**:
- operation別
- result別
- 日付範囲

---

## 4. ナビゲーション更新

### 4.1 Sidebar.tsx 更新

```typescript
const navItems = [
  { path: '/messages', label: 'Messages', icon: MessageSquare },
  { path: '/specifications', label: 'Specifications', icon: FileText },
  { path: '/intents', label: 'Intents', icon: Target },
  { path: '/contradictions', label: '矛盾検出', icon: AlertTriangle },
  // 🆕 追加項目
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/choice-points', label: 'Choice Points', icon: GitBranch },
  { path: '/memory', label: 'Memory', icon: Database },
  { path: '/term-drift', label: 'Term Drift', icon: Shuffle },
  { path: '/temporal-constraint', label: 'Constraints', icon: Clock },
  { path: '/files', label: 'Files', icon: Folder },
];
```

### 4.2 App.tsx ルーティング更新

```typescript
<Routes>
  <Route path="/" element={<Navigate to="/messages" replace />} />
  <Route path="/messages" element={<MessagesPage />} />
  <Route path="/specifications" element={<SpecificationsPage />} />
  <Route path="/intents" element={<IntentsPage />} />
  <Route path="/contradictions" element={<ContradictionsPage />} />
  {/* 🆕 追加ルート */}
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/choice-points" element={<ChoicePointsPage />} />
  <Route path="/memory" element={<MemoryPage />} />
  <Route path="/term-drift" element={<TermDriftPage />} />
  <Route path="/temporal-constraint" element={<TemporalConstraintPage />} />
  <Route path="/files" element={<FileModificationPage />} />
</Routes>
```

---

## 5. 共通コンポーネント

### 5.1 ConstraintLevelBadge

全ページで使用する制約レベル表示バッジ。

```typescript
interface ConstraintLevelBadgeProps {
  level: 'critical' | 'high' | 'medium' | 'low';
}

const levelColors = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-green-100 text-green-800 border-green-200',
};
```

### 5.2 ConfidenceBar

信頼度を視覚的に表示するバー。

```typescript
interface ConfidenceBarProps {
  value: number;  // 0-1
  showLabel?: boolean;
}
```

### 5.3 StatusBadge

各種ステータスを表示するバッジ。

```typescript
interface StatusBadgeProps {
  status: string;
  variant?: 'default' | 'success' | 'warning' | 'error';
}
```

---

## 6. 技術仕様

### 6.1 状態管理

- **React Query**: サーバー状態管理（既存パターン踏襲）
- **ポーリング間隔**: 5秒（標準）、10秒（通知）
- **キャッシュ無効化**: mutation成功時に関連クエリを無効化

### 6.2 エラーハンドリング

```typescript
// 共通エラーハンドラ
const handleApiError = (error: AxiosError) => {
  if (error.response?.status === 404) {
    toast.error('リソースが見つかりません');
  } else if (error.response?.status === 400) {
    const detail = error.response.data?.detail;
    toast.error(detail || 'リクエストが不正です');
  } else {
    toast.error('エラーが発生しました');
  }
};
```

### 6.3 バリデーション

- **Contradiction Resolve**: resolution_rationale 10文字以上
- **Term Drift Resolve**: resolution_note 10文字以上
- **File Modification**: reason がconstraint_levelに応じた長さ
  - CRITICAL: 手動承認必須（UIでブロック）
  - HIGH: 50文字以上
  - MEDIUM: 20文字以上
  - LOW: 1文字以上

---

## 7. 実装スケジュール

### Phase 13-A（Day 1-3）
- [ ] ContradictionResolveModal
- [ ] ContradictionDetail
- [ ] DashboardPage + コンポーネント

### Phase 13-B（Day 4-6）
- [ ] ChoicePointsPage + コンポーネント
- [ ] MemoryPage + コンポーネント

### Phase 13-C（Day 7-10）
- [ ] Term Drift 型定義 + API + ページ
- [ ] Temporal Constraint 型定義 + API + ページ
- [ ] File Modification 型定義 + API + ページ

### Phase 13-D（Day 11-12）
- [ ] ナビゲーション更新
- [ ] 共通コンポーネント
- [ ] 統合テスト

---

## 8. 成功基準

1. **機能完成度**: 全7機能のUI実装完了
2. **API統合**: 全エンドポイントとの正常通信確認
3. **ユーザビリティ**: 各操作が3クリック以内で完了
4. **レスポンシブ**: モバイル/タブレット対応
5. **エラーハンドリング**: 全APIエラーの適切な表示

---

## 9. リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| API仕様変更 | 高 | バックエンドと設計レビュー実施 |
| 型不整合 | 中 | TypeScript strict mode有効化 |
| パフォーマンス低下 | 中 | React Query キャッシュ最適化 |
| UI/UX不統一 | 低 | 共通コンポーネントライブラリ活用 |

---

**作成者**: Resonant Engine Team
**レビュー**: カナ（設計監査）
**承認待ち**: ユノ（思想整合確認）
