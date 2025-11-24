# Frontend Core Features Implementation 作業開始指示書

## 概要

**Sprint**: Frontend Core Features
**タイトル**: Frontend Core Features Implementation
**期間**: kiroペース（段階的実装）
**目標**: フロントエンド実装率35% → 100%達成（バックエンド完全対応）

---

## ⚠️ 重要事項（kiro特性対応）

### 絶対遵守事項（MUST）

1. **仕様書通りの実装を行うこと**
   - 独自判断・改善提案・仕様変更を一切行わない
   - 指定されたファイル配置・コンポーネント名・CSS class名を厳守

2. **段階的実装を行うこと**
   - Phase順（1→2→3→4→5）で実装
   - Phase完了前に次に進まない

3. **既存コードを破壊しないこと**
   - 現在動作している機能（Messages, Intents, Specifications, Notifications）は変更しない
   - 新規コンポーネントのみ追加

### 禁止事項（MUST NOT）

| 禁止事項 | 理由 |
|---------|------|
| CSS class名変更 | Tailwind指定通り。デザインの一貫性確保 |
| API URL変更 | 既存バックエンドAPI仕様に準拠 |
| コンポーネント名変更 | ファイル管理・importの一貫性 |
| 追加機能実装 | アニメーション・バリデーション等追加禁止 |
| 型定義変更 | 既存interface定義改変禁止 |
| ファイル場所変更 | 指定されたディレクトリ構造厳守 |

---

## Phase 1: 矛盾検出UI実装（最重要）

### 目標
バックエンドの矛盾検出機能をフロントエンドで完全可視化

### 実装ステップ

#### Step 1: ディレクトリ・ファイル作成

```bash
# 実行場所: /Users/zero/Projects/resonant-engine/frontend/

# ディレクトリ作成
mkdir -p src/components/contradiction

# ファイル作成（この名前で作成すること）
touch src/components/contradiction/ContradictionDashboard.tsx
touch src/components/contradiction/ContradictionItem.tsx
touch src/components/contradiction/ContradictionFilter.tsx
touch src/components/contradiction/ContradictionResolution.tsx
```

#### Step 2: 型定義追加

**ファイル**: `src/types/api.ts`（既存ファイルに追加）

```typescript
// ContradictionResponseインターフェースを追加
export interface ContradictionResponse {
  id: number;
  level: 'error' | 'warning' | 'info';
  message: string;
  created_at: string;
  resolved: boolean;
  confidence_score?: number;
  related_intent_ids?: number[];
}

// システムメトリクス用（Phase 3で使用）
export interface SystemMetrics {
  messages_count: number;
  intents_count: number;
  contradictions_count: number;
  crisis_index: number;
  uptime_percentage: number;
  memory_usage_mb?: number;
}
```

#### Step 3: ContradictionDashboard.tsx 実装

**ファイル**: `src/components/contradiction/ContradictionDashboard.tsx`

```typescript
import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import ContradictionItem from './ContradictionItem';
import type { ContradictionResponse } from '../../types/api';

const ContradictionDashboard: React.FC = () => {
  const { data: contradictions, isLoading, error } = useQuery(
    'contradictions',
    () => axios.get<ContradictionResponse[]>('/api/contradictions/').then(res => res.data),
    {
      refetchInterval: 5000, // Phase 2でWebSocketに切り替え予定
      staleTime: 0,
      cacheTime: 0
    }
  );

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center text-red-600">
          エラーが発生しました。バックエンドAPIの接続を確認してください。
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">矛盾検出ダッシュボード</h1>

      {contradictions && contradictions.length > 0 ? (
        <div className="grid grid-cols-3 gap-4">
          {contradictions.map(contradiction => (
            <ContradictionItem
              key={contradiction.id}
              contradiction={contradiction}
            />
          ))}
        </div>
      ) : (
        <div className="text-center text-gray-500">
          現在、検出された矛盾はありません。
        </div>
      )}
    </div>
  );
};

export default ContradictionDashboard;
```

#### Step 4: ContradictionItem.tsx 実装

**ファイル**: `src/components/contradiction/ContradictionItem.tsx`

```typescript
import React from 'react';
import type { ContradictionResponse } from '../../types/api';

interface ContradictionItemProps {
  contradiction: ContradictionResponse;
}

const getLevelColor = (level: string) => {
  switch (level) {
    case 'error': return 'border-red-500 bg-red-50';
    case 'warning': return 'border-yellow-500 bg-yellow-50';
    case 'info': return 'border-blue-500 bg-blue-50';
    default: return 'border-gray-500 bg-gray-50';
  }
};

const getLevelTextColor = (level: string) => {
  switch (level) {
    case 'error': return 'text-red-800';
    case 'warning': return 'text-yellow-800';
    case 'info': return 'text-blue-800';
    default: return 'text-gray-800';
  }
};

const ContradictionItem: React.FC<ContradictionItemProps> = ({ contradiction }) => {
  return (
    <div className={`p-4 border-2 rounded-lg ${getLevelColor(contradiction.level)}`}>
      <div className="flex justify-between items-start mb-2">
        <span className={`text-sm font-semibold ${getLevelTextColor(contradiction.level)}`}>
          {contradiction.level.toUpperCase()}
        </span>
        <span className="text-xs text-gray-500">
          {new Date(contradiction.created_at).toLocaleDateString('ja-JP')}
        </span>
      </div>

      <p className="text-sm mb-3 text-gray-900">{contradiction.message}</p>

      <div className="flex justify-between items-center">
        <div>
          {contradiction.resolved ? (
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
              解決済み
            </span>
          ) : (
            <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
              未解決
            </span>
          )}
        </div>

        {contradiction.confidence_score && (
          <span className="text-xs text-gray-600">
            信頼度: {(contradiction.confidence_score * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  );
};

export default ContradictionItem;
```

#### Step 5: ルーティング設定

**ファイル**: `src/App.tsx` の既存Routes内に追加

```typescript
// Importセクションに追加
import ContradictionDashboard from './components/contradiction/ContradictionDashboard';

// <Routes>内の適切な場所に追加（既存のRouteの後）
<Route path="/contradictions" element={<ContradictionDashboard />} />
```

#### Step 6: ナビゲーション追加

既存のナビゲーションコンポーネント（通常は Header.tsx または Navbar.tsx）に追加:

```typescript
// ナビゲーションリンクに追加
<Link
  to="/contradictions"
  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
>
  矛盾検出
</Link>
```

---

## Phase 1 実装確認チェックリスト

完了前に以下を確認すること：

### ファイル作成確認
- [ ] `src/components/contradiction/ContradictionDashboard.tsx` 作成済み
- [ ] `src/components/contradiction/ContradictionItem.tsx` 作成済み
- [ ] `src/types/api.ts` にContradictionResponse型追加済み

### 機能確認
- [ ] `npm run dev` でエラーなく起動
- [ ] `/contradictions` ページにアクセス可能
- [ ] ナビゲーションリンクから遷移可能
- [ ] APIエラー時に適切なエラーメッセージ表示
- [ ] データがない場合に適切なメッセージ表示

### UI確認
- [ ] グリッド3列レイアウト表示
- [ ] 矛盾レベルによる色分け（error=赤、warning=黄、info=青）
- [ ] 解決ステータス表示（解決済み/未解決）
- [ ] 作成日時表示
- [ ] 信頼度スコア表示（存在する場合）

---

## Phase 1 完了後の報告事項

以下の内容を報告すること：

1. **実装完了ファイル一覧**
   - 作成したファイルパスとファイルサイズ

2. **動作確認結果**
   - ローカル開発サーバーでの動作状況
   - エラーの有無
   - UIの表示状況

3. **発見した問題・困った点**
   - 仕様書と実際の差異
   - 想定外のエラー
   - 判断に迷った点

4. **次フェーズへの準備状況**
   - Phase 1が完全に動作すること
   - 既存機能に影響がないこと

---

## デバッグ時の対応

### API接続エラーが発生した場合

1. **バックエンドサーバーの起動確認**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Contradiction APIエンドポイント確認**
   ```bash
   curl http://localhost:8000/api/contradictions/
   ```

3. **ネットワークタブでHTTPステータス確認**
   - 200: 正常
   - 404: エンドポイントが見つからない → バックエンド実装確認
   - 500: サーバーエラー → バックエンドログ確認

### TypeScriptエラーが発生した場合

1. **型定義の確認**
   - `src/types/api.ts` にContradictionResponse型が正しく定義されているか

2. **import文の確認**
   - 相対パス（`../../types/api`）が正しいか

3. **コンパイルエラーの解決**
   ```bash
   npm run type-check
   ```

---

## Phase 2以降の準備

Phase 1完了後、以下の準備を行う：

### Phase 2 (WebSocket統合) 準備事項
- WebSocketライブラリ選定（推奨: native WebSocket API）
- 環境変数設定（VITE_WS_URL）
- 既存ポーリングの特定

### Phase 3 (Dashboard Analytics) 準備事項
- システムメトリクス取得API確認
- グラフライブラリ選定（推奨: Chart.js または Recharts）

---

**注意**: Phase 1が完全に動作することを確認してから次のPhaseに進むこと。不具合がある状態で進めてはならない。

**作成者**: Claude Sonnet 4 (Kana)
**作成日**: 2025-11-24
**対象**: kiro実装者
**重要度**: 最高（プロジェクト成功の鍵）