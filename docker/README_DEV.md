# Resonant Engine - Docker Development Environment

**作成日**: 2025-11-21  
**更新日**: 2025-11-21  
**バージョン**: 1.0.0

---

## 📋 概要

このディレクトリには、Resonant Engineの開発環境を構築・管理するためのDocker設定が含まれています。

### 環境構成
- **PostgreSQL 15**: データベース（全マイグレーション適用済み）
- **Python 3.11**: 開発コンテナ（pytest, asyncpg等インストール済み）
- **ボリュームマウント**: ソースコードとテストの自動同期

---

## 🚀 クイックスタート

### 1. 環境起動

```bash
# プロジェクトルートから実行
./docker/scripts/start-dev.sh
```

または手動で：

```bash
cd docker
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d
```

### 2. テスト実行

```bash
# 全テスト実行
docker exec resonant_dev pytest tests/

# Sprint 11 矛盾検出テスト
docker exec resonant_dev pytest tests/contradiction/ -v

# Sprint 10 Choice Preservationテスト
docker exec resonant_dev pytest tests/memory/ -v

# 特定のテストファイル
docker exec resonant_dev pytest tests/contradiction/test_models.py -v

# カバレッジ付き実行
docker exec resonant_dev pytest tests/contradiction/ --cov=bridge.contradiction --cov-report=html
```

### 3. コンテナ内でシェル実行

```bash
docker exec -it resonant_dev bash
```

### 4. 環境停止

```bash
cd docker
docker-compose -f docker-compose.dev.yml down
```

---

## 📁 ディレクトリ構造

```
docker/
├── docker-compose.dev.yml      # 開発環境のDocker Compose設定
├── docker-compose.yml           # 本番環境のDocker Compose設定
├── Dockerfile.dev               # 開発用Dockerfile
├── .env.dev                     # 開発環境の環境変数
├── .env.example                 # 環境変数のテンプレート
├── README.md                    # 本番環境のREADME
├── README_DEV.md                # このファイル（開発環境のREADME）
├── postgres/                    # PostgreSQLマイグレーション
│   ├── init.sql                 # 初期スキーマ
│   ├── 002_intent_notify.sql   # Intent通知トリガー
│   ├── 003_message_notify.sql  # Message通知トリガー
│   ├── 004_claude_code_tables.sql
│   ├── 005_user_profile_tables.sql
│   ├── 006_choice_points_initial.sql      # Sprint 8: Choice Points初期作成
│   ├── 006_memory_lifecycle_tables.sql
│   ├── 007_choice_preservation_completion.sql  # Sprint 10: Choice拡張
│   ├── 008_contradiction_detection.sql    # Sprint 11: 矛盾検出
│   └── 008_intents_migration.sql
└── scripts/                     # 管理スクリプト
    ├── start-dev.sh             # 開発環境起動
    ├── start.sh                 # 本番環境起動
    ├── stop.sh                  # 環境停止
    ├── reset-db.sh              # データベースリセット
    └── check-health.sh          # ヘルスチェック
```

---

## 🔧 環境設定

### 環境変数 (.env.dev)

```bash
# PostgreSQL設定
POSTGRES_USER=resonant
POSTGRES_PASSWORD=password
POSTGRES_DB=postgres
POSTGRES_PORT=5432

# API設定
API_PORT=8000

# Claude API（テスト時に実際のAPIを使用する場合）
ANTHROPIC_API_KEY=your_api_key_here

# デバッグ設定
DEBUG=true
LOG_LEVEL=DEBUG
```

### ポート設定

| サービス | ポート | 説明 |
|---------|--------|------|
| PostgreSQL | 5432 | データベース |
| API | 8000 | FastAPI開発サーバー |

---

## 🗄️ データベース管理

### マイグレーション実行

開発環境起動時に自動的に`postgres/`ディレクトリ内の全SQLファイルが実行されます。

手動でマイグレーションを実行する場合：

```bash
# 特定のマイグレーションファイルを実行
docker exec -i resonant_postgres_dev psql -U resonant -d postgres < docker/postgres/008_contradiction_detection.sql

# 全マイグレーションを再実行
docker exec -i resonant_postgres_dev psql -U resonant -d postgres < docker/postgres/init.sql
```

### データベース接続

```bash
# psqlで接続
docker exec -it resonant_postgres_dev psql -U resonant -d postgres

# テーブル一覧
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "\dt"

# 特定のテーブル確認
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "SELECT * FROM contradictions LIMIT 5;"
```

### データベースリセット

```bash
./docker/scripts/reset-db.sh
```

---

## 🧪 テスト実行ガイド

### テスト環境の特徴

1. **実際のPostgreSQL使用**: モックではなく、Docker内のPostgreSQLを使用
2. **自動マウント**: ソースコードとテストが自動的にマウントされる
3. **高速実行**: コンテナ内で実行されるため高速

### テストカテゴリ

#### Sprint 11: Contradiction Detection (矛盾検出)

```bash
# 全テスト (48件)
docker exec resonant_dev pytest tests/contradiction/ -v

# モデルテスト (18件)
docker exec resonant_dev pytest tests/contradiction/test_models.py -v

# Detectorテスト (20件)
docker exec resonant_dev pytest tests/contradiction/test_detector.py -v

# 統合テスト (10件)
docker exec resonant_dev pytest tests/contradiction/test_integration.py -v
```

**実行結果** (2025-11-21):
- ✅ 48/48 テスト成功
- ⚠️ 2 warnings (Pydantic deprecation)

#### Sprint 10: Choice Preservation

```bash
# 全テスト
docker exec resonant_dev pytest tests/memory/ -v

# モデルテスト
docker exec resonant_dev pytest tests/memory/test_models.py -v

# サービステスト
docker exec resonant_dev pytest tests/memory/test_service.py -v

# クエリエンジンテスト
docker exec resonant_dev pytest tests/memory/test_choice_query_engine.py -v
```

**実行結果** (2025-11-21):
- ✅ 85/94 テスト成功
- ❌ 9 テスト失敗 (モック関連)

#### その他のテスト

```bash
# Context Assemblerテスト
docker exec resonant_dev pytest tests/context_assembler/ -v

# Intent Bridgeテスト
docker exec resonant_dev pytest tests/intent_bridge/ -v

# 統合テスト
docker exec resonant_dev pytest tests/integration/ -v
```

### テストオプション

```bash
# 詳細出力
docker exec resonant_dev pytest tests/contradiction/ -v

# 失敗時のみ詳細表示
docker exec resonant_dev pytest tests/contradiction/ -v --tb=short

# 特定のテストクラス
docker exec resonant_dev pytest tests/contradiction/test_models.py::TestContradictionModel -v

# 特定のテストメソッド
docker exec resonant_dev pytest tests/contradiction/test_models.py::TestContradictionModel::test_contradiction_with_all_fields -v

# カバレッジレポート
docker exec resonant_dev pytest tests/contradiction/ --cov=bridge.contradiction --cov-report=term-missing

# HTMLカバレッジレポート
docker exec resonant_dev pytest tests/contradiction/ --cov=bridge.contradiction --cov-report=html
# レポートは /app/htmlcov/index.html に生成される
```

---

## 🐛 トラブルシューティング

### ポート競合エラー

```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**解決方法**:
```bash
# 既存のコンテナを停止
docker stop resonant_backend resonant_frontend resonant_intent_bridge resonant_message_bridge

# または全て停止
docker stop $(docker ps -q)
```

### PostgreSQL接続エラー

```
Error: could not connect to server
```

**解決方法**:
```bash
# PostgreSQLコンテナの状態確認
docker ps | grep postgres

# ヘルスチェック
docker exec resonant_postgres_dev pg_isready -U resonant -d postgres

# ログ確認
docker logs resonant_postgres_dev
```

### テストファイルが見つからない

```
ERROR: file or directory not found: tests/contradiction/
```

**解決方法**:
```bash
# ボリュームマウントの確認
docker exec resonant_dev ls -la /app/tests/

# コンテナ再起動
docker-compose -f docker/docker-compose.dev.yml restart dev
```

### マイグレーションエラー

```
ERROR: relation "choice_points" does not exist
```

**解決方法**:
```bash
# 必要なマイグレーションを実行
docker exec -i resonant_postgres_dev psql -U resonant -d postgres < docker/postgres/006_choice_points_initial.sql

# または全マイグレーション再実行
./docker/scripts/reset-db.sh
```

---

## 📊 データベーススキーマ

### 主要テーブル

| テーブル名 | Sprint | 説明 |
|-----------|--------|------|
| `messages` | 1 | Slack風メッセージ |
| `specifications` | 1 | 仕様書管理 |
| `intents` | 1 | Intent管理 |
| `notifications` | 1 | 通知システム |
| `choice_points` | 8, 10 | 選択履歴保存 |
| `contradictions` | 11 | 矛盾検出レコード |
| `intent_relations` | 11 | Intent関係 |

### テーブル確認コマンド

```bash
# 全テーブル一覧
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "\dt"

# テーブル構造確認
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "\d contradictions"

# レコード数確認
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"
```

---

## 🔄 開発ワークフロー

### 1. 新機能開発

```bash
# 1. 開発環境起動
./docker/scripts/start-dev.sh

# 2. コードを編集（ホスト側で編集、自動的にコンテナに反映）

# 3. テスト実行
docker exec resonant_dev pytest tests/your_feature/ -v

# 4. デバッグが必要な場合
docker exec -it resonant_dev bash
python -m pdb your_script.py
```

### 2. マイグレーション追加

```bash
# 1. 新しいマイグレーションファイル作成
# docker/postgres/009_your_feature.sql

# 2. マイグレーション実行
docker exec -i resonant_postgres_dev psql -U resonant -d postgres < docker/postgres/009_your_feature.sql

# 3. テーブル確認
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "\dt"
```

### 3. テスト追加

```bash
# 1. テストファイル作成
# tests/your_feature/test_your_feature.py

# 2. テスト実行
docker exec resonant_dev pytest tests/your_feature/ -v

# 3. カバレッジ確認
docker exec resonant_dev pytest tests/your_feature/ --cov=bridge.your_feature --cov-report=term-missing
```

---

## 📝 ベストプラクティス

### 1. テスト作成

- ✅ 実際のPostgreSQLを使用する
- ✅ `db_pool` fixtureを使用する（`tests/conftest.py`）
- ✅ テストデータはテスト内で作成・削除する
- ❌ モックは最小限に（必要な場合のみ）

### 2. マイグレーション

- ✅ `IF NOT EXISTS`を使用する
- ✅ インデックスを適切に作成する
- ✅ コメントを追加する
- ✅ ロールバック可能にする

### 3. 環境管理

- ✅ `.env.dev`に機密情報を入れない
- ✅ 定期的に`docker-compose down -v`でクリーンアップ
- ✅ マイグレーションは順序を守る

---

## 🎯 次のステップ

### Sprint 12以降の準備

1. **AI判定による矛盾検出**
   - Claude API統合テスト環境
   - セマンティック矛盾検出

2. **パフォーマンステスト**
   - 大量データでのテスト
   - レイテンシ測定

3. **CI/CD統合**
   - GitHub Actions設定
   - 自動テスト実行

---

## 📚 参考資料

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)

---

## 🆘 サポート

問題が発生した場合：

1. このREADMEのトラブルシューティングセクションを確認
2. ログを確認: `docker logs resonant_dev` / `docker logs resonant_postgres_dev`
3. 環境をリセット: `docker-compose -f docker/docker-compose.dev.yml down -v`
4. 再起動: `./docker/scripts/start-dev.sh`

---

**最終更新**: 2025-11-21  
**メンテナー**: Kiro AI Assistant  
**バージョン**: 1.0.0
