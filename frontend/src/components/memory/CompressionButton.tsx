import React, { useState } from 'react';
import type { CompressionResult } from '../../types';

interface CompressionButtonProps {
    onCompress: () => Promise<CompressionResult>;
}

const CompressionButton: React.FC<CompressionButtonProps> = ({ onCompress }) => {
    const [isCompressing, setIsCompressing] = useState(false);
    const [result, setResult] = useState<CompressionResult | null>(null);

    const handleCompress = async () => {
        try {
            setIsCompressing(true);
            setResult(null);
            const res = await onCompress();
            setResult(res);
        } catch (err) {
            console.error('Compression failed:', err);
        } finally {
            setIsCompressing(false);
        }
    };

    return (
        <div className="mt-4">
            <button
                onClick={handleCompress}
                disabled={isCompressing}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 px-4 rounded-lg font-medium shadow transition-colors disabled:opacity-50 flex justify-center items-center"
            >
                {isCompressing ? (
                    <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        処理中 (圧縮実行)...
                    </>
                ) : (
                    'メモリ圧縮を実行'
                )}
            </button>

            {result && (
                <div className="mt-4 bg-green-50 border border-green-200 rounded p-4 text-sm text-green-800">
                    <p className="font-bold mb-1">圧縮完了</p>
                    <ul className="list-disc list-inside">
                        <li>{result.compressed_count} 件のメモリを圧縮しました</li>
                        <li>{result.space_saved_mb.toFixed(2)} MB の空き容量を確保しました</li>
                    </ul>
                </div>
            )}
        </div>
    );
};

export default CompressionButton;
