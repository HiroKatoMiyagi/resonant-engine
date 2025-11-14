# Resonant Platform - クラウドネイティブ設計書
## セルフホスト → Oracle Cloud → AWS 移行戦略

---

## 🎯 設計思想

### 3つの前提
1. **Notionは一時的**：将来は自前DBに移行
2. **段階的移行**：個人利用 → Oracle Cloud → AWS
3. **サービス化前提**：最初から拡張性を考慮

### アーキテクチャの原則
- **クラウドポータブル**：特定サービスに依存しない
- **データ主権**：Notionからの脱却
- **水平スケール**：ユーザー増加に対応
- **コスト最適化**：Oracle Free Tier活用

---

## 📊 3段階移行アーキテクチャ

### Phase 1: セルフホスト（現在）

```
┌─────────────────────────────────────┐
│  Mac (localhost)                    │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ Resonant Dashboard           │  │
│  │ - React (localhost:3000)     │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ FastAPI (localhost:8000)     │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ SQLite (resonant.db)         │  │
│  │ - すべてのデータ              │  │
│  │ - Notionはキャッシュ          │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
         ↓ API（必要時のみ）
    ┌──────────┐
    │ Notion   │ ← 一時的なストレージ
    └──────────┘
```

**コスト: $0（Notion無料枠）**

---

### Phase 2: Oracle Cloud（中期）

```
┌─────────────────────────────────────────────────┐
│  Oracle Cloud Free Tier                         │
│  https://resonant.example.com                   │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Compute Instance (Always Free)           │  │
│  │ - Ampere A1 (4 OCPU, 24GB RAM)          │  │
│  │                                          │  │
│  │  ├─ Resonant Dashboard (Docker)         │  │
│  │  ├─ FastAPI (Docker)                    │  │
│  │  └─ Nginx (リバースプロキシ)            │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Autonomous Database (Always Free)        │  │
│  │ - PostgreSQL互換                         │  │
│  │ - 20GB ストレージ                         │  │
│  │ - 自動バックアップ                        │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Object Storage (20GB Always Free)        │  │
│  │ - ファイル・画像保存                      │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**コスト: $0（Oracle Free Tierのみ）**

**Oracle Free Tierの内容:**
- Compute: Ampere A1 (4 OCPU, 24GB RAM) × 永久無料
- Database: Autonomous DB 20GB × 2インスタンス × 永久無料
- Storage: Object Storage 20GB × 永久無料
- Network: 10TB/月 アウトバウンド × 永久無料

**十分な性能:**
- 同時ユーザー: 100-500人対応可能
- ストレージ: 数万件のタスク・メッセージ保存可能

---

### Phase 3: AWS（将来・サービス公開）

```
┌─────────────────────────────────────────────────────┐
│  AWS (Multi-Region)                                 │
│  https://app.resonant.io                            │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ CloudFront (CDN)                             │  │
│  │ - 静的アセット配信                            │  │
│  │ - DDoS防御                                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ ECS Fargate (コンテナオーケストレーション)    │  │
│  │                                              │  │
│  │  ├─ Dashboard (Frontend)                    │  │
│  │  │   - Auto Scaling (2-20インスタンス)      │  │
│  │  │                                          │  │
│  │  └─ API (Backend)                           │  │
│  │      - Auto Scaling (4-50インスタンス)      │  │
│  │      - Load Balancer                        │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ RDS PostgreSQL (Multi-AZ)                    │  │
│  │ - プライマリDB（読み書き）                     │  │
│  │ - スタンバイDB（自動フェイルオーバー）          │  │
│  │ - Read Replica × 2（読み取り専用）            │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ ElastiCache Redis (Cluster Mode)             │  │
│  │ - セッション管理                              │  │
│  │ - キャッシュ                                  │  │
│  │ - リアルタイム通知                            │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ S3 + CloudFront                              │  │
│  │ - ファイルストレージ                          │  │
│  │ - バックアップ                                │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Cognito (認証)                               │  │
│  │ - マルチテナント対応                          │  │
│  │ - SSO対応                                    │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**コスト見積もり（月間1,000ユーザー想定）:**
- ECS Fargate: $100-200
- RDS PostgreSQL: $50-100
- ElastiCache: $30-50
- CloudFront + S3: $20-30
- Cognito: $10-20
- **合計: $210-400/月**

（ユーザー課金で十分ペイ可能）

---

## 🗄️ データベース設計（移行前提）

### Notion依存を排除したスキーマ

```sql
-- ユーザー（マルチテナント対応）
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  organization_id UUID,  -- Phase 3で使用
  created_at TIMESTAMP
);

-- 組織（Phase 3: マルチテナント）
CREATE TABLE organizations (
  id UUID PRIMARY KEY,
  name TEXT,
  plan TEXT,  -- 'free', 'pro', 'enterprise'
  created_at TIMESTAMP
);

-- 仕様書（Notionの代替）
CREATE TABLE specs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  content JSONB,  -- Markdown + metadata
  status TEXT,
  sync_trigger BOOLEAN DEFAULT FALSE,
  notion_page_id TEXT,  -- Phase 1のみ使用（後で削除）
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- メッセージ
CREATE TABLE messages (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  thread_id UUID,
  sender TEXT,
  content TEXT,
  intent_id UUID,
  created_at TIMESTAMP
);

-- Intent
CREATE TABLE intents (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  type TEXT,
  data JSONB,
  status TEXT,
  source TEXT,  -- 'notion', 'message', 'api'
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- タスク（Backlogの代替）
CREATE TABLE tasks (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  spec_id UUID REFERENCES specs(id),
  title TEXT,
  description TEXT,
  status TEXT,  -- 'todo', 'in_progress', 'done'
  priority TEXT,  -- 'low', 'medium', 'high'
  assignee_id UUID REFERENCES users(id),
  backlog_issue_id TEXT,  -- Phase 1のみ使用
  due_date TIMESTAMP,
  created_at TIMESTAMP
);
```

### 移行戦略

**Phase 1 → Phase 2:**
```python
# Notionデータを自前DBに移行
def migrate_from_notion():
    notion_specs = fetch_all_notion_specs()
    for spec in notion_specs:
        db_spec = {
            'title': spec['name'],
            'content': convert_notion_to_markdown(spec),
            'notion_page_id': spec['id'],  # 参照用に保持
            'status': spec['status']
        }
        insert_spec(db_spec)
```

**Phase 2 → Phase 3:**
```python
# SQLite → PostgreSQL 移行
# pg_dump/pg_restoreで簡単に移行可能
# スキーマ構造は同じなので変更不要
```

---

## 🐳 Docker化（移行準備）

### Dockerfile
```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/resonant
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:80"

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=your_password

volumes:
  postgres_data:
```

**利点:**
- ローカル開発環境と本番環境が同じ
- Oracle Cloud / AWSにそのままデプロイ可能
- 開発者の環境差異を吸収

---

## 💰 コスト比較（3段階）

| Phase | 環境 | 月額コスト | 対応ユーザー数 |
|-------|------|----------|--------------|
| 1. セルフホスト | Mac | $0 | 1人（宏啓さん） |
| 2. Oracle Cloud | OCI Free Tier | $0 | 100-500人 |
| 3. AWS | 本格運用 | $200-400 | 1,000-10,000人 |

### Phase 2（Oracle Cloud）の詳細

**無料で使える内容:**
```
Compute:
- Ampere A1: 4 OCPU, 24GB RAM (永久無料)
- AMD VM: 1/8 OCPU (月750時間無料)

Database:
- Autonomous Database: 20GB × 2個 (永久無料)
- 自動バックアップ・暗号化・パッチ適用

Storage:
- Object Storage: 20GB (永久無料)
- Block Volume: 200GB (永久無料)

Network:
- Outbound: 10TB/月 (永久無料)
- Load Balancer: 1個 (永久無料)
```

**これだけで数百ユーザー対応可能！**

### コスト削減のポイント

1. **Phase 2を長く使う**
   - Oracle Free Tierだけで500人まで対応
   - 課金せずにサービス検証可能

2. **AWS移行は慎重に**
   - 本当にスケールが必要になってから
   - Reserved Instanceで30-50%削減

3. **適材適所**
   - 静的コンテンツ: Cloudflare (無料CDN)
   - 認証: Auth0 Free Tier or 自前実装
   - メール: SendGrid Free Tier

---

## 🔄 段階的移行プラン

### Step 1: セルフホスト（今から2週間）
```
✅ 完全にローカルで動作
✅ Notionは「キャッシュ」として使用
✅ 全データはSQLiteに保存
✅ Docker化完了
```

**成果物:**
- 動作するダッシュボード
- Intent処理の自動化
- メッセージング機能

---

### Step 2: Oracle Cloud移行（2週間後-1ヶ月）
```
✅ Oracle Cloud Freeアカウント作成
✅ Compute Instanceセットアップ
✅ Autonomous Database作成
✅ Dockerイメージデプロイ
✅ HTTPS設定（Let's Encrypt）
```

**移行作業:**
1. SQLiteデータをPostgreSQLにエクスポート
2. Docker Composeで一括デプロイ
3. DNS設定（独自ドメイン or サブドメイン）
4. 動作確認

**所要時間: 1-2日**

---

### Step 3: サービス公開準備（1ヶ月後-3ヶ月）
```
✅ マルチテナント機能実装
✅ 認証システム（ログイン・登録）
✅ サブスクリプション機能（オプション）
✅ 管理画面
✅ ドキュメント整備
```

---

### Step 4: AWS移行（必要に応じて）
```
✅ ユーザー数が500人突破
✅ レスポンス速度の問題発生
✅ Oracle Free Tierの限界
→ AWS移行を検討
```

---

## 🎯 アーキテクチャの要点

### クラウドポータブル設計

**絶対に使わないもの:**
- ❌ AWS Lambda（他クラウドに移行不可）
- ❌ DynamoDB（AWS専用）
- ❌ Oracle専用機能

**使うもの（標準技術）:**
- ✅ Docker（どこでも動く）
- ✅ PostgreSQL（全クラウド対応）
- ✅ Redis（全クラウド対応）
- ✅ REST API（標準）

### データ主権

**Notionからの脱却:**
```
Phase 1: Notion = メインストレージ
         自前DB = キャッシュ

Phase 2: 自前DB = メインストレージ
         Notion = 連携オプション

Phase 3: 自前DB = 完全独立
         Notion = 不使用
```

### スケールアウト戦略

**水平スケール（ユーザー増加対応）:**
```
1台のサーバー
  ↓ ユーザー増加
複数台のサーバー + Load Balancer
  ↓ さらに増加
Auto Scaling + Read Replica
  ↓ グローバル展開
Multi-Region + CDN
```

---

## 📋 実装ロードマップ（改訂版）

### Week 1-2: 基盤構築
- [ ] FastAPI + SQLite セットアップ
- [ ] React ダッシュボード実装
- [ ] 基本的なメッセージング機能
- [ ] Intent生成・処理
- [ ] Docker化

### Week 3-4: 機能拡充
- [ ] Notion連携（段階的に自前DBへ）
- [ ] GitHub/Backlog連携
- [ ] 通知システム
- [ ] リアルタイム更新（WebSocket）

### Week 5-6: Oracle Cloud移行準備
- [ ] PostgreSQL対応
- [ ] データマイグレーションツール
- [ ] 環境変数・設定管理
- [ ] CI/CDパイプライン

### Week 7-8: Oracle Cloud デプロイ
- [ ] OCI環境構築
- [ ] 本番デプロイ
- [ ] HTTPS設定
- [ ] 監視・ログ設定

### Month 3-6: サービス化
- [ ] マルチテナント対応
- [ ] 認証・認可
- [ ] サブスクリプション
- [ ] 管理画面

---

## 🎯 次のアクション

宏啓さん、以下を確認させてください：

1. **Phase 1（セルフホスト）の期間**
   - 2週間程度で移行準備？
   - それとももっとじっくり？

2. **Oracle Cloudアカウント**
   - 既にお持ちですか？
   - それとも新規作成から？

3. **ドメイン**
   - 独自ドメインを用意しますか？
   - それとも後回し？

4. **最初に実装する機能**
   - 「仕様書レビュー」フロー
   - それとも別のユースケース？

この方針で進めてよければ、Phase 1の詳細設計に入ります！
