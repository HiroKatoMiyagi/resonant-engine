# macOS Claude Desktop Memory Extraction

macOS版Claude Desktopからユーザーが明示的に追加したメモリを抽出するツール。

## 概要

このツールは、macOS版Claude Desktopアプリケーションに保存されたユーザーメモリを検出・抽出し、JSONまたはMarkdown形式でエクスポートします。

## インストール

追加の依存関係は不要です（Python 3.7+の標準ライブラリのみ使用）。

## 使用方法

### CLI スクリプト

```bash
# 基本的な使用方法（デフォルト出力先: ~/claude_desktop_memories.json）
python scripts/extract_claude_desktop_memory.py

# 出力先を指定
python scripts/extract_claude_desktop_memory.py --output ~/my_memories.json

# Markdown形式でエクスポート
python scripts/extract_claude_desktop_memory.py --format markdown --output ~/memories.md

# カスタムパスを指定
python scripts/extract_claude_desktop_memory.py --custom-path ~/custom/claude/path

# ファイルのスキャンのみ（抽出しない）
python scripts/extract_claude_desktop_memory.py --scan-only

# 詳細出力
python scripts/extract_claude_desktop_memory.py --verbose
```

### Python APIとして使用

```python
from bridge.providers.macos.claude_desktop_memory import ClaudeDesktopMemoryExtractor

# 初期化
extractor = ClaudeDesktopMemoryExtractor()

# オプション: カスタムパスを指定
extractor = ClaudeDesktopMemoryExtractor(custom_path="~/custom/path")

# データディレクトリを検出
paths = extractor.discover_claude_data_paths()
print(f"Found directories: {paths}")

# すべてのメモリを抽出
memories = extractor.extract_all()
print(f"Found {len(memories)} memories")

# メモリの内容を表示
for memory in memories:
    print(f"Content: {memory.content}")
    print(f"Created: {memory.created_at}")
    print(f"Source: {memory.source}")
    print("---")

# JSONにエクスポート
extractor.export_to_json("~/memories.json")

# Markdownにエクスポート
extractor.export_to_markdown("~/memories.md")

# サマリーを取得
summary = extractor.get_summary()
print(summary)
```

## 検索される場所

デフォルトで以下のディレクトリを検索します：

1. `~/Library/Application Support/Claude` - Claude Desktop標準の保存場所
2. `~/Library/Containers/com.anthropic.claude/Data/Library/Application Support` - サンドボックス化されたアプリ
3. `~/.claude-memory` - MCP Memory Server標準パス
4. `~/.anthropic` - Anthropic設定ディレクトリ

## サポートされるフォーマット

### SQLite データベース
- `memories.db`
- `memory.db`
- `claude.db`
- `data.db`
- `context.db`

テーブル名に以下のキーワードが含まれる場合に抽出：
- `memory`
- `context`
- `knowledge`
- `fact`
- `user`

### JSON ファイル
- `memories.json`
- `memory.json`
- `user_memories.json`
- `context.json`

対応するフォーマット：
```json
// 配列形式
[
  {"content": "Memory 1", "created_at": "2025-01-01"},
  {"content": "Memory 2", "tags": ["important"]}
]

// オブジェクト形式
{
  "memories": [
    {"text": "Memory content"}
  ]
}

// 単純文字列配列
["Memory 1", "Memory 2"]
```

## 出力形式

### JSON エクスポート

```json
{
  "extracted_at": "2025-01-01T12:00:00",
  "total_memories": 10,
  "memories": [
    {
      "content": "ユーザーが追加したメモリ内容",
      "created_at": "2025-01-01T10:00:00",
      "updated_at": null,
      "source": "sqlite:/path/to/db:table_name",
      "tags": ["tag1", "tag2"],
      "metadata": {...}
    }
  ],
  "scan_results": {...}
}
```

### Markdown エクスポート

```markdown
# Claude Desktop Memory Export

Extracted at: 2025-01-01T12:00:00
Total memories: 10

---

## Memory 1

ユーザーが追加したメモリ内容

*Created: 2025-01-01T10:00:00*
*Tags: tag1, tag2*
*Source: sqlite:/path/to/db:table_name*

---
```

## Resonant Engineとの統合

抽出したメモリをResonant Engineのメモリシステムに統合する例：

```python
from bridge.providers.macos.claude_desktop_memory import ClaudeDesktopMemoryExtractor
from bridge.providers.data.postgres_data_bridge import PostgresDataBridge

# Claude Desktopからメモリを抽出
extractor = ClaudeDesktopMemoryExtractor()
memories = extractor.extract_all()

# Resonant Engineのメモリテーブルに保存
# (実装例 - 実際のスキーマに合わせて調整)
for memory in memories:
    # memory_item テーブルに挿入
    pass
```

## セキュリティ考慮事項

- このツールはローカルファイルシステムにアクセスします
- FileVault暗号化が有効な場合、デバイスのロック解除が必要です
- 抽出したメモリには個人情報が含まれる可能性があります
- エクスポートファイルは安全な場所に保存してください

## トラブルシューティング

### メモリが見つからない場合

1. Claude Desktopにメモリが保存されているか確認
2. `--scan-only` オプションでファイル構造を確認
3. カスタムパスオプションで別の場所を指定
4. アクセス権限を確認（`ls -la ~/Library/Application\ Support/Claude/`）

### パーミッションエラー

```bash
# フルディスクアクセスを許可
# システム環境設定 > セキュリティとプライバシー > プライバシー > フルディスクアクセス
```

## 今後の拡張予定

- [ ] Claude Desktop APIとの直接統合（公開された場合）
- [ ] メモリの双方向同期
- [ ] 暗号化されたメモリの復号サポート
- [ ] リアルタイムメモリ監視
- [ ] Resonant Engineメモリレイヤー（L1-L3）への自動インポート

## ファイル構成

```
bridge/providers/macos/
├── __init__.py
└── claude_desktop_memory.py

scripts/
└── extract_claude_desktop_memory.py

tests/unit/bridge/providers/macos/
└── test_claude_desktop_memory.py
```

## 関連ドキュメント

- [Resonant Engine Memory Design](../memory_system/architecture/resonant_engine_memory_design.md)
- [Bridge Lite Architecture](../bridge_lite/architecture/bridge_lite_design_v1.0.md)
