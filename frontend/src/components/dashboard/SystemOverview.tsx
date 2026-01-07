import React from 'react';
import type { SystemOverview as SystemOverviewType } from '../../types';

interface SystemOverviewProps {
    data: SystemOverviewType;
}

const SystemOverview: React.FC<SystemOverviewProps> = ({ data }) => {
    // Status counts from distribution
    const pending = data.status_distribution?.pending || 0;
    const completed = data.status_distribution?.completed || 0;

    // Completion rate
    const total = data.total_intents || 0;
    const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;

    // Correction rate percentage
    const correctionPercent = Math.round((data.correction_rate || 0) * 100);

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-bold text-gray-800">システム概要</h2>
                <span className="text-xs text-gray-500">
                    Last: {new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-center">
                    <span className="text-xs text-gray-500 block mb-1">総Intent数</span>
                    <span className="text-2xl font-bold text-gray-800">{total}</span>
                </div>
                <div className="bg-green-50 p-4 rounded-lg border border-green-100 text-center">
                    <span className="text-xs text-gray-500 block mb-1">完了率</span>
                    <span className="text-2xl font-bold text-gray-800">{completionRate}%</span>
                    <span className="text-xs text-gray-400 block">{completed} / {total}</span>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100 text-center">
                    <span className="text-xs text-gray-500 block mb-1">処理待ち</span>
                    <span className="text-2xl font-bold text-gray-800">{pending}</span>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg border border-purple-100 text-center">
                    <span className="text-xs text-gray-500 block mb-1">修正率</span>
                    <span className="text-2xl font-bold text-gray-800">{correctionPercent}%</span>
                </div>
            </div>

            <div className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-600 mb-3">最近のアクティビティ</h3>
                <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                        <span className="text-2xl font-bold text-blue-600">{data.recent_activity?.last_hour || 0}</span>
                        <span className="text-xs text-gray-500 block">過去1時間</span>
                    </div>
                    <div className="text-center">
                        <span className="text-2xl font-bold text-blue-600">{data.recent_activity?.last_24h || 0}</span>
                        <span className="text-xs text-gray-500 block">過去24時間</span>
                    </div>
                    <div className="text-center">
                        <span className="text-2xl font-bold text-blue-600">{data.recent_activity?.last_7d || 0}</span>
                        <span className="text-xs text-gray-500 block">過去7日間</span>
                    </div>
                </div>
            </div>

            <div className="border-t pt-4 mt-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <span className="text-sm text-gray-600 mr-2">WebSocket接続:</span>
                        <span className="font-medium">{data.active_websockets || 0}</span>
                    </div>
                    <div className="flex items-center">
                        <span className="text-sm text-gray-600 mr-2">平均処理時間:</span>
                        <span className="font-medium">{data.avg_processing_time_ms || 0}ms</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SystemOverview;
