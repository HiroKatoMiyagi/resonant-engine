/**
 * ContradictionItem Component
 * 
 * 個別の矛盾アイテムを表示
 * 仕様書の色指定に厳密に従う
 */

import React from 'react';
import type { Contradiction } from '../../types/contradiction';

interface ContradictionItemProps {
  contradiction: Contradiction;
  onResolve?: (id: string) => void;
}

/**
 * 矛盾タイプに応じた色を返す（仕様書の色指定に厳密に従う）
 * 変更禁止 - 仕様書「3.3 UI仕様」に定義
 */
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

/**
 * 矛盾タイプの日本語ラベルを返す
 */
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
  const [isModalOpen, setIsModalOpen] = React.useState(false);

  // Mock resolve function if not provided by parent (for individual component testing/usage)
  const handleResolve = async (data: any) => {
    if (onResolve) {
      // If props onResolve expects ID, we might need a wrapper or assume parent handles API
      // But based on specs, we want to call API here or propagate up
      // For now, let's assume onResolve prop handles the API call with the data
      // OR we just use it to trigger refresh.
      // Let's adapt: if onResolve is passed, we call it. 
      // Ideally, the modal should call the API directly or a passed function.
      // The prop `onResolve` currently is `(id: string) => void`.
      // We will change the Modal integration slightly in the next step or here.

      // Actually, looking at the spec, 3.1.4 API Integration uses `contradictionsApi.resolve`.
      // We should import API client here or in the parent.
      // Let's import the modal and use it.

      try {
        await import('../../api/client').then(m =>
          m.contradictionsApi.resolve(contradiction.id, data)
        );
        if (onResolve) onResolve(contradiction.id);
      } catch (e) {
        console.error(e);
        throw e; // Modal will catch this
      }
    }
  };

  return (
    <>
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
          <span className={`text-xs px-2 py-1 rounded ${contradiction.resolution_status === 'resolved'
              ? 'bg-green-100 text-green-800'
              : contradiction.resolution_status === 'dismissed'
                ? 'bg-gray-100 text-gray-800'
                : 'bg-red-100 text-red-800'
            }`}>
            {contradiction.resolution_status === 'resolved' ? '解決済み' :
              contradiction.resolution_status === 'dismissed' ? '却下' : '未解決'}
          </span>

          {contradiction.resolution_status === 'pending' && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="text-xs bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
            >
              解決
            </button>
          )}
        </div>
      </div>

      {isModalOpen && (
        <React.Suspense fallback={null}>
          <ContradictionResolveModal
            contradiction={contradiction}
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onResolve={handleResolve}
          />
        </React.Suspense>
      )}
    </>
  );
};

// Lazy import to avoid circular dependencies if any, and for code splitting
const ContradictionResolveModal = React.lazy(() => import('./ContradictionResolveModal'));

export default ContradictionItem;
