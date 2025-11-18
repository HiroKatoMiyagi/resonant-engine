# Sprint 4.5: Claude Code API統合仕様書

## 0. 概要

**目的**: Intent処理にClaude Code機能を統合し、複雑なコード編集・生成タスクを自動化
**期間**: 3日間
**前提**: Sprint 4完了、Claude API統合済み

---

## 1. Done Definition

### Tier 1: 必須
- [ ] Claude Code呼び出しラッパー実装（claude_code_client.py）
- [ ] Intent振り分けロジック（Claude API vs Claude Code）
- [ ] Claude Code専用データベーステーブル（claude_code_sessions）
- [ ] セッション管理機能
- [ ] コードタスク実行と結果保存
- [ ] 既存intent_bridge.pyとの統合
- [ ] エラーハンドリングとタイムアウト処理

### Tier 2: 品質
- [ ] セッション履歴管理
- [ ] 並列実行制御（最大3セッション）
- [ ] リソース使用量監視
- [ ] Claude Code実行ログの構造化保存
- [ ] セキュリティ：サンドボックス実行環境

---

## 2. システムアーキテクチャ

```
┌──────────────────────────────────────────────────────────┐
│           Intent Processing with Claude Code             │
│                                                           │
│  User → Dashboard → POST /api/intents                    │
│                           ↓                              │
│  ┌────────────────────────────────────────────────┐     │
│  │           Intent Bridge                        │     │
│  │  ┌──────────────────────────────────────────┐ │     │
│  │  │  Intent分類ロジック                      │ │     │
│  │  │                                          │ │     │
│  │  │  if (requires_code_execution):           │ │     │
│  │  │      → Claude Code Client                │ │     │
│  │  │  else:                                   │ │     │
│  │  │      → Claude API (Sprint 4)             │ │     │
│  │  └──────────────────────────────────────────┘ │     │
│  └────────────────────────────────────────────────┘     │
│                 ↓                        ↓               │
│  ┌──────────────────────┐  ┌────────────────────────┐  │
│  │   Claude API         │  │  Claude Code Client    │  │
│  │   (思考・提案)        │  │  (コード実行)          │  │
│  │                      │  │                        │  │
│  │  - 質問応答          │  │  - ファイル編集        │  │
│  │  - アイデア生成      │  │  - コード生成          │  │
│  │  - 設計提案          │  │  - リファクタリング    │  │
│  │                      │  │  - テスト実行          │  │
│  │                      │  │  - Git操作             │  │
│  └──────────────────────┘  └────────────────────────┘  │
│                 ↓                        ↓               │
│  ┌──────────────────────────────────────────────────┐  │
│  │           PostgreSQL                              │  │
│  │  - intents                                        │  │
│  │  - claude_code_sessions (新規)                    │  │
│  │  - claude_code_executions (新規)                  │  │
│  │  - notifications                                  │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 3. データベース設計

### 3.1 claude_code_sessions テーブル

```sql
CREATE TABLE claude_code_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id UUID NOT NULL REFERENCES intents(id),
    session_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'running', 'completed', 'failed', 'timeout'
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_duration_seconds INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_intent ON claude_code_sessions(intent_id);
CREATE INDEX idx_sessions_status ON claude_code_sessions(status);
```

### 3.2 claude_code_executions テーブル

```sql
CREATE TABLE claude_code_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES claude_code_sessions(id),
    execution_order INTEGER NOT NULL,
    tool_name VARCHAR(100), -- 'Edit', 'Write', 'Read', 'Bash', etc.
    input_data JSONB,
    output_data JSONB,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_ms INTEGER
);

CREATE INDEX idx_executions_session ON claude_code_executions(session_id);
```

---

## 4. Claude Code Client実装

### 4.1 基本構造

```python
# bridge/claude_code_client.py
import asyncio
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

class ClaudeCodeClient:
    """
    Claude Code CLIをプログラマティックに呼び出すクライアント
    """

    def __init__(self, workspace_path: str = "/tmp/resonant_workspace"):
        self.workspace_path = workspace_path
        self.active_sessions = {}
        self.max_concurrent_sessions = 3

    async def execute_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300  # 5分
    ) -> Dict[str, Any]:
        """
        Claude Codeにタスクを実行させる

        Args:
            task_description: タスクの説明（日本語可）
            context: コンテキスト情報（ファイルパス、環境変数等）
            timeout: タイムアウト秒数

        Returns:
            実行結果（ファイル変更、出力、エラー等）
        """
        session_id = str(uuid.uuid4())

        # セッション数制限チェック
        while len(self.active_sessions) >= self.max_concurrent_sessions:
            await asyncio.sleep(1)

        self.active_sessions[session_id] = {
            'started_at': datetime.now(),
            'status': 'running'
        }

        try:
            result = await self._run_claude_code_session(
                session_id=session_id,
                task=task_description,
                context=context,
                timeout=timeout
            )

            self.active_sessions[session_id]['status'] = 'completed'
            return result

        except asyncio.TimeoutError:
            self.active_sessions[session_id]['status'] = 'timeout'
            raise
        except Exception as e:
            self.active_sessions[session_id]['status'] = 'failed'
            raise
        finally:
            # セッションクリーンアップ（5秒後）
            await asyncio.sleep(5)
            del self.active_sessions[session_id]

    async def _run_claude_code_session(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Claude Code CLIセッションを実行
        """

        # 1. ワークスペース準備
        workspace = f"{self.workspace_path}/{session_id}"
        await self._prepare_workspace(workspace, context)

        # 2. Claude Code呼び出し
        # 注: Claude Code CLIは対話的なため、プロンプトファイル経由で実行
        prompt_file = f"{workspace}/.claude_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(task)

        # 3. Claude Code実行（非対話モード）
        process = await asyncio.create_subprocess_exec(
            'claude-code',
            '--workspace', workspace,
            '--non-interactive',
            '--prompt-file', prompt_file,
            '--output-format', 'json',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            # 4. 結果パース
            result = json.loads(stdout.decode())

            # 5. ファイル変更検出
            changes = await self._detect_file_changes(workspace)

            return {
                'session_id': session_id,
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'file_changes': changes,
                'executions': result.get('tool_calls', []),
                'error': stderr.decode() if stderr else None
            }

        except asyncio.TimeoutError:
            process.kill()
            raise

    async def _prepare_workspace(
        self,
        workspace: str,
        context: Optional[Dict[str, Any]]
    ):
        """ワークスペース準備"""
        import os
        os.makedirs(workspace, exist_ok=True)

        # コンテキストファイルをワークスペースにコピー
        if context and 'files' in context:
            for file_path in context['files']:
                # ファイルコピー処理
                pass

    async def _detect_file_changes(self, workspace: str) -> list:
        """ファイル変更検出（git diff等）"""
        # Git diff等で変更を検出
        return []
```

### 4.2 Intent振り分けロジック

```python
# bridge/intent_classifier.py
from typing import Dict, Literal

IntentType = Literal['chat', 'code_execution']

class IntentClassifier:
    """
    IntentをClaude APIまたはClaude Codeに振り分ける
    """

    # Claude Code実行が必要なキーワード
    CODE_EXECUTION_KEYWORDS = [
        'ファイルを編集',
        'コードを生成',
        'リファクタリング',
        'テストを実行',
        'git commit',
        'デプロイ',
        '実装して',
        'PRを作成',
        'バグを修正'
    ]

    @staticmethod
    def classify(intent_description: str) -> IntentType:
        """
        Intent記述から処理タイプを判定

        Args:
            intent_description: Intentの説明文

        Returns:
            'chat': Claude APIで処理
            'code_execution': Claude Codeで処理
        """
        description_lower = intent_description.lower()

        # コード実行キーワードチェック
        for keyword in IntentClassifier.CODE_EXECUTION_KEYWORDS:
            if keyword in description_lower:
                return 'code_execution'

        # ファイルパス言及チェック（.py, .js等）
        if any(ext in description_lower for ext in ['.py', '.js', '.ts', '.tsx', '.sql']):
            return 'code_execution'

        # デフォルトはチャット
        return 'chat'
```

---

## 5. Intent Bridge統合

### 5.1 intent_bridge.py更新

```python
# bridge/intent_bridge.py (Sprint 4からの更新)
from intent_classifier import IntentClassifier
from claude_code_client import ClaudeCodeClient

class IntentBridge:
    def __init__(self):
        self.pool = None
        self.claude_api = anthropic.Anthropic()
        self.claude_code = ClaudeCodeClient()
        self.classifier = IntentClassifier()

    async def process_intent(self, intent_id):
        async with self.pool.acquire() as conn:
            # 1. Intent取得
            intent = await conn.fetchrow(
                "SELECT * FROM intents WHERE id = $1",
                intent_id
            )

            # 2. Intent分類
            intent_type = self.classifier.classify(intent['description'])

            # 3. ステータス更新
            await conn.execute(
                "UPDATE intents SET status = 'processing', updated_at = NOW() WHERE id = $1",
                intent_id
            )

            try:
                if intent_type == 'code_execution':
                    # Claude Code実行
                    result = await self._process_with_claude_code(conn, intent)
                else:
                    # Claude API実行（Sprint 4）
                    result = await self._process_with_claude_api(intent)

                # 4. 結果保存
                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(result), intent_id)

                await self.create_notification(conn, intent_id, "success")

            except Exception as e:
                await conn.execute("""
                    UPDATE intents
                    SET status = 'failed',
                        result = $1,
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps({"error": str(e)}), intent_id)

                await self.create_notification(conn, intent_id, "error")

    async def _process_with_claude_code(self, conn, intent) -> Dict:
        """Claude Codeで処理"""

        # 1. セッション作成
        session = await conn.fetchrow("""
            INSERT INTO claude_code_sessions (intent_id, session_id, status)
            VALUES ($1, $2, 'running')
            RETURNING *
        """, intent['id'], str(uuid.uuid4()))

        try:
            # 2. Claude Code実行
            result = await self.claude_code.execute_task(
                task_description=intent['description'],
                context={
                    'workspace': '/opt/resonant/workspace',
                    'files': []  # 必要なファイルパス
                },
                timeout=300
            )

            # 3. 実行履歴保存
            for idx, execution in enumerate(result['executions']):
                await conn.execute("""
                    INSERT INTO claude_code_executions
                    (session_id, execution_order, tool_name, input_data, output_data, success)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    session['id'],
                    idx,
                    execution.get('tool'),
                    json.dumps(execution.get('input')),
                    json.dumps(execution.get('output')),
                    execution.get('success', True)
                )

            # 4. セッション完了
            duration = (datetime.now() - session['started_at']).total_seconds()
            await conn.execute("""
                UPDATE claude_code_sessions
                SET status = 'completed',
                    completed_at = NOW(),
                    total_duration_seconds = $1
                WHERE id = $2
            """, int(duration), session['id'])

            return {
                'type': 'code_execution',
                'session_id': session['session_id'],
                'output': result['output'],
                'file_changes': result['file_changes'],
                'success': result['success']
            }

        except asyncio.TimeoutError:
            await conn.execute(
                "UPDATE claude_code_sessions SET status = 'timeout' WHERE id = $1",
                session['id']
            )
            raise
        except Exception as e:
            await conn.execute(
                "UPDATE claude_code_sessions SET status = 'failed' WHERE id = $1",
                session['id']
            )
            raise

    async def _process_with_claude_api(self, intent) -> Dict:
        """Claude APIで処理（Sprint 4からの既存実装）"""
        message = self.claude_api.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": intent['description']
            }]
        )
        return {
            'type': 'chat',
            'response': message.content[0].text,
            'model': message.model,
            'tokens': message.usage.output_tokens
        }
```

---

## 6. セキュリティとリソース管理

### 6.1 サンドボックス実行

```python
# Claude Code実行を隔離環境で実行
# Docker in Dockerまたはfirejailを使用

async def _run_in_sandbox(self, command: list, workspace: str):
    """
    サンドボックス内でClaude Code実行
    """
    process = await asyncio.create_subprocess_exec(
        'firejail',
        '--private=' + workspace,
        '--net=none',  # ネットワーク無効（必要に応じて）
        '--rlimit-as=2g',  # メモリ制限
        '--timeout=00:05:00',  # 5分タイムアウト
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return await process.communicate()
```

### 6.2 リソース制限

```python
# 同時実行制限
MAX_CONCURRENT_SESSIONS = 3

# メモリ制限
MAX_MEMORY_PER_SESSION = "2GB"

# タイムアウト
DEFAULT_TIMEOUT = 300  # 5分
MAX_TIMEOUT = 900  # 15分
```

---

## 7. フロントエンド統合

### 7.1 Intent作成時の実行タイプ選択

```typescript
// frontend/src/types/intent.ts
export type IntentExecutionType = 'auto' | 'claude_api' | 'claude_code';

export interface CreateIntentRequest {
  description: string;
  priority: 'low' | 'medium' | 'high';
  execution_type?: IntentExecutionType;  // デフォルト: 'auto'
}
```

### 7.2 実行履歴表示

```typescript
// Claude Code実行履歴を表示するコンポーネント
export const ClaudeCodeExecutionLog = ({ sessionId }: { sessionId: string }) => {
  const { data: executions } = useQuery(
    ['claude_code_executions', sessionId],
    () => fetchExecutions(sessionId)
  );

  return (
    <div className="execution-log">
      {executions?.map(exec => (
        <div key={exec.id} className="execution-item">
          <span className="tool-name">{exec.tool_name}</span>
          <span className="status">{exec.success ? '✓' : '✗'}</span>
          <span className="duration">{exec.duration_ms}ms</span>
        </div>
      ))}
    </div>
  );
};
```

---

## 8. API拡張

### 8.1 新規エンドポイント

```python
# backend/api/claude_code.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/claude_code", tags=["claude_code"])

@router.get("/sessions/{intent_id}")
async def get_sessions(intent_id: str):
    """Intent関連のClaude Codeセッション一覧"""
    pass

@router.get("/sessions/{session_id}/executions")
async def get_executions(session_id: str):
    """セッション内の実行履歴"""
    pass

@router.get("/stats")
async def get_stats():
    """統計情報（成功率、平均実行時間等）"""
    pass
```

---

## 9. モニタリング

### 9.1 メトリクス

- `claude_code_sessions_total`: 総セッション数
- `claude_code_sessions_success_rate`: 成功率
- `claude_code_execution_duration_seconds`: 平均実行時間
- `claude_code_active_sessions`: 現在実行中のセッション数
- `claude_code_timeout_total`: タイムアウト数

### 9.2 ログ

```
2025-11-18 14:30:00 [INFO] Intent abc123 classified as 'code_execution'
2025-11-18 14:30:01 [INFO] Claude Code session started: session_xyz
2025-11-18 14:30:05 [INFO] Tool executed: Edit (file: main.py, duration: 450ms)
2025-11-18 14:30:07 [INFO] Tool executed: Bash (command: pytest, duration: 1200ms)
2025-11-18 14:30:08 [INFO] Claude Code session completed: session_xyz (7.8s)
```

---

## 10. 使用例

### 10.1 ケース1: ファイル編集

**Intent**: "src/main.pyのcalculate関数をリファクタリングして、型ヒントを追加して"

**処理フロー**:
1. 分類器が `code_execution` と判定
2. Claude Codeセッション起動
3. src/main.py読み込み
4. リファクタリング実行
5. 変更をcommit（オプション）
6. 結果をDBに保存

### 10.2 ケース2: テスト実行

**Intent**: "backendのユニットテストを実行して、失敗があれば修正して"

**処理フロー**:
1. `code_execution` 判定
2. `pytest` 実行
3. エラー解析
4. コード修正
5. 再テスト
6. 結果レポート

### 10.3 ケース3: チャット

**Intent**: "PostgreSQLのパフォーマンスチューニングについて教えて"

**処理フロー**:
1. 分類器が `chat` と判定
2. Claude API呼び出し（Sprint 4）
3. 応答をDBに保存

---

## 11. 成功基準

- [ ] Intent自動分類（Claude API / Claude Code）動作
- [ ] Claude Codeセッション実行と結果保存
- [ ] ファイル編集・コード生成タスクの成功
- [ ] タイムアウト・エラーハンドリング動作
- [ ] セッション並列実行制限（最大3）動作
- [ ] 実行履歴の詳細記録
- [ ] セキュリティ：サンドボックス実行確認

---

## 12. 制限事項と将来拡張

### 12.1 現在の制限

- Claude Code CLIの非対話モードが存在しない場合、expect/pexpect経由の実装が必要
- ファイルシステムアクセスはサンドボックス内に制限
- 複数リポジトリの同時編集は未対応

### 12.2 Phase 2拡張案

- Agent SDK直接統合（より高度な制御）
- MCP (Model Context Protocol) サーバー統合
- Claude CodeのStreaming出力リアルタイム表示
- 複数プロジェクト横断タスク

---

**作成日**: 2025-11-18
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**Sprint**: 4.5（Claude Code API統合）
**依存**: Sprint 4完了必須
