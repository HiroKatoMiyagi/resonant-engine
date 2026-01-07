import React, { useState } from 'react';
import type { AnalyzeRequest, AnalyzeResult } from '../../types/termDrift';

interface TermAnalyzeFormProps {
    onAnalyze: (data: AnalyzeRequest) => Promise<AnalyzeResult>;
}

const TermAnalyzeForm: React.FC<TermAnalyzeFormProps> = ({ onAnalyze }) => {
    const [text, setText] = useState('');
    const [source, setSource] = useState('document');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState<AnalyzeResult | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!text.trim()) return;

        try {
            setIsAnalyzing(true);
            setResult(null);
            const res = await onAnalyze({
                user_id: 'user', // TODO: context
                text,
                source
            });
            setResult(res);
        } catch (err) {
            console.error('Analysis failed:', err);
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Term Analysis</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Source Type</label>
                    <select
                        value={source}
                        onChange={(e) => setSource(e.target.value)}
                        className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-2 border"
                    >
                        <option value="document">Document</option>
                        <option value="chat">Chat Log</option>
                        <option value="specification">Specification</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Text to Analyze</label>
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        rows={4}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
                        placeholder="ここに分析したいテキストを入力してください..."
                    />
                </div>

                <button
                    type="submit"
                    disabled={!text.trim() || isAnalyzing}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                    {isAnalyzing ? '分析中...' : '分析'}
                </button>
            </form>

            {result && (
                <div className="mt-6 border-t pt-4">
                    <h3 className="font-medium text-gray-900 mb-2">Analysis Result</h3>
                    <div className="bg-gray-50 rounded p-4 text-sm">
                        <p>Analyzed Terms: {result.analyzed_terms}</p>
                        <p className={result.drifts_detected > 0 ? 'text-red-600 font-bold' : 'text-green-600'}>
                            Drifts Detected: {result.drifts_detected}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TermAnalyzeForm;
