/**
 * WebSocket失敗時にポーリングにフォールバックするHook
 */

import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';
import axios from 'axios';

interface Intent {
  id: string;
  content: string;
  status: string;
  created_at: string;
}

async function fetchIntents(): Promise<Intent[]> {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await axios.get(`${apiUrl}/api/intents`);
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
