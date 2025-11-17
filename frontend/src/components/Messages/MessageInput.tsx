import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { messagesApi } from '../../api/client';
import { Send } from 'lucide-react';

export default function MessageInput() {
  const [content, setContent] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (content: string) =>
      messagesApi.create({
        user_id: 'hiroki',
        content,
        message_type: 'user',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
      setContent('');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (content.trim()) {
      mutation.mutate(content);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="flex-1 border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        placeholder="メッセージを入力..."
        disabled={mutation.isPending}
      />
      <button
        type="submit"
        disabled={!content.trim() || mutation.isPending}
        className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
      >
        <Send className="h-5 w-5" />
      </button>
    </form>
  );
}
