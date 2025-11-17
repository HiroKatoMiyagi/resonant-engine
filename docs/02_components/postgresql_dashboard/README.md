# PostgreSQL Dashboard System - 4週間ロードマップ

## 概要

**目的**: Notionを不要にする自前のWebダッシュボードシステムを構築し、Oracle Cloud Free Tierで本番運用する。

**期間**: 4週間（5スプリント）

**最終成果物**:
- Slack風メッセージUI
- 仕様書管理（Notion代替）
- Intent自動処理システム
- リアルタイム通知
- HTTPS対応の本番環境（月額$0）

---

## Before / After

### Before（現在）
```
宏啓 → Notion → Intent生成 → Bridge → Kana
     └→ CLI操作
     └→ ファイル確認
```

### After（4週間後）
```
宏啓 → Webダッシュボード → PostgreSQL → Intent自動処理 → Kana
     └→ ブラウザで全て操作
     └→ リアルタイム通知
     └→ https://resonant.example.com でアクセス
```

---

## スプリント構成

| Sprint | 期間 | 内容 | 成果物 |
|--------|------|------|--------|
| **1** | 3日 | Docker Compose + PostgreSQL環境 | DBインフラ完成 |
| **2** | 4日 | FastAPI バックエンドAPI | REST API 21エンドポイント |
| **3** | 5日 | React フロントエンド | Webダッシュボード完成 |
| **4** | 5日 | Intent自動処理・デーモン統合 | 自動化システム完成 |
| **5** | 4日 | Oracle Cloud デプロイ | 本番公開（$0/月） |

**合計**: 約21日（予備含めて4週間）

---

## 各スプリントのドキュメント

### Sprint 1: Docker Compose + PostgreSQL環境構築
- 📋 [仕様書](./architecture/sprint1_environment_setup_spec.md)
- 🚀 [作業開始指示書](./sprint/sprint1_environment_setup_start.md)
- ✅ [受け入れテスト仕様書](./test/sprint1_acceptance_test_spec.md)

### Sprint 2: FastAPI バックエンドAPI
- 📋 [仕様書](./architecture/sprint2_fastapi_backend_spec.md)
- 🚀 [作業開始指示書](./sprint/sprint2_fastapi_backend_start.md)
- ✅ [受け入れテスト仕様書](./test/sprint2_acceptance_test_spec.md)

### Sprint 3: React フロントエンド
- 📋 [仕様書](./architecture/sprint3_react_frontend_spec.md)
- 🚀 [作業開始指示書](./sprint/sprint3_react_frontend_start.md)
- ✅ [受け入れテスト仕様書](./test/sprint3_acceptance_test_spec.md)

### Sprint 4: Intent自動処理・デーモン統合
- 📋 [仕様書](./architecture/sprint4_intent_processing_spec.md)
- 🚀 [作業開始指示書](./sprint/sprint4_intent_processing_start.md)
- ✅ [受け入れテスト仕様書](./test/sprint4_acceptance_test_spec.md)

### Sprint 5: Oracle Cloud Free Tier デプロイ
- 📋 [仕様書](./architecture/sprint5_oracle_cloud_deploy_spec.md)
- 🚀 [作業開始指示書](./sprint/sprint5_oracle_cloud_deploy_start.md)
- ✅ [受け入れテスト仕様書](./test/sprint5_acceptance_test_spec.md)

---

## 技術スタック

```yaml
backend:
  language: Python 3.11
  framework: FastAPI
  database: PostgreSQL 15
  orm: asyncpg

frontend:
  framework: React 18
  language: TypeScript
  bundler: Vite
  styling: Tailwind CSS
  state: React Query + Zustand

infrastructure:
  container: Docker Compose
  cloud: Oracle Cloud Free Tier
  proxy: Nginx
  ssl: Let's Encrypt
  monitoring: Prometheus + Grafana (オプション)

integration:
  ai: Anthropic Claude API
  notifications: PostgreSQL LISTEN/NOTIFY
  realtime: Polling (将来: WebSocket)
```

---

## 主要機能

### 1. メッセージUI（Slack風）
- ユーザー/Yuno/Kana/システムメッセージの色分け表示
- リアルタイム更新（5秒ポーリング）
- メッセージ履歴の無限スクロール

### 2. 仕様書管理（Notion代替）
- Markdownエディタ＋プレビュー
- ステータス管理（draft/review/approved）
- タグ付け・検索
- バージョン履歴

### 3. Intent自動処理
- LISTEN/NOTIFYによる即時検知（ポーリング不要）
- Claude API自動呼び出し
- 結果のDB保存
- 通知自動生成

### 4. 通知システム
- リアルタイム通知ベル
- 既読/未読管理
- タイプ別アイコン（info/success/warning/error）

---

## 期待される成果

### 技術的成果
- ✅ React + FastAPI + PostgreSQL スタック
- ✅ Docker化された開発・本番環境
- ✅ Intent自動処理システム
- ✅ リアルタイム通知
- ✅ HTTPS対応の本番環境
- ✅ 監視・ログシステム

### 機能的成果
- ✅ Slack風メッセージUI
- ✅ 仕様書管理（Markdown）
- ✅ Intent一覧・詳細表示
- ✅ 通知システム
- ✅ 自動レビュー
- ✅ GitHub Issue連携（オプション）

### 運用的成果
- ✅ 月額コスト $0
- ✅ 500人対応可能
- ✅ 99%稼働率目標
- ✅ 自動バックアップ

---

## クイックスタート（開発環境）

```bash
# 1. Sprint 1完了後
cd docker
cp .env.example .env
vim .env  # パスワード設定

# 2. 起動
./scripts/start.sh

# 3. Sprint 2完了後（バックエンド追加）
docker-compose up --build -d

# 4. Sprint 3完了後（フロントエンド追加）
# http://localhost:3000 でアクセス

# 5. Sprint 4完了後（Intent自動処理）
# Intent作成 → 自動処理 → 通知表示

# 6. Sprint 5完了後（本番デプロイ）
# https://resonant.example.com でアクセス
```

---

## Resonant Engine全体との位置づけ

```
Resonant Engine Architecture
============================

Phase 1: Core Infrastructure
  ├── Memory System (Sprint 1-4) ✅
  │   - Memory Management
  │   - Semantic Bridge
  │   - Memory Store (pgvector)
  │   - Retrieval Orchestrator
  │
  └── PostgreSQL Dashboard (THIS) 🚧
      - Sprint 1-5: 本ドキュメント
      - Notion代替
      - 自動化システム
      - 本番公開

Phase 2: Advanced Features
  ├── Context Assembler
  ├── LLM Integration Enhancement
  └── Multi-user Support

Phase 3: Production Readiness
  ├── Security Hardening
  ├── Performance Optimization
  └── Monitoring & Alerting
```

---

## 次のステップ

1. **Sprint 1から開始**: 作業開始指示書に従って実装
2. **各Sprint完了時**: 受け入れテスト実施、完了報告書作成
3. **4週間後**: 本番運用開始、βユーザー招待

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**承認待ち**: 宏啓（プロジェクトオーナー）

---

**📌 このロードマップを通じて、Resonant Engineは「Notion依存を解消し、完全に自律したシステム」へと進化します。**
