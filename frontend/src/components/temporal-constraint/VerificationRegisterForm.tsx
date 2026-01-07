import React, { useState } from 'react';
import type { ConstraintLevel, VerificationRegisterResult } from '../../types/temporalConstraint';

interface VerificationRegisterFormProps {
    onRegister: (params: any) => Promise<VerificationRegisterResult>;
}

const VerificationRegisterForm: React.FC<VerificationRegisterFormProps> = ({ onRegister }) => {
    const [filePath, setFilePath] = useState('');
    const [verType, setVerType] = useState('unit_test');
    const [level, setLevel] = useState<ConstraintLevel>('medium');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [result, setResult] = useState<VerificationRegisterResult | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!filePath) return;

        try {
            setIsSubmitting(true);
            setResult(null);
            const res = await onRegister({
                user_id: 'user',
                file_path: filePath,
                verification_type: verType,
                constraint_level: level,
                verified_by: 'user'
            });
            setResult(res);
            setFilePath(''); // Clear on success
        } catch (err) {
            console.error('Registration failed:', err);
            alert('登録に失敗しました');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Register Verification</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">ファイルパス</label>
                    <input
                        type="text"
                        value={filePath}
                        onChange={(e) => setFilePath(e.target.value)}
                        className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        required
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">検証タイプ</label>
                        <select
                            value={verType}
                            onChange={(e) => setVerType(e.target.value)}
                            className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        >
                            <option value="unit_test">Unit Test</option>
                            <option value="integration_test">Integration Test</option>
                            <option value="e2e_test">E2E Test</option>
                            <option value="manual_review">Manual Review</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">制約レベル</label>
                        <select
                            value={level}
                            onChange={(e) => setLevel(e.target.value as ConstraintLevel)}
                            className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                        </select>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isSubmitting || !filePath}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
                >
                    {isSubmitting ? '登録中...' : '検証を登録'}
                </button>
            </form>

            {result && (
                <div className="mt-4 p-4 bg-green-50 text-green-800 text-sm rounded border border-green-200">
                    登録成功: ID {result.verification_id}
                </div>
            )}
        </div>
    );
};

export default VerificationRegisterForm;
