import React, { useEffect, useState } from 'react';
import { termDriftApi } from '../api/termDrift';
import TermDriftItem from '../components/term-drift/TermDriftItem';
import TermAnalyzeForm from '../components/term-drift/TermAnalyzeForm';
import type { TermDrift, TermDriftResolution } from '../types/termDrift';

const TermDriftPage: React.FC = () => {
    const [drifts, setDrifts] = useState<TermDrift[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchDrifts = async () => {
        try {
            setLoading(true);
            const response = await termDriftApi.getPending('user'); // user_id hardcoded
            setDrifts(response.data);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch drifts:', err);
            setError('データの読み込みに失敗しました。');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDrifts();
    }, []);

    const handleResolve = async (id: string, data: TermDriftResolution) => {
        await termDriftApi.resolve(id, data);
        await fetchDrifts();
    };

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">用語ドリフト検出</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-semibold text-gray-700">保留中のドリフト</h2>

                    {loading ? (
                        <div className="flex justify-center p-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        </div>
                    ) : error ? (
                        <div className="text-red-500 p-4 bg-red-50 rounded">{error}</div>
                    ) : drifts.length === 0 ? (
                        <div className="bg-white p-6 rounded shadow text-center text-gray-500">
                            検出された用語ドリフトはありません。
                        </div>
                    ) : (
                        drifts.map(drift => (
                            <TermDriftItem
                                key={drift.id}
                                drift={drift}
                                onResolve={handleResolve}
                            />
                        ))
                    )}
                </div>

                <div className="lg:col-span-1">
                    <div className="sticky top-6">
                        <TermAnalyzeForm onAnalyze={(data) => termDriftApi.analyze(data).then(res => res.data)} />

                        <div className="mt-6 bg-blue-50 p-4 rounded-lg text-sm text-blue-800 border border-blue-100">
                            <p className="font-bold mb-2">用語ドリフトについて</p>
                            <p>用語の意味変化（Semantic Shift）や定義の拡張・縮小を検出します。システムの一貫性を保つため、定期的なチェックを推奨します。</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TermDriftPage;
