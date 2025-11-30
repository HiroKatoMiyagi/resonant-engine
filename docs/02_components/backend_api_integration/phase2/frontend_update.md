# Frontend更新 作業指示書

## 概要

**目的**: Backend API統合完了を受けてFrontend仕様書とコードを更新する
**前提**: Phase 2完了、統合テスト合格
**期間**: 30分-1時間
**対象**: Frontend仕様書の修正、APIクライアントの確認

---

## 📋 更新が必要な理由

### 現状の問題

Frontend仕様書（`docs/02_components/frontend/architecture/frontend_core_features_spec.md`）に以下の **誤った記載** が存在:

```markdown
## 0. バックエンドAPI構成（重要）

### 2つのバックエンドが存在する

1. Dashboard Backend (backend/app/)
   - 基本CRUD操作
   - ポート: 8000

2. Bridge API (bridge/api/)
   - 高度機能（矛盾検出等）
   - ポート: 8000
```

**実際**:
- Backend API（backend/app/）が **全機能を統合**
- Bridge APIは独立サービスとして存在しない
- 全エンドポイントがポート8000で提供される

---

## Phase 1: Frontend仕様書の修正（15分）

### Step 1.1: frontend_core_features_spec.md修正

**ファイル**: `/Users/zero/Projects/resonant-engine/docs/02_components/frontend/architecture/frontend_core_features_spec.md`

#### 修正箇所1: セクション0の完全書き換え

**Before（削除）**:
```markdown
## 0. バックエンドAPI構成（重要）

### 2つのバックエンドが存在する

Resonant Engineのバックエンドは、**2つの独立したAPIサーバー**で構成されています。

1. **Dashboard Backend** (`backend/app/`)
   - 基本的なCRUD操作
   - ポート: 8000
   - エンドポイント: `/api/messages`, `/api/intents`, `/api/specifications`, `/api/notifications`

2. **Bridge API** (`bridge/api/`)
   - 高度機能（矛盾検出、再評価、Choice Preservation等）
   - ポート: 8000（同じポート）
   - エンドポイント: `/api/v1/contradiction`, `/api/v1/intent/reeval`, `/api/v1/memory`

### APIエンドポイント構成

```plaintext
Frontend
  ├─ Dashboard Backend (http://localhost:8000)
  │   ├─ /api/messages
  │   ├─ /api/intents
  │   ├─ /api/specifications
  │   └─ /api/notifications
  │
  └─ Bridge API (http://localhost:8000)
      ├─ /api/v1/contradiction/*
      ├─ /api/v1/intent/reeval
      ├─ /api/v1/memory/choice-points/*
      ├─ /api/v1/memory/lifecycle/*
      └─ /api/v1/dashboard/*
```

**重要**: 両方のAPIが同じポート8000を使用していますが、URLプレフィックスで区別されます。
```

**After（新規作成）**:
```markdown
## 0. バックエンドAPI構成

### 統一されたBackend API

Resonant EngineのバックエンドAPIは、**単一のFastAPIアプリケーション**で全機能を提供します。

**Backend API** (`backend/app/`)
- ポート: 8000
- すべての機能が統合されています

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
- `GET /api/messages` - メッセージ一覧
- `POST /api/messages` - メッセージ作成
- `GET /api/intents` - Intent一覧
- `POST /api/intents` - Intent作成
- `GET /api/specifications` - 仕様書一覧
- `POST /api/specifications` - 仕様書作成
- `GET /api/notifications` - 通知一覧

#### Contradiction Detection (統合済み)
- `GET /api/v1/contradiction/pending` - 未解決矛盾取得
- `POST /api/v1/contradiction/check` - Intent矛盾チェック
- `PUT /api/v1/contradiction/{id}/resolve` - 矛盾解決

#### Re-evaluation (統合済み)
- `POST /api/v1/intent/reeval` - Intent再評価

#### Choice Preservation (統合済み)
- `GET /api/v1/memory/choice-points/pending` - 未決定選択肢取得
- `POST /api/v1/memory/choice-points/` - 選択肢作成
- `PUT /api/v1/memory/choice-points/{id}/decide` - 選択決定
- `GET /api/v1/memory/choice-points/search` - 選択肢検索

#### Memory Lifecycle (統合済み)
- `GET /api/v1/memory/lifecycle/status` - メモリステータス取得
- `POST /api/v1/memory/lifecycle/compress` - メモリ圧縮
- `DELETE /api/v1/memory/lifecycle/expired` - 期限切れクリーンアップ

#### Dashboard Analytics (統合済み)
- `GET /api/v1/dashboard/overview` - システム概要
- `GET /api/v1/dashboard/timeline` - タイムライン
- `GET /api/v1/dashboard/corrections` - 修正履歴

#### WebSocket (既存)
- `WS /ws/intents` - Intent更新リアルタイム通知
```

---

#### 修正箇所2: Sprint 14-15の記載更新

**Before（削除）**:
```markdown
### Sprint 14での実装

**2つのAPI統合**:
```typescript
// 環境変数
VITE_API_URL=http://localhost:8000              // Dashboard Backend
VITE_BRIDGE_API_URL=http://localhost:8000       // Bridge API
```

**After（新規）**:
```markdown
### Sprint 14での実装

**統一APIエンドポイント**:
```typescript
// 環境変数
VITE_API_URL=http://localhost:8000  // Backend API（全機能）
```

**APIクライアント**:
```typescript
// frontend/src/api/client.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 全エンドポイントが同じベースURL
export const apiClient = {
  // 基本CRUD
  messages: `${API_BASE_URL}/api/messages`,
  intents: `${API_BASE_URL}/api/intents`,
  
  // 高度機能（同じベースURL）
  contradictions: `${API_BASE_URL}/api/v1/contradiction`,
  reeval: `${API_BASE_URL}/api/v1/intent/reeval`,
  choicePoints: `${API_BASE_URL}/api/v1/memory/choice-points`,
  
  // WebSocket（同じベースURL）
  websocket: `ws://${API_BASE_URL.replace('http://', '')}/ws/intents`
};
```
```

---

### Step 1.2: 修正の適用

```bash
# バックアップ作成
cp /Users/zero/Projects/resonant-engine/docs/02_components/frontend/architecture/frontend_core_features_spec.md \
   /Users/zero/Projects/resonant-engine/docs/02_components/frontend/architecture/frontend_core_features_spec.md.backup

# エディタで修正
# 上記のBefore→After修正を適用
```

**確認**:
```bash
# "2つのバックエンド"という記載が残っていないか確認
grep -n "2つのバックエンド" /Users/zero/Projects/resonant-engine/docs/02_components/frontend/architecture/frontend_core_features_spec.md
# 期待: 何も表示されない

# "Bridge API"という独立サービスの記載が残っていないか確認
grep -n "Bridge API.*独立" /Users/zero/Projects/resonant-engine/docs/02_components/frontend/architecture/frontend_core_features_spec.md
# 期待: 何も表示されない
```

---

## Phase 2: APIクライアントコードの確認（15分）

### Step 2.1: client.ts確認

**ファイル**: `frontend/src/api/client.ts`

**確認ポイント**:
1. `VITE_BRIDGE_API_URL`環境変数を使用していないか
2. すべてのエンドポイントが同じベースURLを使用しているか

**期待されるコード**:
```typescript
// frontend/src/api/client.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ✅ 正しい: すべて同じベースURL
export const API_ENDPOINTS = {
  // 基本CRUD
  messages: `${API_BASE_URL}/api/messages`,
  intents: `${API_BASE_URL}/api/intents`,
  specifications: `${API_BASE_URL}/api/specifications`,
  notifications: `${API_BASE_URL}/api/notifications`,
  
  // 高度機能（同じベースURL）
  contradictionsPending: `${API_BASE_URL}/api/v1/contradiction/pending`,
  contradictionsCheck: `${API_BASE_URL}/api/v1/contradiction/check`,
  reevalIntent: `${API_BASE_URL}/api/v1/intent/reeval`,
  choicePointsPending: `${API_BASE_URL}/api/v1/memory/choice-points/pending`,
  
  // WebSocket
  websocket: `ws://${API_BASE_URL.replace('http://', '')}/ws/intents`
};
```

**❌ 誤ったコード（もし存在したら修正）**:
```typescript
// ❌ 間違い: 2つのベースURLを使用
const DASHBOARD_API_URL = import.meta.env.VITE_API_URL;
const BRIDGE_API_URL = import.meta.env.VITE_BRIDGE_API_URL;  // ← 削除

export const API_ENDPOINTS = {
  messages: `${DASHBOARD_API_URL}/api/messages`,
  contradictions: `${BRIDGE_API_URL}/api/v1/contradiction/pending`,  // ← 修正
};
```

---

### Step 2.2: .env確認

**ファイル**: `frontend/.env`

**期待される内容**:
```bash
VITE_API_URL=http://localhost:8000
```

**❌ 削除すべき記載（もし存在したら）**:
```bash
# ❌ 削除
VITE_BRIDGE_API_URL=http://localhost:8000
```

---

### Step 2.3: contradictions.tsxなどのコンポーネント確認

**ファイル**: `frontend/src/pages/Contradictions.tsx`（例）

**確認ポイント**:
- APIエンドポイントが正しく使用されているか

**期待されるコード**:
```typescript
import { API_ENDPOINTS } from '@/api/client';

const fetchContradictions = async () => {
  // ✅ 正しい: API_ENDPOINTSを使用
  const response = await fetch(`${API_ENDPOINTS.contradictionsPending}?user_id=${userId}`);
  const data = await response.json();
  setContradictions(data.contradictions);
};
```

---

## Phase 3: Swagger UI URLの更新（5分）

### Step 3.1: README更新

**ファイル**: `README.md`

**修正箇所**:

**Before**:
```markdown
## API Documentation

- Dashboard Backend: http://localhost:8000/docs
- Bridge API: http://localhost:8000/docs (同じURL、機能が統合されています)
```

**After**:
```markdown
## API Documentation

Backend API（全機能統合）: http://localhost:8000/docs
```

---

## Phase 4: 動作確認（10分）

### Step 4.1: Frontend起動

```bash
cd /Users/zero/Projects/resonant-engine/frontend
npm run dev
```

### Step 4.2: ブラウザで確認

```bash
open http://localhost:3000
```

**確認項目**:
1. メッセージ一覧が表示される
2. Intent一覧が表示される
3. 矛盾検出ページでデータが取得できる（プレースホルダーでない）
4. WebSocket接続が成功する

### Step 4.3: Network Tabで確認

ブラウザの開発者ツール → Networkタブ

**確認ポイント**:
- すべてのAPIリクエストが`http://localhost:8000`に向かっているか
- 2つの異なるURLへのリクエストが存在しないか

**期待**:
```
GET http://localhost:8000/api/messages
GET http://localhost:8000/api/intents
GET http://localhost:8000/api/v1/contradiction/pending?user_id=...
GET http://localhost:8000/api/v1/dashboard/overview
```

---

## 完了基準

### ✅ Frontend更新完了判定

#### ドキュメント
- [ ] `frontend_core_features_spec.md`から「2つのバックエンド」記載削除
- [ ] セクション0が「統一されたBackend API」に更新
- [ ] エンドポイント一覧が正確（14エンドポイント）
- [ ] Sprint 14-15の記載が修正済み

#### コード
- [ ] `client.ts`がVITE_BRIDGE_API_URLを使用していない
- [ ] すべてのエンドポイントが同じベースURLを使用
- [ ] `.env`にBRIDGE_API_URL記載なし

#### 動作確認
- [ ] Frontend起動成功
- [ ] 全ページでデータ取得成功
- [ ] Network Tabで単一URL確認

---

## トラブルシューティング

### 問題1: 404 Not Found

**症状**:
```
GET http://localhost:8000/api/v1/contradiction/pending
404 Not Found
```

**原因**: Backend APIが起動していない、またはルーターが登録されていない

**解決策**:
```bash
# Backend API起動確認
curl http://localhost:8000/health

# ルーター確認
curl http://localhost:8000/docs
# contradictionタグが表示されるか確認
```

---

### 問題2: CORS Error

**症状**:
```
Access to fetch at 'http://localhost:8000/api/v1/contradiction/pending' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**原因**: Backend APIのCORS設定

**解決策**:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ← 確認
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## ドキュメント最終化

### 更新すべきドキュメント一覧

1. ✅ `frontend_core_features_spec.md` - 本作業で更新
2. ✅ `README.md` - 本作業で更新
3. 📝 `BACKEND_API_INTEGRATION_COMPLETE.md` - 統合完了を反映
   ```markdown
   ## 達成率
   - エンドポイント: 14/14 (100%) ✅
   - Frontend仕様書: 更新完了 ✅
   - 統一APIエンドポイント: 完了 ✅
   ```

4. 📝 `docs/reports/backend_api_integration_final_report.md` - Frontend更新を追記

---

## 次のステップ

Frontend更新完了後:

1. **最終動作確認**: E2Eテストを再実行
2. **デプロイ準備**: 本番環境構築準備
3. **ユーザー受け入れテスト**: 実際の利用シナリオでテスト

---

**作成日**: 2025-11-30
**想定時間**: 30分-1時間
**対象**: Frontend仕様書修正、APIクライアント確認
