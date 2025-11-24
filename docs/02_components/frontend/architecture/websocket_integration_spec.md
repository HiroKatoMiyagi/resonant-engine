# Sprint 15: WebSocket統合 詳細仕様書

**バージョン**: 1.0.0
**作成日**: 2025-11-24
**作成者**: Kana (Claude Sonnet 4.5)

---

## 0. CRITICAL: Kiro/実装者への警告

**⚠️ 以下の行為は絶対に禁止**

| 禁止事項 | 過去の問題（総合テストv3.1-v3.7） | 正しい対応 |
|---------|--------------------------------|-----------|
| WebSocket URLのハードコード | v3.4でパスワードハードコード | 環境変数 `VITE_WS_URL` を使用 |
| 独自判断でポーリングにフォールバック | v3.5でテストスキップ | 仕様書の再接続ロジックに従う |
| メッセージ型の独自定義 | v3.5-v3.6でAPI名間違い | 本仕様書の型定義をそのまま使用 |
| 接続エラー時の無限リトライ | - | 指数バックオフ（最大5回） |

---

## 1. 概要

### 1.1 目的

現在の5秒ポーリングをWebSocketリアルタイム通信に置き換え、即座にシステム状態更新を受け取れるようにする。

### 1.2 あなたの体験（ユーザー視点）

```
現状（ポーリング）:
┌─────────────────────────────────────────────────┐
│  あなた: "コードレビューして"                      │
│                                                  │
│  [待機中...]  ←── 5秒ごとに確認                   │
│  [待機中...]                                     │
│  [待機中...]                                     │
│                                                  │
│  Claude: "レビュー結果です..."                    │
└─────────────────────────────────────────────────┘

目標（WebSocket）:
┌─────────────────────────────────────────────────┐
│  あなた: "コードレビューして"                      │
│                                                  │
│  Claude: "分析中です..."       ←── 即座に状態表示  │
│  Claude: "構造を確認中..."                        │
│  Claude: "レビュー結果です..."                    │
└─────────────────────────────────────────────────┘
```

### 1.3 背景

**現状の問題:**
- 5秒ごとのポーリングは非効率（サーバー負荷、遅延）
- 状態変化に気づくまで最大5秒かかる
- ユーザー体験が悪い（待っている感覚）

**バックエンド実装状況:**
- WebSocket API: `/ws/intents` 実装済み
- イベント配信: `EventDistributor` 実装済み
- 接続管理: `WebSocketManager` 実装済み

### 1.4 Done Definition

**Tier 1: 必須要件**
- [ ] WebSocket接続が確立できる
- [ ] Intent更新イベントをリアルタイムで受信できる
- [ ] 接続断時に自動再接続する（指数バックオフ）
- [ ] ポーリングへのフォールバック機能
- [ ] 10件以上の単体/統合テストが作成され、全件PASS

**Tier 2: 品質要件**
- [ ] 接続確立時間 < 1秒
- [ ] メッセージ受信遅延 < 100ms
- [ ] 再接続成功率 > 95%
- [ ] メモリリーク防止（cleanup実装）

---

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              useWebSocket Hook                       │  │
│  │                                                      │  │
│  │  ┌────────────────┐  ┌────────────────────────┐    │  │
│  │  │ WebSocketClient│  │ ConnectionStateManager │    │  │
│  │  │ - connect()    │  │ - status               │    │  │
│  │  │ - disconnect() │  │ - retryCount           │    │  │
│  │  │ - send()       │  │ - lastConnected        │    │  │
│  │  └────────────────┘  └────────────────────────┘    │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │         MessageHandler                      │    │  │
│  │  │  - onIntentUpdate()                         │    │  │
│  │  │  - onContradictionDetected()                │    │  │
│  │  │  - onReEvaluationStarted()                  │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              React Query Cache                       │  │
│  │  - invalidateQueries on WebSocket event              │  │
│  │  - optimistic updates                                │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (wss://)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              /ws/intents endpoint                    │  │
│  │                                                      │  │
│  │  ┌────────────────┐  ┌────────────────────────┐    │  │
│  │  │WebSocketManager│  │   EventDistributor     │    │  │
│  │  │ - connect()    │  │   - INTENT_CHANGED     │    │  │
│  │  │ - broadcast()  │  │   - subscribe()        │    │  │
│  │  └────────────────┘  └────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 データフロー

```
[Intent更新発生]
      │
      ▼
EventDistributor.publish(INTENT_CHANGED, payload)
      │
      ▼
WebSocketManager.broadcast_intent_event(event)
      │
      ▼
WebSocket送信: { type: "intent_update", data: {...}, timestamp: "..." }
      │
      ▼
Frontend useWebSocket フック受信
      │
      ▼
MessageHandler.onIntentUpdate(data)
      │
      ▼
React Query: queryClient.invalidateQueries(['intents'])
      │
      ▼
UI自動更新
```

---

## 3. バックエンドAPI仕様（実装済み）

### 3.1 エンドポイント

**⚠️ CRITICAL: このURLを正確に使用すること**

```
WebSocket URL: ws://{host}/ws/intents
              wss://{host}/ws/intents  (本番環境)
```

**環境変数設定**:
```env
# .env.local
VITE_WS_URL=ws://localhost:8000/ws/intents

# .env.production
VITE_WS_URL=wss://api.resonant-engine.example.com/ws/intents
```

### 3.2 接続パラメータ

```
/ws/intents?intent_ids=id1&intent_ids=id2
```

| パラメータ | 必須 | 説明 |
|-----------|------|------|
| intent_ids | No | 購読するIntent ID（複数指定可）。省略時は全Intent購読 |

### 3.3 メッセージ型定義

**⚠️ CRITICAL: この型定義をそのまま使用すること（変更禁止）**

```typescript
// src/types/websocket.ts

/**
 * クライアント → サーバー メッセージ
 */
export type ClientMessage =
  | { type: 'ping' }
  | { type: 'subscribe'; intent_ids: string[] }
  | { type: 'unsubscribe'; intent_ids: string[] };

/**
 * サーバー → クライアント メッセージ
 */
export type ServerMessage =
  | { type: 'pong' }
  | { type: 'intent_update'; data: IntentUpdatePayload; timestamp: string };

/**
 * Intent更新ペイロード
 */
export interface IntentUpdatePayload {
  intent_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  content?: string;
  response?: string;
  contradiction_detected?: boolean;
  contradiction_id?: string;
  re_evaluation_phase?: ReEvaluationPhase;
}

/**
 * 再評価フェーズ
 */
export type ReEvaluationPhase =
  | 'detect'
  | 'isolate'
  | 'align'
  | 'decide'
  | 'apply'
  | 'log';
```

### 3.4 メッセージシーケンス

```
Client                              Server
   │                                   │
   │──── WebSocket接続要求 ───────────→│
   │                                   │
   │←─── 接続確立 ────────────────────│
   │                                   │
   │──── { type: "ping" } ───────────→│
   │←─── { type: "pong" } ────────────│
   │                                   │
   │──── { type: "subscribe",  ──────→│
   │       intent_ids: ["abc"] }       │
   │                                   │
   │←─── { type: "intent_update", ────│
   │       data: {...},                │
   │       timestamp: "2025-..." }     │
   │                                   │
   │──── { type: "unsubscribe", ─────→│
   │       intent_ids: ["abc"] }       │
   │                                   │
```

---

## 4. フロントエンド実装

### 4.1 WebSocket接続状態

```typescript
// src/types/websocket.ts

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
```

### 4.2 useWebSocket Hook

**⚠️ CRITICAL: このフックの実装をそのまま使用すること**

```typescript
// src/hooks/useWebSocket.ts

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// 定数（変更禁止）
const MAX_RETRY_COUNT = 5;
const BASE_RETRY_DELAY_MS = 1000;
const PING_INTERVAL_MS = 30000;

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

  // メッセージハンドラ
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: ServerMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'pong':
          // Ping応答、接続確認OK
          break;

        case 'intent_update':
          // Intent更新イベント
          handleIntentUpdate(message.data, message.timestamp);
          break;

        default:
          console.warn('Unknown message type:', message);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, []);

  // Intent更新ハンドラ
  const handleIntentUpdate = useCallback((
    data: IntentUpdatePayload,
    timestamp: string
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

  // 接続開始
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState(prev => ({ ...prev, status: 'connecting' }));

    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
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
        }, PING_INTERVAL_MS);
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        clearPingInterval();

        if (!event.wasClean && retryCountRef.current < MAX_RETRY_COUNT) {
          // 再接続
          scheduleReconnect();
        } else if (retryCountRef.current >= MAX_RETRY_COUNT) {
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
      setConnectionState(prev => ({
        ...prev,
        status: 'failed',
        lastError: error as Error,
      }));
    }
  }, [getWebSocketUrl, handleMessage]);

  // 再接続スケジュール（指数バックオフ）
  const scheduleReconnect = useCallback(() => {
    retryCountRef.current += 1;
    const delay = BASE_RETRY_DELAY_MS * Math.pow(2, retryCountRef.current - 1);

    setConnectionState(prev => ({
      ...prev,
      status: 'reconnecting',
      retryCount: retryCountRef.current,
    }));

    setTimeout(() => {
      connect();
    }, delay);
  }, [connect]);

  // Pingインターバルクリア
  const clearPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

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

  const unsubscribe = useCallback((intentIds: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        intent_ids: intentIds,
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

### 4.3 接続状態表示コンポーネント

```typescript
// src/components/WebSocketStatus.tsx

import { useWebSocket } from '../hooks/useWebSocket';

export function WebSocketStatus() {
  const { connectionState } = useWebSocket();

  const statusConfig = {
    disconnected: { color: 'gray', text: '未接続', icon: '○' },
    connecting: { color: 'yellow', text: '接続中...', icon: '◐' },
    connected: { color: 'green', text: '接続済み', icon: '●' },
    reconnecting: { color: 'orange', text: `再接続中 (${connectionState.retryCount}/5)`, icon: '◐' },
    failed: { color: 'red', text: '接続失敗', icon: '✕' },
  };

  const config = statusConfig[connectionState.status];

  return (
    <div className={`ws-status ws-status--${connectionState.status}`}>
      <span className="ws-status__icon">{config.icon}</span>
      <span className="ws-status__text">{config.text}</span>
      {connectionState.status === 'failed' && (
        <button onClick={() => window.location.reload()}>
          再接続
        </button>
      )}
    </div>
  );
}
```

### 4.4 ポーリングフォールバック

**⚠️ WebSocket接続失敗時のみポーリングにフォールバック**

```typescript
// src/hooks/useIntentsWithFallback.ts

import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';
import { fetchIntents } from '../api/intents';

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

---

## 5. エラーハンドリング

### 5.1 接続エラー

| エラー種別 | 対応 |
|-----------|------|
| 接続タイムアウト | 指数バックオフで再接続（最大5回） |
| 認証エラー (401) | ログイン画面にリダイレクト |
| サーバーエラー (5xx) | 指数バックオフで再接続 |
| ネットワークエラー | 指数バックオフで再接続 |
| 最大リトライ到達 | ポーリングフォールバック |

### 5.2 指数バックオフ

```
1回目: 1秒後
2回目: 2秒後
3回目: 4秒後
4回目: 8秒後
5回目: 16秒後
→ 失敗: ポーリングフォールバック
```

---

## 6. テスト要件

### 6.1 必須テスト項目

| テストID | テスト名 | 優先度 |
|---------|---------|--------|
| WS-01 | WebSocket接続確立 | 必須 |
| WS-02 | Intent更新イベント受信 | 必須 |
| WS-03 | Ping/Pong動作確認 | 必須 |
| WS-04 | 購読追加/解除 | 必須 |
| WS-05 | 接続断時の自動再接続 | 必須 |
| WS-06 | 指数バックオフ動作 | 必須 |
| WS-07 | 最大リトライ後のフォールバック | 必須 |
| WS-08 | React Queryキャッシュ更新 | 必須 |
| WS-09 | メモリリーク防止（cleanup） | 推奨 |
| WS-10 | 複数タブでの動作 | 推奨 |

---

## 7. 環境設定

### 7.1 必須環境変数

```env
# 開発環境 (.env.local)
VITE_WS_URL=ws://localhost:8000/ws/intents

# 本番環境 (.env.production)
VITE_WS_URL=wss://api.resonant-engine.example.com/ws/intents
```

### 7.2 Vite設定

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

---

## 8. パフォーマンス要件

| 指標 | 目標値 |
|------|--------|
| 接続確立時間 | < 1秒 |
| メッセージ受信遅延 | < 100ms |
| 再接続成功率 | > 95% |
| メモリ使用量増加 | < 10MB |

---

## 9. 参考資料

- [バックエンドWebSocket実装](../../../bridge/api/websocket.py)
- [WebSocketManager](../../../bridge/realtime/websocket_manager.py)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React Query invalidateQueries](https://tanstack.com/query/latest/docs/react/guides/query-invalidation)

---

**総行数**: 450
