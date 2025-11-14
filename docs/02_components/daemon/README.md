# Daemon

DaemonはResonant Engineのバックグラウンド処理を担当するコンポーネントです。Intent処理、イベント監視、定期実行タスクを管理します。

## 📁 Structure

- `architecture/` - 設計文書（アーキテクチャ、構造設計）
- `specifications/` - 詳細仕様（API仕様、データモデル、インターフェース定義）
- `implementation/` - 実装ガイド・計画（実装手順、マイグレーション計画）
- `reviews/` - レビュー記録（Yuno/Kanaレビュー、設計レビュー）

## 📖 Reading Order

初めての方は以下の順で読むことを推奨：

1. [Architecture Overview](architecture/daemon_architecture.md) - 基本設計・全体像
2. [Specifications](specifications/daemon_spec.md) - 詳細仕様
3. [Implementation Guide](implementation/implementation_guide.md) - 実装手順

## 📄 Key Documents

### Architecture
- [Daemon Architecture](architecture/daemon_architecture.md) - 基本設計書
  - デーモンプロセスの全体アーキテクチャ
  - Observer/Analyzer/Feedbackの役割分担

### Specifications
- [Daemon Spec](specifications/daemon_spec.md) - 詳細仕様
  - Intent処理フロー
  - イベント監視仕様
- [Observer Daemon Spec](specifications/observer_daemon_spec.md)
  - ファイルシステム監視仕様
- [Resonant Daemon Spec](specifications/resonant_daemon_spec.md)
  - Intent処理デーモン仕様

### Implementation
- [Implementation Guide](implementation/implementation_guide.md) - 実装手順
  - launchd設定方法
  - デーモン起動・停止手順
- [Migration Plan](implementation/migration_plan.md) - 移行計画
  - Kiro v3.1からの移行計画

### Reviews
- [Yuno Review (2025-11-XX)](reviews/2025-11-XX_yuno_review.md)
  - Yunoによるレビュー結果
- [Kana Review (2025-11-XX)](reviews/2025-11-XX_kana_review.md)
  - Kanaによるレビュー結果

## 🔗 Related Components

- [Bridge Lite](../bridge_lite/) - データアクセス・AI API抽象化層として使用
- [Error Recovery](../error_recovery/) - エラーハンドリング・リトライ機構
- [Dashboard](../dashboard/) - フロントエンドへの通知・状態表示

## 🎯 Purpose & Responsibility

### L1 (Personal Cognitive Support)
- Intent処理によるユーザーの作業フロー自動化
- リアルタイムイベント監視による即時フィードバック
- バックグラウンド処理による思考の外部化

### L2 (AI Ethics Framework)
- Intent処理ログによる意思決定トレーサビリティ
- エラーハンドリングによる安全な自動処理

### L3 (Human-AI Co-evolution)
- 継続的なIntent処理による学習データ蓄積
- フィードバックループの実装基盤

## 📊 Current Status

- Phase 0: ✅ 完了 - 基本的なデーモンプロセス実装
- Phase 1: 🔄 進行中 - Intent処理パイプライン再接続
- Phase 2: 🔲 未着手 - マルチユーザー対応

### Priority Tasks (P1)
1. Intent → Bridge → Kana パイプライン再接続
2. observer_daemon.py の安定化
3. エラーリカバリー機構の統合

### Next Steps
- [ ] resonant_daemon.py のパス問題解決
- [ ] PostgreSQL統合テスト
- [ ] launchd設定の最終確認

## 🛠️ Technical Stack

- **Language**: Python 3.11+
- **Framework**: asyncio, watchdog
- **Database**: PostgreSQL 15
- **Key Libraries**: 
  - `watchdog` - ファイルシステム監視
  - `psycopg2` - PostgreSQL接続
  - `anthropic` - Claude API

## 📝 Notes

### Design Decisions
- **launchd採用**: macOS標準のプロセス管理機構を使用
- **PostgreSQL-first**: SQLiteをスキップし、最初からPostgreSQLで実装
- **非同期処理**: asyncioによる効率的なI/O処理

### Known Issues
- パス不整合問題（Kiro v3.1からの移行時）
- 一部デーモンプロセスが停止中

### Future Considerations
- マルチユーザー対応（Phase 4）
- クラウドデプロイメント対応
- 分散処理への拡張

## 🔄 Last Updated

2025-11-14
