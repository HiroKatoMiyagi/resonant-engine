"""
Sprint 4.5 Enhanced: コンテキスト自動ロード機能
Intent記述から関連コンテキストファイルを自動検出
"""
from pathlib import Path
import re
from typing import List, Dict, Any, Optional


class ContextLoader:
    """
    Intent記述から関連コンテキストファイルを自動検出
    resonant-engineの3層メモリ構造にアクセス
    """

    def __init__(self, repository_path: str = "/home/user/resonant-engine"):
        self.repo = Path(repository_path)

    def load_context_for_intent(
        self,
        intent_description: str,
        max_files: int = 20
    ) -> Dict[str, Any]:
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
            # Sprint Nは通常Sprint 1を前提とする
            if sprint_num >= 2:
                base_docs = self._find_sprint_documents(1)
                context['files'].extend(base_docs)

        # 3. 必須ドキュメント（常に含める）
        essential_files = [
            self.repo / "CLAUDE.md",  # プロジェクトメモリ
            self.repo / "README.md"
        ]

        # Resonant Regulationsを探す
        resonant_regs = self.repo / "docs/01_core_architecture/resonant_regulations.md"
        if resonant_regs.exists():
            essential_files.append(resonant_regs)

        context['files'].extend([f for f in essential_files if f.exists()])

        # 4. キーワードベース検索
        keywords = self._extract_keywords(intent_description)
        for keyword in keywords[:5]:  # 上位5キーワード
            related_files = self._search_by_keyword(keyword, max_files=3)
            context['files'].extend(related_files)

        # 5. ファイルパス直接指定を検出
        file_paths = self._extract_file_paths(intent_description)
        for file_path in file_paths:
            full_path = self.repo / file_path
            if full_path.exists():
                context['files'].append(full_path)

        # 重複除去
        context['files'] = list(set(context['files']))[:max_files]

        # 6. コンテキストサマリー生成
        context['context_summary'] = self._generate_summary(context['files'])

        return context

    def _extract_sprint_numbers(self, description: str) -> List[int]:
        """
        Sprint番号を抽出（例: "Sprint 4.5" → [4, 5]）
        """
        pattern = r'[Ss]print\s*(\d+(?:\.\d+)?)'
        matches = re.findall(pattern, description)

        sprint_numbers = []
        for match in matches:
            if '.' in match:
                # "4.5" → [4, 5]（4も含める、依存関係のため）
                parts = match.split('.')
                base = int(parts[0])
                sub = int(parts[1])
                sprint_numbers.extend([base, sub])
            else:
                sprint_numbers.append(int(match))

        return sorted(set(sprint_numbers))

    def _find_sprint_documents(self, sprint_num: int) -> List[Path]:
        """
        Sprint関連ドキュメントを検索
        """
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
        """
        重要キーワード抽出
        """
        # 技術キーワード
        tech_keywords = [
            'PostgreSQL', 'FastAPI', 'React', 'Docker', 'Claude',
            'Intent', 'Dashboard', 'API', 'Database', 'Frontend',
            'Backend', 'Bridge', 'Daemon', 'LISTEN', 'NOTIFY',
            'Context', 'Memory', 'Session', 'Execution'
        ]

        found_keywords = []
        description_lower = description.lower()

        for keyword in tech_keywords:
            if keyword.lower() in description_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _extract_file_paths(self, description: str) -> List[str]:
        """
        Intent記述から直接ファイルパスを抽出
        例: "bridge/intent_bridge.py" → ["bridge/intent_bridge.py"]
        """
        # パターン: ディレクトリ/ファイル名.拡張子
        pattern = r'([\w/]+\.[\w]+)'
        matches = re.findall(pattern, description)

        # .pyなど明らかなファイル拡張子のみ
        file_extensions = {'.py', '.js', '.ts', '.tsx', '.md', '.sql', '.yaml', '.yml', '.json'}

        valid_paths = []
        for match in matches:
            if any(match.endswith(ext) for ext in file_extensions):
                valid_paths.append(match)

        return valid_paths

    def _search_by_keyword(self, keyword: str, max_files: int = 5) -> List[Path]:
        """
        キーワードでファイル検索
        """
        docs_dir = self.repo / "docs"
        if not docs_dir.exists():
            return []

        # マークダウンファイルからキーワード検索
        results = []
        for md_file in docs_dir.rglob("*.md"):
            if len(results) >= max_files:
                break

            try:
                content = md_file.read_text(encoding='utf-8')
                if keyword.lower() in content.lower():
                    results.append(md_file)
            except Exception:
                pass

        return results

    def _generate_summary(self, files: List[Path]) -> str:
        """
        コンテキストファイル一覧のサマリー
        """
        if not files:
            return "コンテキストファイル: なし"

        summary_lines = [
            f"コンテキストファイル: {len(files)}個",
            ""
        ]

        # カテゴリ別に整理
        categories = {
            'プロジェクトメモリ': [],
            'Sprint仕様書': [],
            'アーキテクチャ': [],
            '実装コード': [],
            'その他': []
        }

        for file in files:
            if 'CLAUDE.md' in file.name:
                categories['プロジェクトメモリ'].append(file)
            elif 'sprint' in file.name.lower():
                categories['Sprint仕様書'].append(file)
            elif 'architecture' in str(file):
                categories['アーキテクチャ'].append(file)
            elif file.suffix in {'.py', '.js', '.ts', '.tsx'}:
                categories['実装コード'].append(file)
            else:
                categories['その他'].append(file)

        for category, category_files in categories.items():
            if category_files:
                summary_lines.append(f"{category}: {len(category_files)}個")
                for f in category_files[:3]:  # 各カテゴリ最大3ファイル表示
                    try:
                        rel_path = f.relative_to(self.repo)
                        summary_lines.append(f"  - {rel_path}")
                    except ValueError:
                        summary_lines.append(f"  - {f.name}")

        return "\n".join(summary_lines)


# テストコード
if __name__ == '__main__':
    loader = ContextLoader()

    # テストケース
    test_descriptions = [
        "Sprint 4.5のClaude Code Client実装を開始して。Sprint 4も参考に",
        "bridge/intent_bridge.pyを編集してエラーハンドリングを追加",
        "PostgreSQLのパフォーマンスについて教えて"
    ]

    print("コンテキストローダーテスト:")
    print("=" * 70)

    for desc in test_descriptions:
        print(f"\nIntent: {desc}")
        print("-" * 70)

        context = loader.load_context_for_intent(desc, max_files=10)

        print(f"関連Sprint: {context['related_sprints']}")
        print(f"ファイル数: {len(context['files'])}")
        print()
        print(context['context_summary'])
        print()

    print("=" * 70)
    print("テスト完了")
