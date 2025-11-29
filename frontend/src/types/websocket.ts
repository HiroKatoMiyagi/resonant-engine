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
