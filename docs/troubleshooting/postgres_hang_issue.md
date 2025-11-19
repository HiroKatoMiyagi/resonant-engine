# PostgreSQL コマンド待機問題の原因と対応策

## 問題

```bash
docker exec -it resonant_postgres psql -U resonant -d resonant_dashboard -c "\dx"
```

このコマンドが長時間ハングする。

## 原因

### 1. ポート競合
- **ローカルPostgreSQL**: Homebrewインストール版がポート5432を使用中
- **Docker PostgreSQL**: 同じポート5432にマッピングを試みているが、実際には接続できていない
- 結果: コマンドはローカルPostgreSQLに接続しようとするが、コンテナ内のpsqlクライアントから到達できない

### 2. インタラクティブモードの問題
- `-it`フラグ使用時、ターミナルセッションが確立されるが、I/O がブロックされる
- Docker コンテナ内のシェルとホストターミナル間の通信で競合が発生

### 3. 環境の混在
```bash
# 実際の接続状況
ローカルマシン:5432 → Homebrew PostgreSQL (resonant_dashboard DB存在)
Docker:5432 (内部) → Docker PostgreSQL (resonant_dashboard DB存在)
Docker:5432 (外部) → ポート競合により未マッピング
```

## 対応策

### ✅ 方法1: 非インタラクティブモードを使用（推奨）

```bash
# -it フラグを外す
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\dx"

# または echo でクエリを渡す
docker exec resonant_postgres sh -c "echo '\dx' | psql -U resonant -d resonant_dashboard"
```

**メリット**:
- 即座に応答
- スクリプト化しやすい
- CI/CDで使用可能

### ✅ 方法2: Dockerコンテナのポートを変更

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    ports:
      - "5433:5432"  # ホストの5433にマッピング
    environment:
      - POSTGRES_USER=resonant
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=resonant
```

接続方法:
```bash
# ホストから直接接続
psql -h localhost -p 5433 -U resonant -d resonant_dashboard

# Dockerコンテナ経由
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\dx"
```

### ✅ 方法3: ローカルPostgreSQLを停止

```bash
# Homebrewサービスを停止
brew services stop postgresql@15

# または
pg_ctl -D /opt/homebrew/var/postgresql@15 stop

# Dockerコンテナを再起動
docker-compose restart db
```

**注意**: ローカルPostgreSQLのデータが必要な場合は事前にバックアップ

### ✅ 方法4: psql クライアントをホストから使用

```bash
# ホストのpsqlクライアントから接続（ポート指定）
psql -h localhost -p 5432 -U resonant -d resonant_dashboard -c "\dx"
```

現在の状態では、これはHomebrewのPostgreSQLに接続します。

## 検証コマンド

### 接続先の確認
```bash
# Dockerコンテナ内のPostgreSQLバージョン
docker exec resonant_postgres psql -U resonant -d postgres -c "SELECT version();"

# ローカルPostgreSQLバージョン
psql -h localhost -p 5432 -U resonant -d postgres -c "SELECT version();"
```

### ポート使用状況の確認
```bash
lsof -i :5432
# または
netstat -an | grep 5432
```

### Dockerコンテナの状態確認
```bash
docker ps --filter "name=resonant_postgres"
docker logs resonant_postgres --tail 20
docker stats resonant_postgres --no-stream
```

## 推奨構成

開発環境では以下の構成を推奨：

1. **ローカルPostgreSQLを停止** または **異なるポートで起動**
2. **Dockerコンテナのみを使用** してPostgreSQLを管理
3. **非インタラクティブモード** でコマンド実行

```yaml
# docker-compose.yml (推奨設定)
services:
  db:
    image: postgres:15-alpine
    container_name: resonant_postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=resonant
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=resonant
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql  # 初期化スクリプト
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U resonant"]
      interval: 10s
      timeout: 5s
      retries: 5
```

## 現在の状態（2025年11月19日）

### ✅ 確認済み
- Dockerコンテナは正常動作中（21分稼働）
- `resonant_dashboard` に pgvector 0.5.1 インストール済み
- 非インタラクティブモードで正常応答

### ⚠️ 改善が必要
- ローカルPostgreSQLとの競合解消
- docker-compose.ymlでの初期化スクリプト追加
- 開発環境の統一

## 参考資料

- Docker exec documentation: https://docs.docker.com/engine/reference/commandline/exec/
- PostgreSQL port configuration: https://www.postgresql.org/docs/current/runtime-config-connection.html
- pgvector extension: https://github.com/pgvector/pgvector
