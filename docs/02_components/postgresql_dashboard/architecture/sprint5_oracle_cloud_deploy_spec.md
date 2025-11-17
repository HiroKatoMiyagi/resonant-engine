# Sprint 5: Oracle Cloud Free Tier デプロイ仕様書

## 0. 概要

**目的**: 月額$0でResonant Dashboardを本番公開
**期間**: 4日間
**前提**: Sprint 1-4 完了、Oracle Cloud アカウント作成済み

---

## 1. Done Definition

### Tier 1: 必須
- [ ] Oracle Cloud Free Tier VM作成
- [ ] Docker Compose本番デプロイ
- [ ] ドメイン設定（オプション）またはIPアクセス
- [ ] HTTPS対応（Let's Encrypt）
- [ ] PostgreSQLバックアップ設定
- [ ] 全サービス（postgres, backend, frontend, intent_bridge）稼働
- [ ] 外部からのアクセス確認

### Tier 2: 品質
- [ ] Prometheus + Grafana監視設定
- [ ] ログ集約（Loki）
- [ ] アラート設定（Alertmanager）
- [ ] 自動バックアップ（日次）
- [ ] セキュリティ強化（ファイアウォール、fail2ban）
- [ ] 500人同時アクセス対応

---

## 2. Oracle Cloud Free Tier リソース

### 2.1 利用可能リソース（Always Free）

```yaml
compute:
  shape: "VM.Standard.A1.Flex"
  ocpus: 4
  memory_gb: 24
  boot_volume_gb: 200

network:
  vcn: 1個
  load_balancer: 2個
  bandwidth: 10TB/月

database:
  autonomous_db: 2個 (20GB each)
  # 今回は使用せず、Docker内のPostgreSQLを使用
```

### 2.2 推定コスト

```
月額コスト: $0 (Free Tier範囲内)

内訳:
- Compute: $0 (Always Free)
- Storage: $0 (200GB無料)
- Network: $0 (10TB/月無料)
- DNS: $0 (Oracle提供DNS)
- SSL: $0 (Let's Encrypt)

合計: $0/月
```

---

## 3. システムアーキテクチャ（本番）

```
┌───────────────────────────────────────────────────────┐
│               Oracle Cloud Free Tier                   │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │              VM.Standard.A1.Flex                 │  │
│  │         4 OCPU / 24GB RAM / 200GB Disk          │  │
│  │                                                  │  │
│  │  ┌────────────────────────────────────────┐    │  │
│  │  │           Docker Compose               │    │  │
│  │  │                                        │    │  │
│  │  │  ┌────────────┐  ┌───────────────┐   │    │  │
│  │  │  │  Nginx     │  │   Frontend    │   │    │  │
│  │  │  │  (Reverse  │  │   (React)     │   │    │  │
│  │  │  │   Proxy)   │  │   :3000       │   │    │  │
│  │  │  │  :80/:443  │  └───────────────┘   │    │  │
│  │  │  └────────────┘                      │    │  │
│  │  │         │           ┌───────────────┐   │    │  │
│  │  │         └──────────→│   Backend     │   │    │  │
│  │  │                     │   (FastAPI)   │   │    │  │
│  │  │                     │   :8000       │   │    │  │
│  │  │                     └───────────────┘   │    │  │
│  │  │                            │            │    │  │
│  │  │  ┌────────────────────────┼────────┐   │    │  │
│  │  │  │  PostgreSQL 15        ↓        │   │    │  │
│  │  │  │  :5432                         │   │    │  │
│  │  │  │  [Volume: 20GB]                │   │    │  │
│  │  │  └────────────────────────────────┘   │    │  │
│  │  │                                        │    │  │
│  │  │  ┌─────────────────────────────────┐   │    │  │
│  │  │  │  Intent Bridge Daemon           │   │    │  │
│  │  │  │  (Claude API連携)               │   │    │  │
│  │  │  └─────────────────────────────────┘   │    │  │
│  │  │                                        │    │  │
│  │  │  ┌─────────────────────────────────┐   │    │  │
│  │  │  │  Monitoring Stack (オプション)   │   │    │  │
│  │  │  │  - Prometheus :9090             │   │    │  │
│  │  │  │  - Grafana :3001                │   │    │  │
│  │  │  │  - Loki :3100                   │   │    │  │
│  │  │  └─────────────────────────────────┘   │    │  │
│  │  └────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  Public IP: XXX.XXX.XXX.XXX                           │
│  Domain: resonant.example.com (オプション)             │
└───────────────────────────────────────────────────────┘
```

---

## 4. デプロイ構成

### 4.1 docker-compose.prod.yml

```yaml
version: '3.9'

services:
  nginx:
    image: nginx:alpine
    container_name: resonant_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - frontend
      - backend
    networks:
      - resonant_network

  postgres:
    image: postgres:15-alpine
    container_name: resonant_postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - resonant_network
    # 外部アクセス禁止（セキュリティ）
    # ports は設定しない

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: resonant_backend
    restart: always
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      DEBUG: "false"
      LOG_LEVEL: "INFO"
    depends_on:
      - postgres
    networks:
      - resonant_network

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile.prod
    container_name: resonant_frontend
    restart: always
    depends_on:
      - backend
    networks:
      - resonant_network

  intent_bridge:
    build:
      context: ../bridge
      dockerfile: Dockerfile
    container_name: resonant_intent_bridge
    restart: always
    environment:
      POSTGRES_HOST: postgres
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - backend
    networks:
      - resonant_network

  certbot:
    image: certbot/certbot
    container_name: resonant_certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
    name: resonant_postgres_data_prod

networks:
  resonant_network:
    name: resonant_network_prod
    driver: bridge
```

### 4.2 Nginx設定（HTTPS対応）

```nginx
# nginx/conf.d/default.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name resonant.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name resonant.example.com;

    ssl_certificate /etc/letsencrypt/live/resonant.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/resonant.example.com/privkey.pem;

    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket (将来用)
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 5. セキュリティ設定

### 5.1 ファイアウォール（iptables）

```bash
# 基本ポリシー
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# ループバック許可
iptables -A INPUT -i lo -j ACCEPT

# 確立済み接続
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# SSH（22）
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# HTTP/HTTPS（80/443）
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 保存
iptables-save > /etc/iptables/rules.v4
```

### 5.2 Fail2Ban設定

```ini
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
```

---

## 6. バックアップ戦略

### 6.1 自動バックアップスクリプト

```bash
#!/bin/bash
# /opt/resonant/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/resonant/backups"

# PostgreSQLバックアップ
docker exec resonant_postgres pg_dump -U resonant resonant_dashboard \
  | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# 7日以上古いバックアップを削除
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

### 6.2 Cron設定

```bash
# crontab -e
0 3 * * * /opt/resonant/backup.sh >> /var/log/backup.log 2>&1
```

---

## 7. 監視設定（オプション）

### 7.1 Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
prometheus:
  image: prom/prometheus:latest
  container_name: resonant_prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana:latest
  container_name: resonant_grafana
  ports:
    - "3001:3000"
  volumes:
    - grafana_data:/var/lib/grafana
```

### 7.2 主要メトリクス

- CPU/メモリ使用率
- PostgreSQL接続数
- API応答時間
- Intent処理数/成功率
- ディスク使用量

---

## 8. デプロイ手順概要

1. Oracle Cloud VM作成（ARM, 4 OCPU, 24GB）
2. Docker, Docker Composeインストール
3. リポジトリクローン
4. 環境変数設定（.env.prod）
5. SSL証明書取得（Let's Encrypt）
6. docker-compose up -d
7. ファイアウォール設定
8. バックアップスケジュール設定
9. 監視設定（オプション）
10. 動作確認

---

## 9. 成功基準

- [ ] https://resonant.example.com でアクセス可能
- [ ] 全サービス（4コンテナ）稼働
- [ ] SSL証明書有効（A+評価）
- [ ] 自動バックアップ動作
- [ ] 500人同時アクセス対応
- [ ] 99%稼働率（30日間）
- [ ] 月額コスト $0

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
