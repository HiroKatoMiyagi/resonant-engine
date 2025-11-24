# Sprint 15: WebSocket統合 作業開始指示書

**バージョン**: 1.0.0
**作成日**: 2025-11-24
**対象実装者**: Kiro / Claude Code CLI / Google Antigravity

---

## 0. ⚠️ 実装者への重要警告

### 絶対禁止事項（総合テストv3.1-v3.7の教訓）

| 過去の問題 | 発生Sprint | 対策 |
|-----------|-----------|------|
| パスワード・URLのハードコード | v3.4 | 環境変数 `VITE_WS_URL` を必ず使用 |
| 独自判断でのテストスキップ | v3.5 | 本指示書のテスト項目を全て実行 |
| API名・型名の独自変更 | v3.5-v3.6 | 仕様書の型定義をそのままコピー |
| Messages API v2形式の誤り | v3.7 | API仕様を正確に理解してから実装 |

### この指示書の使い方

1. **Day 1〜Day 5の順番通りに実装**
2. **各Dayの成功基準を全て満たしてから次へ**
3. **コードは仕様書からコピー**（独自実装禁止）
4. **不明点は実装前に確認**（独自判断禁止）

---

## 概要

**Sprint**: 15
**タイトル**: WebSocket統合
**目標**: 5秒ポーリングをWebSocketリアルタイム通信に置き換え

---

## Day 1: 型定義と環境設定

### 目標
- WebSocket関連の型定義を追加
- 環境変数設定
- Vite設定更新

### ステップ

#### 1.1 型定義ファイル作成

**⚠️ 以下のコードをそのままコピーすること（変更禁止）**

**ファイル**: `dashboard/frontend/src/types/websocket.ts`

```typescript
/**
 * WebSocket型定義
 * ⚠️ このファイルの内容を変更しないこと
 * バックエンドAPIと完全に一致している
 */

// ===== クライアント → サーバー メッセージ =====

export type ClientMessage =
  | { type: 'ping' }
  | { type: 'subscribe'; intent_ids: string[] }
  | { type: 'unsubscribe'; intent_ids: string[] };

// ===== サーバー → クライアント メッセージ =====

export type ServerMessage =
  | { type: 'pong' }
  | { type: 'intent_update'; data: IntentUpdatePayload; timestamp: string };

// ===== ペイロード型 =====

export interface IntentUpdatePayload {
  intent_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  content?: string;
  response?: string;
  contradiction_detected?: boolean;
  contradiction_id?: string;
  re_evaluation_phase?: ReEvaluationPhase;
}

export type ReEvaluationPhase =
  | 'detect'
  | 'isolate'
  | 'align'
  | 'decide'
  | 'apply'
  | 'log';

// ===== 接続状態 =====

export type ConnectionStatus =
  | 'disconnected'   // 未接続
  | 'connecting'     // 接続中
  | 'connected'      // 接続済み
  | 'reconnecting'   // 再接続中
  | 'failed';        // 接続失敗（リトライ上限到達）

export interface ConnectionState {
  status: ConnectionStatus;
  retryCount: number;
  lastConnected: Date | null;
  lastError: Error | null;
}

// ===== 定数 =====

export const WS_CONFIG = {
  MAX_RETRY_COUNT: 5,
  BASE_RETRY_DELAY_MS: 1000,
  PING_INTERVAL_MS: 30000,
} as const;
```

#### 1.2 環境変数設定

**ファイル**: `dashboard/frontend/.env.local`

```env
# WebSocket URL（開発環境）
# ⚠️ ハードコード禁止。この環境変数を必ず使用すること
VITE_WS_URL=ws://localhost:8000/ws/intents
```

**ファイル**: `dashboard/frontend/.env.production`

```env
# WebSocket URL（本番環境）
VITE_WS_URL=wss://api.resonant-engine.example.com/ws/intents
```

#### 1.3 Vite設定更新

**ファイル**: `dashboard/frontend/vite.config.ts`

以下を `server` セクションに追加:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // ⚠️ WebSocketプロキシ設定を追加
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

### Day 1 成功基準

- [ ] `src/types/websocket.ts` が作成され、型エラーなし
- [ ] `.env.local` に `VITE_WS_URL` が設定済み
- [ ] `vite.config.ts` にWebSocketプロキシ設定追加済み
- [ ] `npm run dev` でエラーなく起動

### Git Commit

```bash
git add dashboard/frontend/src/types/websocket.ts
git add dashboard/frontend/.env.local
git add dashboard/frontend/vite.config.ts
git commit -m "Add Sprint 15 Day 1: WebSocket type definitions and environment setup"
```

---

## Day 2: useWebSocket Hook実装

### 目標
- WebSocket接続管理フックを実装
- 自動再接続ロジック実装
- 指数バックオフ実装

### ステップ

#### 2.1 useWebSocket Hook作成

**⚠️ 以下のコードをそのままコピーすること（変更禁止）**

**ファイル**: `dashboard/frontend/src/hooks/useWebSocket.ts`

```typescript
/**
 * WebSocket接続管理Hook
 * ⚠️ このフックの実装を変更しないこと
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  ConnectionState,
  ServerMessage,
  IntentUpdatePayload,
  WS_CONFIG,
} from '../types/websocket';

export function useWebSocket(intentIds?: string[]) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
    retryCount: 0,
    lastConnected: null,
    lastError: null,
  });

  // WebSocket URL取得（環境変数から）
  const getWebSocketUrl = useCallback(() => {
    const baseUrl = import.meta.env.VITE_WS_URL;
    if (!baseUrl) {
      throw new Error('VITE_WS_URL environment variable is not set');
    }

    if (intentIds && intentIds.length > 0) {
      const params = intentIds.map(id => `intent_ids=${encodeURIComponent(id)}`).join('&');
      return `${baseUrl}?${params}`;
    }
    return baseUrl;
  }, [intentIds]);

  // Intent更新ハンドラ
  const handleIntentUpdate = useCallback((
    data: IntentUpdatePayload,
    _timestamp: string
  ) => {
    // React Queryキャッシュを無効化して再取得
    queryClient.invalidateQueries({ queryKey: ['intents'] });
    queryClient.invalidateQueries({ queryKey: ['intent', data.intent_id] });

    // 矛盾検出時
    if (data.contradiction_detected && data.contradiction_id) {
      queryClient.invalidateQueries({ queryKey: ['contradictions'] });
    }

    // 再評価フェーズ更新時
    if (data.re_evaluation_phase) {
      queryClient.invalidateQueries({ queryKey: ['re-evaluation'] });
    }
  }, [queryClient]);

  // メッセージハンドラ
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: ServerMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'pong':
          // Ping応答、接続確認OK
          break;

        case 'intent_update':
          handleIntentUpdate(message.data, message.timestamp);
          break;

        default:
          console.warn('Unknown WebSocket message type:', message);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [handleIntentUpdate]);

  // Pingインターバルクリア
  const clearPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // 再接続スケジュール（指数バックオフ）
  const scheduleReconnect = useCallback(() => {
    retryCountRef.current += 1;
    const delay = WS_CONFIG.BASE_RETRY_DELAY_MS * Math.pow(2, retryCountRef.current - 1);

    setConnectionState(prev => ({
      ...prev,
      status: 'reconnecting',
      retryCount: retryCountRef.current,
    }));

    console.log(`WebSocket reconnecting in ${delay}ms (attempt ${retryCountRef.current}/${WS_CONFIG.MAX_RETRY_COUNT})`);

    setTimeout(() => {
      connect();
    }, delay);
  }, []);

  // 接続開始
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState(prev => ({ ...prev, status: 'connecting' }));

    try {
      const url = getWebSocketUrl();
      console.log('WebSocket connecting to:', url);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        retryCountRef.current = 0;
        setConnectionState({
          status: 'connected',
          retryCount: 0,
          lastConnected: new Date(),
          lastError: null,
        });

        // Pingインターバル開始
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, WS_CONFIG.PING_INTERVAL_MS);
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        clearPingInterval();

        if (!event.wasClean && retryCountRef.current < WS_CONFIG.MAX_RETRY_COUNT) {
          scheduleReconnect();
        } else if (retryCountRef.current >= WS_CONFIG.MAX_RETRY_COUNT) {
          console.error('WebSocket max retry count reached, falling back to polling');
          setConnectionState(prev => ({
            ...prev,
            status: 'failed',
            lastError: new Error('Max retry count reached'),
          }));
        } else {
          setConnectionState(prev => ({ ...prev, status: 'disconnected' }));
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionState(prev => ({
          ...prev,
          lastError: new Error('WebSocket connection error'),
        }));
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionState(prev => ({
        ...prev,
        status: 'failed',
        lastError: error as Error,
      }));
    }
  }, [getWebSocketUrl, handleMessage, clearPingInterval, scheduleReconnect]);

  // 切断
  const disconnect = useCallback(() => {
    clearPingInterval();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionState(prev => ({ ...prev, status: 'disconnected' }));
  }, [clearPingInterval]);

  // 購読更新
  const subscribe = useCallback((newIntentIds: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        intent_ids: newIntentIds,
      }));
    }
  }, []);

  const unsubscribe = useCallback((removeIntentIds: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        intent_ids: removeIntentIds,
      }));
    }
  }, []);

  // マウント時に接続、アンマウント時に切断
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connectionState,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  };
}
```

### Day 2 成功基準

- [ ] `src/hooks/useWebSocket.ts` が作成され、型エラーなし
- [ ] `npm run dev` でエラーなく起動
- [ ] ブラウザコンソールで「WebSocket connecting to:」ログが出る

### Git Commit

```bash
git add dashboard/frontend/src/hooks/useWebSocket.ts
git commit -m "Add Sprint 15 Day 2: useWebSocket hook with auto-reconnect"
```

---

## Day 3: UIコンポーネント実装

### 目標
- WebSocket接続状態表示コンポーネント
- ポーリングフォールバック実装

### ステップ

#### 3.1 接続状態表示コンポーネント

**ファイル**: `dashboard/frontend/src/components/WebSocketStatus.tsx`

```typescript
/**
 * WebSocket接続状態表示コンポーネント
 */

import { useWebSocket } from '../hooks/useWebSocket';
import type { ConnectionStatus } from '../types/websocket';

const STATUS_CONFIG: Record<ConnectionStatus, {
  color: string;
  text: string;
  icon: string;
}> = {
  disconnected: { color: 'text-gray-500', text: '未接続', icon: '○' },
  connecting: { color: 'text-yellow-500', text: '接続中...', icon: '◐' },
  connected: { color: 'text-green-500', text: '接続済み', icon: '●' },
  reconnecting: { color: 'text-orange-500', text: '再接続中', icon: '◐' },
  failed: { color: 'text-red-500', text: '接続失敗', icon: '✕' },
};

export function WebSocketStatus() {
  const { connectionState, connect } = useWebSocket();
  const config = STATUS_CONFIG[connectionState.status];

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className={config.color}>{config.icon}</span>
      <span className={config.color}>{config.text}</span>
      {connectionState.status === 'reconnecting' && (
        <span className="text-gray-400">
          ({connectionState.retryCount}/5)
        </span>
      )}
      {connectionState.status === 'failed' && (
        <button
          onClick={() => {
            // リトライカウントをリセットして再接続
            window.location.reload();
          }}
          className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
        >
          再接続
        </button>
      )}
    </div>
  );
}
```

#### 3.2 ポーリングフォールバックHook

**ファイル**: `dashboard/frontend/src/hooks/useIntentsWithFallback.ts`

```typescript
/**
 * WebSocket失敗時にポーリングにフォールバックするHook
 */

import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';
import { apiClient } from '../api/client';

interface Intent {
  id: string;
  content: string;
  status: string;
  created_at: string;
}

async function fetchIntents(): Promise<Intent[]> {
  const response = await apiClient.get('/api/intents');
  return response.data;
}

export function useIntentsWithFallback() {
  const { connectionState } = useWebSocket();

  // WebSocket接続失敗時のみポーリング有効化
  const shouldPoll = connectionState.status === 'failed';

  return useQuery({
    queryKey: ['intents'],
    queryFn: fetchIntents,
    // WebSocket失敗時のみ5秒ポーリング
    refetchInterval: shouldPoll ? 5000 : false,
    // 通常時はWebSocketイベントで更新されるので自動refetch無効
    refetchOnWindowFocus: shouldPoll,
  });
}
```

#### 3.3 App.tsxへの統合

**ファイル**: `dashboard/frontend/src/App.tsx` (変更)

ヘッダー部分に追加:

```tsx
import { WebSocketStatus } from './components/WebSocketStatus';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Resonant Engine</h1>
        {/* WebSocket接続状態を表示 */}
        <WebSocketStatus />
      </header>
      {/* ... 残りのコンテンツ ... */}
    </div>
  );
}
```

### Day 3 成功基準

- [ ] `WebSocketStatus` コンポーネントが画面に表示される
- [ ] 接続状態（●接続済み）が正しく表示される
- [ ] WebSocket切断時に「再接続中」表示になる
- [ ] 5回リトライ後に「接続失敗」と「再接続」ボタンが表示される

### Git Commit

```bash
git add dashboard/frontend/src/components/WebSocketStatus.tsx
git add dashboard/frontend/src/hooks/useIntentsWithFallback.ts
git add dashboard/frontend/src/App.tsx
git commit -m "Add Sprint 15 Day 3: WebSocket status UI and polling fallback"
```

---

## Day 4: 統合とテスト

### 目標
- 既存コンポーネントとの統合
- 単体テスト作成
- 動作確認

### ステップ

#### 4.1 既存のポーリングをWebSocketに置き換え

**⚠️ 既存の `useIntents` を `useIntentsWithFallback` に置き換え**

検索: `useQuery.*intents.*refetchInterval`

該当箇所を以下のように変更:

```typescript
// Before
const { data: intents } = useQuery({
  queryKey: ['intents'],
  queryFn: fetchIntents,
  refetchInterval: 5000,  // ← これを削除
});

// After
import { useIntentsWithFallback } from '../hooks/useIntentsWithFallback';

const { data: intents } = useIntentsWithFallback();
```

#### 4.2 単体テスト作成

**ファイル**: `dashboard/frontend/src/hooks/__tests__/useWebSocket.test.ts`

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWebSocket } from '../useWebSocket';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  readyState: number = WebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onclose: ((event: { wasClean: boolean }) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: ((error: Error) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send = jest.fn();
  close = jest.fn();

  // テスト用ヘルパー
  simulateOpen() {
    this.readyState = WebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose(wasClean: boolean = true) {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.({ wasClean });
  }
}

// 環境変数モック
beforeAll(() => {
  (globalThis as any).WebSocket = MockWebSocket;
  (import.meta as any).env = {
    VITE_WS_URL: 'ws://localhost:8000/ws/intents',
  };
});

afterEach(() => {
  MockWebSocket.instances = [];
});

describe('useWebSocket', () => {
  const createWrapper = () => {
    const queryClient = new QueryClient();
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  test('WS-01: WebSocket接続確立', async () => {
    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    expect(result.current.connectionState.status).toBe('connecting');

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await waitFor(() => {
      expect(result.current.connectionState.status).toBe('connected');
    });
  });

  test('WS-03: Ping/Pong動作確認', async () => {
    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      MockWebSocket.instances[0].simulateMessage({ type: 'pong' });
    });

    // エラーなく処理されることを確認
    expect(result.current.connectionState.status).toBe('connected');
  });

  test('WS-05: 接続断時の自動再接続', async () => {
    jest.useFakeTimers();

    const { result } = renderHook(() => useWebSocket(), {
      wrapper: createWrapper(),
    });

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      MockWebSocket.instances[0].simulateClose(false); // 異常切断
    });

    expect(result.current.connectionState.status).toBe('reconnecting');
    expect(result.current.connectionState.retryCount).toBe(1);

    jest.useRealTimers();
  });
});
```

### Day 4 成功基準

- [ ] 既存のポーリングがWebSocketに置き換わっている
- [ ] 単体テスト3件以上作成
- [ ] `npm run test` で全テストPASS
- [ ] 手動テスト: バックエンドを再起動しても自動再接続される

### Git Commit

```bash
git add dashboard/frontend/src/hooks/__tests__/useWebSocket.test.ts
git commit -m "Add Sprint 15 Day 4: WebSocket tests and integration"
```

---

## Day 5: 最終確認とドキュメント

### 目標
- 全機能の動作確認
- パフォーマンス確認
- ドキュメント更新

### ステップ

#### 5.1 動作確認チェックリスト

以下を手動で確認:

| 項目 | 確認方法 | 期待結果 |
|------|---------|---------|
| 接続確立 | ブラウザ開発者ツールでWebSocket接続確認 | `ws://localhost:8000/ws/intents` に接続 |
| リアルタイム更新 | バックエンドでIntent更新 | UIが即座に更新される |
| 再接続 | バックエンドを停止→再起動 | 自動再接続される |
| フォールバック | バックエンドを5回以上停止 | ポーリングに切り替わる |
| 状態表示 | UIのWebSocketStatus確認 | 状態が正しく表示される |

#### 5.2 パフォーマンス確認

```bash
# バックエンド起動
cd bridge && python -m uvicorn api.app:app --reload

# フロントエンド起動
cd dashboard/frontend && npm run dev
```

ブラウザ開発者ツールで確認:
- [ ] 接続確立時間 < 1秒
- [ ] メッセージ受信遅延 < 100ms
- [ ] メモリリークなし（長時間動作させてHeap確認）

### 最終コミット

```bash
git add .
git commit -m "Complete Sprint 15: WebSocket integration

- WebSocket type definitions and environment setup
- useWebSocket hook with auto-reconnect (exponential backoff)
- WebSocketStatus component for connection state display
- Polling fallback when WebSocket fails
- Unit tests for WebSocket functionality

Done criteria:
- [x] WebSocket connection established
- [x] Real-time intent updates received
- [x] Auto-reconnect on disconnect (max 5 retries)
- [x] Polling fallback after max retries
- [x] 10+ unit tests passing"
```

---

## トラブルシューティング

### Q: WebSocket接続が確立されない

**確認事項:**
1. 環境変数 `VITE_WS_URL` が設定されているか
2. バックエンドが起動しているか
3. vite.config.ts のプロキシ設定が正しいか

**解決方法:**
```bash
# 環境変数確認
cat dashboard/frontend/.env.local

# バックエンド起動確認
curl http://localhost:8000/health

# Vite再起動
cd dashboard/frontend && npm run dev
```

### Q: 再接続が動作しない

**確認事項:**
1. `retryCount` が正しくインクリメントされているか（コンソールログ確認）
2. `scheduleReconnect` が呼ばれているか

**解決方法:**
コンソールログを確認:
```
WebSocket reconnecting in 1000ms (attempt 1/5)
WebSocket reconnecting in 2000ms (attempt 2/5)
...
```

### Q: ポーリングフォールバックが動作しない

**確認事項:**
1. `connectionState.status` が `'failed'` になっているか
2. `useIntentsWithFallback` が使用されているか

---

**総行数**: 550
