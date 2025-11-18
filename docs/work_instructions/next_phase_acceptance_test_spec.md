# Resonant Engine 次期開発フェーズ受け入れテスト仕様書

**バージョン**: v2.0
**作成日**: 2025年11月18日
**作成者**: Kana（翻訳層）
**テスト担当**: 加藤宏啓 / Kana

---

## 📋 目次

1. [テスト概要](#1-テスト概要)
2. [Sprint 2: 並行制御テスト](#2-sprint-2-並行制御テスト)
3. [Sprint 2: ドキュメント](#3-sprint-2-ドキュメント)
4. [Sprint 5: Oracle Cloud デプロイ](#4-sprint-5-oracle-cloud-デプロイ)
5. [Claude API 統合検証](#5-claude-api-統合検証)
6. [Kana 実装 Phase 1](#6-kana-実装-phase-1)
7. [総合受け入れテスト](#7-総合受け入れテスト)

---

## 1. テスト概要

### 1.1 目的

次期開発フェーズ（v2.0）の各機能が仕様書通りに実装され、期待通りに動作することを検証する。

### 1.2 合格基準

**全体合格条件**:
- 全受け入れテスト項目 PASS
- テストカバレッジ 80%以上
- パフォーマンスベースライン達成
- ドキュメント完備
- Kana レビュー承認

### 1.3 テスト環境

**ローカル環境**:
- macOS（/Users/zero/Projects/resonant-engine/）
- Python 3.11 + venv
- Docker 20.10+
- PostgreSQL 15（Docker）

**本番環境**（Sprint 5後）:
- Oracle Cloud Free Tier
- Ampere A1 ARM VM (4 OCPU, 24GB RAM)
- Ubuntu 22.04 LTS
- Docker Compose
- HTTPS (Let's Encrypt)

---

## 2. Sprint 2: 並行制御テスト

### 2.1 受け入れテスト項目

| ID | テスト項目 | 期待結果 | 検証方法 |
|----|-----------|---------|---------|
| AT-S2-01 | デッドロック自動リトライ | デッドロック発生時に最大3回自動リトライ | pytest実行 |
| AT-S2-02 | 楽観ロック競合検知 | バージョン不一致時にOptimisticLockError | pytest実行 |
| AT-S2-03 | 悲観ロックNOWAIT | ロック競合時に即座にLockNotAvailableError | pytest実行 |
| AT-S2-04 | 100並列更新成功 | 100個のIntent同時更新が全て成功 | pytest実行 |
| AT-S2-05 | レイテンシ基準達成 | p99 < 500ms | pytest実行 |
| AT-S2-06 | スループット基準達成 | > 50 ops/sec | pytest実行 |
| AT-S2-07 | デッドロック発生率 | < 1% (1000回実行) | pytest実行 |
| AT-S2-08 | リトライ成功率 | > 95% | pytest実行 |
| AT-S2-09 | リソース使用率 | CPU < 90%, Memory < 80% | pytest実行 |
| AT-S2-10 | テストカバレッジ | > 80% | pytest --cov |

### 2.2 テスト手順

#### 2.2.1 環境準備

```bash
# 1. プロジェクトディレクトリに移動
cd /Users/zero/Projects/resonant-engine/

# 2. venv 有効化
source venv/bin/activate

# 3. Docker 環境起動
cd docker && ./scripts/start.sh

# 4. ヘルスチェック
./scripts/check-health.sh
```

#### 2.2.2 テスト実行

```bash
# 1. 並行制御テスト全実行
cd /Users/zero/Projects/resonant-engine/
pytest tests/concurrency/ -v

# 期待される出力:
# tests/concurrency/test_deadlock_retry.py::TestDeadlockRetry::test_deadlock_auto_retry_success PASSED
# tests/concurrency/test_deadlock_retry.py::TestDeadlockRetry::test_max_retry_failure PASSED
# tests/concurrency/test_deadlock_retry.py::TestDeadlockRetry::test_optimistic_lock_conflict PASSED
# tests/concurrency/test_deadlock_retry.py::TestDeadlockRetry::test_pessimistic_lock_nowait PASSED
# tests/concurrency/test_100_parallel_updates.py::TestParallelPerformance::test_100_parallel_intent_updates PASSED
# tests/concurrency/test_100_parallel_updates.py::TestParallelPerformance::test_resource_usage_monitoring PASSED
# ...
# 36 passed in 45.23s
```

#### 2.2.3 カバレッジ確認

```bash
# カバレッジ測定
pytest tests/concurrency/ --cov=bridge.core --cov-report=term --cov-report=html

# 期待される出力:
# bridge/core/bridge_set.py    450    45    82%
# bridge/core/reeval_client.py  120    10    92%
# ...
# TOTAL                        1500   150    80%
```

#### 2.2.4 パフォーマンス確認

```bash
# パフォーマンステスト実行（詳細出力）
pytest tests/concurrency/test_100_parallel_updates.py -v -s

# 期待される出力:
# 📊 Performance Metrics:
#   Total Duration: 2.15s
#   Throughput: 46.51 ops/sec  ← 50 ops/sec 未満の場合は要調査
#   p50 Latency: 45.23ms
#   p95 Latency: 189.45ms
#   p99 Latency: 423.67ms      ← 500ms 未満であること
```

### 2.3 合格基準チェックリスト

- [ ] AT-S2-01: デッドロック自動リトライ PASS
- [ ] AT-S2-02: 楽観ロック競合検知 PASS
- [ ] AT-S2-03: 悲観ロックNOWAIT PASS
- [ ] AT-S2-04: 100並列更新成功 PASS
- [ ] AT-S2-05: p99レイテンシ < 500ms
- [ ] AT-S2-06: スループット > 50 ops/sec
- [ ] AT-S2-07: デッドロック発生率 < 1%
- [ ] AT-S2-08: リトライ成功率 > 95%
- [ ] AT-S2-09: CPU < 90%, Memory < 80%
- [ ] AT-S2-10: テストカバレッジ > 80%

**全項目合格で Sprint 2 受け入れ完了**

---

## 3. Sprint 2: ドキュメント

### 3.1 受け入れテスト項目

| ID | テスト項目 | 期待結果 | 検証方法 |
|----|-----------|---------|---------|
| AT-D2-01 | ロック戦略ドキュメント存在 | locking_strategy.md が存在 | ファイル確認 |
| AT-D2-02 | デッドロック対処法ドキュメント存在 | deadlock_handling.md が存在 | ファイル確認 |
| AT-D2-03 | ベストプラクティスドキュメント存在 | best_practices.md が存在 | ファイル確認 |
| AT-D2-04 | ロック戦略図表完備 | Mermaid図または画像が含まれる | 内容確認 |
| AT-D2-05 | コード例完備 | 実装可能なコード例が含まれる | 内容確認 |
| AT-D2-06 | トラブルシューティング完備 | 問題解決手順が記載されている | 内容確認 |

### 3.2 テスト手順

#### 3.2.1 ファイル存在確認

```bash
# ドキュメントディレクトリ確認
ls -la docs/02_components/bridge_lite/concurrency/

# 期待される出力:
# locking_strategy.md
# deadlock_handling.md
# best_practices.md
```

#### 3.2.2 内容確認

```bash
# 各ドキュメントのプレビュー
cat docs/02_components/bridge_lite/concurrency/locking_strategy.md
cat docs/02_components/bridge_lite/concurrency/deadlock_handling.md
cat docs/02_components/bridge_lite/concurrency/best_practices.md

# 確認ポイント:
# - 見出し構造が適切
# - コード例が実行可能
# - 図表が理解しやすい
# - 誤字脱字がない
```

### 3.3 合格基準チェックリスト

- [ ] AT-D2-01: locking_strategy.md 存在
- [ ] AT-D2-02: deadlock_handling.md 存在
- [ ] AT-D2-03: best_practices.md 存在
- [ ] AT-D2-04: ロック戦略図表完備
- [ ] AT-D2-05: コード例完備
- [ ] AT-D2-06: トラブルシューティング完備

**全項目合格で Sprint 2 ドキュメント受け入れ完了**

---

## 4. Sprint 5: Oracle Cloud デプロイ

### 4.1 受け入れテスト項目

| ID | テスト項目 | 期待結果 | 検証方法 |
|----|-----------|---------|---------|
| AT-S5-01 | Oracle Cloud VM 起動 | VM が Running 状態 | Oracle Console確認 |
| AT-S5-02 | SSH 接続成功 | SSH ログイン可能 | ssh ubuntu@VM_IP |
| AT-S5-03 | Docker インストール | docker --version 成功 | SSH 上で実行 |
| AT-S5-04 | Docker Compose インストール | docker compose version 成功 | SSH 上で実行 |
| AT-S5-05 | Resonant Engine デプロイ | 全サービス起動 | docker compose ps |
| AT-S5-06 | PostgreSQL 接続 | DB 接続成功 | psql 接続テスト |
| AT-S5-07 | Backend API 起動 | /health が 200 OK | curl localhost:8000/health |
| AT-S5-08 | Frontend 起動 | 画面表示成功 | curl localhost:3000 |
| AT-S5-09 | ドメイン DNS 設定 | A レコード設定完了 | nslookup 確認 |
| AT-S5-10 | SSL 証明書取得 | Let's Encrypt 証明書有効 | certbot certificates |
| AT-S5-11 | HTTPS 接続成功 | https://resonant-engine.com が表示 | ブラウザ確認 |
| AT-S5-12 | API HTTPS 接続成功 | https://api.resonant-engine.com/docs が表示 | ブラウザ確認 |
| AT-S5-13 | 自動起動設定 | systemd サービス有効 | systemctl status |
| AT-S5-14 | データ永続化 | VM 再起動後もデータ保持 | VM 再起動テスト |

### 4.2 テスト手順

#### 4.2.1 VM 起動確認

```bash
# 1. Oracle Cloud Console にログイン
# https://cloud.oracle.com/

# 2. Compute → Instances で VM 確認
# 期待される状態: Running (緑アイコン)

# 3. Public IP 確認
# 例: 123.45.67.89
```

#### 4.2.2 SSH 接続テスト

```bash
# SSH 接続
ssh ubuntu@123.45.67.89

# 期待される出力:
# Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-1026-oracle aarch64)
# ...
# ubuntu@resonant-engine-vm:~$
```

#### 4.2.3 Docker 環境確認

```bash
# VM 上で実行

# Docker バージョン確認
docker --version
# 期待される出力: Docker version 24.0.7, build afdd53b

# Docker Compose バージョン確認
docker compose version
# 期待される出力: Docker Compose version v2.21.0
```

#### 4.2.4 アプリケーション起動確認

```bash
# VM 上で実行

# Resonant Engine ディレクトリに移動
cd ~/resonant-engine/docker

# Docker Compose 起動
docker compose -f docker-compose.production.yml up -d

# コンテナステータス確認
docker compose ps

# 期待される出力:
# NAME                IMAGE                          STATUS
# resonant-db         postgres:15-alpine            Up (healthy)
# resonant-backend    resonant-backend:latest       Up (healthy)
# resonant-frontend   resonant-frontend:latest      Up
# resonant-intent     resonant-intent-bridge:latest Up
```

#### 4.2.5 ヘルスチェック

```bash
# VM 上で実行

# Backend API ヘルスチェック
curl http://localhost:8000/health

# 期待される出力:
# {"status":"healthy","timestamp":"2025-11-18T12:34:56Z"}

# Frontend 確認
curl http://localhost:3000

# 期待される出力:
# <!DOCTYPE html>
# <html lang="en">
#   <head>
#     <title>Resonant Engine</title>
# ...
```

#### 4.2.6 HTTPS 接続確認

```bash
# ローカルマシンから実行

# HTTPS 接続テスト
curl -I https://resonant-engine.com

# 期待される出力:
# HTTP/2 200
# server: nginx/1.18.0
# content-type: text/html
# ...

# API エンドポイント確認
curl https://api.resonant-engine.com/health

# 期待される出力:
# {"status":"healthy","timestamp":"2025-11-18T12:34:56Z"}

# ブラウザで確認
# https://resonant-engine.com
# https://api.resonant-engine.com/docs (Swagger UI)
```

#### 4.2.7 SSL 証明書確認

```bash
# VM 上で実行

# 証明書確認
sudo certbot certificates

# 期待される出力:
# Found the following certs:
#   Certificate Name: resonant-engine.com
#     Domains: resonant-engine.com api.resonant-engine.com
#     Expiry Date: 2026-02-16 12:34:56+00:00 (VALID: 89 days)
#     Certificate Path: /etc/letsencrypt/live/resonant-engine.com/fullchain.pem
#     Private Key Path: /etc/letsencrypt/live/resonant-engine.com/privkey.pem
```

#### 4.2.8 自動起動確認

```bash
# VM 上で実行

# systemd サービス確認
sudo systemctl status resonant-engine

# 期待される出力:
# ● resonant-engine.service - Resonant Engine Docker Compose
#    Loaded: loaded (/etc/systemd/system/resonant-engine.service; enabled; vendor preset: enabled)
#    Active: active (exited) since Mon 2025-11-18 12:34:56 UTC; 1h 23min ago
```

#### 4.2.9 データ永続化テスト

```bash
# VM 上で実行

# 1. テストデータ投入
curl -X POST http://localhost:8000/api/intents \
  -H "Content-Type: application/json" \
  -d '{"description":"Test Intent for Persistence","priority":3}'

# Intent ID を記録（例: 550e8400-e29b-41d4-a716-446655440000）

# 2. VM 再起動
sudo reboot

# 3. 再接続（1-2分後）
ssh ubuntu@123.45.67.89

# 4. データ確認
curl http://localhost:8000/api/intents/550e8400-e29b-41d4-a716-446655440000

# 期待される出力: Intent データが返ってくる
```

### 4.3 合格基準チェックリスト

- [ ] AT-S5-01: Oracle Cloud VM 起動
- [ ] AT-S5-02: SSH 接続成功
- [ ] AT-S5-03: Docker インストール
- [ ] AT-S5-04: Docker Compose インストール
- [ ] AT-S5-05: Resonant Engine デプロイ
- [ ] AT-S5-06: PostgreSQL 接続
- [ ] AT-S5-07: Backend API 起動
- [ ] AT-S5-08: Frontend 起動
- [ ] AT-S5-09: ドメイン DNS 設定
- [ ] AT-S5-10: SSL 証明書取得
- [ ] AT-S5-11: HTTPS 接続成功
- [ ] AT-S5-12: API HTTPS 接続成功
- [ ] AT-S5-13: 自動起動設定
- [ ] AT-S5-14: データ永続化

**全項目合格で Sprint 5 受け入れ完了**

---

## 5. Claude API 統合検証

### 5.1 受け入れテスト項目

| ID | テスト項目 | 期待結果 | 検証方法 |
|----|-----------|---------|---------|
| AT-C-01 | Claude API 接続成功 | API 呼び出しが成功 | pytest実行 |
| AT-C-02 | Intent 処理成功 | Intent → Claude → 結果取得 | pytest実行 |
| AT-C-03 | Prompt 構築正常 | 適切な Prompt が生成される | ログ確認 |
| AT-C-04 | レスポンス解析成功 | Claude レスポンスが解析される | pytest実行 |
| AT-C-05 | Token 使用量記録 | token_usage テーブルに記録 | DB確認 |
| AT-C-06 | コスト計算正確 | 正しいコストが計算される | スクリプト実行 |
| AT-C-07 | キャッシング動作 | 同一 Prompt でキャッシュヒット | pytest実行 |
| AT-C-08 | キャッシュヒット率 | > 30% | メトリクス確認 |
| AT-C-09 | エラーハンドリング | API エラー時に適切な処理 | pytest実行 |
| AT-C-10 | レスポンスタイム | < 3秒 | pytest実行 |

### 5.2 テスト手順

#### 5.2.1 環境準備

```bash
# API キー設定
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# .env ファイル確認
cat .env | grep ANTHROPIC_API_KEY
```

#### 5.2.2 統合テスト実行

```bash
# Claude API 統合テスト実行
cd /Users/zero/Projects/resonant-engine/
pytest tests/integration/test_claude_api.py -v

# 期待される出力:
# tests/integration/test_claude_api.py::test_claude_api_integration PASSED
# tests/integration/test_claude_api.py::test_token_usage_tracking PASSED
# tests/integration/test_claude_api.py::test_response_caching PASSED
# tests/integration/test_claude_api.py::test_cache_hit_rate PASSED
# tests/integration/test_claude_api.py::test_error_handling PASSED
# 5 passed in 8.45s
```

#### 5.2.3 Token 使用量確認

```bash
# PostgreSQL 接続
docker compose exec db psql -U resonant -d resonant

# Token 使用量クエリ
SELECT * FROM token_usage ORDER BY timestamp DESC LIMIT 10;

# 期待される出力:
#                  id                  |      timestamp      |     model      | prompt_tokens | completion_tokens | total_cost_usd
# ------------------------------------+---------------------+----------------+---------------+-------------------+----------------
#  550e8400-e29b-41d4-a716-446655440000 | 2025-11-18 12:34:56 | claude-sonnet-4 |           150 |               450 |          0.0075
# ...

# 終了
\q
```

#### 5.2.4 月間コスト計算

```bash
# コスト集計スクリプト実行
cd /Users/zero/Projects/resonant-engine/ && \
source venv/bin/activate && \
python scripts/calculate_token_cost.py

# 期待される出力:
# 📊 Monthly Token Usage (2025-11)
#   Prompt Tokens: 15,234
#   Completion Tokens: 45,678
#   Total Tokens: 60,912
#   Total Cost: $8.45
```

#### 5.2.5 キャッシング確認

```bash
# キャッシングテスト実行（詳細出力）
pytest tests/integration/test_claude_api.py::test_cache_hit_rate -v -s

# 期待される出力:
# 📊 Cache Metrics:
#   Total Requests: 100
#   Cache Hits: 35
#   Cache Misses: 65
#   Cache Hit Rate: 35.0%  ← 30%以上であること
```

### 5.3 合格基準チェックリスト

- [ ] AT-C-01: Claude API 接続成功
- [ ] AT-C-02: Intent 処理成功
- [ ] AT-C-03: Prompt 構築正常
- [ ] AT-C-04: レスポンス解析成功
- [ ] AT-C-05: Token 使用量記録
- [ ] AT-C-06: コスト計算正確
- [ ] AT-C-07: キャッシング動作
- [ ] AT-C-08: キャッシュヒット率 > 30%
- [ ] AT-C-09: エラーハンドリング
- [ ] AT-C-10: レスポンスタイム < 3秒

**全項目合格で Claude API 統合検証受け入れ完了**

---

## 6. Kana 実装 Phase 1

### 6.1 受け入れテスト項目

| ID | テスト項目 | 期待結果 | 検証方法 |
|----|-----------|---------|---------|
| AT-K-01 | KanaTranslator クラス実装 | translator.py が存在 | ファイル確認 |
| AT-K-02 | translate_to_schema 実装 | Yuno → PostgreSQL 翻訳成功 | pytest実行 |
| AT-K-03 | translate_to_fastapi 実装 | Yuno → FastAPI 翻訳成功 | pytest実行 |
| AT-K-04 | translate_to_react 実装 | Yuno → React 翻訳成功 | pytest実行 |
| AT-K-05 | KanaAuditor クラス実装 | auditor.py が存在 | ファイル確認 |
| AT-K-06 | 設計監査機能 | 整合性チェック成功 | pytest実行 |
| AT-K-07 | スコープ整合確認 | L1/L2/L3 チェック成功 | pytest実行 |
| AT-K-08 | 用語一貫性チェック | 用語マッピング確認成功 | pytest実行 |
| AT-K-09 | レポート生成 | AuditReport 生成成功 | pytest実行 |
| AT-K-10 | テストカバレッジ | > 80% | pytest --cov |
| AT-K-11 | 10ドキュメント翻訳成功 | 10個のYunoドキュメント翻訳 | 手動確認 |
| AT-K-12 | 翻訳精度 | > 90% | Yuno レビュー |

### 6.2 テスト手順

#### 6.2.1 ファイル存在確認

```bash
# Kana モジュール確認
ls -la bridge/kana/

# 期待される出力:
# __init__.py
# translator.py
# auditor.py
# consistency_checker.py
# report_generator.py
# prompts/
# templates/
```

#### 6.2.2 翻訳エンジンテスト

```bash
# Kana 翻訳テスト実行
pytest tests/kana/test_translator.py -v

# 期待される出力:
# tests/kana/test_translator.py::TestKanaTranslator::test_translate_yuno_to_schema PASSED
# tests/kana/test_translator.py::TestKanaTranslator::test_translate_yuno_to_fastapi PASSED
# tests/kana/test_translator.py::TestKanaTranslator::test_translate_yuno_to_react PASSED
# 3 passed in 12.34s
```

#### 6.2.3 設計監査テスト

```bash
# Kana 監査テスト実行
pytest tests/kana/test_auditor.py -v

# 期待される出力:
# tests/kana/test_auditor.py::TestKanaAuditor::test_audit_schema PASSED
# tests/kana/test_auditor.py::TestKanaAuditor::test_scope_alignment_check PASSED
# tests/kana/test_auditor.py::TestKanaAuditor::test_terminology_consistency_check PASSED
# 3 passed in 8.23s
```

#### 6.2.4 カバレッジ確認

```bash
# Kana モジュールカバレッジ測定
pytest tests/kana/ --cov=bridge.kana --cov-report=term --cov-report=html

# 期待される出力:
# bridge/kana/translator.py           120    15    87%
# bridge/kana/auditor.py               80    10    87%
# bridge/kana/consistency_checker.py   60     8    86%
# ...
# TOTAL                               350    40    88%  ← 80%以上
```

#### 6.2.5 実際の翻訳テスト

```bash
# Yuno ドキュメント翻訳テスト
cd /Users/zero/Projects/resonant-engine/
source venv/bin/activate
python -c "
from bridge.kana.translator import KanaTranslator
import asyncio
import os

async def main():
    translator = KanaTranslator(os.getenv('ANTHROPIC_API_KEY'))

    # ERF ドキュメント翻訳
    schema = await translator.translate_to_schema(
        'docs/07_philosophy/yuno_documents/emotion_resonance_filter_detailed.md'
    )
    print('=== Generated PostgreSQL Schema ===')
    print(schema)

asyncio.run(main())
"

# 期待される出力:
# === Generated PostgreSQL Schema ===
# -- Yuno思想: Emotion Resonance Filter (ERF)
# -- スコープレベル: L2 (横断)
# -- 整合性確認: 呼吸の一貫性を保持
#
# CREATE TABLE emotion_resonance (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     intensity NUMERIC(3,2) CHECK (intensity >= 0 AND intensity <= 1),
#     valence NUMERIC(3,2) CHECK (valence >= -1 AND valence <= 1),
#     cadence NUMERIC(3,2) CHECK (cadence >= 0 AND cadence <= 1),
#     is_detune BOOLEAN DEFAULT FALSE,
#     created_at TIMESTAMP NOT NULL DEFAULT NOW()
# );
```

#### 6.2.6 10ドキュメント翻訳テスト

```bash
# 10個のYunoドキュメントを順次翻訳
for doc in docs/07_philosophy/yuno_documents/*.md; do
    echo "Translating: $doc"
    python -c "
from bridge.kana.translator import KanaTranslator
import asyncio
import os

async def main():
    translator = KanaTranslator(os.getenv('ANTHROPIC_API_KEY'))
    schema = await translator.translate_to_schema('$doc')
    with open('output/$(basename $doc .md)_schema.sql', 'w') as f:
        f.write(schema)

asyncio.run(main())
    "
done

# 生成されたスキーマ確認
ls -la output/*.sql

# 期待される出力: 10個の .sql ファイル
```

### 6.3 合格基準チェックリスト

- [ ] AT-K-01: KanaTranslator クラス実装
- [ ] AT-K-02: translate_to_schema 実装
- [ ] AT-K-03: translate_to_fastapi 実装
- [ ] AT-K-04: translate_to_react 実装
- [ ] AT-K-05: KanaAuditor クラス実装
- [ ] AT-K-06: 設計監査機能
- [ ] AT-K-07: スコープ整合確認
- [ ] AT-K-08: 用語一貫性チェック
- [ ] AT-K-09: レポート生成
- [ ] AT-K-10: テストカバレッジ > 80%
- [ ] AT-K-11: 10ドキュメント翻訳成功
- [ ] AT-K-12: 翻訳精度 > 90%（Yunoレビュー）

**全項目合格で Kana Phase 1 受け入れ完了**

---

## 7. 総合受け入れテスト

### 7.1 全機能統合テスト

#### 7.1.1 エンドツーエンドシナリオ

**シナリオ**: 新しいIntentの作成から処理完了まで

```bash
# 1. Frontend から Intent 作成（ブラウザ操作）
# https://resonant-engine.com → Intents ページ
# → 「New Intent」ボタンクリック
# → Description: "Implement user authentication system"
# → Priority: 5
# → 「Create」ボタンクリック

# 2. Intent Bridge が自動検知（0.004秒以内）
# → ログ確認
docker compose logs intent_bridge | tail -20

# 期待される出力:
# [2025-11-18 12:34:56] INFO: Received intent notification: 550e8400-...
# [2025-11-18 12:34:56] INFO: Processing intent...
# [2025-11-18 12:34:56] INFO: Calling Claude API...
# [2025-11-18 12:34:58] INFO: Intent processing completed

# 3. Claude API 処理
# → token_usage テーブル確認
docker compose exec db psql -U resonant -d resonant -c \
  "SELECT * FROM token_usage ORDER BY timestamp DESC LIMIT 1;"

# 4. 処理結果確認
# → Frontend で Intent 詳細確認
# Status: completed
# Result: [Claude が生成した実装提案]

# 5. 通知確認
# → Frontend 右上の通知ベルに新着通知
```

#### 7.1.2 パフォーマンステスト（100並列）

```bash
# 100個の Intent を同時作成
python scripts/create_100_intents.py

# 期待される結果:
# - 全て処理完了
# - デッドロック発生率 < 1%
# - p99レイテンシ < 500ms
# - スループット > 50 ops/sec

# 処理状況確認
docker compose exec db psql -U resonant -d resonant -c \
  "SELECT status, COUNT(*) FROM intents GROUP BY status;"

# 期待される出力:
#   status   | count
# -----------+-------
#  completed |   100
```

#### 7.1.3 データ永続化テスト

```bash
# 1. テストデータ投入
curl -X POST https://api.resonant-engine.com/api/intents \
  -H "Content-Type: application/json" \
  -d '{"description":"Test Persistence","priority":3}'

# Intent ID 記録

# 2. Docker 再起動
cd docker && docker compose restart

# 3. データ確認（1分後）
curl https://api.resonant-engine.com/api/intents/{intent_id}

# 期待される結果: データが保持されている
```

#### 7.1.4 SSL/HTTPS テスト

```bash
# SSL証明書確認
openssl s_client -connect resonant-engine.com:443 -servername resonant-engine.com < /dev/null 2>/dev/null | openssl x509 -noout -dates

# 期待される出力:
# notBefore=Nov 18 00:00:00 2025 GMT
# notAfter=Feb 16 23:59:59 2026 GMT

# HTTPS接続テスト
curl -I https://resonant-engine.com
curl -I https://api.resonant-engine.com

# 期待される出力: HTTP/2 200
```

### 7.2 総合合格基準チェックリスト

#### Sprint 2
- [ ] 並行制御テスト 36+件 全 PASS
- [ ] テストカバレッジ > 80%
- [ ] パフォーマンスベースライン達成
- [ ] ドキュメント完備（3ファイル）

#### Sprint 5
- [ ] Oracle Cloud VM 稼働
- [ ] HTTPS 公開成功
- [ ] SSL 証明書有効
- [ ] 自動起動設定完了
- [ ] データ永続化確認

#### Claude API
- [ ] API 統合成功
- [ ] Token 使用量追跡動作
- [ ] キャッシング動作（ヒット率 > 30%）
- [ ] 月間コスト < $50

#### Kana Phase 1
- [ ] 翻訳エンジン実装
- [ ] 設計監査機能実装
- [ ] テストカバレッジ > 80%
- [ ] 10ドキュメント翻訳成功

#### 総合
- [ ] エンドツーエンドシナリオ成功
- [ ] 100並列処理成功
- [ ] データ永続化成功
- [ ] HTTPS 接続成功

### 7.3 最終確認

```bash
# 全テスト一括実行
cd /Users/zero/Projects/resonant-engine/
pytest tests/ -v --cov=bridge --cov-report=html

# 期待される出力:
# ==================== test session starts ====================
# ...
# tests/concurrency/         36 passed
# tests/integration/         15 passed
# tests/kana/                12 passed
# tests/unit/                45 passed
# ==================== 108 passed in 123.45s ===================
# Coverage: 85%
```

---

## 8. 受け入れ完了報告

### 8.1 報告書作成

```bash
# 受け入れテスト完了報告書作成
touch docs/reports/acceptance_test_completion_report_v2.0.md
```

**報告書内容**:
```markdown
# Resonant Engine v2.0 受け入れテスト完了報告書

## テスト実施日
2025年11月18日 - 2025年12月31日

## テスト結果サマリー

| カテゴリ | テスト項目数 | 合格 | 不合格 | 合格率 |
|---------|------------|-----|--------|--------|
| Sprint 2 並行制御 | 10 | 10 | 0 | 100% |
| Sprint 2 ドキュメント | 6 | 6 | 0 | 100% |
| Sprint 5 デプロイ | 14 | 14 | 0 | 100% |
| Claude API | 10 | 10 | 0 | 100% |
| Kana Phase 1 | 12 | 12 | 0 | 100% |
| **総合** | **52** | **52** | **0** | **100%** |

## カバレッジ

- 全体カバレッジ: 85%
- bridge.core: 82%
- bridge.kana: 88%

## パフォーマンス

- p99レイテンシ: 423ms (基準: < 500ms) ✅
- スループット: 54 ops/sec (基準: > 50 ops/sec) ✅
- デッドロック発生率: 0.8% (基準: < 1%) ✅

## 総合評価

**合格** - 全受け入れ基準を満たしています。

## 承認

- テスト担当: Kana（翻訳層）
- プロダクトオーナー: 加藤宏啓
- 承認日: 2025年XX月XX日
```

### 8.2 リリース準備

```bash
# 1. 最終コミット
git add .
git commit -m "Complete Resonant Engine v2.0 (Sprint 2-5, Kana Phase 1)

All acceptance tests PASS (52/52)
Test coverage: 85%
Performance benchmarks achieved

Sprint 2: Concurrency control ✅
Sprint 5: Oracle Cloud deploy ✅
Claude API: Integration complete ✅
Kana Phase 1: Translation engine ✅"

# 2. タグ作成
git tag -a v2.0.0 -m "Resonant Engine v2.0 Release

- Sprint 2: Concurrency control with deadlock retry
- Sprint 5: Oracle Cloud production deploy
- Claude API integration with token tracking
- Kana Phase 1: Yuno to specification translation"

# 3. プッシュ
git push -u origin <current-branch>
git push origin v2.0.0

# 4. プルリクエスト作成
# （GitHub Web UI または gh コマンド）
```

---

**受け入れテスト仕様書バージョン**: v2.0
**最終更新**: 2025年11月18日
**承認**: 加藤宏啓（Hiroaki Kato）
