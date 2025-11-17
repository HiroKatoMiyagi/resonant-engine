import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { intentsApi } from '../api/client';
import { Plus, Eye, Trash2 } from 'lucide-react';
import type { Intent } from '../types';

export default function IntentsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState(5);
  const [selectedIntent, setSelectedIntent] = useState<Intent | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['intents'],
    queryFn: () => intentsApi.list({ limit: 50 }),
    refetchInterval: 5000,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      intentsApi.create({
        description,
        priority,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intents'] });
      setShowCreate(false);
      setDescription('');
      setPriority(5);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => intentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intents'] });
    },
  });

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const statusIcons = {
    pending: '🟡',
    processing: '🔵',
    completed: '✅',
    failed: '❌',
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  const intents = data?.data.items || [];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Intents</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
        >
          <Plus className="h-5 w-5 mr-2" />
          New Intent
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Create New Intent</h2>
          <div className="space-y-4">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Intent description..."
              className="w-full border rounded p-2 h-32"
            />
            <div>
              <label className="block text-sm font-medium mb-1">
                Priority: {priority}
              </label>
              <input
                type="range"
                min="0"
                max="10"
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => createMutation.mutate()}
                disabled={!description.trim()}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
              >
                Create Intent
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedIntent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-lg font-semibold">Intent Details</h2>
              <button
                onClick={() => setSelectedIntent(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="font-medium">Status:</label>
                <span className={`ml-2 px-2 py-1 rounded text-sm ${statusColors[selectedIntent.status]}`}>
                  {selectedIntent.status.toUpperCase()}
                </span>
              </div>
              <div>
                <label className="font-medium">Priority:</label>
                <span className="ml-2">{selectedIntent.priority}</span>
              </div>
              <div>
                <label className="font-medium block">Description:</label>
                <p className="mt-1 text-gray-700">{selectedIntent.description}</p>
              </div>
              {selectedIntent.result && (
                <div>
                  <label className="font-medium block">Result:</label>
                  <pre className="mt-1 bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                    {JSON.stringify(selectedIntent.result, null, 2)}
                  </pre>
                </div>
              )}
              <div>
                <label className="font-medium">Created:</label>
                <span className="ml-2">
                  {new Date(selectedIntent.created_at).toLocaleString()}
                </span>
              </div>
              {selectedIntent.processed_at && (
                <div>
                  <label className="font-medium">Processed:</label>
                  <span className="ml-2">
                    {new Date(selectedIntent.processed_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {intents.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No intents yet</div>
        ) : (
          intents.map((intent) => (
            <div key={intent.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex justify-between items-start">
                <div className="flex items-center">
                  <span className="text-xl mr-2">{statusIcons[intent.status]}</span>
                  <span className={`px-2 py-1 rounded text-sm ${statusColors[intent.status]}`}>
                    {intent.status.toUpperCase()}
                  </span>
                  <span className="ml-4 text-sm text-gray-600">
                    Priority: {intent.priority}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedIntent(intent)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(intent.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <p className="mt-2 text-gray-800">{intent.description}</p>
              <div className="text-sm text-gray-500 mt-2">
                Created: {new Date(intent.created_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
