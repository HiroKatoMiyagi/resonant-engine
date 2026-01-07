import React, { useState } from 'react';
import type { ModificationRequest, TemporalConstraintCheck } from '../../types/temporalConstraint';

interface ConstraintCheckFormProps {
    onCheck: (data: ModificationRequest) => Promise<TemporalConstraintCheck>;
}

const ConstraintCheckForm: React.FC<ConstraintCheckFormProps> = ({ onCheck }) => {
    const [filePath, setFilePath] = useState('');
    const [modType, setModType] = useState<'edit' | 'delete' | 'rename'>('edit');
    const [reason, setReason] = useState('');
    const [isChecking, setIsChecking] = useState(false);
    const [result, setResult] = useState<TemporalConstraintCheck | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!filePath || !reason) return;

        try {
            setIsChecking(true);
            setResult(null);
            const res = await onCheck({
                user_id: 'user', // context
                file_path: filePath,
                modification_type: modType,
                modification_reason: reason,
                requested_by: 'user'
            });
            setResult(res);
        } catch (err) {
            console.error('Check failed:', err);
        } finally {
            setIsChecking(false);
        }
    };

    const getLevelColor = (level: string) => {
        switch (level) {
            case 'critical': return 'bg-red-100 text-red-800';
            case 'high': return 'bg-orange-100 text-orange-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-blue-100 text-blue-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getResultColor = (res: string) => {
        switch (res) {
            case 'approved': return 'text-green-600';
            case 'rejected': return 'text-red-600';
            case 'pending': return 'text-yellow-600';
            default: return 'text-gray-600';
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Constraint Check</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">ファイルパス</label>
                    <input
                        type="text"
                        value={filePath}
                        onChange={(e) => setFilePath(e.target.value)}
                        className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        placeholder="/app/services/..."
                        required
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">変更タイプ</label>
                    <div className="flex space-x-4">
                        {(['edit', 'delete', 'rename'] as const).map(type => (
                            <label key={type} className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="modType"
                                    value={type}
                                    checked={modType === type}
                                    onChange={(e) => setModType(e.target.value as any)}
                                    className="text-blue-600"
                                />
                                <span className="capitalize">{type}</span>
                            </label>
                        ))}
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">変更理由</label>
                    <textarea
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        rows={3}
                        className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        placeholder="変更の理由を入力してください..."
                        required
                    />
                </div>

                <button
                    type="submit"
                    disabled={isChecking || !filePath || !reason}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                    {isChecking ? 'チェック中...' : 'チェック実行'}
                </button>
            </form>

            {result && (
                <div className="mt-6 border-t pt-4">
                    <h3 className="font-medium text-gray-900 mb-2">Check Result</h3>
                    <div className="bg-gray-50 rounded p-4 text-sm space-y-2">
                        <div className="flex items-center justify-between">
                            <span className={`font-bold uppercase ${getResultColor(result.check_result)}`}>
                                {result.check_result}
                            </span>
                            <span className={`px-2 py-1 text-xs font-bold rounded uppercase ${getLevelColor(result.constraint_level)}`}>
                                {result.constraint_level}
                            </span>
                        </div>

                        {result.warning_message && (
                            <div className="text-orange-700 bg-orange-50 p-2 rounded border border-orange-100">
                                ⚠ {result.warning_message}
                            </div>
                        )}

                        {result.required_actions.length > 0 && (
                            <div>
                                <span className="text-gray-600 font-semibold">Required Actions:</span>
                                <ul className="list-disc list-inside text-gray-700 pl-2">
                                    {result.required_actions.map((action, i) => <li key={i}>{action}</li>)}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ConstraintCheckForm;
