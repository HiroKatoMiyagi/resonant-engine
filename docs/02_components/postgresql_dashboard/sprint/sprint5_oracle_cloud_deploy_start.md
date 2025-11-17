# Sprint 5: Oracle Cloud Free Tier デプロイ 作業開始指示書

**対象**: Tsumu (Cursor) または実装担当者
**期間**: 4日間想定
**前提**: Sprint 1-4 完了、Oracle Cloud アカウント作成済み

---

## 1. Done Definition

### Tier 1: 必須
- [ ] Oracle Cloud VM作成（ARM、4 OCPU、24GB）
- [ ] Docker/Docker Composeインストール
- [ ] 本番用docker-compose.prod.yml作成
- [ ] SSL証明書取得（Let's Encrypt）
- [ ] 全サービスデプロイ
- [ ] 外部アクセス確認
- [ ] バックアップ設定

### Tier 2: 品質
- [ ] Prometheus + Grafana監視
- [ ] アラート設定
- [ ] 500人負荷テスト
- [ ] 99%稼働率証明

---

## 2. 実装スケジュール（4日間）

### Day 1: Oracle Cloud VM セットアップ

**タスク1**: VM作成
1. Oracle Cloud Console → Compute → Instances → Create Instance
2. 設定:
   - Shape: VM.Standard.A1.Flex
   - OCPU: 4
   - Memory: 24 GB
   - Image: Oracle Linux 8 または Ubuntu 22.04
   - Boot Volume: 200 GB

**タスク2**: SSH接続設定
```bash
# ローカルで鍵生成
ssh-keygen -t rsa -b 4096 -f ~/.ssh/resonant_oracle

# 公開鍵をOCIコンソールで設定

# SSH接続
ssh -i ~/.ssh/resonant_oracle ubuntu@<PUBLIC_IP>
```

**タスク3**: 基本セットアップ
```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# Docker インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose インストール
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 確認
docker --version
docker-compose --version
```

**タスク4**: ファイアウォール設定（OCI側）
1. VCN → Security Lists
2. Ingress Rules追加:
   - Port 22 (SSH)
   - Port 80 (HTTP)
   - Port 443 (HTTPS)

**完了基準**:
- [ ] VMが起動
- [ ] SSH接続成功
- [ ] Docker動作確認
- [ ] ポート開放完了

---

### Day 2: プロジェクトデプロイ

**タスク1**: リポジトリクローン
```bash
cd /opt
sudo mkdir resonant && sudo chown $USER:$USER resonant
cd resonant
git clone https://github.com/your-repo/resonant-engine.git
cd resonant-engine
```

**タスク2**: 本番用環境変数
```bash
cd docker
cp .env.example .env.prod
vim .env.prod
```

```bash
# .env.prod
POSTGRES_USER=resonant
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
POSTGRES_DB=resonant_dashboard
ANTHROPIC_API_KEY=<YOUR_API_KEY>
DEBUG=false
LOG_LEVEL=INFO
```

**タスク3**: docker-compose.prod.yml作成
```yaml
version: '3.9'

services:
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
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/01_init.sql:ro
    networks:
      - resonant_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 5

  backend:
    build: ../backend
    container_name: resonant_backend
    restart: always
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      DEBUG: "false"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - resonant_network

  frontend:
    build: ../frontend
    container_name: resonant_frontend
    restart: always
    depends_on:
      - backend
    networks:
      - resonant_network

  intent_bridge:
    build: ../bridge
    container_name: resonant_intent_bridge
    restart: always
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
    networks:
      - resonant_network

  nginx:
    image: nginx:alpine
    container_name: resonant_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - frontend
      - backend
    networks:
      - resonant_network

volumes:
  postgres_data:
    name: resonant_postgres_data_prod

networks:
  resonant_network:
    name: resonant_network_prod
```

**タスク4**: Nginx設定（初回HTTP版）
```bash
mkdir -p nginx/conf.d
```

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
    server_name _;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

**タスク5**: 初回デプロイ
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
docker-compose -f docker-compose.prod.yml ps
```

**完了基準**:
- [ ] 全コンテナ起動
- [ ] http://<PUBLIC_IP> でアクセス可能
- [ ] API動作確認

---

### Day 3: SSL証明書とセキュリティ

**タスク1**: Let's Encrypt証明書取得
```bash
# Certbotディレクトリ作成
mkdir -p certbot/conf certbot/www

# 初回証明書取得（ドメイン設定済みの場合）
docker run --rm -v /opt/resonant/resonant-engine/docker/certbot/conf:/etc/letsencrypt \
  -v /opt/resonant/resonant-engine/docker/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  --email your@email.com --agree-tos --no-eff-email \
  -d resonant.example.com
```

**タスク2**: Nginx HTTPS設定更新
```nginx
# nginx/conf.d/default.conf (HTTPS版)
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

    add_header Strict-Transport-Security "max-age=31536000" always;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

**タスク3**: 証明書自動更新設定
```bash
# crontab -e
0 0 1 * * docker run --rm -v /opt/resonant/.../certbot/conf:/etc/letsencrypt certbot/certbot renew
```

**タスク4**: ファイアウォール強化
```bash
# fail2ban インストール
sudo apt install fail2ban -y

# 設定
sudo vim /etc/fail2ban/jail.local
# [sshd]
# enabled = true
# maxretry = 3

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**完了基準**:
- [ ] HTTPS動作確認
- [ ] SSL証明書有効
- [ ] 自動更新設定完了
- [ ] fail2ban動作

---

### Day 4: バックアップと監視

**タスク1**: 自動バックアップ設定
```bash
mkdir -p /opt/resonant/backups

cat > /opt/resonant/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/resonant/backups"

docker exec resonant_postgres pg_dump -U resonant resonant_dashboard \
  | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
echo "$(date): Backup completed: db_$DATE.sql.gz" >> /var/log/resonant_backup.log
EOF

chmod +x /opt/resonant/backup.sh

# crontab -e
# 0 3 * * * /opt/resonant/backup.sh
```

**タスク2**: ヘルスチェックスクリプト
```bash
cat > /opt/resonant/health_check.sh << 'EOF'
#!/bin/bash
CONTAINERS=("resonant_postgres" "resonant_backend" "resonant_frontend" "resonant_nginx" "resonant_intent_bridge")

for container in "${CONTAINERS[@]}"; do
  STATUS=$(docker inspect -f '{{.State.Running}}' $container 2>/dev/null)
  if [ "$STATUS" != "true" ]; then
    echo "ALERT: $container is not running!"
    # ここにアラート送信ロジック（Slack等）
  fi
done
EOF

chmod +x /opt/resonant/health_check.sh

# crontab -e
# */5 * * * * /opt/resonant/health_check.sh
```

**タスク3**: 最終動作確認
```bash
# 全サービス状態確認
docker-compose -f docker-compose.prod.yml ps

# APIヘルスチェック
curl -k https://resonant.example.com/api/health

# ログ確認
docker-compose -f docker-compose.prod.yml logs --tail=100

# バックアップテスト
/opt/resonant/backup.sh
ls -la /opt/resonant/backups/
```

**完了基準**:
- [ ] 日次バックアップ動作
- [ ] ヘルスチェック動作
- [ ] 全サービス安定稼働
- [ ] 外部からHTTPSアクセス成功

---

## 3. 完了報告書

1. **Done Definition達成**: Tier 1: X/7, Tier 2: X/4
2. **インフラ情報**: Public IP、ドメイン、リソース使用量
3. **性能**: 応答時間、同時接続数
4. **セキュリティ**: SSL評価、ファイアウォール設定
5. **運用**: バックアップ頻度、監視設定
6. **コスト**: $0/月 確認

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
