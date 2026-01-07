import React, { useEffect, useState } from 'react';
import { dashboardApi } from '../api/client';
import SystemOverview from '../components/dashboard/SystemOverview';
import TimelineChart from '../components/dashboard/TimelineChart';
import CorrectionsTable from '../components/dashboard/CorrectionsTable';
import type {
    SystemOverview as SystemOverviewType,
    TimelineEntry,
    CorrectionsResponse
} from '../types';

const DashboardPage: React.FC = () => {
    const [overview, setOverview] = useState<SystemOverviewType | null>(null);
    const [timeline, setTimeline] = useState<TimelineEntry[] | null>(null);
    const [corrections, setCorrections] = useState<CorrectionsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [granularity, setGranularity] = useState<'minute' | 'hour' | 'day'>('hour');

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                // 並列でデータ取得
                const [overviewRes, timelineRes, correctionsRes] = await Promise.all([
                    dashboardApi.getOverview(),
                    dashboardApi.getTimeline(granularity),
                    dashboardApi.getCorrections()
                ]);

                setOverview(overviewRes.data);
                // Timeline API returns array directly
                setTimeline(Array.isArray(timelineRes.data) ? timelineRes.data : []);
                setCorrections(correctionsRes.data);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch dashboard data:', err);
                setError('データの読み込みに失敗しました。');
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, [granularity]);

    if (loading && !overview) {
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
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">システムダッシュボード</h1>

            {overview && <SystemOverview data={overview} />}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <TimelineChart
                        data={timeline}
                        onGranularityChange={setGranularity}
                    />
                </div>
                <div className="lg:col-span-1">
                    <div className="bg-white p-6 rounded-lg shadow h-full flex flex-col justify-center items-center text-gray-400">
                        <span className="block text-4xl mb-2">📊</span>
                        <span>Analytics Widgets Coming Soon</span>
                    </div>
                </div>
            </div>

            <CorrectionsTable data={corrections} />
        </div>
    );
};

export default DashboardPage;
