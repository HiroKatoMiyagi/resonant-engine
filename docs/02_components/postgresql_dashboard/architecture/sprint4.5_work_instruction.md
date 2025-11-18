# Sprint 4.5 作業開始指示書

## Claude Code API統合 - 3日間実装ガイド

---

## 0. 前提条件チェックリスト

作業開始前に以下を確認してください：

- [ ] Sprint 4完了（Claude API統合済み）
- [ ] PostgreSQL Dashboard 稼働中
- [ ] intent_bridge.py 動作確認済み
- [ ] Claude Code CLIがローカル/本番環境にインストール済み
- [ ] Claude Code APIキー設定済み（ANTHROPIC_API_KEY）
- [ ] Python 3.11+ 環境
- [ ] asyncio, asyncpg ライブラリ導入済み

---

## 1. 全体タイムライン（3日間）

### Day 1: データベース設計と基盤実装
**成果物**:
- [ ] DB テーブル作成（claude_code_sessions, claude_code_executions）
- [ ] Intent分類ロジック実装
- [ ] Claude Code Client 基本構造

### Day 2: Claude Code統合とIntent Bridge更新
**成果物**:
- [ ] Claude Code実行ラッパー完成
- [ ] intent_bridge.py統合
- [ ] エラーハンドリング実装

### Day 3: テスト・モニタリング・ドキュメント
**成果物**:
- [ ] E2Eテスト実施
- [ ] ログ・メトリクス設定
- [ ] フロントエンド連携（オプション）

---

## 2. Day 1: データベース設計と基盤実装

### 2.1 データベーステーブル作成

**作業場所**: `docker/db/migrations/`

**手順**:

1. マイグレーションファイル作成

```bash
cd /home/user/resonant-engine/docker/db/migrations
touch 006_claude_code_tables.sql
```

2. テーブル定義記述

```sql
-- docker/db/migrations/006_claude_code_tables.sql

-- Claude Codeセッション管理テーブル
CREATE TABLE IF NOT EXISTS claude_code_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id UUID NOT NULL REFERENCES intents(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'timeout')),
    workspace_path TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_duration_seconds INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Claude Code実行履歴テーブル
CREATE TABLE IF NOT EXISTS claude_code_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES claude_code_sessions(id) ON DELETE CASCADE,
    execution_order INTEGER NOT NULL,
    tool_name VARCHAR(100),
    input_data JSONB,
    output_data JSONB,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES claude_code_sessions(id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_sessions_intent ON claude_code_sessions(intent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON claude_code_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON claude_code_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_session ON claude_code_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_executions_order ON claude_code_executions(session_id, execution_order);

-- updated_atトリガー
CREATE TRIGGER update_claude_code_sessions_updated_at
    BEFORE UPDATE ON claude_code_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE claude_code_sessions IS 'Claude Codeセッション管理';
COMMENT ON TABLE claude_code_executions IS 'Claude Code実行履歴（ツール呼び出し単位）';
```

3. マイグレーション適用

```bash
# PostgreSQLコンテナ内で実行
docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard < docker/db/migrations/006_claude_code_tables.sql

# または docker-compose経由
docker-compose exec postgres psql -U resonant -d resonant_dashboard -f /docker-entrypoint-initdb.d/006_claude_code_tables.sql
```

4. 確認

```bash
docker exec -it resonant_postgres psql -U resonant -d resonant_dashboard -c "\dt claude_code*"
```

**成功基準**:
- `claude_code_sessions` テーブル作成完了
- `claude_code_executions` テーブル作成完了
- 全インデックス作成完了

---

### 2.2 Intent分類ロジック実装

**作業場所**: `bridge/intent_classifier.py`（新規作成）

**手順**:

1. ファイル作成

```bash
cd /home/user/resonant-engine/bridge
touch intent_classifier.py
```

2. 実装

```python
# bridge/intent_classifier.py
from typing import Literal
import re

IntentType = Literal['chat', 'code_execution']

class IntentClassifier:
    """
    Intent記述からClaude APIまたはClaude Code実行を判定
    """

    # Claude Code実行が必要なキーワード（日本語）
    CODE_EXECUTION_KEYWORDS = [
        # ファイル操作
        'ファイルを編集', 'ファイルを作成', 'ファイルを削除',
        'コードを追加', 'コードを修正', 'コードを削除',

        # コード生成
        'コードを生成', '関数を作成', 'クラスを作成',
        '実装して', 'コードを書いて',

        # リファクタリング
        'リファクタリング', 'リネーム', '整理して',

        # テスト・実行
        'テストを実行', 'pytest', 'unittest',
        'ビルド', 'デプロイ', 'run',

        # Git操作
        'git commit', 'git push', 'PRを作成',
        'コミット', 'プッシュ',

        # バグ修正
        'バグを修正', 'エラーを直して', 'デバッグ',

        # 英語キーワード
        'edit file', 'create file', 'implement',
        'refactor', 'fix bug', 'run test'
    ]

    # ファイル拡張子パターン
    FILE_EXTENSION_PATTERN = re.compile(
        r'\.(py|js|ts|tsx|jsx|sql|sh|yaml|yml|json|md|txt|html|css)(?:\s|$)',
        re.IGNORECASE
    )

    # ファイルパスパターン（例: src/main.py）
    FILE_PATH_PATTERN = re.compile(
        r'(?:^|\s)[\w/]+\.[\w]+(?:\s|$)'
    )

    @classmethod
    def classify(cls, intent_description: str) -> IntentType:
        """
        Intent記述から処理タイプを判定

        Args:
            intent_description: Intentの説明文

        Returns:
            'chat': Claude APIで処理（質問応答、提案等）
            'code_execution': Claude Codeで処理（コード編集、実行等）
        """
        description_lower = intent_description.lower()

        # 1. コード実行キーワードチェック
        for keyword in cls.CODE_EXECUTION_KEYWORDS:
            if keyword.lower() in description_lower:
                return 'code_execution'

        # 2. ファイル拡張子チェック
        if cls.FILE_EXTENSION_PATTERN.search(intent_description):
            return 'code_execution'

        # 3. ファイルパスチェック（例: src/main.py）
        if cls.FILE_PATH_PATTERN.search(intent_description):
            return 'code_execution'

        # デフォルトはチャット（質問・提案等）
        return 'chat'

    @classmethod
    def get_confidence(cls, intent_description: str) -> float:
        """
        分類の信頼度を返す（0.0〜1.0）

        Returns:
            信頼度（高いほど確信が高い）
        """
        score = 0.0
        description_lower = intent_description.lower()

        # キーワードマッチ数
        keyword_matches = sum(
            1 for kw in cls.CODE_EXECUTION_KEYWORDS
            if kw.lower() in description_lower
        )
        score += min(keyword_matches * 0.2, 0.6)

        # ファイル拡張子
        if cls.FILE_EXTENSION_PATTERN.search(intent_description):
            score += 0.3

        # ファイルパス
        if cls.FILE_PATH_PATTERN.search(intent_description):
            score += 0.1

        return min(score, 1.0)
```

3. テストコード作成

```python
# bridge/test_intent_classifier.py
import pytest
from intent_classifier import IntentClassifier

def test_code_execution_classification():
    # コード実行判定テスト
    assert IntentClassifier.classify("src/main.pyを編集して関数を追加") == 'code_execution'
    assert IntentClassifier.classify("testを実行してエラーを修正") == 'code_execution'
    assert IntentClassifier.classify("新しいAPIエンドポイントを実装して") == 'code_execution'

def test_chat_classification():
    # チャット判定テスト
    assert IntentClassifier.classify("PostgreSQLのパフォーマンスについて教えて") == 'chat'
    assert IntentClassifier.classify("おすすめのアーキテクチャは？") == 'chat'

def test_confidence():
    # 信頼度テスト
    high_conf = IntentClassifier.get_confidence("src/main.pyを編集してバグを修正")
    low_conf = IntentClassifier.get_confidence("どう思う？")
    assert high_conf > 0.5
    assert low_conf < 0.3
```

4. テスト実行

```bash
cd /home/user/resonant-engine/bridge
python -m pytest test_intent_classifier.py -v
```

**成功基準**:
- 全テストケース通過
- コード実行/チャットの判定精度 > 90%

---

### 2.3 Claude Code Client 基本構造実装

**作業場所**: `bridge/claude_code_client.py`（新規作成）

**手順**:

1. ファイル作成

```bash
cd /home/user/resonant-engine/bridge
touch claude_code_client.py
```

2. 基本構造実装（Day 1はスケルトンのみ）

```python
# bridge/claude_code_client.py
import asyncio
import json
import uuid
import os
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

class ClaudeCodeClient:
    """
    Claude Code CLIをプログラマティックに呼び出すクライアント
    """

    def __init__(
        self,
        workspace_root: str = "/tmp/resonant_workspace",
        max_concurrent_sessions: int = 3,
        default_timeout: int = 300
    ):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.max_concurrent_sessions = max_concurrent_sessions
        self.default_timeout = default_timeout

    async def execute_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Claude Codeにタスクを実行させる

        Args:
            task_description: タスクの説明
            context: コンテキスト情報（ファイルパス、環境変数等）
            timeout: タイムアウト秒数（Noneの場合はdefault_timeout使用）

        Returns:
            {
                'session_id': str,
                'success': bool,
                'output': str,
                'file_changes': list,
                'executions': list,
                'error': Optional[str]
            }
        """
        session_id = str(uuid.uuid4())
        timeout = timeout or self.default_timeout

        # セッション数制限チェック
        await self._wait_for_slot()

        self.active_sessions[session_id] = {
            'started_at': datetime.now(),
            'status': 'running',
            'task': task_description
        }

        try:
            result = await self._run_claude_code_session(
                session_id=session_id,
                task=task_description,
                context=context or {},
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
            asyncio.create_task(self._cleanup_session(session_id, delay=5))

    async def _wait_for_slot(self):
        """セッション数制限待機"""
        while len(self.active_sessions) >= self.max_concurrent_sessions:
            await asyncio.sleep(0.5)

    async def _run_claude_code_session(
        self,
        session_id: str,
        task: str,
        context: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Claude Code CLIセッションを実行

        NOTE: Day 2で詳細実装
        """
        # TODO: Day 2で実装
        return {
            'session_id': session_id,
            'success': True,
            'output': 'Mock output',
            'file_changes': [],
            'executions': [],
            'error': None
        }

    async def _cleanup_session(self, session_id: str, delay: int = 5):
        """セッションクリーンアップ"""
        await asyncio.sleep(delay)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def get_active_sessions(self) -> list:
        """現在実行中のセッション一覧"""
        return [
            {
                'session_id': sid,
                'status': info['status'],
                'started_at': info['started_at'].isoformat(),
                'task': info.get('task', '')
            }
            for sid, info in self.active_sessions.items()
        ]
```

3. 簡易テスト

```python
# bridge/test_claude_code_client.py
import pytest
import asyncio
from claude_code_client import ClaudeCodeClient

@pytest.mark.asyncio
async def test_basic_execution():
    client = ClaudeCodeClient()
    result = await client.execute_task("テストタスク")
    assert result['success'] is True
    assert 'session_id' in result

@pytest.mark.asyncio
async def test_concurrent_limit():
    client = ClaudeCodeClient(max_concurrent_sessions=2)

    # 3タスク同時実行
    tasks = [
        client.execute_task(f"Task {i}")
        for i in range(3)
    ]

    results = await asyncio.gather(*tasks)
    assert len(results) == 3
```

**成功基準**:
- ファイル作成完了
- 基本構造実装完了（実行ロジックはDay 2）
- セッション管理ロジック動作確認

---

### Day 1 完了チェック

- [ ] DBテーブル2つ作成完了
- [ ] intent_classifier.py実装完了
- [ ] claude_code_client.py骨組み完成
- [ ] 全テスト通過

---

## 3. Day 2: Claude Code統合とIntent Bridge更新

### 3.1 Claude Code実行ラッパー完成

**作業場所**: `bridge/claude_code_client.py`

**手順**:

1. `_run_claude_code_session` 実装

```python
async def _run_claude_code_session(
    self,
    session_id: str,
    task: str,
    context: Dict[str, Any],
    timeout: int
) -> Dict[str, Any]:
    """
    Claude Code CLIセッションを実行
    """

    # 1. ワークスペース準備
    workspace = self.workspace_root / session_id
    workspace.mkdir(parents=True, exist_ok=True)

    # 2. プロンプトファイル作成
    prompt_file = workspace / ".claude_prompt.txt"
    prompt_file.write_text(task, encoding='utf-8')

    # 3. コンテキストファイルコピー（オプション）
    if 'files' in context:
        for src_file in context['files']:
            # ファイルコピー処理
            pass

    # 4. Claude Code実行
    # NOTE: 現時点でClaude Codeに非対話モードがない場合、
    #       代替として expect/pexpect を使用
    try:
        result = await self._execute_claude_code_cli(
            workspace=str(workspace),
            prompt=task,
            timeout=timeout
        )

        return {
            'session_id': session_id,
            'success': result['exit_code'] == 0,
            'output': result['stdout'],
            'file_changes': await self._detect_file_changes(workspace),
            'executions': result.get('tool_calls', []),
            'error': result.get('stderr') if result['exit_code'] != 0 else None
        }

    except asyncio.TimeoutError:
        raise

    except Exception as e:
        return {
            'session_id': session_id,
            'success': False,
            'output': '',
            'file_changes': [],
            'executions': [],
            'error': str(e)
        }

async def _execute_claude_code_cli(
    self,
    workspace: str,
    prompt: str,
    timeout: int
) -> Dict[str, Any]:
    """
    Claude Code CLI実行（pexpect使用）

    NOTE: Claude Code CLIが非対話モードを提供していない場合の代替実装
    """
    import pexpect

    # Claude Code起動
    child = pexpect.spawn(
        'claude-code',
        args=['--workspace', workspace],
        timeout=timeout,
        encoding='utf-8'
    )

    try:
        # プロンプト送信
        child.expect('>')  # Claude Codeのプロンプト
        child.sendline(prompt)

        # 実行完了待機
        child.expect('Task completed|Error occurred', timeout=timeout)

        output = child.before + child.after
        child.sendline('exit')
        child.wait()

        return {
            'exit_code': child.exitstatus,
            'stdout': output,
            'stderr': '',
            'tool_calls': self._parse_tool_calls(output)
        }

    except pexpect.TIMEOUT:
        child.kill(9)
        raise asyncio.TimeoutError()

    except Exception as e:
        child.kill(9)
        raise

async def _detect_file_changes(self, workspace: Path) -> list:
    """ファイル変更検出（git diff等）"""
    changes = []

    # ワークスペース内のファイルを走査
    for file_path in workspace.rglob('*'):
        if file_path.is_file() and not file_path.name.startswith('.'):
            changes.append({
                'file': str(file_path.relative_to(workspace)),
                'type': 'modified'  # TODO: 追加/削除/変更を区別
            })

    return changes

def _parse_tool_calls(self, output: str) -> list:
    """Claude Code出力からツール呼び出しを抽出"""
    # TODO: 出力パース実装
    return []
```

2. 依存パッケージ追加

```bash
# requirements.txt に追加
echo "pexpect>=4.8.0" >> /home/user/resonant-engine/bridge/requirements.txt
pip install pexpect
```

**成功基準**:
- Claude Code CLI実行成功
- ファイル変更検出動作

---

### 3.2 Intent Bridge統合

**作業場所**: `bridge/intent_bridge.py`

**手順**:

1. `intent_bridge.py` 更新

```python
# bridge/intent_bridge.py
from intent_classifier import IntentClassifier
from claude_code_client import ClaudeCodeClient
import anthropic
import asyncpg
import json
from datetime import datetime

class IntentBridge:
    def __init__(self):
        self.pool = None
        self.claude_api = anthropic.Anthropic()
        self.claude_code = ClaudeCodeClient()
        self.classifier = IntentClassifier()

    # ... 既存の start(), listen_for_intents() 等 ...

    async def process_intent(self, intent_id):
        """
        Intent処理のメインロジック（Sprint 4から更新）
        """
        async with self.pool.acquire() as conn:
            # 1. Intent取得
            intent = await conn.fetchrow(
                "SELECT * FROM intents WHERE id = $1",
                intent_id
            )

            # 2. Intent分類
            intent_type = self.classifier.classify(intent['description'])
            confidence = self.classifier.get_confidence(intent['description'])

            print(f"📊 Intent分類: {intent_type} (信頼度: {confidence:.2f})")

            # 3. ステータス更新: processing
            await conn.execute(
                """UPDATE intents
                   SET status = 'processing',
                       metadata = jsonb_set(
                           COALESCE(metadata, '{}'),
                           '{intent_type}',
                           to_jsonb($2::text)
                       ),
                       updated_at = NOW()
                   WHERE id = $1""",
                intent_id,
                intent_type
            )

            try:
                # 4. タイプに応じた処理
                if intent_type == 'code_execution':
                    result = await self._process_with_claude_code(conn, intent)
                else:
                    result = await self._process_with_claude_api(intent)

                # 5. 結果保存
                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(result), intent_id)

                await self.create_notification(conn, intent_id, "success")

                print(f"✅ Intent {intent_id} 処理完了 ({intent_type})")

            except Exception as e:
                await conn.execute("""
                    UPDATE intents
                    SET status = 'failed',
                        result = $1,
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps({"error": str(e)}), intent_id)

                await self.create_notification(conn, intent_id, "error")
                print(f"❌ Intent {intent_id} 失敗: {e}")

    async def _process_with_claude_code(self, conn, intent) -> Dict:
        """
        Claude Codeで処理（新規実装）
        """
        # 1. セッション作成
        session_id = str(uuid.uuid4())
        session = await conn.fetchrow("""
            INSERT INTO claude_code_sessions (intent_id, session_id, status)
            VALUES ($1, $2, 'running')
            RETURNING *
        """, intent['id'], session_id)

        try:
            # 2. Claude Code実行
            result = await self.claude_code.execute_task(
                task_description=intent['description'],
                context={
                    'workspace': '/opt/resonant/workspace',
                    'files': []
                },
                timeout=300
            )

            # 3. 実行履歴保存
            for idx, execution in enumerate(result.get('executions', [])):
                await conn.execute("""
                    INSERT INTO claude_code_executions
                    (session_id, execution_order, tool_name, input_data, output_data, success)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    session['id'],
                    idx,
                    execution.get('tool'),
                    json.dumps(execution.get('input', {})),
                    json.dumps(execution.get('output', {})),
                    execution.get('success', True)
                )

            # 4. セッション完了
            duration = (datetime.now() - session['started_at']).total_seconds()
            await conn.execute("""
                UPDATE claude_code_sessions
                SET status = 'completed',
                    completed_at = NOW(),
                    total_duration_seconds = $1,
                    updated_at = NOW()
                WHERE id = $2
            """, int(duration), session['id'])

            return {
                'type': 'code_execution',
                'session_id': session_id,
                'output': result['output'],
                'file_changes': result['file_changes'],
                'success': result['success']
            }

        except asyncio.TimeoutError:
            await conn.execute(
                "UPDATE claude_code_sessions SET status = 'timeout', updated_at = NOW() WHERE id = $1",
                session['id']
            )
            raise

        except Exception as e:
            await conn.execute(
                "UPDATE claude_code_sessions SET status = 'failed', updated_at = NOW() WHERE id = $1",
                session['id']
            )
            raise

    async def _process_with_claude_api(self, intent) -> Dict:
        """
        Claude APIで処理（Sprint 4既存実装）
        """
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

**成功基準**:
- Intent分類動作
- Claude Code / Claude API 振り分け成功
- エラーハンドリング動作

---

### Day 2 完了チェック

- [ ] Claude Code CLI実行ラッパー完成
- [ ] Intent Bridge統合完了
- [ ] E2E手動テスト成功（1件のIntent処理）

---

## 4. Day 3: テスト・モニタリング・ドキュメント

### 4.1 E2Eテスト実施

**テストケース**:

1. **コード実行Intent**

```bash
# DashboardからIntent作成
curl -X POST http://localhost:8000/api/intents \
  -H "Content-Type: application/json" \
  -d '{
    "description": "bridge/test_example.pyを作成して、簡単なユニットテストを書いて",
    "priority": "high"
  }'

# 処理結果確認
curl http://localhost:8000/api/intents/{intent_id}
```

**期待結果**:
- `intent_type: 'code_execution'` に分類
- Claude Codeセッション起動
- ファイル作成成功
- DBに結果保存

2. **チャットIntent**

```bash
curl -X POST http://localhost:8000/api/intents \
  -H "Content-Type: application/json" \
  -d '{
    "description": "PostgreSQLのパフォーマンスチューニング方法を教えて",
    "priority": "medium"
  }'
```

**期待結果**:
- `intent_type: 'chat'` に分類
- Claude API呼び出し
- テキスト応答取得

---

### 4.2 ログ・メトリクス設定

**作業場所**: `bridge/intent_bridge.py`

**手順**:

1. ログ追加

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# 各処理にログ追加
logger.info(f"Intent {intent_id} classified as {intent_type} (confidence: {confidence:.2f})")
logger.info(f"Claude Code session {session_id} started")
logger.info(f"Session {session_id} completed in {duration}s")
```

2. メトリクス（オプション）

```python
# Prometheus metrics（将来拡張）
from prometheus_client import Counter, Histogram

claude_code_sessions_total = Counter(
    'claude_code_sessions_total',
    'Total Claude Code sessions',
    ['status']
)

claude_code_duration_seconds = Histogram(
    'claude_code_duration_seconds',
    'Claude Code execution duration'
)
```

---

### 4.3 フロントエンド連携（オプション）

**作業場所**: `backend/api/claude_code.py`（新規）

**手順**:

1. API追加

```python
# backend/api/claude_code.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/claude_code", tags=["claude_code"])

@router.get("/sessions/{intent_id}")
async def get_sessions(intent_id: str):
    """Intent関連のClaude Codeセッション取得"""
    # TODO: DB query
    pass

@router.get("/sessions/{session_id}/executions")
async def get_executions(session_id: str):
    """セッション内の実行履歴取得"""
    # TODO: DB query
    pass
```

2. バックエンド登録

```python
# backend/main.py
from api import claude_code

app.include_router(claude_code.router)
```

---

### Day 3 完了チェック

- [ ] E2Eテスト2ケース以上成功
- [ ] ログ出力確認
- [ ] ドキュメント更新（README等）

---

## 5. 全体完了チェックリスト

### 必須項目
- [ ] DBテーブル2つ作成（sessions, executions）
- [ ] Intent分類ロジック実装
- [ ] Claude Code Client実装
- [ ] Intent Bridge統合
- [ ] エラーハンドリング実装
- [ ] E2Eテスト成功（code_execution, chat）

### 品質項目
- [ ] ログ設定完了
- [ ] セッション並列実行制限動作（max 3）
- [ ] タイムアウト処理動作
- [ ] セキュリティ確認（サンドボックス実行）

---

## 6. トラブルシューティング

### 問題1: Claude Code CLIが見つからない

**症状**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'claude-code'
```

**対処**:
```bash
# Claude Code CLIインストール確認
which claude-code

# インストールされていない場合
# https://docs.claude.com/claude-code からインストール
```

---

### 問題2: pexpect タイムアウト

**症状**:
```
pexpect.exceptions.TIMEOUT: Timeout exceeded
```

**対処**:
1. タイムアウト時間を延長（300秒 → 600秒）
2. Claude Code実行ログを確認
3. 手動でClaude Code CLIを実行してデバッグ

---

### 問題3: セッション数制限が効かない

**症状**: 3セッション以上同時実行されてしまう

**対処**:
```python
# _wait_for_slot() にログ追加
async def _wait_for_slot(self):
    while len(self.active_sessions) >= self.max_concurrent_sessions:
        print(f"⏳ Waiting... (active: {len(self.active_sessions)})")
        await asyncio.sleep(0.5)
```

---

## 7. 成功基準最終確認

Sprint 4.5が完了したと判断できる基準：

1. ✅ Intent自動分類動作（Claude API / Claude Code）
2. ✅ Claude Codeセッション実行成功
3. ✅ ファイル編集・コード生成タスク成功
4. ✅ タイムアウト・エラーハンドリング動作
5. ✅ セッション並列実行制限動作
6. ✅ 実行履歴の詳細記録
7. ✅ E2Eテスト2ケース以上成功

---

**作成日**: 2025-11-18
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**Sprint**: 4.5 作業開始指示書
**対象者**: 実装担当者（ツム / Cursor / ローカル開発者）
