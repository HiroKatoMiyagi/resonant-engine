import React, { useEffect, useState } from 'react';
import { choicePointsApi } from '../api/client';
import ChoicePointItem from '../components/choice-points/ChoicePointItem';
import type { ChoicePoint, CreateChoicePointRequest, DecideChoiceRequest } from '../types';

const ChoicePointsPage: React.FC = () => {
    const [choicePoints, setChoicePoints] = useState<ChoicePoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // For creating new choice point (simple implementation)
    const [isCreating, setIsCreating] = useState(false);
    const [newQuestion, setNewQuestion] = useState('');

    const fetchChoicePoints = async () => {
        try {
            setLoading(true);
            // NOTE: In real app, might want to fetch all or have tabs for pending/all
            // For now, let's fetch pending as primary, maybe implement search later
            const response = await choicePointsApi.search({ user_id: 'user' }); // fetch all for list
            setChoicePoints(response.data.results || response.data.choice_points || []);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch choice points:', err);
            setError('データの読み込みに失敗しました。');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchChoicePoints();
    }, []);

    const handleDecide = async (id: string, data: DecideChoiceRequest) => {
        try {
            await choicePointsApi.decide(id, data);
            // Refresh list to show updated status
            await fetchChoicePoints();
        } catch (err) {
            console.error('Failed to decide choice point:', err);
            throw err; // Let modal handle error display
        }
    };

    const handleCreate = async () => {
        if (!newQuestion.trim()) return;
        try {
            const data: CreateChoicePointRequest = {
                question: newQuestion,
                choices: [], // Initially empty or could add UI for it
                tags: [],
                context_type: 'general',
                user_id: 'user', // TODO: Get from auth context
            };
            await choicePointsApi.create(data);
            setNewQuestion('');
            setIsCreating(false);
            await fetchChoicePoints();
        } catch (err) {
            console.error('Failed to create choice point:', err);
            alert('作成に失敗しました');
        }
    };

    if (loading && choicePoints.length === 0) {
        return (
            <div className="p-8 flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">選択ポイント</h1>
                <button
                    onClick={() => setIsCreating(!isCreating)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium"
                >
                    {isCreating ? 'キャンセル' : '新規作成'}
                </button>
            </div>

            {isCreating && (
                <div className="bg-white p-4 rounded-lg shadow mb-6 border border-blue-200">
                    <h3 className="font-semibold mb-2">新しい選択ポイントを作成</h3>
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={newQuestion}
                            onChange={(e) => setNewQuestion(e.target.value)}
                            placeholder="質問を入力してください (例: 使用するデータベースは？)"
                            className="flex-1 border rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            onClick={handleCreate}
                            disabled={!newQuestion.trim()} // TODO: Add better validation logic for choices if needed
                            className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                        >
                            作成
                        </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                        ※ 簡易作成モード: 詳細な選択肢は後から追加する想定
                    </p>
                </div>
            )}

            {error && (
                <div className="bg-red-50 text-red-700 p-4 rounded">
                    {error}
                </div>
            )}

            <div className="space-y-4">
                {choicePoints.length === 0 ? (
                    <div className="text-center text-gray-500 py-10">
                        選択ポイントはまだありません。
                    </div>
                ) : (
                    choicePoints.map(cp => (
                        <ChoicePointItem
                            key={cp.id}
                            choicePoint={cp}
                            onDecide={handleDecide}
                        />
                    ))
                )}
            </div>
        </div>
    );
};

export default ChoicePointsPage;
