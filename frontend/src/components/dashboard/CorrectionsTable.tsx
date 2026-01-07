import React from 'react';
import type { CorrectionsResponse } from '../../types';

interface CorrectionsTableProps {
    data: CorrectionsResponse | null;
}

const CorrectionsTable: React.FC<CorrectionsTableProps> = ({ data }) => {
    const corrections = data?.corrections || [];
    const count = data?.count || 0;

    return (
        <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-bold text-gray-800">修正履歴</h2>
            </div>

            {corrections.length === 0 ? (
                <div className="p-6 text-center text-gray-500 text-sm">
                    修正履歴なし
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Intent ID
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    修正回数
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    最新の修正
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {corrections.map((correction, index) => (
                                <tr key={correction.intent_id || index} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="text-sm font-mono text-gray-600">
                                            {correction.intent_id?.slice(0, 8) || 'N/A'}...
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                            {correction.correction_count}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        <div className="max-w-xs truncate">
                                            {correction.last_correction || '-'}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-end items-center">
                <span className="text-xs text-gray-900 font-medium">
                    Total: {count}
                </span>
            </div>
        </div>
    );
};

export default CorrectionsTable;
