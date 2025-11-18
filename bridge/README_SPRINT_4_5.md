# Sprint 4.5: Claude Code API Integration

PostgreSQL DashboardシステムのIntent処理に Claude Code API統合を追加

---

## 概要

Intent記述から自動的にClaude APIまたはClaude Code実行を判定し、適切に処理します。

- **Sprint 4**: Claude API統合（質問応答、提案等）
- **Sprint 4.5**: Claude Code統合（コード編集、生成、実行等）

---

## コンポーネント

### 1. Intent Classifier (`intent_classifier.py`)

Intent記述からClaude API vs Claude Code自動判定

**機能:**
- キーワードベース分類（日本語/英語対応）
- ファイルパス/拡張子検出
- 信頼度スコア算出

**使用例:**
```python
from intent_classifier import IntentClassifier

intent_type = IntentClassifier.classify("bridge/intent_bridge.pyを編集してログ追加")
# → 'code_execution'

intent_type = IntentClassifier.classify("PostgreSQLのベストプラクティスを教えて")
# → 'chat'
```

---

### 2. Context Loader (`context_loader.py`)

Intent記述から関連コンテキストファイルを自動検出

**機能:**
- Sprint番号自動抽出（例: "Sprint 4.5" → [4, 5]）
- 関連Sprintドキュメント自動収集
- 依存Sprint含める（Sprint N → Sprint 1も含む）
- 必須ファイル自動ロード（CLAUDE.md、Resonant Regulations）
- キーワードベースファイル検索

**使用例:**
```python
from context_loader import ContextLoader

loader = ContextLoader()
context = loader.load_context_for_intent("Sprint 4.5実装を開始")

# context['files']: ロードされたファイルリスト
# context['related_sprints']: [4, 5]
# context['context_summary']: サマリー文字列
```

---

### 3. Claude Code Client (`claude_code_client.py`)

Claude Code CLIをプログラマティックに呼び出すクライアント

**モード:**
- **Repository Mode**: メインリポジトリで実行（過去Sprint情報アクセス可能）
- **Isolated Mode**: サンドボックス実行

**機能:**
- Git branch自動作成（`claude/session-{id}`）
- 拡張プロンプト生成（コンテキスト付き）
- セッション並列実行制限（最大3）

**使用例:**
```python
from claude_code_client import ClaudeCodeClient

client = ClaudeCodeClient(workspace_mode='repository')
result = await client.execute_task(
    task_description="bridge/README.mdを作成",
    context={'files': [...], 'related_sprints': [4, 5]},
    timeout=300
)
```

---

### 4. Intent Bridge (`intent_bridge.py`)

Intent自動処理デーモン（Sprint 4 + 4.5統合版）

**機能:**
- PostgreSQL LISTEN/NOTIFYでIntent検知
- Intent分類（Claude API vs Claude Code）
- コンテキスト自動ロード
- DB記憶統合（過去Intent参照）
- 処理結果保存
- 通知生成

**起動:**
```bash
cd /home/user/resonant-engine
python3 bridge/intent_bridge.py
```

---

## データベーステーブル

### claude_code_sessions

Claude Codeセッション管理

```sql
CREATE TABLE claude_code_sessions (
    id UUID PRIMARY KEY,
    intent_id UUID REFERENCES intents(id),
    session_id VARCHAR(255) UNIQUE,
    status VARCHAR(50),  -- 'running', 'completed', 'failed', 'timeout'
    workspace_mode VARCHAR(50),  -- 'repository', 'isolated'
    metadata JSONB,  -- context_files, branch等
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_duration_seconds INTEGER,
    ...
);
```

### claude_code_executions

ツール実行履歴

```sql
CREATE TABLE claude_code_executions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES claude_code_sessions(id),
    execution_order INTEGER,
    tool_name VARCHAR(100),  -- 'Edit', 'Write', 'Read', 'Bash'等
    input_data JSONB,
    output_data JSONB,
    success BOOLEAN,
    ...
);
```

---

## 環境変数

```bash
# PostgreSQL接続
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=resonant_dashboard
POSTGRES_USER=resonant
POSTGRES_PASSWORD=your_password

# Claude API
ANTHROPIC_API_KEY=your_api_key
```

---

## 運用フロー

```
1. Intent投稿
   User → Dashboard → POST /api/intents

2. PostgreSQL
   INSERT INTO intents → NOTIFY intent_created

3. Intent Bridge
   LISTEN intent_created → Intent受信

4. Intent分類
   "ファイルを編集" → code_execution
   "教えて" → chat

5. コンテキストロード
   Sprint番号抽出 → 関連ファイル収集 → DB記憶取得

6. 実行
   code_execution: Claude Code実行（Repository Mode）
   chat: Claude API実行

7. 結果保存
   intents.result更新
   claude_code_sessions INSERT
   claude_code_executions INSERT

8. 通知
   notifications INSERT → Dashboard表示
```

---

## テスト

### Intent Classifier

```bash
python3 bridge/intent_classifier.py
```

### Context Loader

```bash
python3 bridge/context_loader.py
```

### Claude Code Client

```bash
python3 bridge/claude_code_client.py
```

---

## 次のステップ

### Phase 2（今後の拡張）

1. **実際のClaude Code API統合**
   - モック実装を実際のAPI呼び出しに置き換え
   - Tool呼び出し履歴の詳細記録

2. **MCP (Model Context Protocol) 統合**
   - より高度なコンテキスト管理

3. **Claude CodeのStreaming出力**
   - リアルタイム進捗表示

4. **複数プロジェクト横断タスク**
   - resonant-engine以外のリポジトリにも対応

---

## トラブルシューティング

### Intent Bridgeが起動しない

```bash
# PostgreSQL接続確認
psql -h localhost -U resonant -d resonant_dashboard

# 環境変数確認
env | grep POSTGRES
env | grep ANTHROPIC
```

### Claude Code実行がタイムアウト

```python
# タイムアウト時間を延長
result = await client.execute_task(
    task_description="...",
    timeout=600  # 10分
)
```

---

**作成日**: 2025-11-18
**Sprint**: 4.5
**ステータス**: Phase 1完了（コアコンポーネント実装済み）
