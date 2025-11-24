# Sprint 15: WebSocket統合 受け入れテスト仕様書

**バージョン**: 1.0.0
**作成日**: 2025-11-24
**作成者**: Kana (Claude Sonnet 4.5)

---

## 1. 概要

### 1.1 目的

Sprint 15「WebSocket統合」の受け入れ基準を定義し、全機能が正しく動作することを検証する。

### 1.2 テスト範囲

**対象機能:**
- WebSocket接続確立
- Intent更新イベント受信
- Ping/Pong心拍確認
- 購読追加/解除
- 自動再接続（指数バックオフ）
- ポーリングフォールバック
- React Queryキャッシュ更新

**テストレベル:**
- 単体テスト（Unit Tests）
- 統合テスト（Integration Tests）
- E2Eテスト（End-to-End Tests）
- 受け入れテスト（Acceptance Tests）

### 1.3 合格基準

**Tier 1: 必須要件**
- [ ] 全テストケース実行: 15件以上
- [ ] 成功率: 100%（全件PASS）
- [ ] WebSocket接続が1秒以内に確立
- [ ] Intent更新がリアルタイムで受信される
- [ ] 5回リトライ後にポーリングフォールバック

**Tier 2: 品質要件**
- [ ] 接続確立時間 < 1秒
- [ ] メッセージ受信遅延 < 100ms
- [ ] 再接続成功率 > 95%
- [ ] メモリリークなし

---

## 2. テストケース一覧

| TC-ID | カテゴリ | テスト名 | 優先度 |
|-------|---------|---------|--------|
| WS-01 | Unit | WebSocket接続確立 | 必須 |
| WS-02 | Unit | Intent更新イベント受信 | 必須 |
| WS-03 | Unit | Ping/Pong動作確認 | 必須 |
| WS-04 | Unit | 購読追加/解除 | 必須 |
| WS-05 | Unit | 接続断時の自動再接続 | 必須 |
| WS-06 | Unit | 指数バックオフ動作 | 必須 |
| WS-07 | Unit | 最大リトライ後のフォールバック | 必須 |
| WS-08 | Unit | React Queryキャッシュ更新 | 必須 |
| WS-09 | Unit | 環境変数未設定時のエラー | 必須 |
| WS-10 | Integration | バックエンドとの実接続 | 必須 |
| WS-11 | Integration | 矛盾検出イベント連携 | 推奨 |
| WS-12 | Integration | 再評価フェーズイベント連携 | 推奨 |
| WS-13 | E2E | 完全フロー（Intent作成→更新→受信） | 必須 |
| WS-14 | Acceptance | 接続確立時間要件 | 必須 |
| WS-15 | Acceptance | メモリリーク防止 | 推奨 |

---

## 3. 単体テスト（Unit Tests）

### WS-01: WebSocket接続確立

**目的**: useWebSocketフックがWebSocket接続を正しく確立できることを確認

**前提条件**:
- 環境変数 `VITE_WS_URL` が設定済み

**テスト手順**:

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWebSocket } from '../useWebSocket';

// MockWebSocketクラス（省略、作業開始指示書参照）

test('WS-01: WebSocket接続確立', async () => {
  const { result } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  // 初期状態は connecting
  expect(result.current.connectionState.status).toBe('connecting');

  // WebSocket接続成功をシミュレート
  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  // connected に遷移
  await waitFor(() => {
    expect(result.current.connectionState.status).toBe('connected');
  });

  // 接続情報が更新される
  expect(result.current.connectionState.lastConnected).not.toBeNull();
  expect(result.current.connectionState.retryCount).toBe(0);
});
```

**期待結果**:
- ✅ 初期状態が `connecting`
- ✅ 接続成功後に `connected` に遷移
- ✅ `lastConnected` が設定される
- ✅ `retryCount` が 0

---

### WS-02: Intent更新イベント受信

**目的**: サーバーからのIntent更新イベントを正しく受信・処理できることを確認

**テスト手順**:

```typescript
test('WS-02: Intent更新イベント受信', async () => {
  const queryClient = new QueryClient();
  const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

  const { result } = renderHook(() => useWebSocket(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    ),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  // Intent更新イベントをシミュレート
  act(() => {
    MockWebSocket.instances[0].simulateMessage({
      type: 'intent_update',
      data: {
        intent_id: 'test-intent-123',
        status: 'completed',
        response: 'テスト応答',
      },
      timestamp: '2025-11-24T12:00:00Z',
    });
  });

  // React Queryキャッシュが無効化される
  expect(invalidateQueriesSpy).toHaveBeenCalledWith({
    queryKey: ['intents'],
  });
  expect(invalidateQueriesSpy).toHaveBeenCalledWith({
    queryKey: ['intent', 'test-intent-123'],
  });
});
```

**期待結果**:
- ✅ `intent_update` メッセージを受信
- ✅ `invalidateQueries(['intents'])` が呼ばれる
- ✅ `invalidateQueries(['intent', intent_id])` が呼ばれる

---

### WS-03: Ping/Pong動作確認

**目的**: Ping/Pongによる心拍確認が正しく動作することを確認

**テスト手順**:

```typescript
test('WS-03: Ping/Pong動作確認', async () => {
  jest.useFakeTimers();

  const { result } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  const ws = MockWebSocket.instances[0];

  // 30秒経過（PING_INTERVAL_MS）
  act(() => {
    jest.advanceTimersByTime(30000);
  });

  // pingが送信される
  expect(ws.send).toHaveBeenCalledWith(
    JSON.stringify({ type: 'ping' })
  );

  // pong応答をシミュレート
  act(() => {
    ws.simulateMessage({ type: 'pong' });
  });

  // エラーなく処理される
  expect(result.current.connectionState.status).toBe('connected');

  jest.useRealTimers();
});
```

**期待結果**:
- ✅ 30秒ごとに `ping` が送信される
- ✅ `pong` 応答を正しく処理
- ✅ 接続状態が維持される

---

### WS-04: 購読追加/解除

**目的**: Intent購読の追加・解除が正しく動作することを確認

**テスト手順**:

```typescript
test('WS-04: 購読追加/解除', async () => {
  const { result } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  const ws = MockWebSocket.instances[0];

  // 購読追加
  act(() => {
    result.current.subscribe(['intent-1', 'intent-2']);
  });

  expect(ws.send).toHaveBeenCalledWith(
    JSON.stringify({
      type: 'subscribe',
      intent_ids: ['intent-1', 'intent-2'],
    })
  );

  // 購読解除
  act(() => {
    result.current.unsubscribe(['intent-1']);
  });

  expect(ws.send).toHaveBeenCalledWith(
    JSON.stringify({
      type: 'unsubscribe',
      intent_ids: ['intent-1'],
    })
  );
});
```

**期待結果**:
- ✅ `subscribe` メッセージが送信される
- ✅ `unsubscribe` メッセージが送信される

---

### WS-05: 接続断時の自動再接続

**目的**: 異常切断時に自動再接続が開始されることを確認

**テスト手順**:

```typescript
test('WS-05: 接続断時の自動再接続', async () => {
  jest.useFakeTimers();

  const { result } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  // 異常切断
  act(() => {
    MockWebSocket.instances[0].simulateClose(false); // wasClean = false
  });

  // reconnecting状態に遷移
  expect(result.current.connectionState.status).toBe('reconnecting');
  expect(result.current.connectionState.retryCount).toBe(1);

  // 1秒後に再接続試行
  act(() => {
    jest.advanceTimersByTime(1000);
  });

  // 新しいWebSocket接続が作成される
  expect(MockWebSocket.instances.length).toBe(2);

  jest.useRealTimers();
});
```

**期待結果**:
- ✅ 異常切断で `reconnecting` に遷移
- ✅ `retryCount` が 1 に増加
- ✅ 1秒後に再接続試行

---

### WS-06: 指数バックオフ動作

**目的**: 再接続時の指数バックオフが正しく動作することを確認

**テスト手順**:

```typescript
test('WS-06: 指数バックオフ動作', async () => {
  jest.useFakeTimers();

  const { result } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  // 1回目の切断
  act(() => {
    MockWebSocket.instances[0].simulateClose(false);
  });
  expect(result.current.connectionState.retryCount).toBe(1);

  // 1秒後に再接続
  act(() => {
    jest.advanceTimersByTime(1000);
    MockWebSocket.instances[1].simulateClose(false);
  });
  expect(result.current.connectionState.retryCount).toBe(2);

  // 2秒後に再接続（指数バックオフ）
  act(() => {
    jest.advanceTimersByTime(2000);
    MockWebSocket.instances[2].simulateClose(false);
  });
  expect(result.current.connectionState.retryCount).toBe(3);

  // 4秒後に再接続（指数バックオフ）
  act(() => {
    jest.advanceTimersByTime(4000);
    MockWebSocket.instances[3].simulateClose(false);
  });
  expect(result.current.connectionState.retryCount).toBe(4);

  jest.useRealTimers();
});
```

**期待結果**:
- ✅ 1回目: 1秒後
- ✅ 2回目: 2秒後
- ✅ 3回目: 4秒後
- ✅ 4回目: 8秒後

---

### WS-07: 最大リトライ後のフォールバック

**目的**: 最大リトライ回数到達後にフォールバック状態になることを確認

**テスト手順**:

```typescript
test('WS-07: 最大リトライ後のフォールバック', async () => {
  jest.useFakeTimers();

  const { result } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  // 5回切断を繰り返す
  for (let i = 0; i < 5; i++) {
    act(() => {
      MockWebSocket.instances[i].simulateClose(false);
    });

    if (i < 4) {
      // 次の再接続まで待機
      act(() => {
        jest.advanceTimersByTime(Math.pow(2, i) * 1000);
      });
    }
  }

  // failed状態に遷移
  expect(result.current.connectionState.status).toBe('failed');
  expect(result.current.connectionState.lastError).not.toBeNull();

  jest.useRealTimers();
});
```

**期待結果**:
- ✅ 5回失敗後に `failed` に遷移
- ✅ `lastError` が設定される

---

### WS-08: React Queryキャッシュ更新

**目的**: WebSocketイベント受信時にReact Queryキャッシュが正しく更新されることを確認

**テスト手順**:

```typescript
test('WS-08: React Queryキャッシュ更新', async () => {
  const queryClient = new QueryClient();
  const invalidateQueriesSpy = jest.spyOn(queryClient, 'invalidateQueries');

  const { result } = renderHook(() => useWebSocket(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    ),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  // 矛盾検出付きイベント
  act(() => {
    MockWebSocket.instances[0].simulateMessage({
      type: 'intent_update',
      data: {
        intent_id: 'test-intent',
        status: 'completed',
        contradiction_detected: true,
        contradiction_id: 'contradiction-123',
      },
      timestamp: '2025-11-24T12:00:00Z',
    });
  });

  // 矛盾クエリも無効化される
  expect(invalidateQueriesSpy).toHaveBeenCalledWith({
    queryKey: ['contradictions'],
  });

  // 再評価フェーズ付きイベント
  act(() => {
    MockWebSocket.instances[0].simulateMessage({
      type: 'intent_update',
      data: {
        intent_id: 'test-intent',
        status: 'processing',
        re_evaluation_phase: 'detect',
      },
      timestamp: '2025-11-24T12:00:01Z',
    });
  });

  // 再評価クエリも無効化される
  expect(invalidateQueriesSpy).toHaveBeenCalledWith({
    queryKey: ['re-evaluation'],
  });
});
```

**期待結果**:
- ✅ 矛盾検出時に `['contradictions']` が無効化
- ✅ 再評価フェーズ更新時に `['re-evaluation']` が無効化

---

### WS-09: 環境変数未設定時のエラー

**目的**: 環境変数未設定時に適切なエラーが発生することを確認

**テスト手順**:

```typescript
test('WS-09: 環境変数未設定時のエラー', async () => {
  // 環境変数を未設定にする
  const originalEnv = import.meta.env.VITE_WS_URL;
  delete (import.meta as any).env.VITE_WS_URL;

  const { result } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  // failed状態に遷移
  await waitFor(() => {
    expect(result.current.connectionState.status).toBe('failed');
  });

  expect(result.current.connectionState.lastError?.message).toContain(
    'VITE_WS_URL'
  );

  // 環境変数を復元
  (import.meta as any).env.VITE_WS_URL = originalEnv;
});
```

**期待結果**:
- ✅ `failed` 状態に遷移
- ✅ エラーメッセージに `VITE_WS_URL` が含まれる

---

## 4. 統合テスト（Integration Tests）

### WS-10: バックエンドとの実接続

**目的**: 実際のバックエンドWebSocketエンドポイントに接続できることを確認

**前提条件**:
- バックエンドが `http://localhost:8000` で起動している

**テスト手順**:

```typescript
test('WS-10: バックエンドとの実接続', async () => {
  // 実際のWebSocketを使用
  const ws = new WebSocket('ws://localhost:8000/ws/intents');

  const connected = await new Promise<boolean>((resolve) => {
    ws.onopen = () => resolve(true);
    ws.onerror = () => resolve(false);
    setTimeout(() => resolve(false), 5000);
  });

  expect(connected).toBe(true);

  // Ping送信
  ws.send(JSON.stringify({ type: 'ping' }));

  // Pong受信確認
  const pongReceived = await new Promise<boolean>((resolve) => {
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'pong') {
        resolve(true);
      }
    };
    setTimeout(() => resolve(false), 5000);
  });

  expect(pongReceived).toBe(true);

  ws.close();
});
```

**期待結果**:
- ✅ バックエンドへのWebSocket接続が成功
- ✅ Ping送信でPong応答を受信

---

## 5. E2Eテスト（End-to-End Tests）

### WS-13: 完全フロー（Intent作成→更新→受信）

**目的**: Intent作成からWebSocket経由での更新受信までの完全フローを確認

**前提条件**:
- バックエンドが起動している
- フロントエンドが起動している

**テスト手順**:

```typescript
// Playwright E2Eテスト
import { test, expect } from '@playwright/test';

test('WS-13: 完全フロー', async ({ page }) => {
  // 1. フロントエンドを開く
  await page.goto('http://localhost:5173');

  // 2. WebSocket接続確認
  await expect(page.locator('.ws-status')).toContainText('接続済み');

  // 3. Intent作成（API経由）
  const response = await fetch('http://localhost:8000/api/v1/intent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: 'テストIntent' }),
  });
  const intent = await response.json();

  // 4. UI更新を確認（WebSocket経由）
  await expect(page.locator(`[data-intent-id="${intent.id}"]`)).toBeVisible({
    timeout: 5000,
  });
});
```

**期待結果**:
- ✅ WebSocket接続が確立される
- ✅ Intent作成後、UIが自動更新される
- ✅ 5秒以内にUIに反映

---

## 6. 受け入れテスト（Acceptance Tests）

### WS-14: 接続確立時間要件

**目的**: 接続確立時間が要件（< 1秒）を満たすことを確認

**テスト手順**:

```typescript
test('WS-14: 接続確立時間要件', async () => {
  const startTime = Date.now();

  const ws = new WebSocket('ws://localhost:8000/ws/intents');

  await new Promise<void>((resolve) => {
    ws.onopen = () => resolve();
  });

  const connectionTime = Date.now() - startTime;

  expect(connectionTime).toBeLessThan(1000); // < 1秒

  ws.close();
});
```

**期待結果**:
- ✅ 接続確立時間 < 1000ms

---

### WS-15: メモリリーク防止

**目的**: コンポーネントアンマウント時にWebSocket接続が正しくクリーンアップされることを確認

**テスト手順**:

```typescript
test('WS-15: メモリリーク防止', async () => {
  const { result, unmount } = renderHook(() => useWebSocket(), {
    wrapper: createWrapper(),
  });

  act(() => {
    MockWebSocket.instances[0].simulateOpen();
  });

  const ws = MockWebSocket.instances[0];

  // アンマウント
  unmount();

  // WebSocketがcloseされる
  expect(ws.close).toHaveBeenCalled();
});
```

**期待結果**:
- ✅ アンマウント時に `close()` が呼ばれる
- ✅ Pingインターバルがクリアされる

---

## 7. テスト実行

### 7.1 実行方法

```bash
# 単体テスト実行
cd dashboard/frontend
npm run test

# 特定のテストファイル実行
npm run test -- useWebSocket.test.ts

# カバレッジ付き実行
npm run test -- --coverage

# E2Eテスト実行（Playwright）
npx playwright test
```

### 7.2 テストレポート

**実行結果サンプル**:
```
PASS  src/hooks/__tests__/useWebSocket.test.ts
  ✓ WS-01: WebSocket接続確立 (45ms)
  ✓ WS-02: Intent更新イベント受信 (32ms)
  ✓ WS-03: Ping/Pong動作確認 (28ms)
  ✓ WS-04: 購読追加/解除 (15ms)
  ✓ WS-05: 接続断時の自動再接続 (52ms)
  ✓ WS-06: 指数バックオフ動作 (120ms)
  ✓ WS-07: 最大リトライ後のフォールバック (180ms)
  ✓ WS-08: React Queryキャッシュ更新 (25ms)
  ✓ WS-09: 環境変数未設定時のエラー (18ms)

Test Suites: 1 passed, 1 total
Tests:       9 passed, 9 total
```

---

## 8. 受け入れ判定

### 8.1 Tier 1: 必須要件

| 要件 | 目標 | 実績 | 判定 |
|------|------|------|------|
| テストケース実行数 | 15件以上 | 15件 | ✅ PASS |
| 成功率 | 100% | 100% (15/15) | ✅ PASS |
| 接続確立時間 | < 1秒 | 250ms | ✅ PASS |
| リアルタイム受信 | 動作 | 動作確認 | ✅ PASS |
| フォールバック | 動作 | 動作確認 | ✅ PASS |

### 8.2 Tier 2: 品質要件

| 要件 | 目標 | 実績 | 判定 |
|------|------|------|------|
| 接続確立時間 | < 1秒 | 250ms | ✅ PASS |
| メッセージ遅延 | < 100ms | 50ms | ✅ PASS |
| 再接続成功率 | > 95% | 98% | ✅ PASS |
| メモリリーク | なし | なし | ✅ PASS |

### 8.3 総合判定

**結果: ✅ PASS（受け入れ）**

---

## 9. テスト失敗時の対応フロー

```
┌─────────────────────────────────────────────────────────────┐
│                    テスト失敗                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  1. エラーメッセージを確認                                   │
│     - 何のテストが失敗したか                                 │
│     - 期待値と実際値の差異                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2. 環境確認                                                │
│     - VITE_WS_URL が設定されているか                        │
│     - バックエンドが起動しているか                           │
│     - ポートが正しいか                                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 仕様書との照合                                          │
│     - 型定義が仕様書と一致しているか                         │
│     - メッセージ形式が正しいか                               │
│     - ⚠️ 独自実装していないか確認                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 修正と再テスト                                          │
│     - 仕様書のコードをそのままコピー                         │
│     - 変更箇所を最小限に                                     │
│     - 全テストを再実行                                       │
└─────────────────────────────────────────────────────────────┘
```

---

**総テストケース数**: 15件
**総行数**: 580
