# Phase 3 詳細設計書

**プロジェクト**: Resonant Engine v1.1  
**作成日**: 2025-11-06  
**対象期間**: 2025-11-05 〜 2025-11-06

---

## 📋 目次

1. [モジュール詳細仕様](#モジュール詳細仕様)
2. [API仕様](#api仕様)
3. [データ構造](#データ構造)
4. [処理フロー](#処理フロー)
5. [エラーハンドリング](#エラーハンドリング)
6. [使用例](#使用例)

---

## モジュール詳細仕様

### 1. `utils/resonant_digest.py`

#### クラス: `ResonantDigestGenerator`

##### コンストラクタ

```python
def __init__(self):
    """
    初期化
    
    Attributes:
        stream (ResonantEventStream): 統一イベントストリームのインスタンス
    """
```

##### メソッド一覧

###### `generate_digest(days: int = 7, output_format: str = "markdown") -> str`

**目的**: 直近N日間の開発文脈を生成

**パラメータ**:
- `days` (int): 分析対象の日数（デフォルト: 7日）
- `output_format` (str): 出力形式（"markdown" または "cursorrules"）

**戻り値**:
- `str`: 生成された開発文脈の文字列

**処理フロー**:
1. 指定日数前からのイベントを取得
2. イベントを種別ごとに分類（intent, action, result, observation）
3. ソース別に分類
4. 指定された形式でフォーマット
5. 文字列として返却

**出力形式**:

**markdown形式**:
```markdown
# Resonant Engine - 開発文脈ダイジェスト

**期間**: 直近7日間
**生成日時**: 2025-11-06 07:08:39

## 📊 サマリー
- **意図**: 3件
- **行動**: 14件
- **結果**: 15件
- **観測**: 5件

## 🎯 主要な開発意図
- **2025-11-05 15:55:17**: 統一イベントストリームのテスト
  - 文脈: 点を線に繋げる統合作業

...
```

**cursorrules形式**:
```markdown
# Resonant Engine - Recent Development Context

*Generated: 2025-11-06 07:01:56*
*Period: Last 7 days*

## Recent Development Intentions
- [2025-11-05 15:55:17] 統一イベントストリームのテスト
  Context: 点を線に繋げる統合作業

## Recent System Activities
- [2025-11-06 06:56:56] result from notion_sync: success
...
```

###### `save_to_cursorrules(days: int = 7, cursorrules_path: Optional[Path] = None)`

**目的**: 生成したダイジェストを.cursorrulesに追加

**パラメータ**:
- `days` (int): 分析対象の日数
- `cursorrules_path` (Optional[Path]): .cursorrulesファイルのパス（Noneの場合は自動検出）

**処理フロー**:
1. cursorrules形式のダイジェストを生成
2. 既存の.cursorrulesファイルを読み込む（存在する場合）
3. 既存のResonant Engineセクションを削除
4. 新しいダイジェストを追加
5. ファイルに書き込み

**エラーハンドリング**:
- ファイル読み込みエラー: 空の文字列として扱う
- ファイル書き込みエラー: 例外を発生

---

### 2. `utils/context_api.py`

#### クラス: `ResonantContextAPI`

##### コンストラクタ

```python
def __init__(self):
    """
    初期化
    
    Attributes:
        stream (ResonantEventStream): 統一イベントストリームのインスタンス
    """
```

##### メソッド一覧

###### `get_recent_changes(days: int = 7) -> Dict[str, Any]`

**目的**: 直近の変更と意図を返す

**パラメータ**:
- `days` (int): 分析対象の日数（デフォルト: 7日）

**戻り値**:
```python
{
    "period_days": 7,
    "generated_at": "2025-11-06T07:07:01",
    "intents": [
        {
            "timestamp": "2025-11-05T15:55:17",
            "intent": "統一イベントストリームのテスト",
            "context": "点を線に繋げる統合作業",
            "source": "user"
        },
        ...
    ],
    "actions": [
        {
            "timestamp": "2025-11-06T06:56:55",
            "action": "fetch_specs",
            "source": "notion_sync",
            "data": {...}
        },
        ...
    ],
    "summary": {
        "total_events": 37,
        "intents_count": 3,
        "actions_count": 14,
        "results_count": 15,
        "success_count": 9,
        "error_count": 6
    },
    "recent_errors": [
        {
            "timestamp": "2025-11-05T20:49:59",
            "error": "The property type in the database does not match...",
            "source": "notion_sync"
        },
        ...
    ]
}
```

**処理フロー**:
1. 指定日数前からのイベントを取得
2. イベントを種別ごとに分類
3. 意図を時系列で整理（最新10件）
4. アクションを時系列で整理（最新20件）
5. 結果を統計（成功/失敗数）
6. エラーを抽出（最新5件）
7. 辞書として返却

###### `get_spec_history(feature_name: str) -> Dict[str, Any]`

**目的**: 特定機能の仕様変更履歴を取得

**パラメータ**:
- `feature_name` (str): 機能名（検索キーワード）

**戻り値**:
```python
{
    "feature_name": "機能名",
    "generated_at": "2025-11-06T07:07:01",
    "events": [
        {
            "timestamp": "2025-11-05T20:51:19",
            "event_type": "observation",
            "spec_name": "機能名",
            "page_id": "2a25f766-...",
            "status": "未構築",
            "memo": ""
        },
        ...
    ],
    "total_events": 5
}
```

**処理フロー**:
1. Notion同期イベントから仕様書関連を検索
2. 機能名を含むイベントを抽出
3. 時系列でソート
4. 辞書として返却

###### `summarize_project_state() -> Dict[str, Any]`

**目的**: プロジェクトの現状をサマリー

**戻り値**:
```python
{
    "generated_at": "2025-11-06T07:07:01",
    "period_30d": {
        "total_events": 37,
        "by_source": {
            "notion_sync": 20,
            "observer_daemon": 5,
            "user": 3,
            ...
        },
        "by_event_type": {
            "action": 14,
            "result": 15,
            "intent": 3,
            ...
        },
        "error_rate": 40.0
    },
    "period_7d": {
        "total_events": 37,
        "by_source": {...},
        "by_event_type": {...},
        "error_rate": 40.0
    },
    "latest_intents": [
        {
            "timestamp": "2025-11-05T15:55:17",
            "intent": "統一イベントストリームのテスト",
            "source": "user"
        },
        ...
    ],
    "activity_trend": {
        "daily_avg_30d": 1.23,
        "daily_avg_7d": 5.29
    }
}
```

**処理フロー**:
1. 直近30日間と7日間のイベントを取得
2. ソース別に統計
3. イベント種別別に統計
4. エラー率を計算
5. 最新の意図を抽出（最新5件）
6. 日平均活動量を計算
7. 辞書として返却

###### `get_context_for_ai(days: int = 7) -> str`

**目的**: AIが理解しやすい形式で文脈を文字列として返す

**パラメータ**:
- `days` (int): 分析対象の日数（デフォルト: 7日）

**戻り値**:
- `str`: AI向けの文脈説明文字列

**出力例**:
```markdown
# Resonant Engine - Project Context (Last 7 days)

Generated: 2025-11-06 07:07:01

## Summary
- Total Events: 37
- Intents: 3
- Actions: 14
- Success Rate: 60.0%

## Recent Development Intentions
- [2025-11-05 15:55:17] 統一イベントストリームのテスト
  Context: 点を線に繋げる統合作業

## Recent Issues
- [2025-11-05 20:49:59] notion_sync: The property type in the database does not match...

## Activity Trend
- Daily Average (Last 7 days): 5.29 events/day
- Daily Average (Last 30 days): 1.23 events/day
```

---

### 3. `scripts/start_dev.sh`

#### 処理フロー

```bash
1. 引数チェック
   - 開発意図が指定されているか確認
   - コンテキスト（オプション）を取得

2. 開発意図を記録
   - python3 utils/record_intent.py "$INTENT" "$CONTEXT"
   - イベントストリームに記録

3. .cursorrulesを更新
   - python3 utils/resonant_digest.py --days 7 --update-cursorrules
   - 最新の開発文脈を注入

4. 完了メッセージを表示
```

#### 引数

- `$1`: 開発意図（必須）
- `$2`: コンテキスト（オプション）

#### 出力

- 開発意図の記録結果
- イベントID
- .cursorrules更新結果
- 次のステップの案内

---

### 4. `scripts/end_dev.sh`

#### 処理フロー

```bash
1. 引数チェック
   - 完了メッセージが指定されているか確認
   - ステータス（デフォルト: success）を取得

2. 開発結果を記録
   - Pythonスクリプトでイベントストリームに記録
   - event_type: "result"
   - source: "user"
   - data: {status, message, session_type: "development"}

3. 最近の開発活動を表示
   - python3 utils/context_api.py recent --format text

4. 完了メッセージを表示
```

#### 引数

- `$1`: 完了メッセージ（必須）
- `$2`: ステータス（オプション、デフォルト: "success"）

#### 出力

- 開発結果の記録結果
- イベントID
- 最近の開発活動サマリー
- 次のステップの案内

---

### 5. `utils/notion_sync_agent.py`

#### クラス: `NotionSyncAgent`

##### 主要メソッド

###### `get_specs_with_sync_trigger() -> List[Dict[str, Any]]`

**目的**: 同期トリガーが「Yes」の仕様書を取得

**戻り値**:
```python
[
    {
        "id": "2a25f766-048d-8049-a6a3-f4c1b1b1f3a6",
        "name": "動作確認",
        "public": False,
        "sync_trigger": True,
        "memo": "",
        "last_sync": None,
        "status": "",
        "url": "https://www.notion.so/..."
    },
    ...
]
```

**処理フロー**:
1. イベントストリームにactionイベントを記録
2. Notion APIでデータベースをクエリ
3. 「同期トリガー」がTrueの仕様書を抽出
4. 各仕様書をobservationイベントとして記録
5. 結果をresultイベントとして記録
6. リストとして返却

**エラーハンドリング**:
- APIエラー: resultイベントにエラー情報を記録
- データベースID未設定: 警告を表示し、空のリストを返却

###### `get_tasks_for_spec(spec_page_id: str) -> List[Dict[str, Any]]`

**目的**: 特定の仕様書に紐付くタスクを取得

**パラメータ**:
- `spec_page_id` (str): 仕様書ページのID

**戻り値**: タスクのリスト

###### `get_reviews_for_spec(spec_page_id: str) -> List[Dict[str, Any]]`

**目的**: 特定の仕様書に紐付くレビューを取得

**パラメータ**:
- `spec_page_id` (str): 仕様書ページのID

**戻り値**: レビューのリスト

###### `write_archive(phase: str, metrics: Dict[str, Any]) -> bool`

**目的**: Resonant Archiveにメトリクスを書き込み

**パラメータ**:
- `phase` (str): フェーズ名
- `metrics` (Dict[str, Any]): メトリクスデータ

**戻り値**: 成功したかどうか

---

## API仕様

### CLIコマンド

#### `resonant_digest.py`

```bash
python3 utils/resonant_digest.py [OPTIONS]

OPTIONS:
  --days DAYS              分析対象の日数（デフォルト: 7）
  --format FORMAT          出力形式（markdown/cursorrules、デフォルト: markdown）
  --output FILE            出力ファイルパス（指定しない場合は標準出力）
  --update-cursorrules     .cursorrulesファイルを更新
```

#### `context_api.py`

```bash
python3 utils/context_api.py COMMAND [OPTIONS]

COMMANDS:
  recent                   直近の変更を取得
  spec                     特定機能の仕様変更履歴を取得
  summary                  プロジェクト状態をサマリー
  ai                       AI向け文脈を生成

OPTIONS:
  --days DAYS              分析対象の日数（デフォルト: 7）
  --feature NAME           機能名（specコマンド用）
  --format FORMAT          出力形式（json/text、デフォルト: json）
```

#### `notion_sync_agent.py`

```bash
python3 utils/notion_sync_agent.py

# 同期トリガーが「Yes」の仕様書を検出して表示
```

#### `start_dev.sh`

```bash
./scripts/start_dev.sh "開発の意図" [コンテキスト]
```

#### `end_dev.sh`

```bash
./scripts/end_dev.sh "完了メッセージ" [ステータス]
```

---

## データ構造

### イベントストリームのデータ構造

```python
{
    "event_id": "EVT-20251106-070725-8ede82",
    "timestamp": "2025-11-06T07:07:25.123456",
    "event_type": "intent|action|result|observation|hypothesis",
    "source": "user|observer_daemon|notion_sync|github_webhook|backlog_sync",
    "data": {
        # イベント種別に応じたデータ
        # intent: {"intent": "...", "context": "..."}
        # action: {"action": "...", "target": "..."}
        # result: {"status": "success|error", "message": "...", ...}
        # observation: {"spec_name": "...", "page_id": "...", ...}
    },
    "parent_event_id": "EVT-20251106-070724-xxxxxx" | None,
    "related_hypothesis_id": "HYP-20251106-xxxxxx" | None,
    "tags": ["tag1", "tag2", ...]
}
```

### Notion仕様書データ構造

```python
{
    "id": "2a25f766-048d-8049-a6a3-f4c1b1b1f3a6",
    "name": "動作確認",
    "public": False,
    "sync_trigger": True,
    "memo": "",
    "last_sync": "2025-11-05" | None,
    "status": "未構築|構築中|実稼働",
    "url": "https://www.notion.so/..."
}
```

### Notionタスクデータ構造

```python
{
    "id": "xxxxx-xxxxx-xxxxx",
    "title": "タスク名",
    "target_page_id": "2a25f766-...",
    "assignee": "担当者名",
    "priority": "Low|Medium|High|Urgent",
    "status": "ToDo|Doing|Blocked|Done",
    "deadline": "2025-11-10" | None,
    "notes": "備考",
    "url": "https://www.notion.so/..."
}
```

---

## 処理フロー

### 開発セッション開始時のフロー

```
[ユーザー]
  ↓
  ./scripts/start_dev.sh "新機能の実装"
  ↓
[record_intent.py]
  ↓
  イベントストリームに記録
  event_type: "intent"
  source: "user"
  ↓
[resonant_digest.py]
  ↓
  直近7日間のイベントを分析
  ↓
  .cursorrulesファイルを更新
  ↓
[完了]
```

### 開発セッション終了時のフロー

```
[ユーザー]
  ↓
  ./scripts/end_dev.sh "実装完了" success
  ↓
[Pythonスクリプト]
  ↓
  イベントストリームに記録
  event_type: "result"
  source: "user"
  data: {status: "success", message: "実装完了", ...}
  ↓
[context_api.py]
  ↓
  最近の開発活動を取得
  ↓
  表示
  ↓
[完了]
```

### Notion同期のフロー

```
[Notion Sync Agent]
  ↓
  get_specs_with_sync_trigger()
  ↓
  [action] イベント記録
  ↓
  Notion API クエリ
  ↓
  「同期トリガー: Yes」の仕様書を検出
  ↓
  [observation] 各仕様書を記録
  ↓
  [result] 結果を記録
  ↓
  仕様書リストを返却
```

---

## エラーハンドリング

### 共通エラー処理

#### 環境変数未設定

```python
if not NOTION_TOKEN:
    raise ValueError("NOTION_TOKEN が設定されていません")
```

#### ファイル読み込みエラー

```python
try:
    with open(file_path, "r") as f:
        content = f.read()
except FileNotFoundError:
    content = ""  # デフォルト値
except Exception as e:
    print(f"⚠️ ファイル読み込みエラー: {e}")
    content = ""
```

#### APIエラー

```python
try:
    response = client.request(...)
except Exception as e:
    # イベントストリームにエラーを記録
    stream.emit(
        event_type="result",
        source="notion_sync",
        data={"status": "error", "error": str(e)},
        parent_event_id=action_id
    )
    return []
```

### エラーイベントの記録

すべてのエラーはイベントストリームに記録されます：

```python
{
    "event_type": "result",
    "source": "notion_sync",
    "data": {
        "status": "error",
        "error": "エラーメッセージ",
        "error_type": "APIResponseError"
    },
    "parent_event_id": "EVT-xxxxx-xxxxxx"
}
```

---

## 使用例

### 例1: 開発セッションの開始と終了

```bash
# 開発開始
./scripts/start_dev.sh "ユーザー認証機能の追加"

# 開発作業...

# 開発終了
./scripts/end_dev.sh "認証機能実装完了" success
```

### 例2: 開発文脈の確認

```bash
# マークダウン形式で確認
python3 utils/resonant_digest.py --days 7

# .cursorrulesを更新
python3 utils/resonant_digest.py --days 7 --update-cursorrules
```

### 例3: プロジェクト状態の確認

```bash
# サマリー表示
python3 utils/context_api.py summary --format text

# AI向け文脈を生成
python3 utils/context_api.py ai --days 7
```

### 例4: Notion同期の確認

```bash
# 同期トリガー検知テスト
python3 utils/notion_sync_agent.py
```

### 例5: Python APIとして使用

```python
from utils.context_api import ResonantContextAPI

api = ResonantContextAPI()

# 最近の変更を取得
recent = api.get_recent_changes(days=7)
print(f"最近のイベント数: {recent['summary']['total_events']}")

# プロジェクト状態をサマリー
state = api.summarize_project_state()
print(f"エラー率: {state['period_7d']['error_rate']}%")

# AI向け文脈を取得
context = api.get_context_for_ai(days=7)
print(context)
```

---

## テスト

### 動作確認済み項目

1. ✅ 環境変数の設定（5/5）
2. ✅ Notion統合の動作確認
3. ✅ Resonant Digest生成機能
4. ✅ Context API（4コマンドすべて）
5. ✅ 開発セッション管理ツール

詳細は `docs/phase3_completion_report.md` を参照。

---

**作成**: 2025-11-06  
**作成者**: Claude Sonnet 4.5  
**プロジェクト**: Resonant Engine v1.1

