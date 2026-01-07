import React from 'react';
import type { OperationLogsResult } from '../../types/fileModification';

interface OperationLogTableProps {
    data: OperationLogsResult;
}

const OperationLogTable: React.FC<OperationLogTableProps> = ({ data }) => {
    const getResultColor = (res: string) => {
        switch (res) {
            case 'approved': return 'text-green-600';
            case 'rejected': return 'text-red-600';
            case 'blocked': return 'text-red-800 font-bold';
            default: return 'text-gray-600';
        }
    };

    return (
        <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-lg font-bold text-gray-800">Operation Logs</h2>
                <span className="text-sm text-gray-500">Total: {data.total}</span>
            </div>

            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Operation</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File Path</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {data.logs.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">ログはありません</td>
                            </tr>
                        ) : (
                            data.logs.map(log => (
                                <tr key={log.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(log.created_at).toLocaleString('ja-JP')}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 uppercase">
                                        {log.operation}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500 font-mono">
                                        {log.file_path}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <span className={getResultColor(log.result)}>{log.result}</span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={log.reason}>
                                        {log.reason}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default OperationLogTable;
