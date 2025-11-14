# Resonant Dashboard - 統合プラットフォーム設計書
## Notion + Slack + Backlog 統合アーキテクチャ

---

## 🎯 ビジョン

**「Slack的なUIで、Notion/Backlog/GitHubを統合操作できるダッシュボード」**

### ユーザー体験
```
宏啓: 「API設計レビューして」（メッセージ送信）
  ↓
システム: 処理中...（ステータス表示）
  ↓
通知: 「✅ レビュー完了」（ダッシュボードに通知）
  ↓
宏啓: 結果確認 → 追加指示
```

---

## 📊 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                  Resonant Dashboard                      │
│              （統合UI - Slack風メッセージング）            │
│                                                          │
│  [入力欄] 「API設計レビューして」                           │
│                                                          │
│  [メッセージ履歴]                                          │
│  👤 宏啓: API設計レビューして                               │
│  🤖 ユノ: 了解、カナに依頼します                            │
│  🤖 カナ: レビュー中...                                    │
│  ✅ 完了: Issue #123 作成しました                          │
│                                                          │
│  [通知]                                                   │
│  🔔 新しいIntent（3分前）                                  │
│  🔔 レビュー完了（1分前）                                   │
└─────────────────────────────────────────────────────────┘
           ↓ REST API / WebSocket
┌─────────────────────────────────────────────────────────┐
│              Resonant Engine (Backend)                   │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Intent      │  │ Yuno        │  │ Kana        │    │
│  │ Manager     │→ │ Interface   │→ │ Interface   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│         ↓               ↓                ↓              │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Adapter Layer                         │   │
│  │  Notion | Slack | Backlog | GitHub             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│               External Services                          │
│  [Notion DB] [Slack] [Backlog] [GitHub]                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🖥️ ダッシュボード UI 設計

### 画面構成

```
┌─────────────────────────────────────────────────┐
│  Resonant Dashboard                    [@宏啓] │
├─────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ホーム    │ │タスク    │ │設定     │           │
│  └─────────┘ └─────────┘ └─────────┘           │
├─────────────────────────────────────────────────┤
│  通知                                    [全既読] │
│  🔔 レビュー完了: API設計v1.2          (2分前)  │
│  🔔 新しいIntent: Backlog同期          (5分前)  │
├─────────────────────────────────────────────────┤
│  メッセージ                                       │
│  ┌─────────────────────────────────────────┐   │
│  │ 👤 宏啓 (10:00)                          │   │
│  │ API設計v1.2をレビューしてください          │   │
│  │                                          │   │
│  │ 🤖 ユノ (10:01)                          │   │
│  │ 了解しました。カナに依頼します             │   │
│  │ 予想所要時間: 3-5分                       │   │
│  │                                          │   │
│  │ 🤖 カナ (10:02)                          │   │
│  │ レビュー中... (進捗: 60%)                 │   │
│  │                                          │   │
│  │ ✅ システム (10:04)                       │   │
│  │ レビュー完了                              │   │
│  │ - GitHub Issue #123 作成                 │   │
│  │ - Notion更新完了                          │   │
│  │ [詳細を見る] [Issueを開く]               │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ メッセージを入力...                       │   │
│  └─────────────────────────────────────────┘   │
│                                     [送信]      │
└─────────────────────────────────────────────────┘
```

### 主要機能

1. **メッセージング**
   - 自然言語で依頼
   - Slack風のスレッド表示
   - リアルタイム更新（WebSocket）

2. **通知センター**
   - Intent発生通知
   - 処理完了通知
   - エラー通知
   - 既読管理

3. **タスク管理**
   - 進行中のタスク一覧
   - 完了履歴
   - Backlog連携

4. **統合ビュー**
   - Notion仕様書プレビュー
   - GitHub Issue埋め込み
   - Backlogチケット表示

---

## 🔧 技術スタック（提案）

### フロントエンド
```typescript
// React + TypeScript
// Tailwind CSS (Slack風UI)
// WebSocket (リアルタイム通信)

// 例: メッセージコンポーネント
interface Message {
  id: string;
  sender: 'user' | 'yuno' | 'kana' | 'system';
  content: string;
  timestamp: Date;
  status?: 'pending' | 'completed' | 'error';
  attachments?: Attachment[];
}

const MessageBubble: React.FC<{message: Message}> = ({message}) => {
  // Slack風の吹き出し表示
}
```

### バックエンド
```python
# FastAPI (REST API + WebSocket)
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.post("/api/message")
async def send_message(message: str):
    """メッセージ受信 → Intent生成"""
    intent = parse_message_to_intent(message)
    await process_intent(intent)
    return {"status": "processing"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """リアルタイム通知用"""
    await websocket.accept()
    # 通知をpush
```

### データベース
```
- PostgreSQL: メッセージ履歴、タスク管理
- Redis: リアルタイム状態管理
- 既存: Notion（仕様書バックエンド）
```

---

## 🔄 データフロー

### 1. メッセージ送信 → Intent生成

```
[ダッシュボード] 宏啓: 「API設計レビューして」
  ↓ POST /api/message
[Backend] Intent Manager
  ↓ 自然言語解析
{
  "intent": "review_spec",
  "query": "API設計",
  "requestor": "宏啓"
}
  ↓ Notion検索
spec_id = "abc123..."
  ↓ intent_protocol.json 書き込み
[resonant_daemon] 検知
```

### 2. 処理中の状態更新

```
[Backend] WebSocket push
  ↓
[ダッシュボード] 
「🤖 ユノ: 了解、カナに依頼します」
「🤖 カナ: レビュー中... 60%」
```

### 3. 完了通知

```
[Backend] 処理完了
  ↓ WebSocket push
[ダッシュボード] 通知
「✅ レビュー完了」
  ↓ クリック
詳細表示（GitHub Issue、Notionリンク）
```

---

## 🗂️ 各サービスの役割分担

| サービス | 役割 | アクセス方法 |
|---------|------|------------|
| **Notion** | 仕様書・ドキュメント保管 | ダッシュボードから参照のみ |
| **Slack** | 外部通知（オプション） | Webhook経由で通知転送 |
| **Backlog** | タスク・チケット管理 | API経由で同期 |
| **GitHub** | コード・Issue管理 | API経由でIssue作成 |
| **Dashboard** | **統合UI** | メイン操作画面 |

### Notionの新しい位置づけ
```
❌ 以前: メインUI（テーブル直接編集）
✅ 今後: バックエンドストレージ（ダッシュボードから操作）
```

---

## 📋 実装ロードマップ

### Phase 1: 基盤構築（2週間）
- [ ] FastAPI バックエンドセットアップ
- [ ] PostgreSQL/Redis セットアップ
- [ ] 既存デーモン連携（Intent Manager）
- [ ] REST API設計・実装

### Phase 2: ダッシュボードUI（2週間）
- [ ] React + Tailwind セットアップ
- [ ] メッセージUIコンポーネント
- [ ] 通知センター実装
- [ ] WebSocket接続

### Phase 3: Intent処理統合（1週間）
- [ ] 自然言語 → Intent 変換
- [ ] Notion/GitHub/Backlog Adapter
- [ ] Yuno/Kana Interface実装

### Phase 4: 高度な機能（2週間）
- [ ] Slack連携（通知転送）
- [ ] タスク管理機能
- [ ] 履歴検索・フィルター
- [ ] ダッシュボード統計表示

### Phase 5: 運用・改善（継続）
- [ ] パフォーマンス最適化
- [ ] エラーハンドリング強化
- [ ] ユーザーフィードバック反映

**総所要時間: 約6-8週間**

---

## 💬 自然言語 → Intent 変換例

### 入力パターンと対応Intent

```python
# 例1: レビュー依頼
入力: 「API設計v1.2をレビューして」
Intent: {
  "type": "review_spec",
  "target": "API設計v1.2",
  "action": "create_github_issue"
}

# 例2: タスク作成
入力: 「認証機能の実装タスクをBacklogに追加」
Intent: {
  "type": "create_task",
  "service": "backlog",
  "title": "認証機能の実装",
  "assignee": null
}

# 例3: 状態確認
入力: 「進行中のタスクを見せて」
Intent: {
  "type": "query_tasks",
  "status": "in_progress"
}

# 例4: Notion検索
入力: 「決済関連の仕様書ある？」
Intent: {
  "type": "search_notion",
  "query": "決済",
  "database": "specs"
}
```

---

## 🔐 セキュリティ・認証

### 考慮事項
- JWT認証
- API Key管理（Notion/GitHub/Backlog）
- WebSocket認証
- CORS設定

### 環境変数
```bash
# .env
NOTION_API_KEY=...
GITHUB_TOKEN=...
BACKLOG_API_KEY=...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET=...
```

---

## 📊 データモデル

### メッセージ
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY,
  thread_id UUID,
  sender TEXT, -- 'user', 'yuno', 'kana', 'system'
  content TEXT,
  intent_id UUID REFERENCES intents(id),
  created_at TIMESTAMP
);
```

### Intent
```sql
CREATE TABLE intents (
  id UUID PRIMARY KEY,
  type TEXT,
  data JSONB,
  status TEXT, -- 'pending', 'processing', 'completed', 'error'
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);
```

### 通知
```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  user_id TEXT,
  title TEXT,
  body TEXT,
  link TEXT,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP
);
```

---

## 🎯 成功指標

### ユーザー体験
- [ ] メッセージ送信から結果通知まで平均5分以内
- [ ] ダッシュボードでの操作完結率 80%以上
- [ ] 通知の見逃し率 10%以下

### 技術指標
- [ ] API応答時間 < 200ms
- [ ] WebSocket遅延 < 100ms
- [ ] システム稼働率 99.9%

### ビジネス指標
- [ ] Notion直接編集の頻度 50%削減
- [ ] タスク管理の一元化達成
- [ ] 宏啓さんの満足度 😊

---

## 🚀 最初の一歩

### MVP（Minimum Viable Product）

**実装する最小機能:**
1. ✅ メッセージ送信UI
2. ✅ Intent生成
3. ✅ 処理状態表示
4. ✅ 完了通知

**実装しない（Phase 2以降）:**
- ❌ Slack連携
- ❌ 高度な検索
- ❌ 統計・分析
- ❌ モバイル対応

### デモシナリオ
```
1. ダッシュボードで「API設計レビューして」入力
2. システムが「処理中...」表示
3. 3分後に「完了しました」通知
4. GitHub Issueリンクをクリックして確認
```

---

## 📝 次のステップ

### 宏啓さんに確認したいこと

1. **ダッシュボードの実装方針**
   - Web アプリケーション（ブラウザで開く）
   - デスクトップアプリ（Electron等）
   - どちらを優先？

2. **最初に実装したい機能**
   - 「API設計レビュー」のフロー
   - それとも別のユースケース？

3. **既存ツールの活用**
   - Slackは実際に使う？（通知のみ？）
   - Backlogは既に運用中？

4. **開発リソース**
   - ツム（Cursor）でフロントエンド開発可能？
   - それとも外部開発者が必要？

この設計を元に、段階的に実装を進めましょう！
