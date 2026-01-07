import React from 'react';
import ConstraintCheckForm from '../components/temporal-constraint/ConstraintCheckForm';
import VerificationRegisterForm from '../components/temporal-constraint/VerificationRegisterForm';
import { temporalConstraintApi } from '../api/temporalConstraint';

const TemporalConstraintPage: React.FC = () => {
    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">時間的制約とファイルの安定性</h1>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                    <ConstraintCheckForm onCheck={(data) => temporalConstraintApi.check(data).then(res => res.data)} />

                    <div className="mt-6 bg-yellow-50 p-4 rounded-lg border border-yellow-100 text-sm text-yellow-800">
                        <h3 className="font-bold mb-2">制約レベルについて</h3>
                        <ul className="list-disc list-inside space-y-1">
                            <li><span className="font-semibold">Critical:</span> コアシステム。変更は原則禁止。</li>
                            <li><span className="font-semibold">High:</span> 重要な機能。十分なテストと承認が必要。</li>
                            <li><span className="font-semibold">Medium:</span> 通常の機能。テスト実行を推奨。</li>
                            <li><span className="font-semibold">Low:</span> 頻繁に変更されるファイル。</li>
                        </ul>
                    </div>
                </div>

                <div>
                    <VerificationRegisterForm onRegister={(params) => temporalConstraintApi.verify(params).then(res => res.data)} />

                    <div className="mt-6 bg-white p-6 rounded-lg shadow">
                        <h3 className="font-bold text-gray-800 mb-4">Quick Actions</h3>
                        <div className="space-y-3">
                            <button className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded border border-transparent hover:border-gray-200 transition-colors text-sm text-gray-700">
                                📄 制約レベル一覧を表示 (Coming Soon)
                            </button>
                            <button className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded border border-transparent hover:border-gray-200 transition-colors text-sm text-gray-700">
                                🛡️ Stableとしてマーク (Coming Soon)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TemporalConstraintPage;
