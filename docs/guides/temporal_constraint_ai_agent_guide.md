# Temporal Constraint CLI - AIエージェント統合ガイド

## 概要

このCLIツールは、AIエージェント（Claude Code、Cursor、GitHub Copilot等）が検証済みファイルを誤って変更することを防ぐためのものです。

## 🎯 AIエージェント向け推奨ワークフロー

### 1. ファイル変更前に必ず制約チェック

```bash
python utils/temporal_constraint_cli.py check --file <対象ファイル> --reason "<変更理由>"
```

**終了コード:**
- `0` = 変更OK
- `1` = 確認が必要（警告を表示）

### 2. 推奨: `write`コマンドを使用

直接ファイルを書き込む代わりに、制約チェック付きの`write`コマンドを使用してください:

```bash
# 標準入力から内容を読み込む場合
echo "ファイル内容" | python utils/temporal_constraint_cli.py write \
  --file <対象ファイル> \
  --reason "<変更理由（20文字以上推奨）>"

# 内容を直接指定する場合
python utils/temporal_constraint_cli.py write \
  --file <対象ファイル> \
  --content "ファイル内容" \
  --reason "<変更理由>"
```

## ⚠️ 制約レベル

| レベル | 説明 | 変更条件 |
|--------|------|----------|
| 🔴 CRITICAL | 本番稼働中のコア機能 | **変更不可**（手動承認が必要） |
| 🟠 HIGH | 検証済み・安定稼働 | 20文字以上の理由が必要 |
| 🟡 MEDIUM | テスト済み | 警告表示のみ |
| 🟢 LOW | 開発中/未登録 | 制約なし |

## 📋 よく使うコマンド

```bash
# 制約状態を確認
python utils/temporal_constraint_cli.py status --file <ファイル>

# 登録済みファイル一覧
python utils/temporal_constraint_cli.py list

# チェックログ確認
python utils/temporal_constraint_cli.py logs
```

## 🤖 AIエージェント実装例

### Python

```python
import subprocess
import json

def safe_write_file(file_path: str, content: str, reason: str) -> dict:
    """制約チェック付きでファイルに書き込む"""
    
    result = subprocess.run(
        [
            "python", "utils/temporal_constraint_cli.py", "write",
            "--file", file_path,
            "--content", content,
            "--reason", reason,
            "--plain"
        ],
        capture_output=True,
        text=True
    )
    
    return {
        "success": result.returncode == 0,
        "message": result.stdout,
        "error": result.stderr if result.returncode != 0 else None
    }

# 使用例
result = safe_write_file(
    "backend/app/main.py",
    "# 新しい内容",
    "バグ修正: ユーザー認証の脆弱性対応 CVE-2025-1234"
)

if not result["success"]:
    print(f"⚠️ 変更がブロックされました: {result['message']}")
```

### TypeScript/Node.js

```typescript
import { execSync } from 'child_process';

function safeWriteFile(filePath: string, content: string, reason: string): { success: boolean; message: string } {
    try {
        const result = execSync(
            `python utils/temporal_constraint_cli.py write --file "${filePath}" --content "${content}" --reason "${reason}" --plain`,
            { encoding: 'utf-8' }
        );
        return { success: true, message: result };
    } catch (error: any) {
        return { success: false, message: error.stdout || error.message };
    }
}
```

## 📝 重要な注意事項

1. **CRITICALファイルは絶対に変更しない**
   - CLIを通しても変更できません
   - 新規ファイルとして実装を検討してください

2. **変更理由は具体的に**
   - 「バグ修正」ではなく「バグ修正: #123 ユーザー認証の問題」
   - Issue番号やCVE番号があれば含める

3. **チェックをバイパスしない**
   - 直接ファイルシステムに書き込まない
   - 常に`check`または`write`コマンドを使用

## 🔗 関連ドキュメント

- [Sprint 12仕様書](../02-01_sprint12/sprint12_term_drift_temporal_constraint_spec.md)
- [APIドキュメント](/api/v1/temporal-constraint/docs)

---

**更新日**: 2025-12-29  
**バージョン**: 1.0.0
