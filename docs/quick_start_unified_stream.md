# 統一イベントストリーム クイックスタートガイド

Resonant Engineの「点」が「線」に繋がりました。  
このガイドで、統合されたイベントストリームをすぐに使い始められます。

---

## 🚀 5分で始める

### 1. 開発意図を記録する

開発を始める前に、何をしようとしているか記録：

```bash
$ python utils/record_intent.py "Webhook受信のエラーハンドリング改善"

✅ 意図を記録しました
   Event ID: EVT-20251105-155517-c23469
   Intent: Webhook受信のエラーハンドリング改善
```

### 2. システムが自動記録

以降、システムが自動的に：
- Git更新を検知 → イベント記録
- Webhook受信 → イベント記録
- Backlog同期 → イベント記録
- 仮説の検証 → イベント記録

**あなたは何もしなくてOK。全て自動です。**

### 3. 最近の活動を確認

```bash
$ python utils/trace_events.py recent

📊 最近の20件のイベント:

💡 [2025-11-05T15:55:17] INTENT from user
   Intent: Webhook受信のエラーハンドリング改善

⚡ [2025-11-05T15:55:11] ACTION from observer_daemon
   action: git_pull

✅ [2025-11-05T15:55:11] RESULT from observer_daemon
   status: success
```

### 4. 「なぜ？」を遡る

あるイベントが「なぜ起きたか」を追跡：

```bash
$ python utils/trace_events.py causality EVT-20251105-155517-c23469

🔗 因果関係チェーン:

原因 → 結果の流れ:

💡 INTENT from user
  ↓
⚡ ACTION from observer_daemon
  ↓
✅ RESULT from observer_daemon
```

---

## 📚 よく使うコマンド

### 最近のイベントを見る
```bash
# デフォルト20件
$ python utils/trace_events.py recent

# 50件表示
$ python utils/trace_events.py recent 50
```

### 特定のシステムのイベントを見る
```bash
# observer_daemonのイベント
$ python utils/trace_events.py source observer_daemon

# github_webhookのイベント
$ python utils/trace_events.py source github_webhook

# backlog_syncのイベント
$ python utils/trace_events.py source backlog_sync
```

### タグで絞り込む
```bash
# Gitに関連するイベント
$ python utils/trace_events.py tag git

# エラーイベント
$ python utils/trace_events.py tag error

# Webhookイベント
$ python utils/trace_events.py tag webhook
```

### 週次/月次サマリーを見る
```bash
# 過去7日間のサマリー
$ python utils/trace_events.py summary

# 過去30日間のサマリー
$ python utils/trace_events.py summary 30

📈 過去7日間の活動サマリー
   総イベント数: 142件

イベント種別:
  - action: 58件
  - result: 45件
  - observation: 23件
  - intent: 10件
  - hypothesis: 6件

発生源:
  - observer_daemon: 76件
  - github_webhook: 32件
  - user: 20件
  - backlog_sync: 14件
```

### 仮説のタイムラインを見る
```bash
$ python utils/trace_events.py hypothesis HYP-20251105-143000-abc123

🧠 仮説 HYP-20251105-143000-abc123 のタイムライン:

[仮説記録] → [検証実行] → [結果確認]
```

---

## 🎯 実践例

### シナリオ1: 「このコミットは何のため？」

**Before（統合前）**:
```
observer_daemon.log を grep で検索
→ git log で関連コミット探す
→ hypothesis_trace_log.json を手動で確認
→ 30分かかる
```

**After（統合後）**:
```bash
# 最近のGit関連イベントを見る
$ python utils/trace_events.py tag git

# 結果イベントのIDをコピー
# 因果関係を遡る
$ python utils/trace_events.py causality EVT-20251105-155511-260507

# 3秒で因果関係が分かる
💡 INTENT: observer_daemonのテスト
  ↓
⚡ ACTION: git_pull
  ↓
✅ RESULT: success
```

### シナリオ2: 「Backlogの仕様変更がどう反映された？」

```bash
# Backlog同期イベントを確認
$ python utils/trace_events.py source backlog_sync

# 特定の課題を取得したイベントを見つける
# そのイベントIDを使って、関連する全イベントを追跡

# 結果: Backlog更新 → Git変更 → 仮説検証 の流れが見える
```

### シナリオ3: 「今週何をしたか振り返る」

```bash
$ python utils/trace_events.py summary 7

# 自動集計結果:
# - 意図: 12件（何を目指したか）
# - 行動: 47件（何を実行したか）
# - 結果: 38件（どうなったか）

# AIに報告書を作成させる時の材料になる
```

---

## 🧠 AIと連携する（次のステップ）

### Cursorで使う

1. **開発開始時に意図を記録**:
```bash
$ python utils/record_intent.py "ユーザー認証機能の追加"
```

2. **Cursorで開発**:
   - 通常通りコーディング
   - observer_daemonが自動記録

3. **Cursorで振り返り**:
```bash
# 最近の活動を確認
$ python utils/trace_events.py recent 20

# この出力をCursorに貼り付けて:
# 「この一連の作業を要約して」
```

### Claude Desktopで使う

```bash
# イベントストリームをJSONで出力
$ cat logs/event_stream.jsonl | tail -50 > /tmp/recent_events.json

# Claude Desktopで:
# 「このイベントストリームから開発の流れを説明して」
```

---

## 🔧 トラブルシューティング

### Q: イベントが記録されない

**A**: システムが起動しているか確認:
```bash
# observer_daemon が起動しているか
$ ps aux | grep observer_daemon

# 起動していなければ
$ cd /Users/zero/Projects/resonant-engine
$ nohup python3 daemon/observer_daemon.py > /dev/null 2>&1 &
```

### Q: イベントストリームのファイルはどこ？

**A**: `logs/event_stream.jsonl`
```bash
# 直接確認
$ tail -f logs/event_stream.jsonl

# または
$ cat logs/event_stream.jsonl | jq .
```

### Q: 古いイベントを削除したい

**A**: 期間を指定してアーカイブ（将来実装予定）
```bash
# 現在は手動でバックアップ
$ cp logs/event_stream.jsonl logs/archive/event_stream_backup_$(date +%Y%m%d).jsonl
$ echo '[]' > logs/event_stream.jsonl
```

---

## 📊 可視化（将来実装予定）

### Phase 3で追加予定:

**Web UI**:
```
http://localhost:5002/events/timeline
→ イベントのタイムライン表示

http://localhost:5002/events/causality/EVT-xxx
→ 因果関係の可視化グラフ

http://localhost:5002/dashboard
→ リアルタイムダッシュボード
```

---

## 🎉 まとめ

### 統合前（点）
- 5つの独立したログファイル
- 相互参照不可
- 「なぜ？」が分からない

### 統合後（線）
- 1つの統一タイムライン
- 因果関係を追跡可能
- 「なぜこの変更が起きたか」が分かる

### 使い方
```bash
# 意図を記録
python utils/record_intent.py "<何をするか>"

# 最近の活動を確認
python utils/trace_events.py recent

# 因果関係を遡る
python utils/trace_events.py causality <EventID>

# 週次サマリー
python utils/trace_events.py summary
```

**これだけで、開発の全体像が見えるようになります。**

---

作成: 2025-11-05  
更新: 2025-11-05

