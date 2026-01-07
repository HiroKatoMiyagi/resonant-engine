import React from 'react';
import type { MemoryStatus } from '../../types';

interface MemoryStatusCardProps {
    status: MemoryStatus;
}

const MemoryStatusCard: React.FC<MemoryStatusCardProps> = ({ status }) => {
    const usagePercent = (status.usage_ratio || 0) * 100;

    const getUsageColor = (percentage: number) => {
        if (percentage >= 95) return 'bg-red-500';
        if (percentage >= 80) return 'bg-orange-500';
        return 'bg-blue-500';
    };

    const usageColor = getUsageColor(usagePercent);

    // Convert bytes to MB for display
    const sizeMB = (status.total_size_bytes || 0) / (1024 * 1024);

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-bold text-gray-800">メモリ状態</h2>
                <span className={`px-2 py-1 text-xs font-bold rounded ${usagePercent >= 80 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    }`}>
                    使用率: {usagePercent.toFixed(1)}%
                </span>
            </div>

            <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>ストレージ使用量</span>
                    <span>{status.total_count} / {status.limit} items</span>
                </div>
                <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        data-testid="usage-bar"
                        className={`h-full ${usageColor} transition-all duration-500`}
                        style={{ width: `${Math.min(usagePercent, 100)}%` }}
                    />
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-blue-50 p-3 rounded border border-blue-100">
                    <span className="text-xs text-gray-500 block mb-1">アクティブ</span>
                    <span className="text-xl font-bold text-blue-800">{status.active_count.toLocaleString()}</span>
                </div>
                <div className="bg-purple-50 p-3 rounded border border-purple-100">
                    <span className="text-xs text-gray-500 block mb-1">アーカイブ</span>
                    <span className="text-xl font-bold text-purple-800">{status.archive_count.toLocaleString()}</span>
                </div>
                <div className="bg-gray-50 p-3 rounded border border-gray-200">
                    <span className="text-xs text-gray-500 block mb-1">合計</span>
                    <span className="text-xl font-bold text-gray-800">{status.total_count.toLocaleString()}</span>
                </div>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-100 text-xs text-gray-500">
                <div>データサイズ: {sizeMB.toFixed(2)} MB</div>
            </div>
        </div>
    );
};

export default MemoryStatusCard;
