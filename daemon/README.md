# Resonant Daemon - バックグラウンドサービス

Resonant Engine の Intent 処理デーモンをバックグラウンドサービスとして実行

## 📋 概要

- **自動起動**: macOS launchd によりシステム起動時に自動起動
- **プロセス監視**: クラッシュ時の自動再起動
- **ログローテーション**: 日次ログファイル、30日間保持
- **シグナルハンドリング**: SIGINT/SIGTERM でのグレースフルシャットダウン

## 🚀 使い方

### Daemon起動
```bash
./scripts/start_daemon.sh
```

### Daemon停止
```bash
./scripts/stop_daemon.sh
```

### Daemon再起動
```bash
./scripts/restart_daemon.sh
```

### ステータス確認
```bash
./scripts/status_daemon.sh
```

### ログ表示（リアルタイム）
```bash
./scripts/logs_daemon.sh
```

## 📝 ログファイル

ログは `daemon/logs/` 配下に保存されます:

- **daemon_YYYYMMDD.log**: メインログ（日次ローテーション）
- **stdout.log**: 標準出力
- **stderr.log**: 標準エラー出力
- **resonant_state.log**: 状態変更ログ

古いログファイルは30日後に自動削除されます。

## 🔧 設定

### launchd plist

`daemon/com.resonant.daemon.plist` がサービス定義ファイルです。

起動時に自動的に `~/Library/LaunchAgents/` にコピーされます。

### 環境変数

`.env` ファイルで以下を設定:

```env
DATABASE_URL=postgresql://resonant@localhost:5432/resonant
ANTHROPIC_API_KEY=your_api_key_here
```

## 🔍 動作確認

### 1. Daemonが起動しているか確認
```bash
launchctl list | grep com.resonant.daemon
```

### 2. プロセスIDを確認
```bash
cat daemon/pids/resonant_daemon.pid
```

### 3. Intent処理を確認
```bash
tail -f daemon/logs/daemon_$(date +%Y%m%d).log
```

## 🛠️ トラブルシューティング

### Daemonが起動しない

1. ログを確認:
   ```bash
   cat daemon/logs/stderr.log
   ```

2. 手動で起動してエラーを確認:
   ```bash
   venv/bin/python daemon/resonant_daemon_db.py
   ```

3. データベース接続を確認:
   ```bash
   psql -U resonant -d resonant -c "SELECT COUNT(*) FROM intents WHERE status='pending';"
   ```

### Daemonが停止しない

強制停止:
```bash
launchctl unload ~/Library/LaunchAgents/com.resonant.daemon.plist
kill $(cat daemon/pids/resonant_daemon.pid)
```

### ログが出力されない

ログディレクトリの権限を確認:
```bash
ls -la daemon/logs/
```

## 📊 機能

### Intent処理フロー

1. 5秒ごとに `intents` テーブルをポーリング
2. `status='pending'` の Intent を検出
3. Claude API (Kana) で処理
4. 結果を `intents` テーブルに保存 (`status='completed'`)
5. WebSocket 経由でフロントエンドに通知

### 自動再起動

- クラッシュ時: 10秒後に自動再起動
- 正常終了時: 再起動なし

### シグナルハンドリング

- **SIGINT (Ctrl+C)**: グレースフルシャットダウン
- **SIGTERM**: グレースフルシャットダウン

## 🔐 セキュリティ

- PIDファイルで二重起動を防止
- データベース接続プール使用
- API Key は環境変数で管理

## 📦 ファイル構成

```
daemon/
├── resonant_daemon_db.py       # Daemon本体
├── com.resonant.daemon.plist   # launchd設定
├── logs/                        # ログディレクトリ
│   ├── daemon_YYYYMMDD.log
│   ├── stdout.log
│   ├── stderr.log
│   └── resonant_state.log
└── pids/                        # PIDファイル
    └── resonant_daemon.pid

scripts/
├── start_daemon.sh             # 起動スクリプト
├── stop_daemon.sh              # 停止スクリプト
├── restart_daemon.sh           # 再起動スクリプト
├── status_daemon.sh            # ステータス確認
└── logs_daemon.sh              # ログ表示
```

## ⚙️ 開発者向け

### Daemon単体テスト

```bash
# 仮想環境を有効化
source venv/bin/activate

# Daemon実行（フォアグラウンド）
python daemon/resonant_daemon_db.py
```

### launchd 設定変更後

```bash
# 再読み込み
./scripts/restart_daemon.sh
```

## 📖 参考

- [macOS launchd](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Intent Processor DB](../dashboard/backend/intent_processor_db.py)
