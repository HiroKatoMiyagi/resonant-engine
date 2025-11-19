# Docker開発環境構築レポート

**構築日**: 2025年11月19日  
**対象プロジェクト**: Resonant Engine  
**構築者**: GitHub Copilot (補助具現層) + Tsumu (実行具現層)  
**環境種別**: 統合開発環境（Docker Compose）

---

## 1. エグゼクティブサマリー

### 構築結果概要

| 項目 | 結果 |
|------|------|
| **構築ステータス** | ✅ **完了** |
| **稼働コンテナ数** | 5/5 |
| **データベース** | PostgreSQL 15.4 + pgvector 0.5.1 |
| **API動作状況** | Backend API (Port 8000) 正常稼働 |
| **フロントエンド** | React (Port 3000) 正常稼働 |
| **統合性** | ✅ 完全統合確認 |

### 主要成果

1. ✅ **Docker Compose環境の完全稼働**
2. ✅ **PostgreSQL + pgvector拡張の利用可能性確認**
3. ✅ **マイクロサービス間通信の確立**
4. ✅ **ローカルPostgreSQLとの競合解消**
5. ✅ **開発効率化基盤の確立**

---

## 2. アーキテクチャ概要

### 2.1 システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                     Host Machine (macOS)                     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Docker Compose Network: resonant             │ │
│  │                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │ │
│  │  │   Frontend   │  │   Backend    │  │  PostgreSQL │  │ │
│  │  │  (React)     │◄─┤   (FastAPI)  │◄─┤   15.4      │  │ │
│  │  │  Port: 3000  │  │  Port: 8000  │  │  Port: 5432 │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │ │
│  │         ▲                  ▲                            │ │
│  │         │                  │                            │ │
│  │  ┌──────┴─────┐    ┌──────┴─────┐                     │ │
│  │  │   Intent   │    │  Message   │                     │ │
│  │  │   Bridge   │    │   Bridge   │                     │ │
│  │  └────────────┘    └────────────┘                     │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                               │
│  Port Mapping:                                               │
│  - 3000:80    (Frontend)                                     │
│  - 8000:8000  (Backend API)                                  │
│  - 5432:5432  (PostgreSQL)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 コンテナ詳細

#### 2.2.1 PostgreSQL Container

**Image**: `postgres:15-alpine`  
**Container Name**: `resonant_postgres`  
**Status**: ✅ Up 2 hours (healthy)

**設定**:
```yaml
environment:
  - POSTGRES_USER=resonant
  - POSTGRES_PASSWORD=password
  - POSTGRES_DB=resonant
ports:
  - "5432:5432"
volumes:
  - postgres_data:/var/lib/postgresql/data
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U resonant"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**拡張機能**:
- `plpgsql` 1.0 (PL/pgSQL procedural language)
- `uuid-ossp` 1.1 (UUID generation)
- `vector` 0.5.1 (pgvector for embeddings)

**データベース**:
- `postgres` (デフォルト)
- `resonant_dashboard` (アプリケーション用)

**テーブル構造** (resonant_dashboard):
```
messages (7 columns)
  - id: uuid PRIMARY KEY
  - user_id: varchar(100) NOT NULL
  - content: text NOT NULL
  - message_type: varchar(50) DEFAULT 'user'
  - metadata: jsonb DEFAULT '{}'
  - created_at: timestamptz DEFAULT now()
  - updated_at: timestamptz DEFAULT now()

intents (10 columns)
  - id: uuid PRIMARY KEY
  - description: text NOT NULL
  - intent_type: varchar(100)
  - status: varchar(50) DEFAULT 'pending'
  - priority: integer DEFAULT 0
  - result: jsonb
  - metadata: jsonb DEFAULT '{}'
  - created_at: timestamptz DEFAULT now()
  - updated_at: timestamptz DEFAULT now()
  - processed_at: timestamptz

claude_code_sessions (TBD)
claude_code_executions (TBD)
notifications (TBD)
specifications (TBD)
```

**リソース使用状況**:
```
CPU: 0.00%
Memory: 25.82MiB / 7.653GiB (0.33%)
Network I/O: Minimal
Disk I/O: postgres_data volume
```

#### 2.2.2 Backend Container

**Container Name**: `resonant_backend`  
**Status**: ✅ Up 26 hours (healthy)  
**Port**: 8000:8000

**主要機能**:
- FastAPI REST API
- Intent処理エンドポイント
- Message管理エンドポイント
- Context Assembler統合

**Health Check**: ✅ Passing

**依存関係**:
- PostgreSQL (Database)
- Anthropic API (Claude)
- Intent Bridge
- Message Bridge

#### 2.2.3 Frontend Container

**Container Name**: `resonant_frontend`  
**Status**: ✅ Up 26 hours  
**Port**: 3000:80

**技術スタック**:
- React
- TypeScript
- Tailwind CSS

**機能**:
- チャットUI
- Intent管理UI
- 通知表示

#### 2.2.4 Intent Bridge Container

**Container Name**: `resonant_intent_bridge`  
**Status**: ✅ Up 23 hours

**役割**:
- Intent分類
- Context Assembler呼び出し
- Intent処理オーケストレーション

#### 2.2.5 Message Bridge Container

**Container Name**: `resonant_message_bridge`  
**Status**: ✅ Up 23 hours

**役割**:
- メッセージルーティング
- WebSocket通信管理
- リアルタイム通知

---

## 3. 構築手順

### 3.1 前提条件

**必要ソフトウェア**:
- Docker Desktop for Mac (version 4.x+)
- Docker Compose (version 2.x+)
- Git

**システム要件**:
- macOS (Apple Silicon or Intel)
- RAM: 8GB以上推奨
- Disk: 20GB以上の空き容量

### 3.2 構築ステップ

#### Step 1: リポジトリクローン

```bash
git clone https://github.com/HiroKatoMiyagi/resonant-engine.git
cd resonant-engine
```

#### Step 2: ブランチ切り替え

```bash
# 開発ブランチに切り替え（必要に応じて）
git checkout claude/sync-postgres-schema-01Ux8VUZ5ZQctviEHbAHzDn3
git pull origin claude/sync-postgres-schema-01Ux8VUZ5ZQctviEHbAHzDn3
```

#### Step 3: 環境変数設定

```bash
# docker/.env ファイル作成
cat > docker/.env << EOF
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxx
DATABASE_URL=postgresql://resonant:password@db:5432/resonant_dashboard
EOF
```

#### Step 4: ローカルPostgreSQLの停止

```bash
# Homebrewでインストールしたローカルpostgresqlを停止
brew services stop postgresql@15

# ポート5432が解放されたことを確認
lsof -i :5432
```

#### Step 5: Docker Compose起動

```bash
# バックグラウンドで起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

#### Step 6: コンテナ状態確認

```bash
# 全コンテナの状態確認
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ヘルスチェック確認
docker inspect resonant_postgres | grep Health -A 10
docker inspect resonant_backend | grep Health -A 10
```

#### Step 7: データベース初期化確認

```bash
# データベース接続確認
docker exec resonant_postgres psql -U resonant -d postgres -c "\l"

# 拡張機能確認
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\dx"

# テーブル確認
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\dt"
```

#### Step 8: API動作確認

```bash
# Backend API health check
curl http://localhost:8000/health

# Frontend確認
open http://localhost:3000
```

---

## 4. トラブルシューティング

### 4.1 ポート競合問題

**問題**: ローカルPostgreSQLとの競合

**症状**:
```
Error: bind: address already in use
```

**解決策**:
```bash
# ローカルPostgreSQLを停止
brew services stop postgresql@15

# プロセス確認
lsof -i :5432

# 必要に応じてプロセスをkill
kill -9 <PID>

# Dockerコンテナ再起動
docker-compose restart db
```

### 4.2 コンテナ起動失敗

**問題**: コンテナが起動しない

**診断コマンド**:
```bash
# ログ確認
docker-compose logs <container_name>

# コンテナ詳細確認
docker inspect <container_name>

# ネットワーク確認
docker network ls
docker network inspect resonant_default
```

**一般的な解決策**:
```bash
# コンテナ再ビルド
docker-compose build --no-cache

# ボリューム削除して再作成
docker-compose down -v
docker-compose up -d
```

### 4.3 データベース接続エラー

**問題**: ホストからPostgreSQLに接続できない

**症状**:
```
password authentication failed for user "resonant"
```

**解決策**:
```bash
# Docker経由で接続（推奨）
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "SELECT 1;"

# パスワードなしでの接続確認
docker exec resonant_postgres psql -U resonant -d postgres -c "\conninfo"
```

### 4.4 pgvector拡張が見つからない

**問題**: CREATE EXTENSION vector が失敗

**確認コマンド**:
```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\dx"
```

**解決策**:
```bash
# pgvectorが含まれるイメージを使用
# docker-compose.ymlで以下を確認:
# image: postgres:15-alpine または pgvector/pgvector:pg15
```

---

## 5. ネットワーク構成

### 5.1 Dockerネットワーク

**Network Name**: `resonant_default`  
**Driver**: bridge  
**Subnet**: 172.x.0.0/16 (自動割り当て)

**コンテナIP割り当て** (例):
```
resonant_postgres:        172.18.0.2
resonant_backend:         172.18.0.3
resonant_frontend:        172.18.0.4
resonant_intent_bridge:   172.18.0.5
resonant_message_bridge:  172.18.0.6
```

### 5.2 ポートマッピング

| サービス | コンテナポート | ホストポート | プロトコル | アクセスURL |
|---------|--------------|------------|-----------|------------|
| Frontend | 80 | 3000 | HTTP | http://localhost:3000 |
| Backend | 8000 | 8000 | HTTP | http://localhost:8000 |
| PostgreSQL | 5432 | 5432 | TCP | postgresql://localhost:5432 |

### 5.3 内部DNS

Docker Composeは自動的に内部DNSを設定：
- `db` → PostgreSQLコンテナ
- `backend` → Backendコンテナ
- `frontend` → Frontendコンテナ

**接続例** (Backend → PostgreSQL):
```python
DATABASE_URL = "postgresql://resonant:password@db:5432/resonant_dashboard"
```

---

## 6. データ永続化

### 6.1 Dockerボリューム

**定義** (docker-compose.yml):
```yaml
volumes:
  postgres_data:
    driver: local
```

**確認コマンド**:
```bash
# ボリューム一覧
docker volume ls

# ボリューム詳細
docker volume inspect resonant-engine_postgres_data
```

**データ格納場所**:
```
/var/lib/docker/volumes/resonant-engine_postgres_data/_data
```

### 6.2 バックアップ戦略

**手動バックアップ**:
```bash
# データベース全体をダンプ
docker exec resonant_postgres pg_dump -U resonant resonant_dashboard > backup.sql

# 復元
docker exec -i resonant_postgres psql -U resonant resonant_dashboard < backup.sql
```

**自動バックアップ** (TODO):
- cron設定
- S3へのアップロード
- バックアップローテーション

---

## 7. セキュリティ

### 7.1 認証情報管理

**環境変数**:
```bash
# docker/.env (Gitignore対象)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxx
DATABASE_URL=postgresql://resonant:password@db:5432/resonant_dashboard
```

**推奨事項**:
- ✅ `.env`ファイルは`.gitignore`に追加済み
- ✅ APIキーはハードコーディングしない
- ⚠️ 本番環境ではSecrets管理サービス使用推奨

### 7.2 ネットワークセキュリティ

**現在の設定**:
- Docker内部ネットワークでの通信
- ホストからのアクセスは必要なポートのみ公開

**改善推奨**:
- リバースプロキシ（Nginx）の導入
- HTTPS化
- ファイアウォール設定

### 7.3 データベースセキュリティ

**現在の設定**:
- パスワード認証（簡易設定）
- Docker内部ネットワークのみアクセス可能

**改善推奨**:
- 強固なパスワード設定
- SSL/TLS接続
- ロールベースアクセス制御

---

## 8. モニタリングとログ

### 8.1 ログ管理

**ログ確認コマンド**:
```bash
# 全サービスのログ
docker-compose logs

# 特定サービスのログ
docker-compose logs backend

# リアルタイムログ
docker-compose logs -f

# 最新N行のログ
docker-compose logs --tail=100 postgres
```

**ログ保存場所**:
```
/var/lib/docker/containers/<container_id>/<container_id>-json.log
```

### 8.2 リソースモニタリング

**コマンド**:
```bash
# リアルタイムモニタリング
docker stats

# 特定コンテナ
docker stats resonant_postgres

# 1回のみ表示
docker stats --no-stream
```

**結果例**:
```
NAME               CPU %   MEM USAGE / LIMIT    MEM %
resonant_postgres  0.00%   25.82MiB / 7.653GiB  0.33%
resonant_backend   0.01%   45.23MiB / 7.653GiB  0.58%
```

### 8.3 ヘルスチェック

**設定例** (docker-compose.yml):
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U resonant"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

**確認コマンド**:
```bash
docker inspect --format='{{json .State.Health}}' resonant_postgres | jq
```

---

## 9. 開発ワークフロー

### 9.1 日常的な操作

**起動**:
```bash
docker-compose up -d
```

**停止**:
```bash
docker-compose down
```

**再起動**:
```bash
docker-compose restart
```

**ログ確認**:
```bash
docker-compose logs -f backend
```

### 9.2 コード変更時

**Backend変更時**:
```bash
# 再ビルド
docker-compose build backend

# 再起動
docker-compose restart backend
```

**Frontend変更時**:
```bash
# 再ビルド
docker-compose build frontend

# 再起動
docker-compose restart frontend
```

### 9.3 データベーススキーマ変更

**マイグレーション** (TODO):
```bash
# Alembic使用予定
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

**手動変更**:
```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "
ALTER TABLE messages ADD COLUMN new_field VARCHAR(100);
"
```

---

## 10. パフォーマンスチューニング

### 10.1 PostgreSQL設定

**推奨設定** (TODO):
```sql
-- shared_buffers: システムメモリの25%
-- effective_cache_size: システムメモリの50-75%
-- work_mem: 4MB-64MB
-- maintenance_work_mem: 64MB-512MB
```

### 10.2 インデックス最適化

**既存インデックス**:
```sql
-- messages
CREATE INDEX idx_messages_created_at ON messages (created_at DESC);
CREATE INDEX idx_messages_type ON messages (message_type);
CREATE INDEX idx_messages_user_id ON messages (user_id);

-- intents
CREATE INDEX idx_intents_created_at ON intents (created_at DESC);
CREATE INDEX idx_intents_priority ON intents (priority DESC);
CREATE INDEX idx_intents_status ON intents (status);
```

**推奨追加インデックス**:
```sql
-- 複合インデックス
CREATE INDEX idx_messages_user_created ON messages (user_id, created_at DESC);
CREATE INDEX idx_intents_status_priority ON intents (status, priority DESC);
```

### 10.3 コンテナリソース制限

**推奨設定** (docker-compose.yml):
```yaml
services:
  db:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 11. CI/CD統合

### 11.1 GitHub Actions (計画中)

**ワークフロー案**:
```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: docker-compose build
      - name: Run tests
        run: docker-compose run backend pytest
```

### 11.2 自動デプロイ (計画中)

**ターゲット**:
- AWS ECS
- Google Cloud Run
- Azure Container Instances

---

## 12. コスト分析

### 12.1 ローカル開発コスト

**リソース使用量**:
- CPU: ほぼ0%（アイドル時）
- Memory: 約100MB（5コンテナ合計）
- Disk: 約2GB（イメージ + ボリューム）

**電力消費**: 微小（通常のmacOS使用と変わらず）

### 12.2 クラウド展開時の推定コスト (参考)

**AWS ECS Fargate** (月額概算):
- PostgreSQL RDS (db.t3.micro): $15
- ECS Tasks (0.25 vCPU, 0.5GB): $20
- Load Balancer: $20
- **合計**: 約$55/月

---

## 13. 今後の改善計画

### 13.1 短期（1-2週間）

- [ ] Alembicマイグレーション導入
- [ ] ログ集約（Fluentd or Loki）
- [ ] メトリクス収集（Prometheus）
- [ ] 自動バックアップスクリプト

### 13.2 中期（1-2ヶ月）

- [ ] Kubernetes移行検討
- [ ] CI/CDパイプライン構築
- [ ] 本番環境デプロイ自動化
- [ ] モニタリングダッシュボード（Grafana）

### 13.3 長期（3-6ヶ月）

- [ ] マルチリージョン展開
- [ ] HA（高可用性）構成
- [ ] DRサイト構築
- [ ] オートスケーリング

---

## 14. ナレッジベース

### 14.1 よくある質問

**Q: コンテナが起動しない**
A: `docker-compose logs <service>`でログ確認。ポート競合やボリューム問題が多い。

**Q: データベースに接続できない**
A: `docker exec`経由での接続を推奨。ホスト経由は認証設定が複雑。

**Q: パフォーマンスが遅い**
A: Docker Desktopのリソース割り当てを確認。PostgreSQL設定も見直し。

### 14.2 便利なコマンド集

```bash
# クイックリスタート
docker-compose restart

# 完全再構築
docker-compose down -v && docker-compose up -d --build

# データベース接続
docker exec -it resonant_postgres psql -U resonant -d resonant_dashboard

# ログのgrep
docker-compose logs backend | grep ERROR

# コンテナに入る
docker exec -it resonant_backend bash

# ディスク使用量確認
docker system df
```

---

## 15. 関連ドキュメント

- [Sprint 6受け入れテストレポート](./sprint6_acceptance_test_report_docker.md)
- [PostgreSQLトラブルシューティングガイド](../troubleshooting/postgres_hang_issue.md)
- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [pgvector公式ドキュメント](https://github.com/pgvector/pgvector)

---

## 16. 変更履歴

| 日付 | バージョン | 変更内容 | 担当者 |
|------|-----------|---------|--------|
| 2025-11-19 | 1.0 | 初版作成 | GitHub Copilot |

---

**文書バージョン**: 1.0  
**作成日**: 2025年11月19日  
**最終更新**: 2025年11月19日  
**ステータス**: ✅ レビュー待ち
