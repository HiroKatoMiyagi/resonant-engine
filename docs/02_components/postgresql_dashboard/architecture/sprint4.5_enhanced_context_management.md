# Sprint 4.5 Enhanced: コンテキスト管理強化版

## 0. 問題提起

### 現在の設計の制限

Sprint 4.5の基本設計では、以下の制限があります：

```python
# 現在の設計
def __init__(self, workspace_path: str = "/tmp/resonant_workspace"):
    self.workspace_path = workspace_path
```

**問題点：**
- 各Claude Codeセッションが独立したワークスペース（`/tmp/resonant_workspace/{session_id}`）で実行
- resonant-engineメインリポジトリ（`/home/user/resonant-engine`）とは切り離されている
- **Sprint 3などの過去Sprint情報にアクセスできない**
- **一貫性のある開発ができない**

### ユーザーの期待

Sprint 4.5の作業中に：
- resonant-engine全体のコンテキストを持つ
- Sprint 1-4のドキュメント、コード、設計を参照できる
- 過去のSprintとの整合性を保ちながら開発できる
- Resonant Regulationsやプロジェクトメモリ（CLAUDE.md）を常に考慮できる

---

## 1. 改善アーキテクチャ

### 1.1 ワークスペース戦略の変更

```python
# 改善版
class ClaudeCodeClient:
    def __init__(
        self,
        workspace_mode: Literal['isolated', 'repository'] = 'repository',
        repository_path: str = "/home/user/resonant-engine",
        isolated_workspace_path: str = "/tmp/resonant_workspace"
    ):
        self.workspace_mode = workspace_mode
        self.repository_path = Path(repository_path)
        self.isolated_workspace_path = Path(isolated_workspace_path)
```

### 1.2 2つのモード

#### モードA: Repository Mode（推奨）

**特徴：**
- Claude Codeが `/home/user/resonant-engine` で直接実行
- 全ての過去Sprint情報にアクセス可能
- CLAUDE.md、Resonant Regulationsを自動考慮
- Git履歴、全ドキュメントが利用可能

**セキュリティ対策：**
- 自動的に新しいGit branchを作成（`claude/session-{session_id}`）
- 変更前に自動バックアップ
- 変更範囲の制限（特定ディレクトリのみ書き込み可能）

**使用ケース：**
- Sprint間の整合性が重要なタスク
- 過去の設計を参照する必要があるタスク
- リファクタリング、アーキテクチャ変更

#### モードB: Isolated Mode（高セキュリティ）

**特徴：**
- 独立したワークスペース（`/tmp/resonant_workspace/{session_id}`）
- 最小限のコンテキストのみロード
- サンドボックス実行

**使用ケース：**
- 実験的なコード生成
- 外部ライブラリのテスト
- セキュリティが最優先のタスク

---

## 2. コンテキスト自動ロード機能

### 2.1 設計思想

**Intent記述から関連コンテキストを自動検出し、Claude Codeセッションに含める**

例：
- Intent: "Sprint 4.5の実装を開始して"
- 自動ロード:
  - `docs/02_components/postgresql_dashboard/architecture/sprint4.5_*.md`
  - `docs/02_components/postgresql_dashboard/architecture/sprint4_*.md` (依存Sprint)
  - `docs/02_components/postgresql_dashboard/architecture/sprint1_*.md` (基盤)
  - `CLAUDE.md` (プロジェクトメモリ)
  - `docs/01_core_architecture/resonant_regulations.md`

### 2.2 実装

```python
# bridge/context_loader.py
from pathlib import Path
import re
from typing import List, Dict, Any

class ContextLoader:
    """
    Intent記述から関連コンテキストファイルを自動検出
    """

    def __init__(self, repository_path: str = "/home/user/resonant-engine"):
        self.repo = Path(repository_path)

    def load_context_for_intent(self, intent_description: str) -> Dict[str, Any]:
        """
        Intent記述から必要なコンテキストを抽出

        Returns:
            {
                'files': [Path, ...],
                'context_summary': str,
                'related_sprints': [int, ...]
            }
        """
        context = {
            'files': [],
            'context_summary': '',
            'related_sprints': []
        }

        # 1. Sprint番号抽出
        sprints = self._extract_sprint_numbers(intent_description)
        context['related_sprints'] = sprints

        # 2. 関連Sprintドキュメント収集
        for sprint_num in sprints:
            sprint_docs = self._find_sprint_documents(sprint_num)
            context['files'].extend(sprint_docs)

            # 依存Sprint（前提Sprint）も含める
            if sprint_num >= 2:
                # Sprint Nは通常Sprint 1を前提とする
                base_docs = self._find_sprint_documents(1)
                context['files'].extend(base_docs)

        # 3. 必須ドキュメント（常に含める）
        essential_files = [
            self.repo / "CLAUDE.md",  # プロジェクトメモリ
            self.repo / "docs/01_core_architecture/resonant_regulations.md",
            self.repo / "README.md"
        ]
        context['files'].extend([f for f in essential_files if f.exists()])

        # 4. キーワードベース検索
        keywords = self._extract_keywords(intent_description)
        for keyword in keywords:
            related_files = self._search_by_keyword(keyword)
            context['files'].extend(related_files)

        # 重複除去
        context['files'] = list(set(context['files']))

        # 5. コンテキストサマリー生成
        context['context_summary'] = self._generate_summary(context['files'])

        return context

    def _extract_sprint_numbers(self, description: str) -> List[int]:
        """Sprint番号を抽出（例: "Sprint 4.5" → [4, 5]）"""
        pattern = r'[Ss]print\s*(\d+(?:\.\d+)?)'
        matches = re.findall(pattern, description)

        sprint_numbers = []
        for match in matches:
            if '.' in match:
                # "4.5" → [4, 5]（4も含める、依存関係のため）
                base = int(match.split('.')[0])
                sub = int(match.split('.')[1])
                sprint_numbers.extend([base, sub])
            else:
                sprint_numbers.append(int(match))

        return sorted(set(sprint_numbers))

    def _find_sprint_documents(self, sprint_num: int) -> List[Path]:
        """Sprint関連ドキュメントを検索"""
        docs_dir = self.repo / "docs/02_components/postgresql_dashboard/architecture"

        if not docs_dir.exists():
            return []

        # sprint{N}_*.md または sprint{N}.{M}_*.md
        patterns = [
            f"sprint{sprint_num}_*.md",
            f"sprint{sprint_num}.*_*.md"
        ]

        files = []
        for pattern in patterns:
            files.extend(docs_dir.glob(pattern))

        return files

    def _extract_keywords(self, description: str) -> List[str]:
        """重要キーワード抽出"""
        # 技術キーワード
        tech_keywords = [
            'PostgreSQL', 'FastAPI', 'React', 'Docker', 'Claude',
            'Intent', 'Dashboard', 'API', 'Database', 'Frontend',
            'Backend', 'Bridge', 'Daemon', 'LISTEN', 'NOTIFY'
        ]

        found_keywords = []
        description_lower = description.lower()

        for keyword in tech_keywords:
            if keyword.lower() in description_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _search_by_keyword(self, keyword: str, max_files: int = 5) -> List[Path]:
        """キーワードでファイル検索（grep相当）"""
        # 簡易実装（実際はGrepツールやfull-text searchを使用）
        docs_dir = self.repo / "docs"
        if not docs_dir.exists():
            return []

        # マークダウンファイルからキーワード検索
        results = []
        for md_file in docs_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                if keyword.lower() in content.lower():
                    results.append(md_file)
                    if len(results) >= max_files:
                        break
            except:
                pass

        return results

    def _generate_summary(self, files: List[Path]) -> str:
        """コンテキストファイル一覧のサマリー"""
        summary_lines = [
            "以下のコンテキストファイルがClaude Codeセッションに含まれます：",
            ""
        ]

        # カテゴリ別に整理
        categories = {
            'プロジェクトメモリ': [],
            'Sprint仕様書': [],
            'アーキテクチャ': [],
            'その他': []
        }

        for file in files:
            if 'CLAUDE.md' in file.name:
                categories['プロジェクトメモリ'].append(file)
            elif 'sprint' in file.name:
                categories['Sprint仕様書'].append(file)
            elif 'architecture' in str(file):
                categories['アーキテクチャ'].append(file)
            else:
                categories['その他'].append(file)

        for category, category_files in categories.items():
            if category_files:
                summary_lines.append(f"### {category}")
                for f in category_files:
                    summary_lines.append(f"- {f.relative_to(self.repo)}")
                summary_lines.append("")

        return "\n".join(summary_lines)
```

---

## 3. Repository Mode詳細設計

### 3.1 実行フロー

```python
# bridge/claude_code_client.py (改善版)
async def execute_task_repository_mode(
    self,
    task_description: str,
    context: Optional[Dict[str, Any]] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Repository Modeでタスク実行
    """
    session_id = str(uuid.uuid4())

    # 1. コンテキスト自動ロード
    context_loader = ContextLoader(str(self.repository_path))
    auto_context = context_loader.load_context_for_intent(task_description)

    print(f"📚 コンテキストロード完了:")
    print(auto_context['context_summary'])

    # 2. Git branch作成（安全性確保）
    branch_name = f"claude/session-{session_id[:8]}"
    await self._create_git_branch(branch_name)

    # 3. 変更前バックアップ
    backup_path = await self._create_backup()

    # 4. Claude Code実行（repository直接）
    try:
        result = await self._run_claude_code_in_repository(
            session_id=session_id,
            task=task_description,
            context_files=auto_context['files'],
            branch=branch_name,
            timeout=timeout
        )

        # 5. 変更をコミット（オプション）
        if result['success'] and result['file_changes']:
            await self._auto_commit_changes(
                branch=branch_name,
                session_id=session_id,
                changes=result['file_changes']
            )

        return result

    except Exception as e:
        # エラー時はバックアップから復元
        await self._restore_backup(backup_path)
        raise

async def _create_git_branch(self, branch_name: str):
    """安全のため新しいGit branchを作成"""
    process = await asyncio.create_subprocess_exec(
        'git', 'checkout', '-b', branch_name,
        cwd=str(self.repository_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

async def _run_claude_code_in_repository(
    self,
    session_id: str,
    task: str,
    context_files: List[Path],
    branch: str,
    timeout: int
) -> Dict[str, Any]:
    """
    Repository内でClaude Code実行

    重要：Claude Codeにコンテキストファイル情報を渡す
    """

    # コンテキストプロンプト生成
    context_prompt = self._build_context_prompt(task, context_files)

    # Claude Code実行（repositoryをワークスペースとして使用）
    process = await asyncio.create_subprocess_exec(
        'claude-code',
        '--workspace', str(self.repository_path),
        '--prompt', context_prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        # 結果パース
        changes = await self._detect_git_changes()

        return {
            'session_id': session_id,
            'success': process.returncode == 0,
            'output': stdout.decode(),
            'file_changes': changes,
            'branch': branch,
            'context_files_used': [str(f) for f in context_files],
            'error': stderr.decode() if stderr else None
        }

    except asyncio.TimeoutError:
        process.kill()
        raise

def _build_context_prompt(self, task: str, context_files: List[Path]) -> str:
    """
    Claude Codeに渡すコンテキスト付きプロンプト生成
    """
    prompt_parts = [
        "# タスク",
        task,
        "",
        "# 利用可能なコンテキストファイル",
        "以下のファイルを参照して、一貫性のある実装を行ってください：",
        ""
    ]

    for file in context_files:
        prompt_parts.append(f"- {file}")

    prompt_parts.extend([
        "",
        "# 特に重要",
        "- CLAUDE.mdのプロジェクトメモリを必ず考慮してください",
        "- Resonant Regulationsに従ってください",
        "- 過去のSprint実装との整合性を保ってください",
        ""
    ])

    return "\n".join(prompt_parts)

async def _detect_git_changes(self) -> List[Dict[str, str]]:
    """Git diffで変更検出"""
    process = await asyncio.create_subprocess_exec(
        'git', 'status', '--porcelain',
        cwd=str(self.repository_path),
        stdout=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()

    changes = []
    for line in stdout.decode().splitlines():
        if line.strip():
            status = line[:2].strip()
            file_path = line[3:]
            changes.append({
                'status': status,  # 'M', 'A', 'D' etc.
                'file': file_path
            })

    return changes
```

---

## 4. 使用例：Sprint 4.5実装時の動作

### 4.1 シナリオ

**Intent**: "Sprint 4.5のClaude Code Client実装を開始して。Sprint 4のIntent Bridgeと整合性を保つこと"

### 4.2 実行フロー

```
1. Intent分類
   → 'code_execution' 判定

2. コンテキスト自動ロード
   検出されたSprint: [4, 5]

   ロードされるファイル:
   - docs/02_components/postgresql_dashboard/architecture/sprint4.5_claude_code_integration_spec.md
   - docs/02_components/postgresql_dashboard/architecture/sprint4.5_work_instruction.md
   - docs/02_components/postgresql_dashboard/architecture/sprint4_intent_processing_spec.md
   - docs/02_components/postgresql_dashboard/architecture/sprint1_environment_setup_spec.md
   - CLAUDE.md
   - docs/01_core_architecture/resonant_regulations.md

3. Git branch作成
   → claude/session-a1b2c3d4

4. Claude Code実行
   ワークスペース: /home/user/resonant-engine

   Claude Codeに渡されるコンテキスト:
   - Sprint 4.5の仕様書（何を実装するか）
   - Sprint 4の仕様書（Intent Bridgeの既存実装を参照）
   - Sprint 1の環境設定（PostgreSQL接続情報等）
   - CLAUDE.md（プロジェクトメモリ、Resonant Regulations）

5. 実装
   Claude Codeが以下を参照しながら実装:
   - Sprint 4のintent_bridge.pyの構造を確認
   - 既存のDB接続方法を参照
   - Resonant Regulationsに従った命名規則
   - プロジェクトメモリ（ユーザーの認知特性）を考慮

6. ファイル変更
   - bridge/claude_code_client.py（新規作成）
   - bridge/intent_bridge.py（更新）
   - bridge/intent_classifier.py（新規作成）

7. 自動コミット
   Branch: claude/session-a1b2c3d4
   Commit: "Implement Claude Code Client for Sprint 4.5"
```

### 4.3 重要な点

**Claude Codeは以下を自動的に考慮できる：**

✅ Sprint 4の`intent_bridge.py`の実装パターン
✅ Sprint 1で設定したPostgreSQL接続方法
✅ CLAUDE.mdに記載された認知特性（ASD構造）
✅ Resonant Regulationsの命名規則
✅ 過去のCommitメッセージスタイル
✅ 既存のディレクトリ構造

**つまり、Sprint 4.5の作業中に、Sprint 1-4の全情報が利用可能**

---

## 5. セキュリティとリスク管理

### 5.1 Git Branch戦略

```python
# 各セッションで新しいbranchを自動作成
branch_name = f"claude/session-{session_id[:8]}"

# メリット:
# - メインブランチを保護
# - 変更をレビュー可能
# - 問題があればbranchを削除するだけ
```

### 5.2 変更範囲制限（オプション）

```python
# 特定ディレクトリのみ書き込み許可
ALLOWED_WRITE_PATHS = [
    'bridge/',
    'backend/',
    'frontend/',
    'docs/02_components/',
    'docker/'
]

READONLY_PATHS = [
    'CLAUDE.md',  # プロジェクトメモリは読み取り専用
    'docs/01_core_architecture/',  # コアアーキテクチャは保護
    '.git/'
]

async def _validate_file_changes(self, changes: List[Dict]) -> bool:
    """変更がポリシーに準拠しているか検証"""
    for change in changes:
        file_path = change['file']

        # 読み取り専用パスチェック
        if any(file_path.startswith(ro) for ro in READONLY_PATHS):
            raise SecurityError(f"読み取り専用ファイルへの変更: {file_path}")

        # 書き込み許可パスチェック
        if not any(file_path.startswith(allowed) for allowed in ALLOWED_WRITE_PATHS):
            raise SecurityError(f"許可されていないパスへの変更: {file_path}")

    return True
```

### 5.3 バックアップとロールバック

```python
async def _create_backup(self) -> Path:
    """変更前の状態をバックアップ"""
    backup_dir = Path("/var/backups/resonant_engine")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_{timestamp}.tar.gz"

    # リポジトリをアーカイブ
    await asyncio.create_subprocess_exec(
        'tar', 'czf', str(backup_path),
        '-C', str(self.repository_path.parent),
        self.repository_path.name
    )

    return backup_path

async def _restore_backup(self, backup_path: Path):
    """バックアップから復元"""
    # エラー時のロールバック処理
    pass
```

---

## 6. 設定ファイル

### 6.1 config/claude_code_config.yaml

```yaml
claude_code:
  # ワークスペースモード: 'repository' または 'isolated'
  workspace_mode: repository

  # Repositoryパス
  repository_path: /home/user/resonant-engine

  # Isolated modeのワークスペース
  isolated_workspace_path: /tmp/resonant_workspace

  # セキュリティ設定
  security:
    auto_create_branch: true
    branch_prefix: "claude/session-"

    allowed_write_paths:
      - bridge/
      - backend/
      - frontend/
      - docs/02_components/
      - docker/

    readonly_paths:
      - CLAUDE.md
      - docs/01_core_architecture/
      - .git/

    auto_backup: true
    backup_dir: /var/backups/resonant_engine

  # コンテキストローディング
  context_loading:
    enabled: true

    # 常に含めるファイル
    essential_files:
      - CLAUDE.md
      - README.md
      - docs/01_core_architecture/resonant_regulations.md

    # Sprint検出時の動作
    auto_load_dependencies: true  # Sprint 4.5 → Sprint 1-4も読む

    # 最大コンテキストファイル数
    max_context_files: 20

  # 実行制御
  execution:
    max_concurrent_sessions: 3
    default_timeout_seconds: 300
    max_timeout_seconds: 900
```

---

## 7. Intent Bridgeへの統合

### 7.1 intent_bridge.py更新

```python
async def _process_with_claude_code(self, conn, intent) -> Dict:
    """
    Claude Codeで処理（Repository Mode使用）
    """

    # Repository Modeで実行
    result = await self.claude_code.execute_task_repository_mode(
        task_description=intent['description'],
        timeout=300
    )

    # コンテキストファイル情報もDB保存
    await conn.execute("""
        UPDATE claude_code_sessions
        SET metadata = $1
        WHERE session_id = $2
    """,
        json.dumps({
            'context_files': result['context_files_used'],
            'branch': result['branch']
        }),
        result['session_id']
    )

    return result
```

---

## 8. 成功基準

### 8.1 機能要件

- [ ] Repository Modeで実行可能
- [ ] Intent記述からSprint番号を自動抽出
- [ ] 関連Sprint全てのドキュメントを自動ロード
- [ ] CLAUDE.md等の必須ファイルを常に含める
- [ ] 自動Git branch作成
- [ ] 変更前バックアップ作成
- [ ] 変更範囲検証（セキュリティ）

### 8.2 テストケース

**テスト1: Sprint 4.5実装**
```
Intent: "Sprint 4.5のClaude Code Client実装を開始"
期待:
- Sprint 4.5, 4, 1のドキュメントをロード
- CLAUDE.mdを含める
- Sprint 4のintent_bridge.pyを参照可能
```

**テスト2: 横断的リファクタリング**
```
Intent: "bridge/とbackend/のエラーハンドリングを統一してリファクタリング"
期待:
- bridge/, backend/の既存コード全てにアクセス可能
- 両方のディレクトリを変更可能
- 整合性のある実装
```

---

## 9. まとめ

### 現在の設計 vs 改善版

| 項目 | 現在の設計 | 改善版（Repository Mode） |
|------|-----------|------------------------|
| ワークスペース | `/tmp/resonant_workspace/{session_id}` | `/home/user/resonant-engine` |
| 過去Sprint参照 | ❌ 不可能 | ✅ 可能 |
| CLAUDE.md参照 | ❌ 不可能 | ✅ 自動ロード |
| コンテキスト | 手動指定のみ | ✅ 自動検出 |
| 整合性 | ❌ 保証なし | ✅ 過去実装参照可能 |
| セキュリティ | ✅ サンドボックス | ⚠️ Branch+バックアップで対応 |

### 推奨設定

**本番環境（resonant-engine開発）:**
- `workspace_mode: repository`
- コンテキスト自動ロード有効
- Git branch自動作成
- バックアップ有効

**実験環境:**
- `workspace_mode: isolated`
- 最小コンテキスト

---

**作成日**: 2025-11-18
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**目的**: Sprint 4.5のコンテキスト管理強化
**ユーザーフィードバック対応**: 過去Sprint情報へのアクセス要件
