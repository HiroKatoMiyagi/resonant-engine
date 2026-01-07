import React, { useState } from 'react';
import type { TimelineEntry } from '../../types';

interface TimelineChartProps {
    data: TimelineEntry[] | null;
    onGranularityChange?: (granularity: 'minute' | 'hour' | 'day') => void;
}

const TimelineChart: React.FC<TimelineChartProps> = ({ data, onGranularityChange }) => {
    const [granularity, setGranularity] = useState<'minute' | 'hour' | 'day'>('hour');

    const entries = Array.isArray(data) ? data : [];
    const maxCount = Math.max(...entries.map(e => e.count), 1);

    const handleGranularityChange = (g: 'minute' | 'hour' | 'day') => {
        setGranularity(g);
        onGranularityChange?.(g);
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-bold text-gray-800">アクティビティタイムライン</h2>
                <div className="flex bg-gray-100 rounded p-1">
                    {(['minute', 'hour', 'day'] as const).map((g) => (
                        <button
                            key={g}
                            onClick={() => handleGranularityChange(g)}
                            className={`px-3 py-1 text-xs rounded capitalize ${granularity === g
                                ? 'bg-white shadow text-blue-600 font-medium'
                                : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            {g === 'minute' ? '分' : g === 'hour' ? '時' : '日'}
                        </button>
                    ))}
                </div>
            </div>

            <div className="relative h-64 border-l border-b border-gray-200 p-4">
                {entries.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        アクティビティはありません
                    </div>
                ) : (
                    <div className="flex items-end justify-around h-full gap-1">
                        {entries.slice(-24).map((entry, index) => (
                            <div key={index} className="flex flex-col items-center flex-1 max-w-8">
                                <div
                                    className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-colors"
                                    style={{
                                        height: `${(entry.count / maxCount) * 100}%`,
                                        minHeight: entry.count > 0 ? '4px' : '0'
                                    }}
                                    title={`${entry.count} events`}
                                />
                                <span className="text-xs text-gray-400 mt-1 truncate w-full text-center">
                                    {new Date(entry.time).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            <div className="mt-2 text-right text-xs text-gray-400">
                Total Events: {entries.reduce((sum, e) => sum + e.count, 0)}
            </div>
        </div>
    );
};

export default TimelineChart;
