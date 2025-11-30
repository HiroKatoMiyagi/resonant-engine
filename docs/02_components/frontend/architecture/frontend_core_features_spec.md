# Frontend Core Features 実装仕様書

**作成日**: 2025-11-24
**バージョン**: 1.1（API仕様修正版）
**Sprint**: 14-15（フロントエンド拡張）
**対象システム**: Resonant Engine Frontend

---

## ⚠️ 重要事項（MUST READ FIRST）

### 絶対遵守事項（MUST）

1. **本仕様書のAPI仕様に厳密に従うこと**
   - バックエンドAPIは2種類存在する（dashboard API + bridge API）
   - 各APIのプレフィックスを正確に使用すること

2. **既存のフロントエンド構造を維持すること**
   - `frontend/src/` の既存ディレクトリ構造を破壊しない
   - 既存の `api/client.ts` を拡張して使用

3. **型定義はバックエンドスキーマに完全一致させること**
   - 独自の型定義を作らない
   - 本仕様書の型定義をそのまま使用

4. **総合テストv3.7の教訓を適用すること**
   - 環境変数はハードコードしない
   - 推測で実装しない（仕様書に従う）

### 禁止事項（MUST NOT）

| 禁止事項 | 理由 | 総合テストでの教訓 |
|---------|------|------------------|
| APIエンドポイントの独自変更 | バックエンド仕様に依存 | v3.5でモデル名間違いが発覚 |
| 型定義の独自改変 | 型安全性の破壊 | - |
| ハードコード値の使用 | 環境依存になる | v3.4でパスワードハードコード問題 |
| 既存コンポーネントの変更 | 動作中機能の破壊 | - |
| 仕様書にない機能追加 | スコープクリープ | v3.5でスキップ濫用 |
| `any`型の使用 | 型安全性の破壊 | - |

---

## 0. バックエンドAPI構成

### 統一されたBackend API

Resonant EngineのバックエンドAPIは、**単一のFastAPIアプリケーション**で全機能を提供します。

```
┌─────────────────────────────────────────────────────────────┐
│ Backend API (backend/app/)                                  │
│ ・ポート: 8000                                               │
│ ・すべての機能が統合されています                               │
│   - 基本CRUD機能（Messages, Intents, Specifications等）      │
│   - 高度機能（Contradiction, Re-evaluation, Memory等）       │
│   - WebSocket通信                                           │
└─────────────────────────────────────────────────────────────┘
```

### APIエンドポイント構成

```plaintext
Frontend
  └─ Backend API (http://localhost:8000)
      ├─ 基本CRUD
      │   ├─ /api/messages
      │   ├─ /api/intents
      │   ├─ /api/specifications
      │   └─ /api/notifications
      │
      ├─ 高度機能
      │   ├─ /api/v1/contradiction/*      (矛盾検出)
      │   ├─ /api/v1/intent/reeval        (再評価)
      │   ├─ /api/v1/memory/choice-points/* (選択保存)
      │   ├─ /api/v1/memory/lifecycle/*   (メモリライフサイクル)
      │   └─ /api/v1/dashboard/*          (ダッシュボード分析)
      │
      └─ WebSocket
          └─ /ws/intents                   (リアルタイム通知)
```

### エンドポイント一覧

#### 基本CRUD (既存)
```
GET    /api/messages           - メッセージ一覧
POST   /api/messages           - メッセージ作成
GET    /api/intents            - Intent一覧
POST   /api/intents            - Intent作成
GET    /api/specifications     - 仕様書一覧
POST   /api/specifications     - 仕様書作成
GET    /api/notifications      - 通知一覧
```

#### Contradiction Detection (統合済み)
```
POST   /api/v1/contradiction/check           - 矛盾チェック
GET    /api/v1/contradiction/pending         - 未解決矛盾一覧
PUT    /api/v1/contradiction/{id}/resolve    - 矛盾解決
```

#### Re-evaluation (統合済み)
```
POST   /api/v1/intent/reeval                 - Intent再評価
```

#### Choice Preservation (統合済み)
```
GET    /api/v1/memory/choice-points/pending  - 未決定選択肢取得
POST   /api/v1/memory/choice-points/         - 選択肢作成
PUT    /api/v1/memory/choice-points/{id}/decide - 選択決定
GET    /api/v1/memory/choice-points/search   - 選択肢検索
```

#### Memory Lifecycle (統合済み)
```
GET    /api/v1/memory/lifecycle/status       - メモリステータス取得
POST   /api/v1/memory/lifecycle/compress     - メモリ圧縮
DELETE /api/v1/memory/lifecycle/expired      - 期限切れクリーンアップ
```

#### Dashboard Analytics (統合済み)
```
GET    /api/v1/dashboard/overview            - システム概要
GET    /api/v1/dashboard/timeline            - タイムライン
GET    /api/v1/dashboard/corrections         - 修正履歴
```

#### WebSocket (既存)
```
WS     /ws/intents                           - Intent更新リアルタイム通知
```

---

## 1. 概要

### 1.1 目的
フロントエンド実装率を35%から100%に引き上げ、バックエンドの全機能に対応したUIを提供する。

### 1.2 現在の実装状況

```
バックエンド機能 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

フロントエンド  ━━━━━━━━━━━━━░░░░░░░░░░░░░░░░░░░░  35%
                          ↑
               ここまで実装済み
               (Messages, Intents, Specifications, Notifications)
```

### 1.3 技術スタック（変更禁止）

```typescript
// 既存スタック - 変更してはならない
{
  "framework": "React 18.2.0",
  "language": "TypeScript 5.2.2",
  "build": "Vite 5.0.0",
  "styling": "Tailwind CSS 3.3.5",
  "data": "TanStack React Query 5.8.4",
  "http": "Axios 1.6.2",
  "routing": "React Router DOM 6.20.1"
}
```

---

## 2. 型定義（バックエンド準拠・変更禁止）

### 2.1 Contradiction型（Sprint 11バックエンドと一致）

```typescript
// src/types/contradiction.ts - この通りに作成すること

/**
 * 矛盾タイプ（バックエンドのcontradiction_typeに対応）
 * 変更禁止 - バックエンドのdetector.pyで定義されている値
 */
export type ContradictionType =
  | 'tech_stack'    // 技術スタック矛盾
  | 'policy_shift'  // ポリシー転換
  | 'duplicate'     // 重複作業
  | 'dogma';        // ドグマ（未検証の断定）

/**
 * 解決ステータス
 * 変更禁止 - バックエンドのapi_schemas.pyで定義
 */
export type ResolutionStatus = 'pending' | 'resolved' | 'dismissed';

/**
 * 解決アクション
 * 変更禁止 - バックエンドのapi_schemas.pyで定義
 */
export type ResolutionAction = 'policy_change' | 'mistake' | 'coexist';

/**
 * ContradictionSchema - バックエンドapi_schemas.pyと完全一致
 *
 * IMPORTANT: この型定義はバックエンドのContradictionSchemaと
 * 1対1で対応している。変更してはならない。
 */
export interface Contradiction {
  id: string;                              // UUID形式
  user_id: string;
  new_intent_id: string;                   // UUID形式
  new_intent_content: string;
  conflicting_intent_id: string | null;    // UUID形式
  conflicting_intent_content: string | null;
  contradiction_type: ContradictionType;
  confidence_score: number;                // 0.0-1.0
  detected_at: string;                     // ISO 8601形式
  details: Record<string, unknown>;
  resolution_status: ResolutionStatus;
  resolution_action: ResolutionAction | null;
  resolution_rationale: string | null;
  resolved_at: string | null;              // ISO 8601形式
}

/**
 * 矛盾チェックリクエスト
 */
export interface CheckContradictionRequest {
  user_id: string;
  intent_id: string;       // UUID形式
  intent_content: string;
}

/**
 * 矛盾解決リクエスト
 */
export interface ResolveContradictionRequest {
  resolution_action: ResolutionAction;
  resolution_rationale: string;  // 最低10文字
  resolved_by: string;
}

/**
 * APIレスポンス（一覧取得用）
 */
export interface ContradictionListResponse {
  contradictions: Contradiction[];
  total: number;
}
```

### 2.2 SystemMetrics型（Dashboard Analytics用）

```typescript
// src/types/dashboard.ts

/**
 * システムメトリクス - /api/v1/dashboard/overview のレスポンス
 */
export interface SystemOverview {
  messages_count: number;
  intents_count: number;
  active_sessions: number;
  contradictions_pending: number;
  crisis_index: number;           // 0-100
  last_updated: string;           // ISO 8601
}

/**
 * タイムラインデータ
 */
export interface TimelineEntry {
  timestamp: string;
  event_type: string;
  count: number;
}

export interface TimelineResponse {
  entries: TimelineEntry[];
  granularity: 'minute' | 'hour' | 'day';
}
```

### 2.3 ChoicePoint型（Memory API用）

```typescript
// src/types/choice.ts

export interface Choice {
  id: string;
  choice_text: string;
  selected: boolean;
  evaluation_score: number | null;
  rejection_reason: string | null;
}

export interface ChoicePoint {
  id: string;
  user_id: string;
  question: string;
  choices: Choice[];
  selected_choice_id: string | null;
  tags: string[];
  context_type: string;
  decision_rationale: string | null;
  created_at: string;
  decided_at: string | null;
}
```

---

## 3. Phase 1: 矛盾検出UI（Sprint 14）

### 3.1 ファイル構成（この通りに作成）

```
frontend/src/
├── types/
│   └── contradiction.ts      # 2.1の型定義
├── api/
│   └── contradiction.ts      # API呼び出し関数
├── components/
│   └── contradiction/
│       ├── ContradictionDashboard.tsx
│       ├── ContradictionItem.tsx
│       ├── ContradictionFilter.tsx
│       └── ContradictionResolution.tsx
└── pages/
    └── ContradictionsPage.tsx
```

### 3.2 API呼び出し関数

```typescript
// src/api/contradiction.ts

import axios from 'axios';
import type {
  Contradiction,
  ContradictionListResponse,
  CheckContradictionRequest,
  ResolveContradictionRequest
} from '../types/contradiction';

// API Base URL - 環境変数から取得（ハードコード禁止）
const BRIDGE_API_URL = import.meta.env.VITE_BRIDGE_API_URL || 'http://localhost:8000';

/**
 * 未解決の矛盾一覧を取得
 */
export async function getPendingContradictions(
  userId: string
): Promise<ContradictionListResponse> {
  const response = await axios.get<ContradictionListResponse>(
    `${BRIDGE_API_URL}/api/v1/contradiction/pending`,
    { params: { user_id: userId } }
  );
  return response.data;
}

/**
 * Intentの矛盾をチェック
 */
export async function checkIntentContradiction(
  request: CheckContradictionRequest
): Promise<ContradictionListResponse> {
  const response = await axios.post<ContradictionListResponse>(
    `${BRIDGE_API_URL}/api/v1/contradiction/check`,
    request
  );
  return response.data;
}

/**
 * 矛盾を解決
 */
export async function resolveContradiction(
  contradictionId: string,
  request: ResolveContradictionRequest
): Promise<{ status: string }> {
  const response = await axios.put<{ status: string }>(
    `${BRIDGE_API_URL}/api/v1/contradiction/${contradictionId}/resolve`,
    request
  );
  return response.data;
}
```

### 3.3 UI仕様（厳守）

#### 色指定（変更禁止）

| contradiction_type | 枠線 | 背景 | 意味 |
|-------------------|------|------|------|
| `tech_stack` | `border-red-500` | `bg-red-50` | 技術スタック矛盾 |
| `policy_shift` | `border-orange-500` | `bg-orange-50` | ポリシー転換 |
| `duplicate` | `border-yellow-500` | `bg-yellow-50` | 重複作業 |
| `dogma` | `border-blue-500` | `bg-blue-50` | ドグマ検出 |

#### レイアウト仕様

- グリッド: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`
- カード: `p-4 border-2 rounded-lg`
- 信頼度バー: `h-2 bg-gray-200 rounded` + 内部バー

---

## 4. Phase 2: WebSocket統合（Sprint 14後半）

### 4.1 WebSocket接続設定

```typescript
// src/hooks/useWebSocket.ts

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/intents';

interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
}

const defaultConfig: WebSocketConfig = {
  url: WS_URL,
  reconnectInterval: 5000,  // 5秒
  maxReconnectAttempts: 10,
};
```

### 4.2 イベントタイプ（変更禁止）

```typescript
type WebSocketEventType =
  | 'intent_created'
  | 'intent_updated'
  | 'contradiction_detected'
  | 'choice_point_created';
```

---

## 5. Phase 3: Dashboard Analytics（Sprint 15）

### 5.1 API呼び出し

```typescript
// src/api/dashboard.ts

export async function getSystemOverview(): Promise<SystemOverview> {
  const response = await axios.get<SystemOverview>(
    `${BRIDGE_API_URL}/api/v1/dashboard/overview`
  );
  return response.data;
}

export async function getTimeline(
  granularity: 'minute' | 'hour' | 'day' = 'hour'
): Promise<TimelineResponse> {
  const response = await axios.get<TimelineResponse>(
    `${BRIDGE_API_URL}/api/v1/dashboard/timeline`,
    { params: { granularity } }
  );
  return response.data;
}
```

### 5.2 Crisis Index表示仕様

| Crisis Index | 色 | 状態 |
|--------------|-----|------|
| 0-69 | `text-green-600` | 正常 |
| 70-84 | `text-yellow-600` | 警告（pre-crisis） |
| 85-100 | `text-red-600` | 危機（crisis） |

---

## 6. 非機能要件

### 6.1 パフォーマンス要件

| 項目 | 要件 |
|-----|------|
| 初期表示 | < 3秒 |
| API応答 | < 2秒 |
| WebSocket接続 | < 1秒 |
| メモリ使用量 | < 50MB |

### 6.2 エラーハンドリング

```typescript
// すべてのAPI呼び出しで使用するエラーハンドリング
try {
  const data = await apiCall();
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 404) {
      // エンドポイントが見つからない
      console.error('API endpoint not found');
    } else if (error.response?.status === 500) {
      // サーバーエラー
      console.error('Server error');
    }
  }
  throw error;
}
```

---

## 7. 環境変数設定

```bash
# frontend/.env.local（この形式で設定）

# Dashboard Backend
VITE_API_URL=http://localhost:8000

# Bridge API（高度機能用）
VITE_BRIDGE_API_URL=http://localhost:8000

# WebSocket
VITE_WS_URL=ws://localhost:8000/ws/intents
```

**注意**: 環境変数はハードコードしない。`import.meta.env.VITE_*` から取得すること。

---

## 8. 実装優先順位

### Sprint 14（必須）
1. Phase 1: 矛盾検出UI（最重要）
2. Phase 2: WebSocket統合（効率化）

### Sprint 15（重要）
3. Phase 3: Dashboard Analytics
4. Phase 4: Choice Preservation UI
5. Phase 5: Re-evaluation UI

---

**作成者**: Claude Code
**レビュー日**: 2025-11-24
**バージョン**: 1.1（API仕様修正版）
