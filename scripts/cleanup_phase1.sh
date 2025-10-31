#!/usr/bin/env bash
# ============================================
# Resonant Cleanup Phase 1 — 呼吸優先整備
# Author: 宏啓 × ユノ（GPT-5）
# Version: v3.1.0
# ============================================

set -euo pipefail
ROOT="/Users/zero/Projects/kiro-v3.1"

echo "🪶 [Resonant Cleanup Phase 1] 開始: $ROOT"

# --- 1️⃣ Archiveフォルダ新設 ---------------------------------------------
mkdir -p "$ROOT/archive_legacy"
echo "✅ archive_legacy フォルダ作成完了"

# --- 2️⃣ 外界残留構造をアーカイブへ移動 ---------------------------------
for dir in n8n cloudflare agents; do
  if [ -d "$ROOT/$dir" ]; then
    mv "$ROOT/$dir" "$ROOT/archive_legacy/" && \
    echo "📦 $dir → archive_legacy に移動"
  fi
done

# --- 3️⃣ macOS残留ファイル削除 -----------------------------------------
find "$ROOT" -name ".DS_Store" -delete
echo "🧹 .DS_Store 全削除完了"

# --- 4️⃣ 危険な.env 重複削除 -------------------------------------------
if [ -f "$ROOT/archive_legacy/n8n/.env" ]; then
  rm -f "$ROOT/archive_legacy/n8n/.env"
  echo "⚠️ 重複 .env（n8n配下）削除完了"
fi

# --- 5️⃣ 不要ログ／キャッシュ除去 ----------------------------------------
find "$ROOT/archive_legacy" -type f \( -name "*.log" -o -name "*.journal" -o -name "*.sqlite" \) -delete
echo "🗑️ ログ・キャッシュ削除完了"

# --- 6️⃣ .gitignore 再生成 ----------------------------------------------
cat > "$ROOT/.gitignore" <<'EOF'
# Environment
.env

# macOS
.DS_Store

# Legacy / Cache
archive_legacy/
*/data/
*.sqlite
*.log
*.journal
binaryData/
