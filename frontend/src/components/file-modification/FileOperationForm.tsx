import React, { useState } from 'react';
import type { FileModificationRequest, FileModificationResult, Operation } from '../../types/fileModification';

interface FileOperationFormProps {
    onExecute: (data: FileModificationRequest) => Promise<FileModificationResult>;
    onCheck: (data: FileModificationRequest) => Promise<any>;
}

const FileOperationForm: React.FC<FileOperationFormProps> = ({ onExecute, onCheck }) => {
    const [operation, setOperation] = useState<Operation>('read');
    const [filePath, setFilePath] = useState('');
    const [content, setContent] = useState('');
    const [newPath, setNewPath] = useState('');
    const [reason, setReason] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState(false);
    const [result, setResult] = useState<FileModificationResult | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!filePath) return;
        if ((operation === 'write' || operation === 'delete') && !reason) {
            alert('変更理由を入力してください');
            return;
        }
        if (operation === 'delete' && !confirmDelete) {
            alert('削除確認チェックを入れてください');
            return;
        }

        try {
            setIsProcessing(true);
            setResult(null);
            const res = await onExecute({
                user_id: 'user',
                file_path: filePath,
                operation,
                content: operation === 'write' ? content : undefined,
                new_path: operation === 'rename' ? newPath : undefined,
                reason,
                requested_by: 'user'
            });
            setResult(res);
            if (res.success && operation !== 'read') {
                setContent('');
                setReason('');
            }
        } catch (err) {
            console.error('Operation failed:', err);
            alert('操作に失敗しました');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleCheck = async () => {
        // Simple check trigger, could be improved to show inline validation
        try {
            const res = await onCheck({
                user_id: 'user', file_path: filePath, operation, reason, requested_by: 'user'
            });
            alert(`Check Result: ${res.check_result}\nLevel: ${res.constraint_level}\n${res.warning_message || ''}`);
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">File Operation</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">操作タイプ</label>
                    <div className="flex space-x-4">
                        {(['read', 'write', 'rename', 'delete'] as const).map(op => (
                            <label key={op} className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="operation"
                                    value={op}
                                    checked={operation === op}
                                    onChange={(e) => setOperation(e.target.value as Operation)}
                                    className="text-blue-600"
                                />
                                <span className="capitalize">{op}</span>
                            </label>
                        ))}
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">ファイルパス</label>
                    <input
                        type="text"
                        value={filePath}
                        onChange={(e) => setFilePath(e.target.value)}
                        className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                        placeholder="/app/config/settings.py"
                        required
                    />
                </div>

                {operation === 'rename' && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">新しいパス</label>
                        <input
                            type="text"
                            value={newPath}
                            onChange={(e) => setNewPath(e.target.value)}
                            className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                            placeholder="/app/config/new_settings.py"
                        />
                    </div>
                )}

                {operation === 'write' && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">コンテンツ</label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            rows={6}
                            className="block w-full border border-gray-300 rounded-md shadow-sm p-2 font-mono text-xs"
                            placeholder="# File content..."
                        />
                    </div>
                )}

                {operation !== 'read' && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            操作理由 <span className="text-red-500 text-xs">*必須</span>
                        </label>
                        <textarea
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            rows={2}
                            className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
                            placeholder="変更の理由を入力してください..."
                        />
                        <p className="text-xs text-gray-500 mt-1">※ MEDIUM: 20文字以上、HIGH: 50文字以上が必要</p>
                    </div>
                )}

                {operation === 'delete' && (
                    <div className="flex items-center">
                        <input
                            id="confirm-delete"
                            type="checkbox"
                            checked={confirmDelete}
                            onChange={(e) => setConfirmDelete(e.target.checked)}
                            className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        />
                        <label htmlFor="confirm-delete" className="ml-2 block text-sm text-red-700 font-bold">
                            削除を確認しました（元に戻せません）
                        </label>
                    </div>
                )}

                <div className="flex space-x-3 pt-2">
                    {operation !== 'read' && (
                        <button
                            type="button"
                            onClick={handleCheck}
                            className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                        >
                            制約チェック
                        </button>
                    )}
                    <button
                        type="submit"
                        disabled={isProcessing || !filePath}
                        className={`flex-1 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white disabled:opacity-50 ${operation === 'delete' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
                            }`}
                    >
                        {isProcessing ? '実行中...' : '実行'}
                    </button>
                </div>
            </form>

            {result && (
                <div className={`mt-4 p-4 rounded border text-sm ${result.success ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
                    }`}>
                    <p className="font-bold">{result.success ? '成功' : '失敗'}</p>
                    <p>{result.message}</p>
                    {result.backup_path && <p className="text-xs mt-1 text-gray-500">Backup: {result.backup_path}</p>}
                </div>
            )}
        </div>
    );
};

export default FileOperationForm;
