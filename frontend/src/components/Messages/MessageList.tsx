import { useQuery } from '@tanstack/react-query';
import { messagesApi } from '../../api/client';
import type { Message } from '../../types';

export default function MessageList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['messages'],
    queryFn: () => messagesApi.list({ limit: 50 }),
    refetchInterval: 5000,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">メッセージを読み込んでいます...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
        メッセージの読み込みに失敗しました
      </div>
    );
  }

  const messages = data?.data.items || [];

  const getMessageStyle = (type: Message['message_type']) => {
    switch (type) {
      case 'user':
        return 'bg-blue-50 border-blue-200';
      case 'yuno':
        return 'bg-purple-50 border-purple-200';
      case 'kana':
        return 'bg-green-50 border-green-200';
      case 'system':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-white border-gray-200';
    }
  };

  const getTypeLabel = (type: Message['message_type']): string => {
    switch (type) {
      case 'user':
        return 'USER';
      case 'yuno':
        return 'YUNO';
      case 'kana':
        return 'KANA';
      case 'system':
        return 'SYSTEM';
    }
  };

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 py-8">メッセージはまだありません</div>
      ) : (
        messages.map((msg) => (
          <div
            key={msg.id}
            className={`p-4 rounded-lg border ${getMessageStyle(msg.message_type)}`}
          >
            <div className="flex justify-between items-start mb-2">
              <span className="font-bold text-sm">{getTypeLabel(msg.message_type)}</span>
              <span className="text-xs text-gray-500">
                {new Date(msg.created_at).toLocaleString()}
              </span>
            </div>
            <div className="text-gray-800 whitespace-pre-wrap">{msg.content}</div>
          </div>
        ))
      )}
    </div>
  );
}
