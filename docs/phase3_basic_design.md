# Phase 3 基本設計書

**プロジェクト**: Resonant Engine v1.1  
**作成日**: 2025-11-06  
**対象期間**: 2025-11-05 〜 2025-11-06  
**目的**: Phase 3（AI統合層）の実装完了報告

---

## 📋 目次

1. [概要](#概要)
2. [新規作成モジュール](#新規作成モジュール)
3. [更新モジュール](#更新モジュール)
4. [ディレクトリ構造](#ディレクトリ構造)
5. [動作する機能](#動作する機能)
6. [アーキテクチャ概要](#アーキテクチャ概要)

---

## 概要

Phase 3では、統一イベントストリームを基盤として、AIがプロジェクトの開発文脈を理解できるようにする統合層を実装しました。

### 実装目標

1. **開発文脈の自動生成**: イベントストリームから開発活動を分析し、AIが理解できる形式で出力
2. **文脈提供API**: プロジェクトの状態をプログラムから取得可能にするAPI
3. **開発セッション管理**: 開発開始・終了時に自動的に文脈を更新する仕組み

### 設計思想

- **統一イベントストリーム**: すべての開発活動を1つのタイムラインに記録
- **因果関係の追跡**: `parent_event_id`により、イベント間の関係を明示
- **AI統合**: CursorなどAI支援ツールが自動的に開発文脈を理解できるようにする

---

## 新規作成モジュール

### 1. `utils/resonant_digest.py` (318行)

**目的**: イベントストリームから開発文脈を自動生成

**主要機能**:
- 直近N日間のイベントを分析
- マークダウン形式とcursorrules形式の両方で出力
- `.cursorrules`ファイルへの自動注入

**クラス**:
- `ResonantDigestGenerator`: ダイジェスト生成のメインクラス

**主要メソッド**:
- `generate_digest(days, output_format)`: ダイジェスト生成
- `save_to_cursorrules(days, cursorrules_path)`: .cursorrules更新

### 2. `utils/context_api.py` (346行)

**目的**: 開発文脈をプログラムから取得するAPI

**主要機能**:
- 直近の変更と意図を取得
- 特定機能の仕様変更履歴を取得
- プロジェクトの現状をサマリー
- AI向けの文脈文字列を生成

**クラス**:
- `ResonantContextAPI`: 文脈提供のメインクラス

**主要メソッド**:
- `get_recent_changes(days)`: 直近の変更を取得
- `get_spec_history(feature_name)`: 仕様変更履歴を取得
- `summarize_project_state()`: プロジェクト状態をサマリー
- `get_context_for_ai(days)`: AI向け文脈文字列を生成

### 3. `scripts/start_dev.sh` (55行)

**目的**: 開発セッション開始時の処理

**処理内容**:
1. 開発意図をイベントストリームに記録
2. `.cursorrules`に最新の開発文脈を注入

**使用方法**:
```bash
./scripts/start_dev.sh "開発の意図"
```

### 4. `scripts/end_dev.sh` (83行)

**目的**: 開発セッション終了時の処理

**処理内容**:
1. 開発結果をイベントストリームに記録
2. 最近の開発活動を表示

**使用方法**:
```bash
./scripts/end_dev.sh "完了メッセージ" [status]
```

### 5. `utils/notion_sync_agent.py` (471行)

**目的**: Notion統合エージェント（Phase 2で実装、今回動作確認）

**主要機能**:
- Notionの4つのデータベース（specs, tasks, reviews, archive）へのアクセス
- 統一イベントストリームへの統合
- 同期トリガー検知

### 6. `utils/create_notion_databases.py` (393行)

**目的**: Notionデータベースの自動作成ツール

**主要機能**:
- 4つのデータベース（specs, tasks, reviews, archive）を一括作成
- データベースIDを環境変数形式で出力

---

## 更新モジュール

### 1. `README.md`

**更新内容**:
- Notion統合のドキュメントリンクを追加
- Phase 3の機能説明を追加

### 2. `daemon/observer_daemon.py`

**更新内容**:
- 統一イベントストリームへの統合（Phase 2で実装済み）

### 3. `utils/github_webhook_receiver.py`

**更新内容**:
- 統一イベントストリームへの統合（Phase 2で実装済み）

---

## ディレクトリ構造

```
resonant-engine/
├── .cursorrules                    # [新規] AI向け開発文脈（自動生成）
├── .env                            # [既存] 環境変数（Notion APIトークン等）
│
├── docs/
│   ├── phase3_basic_design.md      # [新規] 本ドキュメント
│   ├── phase3_detailed_design.md   # [新規] 詳細設計書
│   ├── phase3_completion_report.md # [新規] 完了報告書
│   ├── notion_integration_summary.md # [新規] Notion統合サマリー
│   ├── notion_setup_guide.md       # [新規] Notionセットアップガイド
│   ├── env_template.txt            # [新規] 環境変数テンプレート
│   └── integration_complete.md     # [既存] Phase 2完了報告
│
├── utils/
│   ├── resonant_digest.py          # [新規] 開発文脈自動生成
│   ├── context_api.py              # [新規] 文脈提供API
│   ├── notion_sync_agent.py        # [新規] Notion統合エージェント
│   ├── create_notion_databases.py  # [新規] Notion DB作成ツール
│   ├── record_intent.py            # [既存] 意図記録ツール
│   ├── resonant_event_stream.py    # [既存] 統一イベントストリーム
│   └── trace_events.py             # [既存] イベントトレースツール
│
├── scripts/
│   ├── start_dev.sh                # [新規] 開発セッション開始
│   ├── end_dev.sh                  # [新規] 開発セッション終了
│   └── ...                         # [既存] その他のスクリプト
│
└── logs/
    └── event_stream.jsonl          # [既存] 統一イベントストリームデータ
```

---

## 動作する機能

### 1. 開発文脈の自動生成

**コマンド**:
```bash
# マークダウン形式で出力
python3 utils/resonant_digest.py --days 7

# cursorrules形式で出力
python3 utils/resonant_digest.py --days 7 --format cursorrules

# .cursorrulesファイルを更新
python3 utils/resonant_digest.py --days 7 --update-cursorrules
```

**出力内容**:
- サマリー（意図、行動、結果の件数）
- 主要な開発意図
- 最近の活動（ソース別）
- 重要な結果（成功/失敗）

### 2. 文脈提供API

**コマンド**:
```bash
# 直近の変更を取得
python3 utils/context_api.py recent --format text

# プロジェクト状態をサマリー
python3 utils/context_api.py summary --format text

# AI向け文脈を生成
python3 utils/context_api.py ai --days 7

# 特定機能の仕様変更履歴
python3 utils/context_api.py spec --feature "機能名"
```

**出力形式**:
- JSON形式（プログラムから利用）
- テキスト形式（人間が読む）

### 3. 開発セッション管理

**開発開始時**:
```bash
./scripts/start_dev.sh "新機能の実装"
```

**実行内容**:
1. 開発意図をイベントストリームに記録
2. `.cursorrules`に最新の開発文脈を注入

**開発終了時**:
```bash
./scripts/end_dev.sh "実装完了" success
```

**実行内容**:
1. 開発結果をイベントストリームに記録
2. 最近の開発活動を表示

### 4. Notion統合

**コマンド**:
```bash
# 同期トリガー検知テスト
python3 utils/notion_sync_agent.py

# データベース作成（初回のみ）
python3 utils/create_notion_databases.py
```

**機能**:
- specs DBの監視（同期トリガー検知）
- tasks DBからのタスク取得
- reviews DBからのレビュー取得
- archive DBへのメトリクス書き込み
- すべての操作をイベントストリームに記録

---

## アーキテクチャ概要

### データフロー

```
[開発活動]
    ↓
[統一イベントストリーム] ← event_stream.jsonl
    ↓
[Resonant Digest Generator]
    ├─→ マークダウン形式のダイジェスト
    └─→ .cursorrules形式（AI向け）
    ↓
[Context API]
    ├─→ get_recent_changes()
    ├─→ get_spec_history()
    ├─→ summarize_project_state()
    └─→ get_context_for_ai()
    ↓
[AI支援ツール（Cursor等）]
    └─→ 開発文脈を自動理解
```

### イベントストリームの構造

```json
{
  "event_id": "EVT-20251106-070725-8ede82",
  "timestamp": "2025-11-06T07:07:25.123456",
  "event_type": "intent",
  "source": "user",
  "data": {
    "intent": "Phase 3実装完了のテスト"
  },
  "parent_event_id": null,
  "related_hypothesis_id": null,
  "tags": ["intent", "user_action"]
}
```

### イベント種別

| 種別 | 説明 | 例 |
|------|------|-----|
| `intent` | 意図表明 | ユーザーが「○○を実装する」と宣言 |
| `action` | 行動 | Git pull、Webhook受信、Notion同期 |
| `result` | 結果 | 成功・失敗の記録 |
| `observation` | 観測 | 外部更新の検知、課題の取得 |
| `hypothesis` | 仮説 | HypothesisTraceによる仮説記録 |

---

## 依存関係

### Pythonパッケージ

- `notion-client`: Notion API連携
- `python-dotenv`: 環境変数管理

### 既存モジュール

- `utils/resonant_event_stream.py`: 統一イベントストリーム
- `utils/record_intent.py`: 意図記録ツール

---

## 環境変数

### 必要な環境変数

```bash
# Notion Integration
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_SPECS_DB_ID=2965f766048d80f08fbac1fb8e0c2772
NOTION_TASKS_DB_ID=2955f766048d8030a03bcc65f877304f
NOTION_REVIEWS_DB_ID=2955f766048d80b88a6eee645ff068ba
NOTION_ARCHIVE_DB_ID=29b5f766048d80b4b09ee44ecf3322bf
```

---

## 完了判定

すべての機能が正常に動作することを確認済み：

- ✅ 環境変数の設定（5/5）
- ✅ Notion統合の動作確認
- ✅ Resonant Digest生成機能
- ✅ Context API
- ✅ 開発セッション管理ツール

詳細は `docs/phase3_completion_report.md` を参照。

---

**作成**: 2025-11-06  
**作成者**: Claude Sonnet 4.5  
**プロジェクト**: Resonant Engine v1.1

