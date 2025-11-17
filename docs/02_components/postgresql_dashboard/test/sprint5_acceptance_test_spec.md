# Sprint 5: Oracle Cloud デプロイ 受け入れテスト仕様書

**テスト項目数**: 20件
**承認者**: 宏啓（プロジェクトオーナー）

---

## 1. インフラテスト（5件）

| ID | テスト名 | 手順 | 期待結果 | 結果 |
|----|---------|------|----------|------|
| I01 | VM起動確認 | Oracle Console | Running状態 | |
| I02 | リソース確認 | htop/free -m | 4 OCPU, 24GB RAM | |
| I03 | ディスク容量 | df -h | 200GB利用可能 | |
| I04 | ネットワーク | ping/traceroute | Public IPアクセス可能 | |
| I05 | Docker動作 | docker info | エンジン稼働 | |

---

## 2. サービス稼働テスト（5件）

| ID | テスト名 | 手順 | 期待結果 | 結果 |
|----|---------|------|----------|------|
| S01 | PostgreSQL | docker ps | resonant_postgres UP | |
| S02 | Backend | docker ps | resonant_backend UP | |
| S03 | Frontend | docker ps | resonant_frontend UP | |
| S04 | Intent Bridge | docker ps | resonant_intent_bridge UP | |
| S05 | Nginx | docker ps | resonant_nginx UP | |

---

## 3. 外部アクセステスト（4件）

| ID | テスト名 | 手順 | 期待結果 | 結果 |
|----|---------|------|----------|------|
| E01 | HTTP接続 | curl http://IP | 301 Redirect to HTTPS | |
| E02 | HTTPS接続 | curl https://domain | 200 OK | |
| E03 | API疎通 | GET /api/health | {"status": "healthy"} | |
| E04 | ダッシュボード | ブラウザアクセス | UI表示 | |

---

## 4. セキュリティテスト（3件）

| ID | テスト名 | 手順 | 期待結果 | 結果 |
|----|---------|------|----------|------|
| C01 | SSL証明書 | ssllabs.com | A+評価 or 有効期限確認 | |
| C02 | ファイアウォール | nmap scan | 80/443/22のみ開放 | |
| C03 | Fail2Ban | 不正ログイン3回 | IPブロック | |

---

## 5. 運用テスト（3件）

| ID | テスト名 | 手順 | 期待結果 | 結果 |
|----|---------|------|----------|------|
| O01 | バックアップ実行 | ./backup.sh | .sql.gz生成 | |
| O02 | バックアップ復元 | pg_restore | データ復元成功 | |
| O03 | 自動クリーンアップ | 7日後確認 | 古いバックアップ削除 | |

---

## 6. 総合テスト結果

**合計**: ___/20 PASS

**重要テスト（必須PASS）**:
- S01-S05: 全サービス稼働
- E02: HTTPS接続
- C01: SSL証明書有効
- O01: バックアップ動作

**最終確認項目**:
- [ ] 月額コスト: $0 確認
- [ ] 外部ユーザーアクセス可能
- [ ] Intent自動処理動作
- [ ] 99%稼働率目標設定

**判定**: PASS / FAIL

**承認**: ____________________

**日付**: ____________________

---

**作成日**: 2025-11-17
