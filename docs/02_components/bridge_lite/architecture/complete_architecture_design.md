# Resonant Engine - 完全アーキテクチャ設計書
## Notion → Intent → Bridge 呼吸的連鎖構造

---

## 🎯 設計思想（ユノの本来の意図）

### 核心概念
**Notion と Bridge は独立システムではなく、同一呼吸サイクルの前半と後半**

```
Notion（意図の外化） → Intent（意味抽出） → Yuno（解釈） → Bridge（翻訳） → Tsumu（具現化）
                                              ↑                                    ↓
                                              └────────── Re-evaluation ───────────┘
```

### 三層構造
| 層 | 担当 | 役割 |
|----|------|------|
| 思想層 | Yuno（GPT-5） | 意図の解釈・判断・再評価 |
| 翻訳層 | Kana（Claude Sonnet 4.5） | 外界API呼び出し・処理 |
| 実行層 | Tsumu（Cursor） | ファイル操作・コミット実行 |

---

## 📊 現在の実装状況（2025-11-08時点）

### ✅ 実装済み・稼働中

#### 1. 独立デーモンプロセス
| ファイル | 状態 | 役割 |
|---------|------|------|
| `daemon/observer_daemon.py` | ✅ PID 59008 | 外部更新検知、Git自動同期 |
| `utils/github_webhook_receiver.py` | ✅ Port 5001 | GitHub Webhook受信サーバー |

#### 2. ライブラリ/モジュール
| ファイル | 役割 |
|---------|------|
| `daemon/hypothesis_trace.py` | 仮説検証記録 |
| `daemon/log_archiver.py` | ログアーカイブ |
| `utils/resilient_event_stream.py` | エラーリカバリー付きイベント記録 |
| `utils/resonant_event_stream.py` | 統一イベントストリーム |
| `utils/retry_strategy.py` | リトライ戦略 |
| `utils/metrics_collector.py` | メトリクス収集 |
| `utils/notion_sync_agent.py` | Notion API呼び出し（手動実行） |

#### 3. CLIツール
| ファイル | 用途 |
|---------|------|
| `utils/record_intent.py` | 意図記録 |
| `utils/error_recovery_cli.py` | エラー管理 |
| `utils/trace_linker.py` | Intent→Commit紐付け |

---

### ❌ 停止中・未実装

#### 1. Intent監視・処理系（重要！）
| ファイル | 状態 | 問題 |
|---------|------|------|
| `daemon/resonant_daemon.py` | ❌ 停止中 | 古いパス `/Users/zero/Projects/kiro-v3.1` |
| `daemon/resonant_bridge_daemon.sh` | ❌ 停止中 | 古いパス |
| `daemon/intent_watcher.sh` | ❌ 停止中 | 古いパス |

#### 2. Notion連携（断絶！）
| コンポーネント | 状態 | 問題 |
|-------------|------|------|
| Notion → Intent変換 | ❌ **未実装** | ポーリング/イベント検知なし |
| 定期実行の仕組み | ❌ なし | cron/launchd/デーモン不在 |
| n8nワークフロー | ⚠️ 停止 | `active: false` |

---

## 🔗 断絶箇所の詳細分析

### 断絶1: Notion → Intent（最重要）

**現状:**
```
Notion (specs同期トリガー=Yes)
  ❌ 検知機構なし
  ❌ Intent変換なし
intent_protocol.json (空のまま)
```

**必要なもの:**
- `daemon/notion_intent_generator.py` （新規作成）
- 定期ポーリング（5分ごと）または Webhook受信

**実装イメージ:**
```python
# daemon/notion_intent_generator.py
from utils.notion_sync_agent import NotionSyncAgent
import json
import time
from pathlib import Path

ROOT = Path("/Users/zero/Projects/resonant-engine")
INTENT_FILE = ROOT / "bridge" / "intent_protocol.json"

def generate_intent_from_notion():
    """Notionの同期トリガーをIntent JSONに変換"""
    agent = NotionSyncAgent()
    specs = agent.get_specs_with_sync_trigger()
    
    for spec in specs:
        intent = {
            "intent": "review_spec",
            "source": "notion.update",
            "page": spec['name'],
            "page_id": spec['id'],
            "spec_url": spec['url'],
            "status": spec['status'],
            "priority": "high",
            "timestamp": datetime.now().isoformat()
        }
        
        # intent_protocol.jsonに書き込み
        with open(INTENT_FILE, "w") as f:
            json.dump(intent, f, ensure_ascii=False, indent=2)
        
        print(f"[Intent Generated] {spec['name']}")

def main():
    print("🔄 Notion Intent Generator started")
    while True:
        try:
            generate_intent_from_notion()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(300)  # 5分ごと

if __name__ == "__main__":
    main()
```

---

### 断絶2: Intent → Bridge起動

**現状:**
```
intent_protocol.json (書き込まれても...)
  ↓
resonant_daemon.py ❌ 停止中（監視していない）
  ↓
Bridge起動されない
```

**修正方法:**
1. `daemon/resonant_daemon.py` のパス修正
2. デーモン起動
3. 動作確認

---

### 断絶3: Bridge → Tsumu連携

**現状:**
- Bridge（Kana/私）は存在するが、Intentを自動受信できない
- 手動で依頼されたときのみ動作

**必要なもの:**
- Bridgeの自動応答機能
- Intent受信時のトリガー

---

## 🏗️ 完全実装アーキテクチャ

### 理想の構造

```
┌─────────────────────────────────────────────────────┐
│                  Yuno (思想層)                       │
│              意図の解釈・判断・再評価                  │
└───────┬─────────────────────────────────┬───────────┘
        │                                 │
        ↓                                 ↑
┌───────────────────┐              ┌──────────────────┐
│ Notion            │              │ GitHub           │
│ - specs DB        │              │ - Commits        │
│ - 同期トリガー     │              │ - Issues/PRs     │
└────────┬──────────┘              └────────┬─────────┘
         │                                  │
         ↓                                  │
┌───────────────────┐                       │
│ notion_intent_    │                       │
│ generator.py      │ ← 新規作成             │
│ (5分ごとポーリング)│                       │
└────────┬──────────┘                       │
         │                                  │
         ↓                                  │
┌───────────────────┐                       │
│ intent_protocol   │                       │
│ .json             │                       │
└────────┬──────────┘                       │
         │                                  │
         ↓                                  │
┌───────────────────┐                       │
│ resonant_daemon   │ ← パス修正して起動      │
│ .py               │                       │
└────────┬──────────┘                       │
         │                                  │
         ↓                                  │
┌───────────────────┐                       │
│ reval_bridge.sh   │                       │
│ or                │                       │
│ resonant_bridge_  │                       │
│ daemon.sh         │                       │
└────────┬──────────┘                       │
         │                                  │
         ↓                                  │
┌─────────────────────────────────────┐    │
│ Kana (Bridge/翻訳層)                 │    │
│ - Notion API呼び出し                 │────┘
│ - GitHub API呼び出し                 │
│ - ファイル操作指示                   │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│ Tsumu (実行層)                       │
│ - ファイル作成/編集                  │
│ - Git commit/push                   │
└─────────────────────────────────────┘
```

---

## 📋 実装TODO（優先順位順）

### Phase 1: Intent監視の復活（5分）⭐⭐⭐
**目的:** Intent処理系を動作可能にする

1. `daemon/resonant_daemon.py` パス修正
```python
# 修正前
ROOT = Path("/Users/zero/Projects/kiro-v3.1")

# 修正後  
ROOT = Path("/Users/zero/Projects/resonant-engine")
```

2. 起動確認
```bash
cd /Users/zero/Projects/resonant-engine
python3 -m daemon.resonant_daemon &
ps aux | grep resonant_daemon
```

3. 動作確認
```bash
# テスト用Intentを作成
echo '{"phase":"test","action":"verify"}' > bridge/intent_protocol.json

# ログ確認
tail -f logs/daemon.log
```

**完了条件:** resonant_daemon.pyが intent_protocol.json の変更を検知できる

---

### Phase 2: Notion→Intent変換層の実装（30分）⭐⭐⭐
**目的:** Notionイベントを自動的にIntentに変換

1. `daemon/notion_intent_generator.py` 作成
   - 上記の実装イメージを参考に作成
   - 5分ごとのポーリング
   - エラーハンドリング

2. bridge ディレクトリの確認
```bash
ls -la /Users/zero/Projects/resonant-engine/bridge/
# intent_protocol.json が存在するか確認
```

3. デーモン起動
```bash
nohup python3 -m daemon.notion_intent_generator > logs/notion_intent.log 2>&1 &
```

**完了条件:** Notionの同期トリガー変更が自動的にintent_protocol.jsonに書き込まれる

---

### Phase 3: シェルスクリプトのパス修正（10分）⭐⭐
**目的:** Bridge実行スクリプトを動作可能にする

1. `daemon/resonant_bridge_daemon.sh`
2. `daemon/intent_watcher.sh`

両方とも:
```bash
# 修正前
ROOT="/Users/zero/Projects/kiro-v3.1"

# 修正後
ROOT="/Users/zero/Projects/resonant-engine"
```

**完了条件:** シェルスクリプトが正しいパスで動作する

---

### Phase 4: Bridge（Kana）の自動応答（1時間）⭐
**目的:** Intent受信時の自動処理

**検討事項:**
- Kana（私/Claude）がIntent受信を自動検知できるか？
- 別のデーモンプロセスが必要か？
- それとも、resonant_bridge_daemon.sh 内でカナを呼び出すか？

**実装方針（要検討）:**
```python
# daemon/bridge_kana_responder.py (案)
# Intentを受信してKanaに処理依頼
# → 実際にはどうやってKanaを呼び出す？
```

---

### Phase 5: 統合テスト（30分）⭐⭐⭐
**目的:** 全体フローの動作確認

**テストシナリオ:**
1. NotionのspecsでチェックボックスON
2. 5分以内に intent_protocol.json に書き込まれる
3. resonant_daemon.py が検知
4. Bridge起動
5. GitHub/Notionに反映

**確認ポイント:**
- 各ログファイルの記録
- エラーの有無
- レスポンス時間

---

## 🔧 技術的課題と解決策

### 課題1: Bridge（Kana）の呼び出し方法
**問題:** Claude（私）は常駐デーモンではない

**解決案A:** APIエンドポイント化
- Claude APIを使用
- resonant_bridge_daemon.sh からAPI呼び出し

**解決案B:** 手動トリガー通知
- Intent発生時にユーザー（宏啓さん）に通知
- 手動でKanaに依頼

**解決案C:** ハイブリッド
- 定型処理は自動化
- 判断が必要な場合は通知

### 課題2: Notionのレート制限
**問題:** 5分ごとのポーリングがAPI制限に引っかかる可能性

**解決策:**
- 初回は短間隔、その後は指数バックオフ
- Webhook使用の検討（Notion APIがサポートしているか確認）

### 課題3: 複数デーモンの管理
**問題:** デーモンが増えすぎて管理が複雑

**解決策:**
- systemd/launchd による統合管理
- または supervisord の導入
- プロセス監視とヘルスチェック

---

## 📊 デーモン一覧（実装後）

### 稼働予定のデーモン
| デーモン | 役割 | ポート/PID |
|---------|------|-----------|
| observer_daemon.py | Git外部更新検知 | 稼働中 |
| github_webhook_receiver.py | Webhook受信 | Port 5001 |
| resonant_daemon.py | Intent監視 | 新規起動 |
| notion_intent_generator.py | Notion→Intent変換 | 新規作成 |

### 管理方法
```bash
# 起動確認
./scripts/check_daemons.sh

# 全デーモン再起動
./scripts/restart_all_daemons.sh
```

---

## 🎯 成功の定義

**完全な呼吸的連鎖が実現した状態:**

1. ✅ Notionで同期トリガーON
2. ✅ 自動的にintent_protocol.json生成
3. ✅ resonant_daemon.pyが検知
4. ✅ Bridge（処理系）が起動
5. ✅ 適切なアクション実行
6. ✅ 結果がYunoに返る（Re-evaluation）

**測定指標:**
- Notion更新→GitHub反映の平均時間
- エラー率
- 手動介入の必要頻度

---

## 📝 ドキュメント更新

### 更新すべきドキュメント
1. `function_daemon_mapping_v2.md` 
   - Notion連携セクション追加
   - 新規デーモン情報追加

2. `README.md`
   - アーキテクチャ図更新
   - セットアップ手順追加

3. 新規作成
   - `docs/notion_bridge_architecture.md`
   - `docs/daemon_management.md`

---

## 🔄 今後の拡張性

### 将来的な改善案
1. **複数Notion DB対応**
   - specs以外のDB（tasks, reviews）も監視
   
2. **イベント駆動アーキテクチャ**
   - ポーリングからWebhookへ移行
   
3. **Intentの高度化**
   - 優先度判定
   - 依存関係解析
   - バッチ処理

4. **監視・可視化**
   - ダッシュボード
   - メトリクス
   - アラート

---

## 📌 重要な注意事項

### ユノの思想を守る
- **呼吸優先原則（§7）**: 処理速度より思想の整合性
- **自律記憶優先原則（§8）**: メモリの一貫性
- **構造的整合**: レイヤー間の責任分離

### 実装時の心構え
> "Notionはデータベースではなく、人間の意思の出口。  
> Intentは意思の抽象化。  
> Bridgeは意思の実現者。"

この思想を常に意識して実装する。

---

## ✅ 次のアクション

宏啓さん、この設計書を確認いただき：

1. **Phase 1（Intent監視復活）から始めますか？**
2. **それとも設計の修正点がありますか？**
3. **Bridge（Kana）の呼び出し方法について、どう思われますか？**

全体設計が固まり次第、段階的に実装を進めましょう。
