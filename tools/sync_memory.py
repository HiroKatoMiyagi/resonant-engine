#!/usr/bin/env python3
"""
Memory Synchronization Tool
CLAUDE.md ↔ Claude.ai Chat Memory の双方向同期

Usage:
    # CLAUDE.md → チャットメモリ
    python tools/sync_memory.py export
    
    # チャットメモリ → CLAUDE.md
    python tools/sync_memory.py import
"""

import re
import sys
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent
CLAUDE_MD_PATH = PROJECT_ROOT / "CLAUDE.md"
SESSION_MEMORY_PATH = PROJECT_ROOT / ".sessions" / "memory"

class MemorySyncTool:
    """CLAUDE.mdとチャットメモリの同期ツール"""
    
    MAX_EDIT_LENGTH = 200  # memory_user_editsの1行あたりの制限
    
    def export_to_chat(self) -> List[str]:
        """
        CLAUDE.md → チャットメモリ用の編集コマンドを生成
        
        Returns:
            List[str]: memory_user_editsで実行すべきコマンドのリスト
        """
        with open(CLAUDE_MD_PATH) as f:
            content = f.read()
        
        sections = self._parse_claude_md(content)
        commands = []
        
        for section in sections:
            # 200文字制限に収める
            if len(section["text"]) <= self.MAX_EDIT_LENGTH:
                commands.append(section["text"])
            else:
                # 長い場合は分割
                commands.extend(self._split_long_section(section))
        
        return commands
    
    def _parse_claude_md(self, content: str) -> List[Dict[str, str]]:
        """
        CLAUDE.mdを解析してセクションに分割
        
        Returns:
            List of {"category": str, "text": str}
        """
        sections = []
        
        # 1. 基本情報
        if match := re.search(r"ユーザー名：\*\*(.+?）\*\*", content):
            name = match.group(1)
            sections.append({
                "category": "profile",
                "text": f"User: {name}, lives in Miyagi Prefecture"
            })
        
        if match := re.search(r"プロジェクトルート：\*\*(.+?)\*\*", content):
            path = match.group(1)
            sections.append({
                "category": "environment",
                "text": f"Project path: {path}, uses Python venv"
            })
        
        # 2. 家族構成
        family_section = re.search(r"# 2\. 家族\n(.+?)\n---", content, re.DOTALL)
        if family_section:
            family_text = family_section.group(1).strip()
            # 簡潔にまとめる
            sections.append({
                "category": "family",
                "text": "User has wife 幸恵 and four children: ひなた, そら, 優月, 優陽"
            })
        
        # 3. 認知特性
        cognitive_section = re.search(r"# 3\. 認知特性.+?\n(.+?)\n---", content, re.DOTALL)
        if cognitive_section:
            traits = cognitive_section.group(1).strip()
            # 箇条書きを1行にまとめる
            trait_list = [line.strip("- ") for line in traits.split("\n") if line.startswith("-")]
            if trait_list:
                summary = ", ".join(trait_list[:3])  # 最初の3つ
                sections.append({
                    "category": "cognitive",
                    "text": f"User has ASD traits: {summary}"
                })
        
        # 4. 三層構造
        if "Yuno" in content and "Kana" in content and "Tsumu" in content:
            sections.append({
                "category": "architecture",
                "text": "Resonant Engine uses 3-layer architecture: Yuno (philosophy/GPT-5), Kana (translation/Claude 4.5), Tsumu (implementation/Cursor)"
            })
        
        # 5. 呼吸モデル
        if "呼吸" in content or "Breath" in content:
            sections.append({
                "category": "core_concept",
                "text": "Core concept: Breath-driven development with 6-phase cycle (吸う→共鳴→構造化→再内省→実装→共鳴拡大)"
            })
        
        # 6. 再評価フェーズ
        if "Re-evaluation Phase" in content or "再評価" in content:
            sections.append({
                "category": "mechanism",
                "text": "Re-evaluation Phase operates through 6 stages with 9.8% trigger rate and R_stability≥60 success criteria"
            })
        
        return sections
    
    def _split_long_section(self, section: Dict[str, str]) -> List[str]:
        """
        200文字を超えるセクションを分割
        """
        text = section["text"]
        chunks = []
        
        # 文単位で分割
        sentences = re.split(r'[.。]', text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= self.MAX_EDIT_LENGTH:
                current_chunk += sentence + "."
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "."
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def generate_import_template(self) -> str:
        """
        チャットメモリ → CLAUDE.md へのインポート用テンプレート生成
        
        Returns:
            チャットに送るプロンプト
        """
        return """あなたのメモリに保存されている内容を、以下の形式でMarkdown出力してください：

# Resonant Engine - Project Memory

---

# 1. User Profile and Environment
- Name: [name and birthdate]
- Location: [location]
- Project root: [project path]
- Python environment: [venv usage]
- Execution pattern: [osascript command chain]

---

# 2. Family
- Wife: [name and birthdate]
- Children: [names and birthdates]

---

# 3. Cognitive Traits (ASD-based)
- [trait 1]
- [trait 2]
- ...

---

# 4. Hiroaki Model
### Phase Structure (6 phases)
1. [phase 1]
2. [phase 2]
...

---

# 5. Resonant Engine: Three-Layer Architecture
### 1. Yuno (思想中枢)
- [description]

### 2. Kana (外界翻訳層)
- [description]

### 3. Tsumu (具現化層)
- [description]

---

# 6. Core Concepts
- Breath-driven development: [description]
- Re-evaluation Phase: [description]
- Crisis Index: [description]

---

# 7. Current State
- Implementation progress: [percentage]
- Recent focus: [topics]
- Active sprints: [sprint info]

---

この出力を tools/sync_memory.py import のコマンドで CLAUDE.md に保存します。
"""
    
    def import_from_chat(self, markdown_content: str):
        """
        チャットから出力されたMarkdownをCLAUDE.mdに保存
        
        Args:
            markdown_content: チャットが出力したMarkdown
        """
        with open(CLAUDE_MD_PATH, 'w') as f:
            f.write(markdown_content)
        
        print(f"✅ Memory imported to {CLAUDE_MD_PATH}")
    
    def save_session(self, session_content: str, metadata: Dict = None) -> str:
        """
        現在のセッションメモリを保存
        
        Args:
            session_content: セッションの内容（Markdown形式）
            metadata: メタデータ（タイムスタンプ、トピックなど）
        
        Returns:
            保存されたセッションID
        """
        from datetime import datetime
        import json
        
        # セッションディレクトリ作成
        SESSION_MEMORY_PATH.mkdir(parents=True, exist_ok=True)
        
        # セッションID生成
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = SESSION_MEMORY_PATH / f"{session_id}.md"
        metadata_file = SESSION_MEMORY_PATH / f"{session_id}.json"
        
        # セッション内容保存
        with open(session_file, 'w') as f:
            f.write(session_content)
        
        # メタデータ保存
        if metadata is None:
            metadata = {}
        metadata['session_id'] = session_id
        metadata['created_at'] = datetime.now().isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Session saved: {session_id}")
        print(f"   Content: {session_file}")
        print(f"   Metadata: {metadata_file}")
        
        return session_id
    
    def list_sessions(self) -> List[Dict]:
        """
        保存されたセッション一覧を取得
        
        Returns:
            セッション情報のリスト
        """
        import json
        
        if not SESSION_MEMORY_PATH.exists():
            return []
        
        sessions = []
        for metadata_file in sorted(SESSION_MEMORY_PATH.glob("*.json"), reverse=True):
            with open(metadata_file) as f:
                metadata = json.load(f)
                sessions.append(metadata)
        
        return sessions
    
    def merge_session_to_claude_md(self, session_id: str):
        """
        セッションメモリをCLAUDE.mdにマージ
        
        Args:
            session_id: マージするセッションID
        """
        session_file = SESSION_MEMORY_PATH / f"{session_id}.md"
        
        if not session_file.exists():
            print(f"❌ Session not found: {session_id}")
            return
        
        # セッション内容読み込み
        with open(session_file) as f:
            session_content = f.read()
        
        # CLAUDE.md読み込み
        if CLAUDE_MD_PATH.exists():
            with open(CLAUDE_MD_PATH) as f:
                claude_md_content = f.read()
        else:
            claude_md_content = "# Resonant Engine - Project Memory\n\n"
        
        # セッションセクションを追加
        merged_content = claude_md_content + f"\n\n---\n\n# Session {session_id}\n\n{session_content}"
        
        # 保存
        with open(CLAUDE_MD_PATH, 'w') as f:
            f.write(merged_content)
        
        print(f"✅ Session {session_id} merged into CLAUDE.md")
    
    def show_export_instructions(self, commands: List[str]):
        """
        エクスポート用の指示を表示
        """
        print("=" * 80)
        print("CLAUDE.md → Chat Memory Sync Instructions")
        print("=" * 80)
        print("\nチャット版Claudeで以下のコマンドを実行してください：\n")
        
        for i, cmd in enumerate(commands, 1):
            print(f"{i}. memory_user_edits で追加：")
            print(f'   "{cmd}"')
            print()
        
        print("=" * 80)
        print(f"Total: {len(commands)} edits to apply")
        print("=" * 80)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tools/sync_memory.py export           # CLAUDE.md → Chat Memory")
        print("  python tools/sync_memory.py import           # Chat Memory → CLAUDE.md")
        print("  python tools/sync_memory.py session-save     # Save current session")
        print("  python tools/sync_memory.py session-list     # List all sessions")
        print("  python tools/sync_memory.py session-merge ID # Merge session into CLAUDE.md")
        sys.exit(1)
    
    tool = MemorySyncTool()
    command = sys.argv[1]
    
    if command == "export":
        # CLAUDE.md → チャットメモリ
        commands = tool.export_to_chat()
        tool.show_export_instructions(commands)
        
    elif command == "import":
        # チャットメモリ → CLAUDE.md
        print(tool.generate_import_template())
        print("\n上記のプロンプトをチャット版Claudeに送信し、")
        print("出力されたMarkdownを以下のコマンドで保存してください：\n")
        print("  python tools/sync_memory.py save < output.md")
        
    elif command == "save":
        # 標準入力からMarkdownを読み込み
        markdown = sys.stdin.read()
        tool.import_from_chat(markdown)
    
    elif command == "session-save":
        # セッションメモリを保存
        print("セッション内容を入力してください（Ctrl+D で終了）:")
        session_content = sys.stdin.read()
        
        # メタデータ入力（オプション）
        topic = input("\nセッションのトピック（オプション）: ").strip()
        metadata = {"topic": topic} if topic else {}
        
        tool.save_session(session_content, metadata)
    
    elif command == "session-list":
        # セッション一覧表示
        sessions = tool.list_sessions()
        if not sessions:
            print("保存されたセッションはありません")
        else:
            print("=" * 80)
            print("保存済みセッション一覧")
            print("=" * 80)
            for session in sessions:
                print(f"\nID: {session['session_id']}")
                print(f"作成日時: {session['created_at']}")
                if 'topic' in session and session['topic']:
                    print(f"トピック: {session['topic']}")
            print("=" * 80)
    
    elif command == "session-merge":
        # セッションをCLAUDE.mdにマージ
        if len(sys.argv) < 3:
            print("使い方: python tools/sync_memory.py session-merge <SESSION_ID>")
            sys.exit(1)
        
        session_id = sys.argv[2]
        tool.merge_session_to_claude_md(session_id)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
