import React, { useState } from 'react';
import type { Contradiction, ResolveContradictionRequest } from '../../types';

interface ContradictionResolveModalProps {
  contradiction: Contradiction;
  isOpen: boolean;
  onClose: () => void;
  onResolve: (data: ResolveContradictionRequest) => Promise<void>;
}

const ContradictionResolveModal: React.FC<ContradictionResolveModalProps> = ({
  contradiction,
  isOpen,
  onClose,
  onResolve,
}) => {
  const [action, setAction] = useState<'policy_change' | 'mistake' | 'coexist'>('policy_change');
  const [rationale, setRationale] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (rationale.length < 10) {
      setError('解決根拠は10文字以上で入力してください。');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onResolve({
        resolution_action: action,
        resolution_rationale: rationale,
        resolved_by: 'user', // NOTE: In a real app, get from auth context
      });
      onClose();
    } catch (err) {
      setError('解決処理に失敗しました。');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6 border-b pb-4">
          <h2 className="text-xl font-bold text-gray-800">矛盾の解決</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 p-3 rounded">
            <span className="text-xs text-gray-500 block">矛盾タイプ</span>
            <span className="font-medium text-gray-800">{contradiction.contradiction_type}</span>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <span className="text-xs text-gray-500 block">信頼度</span>
            <span className="font-medium text-gray-800">{(contradiction.confidence_score * 100).toFixed(0)}%</span>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">新規Intent</h3>
          <div className="bg-blue-50 border border-blue-200 p-3 rounded text-sm text-gray-800">
            {contradiction.new_intent_content}
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">競合Intent</h3>
          <div className="bg-red-50 border border-red-200 p-3 rounded text-sm text-gray-800">
            {contradiction.conflicting_intent_content}
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">解決アクション</h3>
          <div className="space-y-2">
            <label className="flex items-center space-x-2 p-3 border rounded cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="resolution_action"
                value="policy_change"
                checked={action === 'policy_change'}
                onChange={(e) => setAction(e.target.value as any)}
                className="text-blue-600"
              />
              <div>
                <span className="font-medium block">policy_change</span>
                <span className="text-xs text-gray-500">方針変更として承認（新規Intentを採用）</span>
              </div>
            </label>
            <label className="flex items-center space-x-2 p-3 border rounded cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="resolution_action"
                value="mistake"
                checked={action === 'mistake'}
                onChange={(e) => setAction(e.target.value as any)}
                className="text-blue-600"
              />
              <div>
                <span className="font-medium block">mistake</span>
                <span className="text-xs text-gray-500">誤りとして棄却（新規Intentを破棄）</span>
              </div>
            </label>
            <label className="flex items-center space-x-2 p-3 border rounded cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="resolution_action"
                value="coexist"
                checked={action === 'coexist'}
                onChange={(e) => setAction(e.target.value as any)}
                className="text-blue-600"
              />
              <div>
                <span className="font-medium block">coexist</span>
                <span className="text-xs text-gray-500">共存可能として承認（両方を維持）</span>
              </div>
            </label>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">解決根拠 <span className="text-red-500 text-xs">*必須 (10文字以上)</span></h3>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="なぜこの解決策を選んだのか、詳細な理由を入力してください..."
            className="w-full border rounded p-3 h-24 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border rounded hover:bg-gray-50"
            disabled={isSubmitting}
          >
            キャンセル
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                処理中...
              </>
            ) : (
              '解決を確定'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContradictionResolveModal;
