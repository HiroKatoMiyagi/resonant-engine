# Frontend Sprint 14 作業開始指示書

**Sprint**: 14（フロントエンド拡張 Phase 1-2）
**対象**: Kiro（Claude Sonnet 4.5）実装者
**作成日**: 2025-11-24
**バージョン**: 1.1

---

## ⚠️ 最重要警告（総合テストv3.7からの教訓）

### Kiro特性を考慮した絶対遵守事項

総合テストv3.1〜v3.7の実施で判明したKiroの傾向に基づく警告：

| 過去の問題 | 発生Sprint | 対策 |
|-----------|-----------|------|
| パスワードのハードコード | v3.4 | 環境変数を使用すること |
| 独自判断でのテストスキップ | v3.5 | 仕様書の指示に厳密に従う |
| Claude APIモデル名の間違い | v3.5-v3.6 | 本仕様書の値をそのまま使用 |
| Messages API v2形式の誤り | v3.7 | API仕様を正確に理解する |
| conftest.py重複作成 | v3.4 | 既存ファイルを確認してから作成 |

### 絶対禁止事項（MUST NOT）

```
❌ 禁止: APIエンドポイントを推測で作成
   → 仕様書の「API一覧」セクションを参照すること

❌ 禁止: 型定義を独自に変更
   → 仕様書の型定義をそのままコピーすること

❌ 禁止: 環境変数をハードコード
   → import.meta.env.VITE_* を使用すること

❌ 禁止: 既存のコンポーネントを変更
   → 新規ファイルのみ追加すること

❌ 禁止: 仕様書にない機能を追加
   → アニメーション、バリデーション等の追加禁止

❌ 禁止: any型の使用
   → 明示的な型定義を使用すること
```

---

## 1. 作業開始前の確認事項

### 1.1 環境確認コマンド

```bash
# 1. フロントエンドディレクトリに移動
cd frontend

# 2. 依存関係インストール確認
npm install

# 3. 開発サーバー起動確認
npm run dev

# 4. 既存ページが正常動作することを確認
#    - http://localhost:5173/messages
#    - http://localhost:5173/intents
#    - http://localhost:5173/specifications
```

### 1.2 バックエンドAPI確認

```bash
# Dashboard Backend確認（基本CRUD）
curl http://localhost:8000/api/messages

# Bridge API確認（高度機能）
# ※ 矛盾検出APIはDBプール依存のため、エンドポイント存在確認のみ
curl -I http://localhost:8000/api/v1/contradiction/pending
```

### 1.3 既存ファイル構造確認

```bash
# 現在のフロントエンド構造を確認
ls -la frontend/src/
ls -la frontend/src/components/
ls -la frontend/src/types/
ls -la frontend/src/api/
```

**重要**: 既存ファイルは変更しない。新規ファイルのみ追加。

---

## 2. Phase 1: 矛盾検出UI実装手順

### Step 1: 型定義ファイル作成

**ファイル**: `frontend/src/types/contradiction.ts`

```bash
# ディレクトリ確認（typesディレクトリが存在するか）
ls frontend/src/types/

# ファイル作成
touch frontend/src/types/contradiction.ts
```

**内容**: 仕様書「2.1 Contradiction型」のコードをそのままコピー

```typescript
// frontend/src/types/contradiction.ts
// 以下を仕様書からそのままコピー

export type ContradictionType =
  | 'tech_stack'
  | 'policy_shift'
  | 'duplicate'
  | 'dogma';

export type ResolutionStatus = 'pending' | 'resolved' | 'dismissed';

export type ResolutionAction = 'policy_change' | 'mistake' | 'coexist';

export interface Contradiction {
  id: string;
  user_id: string;
  new_intent_id: string;
  new_intent_content: string;
  conflicting_intent_id: string | null;
  conflicting_intent_content: string | null;
  contradiction_type: ContradictionType;
  confidence_score: number;
  detected_at: string;
  details: Record<string, unknown>;
  resolution_status: ResolutionStatus;
  resolution_action: ResolutionAction | null;
  resolution_rationale: string | null;
  resolved_at: string | null;
}

export interface CheckContradictionRequest {
  user_id: string;
  intent_id: string;
  intent_content: string;
}

export interface ResolveContradictionRequest {
  resolution_action: ResolutionAction;
  resolution_rationale: string;
  resolved_by: string;
}

export interface ContradictionListResponse {
  contradictions: Contradiction[];
  total: number;
}
```

### Step 2: API関数ファイル作成

**ファイル**: `frontend/src/api/contradiction.ts`

```bash
touch frontend/src/api/contradiction.ts
```

**内容**: 仕様書「3.2 API呼び出し関数」のコードをそのままコピー

```typescript
// frontend/src/api/contradiction.ts

import axios from 'axios';
import type {
  ContradictionListResponse,
  CheckContradictionRequest,
  ResolveContradictionRequest
} from '../types/contradiction';

const BRIDGE_API_URL = import.meta.env.VITE_BRIDGE_API_URL || 'http://localhost:8000';

export async function getPendingContradictions(
  userId: string
): Promise<ContradictionListResponse> {
  const response = await axios.get<ContradictionListResponse>(
    `${BRIDGE_API_URL}/api/v1/contradiction/pending`,
    { params: { user_id: userId } }
  );
  return response.data;
}

export async function checkIntentContradiction(
  request: CheckContradictionRequest
): Promise<ContradictionListResponse> {
  const response = await axios.post<ContradictionListResponse>(
    `${BRIDGE_API_URL}/api/v1/contradiction/check`,
    request
  );
  return response.data;
}

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

### Step 3: コンポーネントディレクトリ作成

```bash
mkdir -p frontend/src/components/contradiction
touch frontend/src/components/contradiction/ContradictionDashboard.tsx
touch frontend/src/components/contradiction/ContradictionItem.tsx
```

### Step 4: ContradictionItem.tsx 実装

```typescript
// frontend/src/components/contradiction/ContradictionItem.tsx

import React from 'react';
import type { Contradiction } from '../../types/contradiction';

interface ContradictionItemProps {
  contradiction: Contradiction;
  onResolve?: (id: string) => void;
}

// 矛盾タイプに応じた色を返す（仕様書の色指定に厳密に従う）
const getTypeStyles = (type: string): string => {
  switch (type) {
    case 'tech_stack':
      return 'border-red-500 bg-red-50';
    case 'policy_shift':
      return 'border-orange-500 bg-orange-50';
    case 'duplicate':
      return 'border-yellow-500 bg-yellow-50';
    case 'dogma':
      return 'border-blue-500 bg-blue-50';
    default:
      return 'border-gray-500 bg-gray-50';
  }
};

const getTypeLabel = (type: string): string => {
  switch (type) {
    case 'tech_stack': return '技術スタック矛盾';
    case 'policy_shift': return 'ポリシー転換';
    case 'duplicate': return '重複作業';
    case 'dogma': return 'ドグマ検出';
    default: return type;
  }
};

const ContradictionItem: React.FC<ContradictionItemProps> = ({
  contradiction,
  onResolve
}) => {
  return (
    <div className={`p-4 border-2 rounded-lg ${getTypeStyles(contradiction.contradiction_type)}`}>
      {/* ヘッダー */}
      <div className="flex justify-between items-start mb-2">
        <span className="text-sm font-semibold">
          {getTypeLabel(contradiction.contradiction_type)}
        </span>
        <span className="text-xs text-gray-500">
          {new Date(contradiction.detected_at).toLocaleDateString('ja-JP')}
        </span>
      </div>

      {/* 内容 */}
      <p className="text-sm mb-2 text-gray-800">
        {contradiction.new_intent_content}
      </p>

      {/* 信頼度 */}
      <div className="mb-2">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>信頼度</span>
          <span>{(contradiction.confidence_score * 100).toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded">
          <div
            className="h-2 bg-blue-500 rounded"
            style={{ width: `${contradiction.confidence_score * 100}%` }}
          />
        </div>
      </div>

      {/* ステータス */}
      <div className="flex justify-between items-center">
        <span className={`text-xs px-2 py-1 rounded ${
          contradiction.resolution_status === 'resolved'
            ? 'bg-green-100 text-green-800'
            : contradiction.resolution_status === 'dismissed'
            ? 'bg-gray-100 text-gray-800'
            : 'bg-red-100 text-red-800'
        }`}>
          {contradiction.resolution_status === 'resolved' ? '解決済み' :
           contradiction.resolution_status === 'dismissed' ? '却下' : '未解決'}
        </span>

        {contradiction.resolution_status === 'pending' && onResolve && (
          <button
            onClick={() => onResolve(contradiction.id)}
            className="text-xs bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
          >
            解決
          </button>
        )}
      </div>
    </div>
  );
};

export default ContradictionItem;
```

### Step 5: ContradictionDashboard.tsx 実装

```typescript
// frontend/src/components/contradiction/ContradictionDashboard.tsx

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPendingContradictions } from '../../api/contradiction';
import ContradictionItem from './ContradictionItem';

const ContradictionDashboard: React.FC = () => {
  // TODO: 実際のユーザーIDを取得する仕組みが必要
  const userId = 'default';

  const { data, isLoading, error } = useQuery({
    queryKey: ['contradictions', userId],
    queryFn: () => getPendingContradictions(userId),
    refetchInterval: 5000, // 5秒間隔で更新（Phase 2でWebSocket化予定）
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">読み込み中...</div>
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

  const contradictions = data?.contradictions ?? [];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">矛盾検出ダッシュボード</h1>

      {contradictions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {contradictions.map((contradiction) => (
            <ContradictionItem
              key={contradiction.id}
              contradiction={contradiction}
            />
          ))}
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          現在、検出された矛盾はありません。
        </div>
      )}
    </div>
  );
};

export default ContradictionDashboard;
```

### Step 6: ルーティング追加

**ファイル**: `frontend/src/App.tsx`（既存ファイルに追加）

```typescript
// 1. importセクションに追加
import ContradictionDashboard from './components/contradiction/ContradictionDashboard';

// 2. <Routes>内に追加（既存のRouteの後ろ）
<Route path="/contradictions" element={<ContradictionDashboard />} />
```

### Step 7: ナビゲーション追加

既存のナビゲーションコンポーネント（Sidebar.tsx等）に追加：

```typescript
// ナビゲーションリンクに追加
<Link
  to="/contradictions"
  className={`flex items-center px-4 py-2 text-sm ${
    location.pathname === '/contradictions'
      ? 'bg-gray-700 text-white'
      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
  }`}
>
  矛盾検出
</Link>
```

---

## 3. Phase 1 完了確認チェックリスト

### ファイル作成確認

```bash
# 以下のファイルが存在することを確認
ls frontend/src/types/contradiction.ts
ls frontend/src/api/contradiction.ts
ls frontend/src/components/contradiction/ContradictionDashboard.tsx
ls frontend/src/components/contradiction/ContradictionItem.tsx
```

- [ ] `src/types/contradiction.ts` 作成済み
- [ ] `src/api/contradiction.ts` 作成済み
- [ ] `src/components/contradiction/ContradictionDashboard.tsx` 作成済み
- [ ] `src/components/contradiction/ContradictionItem.tsx` 作成済み

### 動作確認

```bash
# TypeScriptコンパイルエラーがないことを確認
npm run build

# 開発サーバーで動作確認
npm run dev
```

- [ ] `npm run build` がエラーなく完了
- [ ] `http://localhost:5173/contradictions` にアクセス可能
- [ ] ナビゲーションから遷移可能
- [ ] 既存ページ（messages, intents, specifications）が正常動作

### UI確認

- [ ] グリッドレイアウト（1/2/3列レスポンシブ）表示
- [ ] 矛盾タイプごとの色分け表示
- [ ] 信頼度バー表示
- [ ] 解決ステータス表示
- [ ] エラー時のメッセージ表示
- [ ] データなし時のメッセージ表示

---

## 4. 困った時の対処法

### TypeScriptエラーが発生した場合

```bash
# 型定義の確認
cat frontend/src/types/contradiction.ts

# import文のパス確認
# 相対パスが正しいか確認
```

### API接続エラーが発生した場合

```bash
# 1. バックエンド起動確認
curl http://localhost:8000/health

# 2. APIエンドポイント確認
curl http://localhost:8000/api/v1/contradiction/pending

# 3. 環境変数確認
cat frontend/.env.local
```

### 既存機能が壊れた場合

```bash
# git diffで変更箇所を確認
git diff frontend/src/App.tsx

# 既存ファイルへの変更は最小限（import追加とRoute追加のみ）であることを確認
```

---

## 5. Phase 1完了後の報告事項

以下の内容を報告すること：

1. **作成ファイル一覧**
   - ファイルパスとファイルサイズ

2. **動作確認結果**
   - `npm run build` 結果
   - ブラウザでの動作確認結果

3. **スクリーンショット**
   - 矛盾検出ダッシュボード画面
   - エラー状態画面（APIエラー時）
   - データなし状態画面

4. **発見した問題**
   - 仕様書との差異
   - 追加で必要な対応

---

## 6. Phase 2への移行条件

**Phase 1が完全に動作することを確認してからPhase 2に進むこと**

Phase 2開始条件：
- [ ] Phase 1チェックリスト全項目完了
- [ ] 既存機能に影響なし
- [ ] `npm run build` エラーなし

---

**作成者**: Claude Code
**レビュー日**: 2025-11-24
**対象**: Kiro（Claude Sonnet 4.5）
