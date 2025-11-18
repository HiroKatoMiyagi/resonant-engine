"""
Sprint 4.5: Claude Code Client
Claude Code APIをプログラマティックに呼び出すクライアント
Repository Mode + Context Auto-loading対応
"""
import asyncio
import json
import uuid
import os
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pathlib import Path


class ClaudeCodeClient:
    """
    Claude Code CLIをプログラマティックに呼び出すクライアント

    Modes:
    - repository: メインリポジトリで直接実行（過去Sprint情報アクセス可能）
    - isolated: 独立ワークスペースで実行（サンドボックス）
    """

    def __init__(
        self,
        workspace_mode: Literal['repository', 'isolated'] = 'repository',
        repository_path: str = "/home/user/resonant-engine",
        isolated_workspace_path: str = "/tmp/resonant_workspace",
        max_concurrent_sessions: int = 3,
        default_timeout: int = 300
    ):
        self.workspace_mode = workspace_mode
        self.repository_path = Path(repository_path)
        self.isolated_workspace_path = Path(isolated_workspace_path)
        self.max_concurrent_sessions = max_concurrent_sessions
        self.default_timeout = default_timeout

        # アクティブセッション管理
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # ワークスペース準備
        if workspace_mode == 'isolated':
            self.isolated_workspace_path.mkdir(parents=True, exist_ok=True)

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
            context: コンテキスト情報（files, related_sprints, db_memories等）
            timeout: タイムアウト秒数（Noneの場合はdefault_timeout使用）

        Returns:
            {
                'session_id': str,
                'success': bool,
                'output': str,
                'file_changes': list,
                'executions': list,
                'context_files_used': list,
                'branch': str (repository modeの場合),
                'error': Optional[str]
            }
        """
        session_id = str(uuid.uuid4())
        timeout = timeout or self.default_timeout
        context = context or {}

        # セッション数制限チェック
        await self._wait_for_slot()

        self.active_sessions[session_id] = {
            'started_at': datetime.now(),
            'status': 'running',
            'task': task_description
        }

        try:
            if self.workspace_mode == 'repository':
                result = await self._execute_repository_mode(
                    session_id=session_id,
                    task=task_description,
                    context=context,
                    timeout=timeout
                )
            else:
                result = await self._execute_isolated_mode(
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
            asyncio.create_task(self._cleanup_session(session_id, delay=5))

    async def _execute_repository_mode(
        self,
        session_id: str,
        task: str,
        context: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Repository Modeでタスク実行
        メインリポジトリで直接実行し、全記憶にアクセス可能
        """
        # 1. Git branch作成（安全性確保）
        branch_name = f"claude/session-{session_id[:8]}"
        await self._create_git_branch(branch_name)

        # 2. 拡張プロンプト生成
        prompt = self._build_context_prompt(task, context, branch_name)

        print(f"📚 Repository Mode実行:")
        print(f"  - Session ID: {session_id[:8]}")
        print(f"  - Branch: {branch_name}")
        if 'files' in context:
            print(f"  - Context Files: {len(context['files'])}個")
        if 'related_sprints' in context:
            print(f"  - Related Sprints: {context['related_sprints']}")

        # 3. Claude Code実行（モック実装 - 実際のClaude Code API統合時に置き換え）
        result = await self._run_claude_code_mock(
            session_id=session_id,
            workspace=str(self.repository_path),
            prompt=prompt,
            branch=branch_name,
            timeout=timeout
        )

        # 4. 結果にメタデータ追加
        result['branch'] = branch_name
        result['context_files_used'] = [
            str(f) for f in context.get('files', [])
        ]
        result['workspace_mode'] = 'repository'

        return result

    async def _execute_isolated_mode(
        self,
        session_id: str,
        task: str,
        context: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Isolated Modeでタスク実行
        独立ワークスペースでサンドボックス実行
        """
        # ワークスペース作成
        workspace = self.isolated_workspace_path / session_id
        workspace.mkdir(parents=True, exist_ok=True)

        # プロンプト生成
        prompt = self._build_context_prompt(task, context)

        print(f"🔒 Isolated Mode実行:")
        print(f"  - Session ID: {session_id[:8]}")
        print(f"  - Workspace: {workspace}")

        # Claude Code実行（モック）
        result = await self._run_claude_code_mock(
            session_id=session_id,
            workspace=str(workspace),
            prompt=prompt,
            timeout=timeout
        )

        result['workspace_mode'] = 'isolated'
        result['workspace_path'] = str(workspace)

        return result

    async def _run_claude_code_mock(
        self,
        session_id: str,
        workspace: str,
        prompt: str,
        branch: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Claude Code実行（モック実装）

        NOTE: 実際のClaude Code API統合時に置き換える
        現在はテスト用のモック実装
        """
        # モック: 2秒待機してダミー結果を返す
        await asyncio.sleep(2)

        return {
            'session_id': session_id,
            'success': True,
            'output': f"Mock: Task '{prompt[:50]}...' executed successfully",
            'file_changes': [],
            'executions': [
                {
                    'tool': 'Read',
                    'input': {'file': 'CLAUDE.md'},
                    'output': {'content': '...(省略)...'},
                    'success': True
                }
            ],
            'error': None
        }

    def _build_context_prompt(
        self,
        task: str,
        context: Dict[str, Any],
        branch: Optional[str] = None
    ) -> str:
        """
        コンテキスト付きプロンプト生成
        """
        prompt_parts = [
            "# タスク",
            task,
            "",
            "---",
            ""
        ]

        # コンテキストファイル
        if context.get('files'):
            prompt_parts.extend([
                "# 利用可能なコンテキスト",
                "",
                "## ファイルベースメモリ",
                "",
                "以下のファイルを参照してください：",
                ""
            ])

            for file in context['files'][:15]:  # 最大15ファイル
                prompt_parts.append(f"- {file}")

            prompt_parts.append("")

        # DB記憶
        if context.get('db_memories'):
            prompt_parts.extend([
                "## PostgreSQL記憶（過去のIntent処理結果）",
                "",
                "類似タスクの過去実行結果：",
                ""
            ])

            for memory in context['db_memories'][:3]:  # 最大3件
                prompt_parts.extend([
                    f"### Intent: {memory.get('description', 'N/A')}",
                    f"- ステータス: {memory.get('status', 'N/A')}",
                    f"- 結果:",
                    "```json",
                    json.dumps(memory.get('result', {}), indent=2, ensure_ascii=False),
                    "```",
                    ""
                ])

        # 重要な指針
        prompt_parts.extend([
            "## 重要な指針",
            "",
            "- **CLAUDE.md（プロジェクトメモリ）を必ず考慮してください**",
            "  - ユーザーの認知特性（ASD構造）を理解する",
            "  - Resonant Regulationsに従う",
            "  - 呼吸優先原則を守る",
            "",
            "- **過去のSprint実装との整合性を保つ**",
        ])

        if context.get('related_sprints'):
            prompt_parts.append(f"  - 関連Sprint: {', '.join(map(str, context['related_sprints']))}")

        prompt_parts.extend([
            "",
            "---",
            ""
        ])

        if branch:
            prompt_parts.extend([
                f"# 実行環境",
                f"- Git branch: {branch}",
                f"- Workspace: {self.repository_path}",
                "",
            ])

        return "\n".join(prompt_parts)

    async def _create_git_branch(self, branch_name: str) -> bool:
        """Git branchを作成"""
        try:
            process = await asyncio.create_subprocess_exec(
                'git', 'checkout', '-b', branch_name,
                cwd=str(self.repository_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                print(f"✅ Git branch作成: {branch_name}")
                return True
            else:
                # ブランチが既に存在する場合は切り替え
                process2 = await asyncio.create_subprocess_exec(
                    'git', 'checkout', branch_name,
                    cwd=str(self.repository_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process2.communicate()
                print(f"✅ Git branch切り替え: {branch_name}")
                return True

        except Exception as e:
            print(f"⚠️  Git branch作成失敗: {e}")
            return False

    async def _wait_for_slot(self):
        """セッション数制限待機"""
        while len(self.active_sessions) >= self.max_concurrent_sessions:
            print(f"⏳ セッション数上限待機中... (active: {len(self.active_sessions)})")
            await asyncio.sleep(0.5)

    async def _cleanup_session(self, session_id: str, delay: int = 5):
        """セッションクリーンアップ"""
        await asyncio.sleep(delay)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """現在実行中のセッション一覧"""
        return [
            {
                'session_id': sid,
                'status': info['status'],
                'started_at': info['started_at'].isoformat(),
                'task': info.get('task', '')[:50]
            }
            for sid, info in self.active_sessions.items()
        ]


# テストコード
if __name__ == '__main__':
    import asyncio
    from context_loader import ContextLoader

    async def test_claude_code_client():
        print("Claude Code Clientテスト")
        print("=" * 70)

        # Repository Modeテスト
        client = ClaudeCodeClient(workspace_mode='repository')
        loader = ContextLoader()

        # コンテキストロード
        intent = "Sprint 4.5のClaude Code Client実装テスト"
        context = loader.load_context_for_intent(intent, max_files=5)

        print(f"\nIntent: {intent}")
        print("-" * 70)

        # タスク実行
        result = await client.execute_task(
            task_description=intent,
            context=context,
            timeout=10
        )

        print("\n実行結果:")
        print(f"  - Success: {result['success']}")
        print(f"  - Session ID: {result['session_id'][:8]}")
        print(f"  - Branch: {result.get('branch', 'N/A')}")
        print(f"  - Output: {result['output'][:100]}...")
        print(f"  - Context Files: {len(result.get('context_files_used', []))}個")

        print("\n" + "=" * 70)
        print("テスト完了")

    asyncio.run(test_claude_code_client())
