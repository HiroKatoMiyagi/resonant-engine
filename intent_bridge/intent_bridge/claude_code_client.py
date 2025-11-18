"""
Claude Code Client - Claude Code CLI統合

Claude Code CLIをプログラマティックに呼び出すクライアント
"""
import asyncio
import json
import uuid
import os
import shutil
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClaudeCodeClient:
    """
    Claude Code CLIをプログラマティックに呼び出すクライアント

    Note: Claude Code CLIが利用できない場合はモックモードで動作
    """

    def __init__(self, workspace_path: str = "/tmp/resonant_workspace"):
        self.workspace_path = workspace_path
        self.active_sessions = {}
        self.max_concurrent_sessions = 3

        # Claude Code CLI の存在確認
        self.claude_code_available = shutil.which('claude-code') is not None
        if not self.claude_code_available:
            logger.warning("⚠️  Claude Code CLI not found - using mock mode")

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
            logger.info(f"⏳ Waiting for session slot (current: {len(self.active_sessions)})")
            await asyncio.sleep(1)

        self.active_sessions[session_id] = {
            'started_at': datetime.now(),
            'status': 'running',
            'task': task_description
        }

        try:
            if self.claude_code_available:
                result = await self._run_claude_code_session(
                    session_id=session_id,
                    task=task_description,
                    context=context,
                    timeout=timeout
                )
            else:
                # モックモード
                result = await self._run_mock_session(
                    session_id=session_id,
                    task=task_description,
                    context=context
                )

            self.active_sessions[session_id]['status'] = 'completed'
            return result

        except asyncio.TimeoutError:
            self.active_sessions[session_id]['status'] = 'timeout'
            raise
        except Exception as e:
            self.active_sessions[session_id]['status'] = 'failed'
            logger.error(f"❌ Session {session_id} failed: {e}")
            raise
        finally:
            # セッションクリーンアップ（5秒後）
            await asyncio.sleep(5)
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

    async def _run_claude_code_session(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Claude Code CLIセッションを実行（本物）
        """
        # 1. ワークスペース準備
        workspace = f"{self.workspace_path}/{session_id}"
        await self._prepare_workspace(workspace, context)

        # 2. プロンプトファイル作成
        prompt_file = f"{workspace}/.claude_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(task)

        # 3. Claude Code実行（非対話モード想定）
        try:
            process = await asyncio.create_subprocess_exec(
                'claude-code',
                '--workspace', workspace,
                '--non-interactive',  # 実際のCLIにこのオプションがあるかは不明
                '--prompt-file', prompt_file,
                '--output-format', 'json',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            # 4. 結果パース
            result = json.loads(stdout.decode()) if stdout else {}

            # 5. ファイル変更検出
            changes = await self._detect_file_changes(workspace)

            return {
                'session_id': session_id,
                'success': result.get('success', True),
                'output': result.get('output', stdout.decode() if stdout else ''),
                'file_changes': changes,
                'executions': result.get('tool_calls', []),
                'error': stderr.decode() if stderr else None,
                'mode': 'real'
            }

        except asyncio.TimeoutError:
            if 'process' in locals():
                process.kill()
            raise
        finally:
            # ワークスペースクリーンアップ
            await self._cleanup_workspace(workspace)

    async def _run_mock_session(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        モックモード実行（Claude Code CLIがない場合）
        """
        logger.info(f"🎭 Running mock session for: {task[:50]}...")

        # 模擬実行（1-3秒）
        await asyncio.sleep(2)

        # タスクの種類に応じたモック応答
        mock_output = self._generate_mock_output(task)

        return {
            'session_id': session_id,
            'success': True,
            'output': mock_output,
            'file_changes': [],
            'executions': [
                {
                    'tool': 'Analysis',
                    'success': True,
                    'description': 'タスク分析完了'
                },
                {
                    'tool': 'Mock',
                    'success': True,
                    'description': 'モック実行完了'
                }
            ],
            'error': None,
            'mode': 'mock'
        }

    def _generate_mock_output(self, task: str) -> str:
        """モックモード用の出力生成"""
        task_lower = task.lower()

        if 'test' in task_lower or 'テスト' in task:
            return """[Mock] テスト実行シミュレーション

✅ 単体テスト: 15件 PASS
✅ 統合テスト: 8件 PASS
⏭️  E2Eテスト: スキップ

カバレッジ: 82%

本物のClaude Code CLIを使用すると、実際のテストが実行されます。"""

        elif 'ファイル' in task or 'file' in task_lower:
            return """[Mock] ファイル操作シミュレーション

✅ ファイル読み込み完了
✅ 分析完了
✅ 変更案生成完了

本物のClaude Code CLIを使用すると、実際のファイル編集が行われます。"""

        elif 'git' in task_lower or 'commit' in task_lower:
            return """[Mock] Git操作シミュレーション

✅ 変更検出完了
✅ コミットメッセージ生成完了
⏭️  実際のコミット: スキップ（モックモード）

本物のClaude Code CLIを使用すると、実際のGit操作が実行されます。"""

        else:
            return f"""[Mock] タスク実行シミュレーション

タスク: {task[:100]}

✅ タスク分析完了
✅ 実行計画作成完了
⏭️  実際の実行: スキップ（モックモード）

本物のClaude Code CLIを使用すると、実際のコード実行が行われます。
Claude Code CLIインストール: https://docs.anthropic.com/claude-code"""

    async def _prepare_workspace(
        self,
        workspace: str,
        context: Optional[Dict[str, Any]]
    ):
        """ワークスペース準備"""
        os.makedirs(workspace, exist_ok=True)

        # コンテキストファイルをワークスペースにコピー
        if context and 'files' in context:
            for file_path in context['files']:
                if os.path.exists(file_path):
                    dest = os.path.join(workspace, os.path.basename(file_path))
                    shutil.copy2(file_path, dest)

    async def _detect_file_changes(self, workspace: str) -> list:
        """ファイル変更検出（git diff等）"""
        changes = []
        # 実際の実装では、git diffやファイルタイムスタンプ比較を行う
        return changes

    async def _cleanup_workspace(self, workspace: str):
        """ワークスペースクリーンアップ"""
        try:
            if os.path.exists(workspace):
                shutil.rmtree(workspace)
        except Exception as e:
            logger.warning(f"⚠️  Workspace cleanup failed: {e}")

    def get_active_sessions(self) -> Dict[str, Any]:
        """アクティブなセッション情報を返す"""
        return {
            'count': len(self.active_sessions),
            'max': self.max_concurrent_sessions,
            'sessions': [
                {
                    'session_id': sid,
                    'status': info['status'],
                    'task': info['task'][:50] + '...' if len(info['task']) > 50 else info['task'],
                    'duration': (datetime.now() - info['started_at']).total_seconds()
                }
                for sid, info in self.active_sessions.items()
            ]
        }
