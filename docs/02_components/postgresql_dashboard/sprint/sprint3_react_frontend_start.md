# Sprint 3: React フロントエンド 作業開始指示書

**対象**: Tsumu (Cursor) または実装担当者
**期間**: 5日間想定
**前提**: Sprint 1, 2 完了、FastAPI稼働中

---

## 1. Done Definition

### Tier 1: 必須
- [ ] Vite + React 18 + TypeScriptプロジェクト構築
- [ ] メッセージUI（送信・履歴表示）
- [ ] 仕様書管理画面（CRUD + Markdown）
- [ ] Intent一覧・詳細画面
- [ ] 通知システムUI
- [ ] FastAPI連携完了
- [ ] Dockerコンテナ化

### Tier 2: 品質
- [ ] Tailwind CSSによるモダンUI
- [ ] React Queryによる状態管理
- [ ] コンポーネントテスト10件以上
- [ ] レスポンシブデザイン
- [ ] エラー境界実装

---

## 2. 実装スケジュール（5日間）

### Day 1: プロジェクトセットアップ

**タスク1**: Viteプロジェクト作成
```bash
cd /Users/zero/Projects/resonant-engine
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

**タスク2**: 依存パッケージインストール
```bash
npm install @tanstack/react-query axios react-router-dom
npm install lucide-react react-markdown @tailwindcss/typography
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**タスク3**: Tailwind設定
```javascript
// tailwind.config.js
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [require('@tailwindcss/typography')],
}
```

**タスク4**: ディレクトリ構造
```bash
mkdir -p src/{api,components,pages,hooks,stores,types,utils}
mkdir -p src/components/{Layout,Messages,Specifications,Intents,Notifications}
```

**完了基準**:
- [ ] `npm run dev` で起動
- [ ] Tailwind動作確認
- [ ] ディレクトリ構造整備

---

### Day 2: レイアウトとルーティング

**タスク1**: React Router設定
```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import MessagesPage from './pages/MessagesPage';
import SpecificationsPage from './pages/SpecificationsPage';
import IntentsPage from './pages/IntentsPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<MessagesPage />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/specifications" element={<SpecificationsPage />} />
          <Route path="/intents" element={<IntentsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
```

**タスク2**: サイドバーレイアウト
```typescript
// src/components/Layout/Sidebar.tsx
import { MessageSquare, FileText, Target, Bell } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  const navItems = [
    { to: '/messages', icon: MessageSquare, label: 'Messages' },
    { to: '/specifications', icon: FileText, label: 'Specifications' },
    { to: '/intents', icon: Target, label: 'Intents' },
  ];

  return (
    <aside className="w-64 bg-gray-800 text-white p-4">
      <h1 className="text-xl font-bold mb-6">Resonant Dashboard</h1>
      <nav>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center p-2 rounded ${isActive ? 'bg-gray-700' : 'hover:bg-gray-700'}`
            }
          >
            <Icon className="mr-2 h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
```

**タスク3**: 通知ベルコンポーネント
```typescript
// src/components/Notifications/NotificationBell.tsx
import { Bell } from 'lucide-react';
import { useState } from 'react';

export default function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(3);
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button onClick={() => setIsOpen(!isOpen)} className="relative">
        <Bell className="h-6 w-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white shadow-lg rounded-lg">
          {/* 通知リスト */}
        </div>
      )}
    </div>
  );
}
```

**完了基準**:
- [ ] ルーティング動作
- [ ] サイドバーナビゲーション
- [ ] 通知ベルUI

---

### Day 3: APIクライアントとメッセージUI

**タスク1**: Axiosクライアント
```typescript
// src/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
});

export const messagesApi = {
  list: (params?: any) => api.get('/messages', { params }),
  get: (id: string) => api.get(`/messages/${id}`),
  create: (data: any) => api.post('/messages', data),
  update: (id: string, data: any) => api.put(`/messages/${id}`, data),
  delete: (id: string) => api.delete(`/messages/${id}`),
};
```

**タスク2**: React Query設定
```typescript
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
);
```

**タスク3**: メッセージリストコンポーネント
```typescript
// src/components/Messages/MessageList.tsx
import { useQuery } from '@tanstack/react-query';
import { messagesApi } from '../../api/client';

export default function MessageList() {
  const { data, isLoading } = useQuery({
    queryKey: ['messages'],
    queryFn: () => messagesApi.list({ limit: 50 }),
    refetchInterval: 5000, // 5秒ごとに更新
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      {data?.data.items.map((msg: any) => (
        <div key={msg.id} className={`p-4 rounded ${
          msg.message_type === 'user' ? 'bg-blue-100' :
          msg.message_type === 'yuno' ? 'bg-purple-100' :
          msg.message_type === 'kana' ? 'bg-green-100' : 'bg-gray-100'
        }`}>
          <div className="font-bold">{msg.message_type.toUpperCase()}</div>
          <div>{msg.content}</div>
          <div className="text-sm text-gray-500">{new Date(msg.created_at).toLocaleString()}</div>
        </div>
      ))}
    </div>
  );
}
```

**タスク4**: メッセージ入力コンポーネント
```typescript
// src/components/Messages/MessageInput.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { messagesApi } from '../../api/client';

export default function MessageInput() {
  const [content, setContent] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (content: string) => messagesApi.create({
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
        className="flex-1 border rounded p-2"
        placeholder="メッセージを入力..."
      />
      <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">
        送信
      </button>
    </form>
  );
}
```

**完了基準**:
- [ ] API接続成功
- [ ] メッセージ一覧表示
- [ ] メッセージ送信機能
- [ ] 自動更新動作

---

### Day 4: 仕様書とIntent画面

**タスク1**: 仕様書一覧画面
```typescript
// src/pages/SpecificationsPage.tsx
export default function SpecificationsPage() {
  const { data } = useQuery({
    queryKey: ['specifications'],
    queryFn: () => specificationsApi.list(),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Specifications</h1>
      <button className="bg-green-500 text-white px-4 py-2 rounded mb-4">
        + 新規作成
      </button>
      <div className="space-y-4">
        {data?.data.items.map((spec: any) => (
          <div key={spec.id} className="bg-white p-4 rounded shadow">
            <h2 className="text-lg font-bold">{spec.title}</h2>
            <div className="flex gap-2 mt-2">
              <span className={`px-2 py-1 rounded text-sm ${
                spec.status === 'draft' ? 'bg-yellow-100' :
                spec.status === 'review' ? 'bg-blue-100' : 'bg-green-100'
              }`}>
                {spec.status}
              </span>
              {spec.tags.map((tag: string) => (
                <span key={tag} className="px-2 py-1 bg-gray-100 rounded text-sm">
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**タスク2**: Markdownエディタ（簡易版）
```typescript
// src/components/Specifications/MarkdownEditor.tsx
import ReactMarkdown from 'react-markdown';
import { useState } from 'react';

export default function MarkdownEditor({ value, onChange }) {
  const [preview, setPreview] = useState(false);

  return (
    <div>
      <div className="flex gap-2 mb-2">
        <button onClick={() => setPreview(false)} className={!preview ? 'font-bold' : ''}>
          編集
        </button>
        <button onClick={() => setPreview(true)} className={preview ? 'font-bold' : ''}>
          プレビュー
        </button>
      </div>
      {preview ? (
        <div className="prose">
          <ReactMarkdown>{value}</ReactMarkdown>
        </div>
      ) : (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full h-96 border rounded p-2 font-mono"
        />
      )}
    </div>
  );
}
```

**タスク3**: Intent一覧画面
```typescript
// src/pages/IntentsPage.tsx
export default function IntentsPage() {
  const { data } = useQuery({
    queryKey: ['intents'],
    queryFn: () => intentsApi.list(),
  });

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Intents</h1>
      <div className="space-y-4">
        {data?.data.items.map((intent: any) => (
          <div key={intent.id} className="bg-white p-4 rounded shadow">
            <div className="flex justify-between">
              <span className={`px-2 py-1 rounded text-sm ${statusColors[intent.status]}`}>
                {intent.status.toUpperCase()}
              </span>
              <span className="text-sm">Priority: {intent.priority}</span>
            </div>
            <p className="mt-2">{intent.description}</p>
            <div className="text-sm text-gray-500 mt-2">
              Created: {new Date(intent.created_at).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**完了基準**:
- [ ] 仕様書一覧表示
- [ ] Markdownプレビュー
- [ ] Intent一覧表示
- [ ] ステータス別表示

---

### Day 5: Docker統合とテスト

**タスク1**: Dockerfile作成
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**タスク2**: nginx.conf
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
    }
}
```

**タスク3**: docker-compose.yml更新
```yaml
frontend:
  build: ../frontend
  container_name: resonant_frontend
  ports:
    - "3000:80"
  depends_on:
    - backend
  networks:
    - resonant_network
```

**タスク4**: 統合テスト
```bash
cd docker
docker-compose up --build -d
open http://localhost:3000
```

**完了基準**:
- [ ] Docker ビルド成功
- [ ] 全画面動作確認
- [ ] API通信成功
- [ ] Notion不要でダッシュボード操作可能

---

## 3. 完了報告書

1. **Done Definition達成**: Tier 1: X/7, Tier 2: X/5
2. **実装コンポーネント数**: X個
3. **API連携エンドポイント数**: X個
4. **性能**: 初回表示時間、再描画速度
5. **次のアクション**: Sprint 4への準備

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
