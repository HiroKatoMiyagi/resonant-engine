#!/usr/bin/env python3
"""
Quick Session Save Helper
現在のセッション内容をテンプレートに沿って保存
"""

import sys
from datetime import datetime
from pathlib import Path

# 親ディレクトリからsync_memoryをインポート
sys.path.insert(0, str(Path(__file__).parent))
from sync_memory import MemorySyncTool

def create_session_template() -> str:
    """
    セッションメモリのテンプレートを生成
    """
    return f"""# Claude Code Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Context
[このセッションの背景・目的]

## Actions Taken
- [実行したアクション1]
- [実行したアクション2]

## Key Decisions
- [重要な決定事項1]
- [重要な決定事項2]

## Files Created/Modified
- [ファイル1]
- [ファイル2]

## Next Steps
- [次のステップ1]
- [次のステップ2]

## Technical Notes
[技術的メモ]

## Questions/Issues
[未解決の質問や問題]
"""

def quick_save():
    """
    クイックセーブ - エディタで入力してセッション保存
    """
    import tempfile
    import subprocess
    
    # テンプレート作成
    template = create_session_template()
    
    # 一時ファイルに書き込み
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(template)
        temp_path = f.name
    
    # エディタで開く
    editor = subprocess.os.environ.get('EDITOR', 'nano')
    subprocess.call([editor, temp_path])
    
    # 編集後の内容を読み込み
    with open(temp_path) as f:
        session_content = f.read()
    
    # トピック抽出（1行目から）
    first_line = session_content.split('\n')[0]
    topic = first_line.replace('#', '').strip()
    
    # 保存
    tool = MemorySyncTool()
    session_id = tool.save_session(session_content, {"topic": topic})
    
    # 一時ファイル削除
    Path(temp_path).unlink()
    
    return session_id

if __name__ == "__main__":
    print("Quick Session Save")
    print("=" * 80)
    print("エディタが開きます。セッション内容を入力して保存してください。")
    print()
    
    session_id = quick_save()
    
    print()
    print("=" * 80)
    print(f"✅ Session saved: {session_id}")
    print()
    print("次のステップ:")
    print(f"  1. セッション一覧: python tools/sync_memory.py session-list")
    print(f"  2. CLAUDE.mdにマージ: python tools/sync_memory.py session-merge {session_id}")
    print("=" * 80)
