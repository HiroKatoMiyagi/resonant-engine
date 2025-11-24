# Frontend Core Features Implementation 仕様書

## 0. CRITICAL: フロントエンド vs バックエンド ギャップ解消

**⚠️ IMPORTANT: 「フロントエンド実装率35% → 100%達成」**

Frontend Core Features Implementationは、現在35%しか実装されていないフロントエンド機能を、バックエンドとの100%対応を目指して完全実装します。特に矛盾検出UI、リアルタイム通信、ダッシュボード分析などの重要機能が未実装であり、これらを優先的に実装します。

```yaml
frontend_gap_analysis:
    current_implementation: "35% (基本CRUD のみ)"
    target_implementation: "100% (バックエンド完全対応)"
    critical_missing:
        - Contradiction Detection UI (最重要)
        - WebSocket/SSE Integration (効率化)
        - Dashboard Analytics (可視化)
        - Choice Preservation UI (選択肢管理)
        - Re-evaluation Phase UI (AI修正フィードバック)
    current_inefficiencies:
        - 5秒間隔ポーリング → WebSocket切り替え必須
        - システム状態の可視化なし
        - 矛盾検出結果がUIで見えない
```

### 現在の実装状況

```
バックエンド機能 (100%完成)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

フロントエンド対応 (35%のみ)
━━━━━━━━━━━━━━░░░░░░░░░░░░░░░░░░░░░░░░░░░
              ↑
    ここまで実装済み（Messages, Intents, Specifications, Notifications CRUD）

未対応の重要機能:
  - Contradiction Detection (矛盾検出) ❌
  - Choice Preservation (選択肢保存) ❌
  - Re-evaluation Phase (AI修正) ❌
  - Dashboard Analytics (分析) ❌
  - WebSocket (リアルタイム) ❌
  - Memory Lifecycle UI (記憶管理) ❌
```

### 呼吸モデルとの関係

```
Frontend Implementation (フロントエンドの呼吸)
    ↓
Phase 1: Contradiction Detection UI (矛盾の可視化)
    ↓
Phase 2: WebSocket Integration (リアルタイム通信)
    ↓
Phase 3: Dashboard Analytics (システム状態可視化)
    ↓
Phase 4: Choice Preservation UI (選択肢保存)
    ↓
Phase 5: Re-evaluation UI (AI修正フィードバック)
```

### Done Definition (Phase制)

#### Phase 1: 矛盾検出UI (最重要)
- [ ] ContradictionDashboard実装（グリッド3列レイアウト）
- [ ] ContradictionItem実装（レベル別色分け）
- [ ] ContradictionFilter実装（フィルタリング機能）
- [ ] ContradictionResolution実装（解決アクション）
- [ ] API統合完了（`/api/contradictions/`）

#### Phase 2: WebSocket統合 (効率化)
- [ ] WebSocketクライアント実装
- [ ] 5秒ポーリング → リアルタイム通信切り替え
- [ ] 対象コンポーネント更新（Messages, Notifications, Dashboard）
- [ ] 接続管理・エラーハンドリング実装

#### Phase 3: Dashboard Analytics (可視化)
- [ ] AnalyticsDashboard実装
- [ ] SystemMetrics実装（Messages総数、Intents総数、矛盾検出数）
- [ ] ActivityGraph実装（時系列グラフ）
- [ ] StatusIndicator実装（Crisis Index表示）

#### Phase 4: Choice Preservation UI (選択肢管理)
- [ ] ChoicePointsList実装
- [ ] ChoicePointDetail実装
- [ ] ChoiceRestore実装
- [ ] API統合完了（`/api/choices/`）

#### Phase 5: Re-evaluation UI (AI修正)
- [ ] ReEvaluationPanel実装
- [ ] AIFeedbackDisplay実装
- [ ] Re-evaluation Phase発動時の可視化

---

## 1. 概要

### 1.1 目的
React + TypeScriptフロントエンドを拡張し、バックエンドの全機能に対応したUIを提供する。

### 1.2 背景

**現在のフロントエンド実装状況:**
- ✅ Messages CRUD (完了)
- ✅ Intents CRUD (完了)
- ✅ Specifications CRUD (完了)
- ✅ Notifications (完了)
- ❌ Contradiction Detection (未実装)
- ❌ Choice Preservation (未実装)
- ❌ Re-evaluation Phase (未実装)
- ❌ Dashboard Analytics (未実装)
- ❌ WebSocket/SSE (ポーリングのみ)
- ❌ Memory Lifecycle (未実装)

**問題:**
- 重要な機能（矛盾検出、選択肢保存）がUIで操作できない
- 5秒間隔のポーリングが非効率
- システム状態が可視化されていない
- AI修正フィードバックが見えない

### 1.3 目標
- フロントエンド実装率: 35% → 100%
- 矛盾検出UIによるユーザビリティ向上
- WebSocket統合による効率化
- ダッシュボードによるシステム状態可視化

### 1.4 技術スタック（変更禁止）

```typescript
// 既存スタック維持
{
  "frontend": {
    "framework": "React 18",
    "language": "TypeScript",
    "build": "Vite",
    "styling": "Tailwind CSS",
    "data": "React Query v4",
    "http": "Axios",
    "routing": "React Router"
  }
}
```

---

## 2. フェーズ別詳細仕様

### 2.1 Phase 1: 矛盾検出UI (最重要)

#### 2.1.1 機能要件

**目的**: バックエンドの矛盾検出機能をフロントエンドで完全に可視化

**API仕様**: 既存 `/api/contradictions/` エンドポイント使用

**コンポーネント構成**:
```typescript
/src/components/contradiction/
├─ ContradictionDashboard.tsx     // メインダッシュボード
├─ ContradictionItem.tsx          // 個別矛盾表示
├─ ContradictionFilter.tsx        // フィルタリング
└─ ContradictionResolution.tsx    // 解決アクション
```

#### 2.1.2 UI仕様（厳守）

**レイアウト**: グリッド3列
**色指定**:
- Error: `border-red-500 bg-red-50`
- Warning: `border-yellow-500 bg-yellow-50`
- Info: `border-blue-500 bg-blue-50`

**フォント**: Inter, 14px base
**スペーシング**: Tailwind標準（p-4, m-2等）

#### 2.1.3 データフロー

```typescript
interface ContradictionResponse {
  id: number;
  level: 'error' | 'warning' | 'info';
  message: string;
  created_at: string;
  resolved: boolean;
  confidence_score?: number;
  related_intent_ids?: number[];
}
```

### 2.2 Phase 2: WebSocket統合 (効率化)

#### 2.2.1 機能要件

**目的**: 5秒ポーリング → リアルタイム通信切り替え

**WebSocket URL**: `ws://localhost:8000/ws` (環境変数から取得)

**対象コンポーネント**:
- MessagesPage (メッセージ更新)
- NotificationsPanel (通知受信)
- DashboardAnalytics (メトリクス更新)
- ContradictionDashboard (矛盾検出更新)

#### 2.2.2 実装仕様

```typescript
// WebSocketクライアント（場所指定）
/src/hooks/useWebSocket.ts
/src/services/websocket.ts

// イベントタイプ（追加禁止）
type WebSocketEvent =
  | 'message_created'
  | 'contradiction_detected'
  | 'notification_sent'
  | 'system_status_update'
```

#### 2.2.3 接続管理

```typescript
const WS_CONFIG = {
  url: process.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  reconnectInterval: 5000,
  maxReconnectAttempts: 10
}
```

### 2.3 Phase 3: Dashboard Analytics (可視化)

#### 2.3.1 機能要件

**目的**: システム状態をリアルタイム表示

**コンポーネント構成**:
```typescript
/src/components/dashboard/
├─ AnalyticsDashboard.tsx
├─ SystemMetrics.tsx
├─ ActivityGraph.tsx
└─ StatusIndicator.tsx
```

#### 2.3.2 表示項目（追加・削除禁止）

```typescript
interface SystemMetrics {
  messages_count: number;
  intents_count: number;
  contradictions_count: number;
  crisis_index: number; // 0-100
  uptime_percentage: number;
  memory_usage_mb?: number;
}
```

### 2.4 Phase 4: Choice Preservation UI

#### 2.4.1 API仕様（変更禁止）

```typescript
// 既存API使用
GET    /api/choices/
POST   /api/choices/
PUT    /api/choices/{id}/restore
DELETE /api/choices/{id}
```

#### 2.4.2 コンポーネント構成

```typescript
/src/components/choice/
├─ ChoicePointsList.tsx
├─ ChoicePointDetail.tsx
└─ ChoiceRestore.tsx
```

### 2.5 Phase 5: Re-evaluation UI

#### 2.5.1 機能要件

**目的**: Re-evaluation Phase発動時のAI修正を可視化

**表示内容**:
- 修正前の状態
- AI提案内容
- 修正後の状態
- ユーザー承認/拒否

---

## 3. 非機能要件

### 3.1 パフォーマンス要件

| 項目 | 要件 |
|-----|------|
| 初期表示 | < 3秒 |
| API応答 | < 2秒 |
| WebSocket接続 | < 1秒 |
| メモリ使用量 | < 50MB |

### 3.2 ユーザビリティ要件

- 直感的なレイアウト
- 色による視覚的分類
- レスポンシブデザイン
- エラー状態の明確な表示

### 3.3 保守性要件

- TypeScript型安全性100%
- コンポーネント単位での分割
- 既存APIとの完全互換性
- 設定の外部化

---

## 4. 制約事項

### 4.1 技術制約（厳守）

1. **使用技術スタック変更禁止**
2. **既存APIエンドポイント変更禁止**
3. **ファイル配置規則厳守**
4. **色・フォント・スペーシング指定厳守**
5. **追加機能実装禁止**（アニメーション等）

### 4.2 実装制約

1. **判断余地を与えない詳細指定**
2. **段階的実装（Phase順厳守）**
3. **既存コードとの競合回避**
4. **テスト可能性の確保**

---

## 5. テスト戦略

### 5.1 単体テスト

- Jest + React Testing Library
- コンポーネント単位でのテスト
- API統合テスト（Mock Serviceない場合）

### 5.2 統合テスト

- E2Eテスト（Playwright推奨）
- 実際のバックエンドとの統合確認
- WebSocket接続テスト

### 5.3 受け入れテスト

- Phase毎の受け入れ基準
- UI/UX要件の確認
- パフォーマンステスト

---

## 6. リスク管理

### 6.1 技術リスク

| リスク | 影響度 | 対策 |
|--------|--------|------|
| WebSocket接続不安定 | 中 | フォールバック（ポーリング）機能 |
| API応答遅延 | 中 | タイムアウト処理・ローディング状態 |
| バックエンド仕様変更 | 高 | 型定義による早期検出 |

### 6.2 スケジュールリスク

| リスク | 対策 |
|--------|------|
| Phase 1遅延 | 最重要機能のため優先リソース投入 |
| WebSocket実装複雑化 | 段階的実装（接続→イベント→統合） |
| テスト工数不足 | 実装と並行してテスト作成 |

---

## 7. 実装優先順位

### Priority 1 (必須)
- Phase 1: 矛盾検出UI
- Phase 2: WebSocket統合

### Priority 2 (重要)
- Phase 3: Dashboard Analytics

### Priority 3 (推奨)
- Phase 4: Choice Preservation UI
- Phase 5: Re-evaluation UI

---

**作成者**: Claude Sonnet 4 (Kana)
**作成日**: 2025-11-24
**バージョン**: 1.0
**対象システム**: Resonant Engine Frontend