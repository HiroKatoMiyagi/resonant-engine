#!/bin/bash
# ===============================================
# 🧭 make_overview.sh - Resonant Engine 全体把握報告書自動生成
# ===============================================

set -e

REPORT_DIR="reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M")
REPORT_FILE="${REPORT_DIR}/overview_${TIMESTAMP}.md"

mkdir -p "${REPORT_DIR}"

cat << 'EOF' > "${REPORT_FILE}"
# 🌐 Resonant Engine 全体把握報告書
**作成日時**：$(date +"%Y-%m-%d %H:%M:%S %Z")  
**対象範囲**：思想層（Resonant Core）〜外界層（GitHub / File System）

---

## 🧭 サマリ（Summary）
{{summary}}

---

## 🧩 システム全体構造（System Map）
{{system_map}}

---

## ⚙️ 運用状態（Operations）
{{operations}}

---

## 📊 指標と傾向（Metrics）
{{metrics}}

---

## 🪶 結び
> 本レポートは思想層〜外界層の呼吸的整合状態を把握するために生成されています。
> 詳細分析は `make_report.sh` により補完可能です。
EOF

echo "✅ Resonant Engine 全体把握報告書 生成完了: ${REPORT_FILE}"
