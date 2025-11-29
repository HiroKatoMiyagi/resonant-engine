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
  failed: { color: 'text-gray-500', text: 'ポーリングモード', icon: '◎' },
};

export function WebSocketStatus() {
  const { connectionState } = useWebSocket();
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

    </div>
  );
}
