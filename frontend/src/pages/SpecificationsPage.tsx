import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { specificationsApi } from '../api/client';
import { Plus, Edit, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Specification } from '../types';

export default function SpecificationsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [previewMode, setPreviewMode] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['specifications'],
    queryFn: () => specificationsApi.list({ limit: 50 }),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      specificationsApi.create({
        title,
        content,
        tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['specifications'] });
      setShowCreate(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (id: string) =>
      specificationsApi.update(id, {
        title,
        content,
        tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['specifications'] });
      setEditingId(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => specificationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['specifications'] });
    },
  });

  const resetForm = () => {
    setTitle('');
    setContent('');
    setTags('');
    setPreviewMode(false);
  };

  const handleEdit = (spec: Specification) => {
    setEditingId(spec.id);
    setTitle(spec.title);
    setContent(spec.content);
    setTags(spec.tags.join(', '));
    setShowCreate(false);
  };

  const statusColors = {
    draft: 'bg-yellow-100 text-yellow-800',
    review: 'bg-blue-100 text-blue-800',
    approved: 'bg-green-100 text-green-800',
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  const specs = data?.data.items || [];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Specifications</h1>
        <button
          onClick={() => {
            setShowCreate(true);
            setEditingId(null);
            resetForm();
          }}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center"
        >
          <Plus className="h-5 w-5 mr-2" />
          New Specification
        </button>
      </div>

      {(showCreate || editingId) && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">
            {editingId ? 'Edit Specification' : 'Create New Specification'}
          </h2>
          <div className="space-y-4">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Title"
              className="w-full border rounded p-2"
            />
            <div>
              <div className="flex gap-2 mb-2">
                <button
                  onClick={() => setPreviewMode(false)}
                  className={`px-3 py-1 rounded ${!previewMode ? 'bg-gray-200' : ''}`}
                >
                  Edit
                </button>
                <button
                  onClick={() => setPreviewMode(true)}
                  className={`px-3 py-1 rounded ${previewMode ? 'bg-gray-200' : ''}`}
                >
                  Preview
                </button>
              </div>
              {previewMode ? (
                <div className="prose max-w-none border rounded p-4 min-h-[200px] bg-gray-50">
                  <ReactMarkdown>{content}</ReactMarkdown>
                </div>
              ) : (
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Content (Markdown)"
                  className="w-full border rounded p-2 h-48 font-mono"
                />
              )}
            </div>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Tags (comma separated)"
              className="w-full border rounded p-2"
            />
            <div className="flex gap-2">
              <button
                onClick={() =>
                  editingId ? updateMutation.mutate(editingId) : createMutation.mutate()
                }
                disabled={!title || !content}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
              >
                {editingId ? 'Update' : 'Create'}
              </button>
              <button
                onClick={() => {
                  setShowCreate(false);
                  setEditingId(null);
                  resetForm();
                }}
                className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {specs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No specifications yet</div>
        ) : (
          specs.map((spec) => (
            <div key={spec.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start">
                <h2 className="text-lg font-semibold">{spec.title}</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(spec)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Edit className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(spec.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                <span className={`px-2 py-1 rounded text-sm ${statusColors[spec.status]}`}>
                  {spec.status}
                </span>
                <span className="text-sm text-gray-500">v{spec.version}</span>
                {spec.tags.map((tag) => (
                  <span key={tag} className="px-2 py-1 bg-gray-100 rounded text-sm">
                    #{tag}
                  </span>
                ))}
              </div>
              <div className="text-sm text-gray-500 mt-2">
                Updated: {new Date(spec.updated_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
