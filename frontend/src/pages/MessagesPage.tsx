import MessageList from '../components/Messages/MessageList';
import MessageInput from '../components/Messages/MessageInput';

export default function MessagesPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Messages</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <MessageList />
        <div className="mt-4 pt-4 border-t">
          <MessageInput />
        </div>
      </div>
    </div>
  );
}
