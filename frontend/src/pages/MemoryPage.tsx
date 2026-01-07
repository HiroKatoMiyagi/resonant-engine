import React, { useEffect, useState } from 'react';
import { memoryApi } from '../api/client';
import MemoryStatusCard from '../components/memory/MemoryStatusCard';
import CompressionButton from '../components/memory/CompressionButton';
import type { MemoryStatus } from '../types';

const MemoryPage: React.FC = () => {
    const [status, setStatus] = useState<MemoryStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = async () => {
        try {
            setLoading(true);
            const response = await memoryApi.getStatus('user'); // user_id hardcoded for now
            setStatus(response.data);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch memory status:', err);
            setError('メモリ状態の取得に失敗しました。');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const handleCompress = async () => {
        const response = await memoryApi.compress('user');
        await fetchStatus(); // Refresh status after compression
        return response.data;
    };

    const handleCleanup = async () => {
        try {
            if (!confirm('期限切れのメモリを完全に削除しますか？この操作は取り消せません。')) return;
            await memoryApi.cleanupExpired();
            await fetchStatus();
            alert('クリーンアップが完了しました');
        } catch (err) {
            console.error('Cleanup failed:', err);
            alert('クリーンアップに失敗しました');
        }
    };

    if (loading && !status) {
        return (
            <div className="p-8 flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 text-center text-red-500">
                <p>{error}</p>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-4 text-blue-500 underline"
                >
                    再読み込み
                </button>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">メモリライフサイクル管理</h1>

            {status && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2">
                        <MemoryStatusCard status={status} />
                    </div>
                    <div className="space-y-6">
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="font-bold text-gray-800 mb-4">Actions</h3>
                            <CompressionButton onCompress={handleCompress} />

                            <button
                                onClick={handleCleanup}
                                className="w-full mt-4 border border-red-300 text-red-600 hover:bg-red-50 py-3 px-4 rounded-lg font-medium transition-colors"
                            >
                                期限切れを削除
                            </button>
                        </div>

                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-sm text-blue-800">
                            <p className="font-bold mb-2">💡 Tips</p>
                            <p>メモリ使用率が80%を超えると、システムパフォーマンスに影響する可能性があります。こまめな圧縮を推奨します。</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MemoryPage;
