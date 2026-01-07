import React, { useState } from 'react';
import type { TermDrift, TermDriftResolution } from '../../types/termDrift';

interface TermDriftItemProps {
    drift: TermDrift;
    onResolve?: (id: string, data: TermDriftResolution) => Promise<void>;
}

const TermDriftItem: React.FC<TermDriftItemProps> = ({ drift, onResolve }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [resolutionAction, setResolutionAction] = useState<'intentional_change' | 'rollback' | 'migration_needed'>('intentional_change');
    const [resolutionNote, setResolutionNote] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const getDriftTypeColor = (type: string) => {
        switch (type) {
            case 'semantic_shift': return 'bg-purple-100 text-purple-800';
            case 'expansion': return 'bg-blue-100 text-blue-800';
            case 'contraction': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const handleResolve = async () => {
        if (!onResolve) return;
        try {
            setIsSubmitting(true);
            await onResolve(drift.id, {
                resolution_action: resolutionAction,
                resolution_note: resolutionNote,
                resolved_by: 'user' // TODO: Get from auth context
            });
            setIsModalOpen(false);
        } catch (err) {
            console.error('Resolve failed:', err);
            alert('解決処理に失敗しました');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <>
            <div className="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-bold text-gray-800">{drift.term_name}</h3>
                        <span
                            data-testid="drift-type-badge"
                            className={`px-2 py-1 text-xs font-bold rounded uppercase ${getDriftTypeColor(drift.drift_type)}`}
                        >
                            {drift.drift_type}
                        </span>
                    </div>
                    <div className="text-right">
                        <div className="text-sm font-semibold text-gray-600">
                            Confidence: {(drift.confidence_score * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-400">
                            {new Date(drift.detected_at).toLocaleDateString()}
                        </div>
                    </div>
                </div>

                <div className="bg-gray-50 rounded p-3 mb-4 text-sm text-gray-700">
                    <p className="font-semibold mb-1 text-gray-500 text-xs">変更サマリー:</p>
                    <p>{drift.change_summary}</p>
                </div>

                {drift.impact_analysis && (
                    <div className="mb-4 text-sm">
                        <p className="font-semibold mb-1 text-gray-500 text-xs">影響分析:</p>
                        <ul className="list-disc list-inside text-gray-600">
                            <li>{drift.impact_analysis.affected_instances}つのインスタンスに影響</li>
                            {drift.impact_analysis.migration_needed && (
                                <li className="text-red-600 font-medium">マイグレーションが必要な可能性あり</li>
                            )}
                        </ul>
                    </div>
                )}

                {drift.status === 'pending' && onResolve && (
                    <div className="flex justify-end pt-2 border-t">
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
                        >
                            解決する
                        </button>
                    </div>
                )}
            </div>

            {isModalOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg w-full max-w-lg p-6 shadow-xl">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">ドリフトの解決: {drift.term_name}</h2>

                        <div className="mb-4 space-y-2">
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="action"
                                    value="intentional_change"
                                    checked={resolutionAction === 'intentional_change'}
                                    onChange={(e) => setResolutionAction(e.target.value as any)}
                                    className="text-blue-600"
                                />
                                <span>Intentional Change (意図的な変更)</span>
                            </label>
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="action"
                                    value="rollback"
                                    checked={resolutionAction === 'rollback'}
                                    onChange={(e) => setResolutionAction(e.target.value as any)}
                                    className="text-blue-600"
                                />
                                <span>Rollback (元に戻す)</span>
                            </label>
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="action"
                                    value="migration_needed"
                                    checked={resolutionAction === 'migration_needed'}
                                    onChange={(e) => setResolutionAction(e.target.value as any)}
                                    className="text-blue-600"
                                />
                                <span>Migration Needed (要マイグレーション)</span>
                            </label>
                        </div>

                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">解決ノート (10文字以上)</label>
                            <textarea
                                value={resolutionNote}
                                onChange={(e) => setResolutionNote(e.target.value)}
                                className="w-full border rounded p-2 h-24"
                                placeholder="理由を入力してください..."
                            />
                        </div>

                        <div className="flex justify-end space-x-3">
                            <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 border rounded">キャンセル</button>
                            <button
                                onClick={handleResolve}
                                disabled={resolutionNote.length < 10 || isSubmitting}
                                className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
                            >
                                {isSubmitting ? '処理中...' : '解決を確定'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default TermDriftItem;
