import React, { useState } from 'react';
import type { ChoicePoint, DecideChoiceRequest } from '../../types';

interface ChoicePointDecideModalProps {
    choicePoint: ChoicePoint;
    isOpen: boolean;
    onClose: () => void;
    onDecide: (data: DecideChoiceRequest) => Promise<void>;
}

const ChoicePointDecideModal: React.FC<ChoicePointDecideModalProps> = ({
    choicePoint,
    isOpen,
    onClose,
    onDecide
}) => {
    const [selectedChoiceId, setSelectedChoiceId] = useState<string>('');
    const [rationale, setRationale] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!selectedChoiceId) {
            setError('選択肢を選んでください。');
            return;
        }
        if (rationale.length < 10) {
            setError('決定理由は10文字以上で入力してください。');
            return;
        }

        try {
            setIsSubmitting(true);
            setError(null);
            await onDecide({
                selected_choice_id: selectedChoiceId,
                decision_rationale: rationale,
                rejection_reasons: {} // TODO: Add rejection reasons UI if needed in future
            });
        } catch (err) {
            setError('決定処理に失敗しました。');
            console.error(err);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg w-full max-w-2xl p-6 shadow-xl">
                <div className="flex justify-between items-center mb-6 border-b pb-4">
                    <h2 className="text-xl font-bold text-gray-800">決定を行う</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                        ✕
                    </button>
                </div>

                <p className="font-semibold text-lg mb-4 text-gray-800">{choicePoint.question}</p>

                <div className="mb-6 space-y-3">
                    {choicePoint.choices.map(choice => (
                        <label
                            key={choice.choice_id}
                            className={`flex items-center p-4 border-2 rounded cursor-pointer transition-colors ${selectedChoiceId === choice.choice_id
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 hover:border-blue-200'
                                }`}
                        >
                            <input
                                type="radio"
                                name="choice"
                                value={choice.choice_id}
                                checked={selectedChoiceId === choice.choice_id}
                                onChange={(e) => setSelectedChoiceId(e.target.value)}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <span className="ml-3 font-medium text-gray-900">{choice.choice_text}</span>
                        </label>
                    ))}
                </div>

                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        決定理由 <span className="text-red-500 text-xs">*必須 (10文字以上)</span>
                    </label>
                    <textarea
                        value={rationale}
                        onChange={(e) => setRationale(e.target.value)}
                        placeholder="なぜこの選択肢を選んだのか、理由を入力してください..."
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
                        {isSubmitting ? '処理中...' : '決定を確定'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChoicePointDecideModal;
