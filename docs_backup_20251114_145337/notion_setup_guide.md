# Notion統合セットアップガイド

Resonant EngineとNotionを統合するためのステップバイステップガイド

---

## 📋 前提条件

- Notionワークスペースへのアクセス
- Notion Integration（API Token）の作成権限
- 以下の4つのデータベースが存在すること：
  - specs（仕様書）
  - tasks（タスク）
  - reviews（レビュー）
  - resonant_archive（アーカイブ）

---

## 🔧 Step 1: Notion Integrationの作成

### 1.1 Notion Integrationを作成

1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. 「+ New integration」をクリック
3. 以下を設定：
   - **Name**: Resonant Engine
   - **Associated workspace**: あなたのワークスペース
   - **Type**: Internal Integration
4. 「Submit」をクリック
5. **Integration Token（シークレット）**をコピー
   - 形式: `secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - ⚠️ このトークンは外部に漏らさないこと

### 1.2 データベースにIntegrationを招待

各データベースページで：
1. 右上の「⋯」メニューをクリック
2. 「Add connections」を選択
3. 「Resonant Engine」を選択

**対象データベース**:
- specs
- tasks
- reviews
- resonant_archive

---

## 🔧 Step 2: データベースIDの取得

### 2.1 データベースIDの確認方法

Notionでデータベースページを開き、URLを確認：

```
https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=yyyyyyyyy
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      これがデータベースID（32文字）
```

**例**:
```
https://www.notion.so/2955f766048d8030a03bcc65f877304f?v=123456
→ データベースID: 2955f766048d8030a03bcc65f877304f
```

### 2.2 4つのデータベースIDを取得

エクスポートしたCSVファイル名から推測：

1. **specs DB**:
   - ファイル: `specs 2965f766048d80f08fbac1fb8e0c2772_all.csv`
   - ID: `2965f766048d80f08fbac1fb8e0c2772`

2. **tasks DB**:
   - ファイル: `tasks 2955f766048d8030a03bcc65f877304f_all.csv`
   - ID: `2955f766048d8030a03bcc65f877304f`

3. **reviews DB**:
   - ファイル: `reviews 2955f766048d80b88a6eee645ff068ba_all.csv`
   - ID: `2955f766048d80b88a6eee645ff068ba`

4. **resonant_archive DB**:
   - ファイル: `resonant_archive 29b5f766048d80b4b09ee44ecf3322bf_all.csv`
   - ID: `29b5f766048d80b4b09ee44ecf3322bf`

---

## 🔧 Step 3: 環境変数の設定

### 3.1 .envファイルに追加

プロジェクトルートの`.env`ファイルに以下を追加：

```bash
# Notion Integration
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Notion Database IDs
NOTION_SPECS_DB_ID=2965f766048d80f08fbac1fb8e0c2772
NOTION_TASKS_DB_ID=2955f766048d8030a03bcc65f877304f
NOTION_REVIEWS_DB_ID=2955f766048d80b88a6eee645ff068ba
NOTION_ARCHIVE_DB_ID=29b5f766048d80b4b09ee44ecf3322bf
```

**⚠️ 重要**: `.env`ファイルは`.gitignore`に含まれていることを確認してください。

---

## 🧪 Step 4: 動作確認

### 4.1 Notion Sync Agentのテスト

```bash
cd /Users/zero/Projects/resonant-engine
python3 utils/notion_sync_agent.py
```

**期待される出力**:
```
🔄 Notion Sync Agent - 同期トリガー検知テスト

[📡 Event Emitted] EVT-20251105-xxxxx: action from notion_sync
✅ 0件の仕様書が同期対象です
```

（現在、specsに「同期トリガー: Yes」のデータがないため0件）

### 4.2 テストデータの作成

Notionのspecsデータベースで：
1. 新しいページを作成
2. 以下を設定：
   - **名前**: テスト仕様書
   - **同期トリガー**: Yes
   - **構築ステータス**: 未構築
3. 保存

再度テストを実行：
```bash
python3 utils/notion_sync_agent.py
```

**期待される出力**:
```
✅ 1件の仕様書が同期対象です

📄 テスト仕様書
   ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ステータス: 未構築
   メモ: (なし)
   URL: https://www.notion.so/...
```

---

## 🔄 Step 5: 自動同期の設定

### 5.1 Notion同期デーモンの作成

定期的にNotionを監視するデーモンを作成予定：

```python
# daemon/notion_sync_daemon.py
# 60秒ごとにspecsを監視
# 同期トリガー: Yes を検知したら処理
```

### 5.2 統合イベントストリーム連携

Notion同期を他のシステムと統合：

```
Notion specs (同期トリガー: Yes)
  ↓
[Event] observation from notion_sync
  ↓
[Event] action: AI分析開始
  ↓
[Event] result: タスク生成
  ↓
Notion tasks に自動書き込み
```

---

## 📊 データベーススキーマ

### specs（仕様書）

| 列名 | 型 | 説明 |
|------|-----|------|
| 名前 | Title | 仕様書の名前 |
| 公開可 | Checkbox | 外部公開可否 |
| 同期トリガー | Select (Yes/No) | **Resonant Engineの同期対象** |
| 実行メモ | Rich text | 実装メモ |
| 最終同期 | Date | 最後に同期した日時 |
| 検収 | ? | 検収情報 |
| 構築ステータス | Select | 未構築/構築中/実稼働 |

### tasks（タスク）

| 列名 | 型 | 説明 |
|------|-----|------|
| タスク名 | Title | タスクの識別名 |
| 対象ページID | Text | **specsへの参照** |
| 担当 | Text | 実担当者名 |
| 優先度 | Select | Low/Medium/High/Urgent |
| 状態 | Select | ToDo/Doing/Blocked/Done |
| 期限 | Date | 期限日 |
| 備考 | Rich text | 補足情報 |

### reviews（レビュー）

| 列名 | 型 | 説明 |
|------|-----|------|
| 対象ページID | Text | **specsへの参照** |
| レビュー種別 | Select | ユノ/アトラス/外部 |
| ステータス | Select | Open/In Review/Resolved |
| 重要度 | Select | Low/Medium/High/Critical |
| レビュアー | Text | 担当レビュアー名 |
| コメント | Rich text | レビュー本文 |
| 公開可 | Checkbox | 公開サマリ出力可否 |

### resonant_archive（アーカイブ）

| 列名 | 型 | 説明 |
|------|-----|------|
| Phase | Title | フェーズ名 |
| Stability Index | Rich text | 安定性指標 |
| Coherence Ratio | Rich text | 一貫性比率 |
| Last Update | Rich text | 最終更新日時 |
| Telemetry (Base64) | Rich text | テレメトリデータ（Base64エンコード） |

---

## 🎯 次のステップ

### Phase 3: AI統合

1. **自動タスク生成**:
   - specsの変更を検知
   - AIが実装タスクを分解
   - tasksに自動書き込み

2. **自動レビュー**:
   - AIがコード変更をレビュー
   - reviewsに結果を書き込み
   - 「レビュー種別: ユノ/アトラス」を自動設定

3. **メトリクス記録**:
   - 開発活動のメトリクスを自動計算
   - resonant_archiveに定期書き込み

---

## ❓ トラブルシューティング

### エラー: "NOTION_TOKEN が設定されていません"

→ `.env`ファイルにトークンを追加してください

### エラー: "APIStatusError: object: database, status: 404"

→ データベースIDが間違っているか、Integrationが招待されていません

### エラー: "APIStatusError: status: 401"

→ Notion Tokenが無効です。再生成してください

---

作成: 2025-11-05  
更新: 2025-11-05

