# Resonant Engine - 機能とコンポーネントの完全分類

## 📂 コンポーネント分類の概要

Resonant Engineのすべてのコンポーネントを**実態に基づいて**以下の4つに分類：

1. **独立したデーモンプロセス** - 起動して常駐するプロセス
2. **ライブラリ/モジュール** - 他のプログラムから読み込まれる
3. **スタンドアロンスクリプト/CLIツール** - 必要時に単発実行
4. **シェルスクリプト** - Bash/Zshスクリプト
5. **ログファイル** - 各種ログデータ

---

## 1️⃣ 独立したデーモンプロセス（起動して常駐）

### ✅ 稼働中
| ファイル | ポート/PID | 役割 | 起動方法 |
|---------|----------|------|---------|
| `daemon/observer_daemon.py` | PID 59008 | 外部更新検知、Git自動同期 | `python3 -m daemon.observer_daemon &` |
| `utils/github_webhook_receiver.py` | Port 5001 | GitHub Webhook受信サーバー | `python3 utils/github_webhook_receiver.py &` |

### ❌ 停止中（パス不整合が原因）
| ファイル | 役割 | 問題 | 修正方法 |
|---------|------|------|---------|
| `daemon/resonant_daemon.py` | Intent監視、Re-evaluation Bridge起動 | 古いパス `/Users/zero/Projects/kiro-v3.1` | パス修正して起動 |

---

## 2️⃣ ライブラリ/モジュール（他のプログラムから読み込まれる）

### デーモン補助ライブラリ
| ファイル | 提供するもの | 使用例 |
|---------|------------|-------|
| `daemon/hypothesis_trace.py` | `HypothesisTrace`クラス | `tracer = HypothesisTrace()` |
| `daemon/log_archiver.py` | `archive(reason)`関数 | `log_archiver.archive("boot")` |

### イベントストリーム関連
| ファイル | 提供するもの | 用途 |
|---------|------------|------|
| `utils/resonant_event_stream.py` | `get_stream()`関数 | 統一イベントストリームへの記録 |
| `utils/resilient_event_stream.py` | `ResilientEventStream`クラス | エラーリカバリー付きイベント記録 |
| `utils/trace_events.py` | イベント関連ユーティリティ | イベント処理補助 |

### エラーハンドリング関連
| ファイル | 提供するもの | 用途 |
|---------|------------|------|
| `utils/retry_strategy.py` | リトライ戦略クラス群 | ExponentialBackoff, LinearBackoff等 |
| `utils/error_recovery.py` | `with_retry()`関数、`ErrorClassifier` | 自動リトライとエラー分類 |
| `utils/metrics_collector.py` | `get_metrics_collector()`関数 | メトリクス収集・集計 |

### Notion/外部連携
| ファイル | 提供するもの | 用途 |
|---------|------------|------|
| `utils/context_api.py` | Context API関連 | コンテキスト管理 |
| `utils/intent_logger.py` | Intent記録機能 | 意図のログ記録 |

---

## 3️⃣ スタンドアロンスクリプト/CLIツール（必要時に単発実行）

### CLIツール（コマンドライン実行）
| ファイル | 用途 | 実行例 |
|---------|------|-------|
| `utils/record_intent.py` | 開発意図の記録 | `python utils/record_intent.py "機能追加"` |
| `utils/error_recovery_cli.py` | エラー管理CLI | `python utils/error_recovery_cli.py status` |
| `utils/trace_linker.py` | Intent→Commit紐付け | `python utils/trace_linker.py` (Webhookから自動実行) |

### Notion関連スクリプト
| ファイル | 用途 | 実行タイミング |
|---------|------|-------------|
| `utils/notion_sync_agent.py` | Notion同期エージェント | 手動実行 or 定期実行 |
| `utils/backlog_sync_agent.py` | Backlog同期エージェント | 手動実行 or 定期実行 |
| `utils/create_notion_databases.py` | Notionデータベースセットアップ | 初回セットアップ時 |
| `utils/rename_notion_databases.py` | データベース名変更 | メンテナンス時 |

### 統計・レポート生成
| ファイル | 用途 | 実行例 |
|---------|------|-------|
| `utils/resonant_digest.py` | ダイジェストレポート生成 | `python utils/resonant_digest.py` |

---

## 4️⃣ シェルスクリプト（Bash/Zsh）

### ✅ 実行可能
| ファイル | 用途 | 実行方法 |
|---------|------|---------|
| `scripts/start_dev.sh` | 開発セッション開始 | `./scripts/start_dev.sh` |
| `scripts/end_dev.sh` | 開発セッション終了 | `./scripts/end_dev.sh` |
| `scripts/reval_bridge.sh` | Re-evaluation Bridge実行 | `./scripts/reval_bridge.sh` |
| `scripts/reflection_verification.sh` | リフレクション検証 | `./scripts/reflection_verification.sh` |
| `scripts/telemetry_feedback_loop.sh` | テレメトリーフィードバック | `./scripts/telemetry_feedback_loop.sh` |
| `scripts/notion_archive_push.sh` | Notionアーカイブ同期 | `./scripts/notion_archive_push.sh` |
| `scripts/auto_sync_phase3.sh` | 自動同期（Phase3） | `./scripts/auto_sync_phase3.sh` |
| `scripts/cleanup_phase1.sh` | クリーンアップ | `./scripts/cleanup_phase1.sh` |
| `scripts/make_overview.sh` | 概要レポート生成 | `./scripts/make_overview.sh` |
| `scripts/make_report.sh` | レポート生成 | `./scripts/make_report.sh` |
| `scripts/resonant_watcher.sh` | Resonant監視 | `./scripts/resonant_watcher.sh` |
| `scripts/setup_env.sh` | 環境セットアップ | `./scripts/setup_env.sh` |

### ❌ 動作不可（パス不整合）
| ファイル | 用途 | 問題 |
|---------|------|------|
| `daemon/resonant_bridge_daemon.sh` | Bridge自動起動デーモン | 古いパス `/Users/zero/Projects/kiro-v3.1` |
| `daemon/intent_watcher.sh` | Intent変更検知 | 古いパス `/Users/zero/Projects/kiro-v3.1` |

### その他
| ファイル | 用途 |
|---------|------|
| `daemon/auto_reflect.sh` | 自動リフレクション |
| `daemon/resonant_daemon_bridge.sh` | Daemon Bridge |
| `daemon/resonant_io_watcher.sh` | IO監視 |
| `utils/trace_auto.sh` | 自動Trace |

---

## 5️⃣ ログファイル

### イベントストリーム関連
| ファイル | 内容 | 更新頻度 |
|---------|------|---------|
| `logs/event_stream.jsonl` | 統一イベントストリーム | リアルタイム |
| `logs/webhook_log.jsonl` | GitHub Webhook受信ログ | pushイベント時 |
| `logs/trace_map.jsonl` | Intent→Commit紐付け | pushイベント後 |
| `logs/intent_log.jsonl` | Intent記録 | intent記録時 |

### エラー・デバッグ関連
| ファイル | 内容 | 用途 |
|---------|------|------|
| `logs/dead_letter_queue.jsonl` | デッドレターキュー | リトライ失敗イベント |
| `logs/metrics.json` | メトリクス統計 | リアルタイム |
| `logs/delivery_cache.json` | Webhook重複防止キャッシュ | Webhook受信時 |

### デーモンログ
| ファイル | 内容 | 生成元 |
|---------|------|-------|
| `daemon/logs/observer_daemon.log` | Observer動作ログ | observer_daemon.py |
| `logs/daemon.log` | Resonant Daemon動作ログ | resonant_daemon.py |
| `logs/daemon_bridge.log` | Bridge動作ログ | resonant_bridge_daemon.sh |
| `logs/resonant_state.log` | State記録 | resonant_daemon.py |

### HypothesisTrace関連
| ファイル | 内容 |
|---------|------|
| `daemon/hypothesis_trace_log.json` | 仮説検証ログ（JSON） |
| `daemon/hypothesis_trace_log.jsonl` | 仮説検証ログ（JSONL） |

### アーカイブ
| ディレクトリ | 内容 |
|----------|------|
| `daemon/logs/archive/` | 日付別アーカイブ |
| `daemon/logs/archive/YYYY-MM-DD/` | 各日のアーカイブデータ |
| `logs/archive_journal.jsonl` | アーカイブジャーナル |
| `logs/result_diff_*.log` | Git pull後の差分 |

### その他
| ファイル | 内容 |
|---------|------|
| `logs/telemetry_feedback.log` | テレメトリーフィードバック |
| `logs/last_commit.txt` | 最終コミットハッシュ（重複防止用） |


## 6️⃣ Notion連携（理論と実装の乖離）

### 理論上の構造（Yuno記憶）
- n8n連携は「思想的に吸収」
- Yuno → Kana → Tsumu の自動連携
- specsテーブルの「同期トリガー=Yes」を自動検知

### 実際の実装状態
| コンポーネント | 状態 | 役割 |
|-------------|------|------|
| `utils/notion_sync_agent.py` | ✅ 存在 | Notion API呼び出し、specs取得 |
| `utils/n8n/notion_writeback_v1.79.json` | ⚠️ `active: false` | 停止中のワークフロー |
| 定期実行の仕組み | ❌ **なし** | cron/launchd/デーモン不在 |

### 実際の使用方法
```bash
# 手動実行
python utils/notion_sync_agent.py
```

### 今後の実装候補
1. **デーモン化**: `daemon/notion_sync_daemon.py` を作成
2. **cronで定期実行**: 5分ごとにポーリング
3. **Notion Webhook**: Notion側から通知（要API設定）

---

## 📊 機能と担当コンポーネントのマッピング

### ✅ 動作している機能

#### 1. 外部更新検知
- **デーモン**: `daemon/observer_daemon.py` ✅
- **ライブラリ**: `hypothesis_trace.py`, `log_archiver.py`
- **ログ**: `daemon/logs/observer_daemon.log`, `logs/last_commit.txt`

#### 2. Git自動同期
- **デーモン**: `daemon/observer_daemon.py` ✅
- **ログ**: `logs/result_diff_*.log`

#### 3. HypothesisTrace記録
- **デーモン**: `daemon/observer_daemon.py` が使用
- **ライブラリ**: `daemon/hypothesis_trace.py` 📦
- **ログ**: `daemon/hypothesis_trace_log.json`

#### 4. GitHub Webhook受信
- **デーモン**: `utils/github_webhook_receiver.py` ✅ (Port 5001)
- **スクリプト**: `utils/trace_linker.py` (自動実行)
- **ログ**: `logs/webhook_log.jsonl`, `logs/delivery_cache.json`

#### 5. エラー回復システム
- **ライブラリ**: `utils/resilient_event_stream.py` 📦
- **ライブラリ**: `utils/retry_strategy.py` 📦
- **ライブラリ**: `utils/error_recovery.py` 📦
- **CLIツール**: `utils/error_recovery_cli.py` 🔧
- **ログ**: `logs/dead_letter_queue.jsonl`

#### 6. メトリクス収集
- **ライブラリ**: `utils/metrics_collector.py` 📦
- **CLIツール**: `utils/error_recovery_cli.py metrics` 🔧
- **ログ**: `logs/metrics.json`

---

### ❌ 動作していない機能

#### 1. Intent監視
- **デーモン**: `daemon/resonant_daemon.py` ❌ (停止中)
- **修正必要**: パス `/Users/zero/Projects/kiro-v3.1` → `/Users/zero/Projects/resonant-engine`
- **ログ**: `logs/daemon.log`, `logs/resonant_state.log`

#### 2. Re-evaluation Bridge自動起動
- **デーモン**: `daemon/resonant_daemon.py` ❌ (上記に依存)
- **シェル**: `scripts/reval_bridge.sh` ✅ (手動実行可)
- **依存関係**: resonant_daemon.py → reval_bridge.sh

#### 3. intent_protocol.json処理
- **シェル**: `daemon/resonant_bridge_daemon.sh` ❌ (パス不整合)
- **シェル**: `daemon/intent_watcher.sh` ❌ (パス不整合)
- **修正必要**: パス修正
- **ログ**: `logs/daemon_bridge.log`

#### 4. Yunoからの意図の自動処理
- **依存チェーン**:
  ```
  Yuno → intent_protocol.json
    ↓
  resonant_daemon.py ❌
    ↓
  reval_bridge.sh → resonant_bridge_daemon.sh ❌
    ↓
  intent_watcher.sh ❌
    ↓
  各種スクリプト
  ```
- **停止理由**: チェーン全体が停止

---

## 🔧 修正手順

### 最小限の修正（Intent監視を復活）

**1. resonant_daemon.py のパス修正**
```bash
nano /Users/zero/Projects/resonant-engine/daemon/resonant_daemon.py
```

```python
# 修正前
ROOT = Path("/Users/zero/Projects/kiro-v3.1")

# 修正後
ROOT = Path("/Users/zero/Projects/resonant-engine")
```

**2. デーモン起動**
```bash
cd /Users/zero/Projects/resonant-engine
nohup python3 -m daemon.resonant_daemon > daemon/logs/resonant_daemon.log 2>&1 &
```

**3. 動作確認**
```bash
ps aux | grep resonant_daemon
tail -f logs/daemon.log
```

---

### 完全修正（Intent自動処理を復活）

**1. resonant_bridge_daemon.sh のパス修正**
```bash
nano daemon/resonant_bridge_daemon.sh
```

```bash
# 修正前
ROOT="/Users/zero/Projects/kiro-v3.1"

# 修正後
ROOT="/Users/zero/Projects/resonant-engine"
```

**2. intent_watcher.sh のパス修正**
```bash
nano daemon/intent_watcher.sh
```

```bash
# 修正前
ROOT="/Users/zero/Projects/kiro-v3.1"

# 修正後
ROOT="/Users/zero/Projects/resonant-engine"
```

**3. 実行権限確認**
```bash
chmod +x daemon/resonant_bridge_daemon.sh
chmod +x daemon/intent_watcher.sh
```

**4. テスト実行**
```bash
# Intent Protocol作成
echo '{"phase":"test","action":"verify"}' > bridge/intent_protocol.json

# ログ確認
tail -f logs/daemon.log
tail -f logs/daemon_bridge.log
```

---

## 📈 優先度マトリクス

| コンポーネント | 種類 | 必須度 | 状態 | 理由 |
|------------|------|-------|------|------|
| observer_daemon.py | デーモン | ✅ 必須 | ✅ 稼働中 | 外部更新検知・Git同期 |
| github_webhook_receiver.py | デーモン | ✅ 必須 | ✅ 稼働中 | GitHub連携 |
| resilient_event_stream.py | ライブラリ | ✅ 必須 | ✅ 利用中 | エラー回復基盤 |
| resonant_daemon.py | デーモン | 🟡 推奨 | ❌ 停止中 | Intent監視 |
| resonant_bridge_daemon.sh | シェル | 🟢 オプション | ❌ 停止中 | Intent自動処理 |
| intent_watcher.sh | シェル | 🟢 オプション | ❌ 停止中 | Intent変更検知 |

---

## 🎯 まとめ

### アーキテクチャ構成
- **独立デーモン**: 2つ稼働中（observer, webhook_receiver）
- **ライブラリ**: 10個以上（イベント、エラー、メトリクス）
- **CLIツール**: 3つ（record_intent, error_recovery_cli, trace_linker）
- **シェルスクリプト**: 15個以上
- **ログファイル**: 20種類以上

### 現在の課題
- **パス不整合**: 3ファイルのみ修正すれば完全復活
- **運用習慣**: Intent記録の習慣化が必要

### システム評価
- **技術的完成度**: ⭐⭐⭐⭐⭐ (5/5) - エンタープライズグレード
- **運用成熟度**: ⭐⭐⭐☆☆ (3/5) - 修正と習慣化が必要
- **修正難易度**: ⭐☆☆☆☆ (1/5) - パス修正のみ

---

## 📌 凡例
- ✅ = 稼働中
- ❌ = 停止中
- 📦 = ライブラリ/モジュール
- 🔧 = CLIツール
- 🟢 = オプション
- 🟡 = 推奨
- ⭐ = 必須
