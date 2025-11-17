# Resonant Dashboard - Docker Environment

## 概要

Resonant EngineのWebダッシュボードシステムを支えるDocker Compose環境です。

### 主な機能
- PostgreSQL 15によるデータ永続化
- 4つのコアテーブル（messages, specifications, intents, notifications）
- ヘルスチェック機能
- 開発用ヘルパースクリプト

## クイックスタート

### 前提条件
- Docker 20.10以上
- Docker Compose V2以上
- ポート5432が空いていること

### セットアップ

1. 環境変数を設定
```bash
cd docker
cp .env.example .env
vim .env  # POSTGRES_PASSWORDを設定
```

2. 起動
```bash
./scripts/start.sh
```

3. ヘルスチェック
```bash
./scripts/check-health.sh
```

### よく使うコマンド

```bash
# ログ確認
docker-compose logs -f postgres

# psql接続
docker-compose exec postgres psql -U resonant -d resonant_dashboard

# 停止
./scripts/stop.sh

# 完全リセット（データ削除）
docker-compose down -v
```

## データベーススキーマ

### messages
Slack風メッセージ管理

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| user_id | VARCHAR | ユーザーID |
| content | TEXT | メッセージ内容 |
| message_type | VARCHAR | user/yuno/kana/system |
| metadata | JSONB | 追加情報 |
| created_at | TIMESTAMP | 作成日時 |

### specifications
仕様書管理（Notion代替）

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| title | VARCHAR | タイトル |
| content | TEXT | Markdown内容 |
| version | INTEGER | バージョン |
| status | VARCHAR | draft/review/approved |
| tags | TEXT[] | タグ配列 |

### intents
Intent管理

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| description | TEXT | Intent説明 |
| status | VARCHAR | pending/processing/completed/failed |
| priority | INTEGER | 優先度 |
| result | JSONB | 処理結果 |

### notifications
通知システム

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| user_id | VARCHAR | ユーザーID |
| title | VARCHAR | 通知タイトル |
| is_read | BOOLEAN | 既読フラグ |
| notification_type | VARCHAR | info/success/warning/error |

## トラブルシューティング

### ポート競合
```bash
# .envでポート変更
POSTGRES_PORT=5433
```

### パスワードエラー
```bash
# .envのPOSTGRES_PASSWORDを確認
cat .env | grep POSTGRES_PASSWORD
```

### データ永続化テスト
```bash
# データ挿入
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "INSERT INTO messages (user_id, content) VALUES ('test', 'persistence test');"

# 再起動
./scripts/stop.sh
./scripts/start.sh

# データ確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT * FROM messages WHERE content = 'persistence test';"
```

## 次のステップ

このSprint完了後:
- Sprint 2: FastAPI バックエンドAPI実装
- Sprint 3: React フロントエンド実装
- Sprint 4: Intent自動処理統合
- Sprint 5: Oracle Cloud デプロイ

---

**作成日**: 2025-11-17
**作成者**: Kana (Claude Sonnet 4.5)
