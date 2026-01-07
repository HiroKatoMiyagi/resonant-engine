import React, { useState } from 'react';
import type { ChoicePoint, DecideChoiceRequest } from '../../types';
import ChoicePointDecideModal from './ChoicePointDecideModal';

interface ChoicePointItemProps {
    choicePoint: ChoicePoint;
    onDecide?: (id: string, data: DecideChoiceRequest) => Promise<void>;
}

const ChoicePointItem: React.FC<ChoicePointItemProps> = ({
    choicePoint,
    onDecide
}) => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const getStatusStyle = (status: string) => {
        switch (status) {
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            case 'decided': return 'bg-green-100 text-green-800';
            case 'expired': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <>
            <div className="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs font-bold rounded uppercase ${getStatusStyle(choicePoint.status)}`}>
                            {choicePoint.status}
                        </span>
                        <div className="space-x-1">
                            {choicePoint.tags.map(tag => (
                                <span key={tag} className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                                    #{tag}
                                </span>
                            ))}
                        </div>
                    </div>
                    <span className="text-xs text-gray-400">
                        {new Date(choicePoint.created_at).toLocaleDateString()}
                    </span>
                </div>

                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                    {choicePoint.question}
                </h3>

                <div className="space-y-2 mb-4">
                    {choicePoint.choices.map(choice => (
                        <div
                            key={choice.choice_id}
                            className={`p-3 rounded border ${choicePoint.selected_choice_id === choice.choice_id
                                ? 'bg-green-50 border-green-200'
                                : 'bg-gray-50 border-gray-100'
                                }`}
                        >
                            <div className="flex items-center justify-between">
                                <span className={`font-medium ${choicePoint.selected_choice_id === choice.choice_id ? 'text-green-800' : 'text-gray-700'
                                    }`}>
                                    {choice.choice_text}
                                </span>
                                {choicePoint.selected_choice_id === choice.choice_id && (
                                    <span className="text-green-600 text-xs font-bold">SELECTED</span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {choicePoint.status === 'decided' && choicePoint.decision_rationale && (
                    <div className="bg-gray-50 p-3 rounded mb-4 text-sm text-gray-600 italic border-l-4 border-gray-300">
                        <span className="font-semibold not-italic block mb-1">Decision Rationale:</span>
                        {choicePoint.decision_rationale}
                    </div>
                )}

                {choicePoint.status === 'pending' && onDecide && (
                    <div className="flex justify-end pt-2 border-t">
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
                        >
                            決定する
                        </button>
                    </div>
                )}
            </div>

            {isModalOpen && onDecide && (
                <ChoicePointDecideModal
                    choicePoint={choicePoint}
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onDecide={async (data) => {
                        await onDecide(choicePoint.id, data);
                        setIsModalOpen(false);
                    }}
                />
            )}
        </>
    );
};

export default ChoicePointItem;
