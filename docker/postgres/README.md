# Resonant Engine PostgreSQL Schema Management

## ファイル構成

```
docker/postgres/
├── schema.sql                         # ✅ 最新の完全スキーマ（新規環境構築用）
├── init.sql                           # ⚠️ 旧版（削除予定）
└── migrations/                        # 📚 履歴参照用（本番稼働後に使用）
    ├── 002_intent_notify.sql
    ├── 003_message_notify.sql
    ├── 004_claude_code_tables.sql
    ├── 005_user_profile_tables.sql
    ├── 006_choice_points_initial.sql
    ├── 007_choice_preservation_completion.sql
    └── 008_contradiction_detection.sql
```

## スキーマ管理方針

### 現在（開発フェーズ）: 統合スキーマ方式

**使用するファイル**: `schema.sql`

- 新規環境構築時は`schema.sql`のみを実行
- すべてのテーブル定義が1ファイルに統合
- バージョン管理: `schema_version`テーブルで追跡

**理由**:
- 開発中は頻繁にDBを再構築する
- 「現在のあるべき姿」が一目でわかる
- Docker環境でクリーンスタートが容易

### 将来（本番稼働後）: マイグレーション方式

**使用するファイル**: `migrations/`ディレクトリ

- 本番データベースには`schema.sql`でデプロイ
- 以降の変更は`migrations/`にファイル追加
- ロールバック可能な安全なデプロイ

## 新規環境構築手順

### 方法1: Docker Compose（推奨）

```bash
cd /Users/zero/Projects/resonant-engine/docker
docker compose down -v  # 既存データ削除
docker compose up -d
```

`docker-compose.yml`の設定で`schema.sql`が自動実行されます。

### 方法2: 手動実行

```bash
# PostgreSQL起動
docker compose up -d postgres

# スキーマ適用
docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard \
  < /docker-entrypoint-initdb.d/schema.sql
```

## スキーマ確認

### 現在のテーブル一覧

```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\dt"
```

### 特定テーブルの定義確認

```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\d choice_points"
```

### スキーマバージョン確認

```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard \
  -c "SELECT * FROM schema_version ORDER BY applied_at DESC"
```

期待される結果:
```
 version | applied_at | description
---------+------------+-----------------------------------
 2.0.0   | 2025-11-30 | Complete schema - Backend API...
```

## テーブル一覧（v2.0.0）

| テーブル名 | 説明 | 主要カラム |
|-----------|------|-----------|
| `messages` | メッセージシステム | user_id, content, message_type |
| `specifications` | 仕様書管理 | title, content, status, tags |
| `intents` | Intent管理 | source, type, data, status |
| `corrections` | 修正履歴 | intent_id, source, diff |
| `notifications` | 通知システム | user_id, title, is_read |
| `contradictions` | 矛盾検出 | new_intent_id, contradiction_type |
| `intent_relations` | Intent関係性 | source_intent_id, relation_type |
| `choice_points` | 選択保存 | question, choices, tags |
| `memories` | メモリシステム | content, embedding, memory_type |
| `user_profiles` | ユーザープロファイル | user_id, persistent_context |

## マイグレーションファイルについて

### 現状の問題

`migrations/`ディレクトリのファイルは**開発途中で作成された増分変更**です。

**問題点**:
- `006`と`007`で重複定義がある
- `init.sql`との関係が不明確
- 全ファイルを順番に実行しても正しいスキーマにならない可能性

### 解決策

`schema.sql`を**信頼できる唯一の情報源（Single Source of Truth）**とし、マイグレーションファイルは**履歴参照用のみ**とします。

## スキーマ変更時のルール

### 開発中（現在）

1. `schema.sql`を直接編集
2. `schema_version`テーブルのバージョンを更新
3. コミット前に`schema.sql`で環境再構築して動作確認

```bash
# 変更後の確認手順
cd docker
docker compose down -v
docker compose up -d
# テスト実行
```

### 本番稼働後（将来）

1. `migrations/`に新規ファイル作成（例: `010_add_feature_x.sql`）
2. 本番環境にマイグレーション適用
3. `schema.sql`も同じ内容で更新（整合性維持）

## トラブルシューティング

### 問題: テーブルが存在しない

```bash
# schema.sqlが実行されたか確認
docker exec resonant_postgres psql -U resonant -d resonant_dashboard \
  -c "SELECT version FROM schema_version"
```

バージョンが表示されない場合:
```bash
# 手動でschema.sql実行
docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard \
  < docker/postgres/schema.sql
```

### 問題: init.sqlとschema.sqlどちらが使われている？

```bash
# docker-compose.ymlを確認
grep -A 5 "postgres:" docker/docker-compose.yml
```

`volumes`セクションで`schema.sql`がマウントされているか確認。

### 問題: マイグレーションファイルを実行すべき？

**答え**: NO

開発中は`schema.sql`のみ使用。マイグレーションファイルは実行不要。

## 参考資料

- PostgreSQL公式ドキュメント: https://www.postgresql.org/docs/
- pgvector: https://github.com/pgvector/pgvector
- Docker PostgreSQL: https://hub.docker.com/_/postgres

---

**作成日**: 2025-11-30
**最終更新**: 2025-11-30
**管理者**: Resonant Engine開発チーム
