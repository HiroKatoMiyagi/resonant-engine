/**
 * ContradictionDashboard Component
 * 
 * 矛盾検出ダッシュボード
 * 5秒間隔でポーリング（Phase 2でWebSocket化予定）
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPendingContradictions } from '../../api/contradiction';
import ContradictionItem from './ContradictionItem';
import { useWebSocket } from '../../hooks/useWebSocket';

const ContradictionDashboard: React.FC = () => {
  // WebSocket接続（リアルタイム更新用）
  const { connectionState } = useWebSocket();
  
  // TODO: 実際のユーザーIDを取得する仕組みが必要
  // 現在はデフォルト値を使用
  const userId = 'default';

  // WebSocket失敗時のみポーリング有効化
  const shouldPoll = connectionState.status === 'failed';

  const { data, isLoading, error } = useQuery({
    queryKey: ['contradictions', userId],
    queryFn: () => getPendingContradictions(userId),
    // WebSocket失敗時のみ5秒ポーリング
    refetchInterval: shouldPoll ? 5000 : false,
    refetchOnWindowFocus: shouldPoll,
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
        <div className="text-center text-sm text-gray-500 mt-2">
          {error instanceof Error ? error.message : '不明なエラー'}
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
