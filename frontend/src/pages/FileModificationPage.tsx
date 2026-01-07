import React, { useEffect, useState } from 'react';
import FileOperationForm from '../components/file-modification/FileOperationForm';
import OperationLogTable from '../components/file-modification/OperationLogTable';
import { fileModificationApi } from '../api/fileModification';
import type { FileModificationRequest, FileModificationResult, OperationLogsResult } from '../types/fileModification';

const FileModificationPage: React.FC = () => {
    const [logs, setLogs] = useState<OperationLogsResult>({ total: 0, logs: [] });
    const [loadingLogs, setLoadingLogs] = useState(false);

    const fetchLogs = async () => {
        try {
            setLoadingLogs(true);
            const res = await fileModificationApi.getLogs({ user_id: 'user', limit: 20 });
            setLogs(res.data);
        } catch (err) {
            console.error('Failed to fetch logs:', err);
        } finally {
            setLoadingLogs(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, []);

    const handleExecute = async (data: FileModificationRequest): Promise<FileModificationResult> => {
        let res;
        switch (data.operation) {
            case 'write': res = await fileModificationApi.write(data); break;
            case 'delete': res = await fileModificationApi.delete(data); break;
            case 'rename': res = await fileModificationApi.rename(data); break;
            default: throw new Error('Invalid operation for execute');
        }
        // Refresh logs after operation
        await fetchLogs();
        return res.data;
    };

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">ファイル操作サービス</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1">
                    <FileOperationForm
                        onExecute={handleExecute}
                        onCheck={(data) => fileModificationApi.check(data).then(res => res.data)}
                    />

                    <div className="bg-blue-50 p-4 rounded text-sm text-blue-800 border-blue-100">
                        <p className="font-bold mb-2">Security Note</p>
                        <p>すべての操作は制約チェックを通過する必要があります。重要なファイルへの操作はブロックされる場合があります。</p>
                    </div>
                </div>

                <div className="lg:col-span-2">
                    {loadingLogs && logs.total === 0 ? (
                        <div className="flex justify-center p-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        </div>
                    ) : (
                        <OperationLogTable data={logs} />
                    )}
                </div>
            </div>
        </div>
    );
};

export default FileModificationPage;
