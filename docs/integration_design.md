# Resonant Engine 統合設計書
## 「点」を「線」に繋ぐアーキテクチャ

作成日: 2025-11-05
目的: 分散した記録システムを統一イベントストリームで統合

---

## 🎯 現状の問題

### 点として存在する記録システム

```
observer_daemon.py
├─ logs/observer_daemon.log (独自フォーマット)
└─ logs/hypothesis_trace_log.json (JSON配列)

github_webhook_receiver.py
└─ logs/webhook_log.jsonl (JSONL)

intent_logger.py
└─ logs/intent_log.jsonl (JSONL、未使用)

backlog_sync_agent.py
└─ (記録なし、読むだけ)

log_archiver.py
└─ logs/archive/ (アーカイブのみ)
```

**問題点**:
- ❌ 5つの異なるログ形式
- ❌ 相互参照不可
- ❌ 因果関係が追えない
- ❌ タイムラインが再構成できない

---

## 🎯 統合後の設計

### 統一イベントストリーム

```
event_stream.jsonl (全イベントを1つの時系列に記録)
├─ intent イベント（意図）
├─ action イベント（行動）
├─ result イベント（結果）
├─ observation イベント（観測）
└─ hypothesis イベント（仮説）

各イベントは parent_event_id で因果関係を保持
```

### イベントフロー例

```
[ユーザー] Backlogで仕様を更新
    ↓
EVT-001 (intent, source=user)
    ↓
[Backlog Webhook] Resonant Engineに通知
    ↓
EVT-002 (action, source=backlog_sync, parent=EVT-001)
    ↓
[observer_daemon] GitHub変更を検知
    ↓
EVT-003 (observation, source=observer_daemon, parent=EVT-002)
    ↓
[observer_daemon] Git pull実行
    ↓
EVT-004 (action, source=observer_daemon, parent=EVT-003)
    ↓
[HypothesisTrace] 仮説を記録
    ↓
EVT-005 (hypothesis, source=hypothesis_trace, parent=EVT-004, hypothesis_id=HYP-xxx)
    ↓
[observer_daemon] 仮説を検証
    ↓
EVT-006 (result, source=observer_daemon, parent=EVT-005, hypothesis_id=HYP-xxx)
```

この流れで、**「なぜこのコミットが発生したか」が遡れる**

---

## 📝 統合実装計画

### Phase 1: 基盤構築 ✅

- [x] `utils/resonant_event_stream.py` の実装
  - イベント記録 (emit)
  - イベント検索 (query)
  - 因果関係追跡 (trace_causality)
  - タイムライン取得 (get_timeline)

### Phase 2: 既存システムの統合

#### 2.1 observer_daemon.py の統合

**変更点**:
```python
from utils.resonant_event_stream import get_stream

stream = get_stream()

# Git更新検知時
observation_id = stream.emit(
    event_type="observation",
    source="observer_daemon",
    data={"commit": last_commit_msg, "branch": "origin/main"}
)

# Pull実行時
action_id = stream.emit(
    event_type="action",
    source="observer_daemon",
    data={"action": "git_pull"},
    parent_event_id=observation_id
)

# 仮説記録時
hyp_id = tracer.record(...)
hypothesis_id = stream.emit(
    event_type="hypothesis",
    source="hypothesis_trace",
    data={"hypothesis_id": hyp_id, "intent": "..."},
    parent_event_id=action_id,
    related_hypothesis_id=hyp_id
)

# 仮説検証時
stream.emit(
    event_type="result",
    source="observer_daemon",
    data={"status": "validated", "diff": "..."},
    parent_event_id=hypothesis_id,
    related_hypothesis_id=hyp_id
)
```

#### 2.2 github_webhook_receiver.py の統合

**変更点**:
```python
from utils.resonant_event_stream import get_stream

@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    stream = get_stream()
    
    # Webhook受信イベント
    webhook_id = stream.emit(
        event_type="action",
        source="github_webhook",
        data={
            "event": event_type,
            "delivery_id": delivery_id,
            "commits": payload.get("commits", [])
        },
        tags=["github", "webhook"]
    )
    
    # trace_linker実行
    stream.emit(
        event_type="action",
        source="trace_linker",
        data={"trigger": "github_push"},
        parent_event_id=webhook_id
    )
```

#### 2.3 backlog_sync_agent.py の統合

**変更点**:
```python
from utils.resonant_event_stream import get_stream

def sync_backlog_specs():
    """Backlogから仕様を取得し、イベントストリームに記録"""
    stream = get_stream()
    
    issues = get_issues()
    
    sync_id = stream.emit(
        event_type="action",
        source="backlog_sync",
        data={"action": "fetch_specs", "count": len(issues)},
        tags=["backlog", "specs"]
    )
    
    for issue in issues:
        stream.emit(
            event_type="observation",
            source="backlog_sync",
            data={
                "issue_key": issue["issueKey"],
                "summary": issue["summary"],
                "updated_at": issue.get("updated")
            },
            parent_event_id=sync_id,
            tags=["backlog", "issue"]
        )
```

#### 2.4 intent_logger.py の廃止

**変更**:
- `intent_logger.py` を削除
- 代わりに `resonant_event_stream.py` の `emit(event_type="intent")` を使う

---

## 🔍 統合後の使い方

### 1. 特定の仮説に関連する全イベントを取得

```python
from utils.resonant_event_stream import get_stream

stream = get_stream()
timeline = stream.get_timeline("HYP-20251105-143000-abc123")

for event in timeline:
    print(f"{event['timestamp']}: {event['event_type']} from {event['source']}")
```

### 2. 因果関係を遡る

```python
# 最新の結果イベントを取得
results = stream.query(event_type="result", limit=1)
latest_result = results[0]

# 「なぜこの結果になったか」を遡る
chain = stream.trace_causality(latest_result["event_id"])

print("因果関係チェーン:")
for event in chain:
    print(f"→ {event['event_type']}: {event['data']}")
```

### 3. 最近の開発活動を要約

```python
from datetime import datetime, timedelta

since = datetime.now() - timedelta(days=7)
recent_events = stream.query(since=since, limit=100)

intents = [e for e in recent_events if e["event_type"] == "intent"]
actions = [e for e in recent_events if e["event_type"] == "action"]
hypotheses = [e for e in recent_events if e["event_type"] == "hypothesis"]

print(f"過去7日間:")
print(f"- 意図: {len(intents)}件")
print(f"- 行動: {len(actions)}件")
print(f"- 仮説: {len(hypotheses)}件")
```

---

## 📊 期待される効果

### Before（点）
- 「このコミットは何のため？」→ ログを手動で探す
- 「仕様変更がどう反映された？」→ 追跡不可
- 「AIに文脈を伝える」→ 手動でコピペ

### After（線）
- 「このコミットは何のため？」→ `trace_causality()`で因果関係を自動表示
- 「仕様変更がどう反映された？」→ Backlog更新イベント→Git変更イベントが繋がる
- 「AIに文脈を伝える」→ 直近のイベントストリームから自動生成

---

## 🚀 実装順序

1. ✅ **基盤実装** (完了)
   - `resonant_event_stream.py`

2. 🔨 **統合実装** (次のステップ)
   - observer_daemon.py の改修
   - github_webhook_receiver.py の改修
   - backlog_sync_agent.py の改修

3. 🧪 **動作確認**
   - 手動でGit push → イベントストリーム確認
   - Webhook送信 → イベントチェーン確認

4. 🎯 **AI統合** (Phase 3)
   - イベントストリームから開発文脈を自動生成
   - `.cursorrules`に注入

---

## 📝 互換性維持

既存のログファイルは**そのまま残す**:
- `observer_daemon.log`: デバッグ用に継続記録
- `hypothesis_trace_log.json`: HypothesisTraceクラスの内部実装として維持
- `webhook_log.jsonl`: Webhook生ログとして保持

**新規追加**:
- `event_stream.jsonl`: 統合タイムライン（これが主軸）

---

## 🎯 成功指標

- [ ] 任意のイベントから因果関係を遡れる
- [ ] 仮説IDで関連イベントを全取得できる
- [ ] 直近7日の開発活動サマリーを自動生成できる
- [ ] AIが「なぜこの変更が起きたか」を説明できる

---

作成: 2025-11-05
更新: 2025-11-05

