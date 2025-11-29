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
  const pingIntervalRef = useRef<number | null>(null);

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

      ws.onerror = () => {
        // WebSocketエラー（エンドポイント未実装の場合も含む）
        console.warn('WebSocket connection failed, falling back to polling');
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
    // WebSocket URLが設定されている場合のみ接続
    const wsUrl = import.meta.env.VITE_WS_URL;
    if (wsUrl && wsUrl !== 'disabled') {
      connect();
    } else {
      // WebSocket無効時は即座にfailed状態にしてポーリングにフォールバック
      setConnectionState({
        status: 'failed',
        retryCount: 0,
        lastConnected: null,
        lastError: new Error('WebSocket disabled'),
      });
    }
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
