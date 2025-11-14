# 📋 Resonant Engine 現状分析プロトコル

> **目的**: プロジェクトの現状を効率的に把握し、問題点を特定するための調査手順書  
> **作成日**: 2025-11-12  
> **対象**: Resonant Engine v1 (macOS環境)

## 🎯 調査の基本方針

### 制約事項
- ❌ `directory_tree`は容量オーバーで使用不可
- ⚠️ セッション上限に配慮（不要なファイル全文読み込みを避ける）
- ✅ 段階的に詳細度を上げる（全体 → 詳細）

### 優先順位
1. **動作状態の確認**（プロセス、最新ログ）
2. **パイプライン完全性**（Intent → Bridge → Kana）
3. **イベントストリーム活性度**（ログの鮮度）
4. **コンポーネント実装状況**（コードの存在と内容）

---

## 📊 調査フロー（6ステップ）

### Step 1: プロジェクト構造の把握

```bash
# ツール: list_directory
# 対象: /Users/zero/Projects/resonant-engine
```

**確認項目**:
- ディレクトリ構成（daemon, bridge, logs, dashboard,scripts,utils,docs等）
- 主要な設定ファイル（.env, requirements.txt等）
- ドキュメントファイルの存在

**判断基準**:
- ✅ 必須ディレクトリ: `daemon/`, `bridge/`, `logs/`, `dashboard/backend/`, `scripts/`, `utils/`, `docs/`
- ⚠️ 欠けていれば優先度P0で報告

---

### Step 2: ログディレクトリの確認

```bash
# ツール: list_directory
# 対象: /Users/zero/Projects/resonant-engine/logs
```

**確認項目**:
```
必須ログファイル:
├── intent_log.jsonl          # Intent記録
├── event_stream.jsonl        # イベントストリーム
├── intent_processor.log      # IntentProcessor動作ログ
├── kana_responses.log        # Claude API応答
├── daemon.log                # resonant_daemon動作ログ
├── trace_map.jsonl           # トレースマップ
└── webhook_log.jsonl         # Webhook記録
```

**次のアクション決定**:
- ファイル存在確認のみ（この段階では中身を読まない）
- 欠けているファイルがあればメモ

---

### Step 3: プロセス稼働状況の確認

```bash
# ツール: osascript (do shell script)
# コマンド: ps aux | grep -E '(observer_daemon|resonant_daemon)' | grep -v grep
```

**確認項目**:
- `resonant_daemon.py`のPID、起動時刻、CPU時間
- `observer_daemon.py`のPID、起動時刻、CPU時間

**判断基準**:
```
✅ 正常: 両方のプロセスが動作中
⚠️ 部分停止: どちらか一方のみ動作
❌ 停止: どちらも動作していない
```

**lockファイル確認**:
```bash
# プロセスが見つからない場合のみ確認
ls /Users/zero/Projects/resonant-engine/daemon/pids/
```
- lockファイル存在 + プロセス不在 = **stale lock**（手動削除が必要）

---

### Step 4: ログファイルの時系列確認

**優先順位順に確認**:

#### 4-1. event_stream.jsonl（最重要）
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/logs/event_stream.jsonl
```

**確認ポイント**:
- 最終更新日時（`tail -1`の`timestamp`フィールド）
- 直近のイベントタイプ（`event_type`, `source`）
- エラーイベントの有無（`tags`に`"error"`）

**判断基準**:
```
✅ 活発: 24時間以内の更新
⚠️ 停滞: 1週間以内だが更新少ない
❌ 停止: 1週間以上更新なし
```

#### 4-2. intent_log.jsonl
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/logs/intent_log.jsonl
```

**確認ポイント**:
- Intent記録の件数
- 最終記録日時
- Intentの内容（テストか実運用か）

#### 4-3. intent_processor.log
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/logs/intent_processor.log
```

**確認ポイント**:
- Claude API呼び出し成功ログ（`✅ Kana応答受信`）
- エラーログ（`❌`）
- 最終動作日時

#### 4-4. kana_responses.log
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/logs/kana_responses.log
```

**確認ポイント**:
- Claude APIからの応答内容
- JSON形式の妥当性
- 応答の質（`estimated_complexity`等）

#### 4-5. daemon.log（tail のみ）
```bash
# ツール: osascript
# コマンド: tail -50 /Users/zero/Projects/resonant-engine/logs/daemon.log
```

**理由**: ファイルが巨大な可能性があるため、最後の50行のみ確認

**確認ポイント**:
- `intent_protocol.json`の変更検知
- Intent処理の成否
- エラーメッセージ

---

### Step 5: 主要コンポーネントの確認

**優先順位順**:

#### 5-1. intent_protocol.json（現在のIntent）
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/bridge/intent_protocol.json
```

**確認ポイント**:
- 最後のIntent内容
- timestamp
- テスト用か実運用か

#### 5-2. intent_processor.py（Bridge層）
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/dashboard/backend/intent_processor.py
```

**確認ポイント**:
- Claude API統合コードの存在
- エラーハンドリング
- ログ出力機構

#### 5-3. resonant_daemon.py（Intent監視）
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/daemon/resonant_daemon.py
```

**確認ポイント**:
- IntentProcessor統合状況
- パス指定（旧パス参照していないか）
- 監視ループの実装

#### 5-4. observer_daemon.py（Git同期）
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/daemon/observer_daemon.py
```

**確認ポイント**:
- パス指定（旧パス参照していないか）
- イベントストリーム統合
- 重複検知ロジック

---

### Step 6: 設定ファイルの確認

#### 6-1. .env（APIキー等）
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/.env
```

**確認ポイント**:
- `ANTHROPIC_API_KEY`の存在
- `NOTION_API_KEY`の存在
- 各種DB_IDの設定

**注意**: APIキーが含まれるため、読み込んだ内容は要約のみ提示

#### 6-2. requirements.txt
```bash
# ツール: read_file
# 対象: /Users/zero/Projects/resonant-engine/requirements.txt
```

**確認ポイント**:
- `anthropic`パッケージ
- `python-dotenv`
- その他必須パッケージ

---

## 🔍 トラブルシューティング

### 問題1: directory_tree が容量オーバー

**対処法**:
```
❌ directory_tree /path/to/project
↓
✅ list_directory /path/to/project
✅ list_directory /path/to/project/subdir
```

段階的に詳細度を上げる。

---

### 問題2: ログファイルが巨大

**対処法**:
```bash
# read_file ではなく tail を使用
osascript: do shell script "tail -50 /path/to/logfile"
```

---

### 問題3: パスが古い（kiro-v3.1参照）

**確認箇所**:
- `resonant_daemon.py`の`ROOT`変数
- `observer_daemon.py`の`BASE_DIR`変数
- `intent_processor.py`の`ROOT`変数

**正しいパス**: `/Users/zero/Projects/resonant-engine`

---

## 📝 調査結果のテンプレート

```markdown
## ✅ 動作している機能
- [機能名]
  - 状態: ✅/⚠️/❌
  - 最終確認: [日時]
  - 証拠: [ログファイル名、行番号]

## ❌ 未実装・問題がある部分
- [機能名]
  - 問題: [説明]
  - 影響: [説明]
  - 優先度: P0/P1/P2

## 🎯 過去スレッドとの相違点
- [項目] 
  - 過去分析: [内容]
  - 実態: [内容]
  - 乖離理由: [説明]

## 📋 真の優先順位
### P0（緊急・最優先）
1. [タスク]
2. [タスク]

### P1（重要）
3. [タスク]
4. [タスク]
```

---

## 🚀 次のアクションテンプレート

```markdown
### 今すぐやるべきこと:
```bash
# 1. [説明]
cd /Users/zero/Projects/resonant-engine
[コマンド]

# 2. [説明]
[コマンド]
```

### 次に実装すべき機能（優先順）:
1. **[機能名]**（P0）
   - [説明]
   - [実装方針]

2. **[機能名]**（P1）
   - [説明]
   - [実装方針]
```

---

## 💡 調査時の注意点

### Do's ✅
- 段階的に詳細度を上げる（list → read）
- ログは最新部分のみ確認（tail）
- プロセス状態を最初に確認
- パス不整合を常にチェック

### Don'ts ❌
- いきなり`directory_tree`を使わない
- 巨大ファイルを`read_file`しない
- 全ログを一度に読み込まない
- APIキーを含むファイルをそのまま表示しない

---

## 📌 チェックリスト

調査完了時に確認：

- [ ] プロセス稼働状況を確認した
- [ ] 主要ログファイルの最終更新日を確認した
- [ ] パイプライン（Intent → Bridge → Kana）の状態を確認した
- [ ] 過去スレッドとの相違点を特定した
- [ ] 優先順位（P0/P1/P2）を決定した
- [ ] 次のアクションを具体的に提示した

---

## 🔄 調査の更新頻度

- **緊急時**: 即座
- **通常**: 週1回
- **定期メンテナンス**: 月1回

---

## 📚 関連ドキュメント

- **Resonant Engine総合ドキュメント**: `/docs/resonant_total_chronicle_v5_expanded.md`
- **Yunoドキュメント**: `/docs/yuno/`
- **Phase実装レポート**: `/docs/`

---

## 🔖 バージョン履歴

- **v1.0** (2025-11-12): 初版作成
  - 実際の調査プロセスから抽出
  - 6ステップの段階的調査フロー確立
  - トラブルシューティング追加

---

**次回更新**: 実際の運用を通じて改善点を反映

**メンテナンス担当**: Kana (Claude Sonnet 4.5)  
**承認**: 宏啓 (Hiroaki Kato)
